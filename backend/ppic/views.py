from rest_framework.viewsets import ModelViewSet,ReadOnlyModelViewSet,CreateUpdateDeleteModelViewSet,UpdateModelViewSet,CreateModelViewSet,GetModelViewSet

from rest_framework.response import Response
from rest_framework import status

from math import ceil
import functools
import time
from django.db import connection, reset_queries
from django.db.models import Prefetch,Q,Sum,F,Count
from django.shortcuts import get_object_or_404
from dateutil import rrule

from manager.shortcuts import invalid
from ppic.models import *

from purchasing.models import Supplier
from .serializer import *
from .utils import MultipartJsonParser
from marketing.models import Customer, SalesOrder
from .permissions import PpicPermission,CanManageWarehouse,CanManageDelivery,CanManageMaterial,CanManageProduct,CanManageProduction


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
    permission_classes = [PpicPermission]
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


class ProductionListViewSet(ReadOnlyModelViewSet):
    permission_classes = [PpicPermission]
    serializer_class = ProductReadOnlySerializer
    queryset = Product.objects.prefetch_related(
            Prefetch('ppic_process_related',queryset=Process.objects.
            prefetch_related(
                Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.select_related('warehouse_type'))).
            prefetch_related(
                Prefetch('requirementproduct_set',queryset=RequirementProduct.objects.select_related('product','product__customer','product__type').prefetch_related(
                    Prefetch('product__ppic_warehouseproduct_related',queryset=WarehouseProduct.objects.select_related('warehouse_type').filter(warehouse_type=1))))).
            prefetch_related(
                Prefetch('requirementmaterial_set',queryset=RequirementMaterial.objects.select_related('material','material__uom','material__supplier','material__warehousematerial'))).select_related('process_type').exclude(process_type=2))).select_related('type','customer')

class ProductDetailReadOnlyViewSet(ReadOnlyModelViewSet):
    permission_classes = [PpicPermission]
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

class ProductTypeManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a viewset for cud product type
    '''
    permission_classes = [PpicPermission,CanManageProduct]
    serializer_class = ProductTypeSerializer
    queryset = ProductType.objects.all()
    
    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']
        product_type = get_object_or_404(self.queryset,pk=pk)

        if product_type.product_set.exists():
            invalid('There is still product with this type in database')

        if product_type.id == 1 or product_type.id ==2:
            invalid('It is forbidden to delete the main type of production on the system')

        return super().destroy(request, *args, **kwargs)

class ProductTypeViewSet(ReadOnlyModelViewSet):
    '''
    a viewset for handling all request for product type things
    '''
    permission_classes = [PpicPermission]
    serializer_class = ProductTypeSerializer
    queryset = ProductType.objects.annotate(products=Count('product'))
    

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



class ProcessTypeViewSet(ReadOnlyModelViewSet):
    '''
    a viewset for get and retrieve process type
    '''
    permission_classes = [PpicPermission]
    serializer_class = ProcessTypeSerializer
    queryset = ProcessType.objects.annotate(amount_of_process=Count('process'))

class ProductListViewSet(ReadOnlyModelViewSet):
    '''
    a viewset for handling request for list of products
    '''
    permission_classes = [PpicPermission]
    serializer_class = ProductListSerializer
    queryset = Product.objects.select_related('customer','type')

class ProductOrderedViewSet(ReadOnlyModelViewSet):
    '''
    a viewset for request list of product there is still have an upcoming product delivery
    '''
    permission_classes = [PpicPermission]
    serializer_class = ProductListSerializer
    permission_classes=[PpicPermission]
    queryset = Product.objects.select_related('customer','type').prefetch_related(Prefetch(
        'ppic_productorder_related',queryset=ProductOrder.objects.select_related('sales_order','product'))).filter(Q(ppic_productorders__sales_order__fixed=True)&Q(ppic_productorders__ordered__gt=F('ppic_productorders__delivered'))&Q(ppic_productorders__sales_order__done=False)).annotate(rest_order=Sum(
            'ppic_productorders__ordered')-Sum('ppic_productorders__delivered')).filter(Q(rest_order__isnull=False))

class MaterialOrderedViewSet(ReadOnlyModelViewSet):
    '''
    a viewset for request list of material there is still have an upcoming material receipt
    '''
    permission_classes = [PpicPermission]
    serializer_class = MaterialListSerializer
    queryset = Material.objects.prefetch_related(
        Prefetch(
            'ppic_requirementmaterial_related',queryset=RequirementMaterial.objects.select_related('process','process__process_type','process__product'))).select_related('warehousematerial','uom','supplier').filter(ppic_materialorders__done=False,ppic_materialorders__ordered__gt=F('ppic_materialorders__arrived'),ppic_materialorders__purchase_order_material__done=False).annotate(rest_arrival=Sum(
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



class MaterialListViewSet(ReadOnlyModelViewSet):
    '''
    a viewset for handling request for list of materials
    '''
    permission_classes = [PpicPermission]
    serializer_class = MaterialListSerializer
    queryset = Material.objects.prefetch_related(
        Prefetch('ppic_requirementmaterial_related',queryset=RequirementMaterial.objects.select_related('process','process__process_type','process__product'))).select_related('warehousematerial','uom','supplier')


class CustomerListViewSet(ReadOnlyModelViewSet):
    permission_classes = [PpicPermission]
    serializer_class = CustomerListSerializer
    queryset = Customer.objects.all()

class ProductManagementViewSet(CreateUpdateDeleteModelViewSet):
    permission_classes = [PpicPermission,CanManageProduct]
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

class MaterialSupplierReadOnlyViewSet(ReadOnlyModelViewSet):
    permission_classes = [PpicPermission]
    serializer_class = MaterialSupplierReadOnlySerializer
    queryset = Supplier.objects.prefetch_related(Prefetch('ppic_material_related',queryset=Material.objects.prefetch_related(Prefetch('ppic_requirementmaterial_related',queryset=RequirementMaterial.objects.select_related('process__product','process__process_type'))).select_related('warehousematerial').select_related('uom') ))

class UomListViewSet(ReadOnlyModelViewSet):
    permission_classes = [PpicPermission]
    serializer_class = UomListSerializer
    queryset = UnitOfMaterial.objects.annotate(materials=Count('material'))

class SupplierListViewSet(ReadOnlyModelViewSet):
    permission_classes = [PpicPermission]
    serializer_class = SupplierListSerializer
    queryset = Supplier.objects.all()


class MaterialDetailViewSet(ReadOnlyModelViewSet):
    permission_classes = [PpicPermission]
    serializer_class = MaterialDetailSerializer
    queryset = Material.objects.prefetch_related(
        Prefetch('ppic_requirementmaterial_related',queryset=RequirementMaterial.objects.select_related('process__product'))).select_related('warehousematerial')

class MaterialManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a view set for cud data material
    '''
    permission_classes = [PpicPermission,CanManageMaterial]
    serializer_class = MaterialSerializer
    queryset = Material.objects.prefetch_related('ppic_requirementmaterial_related').select_related('warehousematerial')

    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']
        instances = self.queryset
        instance = get_object_or_404(instances,pk=pk)

        req_material = instance.ppic_requirementmaterial_related.all()
        wh_material = instance.warehousematerial

        if len(req_material) > 0:
            invalid('Cannot delete material that are still use in production')
        if wh_material.quantity > 0:
            invalid('Cannot delete material that still have stock in warehouse')
        return super().destroy(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        
        instance = self.get_object()
        image  = request.data.get('image',None)
        if image is not None and image =='':
            instance.image.delete(save=True)
        
        return super().update(request, *args, **kwargs)

class MaterialViewSet(ReadOnlyModelViewSet):
    permission_classes = [PpicPermission]
    serializer_class = MaterialSerializer
    queryset = Material.objects.prefetch_related('ppic_requirementmaterial_related').select_related('warehousematerial')

class RequirementMaterialViewSet(CreateUpdateDeleteModelViewSet):
    permission_classes = [PpicPermission]
    serializer_class = RequirementMaterialManagement
    queryset = RequirementMaterial.objects.all()

class RequirementProductViewSet(CreateUpdateDeleteModelViewSet):
    permission_classes = [PpicPermission]
    serializer_class = RequirementProductManagement
    queryset = RequirementProduct.objects.all()


class MrpReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    get mrp
    '''
    permission_classes = [PpicPermission]
    serializer_class = MrpReadOnlySerializer
    queryset = MaterialRequirementPlanning.objects.prefetch_related(
        Prefetch('detailmrp_set',queryset=DetailMrp.objects.select_related('product'))).select_related('material','material__supplier','material__uom')

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

        
        querysetMrp = MaterialRequirementPlanning.objects.prefetch_related(
            Prefetch('detailmrp_set',queryset=DetailMrp.objects.select_related('product'))).select_related('material','material__supplier','material__uom','material__warehousematerial')
        
        for mrp in querysetMrp:
            recommend_seriz.append(mrp)
        
        ## requirements material in table are merged with requirements material which calculated with all product ordered

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

class MrpManagementViewSet(ModelViewSet):
    '''
    list : for mrp recommendations
    create , update , delete : mrp -> detail mrp
    '''
    permission_classes = [PpicPermission,CanManageMaterial]
    serializer_class = MrpManagementSerializer
    queryset = MaterialRequirementPlanning.objects.prefetch_related(Prefetch('detailmrp_set',queryset=DetailMrp.objects.select_related('mrp','product'))).select_related('material')
    
        

class WarehouseFinishGoodViewSet(GetModelViewSet):
    '''
    warehouse type (finish good) -> warehouse product -> product
    '''
    permission_classes = [PpicPermission]
    serializer_class = WarehouseTypeReadOnlySerializer
    queryset = WarehouseType.objects.prefetch_related(
        Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.select_related('process__process_type','process__product').select_related('product__customer','product__type'))).filter(Q(id=1))



class WarehouseSubcontViewSet(GetModelViewSet):
    '''
    warehouse type (subcont) -> warehouse product -> product
    '''
    permission_classes = [PpicPermission]
    serializer_class = WarehouseTypeReadOnlySerializer
    queryset = WarehouseType.objects.prefetch_related(
        Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.select_related('process__process_type','process__product').select_related('product__customer','product__type').filter(Q(quantity__gt=0)))).filter(Q(id=2))

class WarehouseWipViewSet(GetModelViewSet):
    '''
    warehouse type (wip) -> warehouse product -> product
    '''
    permission_classes = [PpicPermission]
    serializer_class = WarehouseTypeReadOnlySerializer
    queryset = WarehouseType.objects.prefetch_related(
        Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.select_related('process__process_type','process__product').select_related('product__customer','product__type'))).filter(Q(id__gt=2))

    
class WarehouseProductManagementViewSet(UpdateModelViewSet):
    '''
    management edit stock warehouse product eg: wip, finishgood, subcont
    '''
    permission_classes = [PpicPermission,CanManageWarehouse]
    serializer_class = WarehouseProductManagementSerializer
    queryset = WarehouseProduct.objects.all()

class WarehouseMaterialManagementViewSet(UpdateModelViewSet):
    '''
    management edit stock warehouse material
    '''
    permission_classes = [PpicPermission,CanManageWarehouse]
    serializer_class = WarehouseMaterialManagementSerializer
    queryset = WarehouseMaterial.objects.all()


class UomWarehouseMaterialViewSet(ReadOnlyModelViewSet):
    '''
    uom -> material -> stock in warehouse material
    '''
    permission_classes = [PpicPermission]
    serializer_class = UomWarehouseMaterialSerializer
    queryset = UnitOfMaterial.objects.prefetch_related(Prefetch('material_set',queryset=Material.objects.select_related('supplier','warehousematerial'))).annotate(amount_of_material=Count('material'))

class UomManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    management for unit of material
    '''
    permission_classes = [PpicPermission,CanManageMaterial]
    serializer_class = UomManagementSerializer
    queryset = UnitOfMaterial.objects.prefetch_related(Prefetch('material_set',queryset=Material.objects.select_related('supplier','warehousematerial')))

    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']
        uom = get_object_or_404(self.queryset,pk=pk)

        if uom.material_set.exists():
            invalid('There is still material with this unit in database')

        return super().destroy(request, *args, **kwargs)


class UomConversionReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    viewset for get and retrieve list of conversion uom
    '''
    permission_classes = [PpicPermission]
    serializer_class = ConversionUomReadOnlySerializer
    queryset = ConversionUom.objects.select_related('uom_input','uom_output')


class UomConversionManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    viewset for management conversion of uom
    '''
    permission_classes = [PpicPermission,CanManageWarehouse]
    serializer_class = ConversionUomManagementSerializer
    queryset = ConversionUom.objects.all()

class BasedConversionMaterialReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    viewset for get and retrieve list of based conversion material
    '''
    permission_classes = [PpicPermission]
    serializer_class = BasedConversionReadOnlySerializer
    queryset = BasedConversionMaterial.objects.select_related('material_input__uom','material_input__supplier','material_output__uom','material_output__supplier')

class BasedConversionMaterialManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    viewset for management based conversion of material
    '''
    permission_classes = [PpicPermission,CanManageWarehouse]
    serializer_class = BasedConversionManagementSerializer
    queryset = BasedConversionMaterial.objects.all()

class ReportConversionMaterialReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    viewset for get and retrieve list of conversion material reports
    '''
    permission_classes = [PpicPermission]
    serializer_class = ConversionMaterialReportReadOnlySerializer
    queryset = ConversionMaterialReport.objects.select_related('material_input__uom','material_input__supplier','material_output__uom','material_output__supplier').order_by('-created')

class ReportConversionMaterialManagementViewSet(CreateModelViewSet):
    '''
    viewset for management report conversion of material ie: shearing material
    '''
    permission_classes = [PpicPermission,CanManageWarehouse]
    serializer_class = ConversionMaterialReportManagementSerializer
    queryset = ConversionMaterialReport.objects.all()
    

class MaterialOrderReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    a viewset for get material order list
    '''
    permission_classes = [PpicPermission]
    serializer_class = MaterialOrderReadOnlySerializer
    queryset = MaterialOrder.objects.select_related('material','material__uom','material__supplier','purchase_order_material','purchase_order_material__supplier').filter(done=False)



    
class MaterialReceiptScheduleReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    a read only view set for schedule material receipt
    '''
    permission_classes = [PpicPermission]
    serializer_class = MaterialReceiptScheduleReadOnlySerializer
    queryset = MaterialReceiptSchedule.objects.select_related('material_order','material_order__material','material_order__purchase_order_material','material_order__material__supplier','material_order__material__uom','material_order__purchase_order_material__supplier').filter(Q(fulfilled_quantity__lte=0)&Q(material_order__done=False)).order_by('date')

class DeliveryNoteMaterialReadOnlyViewSet(ReadOnlyModelViewSet):
    permission_classes = [PpicPermission]
    serializer_class = DeliveryNoteMaterialReadOnlySerializer
    queryset = DeliveryNoteMaterial.objects.prefetch_related(
            Prefetch('materialreceipt_set',queryset=MaterialReceipt.objects.select_related('material_order','material_order__material','material_order__purchase_order_material','schedules','schedules__material_order','schedules__material_order__material','schedules__material_order__purchase_order_material','material_order__material__supplier','material_order__material__uom','material_order__purchase_order_material__supplier','delivery_note_material','delivery_note_material__supplier'))).select_related('supplier')


class DeliveryNoteMaterialManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a view set for cud receipt NOTE material
    '''
    permission_classes = [PpicPermission,CanManageWarehouse]
    serializer_class = DeliveryNoteMaterialManagementSerializer
    queryset = DeliveryNoteMaterial.objects.select_related('supplier').prefetch_related('materialreceipt_set')

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
    '''
    a viewset for cud all material received
    '''
    permission_classes = [PpicPermission,CanManageWarehouse]
    serializer_class = MaterialReceiptManagementSerializer
    queryset = MaterialReceipt.objects.select_related('delivery_note_material','material_order','delivery_note_material__supplier','material_order__purchase_order_material','material_order__purchase_order_material__supplier','material_order__material','material_order__material__warehousematerial')

    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']
        instance_mr = get_object_or_404(self.queryset,pk=pk)
        
        if instance_mr.quantity > 0:
            invalid()
        
        return super().destroy(request, *args, **kwargs)


class ProductOrderListViewSet(ReadOnlyModelViewSet):
    '''
    a viewset for get and retrieve product ordered, used in delivery module, ppic
    '''
    permission_classes = [PpicPermission]
    serializer_class = ProductOrderListSerializer
    queryset   = ProductOrder.objects.select_related('product','sales_order','product__customer','product__type','sales_order__customer').filter(Q(done=False),Q(sales_order__fixed=True)&Q(sales_order__done=False))

class DeliveryScheduleListViewSet(ReadOnlyModelViewSet):
    '''
    a view set for get and retrieve delivery schedule
    '''
    permission_classes = [PpicPermission]
    serializer_class = DeliveryScheduleListSerializer
    queryset = DeliverySchedule.objects.select_related('product_order','product_order__product','product_order__product__customer','product_order__product__type','product_order__sales_order','product_order__sales_order__customer').filter(Q(fulfilled_quantity__lte=0)&Q(product_order__done=False),Q(product_order__sales_order__fixed=True)&Q(product_order__sales_order__done=False)).order_by('date')


class DeliveryNoteCustomerReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    a view set for get and retrieve delivery note -> product delivery -> schedule if exists
    '''
    permission_classes = [PpicPermission]
    serializer_class = DeliveryNoteCustomerReadOnlySerializer
    queryset = DeliveryNoteCustomer.objects.prefetch_related(
            Prefetch('productdelivercustomer_set',queryset=ProductDeliverCustomer.objects.select_related('product_order','product_order__product','product_order__sales_order','schedules','delivery_note_customer','delivery_note_customer__customer','delivery_note_customer__vehicle','delivery_note_customer__driver','schedules__product_order'))).select_related('customer','vehicle','driver')

class DeliveryNoteCustomerManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a view set for create, update, delete delivery note
    '''
    permission_classes = [PpicPermission,CanManageDelivery]
    serializer_class = DeliveryNoteCustomerManagementSerializer
    queryset = DeliveryNoteCustomer.objects.select_related('driver','customer','vehicle').prefetch_related('productdelivercustomer_set')

    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']
        instance_dn_customer = get_object_or_404(self.queryset,pk=pk)
        if instance_dn_customer.productdelivercustomer_set.exists():
            invalid()

        return super().destroy(request, *args, **kwargs)


class ProductDeliverManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a view set for create, update, delete product delivery
    '''
    permission_classes = [PpicPermission,CanManageDelivery]
    serializer_class = ProductDeliverCustomerManagementSerializer
    queryset = ProductDeliverCustomer.objects.select_related('delivery_note_customer','product_order','schedules','product_order__product','product_order__sales_order__customer','delivery_note_customer__customer')

    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']
        instance_pd = get_object_or_404(self.queryset,pk=pk)
        if instance_pd.quantity > 0 or instance_pd.paid is True:
            invalid()

        return super().destroy(request, *args, **kwargs)

class MachineManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a viewset for cud machine
    '''
    permission_classes = [PpicPermission,CanManageProduction]
    serializer_class = MachineSerializer
    queryset = Machine.objects.annotate(numbers_of_production=Count('productionreport'))
    
    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']
        instance = get_object_or_404(self.queryset,pk=pk)
        if instance.productionreport_set.exists():
            invalid()

        return super().destroy(request, *args, **kwargs)


class MachineViewSet(ReadOnlyModelViewSet):
    '''
    viewset for machine
    '''
    permission_classes = [PpicPermission]
    serializer_class = MachineSerializer
    queryset = Machine.objects.annotate(numbers_of_production=Count('productionreport'))
    
class OperatorManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a viewset for cud operator
    '''    
    permission_classes = [PpicPermission,CanManageProduction]
    serializer_class = OperatorSerializer
    queryset = Operator.objects.annotate(numbers_of_production=Count('productionreport'))

    def destroy(self, request, *args, **kwargs):

        pk = kwargs['pk']
        instance = get_object_or_404(self.queryset,pk=pk)
        if instance.productionreport_set.exists():
            invalid()

        return super().destroy(request, *args, **kwargs)


class OperatorViewSet(ReadOnlyModelViewSet):
    '''
    viewset for operator
    '''
    permission_classes = [PpicPermission]
    serializer_class = OperatorSerializer
    queryset = Operator.objects.annotate(numbers_of_production=Count('productionreport'))

class DriverManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a viewset for cud driver
    '''
    permission_classes = [PpicPermission,CanManageDelivery]
    serializer_class = DriverSerializer
    queryset = Driver.objects.all()
    
    def destroy(self, request, *args, **kwargs):

        pk = kwargs['pk']

        instance = get_object_or_404(self.queryset,pk=pk)
        if instance.deliverynotecustomer_set.exists():
            invalid()

        if instance.deliverynotesubcont_set.exists():
            invalid()

        return super().destroy(request, *args, **kwargs)


class DriverViewSet(ReadOnlyModelViewSet):
    '''
    viewset for get and retrieve driver
    '''
    permission_classes = [PpicPermission]
    serializer_class = DriverSerializer
    queryset = Driver.objects.annotate(numbers_of_delivery_customer=Count('deliverynotecustomer',distinct=True),numbers_of_delivery_subcont=Count('deliverynotesubcont',distinct=True))


class VehicleManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a viewset for cud vehicle
    '''
    permission_classes = [PpicPermission,CanManageDelivery]
    serializer_class = VehicleSerializer
    queryset = Vehicle.objects.all()

    def destroy(self, request, *args, **kwargs):

        pk = kwargs['pk']

        instance = get_object_or_404(self.queryset,pk=pk)
        if instance.deliverynotecustomer_set.exists():
            invalid()

        if instance.deliverynotesubcont_set.exists():
            invalid()

        return super().destroy(request, *args, **kwargs)


class VehicleViewSet(ReadOnlyModelViewSet):
    '''
    viewset for get and retrieve vehicle
    '''
    permission_classes = [PpicPermission]
    serializer_class = VehicleSerializer
    queryset = Vehicle.objects.annotate(numbers_of_delivery_customer=Count('deliverynotecustomer',distinct=True),numbers_of_delivery_subcont=Count('deliverynotesubcont',distinct=True))


class ProductionReportReadOnlyViewSet(ReadOnlyModelViewSet):
    permission_classes = [PpicPermission]
    serializer_class = ProductionReportReadOnlySerializer
    queryset = ProductionReport.objects.prefetch_related(
        Prefetch('productproductionreport_set',ProductProductionReport.objects.select_related('product','product__customer','product__type')),
        Prefetch('materialproductionreport_set',MaterialProductionReport.objects.select_related('material','material__uom','material__supplier'))).select_related('operator','machine','product','product__customer','product__type','process','process__product','process__process_type').order_by('-date')


class ProductionPriorityViewSet(ReadOnlyModelViewSet):
    permission_classes = [PpicPermission]
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
    permission_classes = [PpicPermission,CanManageProduction]
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



class DeliveryNoteSubcontManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a view set to handle cud (Create,Update,Delete) delivery note subcont
    '''
    permission_classes = [PpicPermission,CanManageDelivery]
    serializer_class = DeliveryNoteSubcontManagementSerializer
    queryset = DeliveryNoteSubcont.objects.prefetch_related('productdeliversubcont_set').select_related('driver','vehicle','supplier')

    def destroy(self, request, *args, **kwargs):
        
        pk = kwargs['pk']
        instance = get_object_or_404(self.queryset,pk=pk)

        for productSubcont in instance.productdeliversubcont_set.all():
            if productSubcont.quantity > 0:
                ## if quantity product subconstruction that included in this delivery note is not zero, raise error 

                invalid()

        return super().destroy(request, *args, **kwargs)

class ProductDeliverySubcontManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a view set to handle cud (Create,Update,Delete) product that included in delivery note subcont
    '''
    permission_classes = [PpicPermission,CanManageDelivery]
    serializer_class = ProductDeliverySubcontManagementSerializer
    queryset = ProductDeliverSubcont.objects.prefetch_related('subcontreceipt_set').select_related('product','process','deliver_note_subcont')

    def destroy(self, request, *args, **kwargs):

        pk = kwargs['pk']
        instance = get_object_or_404(self.queryset,pk=pk)

        if instance.quantity > 0:
            ## if quantity product subconstruction sended to supplier is greater than zero, raise errorr

            invalid()

        return super().destroy(request, *args, **kwargs)

class ReceiptSubcontScheduleManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a viewset to handle cud schedule of product in subconstruction
    '''
    permission_classes = [PpicPermission,CanManageDelivery]
    serializer_class = ReceiptSubcontScheduleManagementSerializer
    queryset = ReceiptSubcontSchedule.objects.select_related('product_subcont').prefetch_related('product_subcont__subcontreceipt_set')

    def destroy(self, request, *args, **kwargs):

        pk = kwargs['pk']
        instance = get_object_or_404(self.queryset,pk=pk)
        if instance.fulfilled_quantity > 0:
            invalid()

        return super().destroy(request, *args, **kwargs)

class ReceiptSubcontScheduleListViewSet(ReadOnlyModelViewSet):
    '''
    a viewset for get all arrival schedule of product subconstruction
    '''
    permission_classes = [PpicPermission]
    serializer_class = ReceiptSubcontScheduleListSerializer
    queryset = ReceiptSubcontSchedule.objects.select_related('product_subcont','product_subcont__deliver_note_subcont','product_subcont__process','product_subcont__product','product_subcont__deliver_note_subcont__supplier','product_subcont__deliver_note_subcont__driver','product_subcont__deliver_note_subcont__vehicle','product_subcont__product__customer','product_subcont__product__type','product_subcont__process__process_type','product_subcont__process__product').annotate(received=Sum('product_subcont__subcontreceipt__quantity')).filter(~Q(fulfilled_quantity__gt=0),Q(received__lt=F('product_subcont__quantity')) |Q(received=None) )

class ProductDeliverSubcontListViewSet(ReadOnlyModelViewSet):
    '''
    a view set to get all list of product that in subconstruction
    '''
    permission_classes = [PpicPermission]
    serializer_class = ProductDeliverSubcontListSerializer
    queryset = ProductDeliverSubcont.objects.prefetch_related('subcontreceipt_set').select_related('deliver_note_subcont','process','product').annotate(received=Sum('subcontreceipt__quantity')).filter(Q(received__lt=F('quantity'))|Q(received=None))


class ProductListSubcontReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    a view set to get all product that can be delivered in delivery product subconstruction
    '''
    permission_classes = [PpicPermission]
    serializer_class=ProductReadOnlySerializer
    queryset = Product.objects.prefetch_related(
            Prefetch('ppic_process_related',queryset=Process.objects.
            prefetch_related(
                Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.select_related('warehouse_type'))).
            prefetch_related(
                Prefetch('requirementproduct_set',queryset=RequirementProduct.objects.select_related('product'))).
            prefetch_related(
                Prefetch('requirementmaterial_set',queryset=RequirementMaterial.objects.select_related('material'))).select_related('process_type').filter(process_type=2) ))

class DeliveryNoteSubcontReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    a view set to get and retrieve delivery product subconstruction
    '''
    permission_classes = [PpicPermission]
    serializer_class = DeliveryNoteSubcontReadOnlySerializer
    queryset = DeliveryNoteSubcont.objects.prefetch_related(
        Prefetch('productdeliversubcont_set',queryset=ProductDeliverSubcont.objects.select_related('deliver_note_subcont','product','process','deliver_note_subcont__driver','deliver_note_subcont__vehicle','deliver_note_subcont__supplier','product__customer','product__type','process__process_type','process__product').annotate(received=Sum('subcontreceipt__quantity')).prefetch_related(
        Prefetch('requirementmaterialsubcont_set',queryset=RequirementMaterialSubcont.objects.select_related('product_subcont','material','material__uom','material__supplier') )).prefetch_related(
            Prefetch('requirementproductsubcont_set',queryset=RequirementProductsubcont.objects.select_related('product_subcont','product','product__customer','product__type'))).prefetch_related('receiptsubcontschedule_set'))).select_related('driver','vehicle','supplier')


class ProductDeliverSubcontReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    a viewset for get product in subconstruction, nested to requirement material subcont, requirement product subcont, and arrival schedule
    '''
    permission_classes = [PpicPermission]
    serializer_class = ProductDeliverSubcontReadOnlySerializer
    queryset = ProductDeliverSubcont.objects.select_related('deliver_note_subcont','product','process','deliver_note_subcont__driver','deliver_note_subcont__vehicle','deliver_note_subcont__supplier','product__customer','product__type','process__process_type','process__product').annotate(received=Sum('subcontreceipt__quantity')).prefetch_related(Prefetch('requirementmaterialsubcont_set',queryset=RequirementMaterialSubcont.objects.select_related('product_subcont','material','material__uom','material__supplier') )).prefetch_related(
            Prefetch('requirementproductsubcont_set',queryset=RequirementProductsubcont.objects.select_related('product_subcont','product','product__customer','product__type'))).prefetch_related('receiptsubcontschedule_set').order_by('deliver_note_subcont__date')


class ProcessManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a viewset that handle management create update delete for process, nested to requirement material, requirement product, warehouse product
    '''
    permission_classes = [PpicPermission,CanManageProduct]
    serializer_class = ProcessPartialManagementSerializer
    queryset = Process.objects.prefetch_related(Prefetch('requirementmaterial_set',queryset=RequirementMaterial.objects.select_related('material','process'))).prefetch_related(Prefetch('requirementproduct_set',queryset=RequirementProduct.objects.select_related('product','process'))).prefetch_related(Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.select_related('warehouse_type','product'))).select_related('product','process_type')


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
            wh_type_fg = WarehouseType.objects.get(pk=1)

            try:
                prev_process = product.ppic_process_related.get(order = (order - 1))
                wh_product_prev_process = prev_process.warehouseproduct_set.exclude(warehouse_type=2).get()
                wh_product_prev_process.warehouse_type = wh_type_fg
                wh_product_prev_process.save()

            except:
                prev_process = product.ppic_process_related.get(order = (order - 2))
                wh_product_prev_process = prev_process.warehouseproduct_set.exclude(warehouse_type=2).get()
                wh_product_prev_process.warehouse_type = wh_type_fg
                wh_product_prev_process.save()
        
        return super().destroy(request, *args, **kwargs)


