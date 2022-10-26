from rest_framework.viewsets import ModelViewSet,ReadOnlyModelViewSet,CreateUpdateDeleteModelViewSet,UpdateModelViewSet,CreateModelViewSet,GetModelViewSet,CreateUpdateModelViewSet

from rest_framework.permissions import AllowAny
from rest_framework.serializers import ValidationError
from rest_framework.response import Response
from rest_framework.parsers import JSONParser,MultiPartParser,FormParser
from rest_framework.decorators import api_view
from rest_framework import status

from math import ceil
import functools
import time
from django.db import connection, reset_queries
from django.db.models import Prefetch,Q,Sum,F,Count
from django.shortcuts import get_object_or_404

import json

from manager.shortcuts import invalid
from ppic.models import *

from purchasing.models import Supplier
from .serializer import *
from .utils import MultipartJsonParser
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


class ProductListReadOnlyViewSet(ReadOnlyModelViewSet):
    serializer_class = ProductCustomerReadOnlySerializer
    queryset = Customer.objects.prefetch_related(
        Prefetch('ppic_product_related',queryset=Product.objects.prefetch_related(
            Prefetch('ppic_process_related',queryset=Process.objects.
            prefetch_related(
                Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.select_related('warehouse_type'))).
            prefetch_related(
                Prefetch('requirementproduct_set',queryset=RequirementProduct.objects.select_related('product'))).
            prefetch_related(
                Prefetch('requirementmaterial_set',queryset=RequirementMaterial.objects.select_related('material'))).select_related('process_type'))).select_related('type')))


class CustomerProductionListReadOnlyViewSet(ReadOnlyModelViewSet):
    serializer_class = ProductCustomerReadOnlySerializer
    queryset = Customer.objects.prefetch_related(
        Prefetch('ppic_product_related',queryset=Product.objects.prefetch_related(
            Prefetch('ppic_process_related',queryset=Process.objects.
            prefetch_related(
                Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.select_related('warehouse_type'))).
            prefetch_related(
                Prefetch('requirementproduct_set',queryset=RequirementProduct.objects.select_related('product'))).
            prefetch_related(
                Prefetch('requirementmaterial_set',queryset=RequirementMaterial.objects.select_related('material'))).select_related('process_type').exclude(process_type=2) )).select_related('type')))

class ProductDetailReadOnlyViewSet(ReadOnlyModelViewSet):
    serializer_class = ProductDetailSerializer
    queryset = Product.objects.prefetch_related(
            Prefetch('ppic_process_related',queryset=Process.objects.
            prefetch_related(
                Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.select_related('warehouse_type'))).
            prefetch_related(
                Prefetch('requirementproduct_set',queryset=RequirementProduct.objects.select_related('product'))).
            prefetch_related(
                Prefetch('requirementmaterial_set',queryset=RequirementMaterial.objects.select_related('material'))).select_related('process_type'))).prefetch_related(
                    Prefetch('ppic_productorder_related',queryset=ProductOrder.objects.select_related('sales_order').filter(done=False))).select_related('type').annotate(productordered=Sum('ppic_productorders__ordered')).annotate(productdelivered=Sum('ppic_productorders__delivered'))


class ProductTypeViewSet(ModelViewSet):
    '''
    a viewset for handling all request for product type things
    '''
    serializer_class = ProductTypeSerializer
    queryset = ProductType.objects.annotate(products=Count('product'))
    
    
    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']
        product_type = get_object_or_404(self.queryset,pk=pk)

        if product_type.product_set.exists():
            raise ValidationError('There is still product with this type in database')

        if product_type.id == 1 or product_type.id ==2:
            raise ValidationError('It is forbidden to delete the main type of production on the system')

        return super().destroy(request, *args, **kwargs)

class ProcessTypeViewSet(ModelViewSet):
    '''
    a viewset for handling all request for process type things
    '''
    serializer_class = ProcessTypeSerializer
    queryset = ProcessType.objects.annotate(amount_of_process=Count('process'))

    
    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']
        process_type = get_object_or_404(self.queryset,pk=pk)

        if process_type.process_set.exists():
            raise ValidationError('There is still process with this type in database')
        
        if process_type.id == 2 or process_type.id == 1:
            raise ValidationError("It is forbidden to delete the main production type on the system")

        return super().destroy(request, *args, **kwargs)


