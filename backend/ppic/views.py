from rest_framework.viewsets import ModelViewSet,ReadOnlyModelViewSet,CreateUpdateDeleteModelViewSet,UpdateModelViewSet,CreateModelViewSet,GetModelViewSet

from rest_framework.permissions import AllowAny
from rest_framework.serializers import ValidationError
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status

from math import ceil
import functools
import time
from django.db import connection, reset_queries
from django.db.models import Prefetch,Q
from django.shortcuts import get_object_or_404


from manager.shortcuts import invalid
from ppic.models import *

from purchasing.models import Supplier
from .serializer import *

from marketing.models import Customer, SalesOrder


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


class ProductCustomerReadOnlyViewSet(ReadOnlyModelViewSet):
    serializer_class = ProductCustomerReadOnlySerializer
    permission_classes = [AllowAny]
    queryset = Customer.objects.prefetch_related(
        Prefetch('ppic_product_related',queryset=Product.objects.prefetch_related(
            Prefetch('ppic_process_related',queryset=Process.objects.
            prefetch_related(
                Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.select_related('warehouse_type'))).
            prefetch_related(
                Prefetch('requirementproduct_set',queryset=RequirementProduct.objects.select_related('product'))).
            prefetch_related(
                Prefetch('requirementmaterial_set',queryset=RequirementMaterial.objects.select_related('material'))).select_related('process_type'))).select_related('type')))

class ProductManagementViewSet(CreateUpdateDeleteModelViewSet):
    serializer_class = ProductManagementSerializer
    permission_classes = [AllowAny]
    queryset = Product.objects.prefetch_related(
            Prefetch('ppic_process_related',queryset=Process.objects.
            prefetch_related(
                Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.select_related('warehouse_type'))).
            prefetch_related(
                Prefetch('requirementproduct_set',queryset=RequirementProduct.objects.select_related('product'))).
            prefetch_related(
                Prefetch('requirementmaterial_set',queryset=RequirementMaterial.objects.select_related('material'))).select_related('process_type'))).select_related('type')

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


class MaterialSupplierReadOnlyViewSet(ReadOnlyModelViewSet):
    serializer_class = MaterialSupplierReadOnlySerializer
    permission_classes = [AllowAny]
    queryset = Supplier.objects.prefetch_related(Prefetch('ppic_material_related',queryset=Material.objects.prefetch_related(Prefetch('ppic_requirementmaterial_related',queryset=RequirementMaterial.objects.select_related('process__product'))).select_related('warehousematerial') ))

class MaterialSerializer(ModelViewSet):
    serializer_class = MaterialSerializer
    permission_classes = [AllowAny]
    queryset = Material.objects.prefetch_related('ppic_requirementmaterial_related').select_related('warehousematerial')

    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']
        instances = self.queryset
        instance = get_object_or_404(instances,pk=pk)

        req_material = instance.ppic_requirementmaterial_related.all()
        wh_material = instance.ppic_warehousematerial_related.first()

        if len(req_material) > 0:
            raise ValidationError('Tidak bisa menghapus data material yang menjadi kebutuhan produksi')
        if wh_material.quantity > 0:
            raise ValidationError('Tidak bisa menghapus data material yang memiliki stok di gudang')
        return super().destroy(request, *args, **kwargs)

class RequirementMaterialViewSet(CreateUpdateDeleteModelViewSet):
    serializer_class = RequirementMaterialManagement
    permission_classes = [AllowAny]
    queryset = RequirementMaterial.objects.all()

class RequirementProductViewSet(CreateUpdateDeleteModelViewSet):
    serializer_class = RequirementProductManagement
    permission_classes = [AllowAny]
    queryset = RequirementProduct.objects.all()


class MrpReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    get mrp
    '''
    serializer_class = MrpReadOnlySerializer
    permission_classes = [AllowAny]
    queryset = MaterialRequirementPlanning.objects.prefetch_related(Prefetch('detailmrp_set',queryset=DetailMrp.objects.select_related('product'))).select_related('material__supplier','material__uom')

    @queryDebug
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

class MrpManagementViewSet(ModelViewSet):
    '''
    list : for mrp recommendations
    create , update , delete : mrp -> detail mrp
    '''
    serializer_class = MrpManagementSerializer
    permission_classes = [AllowAny]
    queryset = MaterialRequirementPlanning.objects.all()
    data = {}

    @queryDebug
    def list(self, request, *args, **kwargs):

        sales_order = SalesOrder.objects.filter(fixed=True,done=False).prefetch_related(Prefetch('productorder_set',queryset=ProductOrder.objects.filter(done=False).prefetch_related(Prefetch('product',queryset=Product.objects.prefetch_related(Prefetch('ppic_process_related',queryset=Process.objects.prefetch_related(Prefetch('requirementmaterial_set',queryset=RequirementMaterial.objects.select_related('material'))).prefetch_related(Prefetch('requirementproduct_set',queryset=RequirementProduct.objects.select_related('product'))).prefetch_related('warehouseproduct_set')))))))
        
        store_product = {}
        data = {}
        recommend_seriz = []
        for so in sales_order:
            for po in so.productorder_set.all():
                if po.product in store_product:
                    store_product[po.product] += po.ordered
                else:
                    store_product[po.product] = po.ordered 


        for product in store_product:
            self.search(data,product,store_product[product])
        
        for material in data:
                data[material]['quantity'] -= material.warehousematerial.quantity

        for each_material in data:
            each_seriz = {
                    "material":each_material,
                    "quantity":data[each_material]["quantity"],
                    "detailmrp_set":[
                        {
                            "product":k,
                            "quantity":v['quantity'],
                            "quantity_production":v['quantity_production']
                        } 
                            for k,v in data[each_material]["detail"].items()]
                    }
            recommend_seriz.append(each_seriz)
        
        
        mrp_seriz = MrpReadOnlySerializer(recommend_seriz,many=True)

        return  Response(mrp_seriz.data)

    def search(self,data,product,quantity):
        

        for process in product.ppic_process_related.order_by('-order'):

            for wh_product in process.warehouseproduct_set.all():
                quantity -= wh_product.quantity 
            
            for req_product in process.requirementproduct_set.all():
                self.search(data,req_product.product,quantity)

            for req_material in process.requirementmaterial_set.all():
                
                qty_req_material = ceil(quantity/req_material.output) * req_material.input

                if req_material.material in data:
                    data[req_material.material]['quantity'] += qty_req_material
                else:
                    data[req_material.material] = { 'quantity' : qty_req_material }
                
                if 'detail' in data[req_material.material]:
                    
                    if product in data[req_material.material]['detail']:
                        data[req_material.material]['detail'][product]['quantity_production'] += quantity
                        data[req_material.material]['detail'][product]['quantity'] += qty_req_material
                    else:
                         data[req_material.material]['detail'][product] = {
                            'quantity_production':quantity,
                            'quantity':qty_req_material
                            }
                else:
                    data[req_material.material]['detail'] = { product : {
                            'quantity_production':quantity,
                            'quantity':qty_req_material
                            } }
        

class WarehouseFinishGoodViewSet(GetModelViewSet):
    '''
    warehouse type (finish good) -> warehouse product -> product
    '''
    serializer_class = WarehouseTypeReadOnlySerializer
    permission_classes = [AllowAny]
    queryset = WarehouseType.objects.prefetch_related(
        Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.select_related('process__process_type','process__product').select_related('product__customer','product__type'))).filter(Q(id=1))

class WarehouseScrapMaterialViewSet():
    '''
    class for warehouse scrap material
    '''
    pass


class WarehouseSubcontViewSet(GetModelViewSet):
    '''
    warehouse type (subcont) -> warehouse product -> product
    '''
    serializer_class = WarehouseTypeReadOnlySerializer
    permission_classes = [AllowAny]
    queryset = WarehouseType.objects.prefetch_related(
        Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.select_related('process__process_type','process__product').select_related('product__customer','product__type').filter(Q(quantity__gt=0)))).filter(Q(id=2))

class WarehouseWipViewSet(GetModelViewSet):
    '''
    warehouse type (wip) -> warehouse product -> product
    '''
    serializer_class = WarehouseTypeReadOnlySerializer
    permission_classes = [AllowAny]
    queryset = WarehouseType.objects.prefetch_related(
        Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.select_related('process__process_type','process__product').select_related('product__customer','product__type'))).filter(Q(id__gt=2))

    
class WarehouseProductManagementViewSet(UpdateModelViewSet):
    '''
    management edit stock warehouse product eg: wip, finishgood, subcont
    '''
    serializer_class = WarehouseProductManagementSerializer
    permission_classes = [AllowAny]
    queryset = WarehouseProduct.objects.all()

class WarehouseMaterialManagementViewSet(UpdateModelViewSet):
    '''
    management edit stock warehouse material
    '''
    serializer_class = WarehouseMaterialManagementSerializer
    permission_classes = [AllowAny]
    queryset = WarehouseMaterial.objects.all()


class UomWarehouseMaterialViewSet(ReadOnlyModelViewSet):
    '''
    uom -> material -> stock in warehouse material
    '''
    serializer_class = UomWarehouseMaterialSerializer
    permission_classes = [AllowAny]
    queryset = UnitOfMaterial.objects.prefetch_related(Prefetch('material_set',queryset=Material.objects.select_related('supplier','warehousematerial')))

class UomManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    management for unit of material
    '''
    serializer_class = UomManagementSerializer
    permission_classes = [AllowAny]
    queryset = UnitOfMaterial.objects.prefetch_related(Prefetch('material_set',queryset=Material.objects.select_related('supplier','warehousematerial')))

    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']
        uom = get_object_or_404(self.queryset,pk=pk)

        if uom.material_set.exists():
            raise ValidationError('Masih ada material yang memiliki unit tersebut')

        return super().destroy(request, *args, **kwargs)


class UomConversionReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    viewset for get and retrieve list of conversion uom
    '''
    serializer_class = ConversionUomReadOnlySerializer
    permission_classes = [AllowAny]
    queryset = ConversionUom.objects.select_related('uom_input','uom_output')


class UomConversionManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    viewset for management conversion of uom
    '''
    serializer_class = ConversionUomManagementSerializer
    permission_classes = [AllowAny]
    queryset = ConversionUom.objects.all()

class BasedConversionMaterialReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    viewset for get and retrieve list of based conversion material
    '''
    serializer_class = BasedConversionReadOnlySerializer
    permission_classes = [AllowAny]
    queryset = BasedConversionMaterial.objects.select_related('material_input__uom','material_input__supplier','material_output__uom','material_output__supplier')

class BasedConversionMaterialManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    viewset for management based conversion of material
    '''
    serializer_class = BasedConversionManagementSerializer
    permission_classes = [AllowAny]
    queryset = BasedConversionMaterial.objects.all()

class ReportConversionMaterialReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    viewset for get and retrieve list of conversion material reports
    '''
    serializer_class = ConversionMaterialReportReadOnlySerializer
    permission_classes = [AllowAny]
    queryset = ConversionMaterialReport.objects.select_related('material_input__uom','material_input__supplier','material_output__uom','material_output__supplier')

class ReportConversionMaterialManagementViewSet(CreateModelViewSet):
    '''
    viewset for management report conversion of material ie: shearing material
    '''
    serializer_class = ConversionMaterialReportManagementSerializer
    permission_classes = [AllowAny]
    queryset = ConversionMaterialReport.objects.all()
    










