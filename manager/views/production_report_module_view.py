from rest_framework.viewsets import GetModelViewSet
from rest_framework import response
from django.db.models import Sum,Count,Avg,Q

from datetime import date
from dateutil import rrule

from manager.permissions import ManagerPermission
from manager.serializer import ReportProductionReadOnlySerializer,OperatorReadOnlySerializer,MachineReadOnlySerializer


from ppic.models import ProductionReport,Operator,Machine

class ReportProductionReadOnlyViewSet(GetModelViewSet):
    '''
    a viewset class for get data total quantity production, and total quantity not good production each month
    '''
    serializer_class = ReportProductionReadOnlySerializer
    permission_classes = [ManagerPermission]
    queryset = ProductionReport.objects.filter(date__lte=date.today()).values('date__year','date__month').annotate(total_good_production=Sum('quantity',default=0,filter=Q(process__warehouseproduct__warehouse_type__id__contains=1))).annotate(total_not_good_production=Sum('quantity_not_good',default=0)).order_by('date__year','date__month')

    def __init__(self, **kwargs):
        self.storage_data = []
        super().__init__(**kwargs)

    storage_data = []

    def loop_through_dates(self,first_date,last_date,store_data):

        for dt in rrule.rrule(rrule.MONTHLY,dtstart=first_date,until=last_date):
            
            data_production = store_data.get(dt.date(),{
                "total_good_production":0,
                "total_not_good_production":0
            })

            temp_data = {
                'production_date':dt.date(),
                **data_production
            }
            
            self.storage_data.append(temp_data)
            
            ### append each data to storage data before return all data

        return

    def generate_queryset(self,queryset) -> dict:
        
        ## set dates to key of dictionary, and set data total productions as value

        store_data = {}
        for data in queryset:
            year = data['date__year']
            month = data['date__month']
            each_date = date(year,month,1)

            store_data[each_date] = {
                'total_good_production':data['total_good_production'],
                'total_not_good_production':data['total_not_good_production']
            }
            
        return store_data

    def generate_data_and_return_from_queryset(self):
        
        queryset = self.filter_queryset(self.get_queryset())
        first_data = queryset.first()
        last_data = queryset.last()

        if first_data:
            # if data is exists then do generate, else return empty array(list)

            first_year = first_data['date__year']
            first_month = first_data['date__month']
            first_date = date(first_year,first_month,1)

            last_year = last_data['date__year']
            last_month = last_data['date__month']
            last_date = date(last_year,last_month,1)

            store_data = self.generate_queryset(queryset)
            self.loop_through_dates(first_date,last_date,store_data)

        serializer = self.get_serializer(self.storage_data,many=True)

        return  response.Response(serializer.data)

    def list(self, request, *args, **kwargs):

        return self.generate_data_and_return_from_queryset()


class OperatorReadOnlyViewSet(GetModelViewSet):
    '''
    a viewset class for get all data operator, avg production, good percentage of production, and times do production
    '''
    serializer_class = OperatorReadOnlySerializer
    permission_classes = [ManagerPermission]
    queryset = Operator.objects.annotate(times_do_production=Count('productionreport',distinct=True),avg_production=Avg('productionreport__quantity'),good_percentage=(Sum('productionreport__quantity') / (Sum('productionreport__quantity')+Sum('productionreport__quantity_not_good'))) * 100,total_goods_produced=Sum('productionreport__quantity')  )


class MachineReadOnlyViewSet(GetModelViewSet):
    '''
    a viewset class for get all data machine, avg production, goods percentage of production, and times used in production
    '''
    serializer_class = MachineReadOnlySerializer
    permission_classes = [ManagerPermission]
    queryset = Machine.objects.prefetch_related('productionreport_set').annotate(times_do_production=Count('productionreport',distinct=True),avg_production=Avg('productionreport__quantity'),good_percentage=(Sum('productionreport__quantity')/(Sum('productionreport__quantity')+Sum('productionreport__quantity_not_good'))) * 100,total_goods_produced=Sum('productionreport__quantity') )
