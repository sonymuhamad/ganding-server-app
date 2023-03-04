from rest_framework.viewsets import GetModelViewSet,ReadOnlyModelViewSet
from rest_framework.response import Response

from django.db.models import Prefetch,Q,F,Sum

from datetime import date
from dateutil import rrule

from marketing.permissions import MarketingPermission
from marketing.models import SalesOrder

from ppic.models import ProductOrder
from marketing.serializers.sales_order_serializer import TwoDepthProductOrderSerializer,OneDepthSalesOrderNestedProductOrderSerializer,ReportProductOrderSerializer

class FinishedSalesOrderViewSet(GetModelViewSet):
    '''
    a viewset provide endpoint to get sales order that already finished, but not closed yet.
    '''
    permission_classes = [MarketingPermission]
    serializer_class = OneDepthSalesOrderNestedProductOrderSerializer
    queryset = SalesOrder.objects.select_related('customer').prefetch_related(
        Prefetch('productoder_set',ProductOrder.objects.select_related('product','product__customer','product__type'))).filter(Q(closed=False),productorder__delivered__gte=F('productorder__ordered'))


class ReportProductOrderViewSet(ReadOnlyModelViewSet):
    '''
    a viewset for get total ordered product each month, retrieve means for particular customer
    '''
    permission_classes = [MarketingPermission]
    serializer_class = ReportProductOrderSerializer
    queryset = ProductOrder.objects.filter(Q(sales_order__fixed=True),sales_order__date__lte=date.today()).values('sales_order__date__year','sales_order__date__month').annotate(total_order=Sum('ordered')).order_by('sales_order__date__year','sales_order__date__month')

    def generate_date_from_queryset(self,queryset) -> dict:

        store_data = {}

        for data in queryset:
            year = data['sales_order__date__year']
            month = data['sales_order__date__month']
            store_data[date(year,month,1)] = data['total_order']
        
        return store_data

    def generate_data_from_dates(self,first_date,last_date,data_report,generated_data):
        
        for dt in rrule.rrule(rrule.MONTHLY,dtstart=first_date,until=last_date):
                current_date = date(dt.year,dt.month,1)
                current_total_order = generated_data.get(current_date,0)
                data_report.append({
                    'date':current_date,
                    'total_order':current_total_order
                })

    def list(self, request, *args, **kwargs):
        return self.generate_data_and_return(self.queryset)

    def generate_data_and_return(self,queryset):
        
        first_monthly_order = queryset.first()
        last_monthly_order = queryset.last()
        data_report = []

        if queryset.count() > 0:
            generated_data = self.generate_date_from_queryset(queryset)

            first_year = first_monthly_order['sales_order__date__year']
            first_month = first_monthly_order['sales_order__date__month']

            last_year = last_monthly_order['sales_order__date__year']
            last_month = last_monthly_order['sales_order__date__month']

            first_date = date(first_year,first_month,1)
            last_date = date(last_year,last_month,1)

            self.generate_data_from_dates(first_date,last_date,data_report,generated_data)

        serializer = self.get_serializer(data_report,many=True)
        return Response(serializer.data)



    def retrieve(self, request, *args, **kwargs):
        
        pk = int(kwargs['pk'])

        queryset = ProductOrder.objects.filter(Q(sales_order__fixed=True),sales_order__date__lte=date.today(),sales_order__customer__pk__exact=pk).values('sales_order__date__year','sales_order__date__month').annotate(total_order=Sum('ordered')).order_by('sales_order__date__year','sales_order__date__month')
        
        return self.generate_data_and_return(queryset)


class InProgressProductOderViewSet(GetModelViewSet):
    '''
    a viewset provide endpoint to get in progress order
    '''
    serializer_class = TwoDepthProductOrderSerializer
    permission_classes = [MarketingPermission]
    queryset = ProductOrder.objects.select_related('product','sales_order','product__customer','product__type','sales_order__customer').filter(Q(delivered__lt=F('ordered')),Q(sales_order__fixed=True)&Q(sales_order__closed=False)).order_by('pk')



