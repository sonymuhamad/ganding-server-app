from rest_framework.viewsets import GetModelViewSet
from rest_framework.response import Response
from django.db.models import Prefetch,Q,F,Sum

from datetime import date
from dateutil import rrule

from ppic.permissions import PpicPermission

from ppic.models import Product,ProductOrder,Material,ProductionReport,RequirementMaterial

from ppic.serializers.product_serializer import OneDepthProductNestedOrderSerializer
from ppic.serializers.material_serializer import MaterialDetailSerializer
from ppic.serializers.production_serializer import MonthlyProductionReportSerializer

class ProductOrderedViewSet(GetModelViewSet):
    '''
    a viewset for request list of product there is still have an upcoming product delivery
    '''
    permission_classes = [PpicPermission]
    serializer_class = OneDepthProductNestedOrderSerializer
    queryset = Product.objects.get_queryset_related().prefetch_related(
        Prefetch('ppic_productorder_related',queryset=ProductOrder.objects.select_related('sales_order','product'))).filter(Q(ppic_productorders__sales_order__fixed=True)&Q(ppic_productorders__ordered__gt=F('ppic_productorders__delivered'))&Q(ppic_productorders__sales_order__closed=False)).annotate(rest_order=Sum(
            'ppic_productorders__ordered')-Sum('ppic_productorders__delivered')).filter(Q(rest_order__isnull=False))

class MaterialOrderedViewSet(GetModelViewSet):
    '''
    a viewset for request list of material there is still have an upcoming material receipt
    '''
    permission_classes = [PpicPermission]
    serializer_class = MaterialDetailSerializer
    queryset = Material.objects.get_queryset_related().prefetch_related(
        Prefetch('ppic_requirementmaterial_related',queryset=RequirementMaterial.objects.select_related('process','process__process_type','process__product'))).filter(ppic_materialorders__ordered__gt=F('ppic_materialorders__arrived'),ppic_materialorders__purchase_order_material__done=False).annotate(rest_arrival=Sum(
            'ppic_materialorders__ordered')-Sum('ppic_materialorders__arrived')).filter(Q(
                            rest_arrival__isnull=False))

class MonthlyProductionReportViewSet(GetModelViewSet):
    '''
    a viewset for get monthly report of total production
    '''
    permission_classes = [PpicPermission]
    serializer_class = MonthlyProductionReportSerializer
    queryset = ProductionReport.objects.filter(Q(process__warehouseproduct__warehouse_type__id__contains=1),date__lte=date.today()).values('date__year','date__month').annotate(total_production=Sum('quantity',default=0)+Sum('quantity_not_good',default=0)).order_by('date__year','date__month')

    def list(self, request, *args, **kwargs):
        '''
        endpoint to get all production finished goods for every month,
        '''
        
        validate_data = []
        queryset = self.filter_queryset(self.get_queryset())
        start = queryset.first()
        end = queryset.last()

        if start:
            start_date = date(start['date__year'],start['date__month'],1)
            end_date = date(end['date__year'],end['date__month'],1)        

            for dt in rrule.rrule(rrule.MONTHLY,dtstart=start_date,until=end_date):
                try:
                    data = queryset.get(date__year=dt.year,date__month=dt.month)
                    validate_data.append(data)
                except:
                    temp_data = {
                        'date__year':dt.year,
                        'date__month':dt.month,
                        'total_production':0
                    }
                    validate_data.append(temp_data)

        serializer = self.get_serializer(validate_data, many=True)
        return Response(serializer.data)
