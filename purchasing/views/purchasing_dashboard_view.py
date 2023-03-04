from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.response import Response

from django.db.models import Q,Sum
from dateutil import rrule
from datetime import date

from ppic.models import Material

from purchasing.permissions import PurchasingPermission
from purchasing.serializers.purchase_order_serializer import MaterialUsageAndOrderSerializer


class MaterialUsageAndOrderViewSet(ReadOnlyModelViewSet):
    '''
    a viewset for get all usage material on each month, and order material on each month
    '''
    permission_classes = [PurchasingPermission]
    serializer_class = MaterialUsageAndOrderSerializer
    
    ## queryset provided data all order through year->month
    queryset = Material.objects.filter(Q(ppic_materialorders__isnull=False),ppic_materialorders__purchase_order_material__date__lte=date.today()).values('ppic_materialorders__purchase_order_material__date__year','ppic_materialorders__purchase_order_material__date__month').annotate(total_order=Sum('ppic_materialorders__ordered')).order_by('ppic_materialorders__purchase_order_material__date__year','ppic_materialorders__purchase_order_material__date__month')

    ## querysetProduction provided data all material usage through year->month
    querysetProduction = Material.objects.filter(Q(ppic_materialproductionreports__isnull=False),ppic_materialproductionreports__production_report__date__lte=date.today()).values('ppic_materialproductionreports__production_report__date__year','ppic_materialproductionreports__production_report__date__month').annotate(total_usage=Sum('ppic_materialproductionreports__quantity')).order_by('ppic_materialproductionreports__production_report__date__year','ppic_materialproductionreports__production_report__date__month')

    def getStartDate(self,orderDate,usageDate):
        '''
        a function to get startDate
        '''
        if orderDate < usageDate:
            return orderDate
        return usageDate 

    def getEndDate(self,orderDate,usageDate):
        '''
        a function to get last start Date
        '''
        if orderDate > usageDate:
            return orderDate
        return usageDate

    def getFirstDateAndLastDate(self,startOrder,endOrder,startProduction,endProduction):
        '''
        a function to get first, and last date with comparing data between material usage, and material order
        return (firstDate,lastDate)
        '''
        
        startOrderDate,endOrderDate,startProductionDate,endProductionDate = (date.today()for x in range(4))

        if startOrder:
            start_year_order = startOrder['ppic_materialorders__purchase_order_material__date__year']
            start_month_order = startOrder['ppic_materialorders__purchase_order_material__date__month']

            end_year_order,end_month_order = endOrder['ppic_materialorders__purchase_order_material__date__year'],endOrder['ppic_materialorders__purchase_order_material__date__month']

            startOrderDate = date(start_year_order,start_month_order,1)
            endOrderDate = date(end_year_order,end_month_order,1)

        if startProduction:
            start_year_usage,start_month_usage = startProduction['ppic_materialproductionreports__production_report__date__year'],startProduction['ppic_materialproductionreports__production_report__date__month']

            end_year_usage,end_month_usage = endProduction['ppic_materialproductionreports__production_report__date__year'],endProduction['ppic_materialproductionreports__production_report__date__month']

            startProductionDate = date(start_year_usage,start_month_usage,1)
            endProductionDate = date(end_year_usage,end_month_usage,1)

        startDate = self.getStartDate(startOrderDate,startProductionDate)
        endDate = self.getEndDate(endOrderDate,endProductionDate)

        return startDate,endDate 
    
    def get_usage(self,queryset):
        '''
        transform data in queryset to dictionary, then return it
        '''
        usages = {}
        for usage in queryset:
            year = usage['ppic_materialproductionreports__production_report__date__year']
            month = usage['ppic_materialproductionreports__production_report__date__month']
            usages[date(year,month,1)] = usage['total_usage']
        
        return usages

    def get_order(self,queryset):
        '''
        transform data in queryset to dictionary, then return it
        '''
        orders = {}
        for order in queryset:
            year = order['ppic_materialorders__purchase_order_material__date__year']
            month = order['ppic_materialorders__purchase_order_material__date__month']
            orders[date(year,month,1)] = order['total_order']
            ## date(key) => total_order(value)

        return orders

    def generate_data_and_return(self,start_date,end_date,queryset_order,queryset_usage):
        '''
        a function to generate data order material and data usage material
        '''

        validated_data = []
        
        data_order = self.get_order(queryset_order)
        data_usage = self.get_usage(queryset_usage)

        if len(data_order) != 0 and len(data_usage) != 0:
            
            for dt in rrule.rrule(rrule.MONTHLY,dtstart=start_date,until=end_date):
                current_date = date(dt.year,dt.month,1)
                current_order = data_order.get(current_date,0)
                current_usage = data_usage.get(current_date,0)
                
                validated_data.append({
                    'date':current_date,
                    'total_order': current_order,
                    'total_usage': current_usage
                })

        serializer = self.get_serializer(validated_data, many=True)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):

        queryset = self.filter_queryset(self.get_queryset())
        startOrder = queryset.first()
        endOrder = queryset.last()
        startProduction = self.querysetProduction.first()
        endProduction = self.querysetProduction.last()
        startDate,endDate = self.getFirstDateAndLastDate(startOrder,endOrder,startProduction,endProduction)

        return self.generate_data_and_return(startDate,endDate,queryset,self.querysetProduction) 

    def retrieve(self, request, *args, **kwargs):

        pk = kwargs['pk']
        queryset_order = Material.objects.filter(Q(id__exact=pk) & Q(ppic_materialorders__isnull=False),ppic_materialorders__purchase_order_material__date__lte=date.today()).values('ppic_materialorders__purchase_order_material__date__year','ppic_materialorders__purchase_order_material__date__month').annotate(total_order=Sum('ppic_materialorders__ordered')).order_by('ppic_materialorders__purchase_order_material__date__year','ppic_materialorders__purchase_order_material__date__month')

        queryset_production = Material.objects.filter(Q(id__exact=pk),Q(ppic_materialproductionreports__isnull=False),ppic_materialproductionreports__production_report__date__lte=date.today()).values('ppic_materialproductionreports__production_report__date__year','ppic_materialproductionreports__production_report__date__month').annotate(total_usage=Sum('ppic_materialproductionreports__quantity')).order_by('ppic_materialproductionreports__production_report__date__year','ppic_materialproductionreports__production_report__date__month')

        startOrder = queryset_order.first()
        endOrder = queryset_order.last()
        startProduction = queryset_production.first()
        endProduction = queryset_production.last()
        startDate,endDate = self.getFirstDateAndLastDate(startOrder,endOrder,startProduction,endProduction)
        
        return self.generate_data_and_return(startDate,endDate,queryset_order,queryset_production)