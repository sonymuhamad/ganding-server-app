from rest_framework.response import Response
from rest_framework import status

from django.shortcuts import get_object_or_404
from django.db.models import Prefetch,F,Count,Sum

from manager.viewsets import ReadOnlyModelViewSet,CreateUpdateDeleteModelViewSet
from manager.shortcuts import invalid
from ppic.utils import MultipartJsonParser
from ppic.permissions import CanManageProduct,PpicPermission

from ppic.models import Product,ProductOrder,Process,WarehouseProduct,RequirementMaterial,RequirementProduct,ProcessType,ProductType,WarehouseType

from ppic.serializers.product_serializer import OneDepthProductNestedProcessAndOrderSerializer,OneDepthProductSerializer,ProductTypeSerializer,ProcessTypeSerializer,ProcessManagementSerializer,ProductManagementSerializer

from rest_framework.permissions import AllowAny

class ProductListViewSet(ReadOnlyModelViewSet):
    '''
    a viewset for handle request of data products
    '''
    serializer_class = OneDepthProductSerializer
    queryset = Product.objects.get_queryset_related()

class ProductTypeViewSet(ReadOnlyModelViewSet):
    '''
    a viewset for handling request of data product type
    '''
    permission_classes = [PpicPermission]
    serializer_class = ProductTypeSerializer
    queryset = ProductType.objects.annotate(products=Count('product'))

class ProductTypeManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a viewset for cud product type
    '''
    permission_classes = [PpicPermission,CanManageProduct]
    serializer_class = ProductTypeSerializer
    queryset = ProductType.objects.all()
    
    def destroy(self, request, *args, **kwargs):
        '''
        function for delete product type return response object
        '''
        pk = kwargs['pk']
        product_type = get_object_or_404(self.queryset,pk=pk)

        if product_type.product_set.exists():
            invalid('There is still product with this type in database')

        if product_type.id == 1 or product_type.id ==2:
            invalid('It is forbidden to delete the main type of production on the system')

        return super().destroy(request, *args, **kwargs)    

class ProcessTypeViewSet(ReadOnlyModelViewSet):
    '''
    a viewset for get and retrieve process type
    '''
    permission_classes = [PpicPermission]
    serializer_class = ProcessTypeSerializer
    queryset = ProcessType.objects.annotate(amount_of_process=Count('process'))

class ProcessTypeManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a viewset for cud process type
    '''    
    permission_classes = [PpicPermission,CanManageProduct]
    serializer_class = ProcessTypeSerializer
    queryset = ProcessType.objects.all()
    
    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']
        process_type = get_object_or_404(self.queryset,pk=pk)

        if process_type.process_set.exists():
            invalid('There is still process with this type in database')
        
        if process_type.id == 2 or process_type.id == 1:
            invalid("It is forbidden to delete the main production type on the system")

        return super().destroy(request, *args, **kwargs)

class ProductDetailReadOnlyViewSet(ReadOnlyModelViewSet):
    permission_classes = [PpicPermission]
    serializer_class = OneDepthProductNestedProcessAndOrderSerializer
    queryset_warehouseproduct = WarehouseProduct.objects.select_related('warehouse_type','process','product')
    queryset_product_order = ProductOrder.objects.select_related('sales_order','product').filter(delivered__lt=F('ordered'))

    queryset_requirement_product = RequirementProduct.objects.select_related('product','process','product__customer','product__type').prefetch_related(
        Prefetch('product__ppic_warehouseproduct_related',queryset_warehouseproduct))
    queryset_requirement_material = RequirementMaterial.objects.select_related('material','material__warehousematerial','material__supplier','material__uom','material__warehousematerial__material','process')

    queryset = Product.objects.get_queryset_related().prefetch_related(
            Prefetch('ppic_process_related',queryset=Process.objects.
            prefetch_related(
                Prefetch('warehouseproduct_set',queryset = queryset_warehouseproduct)).
            prefetch_related(
                Prefetch('requirementproduct_set',queryset = queryset_requirement_product )).
            prefetch_related(
                Prefetch('requirementmaterial_set',queryset = queryset_requirement_material)).select_related('process_type','product'))).prefetch_related(
                    Prefetch('ppic_productorder_related',queryset = queryset_product_order)).annotate(productordered=Sum('ppic_productorders__ordered')).annotate(productdelivered=Sum('ppic_productorders__delivered'))

class ProcessManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a viewset that handle management create update delete for process, nested to requirement material, requirement product, warehouse product
    '''
    permission_classes = [PpicPermission,CanManageProduct]
    serializer_class = ProcessManagementSerializer
    queryset = Process.objects.prefetch_related(
        Prefetch('requirementmaterial_set',queryset=RequirementMaterial.objects.select_related('material','process'))).prefetch_related(
        Prefetch('requirementproduct_set',queryset=RequirementProduct.objects.select_related('product','process'))).prefetch_related(
        Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.select_related('warehouse_type','product','process'))).select_related('product','process_type')

    def change_previous_process(self,previous_process:Process):
        '''
        change previous process of deleted process to finished goods
        '''
        wh_type_fg = WarehouseType.objects.get(pk=1)
        wh_product_prev_process = previous_process.warehouseproduct_set.exclude(warehouse_type=2).get()
        wh_product_prev_process.warehouse_type = wh_type_fg
        wh_product_prev_process.save()

    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']
        instance_process = get_object_or_404(self.queryset,pk=pk)
        
        for wh_products in instance_process.warehouseproduct_set.all():
            if wh_products.quantity > 0:
                invalid()

        whProduct = instance_process.warehouseproduct_set.exclude(warehouse_type=2).get()
        product = instance_process.product
        len_queryset_process = product.ppic_process_related.count()

        if whProduct.warehouse_type.id == 1 and len_queryset_process > 1 :
            ## change the previous of the last process to finished good, before delete selected process

            order = instance_process.order

            try:
                one_previous_process = product.ppic_process_related.get(order = (order - 1))
                self.change_previous_process(one_previous_process)

            except:
                two_previous_process = product.ppic_process_related.get(order = (order - 2))
                self.change_previous_process(two_previous_process)
        
        return super().destroy(request, *args, **kwargs)

class ProductManagementViewSet(CreateUpdateDeleteModelViewSet):
    permission_classes = [PpicPermission,CanManageProduct]
    serializer_class = ProductManagementSerializer
    parser_classes = [MultipartJsonParser]
    queryset = Product.objects.get_queryset_related().prefetch_related(
            Prefetch('ppic_process_related',queryset=Process.objects.
            prefetch_related(
                Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.select_related('warehouse_type','product','process'))).
            prefetch_related(
                Prefetch('requirementproduct_set',queryset=RequirementProduct.objects.select_related('product'))).
            prefetch_related(
                Prefetch('requirementmaterial_set',queryset=RequirementMaterial.objects.select_related('material'))).select_related('process_type')))

    def fields_check(self,data):
        
        many_process = data.get('ppic_process_related',[])

        if many_process == []:
            return {**data,'ppic_process_related':[]}

        for process in many_process:
            reqproduct = process.get('requirementproduct_set',None)
            reqmaterial = process.get('requirementmaterial_set',None)
            if reqproduct is None:
                process['requirementproduct_set'] = []
            if reqmaterial is None:
                process['requirementmaterial_set'] = []
        
        return data

    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']
        queryset = Product.objects.prefetch_related('ppic_productorder_related').prefetch_related('ppic_warehouseproduct_related').prefetch_related('ppic_requirementproduct_related')

        instance_product = get_object_or_404(queryset,pk=pk)
        
        for productorder in instance_product.ppic_productorder_related.all():
            if productorder.delivered > 0:
                invalid()

        for whproduct in instance_product.ppic_warehouseproduct_related.all():
            if whproduct.quantity > 0:
                invalid()

        for requirement_product in instance_product.ppic_requirementproduct_related.all():
            if requirement_product.conversion > 0:
                invalid()

        return super().destroy(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):

        data = self.fields_check(request.data.dict())
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        image  = data.get('image',None)
        if image is not None and image =='':
            instance.image.delete(save=True)
            data.pop('image')

        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        
        data = self.fields_check(request.data.dict())
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

###########################################
###########################################
