from rest_framework.response import Response
from django.db.models import Prefetch,Count,F
from math import ceil

from manager.viewsets import CreateUpdateDeleteModelViewSet,RetrieveModelViewSet,ReadOnlyModelViewSet,UpdateModelViewSet

from purchasing.permissions import PurchasingPermission,CanManagePurchaseOrderMaterial
from purchasing.models import PurchaseOrderMaterial
from django.shortcuts import get_object_or_404
from manager.shortcuts import invalid
from purchasing.shortcuts import validate_mo

from ppic.models import Material,MaterialRequirementPlanning,DetailMrp,RequirementMaterial,Product,ProductOrder,WarehouseProduct,Process,RequirementProduct,MaterialOrder,MaterialReceiptSchedule,MaterialReceipt
from marketing.models import SalesOrder

from purchasing.serializers.purchase_order_serializer import PurchaseOrderManagementSerializer,PurchaseOrderReadOnlySerializer,MaterialReceiptScheduleReadOnlySerializer,CloseStatusPurchaseOrderSerializer,StatusPurchaseOrderManagementSerializer,MaterialOrderManagementSerializer,MaterialReceiptScheduleManagementSerializer

from ppic.serializers.warehouse_serializer import MaterialReceiptReadOnlySerializer
from ppic.serializers.material_serializer import OneDepthMaterialNestedWarehouseSerializer,TwoDepthMrpSerializer


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

class PurchaseOrderReadOnlyViewSet(ReadOnlyModelViewSet):
    permission_classes = [PurchasingPermission]
    serializer_class = PurchaseOrderReadOnlySerializer
    queryset = PurchaseOrderMaterial.objects.prefetch_related(
            Prefetch('materialorder_set',queryset=MaterialOrder.objects.select_related('material','purchase_order_material','material__supplier','material__uom','purchase_order_material__supplier','to_product','to_product__type','to_product__customer').annotate(total_receipt_schedule=Count('materialreceiptschedule',distinct=True)).prefetch_related(Prefetch('materialreceiptschedule_set',MaterialReceiptSchedule.objects.select_related('material_order','material_order__material','material_order__purchase_order_material','material_order__material__uom','material_order__material__supplier','material_order__purchase_order_material__supplier').order_by('date'))) )).select_related('supplier')

class MaterialReceiptListViewSet(ReadOnlyModelViewSet):
    '''
    a viewset for retrieve queryset of material receipt, based on particular purchase order
    '''
    serializer_class = MaterialReceiptReadOnlySerializer
    queryset = MaterialReceipt.objects.select_related('delivery_note_material','material_order','delivery_note_material__supplier','material_order__material','material_order__purchase_order_material','material_order__purchase_order_material__supplier','material_order__material__uom','material_order__material__supplier','schedules','schedules__material_order','schedules__material_order__material','schedules__material_order__purchase_order_material').order_by('delivery_note_material__date')

    def retrieve(self, request, *args, **kwargs):

        pk = kwargs['pk']
        
        queryset = self.filter_queryset(self.get_queryset())
        validate_queryset = queryset.filter(material_order__purchase_order_material__id=pk)
        serializer = self.get_serializer(validate_queryset, many=True)

        return Response(serializer.data)


class CloseStatusPurchaseOrderViewSet(UpdateModelViewSet):
    '''
    a viewset for change status close of purchase order material
    '''
    serializer_class = CloseStatusPurchaseOrderSerializer
    permission_classes = [PurchasingPermission,CanManagePurchaseOrderMaterial]
    queryset = PurchaseOrderMaterial.objects.all()



class StatusPurchaseOrderManagementViewSet(UpdateModelViewSet):
    '''
    a viewset to just update status of purchase order material
    '''
    permission_classes = [PurchasingPermission,CanManagePurchaseOrderMaterial]
    serializer_class = StatusPurchaseOrderManagementSerializer
    queryset = PurchaseOrderMaterial.objects.prefetch_related('materialorder_set')


