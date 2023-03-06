from rest_framework.response import Response

from manager.viewsets import CreateUpdateDeleteModelViewSet,ReadOnlyModelViewSet
from manager.shortcuts import invalid
from django.shortcuts import get_object_or_404
from django.db.models import Prefetch,F,Count
from math import ceil

from ppic.permissions import PpicPermission,CanManageMaterial

from ppic.models import UnitOfMaterial,Material,MaterialRequirementPlanning,DetailMrp,RequirementMaterial,Product,ProductOrder,WarehouseProduct,Process,RequirementProduct,MaterialOrder

from marketing.models import SalesOrder

from ppic.serializers.material_serializer import UnitOfMaterialSerializer,OneDepthMaterialNestedWarehouseSerializer,MaterialDetailSerializer,MaterialManagementSerializer,TwoDepthMrpSerializer,MrpManagementSerializer


class UomManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    management for unit of material
    '''
    permission_classes = [PpicPermission,CanManageMaterial]
    serializer_class = UnitOfMaterialSerializer
    queryset = UnitOfMaterial.objects.prefetch_related(Prefetch('material_set',queryset=Material.objects.select_related('supplier','warehousematerial')))

    def destroy(self, request, *args, **kwargs):
        pk = int(kwargs['pk'])
        uom = get_object_or_404(self.queryset,pk=pk)

        if pk == 1 or pk == 2 or pk ==3:
            invalid('Tidak bisa menghapus unit material utama dalam sistem') 

        if uom.material_set.exists():
            invalid('Masih ada material dengan unit tersebut di database')

        return super().destroy(request, *args, **kwargs)

class UomListViewSet(ReadOnlyModelViewSet):
    '''
    viewset provide list data of unit of material 
    '''
    permission_classes = [PpicPermission]
    serializer_class = UnitOfMaterialSerializer
    queryset = UnitOfMaterial.objects.annotate(amount_of_material=Count('material'))

class MaterialListViewSet(ReadOnlyModelViewSet):
    '''
    a viewset for handle request for list data of material
    '''
    serializer_class = OneDepthMaterialNestedWarehouseSerializer
    queryset = Material.objects.get_queryset_related()

class MaterialDetailViewSet(ReadOnlyModelViewSet):
    '''
    viewset for handle request for detail material
        nested to its requirement mateiral and warehouse material
    '''
    serializer_class = MaterialDetailSerializer
    queryset = Material.objects.get_queryset_related().prefetch_related(
        Prefetch('ppic_requirementmaterial_related',queryset=RequirementMaterial.objects.select_related('process','process__process_type','process__product','material','material__supplier','material__uom')))

class MrpReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    get mrp
    '''
    serializer_class = TwoDepthMrpSerializer
    queryset = MaterialRequirementPlanning.objects.prefetch_related(
        Prefetch('detailmrp_set',queryset=DetailMrp.objects.select_related('product'))).select_related('material','material__supplier','material__uom')

    def list(self, request, *args, **kwargs):
        '''
        a list for material requirement planning recommendation in material page 
        '''

        sales_order = SalesOrder.objects.filter(fixed=True,closed=False).prefetch_related(
            Prefetch('productorder_set',queryset=ProductOrder.objects.filter(delivered__lt=F('ordered')).select_related('product').prefetch_related('product__ppic_process_related')))
        
                
        productList = Product.objects.prefetch_related(
            Prefetch('ppic_process_related',queryset=Process.objects.select_related('product','process_type').prefetch_related(
                Prefetch('requirementproduct_set',queryset=RequirementProduct.objects.select_related('product'))).prefetch_related(
                    Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.select_related('warehouse_type','product','process'))).prefetch_related(
                        Prefetch('requirementmaterial_set',queryset=RequirementMaterial.objects.select_related('material','material__supplier','material__uom','material__warehousematerial','process').prefetch_related(
                            Prefetch('material__ppic_materialorder_related',queryset=MaterialOrder.objects.filter(ordered__gt=F('arrived')).select_related('material','purchase_order_material'))).prefetch_related(
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

        mrp_seriz = self.get_serializer(recommend_seriz,many=True)
        
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


class MrpManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    list : for mrp recommendations
    create , update , delete : mrp -> detail mrp
    '''
    permission_classes = [PpicPermission,CanManageMaterial]
    serializer_class = MrpManagementSerializer
    queryset = MaterialRequirementPlanning.objects.prefetch_related(Prefetch('detailmrp_set',queryset=DetailMrp.objects.select_related('mrp','product'))).select_related('material')


class MaterialManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a view set for cud data material
    '''
    permission_classes = [PpicPermission,CanManageMaterial]
    serializer_class = MaterialManagementSerializer
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
    