class SupplierListViewSet(ModelViewSet):
    permission_classes = [PpicPermission]
    serializer_class=SupplierListSerializer
    queryset = Supplier.objects.all()


class ReceiptNoteSubcontManagementViewSet(ModelViewSet):
    '''
    a view set for management receipt note subcont
    '''
    permission_classes = [PpicPermission,CanManageWarehouse]
    serializer_class = ReceiptNoteSubcontManagementSerializer
    queryset = ReceiptNoteSubcont.objects.prefetch_related('subcontreceipt_set').select_related('supplier')

    
    def update(self, request, *args, **kwargs):
        
        instance = self.get_object()
        image  = request.data.get('image',None)
        if image is not None and image =='':
            instance.image.delete(save=True)
        
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']

        instance = get_object_or_404(self.queryset,pk=pk)

        if instance.subcontreceipt_set.exists():
            invalid()

        return super().destroy(request, *args, **kwargs)


class ReceiptNoteSubcontReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    a viewset for get and retrieve receipt note subcont nested to product that received
    '''
    permission_classes = [PpicPermission]
    serializer_class = ReceiptNoteSubcontReadOnlySerializer
    queryset = ReceiptNoteSubcont.objects.prefetch_related(
        Prefetch('subcontreceipt_set',queryset=SubcontReceipt.objects.select_related('product_subcont','receipt_note','schedules','product_subcont__product','product_subcont__process','product_subcont__deliver_note_subcont','product_subcont__product__customer','product_subcont__product__type','product_subcont__process__product','product_subcont__process__process_type','product_subcont__deliver_note_subcont__driver','product_subcont__deliver_note_subcont__vehicle','product_subcont__deliver_note_subcont__supplier','schedules__product_subcont','schedules__product_subcont__product','schedules__product_subcont__process','schedules__product_subcont__deliver_note_subcont','receipt_note__supplier'))).select_related('supplier')


class SubcontReceiptManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a viewset for cud (create, update, delete) subcont receipt or product received from subconstruction 
    '''
    permission_classes = [PpicPermission,CanManageWarehouse]
    serializer_class = SubcontReceiptManagementSerializer
    queryset = SubcontReceipt.objects.select_related('product_subcont','receipt_note','schedules','product_subcont__product','product_subcont__process','product_subcont__deliver_note_subcont','receipt_note__supplier','schedules__product_subcont','product_subcont__deliver_note_subcont__supplier')

    def destroy(self, request, *args, **kwargs):

        pk = kwargs['pk']

        instance = get_object_or_404(self.queryset,pk=pk)

        if instance.quantity > 0:
            invalid()

        return super().destroy(request, *args, **kwargs)