class MaterialListViewSet(RetrieveModelViewSet):
    '''
    a viewset for retrieve queryset of material, based on particular supplier
    '''
    permission_classes = [PurchasingPermission]
    serializer_class = OneDepthMaterialNestedWarehouseSerializer
    queryset = Material.objects.get_queryset_related()

    def retrieve(self, request, *args, **kwargs):
        pk = kwargs['pk']

        queryset = self.filter_queryset(self.get_queryset())
        validate_queryset = queryset.filter(supplier__id__exact=pk)
        serializer = self.get_serializer(validate_queryset, many=True)

        return Response(serializer.data)                    

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


class MaterialReceiptScheduleManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a viewset for management material receipt schedule
    '''
    permission_classes = [PurchasingPermission,CanManagePurchaseOrderMaterial]
    serializer_class = MaterialReceiptScheduleManagementSerializer
    queryset = MaterialReceiptSchedule.objects.select_related('material_order','material_order__purchase_order_material','material_order__material','material_order__purchase_order_material__supplier','material_order__material__supplier','material_order__material__uom')

    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']
        instance = get_object_or_404(self.queryset,pk=pk)

        if instance.fulfilled_quantity > 0:
            invalid()

        return super().destroy(request, *args, **kwargs)

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

class MrpReadOnlyViewSet(RetrieveModelViewSet):
    '''
    get mrp
    '''
    permission_classes = [PurchasingPermission]
    serializer_class = TwoDepthMrpSerializer
    queryset = MaterialRequirementPlanning.objects.prefetch_related(
        Prefetch('detailmrp_set',queryset=DetailMrp.objects.select_related('product'))).select_related('material','material__supplier','material__uom')

    queryset_product =  Product.objects.prefetch_related(
            Prefetch('ppic_process_related',queryset=Process.objects.select_related('process_type').prefetch_related(
                Prefetch('requirementproduct_set',queryset=RequirementProduct.objects.select_related('product'))).prefetch_related(
                    Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.select_related('warehouse_type',))).prefetch_related(
                        Prefetch('requirementmaterial_set',queryset=RequirementMaterial.objects.select_related('material','material__supplier','material__uom','material__warehousematerial','process').prefetch_related(
                            Prefetch('material__ppic_materialorder_related',queryset=MaterialOrder.objects.filter(ordered__gt=F('arrived')).select_related('material','purchase_order_material'))).prefetch_related(
                                Prefetch('material__ppic_materialrequirementplanning_related',queryset=MaterialRequirementPlanning.objects.select_related('material').prefetch_related(
                                    Prefetch('detailmrp_set',queryset=DetailMrp.objects.select_related('product','mrp'))))))).order_by('-order'))).select_related('type','customer')
    
    queryset_sales_order = SalesOrder.objects.filter(fixed=True,closed=False).prefetch_related(
            Prefetch('productorder_set',queryset=ProductOrder.objects.filter(delivered__lt=F('ordered')).select_related('product').prefetch_related('product__ppic_process_related')))

    querysetMrp = MaterialRequirementPlanning.objects.prefetch_related(
            Prefetch('detailmrp_set',queryset=DetailMrp.objects.select_related('product'))).select_related('material','material__supplier','material__uom','material__warehousematerial')

    productList = {}        
    storage_product_ordered = {}
    storage_product_to_be_produced = {}
    storage_material = {}
    recommend_serializer = []

    def __init__(self, **kwargs) -> None:
        self.productList = {}        
        self.storage_product_ordered = {}
        self.storage_product_to_be_produced = {}
        self.storage_material = {}
        self.recommend_serializer = []

        super().__init__(**kwargs)

    def generate_data_product(self):
        
        for product in self.queryset_product:
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


            self.productList[product.id]  = {
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

    def generate_product_order(self):

        for so in self.queryset_sales_order:
            for po in so.productorder_set.all():
                if po.product.id in self.storage_product_ordered:
                    self.storage_product_ordered[po.product.id] += (po.ordered - po.delivered)
                else:
                    self.storage_product_ordered[po.product.id] = (po.ordered - po.delivered) 

    def search_related_production(self):
        for k,v in self.storage_product_ordered.items():
            self.searchNestedProduction(k,v)
        
    def search_material_related_to_production(self):
        for k,v in self.storage_product_to_be_produced.items():
            self.search(k,v)
        
    def generate_data_material_usages(self):
        
        for k,v in list(self.storage_material.items()):
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
                    del self.storage_material[k]

    def generator_queryset_mrp(self,pk=None):
        if pk == None:
            for mrp in self.querysetMrp:
                yield mrp
        else:
            for mrp in self.querysetMrp.filter(material__supplier__pk__exact=pk):
                yield mrp


    def generate_data_for_serializer(self,pk=None):

        self.generate_data_product()
        self.generate_product_order()
        self.search_related_production()
        self.search_material_related_to_production()
        self.generate_data_material_usages()
        
        for key,value in self.storage_material.items():
            if pk is not None and value['instance'].supplier.id != pk:
                continue

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
            self.recommend_serializer.append(each_seriz)
        
        
        for mrp in self.generator_queryset_mrp(pk):
            self.recommend_serializer.append(mrp)
        

        mrp_seriz = self.get_serializer(self.recommend_serializer,many=True)

        return  Response(mrp_seriz.data)


    def list(self, request, *args, **kwargs):
        '''
        a list for material requirement planning recommendation in material page 
        '''
        ## requirements material in table are merged with requirements material which calculated with all product ordered
        
        return self.generate_data_for_serializer()         

    def retrieve(self, request, *args, **kwargs):

        pk = int(kwargs['pk'])

        return self.generate_data_for_serializer(pk)

    def searchNestedProduction(self,idProduct,quantity):
        
        product = self.productList[idProduct]

        if idProduct in self.storage_product_to_be_produced:
            self.storage_product_to_be_produced[idProduct] += quantity
        else:
            self.storage_product_to_be_produced[idProduct] = quantity

        for process in product['ppic_process_related']:

            for wh_product in process['warehouseproduct_set']:
                quantity -= wh_product['quantity'] 
            
            for req_product in process['requirementproduct_set']:
                qty_production = ceil(quantity/req_product['output']) * req_product['input']
                idProductSearch = req_product['product']
                
                self.searchNestedProduction(idProductSearch,qty_production)


    def search(self,idProduct,quantity):
        
        product = self.productList[idProduct]
        instanceProduct = self.productList[idProduct]['instance']

        for process in product['ppic_process_related']:

            for wh_product in process['warehouseproduct_set']:
                quantity -= wh_product['quantity'] 

            for req_material in process['requirementmaterial_set']:
                
                qty_req_material = ceil(quantity/req_material['output']) * req_material['input']

                if req_material['material']['id'] in self.storage_material:
                    self.storage_material[req_material['material']['id']]['quantity'] += qty_req_material
                else:
                    self.storage_material[req_material['material']['id']] = req_material['material']
                    self.storage_material[req_material['material']['id']]['quantity'] = qty_req_material

                if 'detail' in self.storage_material[req_material['material']['id']]:
                    
                    if instanceProduct in self.storage_material[req_material['material']['id']]['detail']:
                        self.storage_material[req_material['material']['id']]['detail'][instanceProduct]['quantity_production'] += quantity
                        self.storage_material[req_material['material']['id']]['detail'][instanceProduct]['quantity'] += qty_req_material
                    else:
                         self.storage_material[req_material['material']['id']]['detail'][instanceProduct] = {
                            'quantity_production':quantity,
                            'quantity':qty_req_material
                            }
                else:
                    self.storage_material[req_material['material']['id']]['detail'] = { instanceProduct : {
                            'quantity_production':quantity,
                            'quantity':qty_req_material
                            } }
                    