class ProductListViewSet(ReadOnlyModelViewSet):
    '''
    a viewset for handling request for list of products
    '''
    serializer_class = ProductListSerializer
    queryset = Product.objects.all()

class MaterialListViewSet(ReadOnlyModelViewSet):
    '''
    a viewset for handling request for list of materials
    '''
    serializer_class = MaterialListSerializer
    queryset = Material.objects.all()


class CustomerListViewSet(ReadOnlyModelViewSet):
    serializer_class = CustomerListSerializer
    queryset = Customer.objects.all()

class ProductManagementViewSet(CreateUpdateDeleteModelViewSet):
    serializer_class = ProductManagementSerializer
    parser_classes = [MultipartJsonParser]
    queryset = Product.objects.prefetch_related(
            Prefetch('ppic_process_related',queryset=Process.objects.
            prefetch_related(
                Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.select_related('warehouse_type'))).
            prefetch_related(
                Prefetch('requirementproduct_set',queryset=RequirementProduct.objects.select_related('product'))).
            prefetch_related(
                Prefetch('requirementmaterial_set',queryset=RequirementMaterial.objects.select_related('material'))).select_related('process_type'))).select_related('type')

    def fields_check(self,data):
        
        process = data.get('ppic_process_related',[])

        for process in process:
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

class MaterialSupplierReadOnlyViewSet(ReadOnlyModelViewSet):
    serializer_class = MaterialSupplierReadOnlySerializer
    queryset = Supplier.objects.prefetch_related(Prefetch('ppic_material_related',queryset=Material.objects.prefetch_related(Prefetch('ppic_requirementmaterial_related',queryset=RequirementMaterial.objects.select_related('process__product','process__process_type'))).select_related('warehousematerial').select_related('uom') ))

class UomListViewSet(ReadOnlyModelViewSet):
    serializer_class = UomListSerializer
    queryset = UnitOfMaterial.objects.annotate(materials=Count('material'))

class SupplierListViewSet(ReadOnlyModelViewSet):
    serializer_class = SupplierListSerializer
    queryset = Supplier.objects.all()


class MaterialDetailViewSet(ReadOnlyModelViewSet):
    serializer_class = MaterialDetailSerializer
    queryset = Material.objects.prefetch_related(
        Prefetch('ppic_requirementmaterial_related',queryset=RequirementMaterial.objects.select_related('process__product'))).select_related('warehousematerial')

