
from django.db.models import Prefetch,Count,Q,Sum
from rest_framework.viewsets import ModelViewSet,ReadOnlyModelViewSet,CreateUpdateDeleteModelViewSet,RetrieveModelViewSet,UpdateModelViewSet
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .serializer import *

from ppic.models import *
from .permissions import PurchasingPermission,CanManagePurchaseOrderMaterial,CanManageSupplier

from .models import Supplier,PurchaseOrderMaterial
from manager.shortcuts import invalid
from dateutil import rrule
import functools
import time
from django.db import connection, reset_queries



def queryDebug(func):

    @functools.wraps(func)
    def inner_func(*args, **kwargs):

        reset_queries()

        start_queries = len(connection.queries)

        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()

        end_queries = len(connection.queries)

        print(f"Function : {func.__name__}")
        print(f"Number of Queries : {end_queries - start_queries}")
        print(f"Finished in : {(end - start):.2f}s")

        return result

    return inner_func


def validate_mo(queryset):
    for mo in queryset:
            if mo.arrived > 0:
                invalid()

def validate_po(queryset):

    for po in queryset:
        if po.done:
            invalid()
        queryset_mo = po.materialorder_set.all() 
        validate_mo(queryset_mo)

class SupplierManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a viewset for cud supplier
    '''
    permission_classes = [PurchasingPermission,CanManageSupplier]
    serializer_class = BaseSupplierSerializer
    queryset = Supplier.objects.all()

    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']

        queryset = Supplier.objects.prefetch_related(
            Prefetch('purchasing_purchaseordermaterial_related',queryset=PurchaseOrderMaterial.objects.prefetch_related('materialorder_set'))).prefetch_related(
                Prefetch('ppic_material_related',queryset=Material.objects.prefetch_related('ppic_requirementmaterial_related').select_related('warehousematerial')))

        instance_supplier = get_object_or_404(queryset,pk=pk)
        queryset_po = instance_supplier.purchasing_purchaseordermaterial_related.all()

        validate_po(queryset_po)
        
        for material in instance_supplier.ppic_material_related.all():
            
            for requirementmaterial in material.ppic_requirementmaterial_related.all():
                if requirementmaterial.input > 0:
                    invalid()
            
            if material.warehousematerial.quantity>0:
                invalid()

        return super().destroy(request, *args, **kwargs)

class SupplierViewSet(ReadOnlyModelViewSet):
    permission_classes = [PurchasingPermission]
    serializer_class = BaseSupplierSerializer
    queryset = Supplier.objects.annotate(number_of_material=Count(
        'ppic_materials',distinct=True)).annotate(number_of_purchase_order=Count(
            'purchasing_purchaseordermaterials',distinct=True))

class SupplierReadOnlyViewSet(RetrieveModelViewSet):
    '''
    a viewset for retrieve detail supplier nested to material, purchase order -> material order
    '''
    permission_classes = [PurchasingPermission]
    serializer_class = SupplierReadOnlySerializer
    queryset = Supplier.objects.prefetch_related(Prefetch(
        'ppic_material_related',queryset=Material.objects.select_related('uom','supplier','warehousematerial')),Prefetch(
            'purchasing_purchaseordermaterial_related',queryset=PurchaseOrderMaterial.objects.prefetch_related(Prefetch(
                'materialorder_set',queryset=MaterialOrder.objects.select_related('material','purchase_order_material','material__uom','material__supplier')))))

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

class PurchaseOrderReadOnlyViewSet(ReadOnlyModelViewSet):
    permission_classes = [PurchasingPermission]
    serializer_class = PurchaseOrderReadOnlySerializer
    queryset = PurchaseOrderMaterial.objects.prefetch_related(
            Prefetch('materialorder_set',queryset=MaterialOrder.objects.select_related('material','purchase_order_material','material__supplier','material__uom','purchase_order_material__supplier'))).select_related('supplier')


class MaterialReceiptScheduleReadOnlyViewSet(RetrieveModelViewSet):
    '''
    a viewset for get all schedule based on its purchase order material, for detail po page
    '''
    permission_classes = [PurchasingPermission]
    serializer_class = MaterialReceiptScheduleReadOnlySerializer
    queryset = MaterialReceiptSchedule.objects.select_related('material_order','material_order__purchase_order_material','material_order__material','material_order__purchase_order_material__supplier','material_order__material__supplier','material_order__material__uom')

    def retrieve(self, request, *args, **kwargs):
        pk = kwargs['pk']
        queryset = self.filter_queryset(self.get_queryset())
        validate_queryset = queryset.filter(material_order__purchase_order_material__id__exact=pk)
        serializer = self.get_serializer(validate_queryset, many=True)

        return Response(serializer.data)


class StatusPurchaseOrderManagementViewSet(UpdateModelViewSet):
    '''
    a viewset to just update status of purchase order material
    '''
    permission_classes = [PurchasingPermission,CanManagePurchaseOrderMaterial]
    serializer_class = StatusPurchaseOrderManagementSerializer
    queryset = PurchaseOrderMaterial.objects.prefetch_related('materialorder_set')


class PurchaseOrderManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a viewset for cud purchase order
    '''
    permission_classes = [PurchasingPermission,CanManagePurchaseOrderMaterial]
    serializer_class = PurchaseOrderManagementSerializer

    queryset = PurchaseOrderMaterial.objects.select_related('supplier')
    
    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']
        instance_po = self.queryset
        instance_po = get_object_or_404(instance_po,pk=pk)
        
        if instance_po.done:
            invalid()
        
        instance_mo = instance_po.materialorder_set.all()
        validate_mo(instance_mo)

        return super().destroy(request, *args, **kwargs)

class MaterialReceiptScheduleManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a viewset for management material receipt schedule
    '''
    permission_classes = [PurchasingPermission,CanManagePurchaseOrderMaterial]
    serializer_class = MaterialReceiptScheduleManagementSerializer
    queryset = MaterialReceiptSchedule.objects.select_related('material_order')

    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']
        instance = get_object_or_404(self.queryset,pk=pk)

        if instance.fulfilled_quantity > 0:
            invalid()

        return super().destroy(request, *args, **kwargs)

class MaterialOrderManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a viewset for cud material order
    '''
    permission_classes = [PurchasingPermission,CanManagePurchaseOrderMaterial]
    serializer_class = MaterialOrderManagementSerializer
    queryset = MaterialOrder.objects.select_related('purchase_order_material','material')

    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']
        instance_mos = self.queryset
        instance_mo = get_object_or_404(instance_mos,pk=pk)

        if instance_mo.arrived > 0:
             invalid()
             
        return super().destroy(request, *args, **kwargs)
        

class MaterialListViewSet(RetrieveModelViewSet):
    '''
    a viewset for retrieve queryset of material, based on particular supplier
    '''
    permission_classes = [PurchasingPermission]
    serializer_class = MaterialListSerializer
    queryset = Material.objects.select_related('supplier','uom')

    def retrieve(self, request, *args, **kwargs):
        pk = kwargs['pk']

        queryset = self.filter_queryset(self.get_queryset())
        validate_queryset = queryset.filter(supplier__id__exact=pk)
        serializer = self.get_serializer(validate_queryset, many=True)

        return Response(serializer.data)

class MaterialReceiptListViewSet(ReadOnlyModelViewSet):
    '''
    a viewset for retrieve queryset of material receipt, based on particular purchase order
    '''
    permission_classes = [PurchasingPermission]
    serializer_class = MaterialReceiptListSerializer
    queryset = MaterialReceipt.objects.select_related('delivery_note_material','material_order','delivery_note_material__supplier','material_order__material','material_order__purchase_order_material','material_order__purchase_order_material__supplier','material_order__material__uom','material_order__material__supplier','schedules','schedules__material_order','schedules__material_order__material','schedules__material_order__purchase_order_material').order_by('delivery_note_material__date')

    def retrieve(self, request, *args, **kwargs):

        pk = kwargs['pk']
        
        queryset = self.filter_queryset(self.get_queryset())
        validate_queryset = queryset.filter(material_order__purchase_order_material__id=pk)
        serializer = self.get_serializer(validate_queryset, many=True)

        return Response(serializer.data)




