class MaterialViewSet(ModelViewSet):
    serializer_class = MaterialSerializer
    queryset = Material.objects.prefetch_related('ppic_requirementmaterial_related').select_related('warehousematerial')

    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']
        instances = self.queryset
        instance = get_object_or_404(instances,pk=pk)

        req_material = instance.ppic_requirementmaterial_related.all()
        wh_material = instance.warehousematerial

        if len(req_material) > 0:
            raise ValidationError('Tidak bisa menghapus data material yang menjadi kebutuhan produksi')
        if wh_material.quantity > 0:
            raise ValidationError('Tidak bisa menghapus data material yang memiliki stok di gudang')
        return super().destroy(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        
        instance = self.get_object()
        image  = request.data.get('image',None)
        if image is not None and image =='':
            instance.image.delete(save=True)
            
        
        return super().update(request, *args, **kwargs)

class RequirementMaterialViewSet(CreateUpdateDeleteModelViewSet):
    serializer_class = RequirementMaterialManagement
    queryset = RequirementMaterial.objects.all()

class RequirementProductViewSet(CreateUpdateDeleteModelViewSet):
    serializer_class = RequirementProductManagement
    queryset = RequirementProduct.objects.all()


class MrpReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    get mrp
    '''
    serializer_class = MrpReadOnlySerializer
    queryset = MaterialRequirementPlanning.objects.prefetch_related(
        Prefetch('detailmrp_set',queryset=DetailMrp.objects.select_related('product'))).select_related('material','material__supplier','material__uom')


    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

class MrpManagementViewSet(ModelViewSet):
    '''
    list : for mrp recommendations
    create , update , delete : mrp -> detail mrp
    '''
    serializer_class = MrpManagementSerializer
    queryset = MaterialRequirementPlanning.objects.all()
    data = {}

    @queryDebug
    def list(self, request, *args, **kwargs):
        '''
        a list for material requirement planning recommendation in material page 
        '''

        sales_order = SalesOrder.objects.filter(fixed=True,done=False).prefetch_related(
            Prefetch('productorder_set',queryset=ProductOrder.objects.filter(done=False).select_related('product').prefetch_related('product__ppic_process_related')))
        
                
        productList = Product.objects.prefetch_related(
            Prefetch('ppic_process_related',queryset=Process.objects.select_related('product','process_type').prefetch_related(
                Prefetch('requirementproduct_set',queryset=RequirementProduct.objects.select_related('product'))).prefetch_related(
                    Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.select_related('warehouse_type','product','process'))).prefetch_related(
                        Prefetch('requirementmaterial_set',queryset=RequirementMaterial.objects.select_related('material','material__supplier','material__uom','material__warehousematerial','process').prefetch_related(
                            Prefetch('material__ppic_materialorder_related',queryset=MaterialOrder.objects.filter(done=False,ordered__gt=F('arrived')).select_related('material','purchase_order_material'))).prefetch_related(
                                Prefetch('material__ppic_materialrequirementplanning_related',queryset=MaterialRequirementPlanning.objects.select_related('material').prefetch_related(
                                    Prefetch('detailmrp_set',queryset=DetailMrp.objects.select_related('product','mrp'))))))).order_by('-order'))).select_related('type','customer')


        dataProducts = {}

        for product in productList:
            ppic_process_related = []

            for process in product.ppic_process_related.all():
                
                tempProcess = {}
                req_products = []
                req_materials = []
                warehouseproducts = []

                for reqProduct in process.requirementproduct_set.all():
                    tempReqProduct = {}
                    tempReqProduct['id'] = reqProduct.id
                    tempReqProduct['product'] = reqProduct.product.id
                    tempReqProduct['input'] = reqProduct.input
                    tempReqProduct['output'] = reqProduct.output
                    
                    req_products.append(tempReqProduct)

                for whProduct in process.warehouseproduct_set.all():
                    tempWhProduct = {}
                    tempWhProduct['id'] = whProduct.id
                    tempWhProduct['quantity'] = whProduct.quantity
                    tempWhProduct['warehouse_type'] = whProduct.warehouse_type

                    warehouseproducts.append(tempWhProduct)

                for reqMaterial in process.requirementmaterial_set.all():
                    tempReqMaterial = {}
                    ppic_materialorder_related = []
                    ppic_materialrequirementplanning_related = []

                    for materialOrder in reqMaterial.material.ppic_materialorder_related.all():
                        tempMaterialOrder = {}
                        tempMaterialOrder['id'] = materialOrder.id
                        tempMaterialOrder['ordered'] = materialOrder.ordered
                        tempMaterialOrder['arrived'] = materialOrder.arrived
                        tempMaterialOrder['material'] = materialOrder.material
                        tempMaterialOrder['purchase_order_material'] = materialOrder.purchase_order_material
                        tempMaterialOrder['done'] = materialOrder.done

                        ppic_materialorder_related.append(tempMaterialOrder)

                    for mrp in reqMaterial.material.ppic_materialrequirementplanning_related.all():
                        detailmrp_set = []
                        for detMrp in mrp.detailmrp_set.all():
                            tempDetMrp = {}
                            tempDetMrp['id'] = detMrp.id
                            tempDetMrp['quantity'] = detMrp.quantity
                            tempDetMrp['quantity_production'] = detMrp.quantity_production
                            tempDetMrp['mrp'] = detMrp.mrp
                            tempDetMrp['product'] = detMrp.product

                            detailmrp_set.append(tempDetMrp)
                        
                        tempMrp = {}
                        tempMrp['quantity'] = mrp.quantity
                        tempMrp['id'] = mrp.id
                        tempMrp['created'] = mrp.created
                        tempMrp['last_update'] = mrp.last_update
                        tempMrp['detailmrp_set'] = detailmrp_set
                        tempMrp['material'] = mrp.material

                        ppic_materialrequirementplanning_related.append(tempMrp)

                    tempReqMaterial['id'] = reqMaterial.id
                    tempReqMaterial['process'] = reqMaterial.process
                    tempReqMaterial['input'] = reqMaterial.input
                    tempReqMaterial['output'] = reqMaterial.output
                    tempReqMaterial['material'] = {
                        'instance':reqMaterial.material,
                        'id':reqMaterial.material.id,
                        'name':reqMaterial.material.name,
                        'image':reqMaterial.material.image,
                        'spec':reqMaterial.material.spec,
                        'length':reqMaterial.material.length,
                        'width':reqMaterial.material.width,
                        'thickness':reqMaterial.material.thickness,
                        'uom':reqMaterial.material.uom,
                        'supplier':reqMaterial.material.supplier,
                        'created':reqMaterial.material.created,
                        'last_update':reqMaterial.material.last_update,
                        'ppic_materialorder_related': ppic_materialorder_related,
                        'ppic_materialrequirementplanning_related' : ppic_materialrequirementplanning_related,
                        'warehousematerial':reqMaterial.material.warehousematerial
                    }

                    req_materials.append(tempReqMaterial)

                tempProcess['id'] = process.id
                tempProcess['product'] = product.id
                tempProcess['process_name'] = process.process_name
                tempProcess['order'] = process.order
                tempProcess['process_type'] = process.process_type
                tempProcess['requirementproduct_set'] = req_products
                tempProcess['warehouseproduct_set'] = warehouseproducts
                tempProcess['requirementmaterial_set'] = req_materials

                ppic_process_related.append(tempProcess)


            dataProducts[product.id]  = {
                'instance':product,
                'id':product.id,
                'code':product.code,
                'name':product.name,
                'weight':product.weight,
                'image':product.image,
                'process':product.process,
                'price':product.price,
                'customer':product.customer,
                'type':product.type,
                'created':product.created,
                'last_update':product.last_update,
                'ppic_process_related' : ppic_process_related
            }

        store_product_ordered = {}
        store_product = {}
        data = {}
        recommend_seriz = []
        for so in sales_order:
            for po in so.productorder_set.all():
                if po.product.id in store_product_ordered:
                    store_product_ordered[po.product.id] += (po.ordered - po.delivered)
                else:
                    store_product_ordered[po.product.id] = (po.ordered - po.delivered) 

        for k,v in store_product_ordered.items():
            self.searchNestedProduction(store_product,k,v,dataProducts)

        for k,v in store_product.items():
            self.search(data,k,v,dataProducts)
        
        for k,v in list(data.items()):
                # k is map to each material
                readyStockAndOrderedMaterials = v['warehousematerial'].quantity
                inRequestMaterials = 0

                for material_order in v['ppic_materialorder_related']:
                    readyStockAndOrderedMaterials += (material_order['ordered']- material_order['arrived'])
                
                for requestMaterial in v['ppic_materialrequirementplanning_related']:
                    
                    for detailmrp in requestMaterial['detailmrp_set']:
                        if detailmrp['product'] in v['detail']:

                            v['detail'][detailmrp['product']]['quantity_production'] -= detailmrp['quantity_production']
                            v['detail'][detailmrp['product']]['quantity'] -= detailmrp['quantity']
                            
                            if v['detail'][detailmrp['product']]['quantity_production'] <=0 or v['detail'][detailmrp['product']]['quantity'] <= 0  :
                                v['detail'].pop(detailmrp['product'])
                                continue


                    inRequestMaterials += requestMaterial['quantity']

                v['quantity'] -= (readyStockAndOrderedMaterials + inRequestMaterials)
                
                if v['quantity'] <= 0:
                    del data[k]

        for key,value in data.items():
            each_seriz = {
                    "material":value['instance'],
                    "quantity":value['quantity'],
                    "detailmrp_set":[
                        {
                            "product":k,
                            "quantity":v['quantity'],
                            "quantity_production":v['quantity_production']
                        } 
                            for k,v in value["detail"].items()]
                    }
            recommend_seriz.append(each_seriz)
        
        
        mrp_seriz = MrpReadOnlySerializer(recommend_seriz,many=True)

        return  Response(mrp_seriz.data)

    def searchNestedProduction(self,data,idProduct,quantity,dataProducts):
        
        product = dataProducts[idProduct]

        if idProduct in data:
            data[idProduct] += quantity
        else:
            data[idProduct] = quantity

        for process in product['ppic_process_related']:

            for wh_product in process['warehouseproduct_set']:
                quantity -= wh_product['quantity'] 
            
            for req_product in process['requirementproduct_set']:
                qty_production = ceil(quantity/req_product['output']) * req_product['input']
                idProductSearch = req_product['product']
                
                self.searchNestedProduction(data,idProductSearch,qty_production,dataProducts)


    def search(self,data,idProduct,quantity,dataProducts):
        
        product = dataProducts[idProduct]
        instanceProduct = dataProducts[idProduct]['instance']

        for process in product['ppic_process_related']:

            for wh_product in process['warehouseproduct_set']:
                quantity -= wh_product['quantity'] 

            for req_material in process['requirementmaterial_set']:
                
                qty_req_material = ceil(quantity/req_material['output']) * req_material['input']

                if req_material['material']['id'] in data:
                    data[req_material['material']['id']]['quantity'] += qty_req_material
                else:
                    data[req_material['material']['id']] = req_material['material']
                    data[req_material['material']['id']]['quantity'] = qty_req_material
                
                if idProduct ==8:
                    print(qty_req_material)

                if 'detail' in data[req_material['material']['id']]:
                    
                    if instanceProduct in data[req_material['material']['id']]['detail']:
                        data[req_material['material']['id']]['detail'][instanceProduct]['quantity_production'] += quantity
                        data[req_material['material']['id']]['detail'][instanceProduct]['quantity'] += qty_req_material
                    else:
                         data[req_material['material']['id']]['detail'][instanceProduct] = {
                            'quantity_production':quantity,
                            'quantity':qty_req_material
                            }
                else:
                    data[req_material['material']['id']]['detail'] = { instanceProduct : {
                            'quantity_production':quantity,
                            'quantity':qty_req_material
                            } }
        

class WarehouseFinishGoodViewSet(GetModelViewSet):
    '''
    warehouse type (finish good) -> warehouse product -> product
    '''
    serializer_class = WarehouseTypeReadOnlySerializer
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
    queryset = WarehouseType.objects.prefetch_related(
        Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.select_related('process__process_type','process__product').select_related('product__customer','product__type').filter(Q(quantity__gt=0)))).filter(Q(id=2))

class WarehouseWipViewSet(GetModelViewSet):
    '''
    warehouse type (wip) -> warehouse product -> product
    '''
    serializer_class = WarehouseTypeReadOnlySerializer
    queryset = WarehouseType.objects.prefetch_related(
        Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.select_related('process__process_type','process__product').select_related('product__customer','product__type'))).filter(Q(id__gt=2))

    
class WarehouseProductManagementViewSet(UpdateModelViewSet):
    '''
    management edit stock warehouse product eg: wip, finishgood, subcont
    '''
    serializer_class = WarehouseProductManagementSerializer
    queryset = WarehouseProduct.objects.all()

class WarehouseMaterialManagementViewSet(UpdateModelViewSet):
    '''
    management edit stock warehouse material
    '''
    serializer_class = WarehouseMaterialManagementSerializer
    queryset = WarehouseMaterial.objects.all()


class UomWarehouseMaterialViewSet(ReadOnlyModelViewSet):
    '''
    uom -> material -> stock in warehouse material
    '''
    serializer_class = UomWarehouseMaterialSerializer
    queryset = UnitOfMaterial.objects.prefetch_related(Prefetch('material_set',queryset=Material.objects.select_related('supplier','warehousematerial'))).annotate(amount_of_material=Count('material'))

class UomManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    management for unit of material
    '''
    serializer_class = UomManagementSerializer
    queryset = UnitOfMaterial.objects.prefetch_related(Prefetch('material_set',queryset=Material.objects.select_related('supplier','warehousematerial')))

    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']
        uom = get_object_or_404(self.queryset,pk=pk)

        if uom.material_set.exists():
            raise ValidationError('There is still material with this unit in database')

        return super().destroy(request, *args, **kwargs)


class UomConversionReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    viewset for get and retrieve list of conversion uom
    '''
    serializer_class = ConversionUomReadOnlySerializer
    queryset = ConversionUom.objects.select_related('uom_input','uom_output')


class UomConversionManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    viewset for management conversion of uom
    '''
    serializer_class = ConversionUomManagementSerializer
    queryset = ConversionUom.objects.all()

class BasedConversionMaterialReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    viewset for get and retrieve list of based conversion material
    '''
    serializer_class = BasedConversionReadOnlySerializer
    queryset = BasedConversionMaterial.objects.select_related('material_input__uom','material_input__supplier','material_output__uom','material_output__supplier')

class BasedConversionMaterialManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    viewset for management based conversion of material
    '''
    serializer_class = BasedConversionManagementSerializer
    queryset = BasedConversionMaterial.objects.all()

class ReportConversionMaterialReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    viewset for get and retrieve list of conversion material reports
    '''
    serializer_class = ConversionMaterialReportReadOnlySerializer
    queryset = ConversionMaterialReport.objects.select_related('material_input__uom','material_input__supplier','material_output__uom','material_output__supplier').order_by('-created')

class ReportConversionMaterialManagementViewSet(CreateModelViewSet):
    '''
    viewset for management report conversion of material ie: shearing material
    '''
    serializer_class = ConversionMaterialReportManagementSerializer
    queryset = ConversionMaterialReport.objects.all()
    

class MaterialOrderReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    a viewset for get material order list
    '''
    serializer_class = MaterialOrderReadOnlySerializer
    queryset = MaterialOrder.objects.select_related('material','material__uom','material__supplier','purchase_order_material','purchase_order_material__supplier').filter(done=False)



    
class MaterialReceiptScheduleReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    a read only view set for schedule material receipt
    '''
    serializer_class = MaterialReceiptScheduleReadOnlySerializer
    queryset = MaterialReceiptSchedule.objects.select_related('material_order','material_order__material','material_order__purchase_order_material','material_order__material__supplier','material_order__purchase_order_material__supplier').filter(Q(fulfilled_quantity__lte=0)&Q(material_order__done=False)).order_by('date')

class DeliveryNoteMaterialReadOnlyViewSet(ReadOnlyModelViewSet):
    serializer_class = DeliveryNoteMaterialReadOnlySerializer
    queryset = DeliveryNoteMaterial.objects.prefetch_related(
            Prefetch('materialreceipt_set',queryset=MaterialReceipt.objects.select_related('material_order','material_order__material','material_order__purchase_order_material'))).select_related('supplier')



class DeliveryNoteMaterialManagementViewSet(CreateUpdateDeleteModelViewSet):
    serializer_class = DeliveryNoteMaterialManagementSerializer
    queryset = DeliveryNoteMaterial.objects.all()

    def update(self, request, *args, **kwargs):
        
        instance = self.get_object()
        image  = request.data.get('image',None)
        if image is not None and image =='':
            instance.image.delete(save=True)
        
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']
        instance_dn_material = get_object_or_404(self.queryset,pk=pk)
        
        if instance_dn_material.materialreceipt_set.exists():
            invalid()
        
        return super().destroy(request, *args, **kwargs)

class MaterialReceiptManagementViewSet(CreateUpdateDeleteModelViewSet):
    serializer_class = MaterialReceiptManagementSerializer
    queryset = MaterialReceipt.objects.all()

    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']
        instance_mr = get_object_or_404(self.queryset,pk=pk)
        
        if instance_mr.quantity > 0:
            invalid()
        
        return super().destroy(request, *args, **kwargs)


class DeliveryNoteCustomerReadOnlyViewSet(ReadOnlyModelViewSet):
    serializer_class = CustomerDeliveryNoteReadOnlySerializer
    queryset = Customer.objects.prefetch_related(
        Prefetch('ppic_deliverynotecustomer_related',queryset=DeliveryNoteCustomer.objects.prefetch_related(
            Prefetch('productdelivercustomer_set',queryset=ProductDeliverCustomer.objects.select_related('product_order','product_order__product','product_order__sales_order')))))

class DeliveryNoteCustomerManagementViewSet(CreateUpdateDeleteModelViewSet):
    serializer_class = DeliveryNoteCustomerManagementSerializer
    queryset = DeliveryNoteCustomer.objects.all()

    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']
        instance_dn_customer = get_object_or_404(self.queryset,pk=pk)
        if instance_dn_customer.producdelivercustomer_set.exists():
            invalid()

        return super().destroy(request, *args, **kwargs)


class ProductDeliverManagementViewSet(CreateUpdateDeleteModelViewSet):
    serializer_class = ProductDeliverCustomerManagementSerializer
    queryset = ProductDeliverCustomer.objects.all()

    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']
        instance_pd = get_object_or_404(self.queryset,pk=pk)
        if instance_pd.quantity > 0 or instance_pd.paid is True:
            invalid()

        return super().destroy(request, *args, **kwargs)

class MachineViewSet(ModelViewSet):
    serializer_class = MachineSerializer
    queryset = Machine.objects.all()

    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']
        instance = get_object_or_404(self.queryset,pk=pk)
        if instance.productionreport_set.exists():
            invalid()

        return super().destroy(request, *args, **kwargs)

class OperatorViewSet(ModelViewSet):
    serializer_class = OperatorSerializer
    queryset = Operator.objects.all()

    def destroy(self, request, *args, **kwargs):

        pk = kwargs['pk']
        instance = get_object_or_404(self.queryset,pk=pk)
        if instance.productionreport_set.exists():
            invalid()

        return super().destroy(request, *args, **kwargs)


class ProductionReportReadOnlyViewSet(ReadOnlyModelViewSet):
    serializer_class = ProductionReportReadOnlySerializer
    queryset = ProductionReport.objects.all()


class ProductionPriorityViewSet(ReadOnlyModelViewSet):
    serializer_class = ProductSerializer
    queryset = Product.objects.all()

    
    @queryDebug
    def list(self, request, *args, **kwargs):

        sales_order = SalesOrder.objects.filter(fixed=True,done=False).prefetch_related(
            Prefetch('productorder_set',queryset=ProductOrder.objects.filter(done=False).select_related('product').prefetch_related('product__ppic_process_related')))

        process_type_subcont = ProcessType.objects.get(pk=2)
        
        productList = Product.objects.prefetch_related(
            Prefetch('ppic_process_related',queryset=Process.objects.select_related('product','process_type').prefetch_related(
                Prefetch('requirementproduct_set',queryset=RequirementProduct.objects.select_related('product','product__customer','product__type','process').prefetch_related(Prefetch('product__ppic_warehouseproduct_related',queryset=WarehouseProduct.objects.select_related('warehouse_type','product','process'))))).prefetch_related(
                    Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.select_related('warehouse_type','product','process'))).prefetch_related(
                        Prefetch('requirementmaterial_set',queryset=RequirementMaterial.objects.select_related('material','material__supplier','material__uom','material__warehousematerial','process'))).exclude(process_type=process_type_subcont).order_by('-order'))).select_related('type','customer')

        dataProduct = {}
        productOrdered = {}
        productionPriority = []
        storageProduct = {}

        for product in productList:
            ppic_process_related = []

            for process in product.ppic_process_related.all():
                
                tempProcess = {}
                req_products = []
                req_materials = []
                warehouseproducts = []

                for reqProduct in process.requirementproduct_set.all():
                    tempReqProduct = {}
                    tempReqProduct['id'] = reqProduct.id
                    tempReqProduct['product'] = reqProduct.product
                    tempReqProduct['idProduct'] = reqProduct.product.id
                    tempReqProduct['input'] = reqProduct.input
                    tempReqProduct['output'] = reqProduct.output
                    
                    req_products.append(tempReqProduct)

                for whProduct in process.warehouseproduct_set.all():
                    tempWhProduct = {}
                    tempWhProduct['id'] = whProduct.id
                    tempWhProduct['quantity'] = whProduct.quantity
                    tempWhProduct['warehouse_type'] = whProduct.warehouse_type

                    warehouseproducts.append(tempWhProduct)

                for reqMaterial in process.requirementmaterial_set.all():
                    tempReqMaterial = {}

                    tempReqMaterial['id'] = reqMaterial.id
                    tempReqMaterial['process'] = reqMaterial.process
                    tempReqMaterial['input'] = reqMaterial.input
                    tempReqMaterial['output'] = reqMaterial.output
                    tempReqMaterial['material'] = reqMaterial.material
                    tempReqMaterial['idMaterial'] = reqMaterial.material.id

                    req_materials.append(tempReqMaterial)

                tempProcess['id'] = process.id
                tempProcess['product'] = product
                tempProcess['process_name'] = process.process_name
                tempProcess['order'] = process.order
                tempProcess['process_type'] = process.process_type
                tempProcess['requirementproduct_set'] = req_products
                tempProcess['warehouseproduct_set'] = warehouseproducts
                tempProcess['requirementmaterial_set'] = req_materials

                ppic_process_related.append(tempProcess)


            dataProduct[product.id]  = {
                'id':product.id,
                'code':product.code,
                'name':product.name,
                'weight':product.weight,
                'image':product.image,
                'process':product.process,
                'price':product.price,
                'customer':product.customer,
                'type':product.type,
                'created':product.created,
                'last_update':product.last_update,
                'ppic_process_related' : ppic_process_related
            }


        for so in sales_order:
            for po in so.productorder_set.all():
                if po.product.id in productOrdered:
                    productOrdered[po.product.id] += (po.ordered - po.delivered)
                else:
                    productOrdered[po.product.id] = (po.ordered - po.delivered)

        for k,v in productOrdered.items():
            self.recursiveSearchRequirementProduct(storageProduct,dataProduct,v,k)

        for k,v in storageProduct.items():
            self.search(productionPriority,dataProduct,v,k)

        prioritySeriz = ProductSerializer(productionPriority,many=True)
        return Response(prioritySeriz.data)

    def recursiveSearchRequirementProduct(self,storageProducts,productList,quantity,idProduct):
        product = productList[idProduct]

        if idProduct in storageProducts:
            storageProducts[idProduct] += quantity
        else:
            storageProducts[idProduct] = quantity

        for process in product['ppic_process_related']:
            
            for whProduct in process['warehouseproduct_set']:
                quantity -= whProduct['quantity']

            for reqProduct in process['requirementproduct_set']:
                reqProductQtyProduction = ceil(quantity/reqProduct['output']) * reqProduct['input']
                self.recursiveSearchRequirementProduct(storageProducts,productList,reqProductQtyProduction,reqProduct['idProduct'])
    

    def search(self,storage,productList,quantity,idProduct):
        product = productList[idProduct]
        
        for process in product['ppic_process_related']:

            for whProduct in process['warehouseproduct_set']:
                quantity -= whProduct['quantity']
                
            process['production_quantity'] = quantity

        storage.append(product)

class ProductionReportManagementViewSet(CreateUpdateDeleteModelViewSet):
    serializer_class = ProductionReportManagementSerializer
    queryset = ProductionReport.objects.prefetch_related('materialproductionreport_set').prefetch_related('productproductionreport_set')
    
    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']
        instance_pr = get_object_or_404(self.queryset,pk=pk)

        if instance_pr.quantity > 0 or instance_pr.quantity_not_good > 0:
            invalid()
        
        for material_report in instance_pr.materialproductionreport_set.all():
            if material_report.quantity > 0:
                invalid()
        
        for product_report in instance_pr.productproductionreport_set.all():
            if product_report.quantity > 0:
                invalid()

        return super().destroy(request, *args, **kwargs)

