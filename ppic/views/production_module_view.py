from rest_framework.response import Response

from math import ceil
from django.shortcuts import get_object_or_404
from django.db.models import Count,Prefetch,F,Sum

from manager.shortcuts import invalid
from manager.viewsets import CreateUpdateDeleteModelViewSet,ReadOnlyModelViewSet
from ppic.permissions import PpicPermission,CanManageProduction

from ppic.models import Machine,Operator,Product,Process,RequirementMaterial,RequirementProduct,WarehouseProduct,RequirementMaterialSubcont,RequirementProductsubcont,ProductionReport,MaterialProductionReport,ProductProductionReport,ProductOrder,ProcessType,ReceiptSubcontSchedule,ProductDeliverSubcont

from ppic.serializers.product_serializer import OneDepthProductNestedProcessSerializer
from marketing.models import SalesOrder

from ppic.serializers.production_serializer import MachineSerializer,OperatorSerializer,ProductionReportManagementSerializer,ProductionReportReadOnlySerializer,ReceiptSubcontScheduleManagementSerializer

from ppic.serializers.delivery_serializer import ProductDeliverSubcontReadOnlySerializer

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


class ProductionPriorityViewSet(ReadOnlyModelViewSet):
    '''
    '''
    permission_classes = [PpicPermission]
    serializer_class = OneDepthProductNestedProcessSerializer
    queryset = Product.objects.all()

    def list(self, request, *args, **kwargs):

        sales_order = SalesOrder.objects.filter(fixed=True,closed=False).prefetch_related(
            Prefetch('productorder_set',queryset=ProductOrder.objects.filter(delivered__lt=F('ordered')).select_related('product').prefetch_related('product__ppic_process_related')))

        process_type_subcont = ProcessType.objects.get(pk=2)

        queryset_warehouseproduct = WarehouseProduct.objects.select_related('warehouse_type','process','product')
        queryset_requirement_product = RequirementProduct.objects.select_related('product','process','product__customer','product__type').prefetch_related(
        Prefetch('product__ppic_warehouseproduct_related',queryset_warehouseproduct))
        queryset_requirement_material = RequirementMaterial.objects.select_related('material','material__warehousematerial','material__supplier','material__uom','material__warehousematerial__material','process')

        queryset_product = Product.objects.get_queryset_related().prefetch_related(
            Prefetch('ppic_process_related',queryset=Process.objects.
            prefetch_related(
                Prefetch('warehouseproduct_set',queryset = queryset_warehouseproduct)).
            prefetch_related(
                Prefetch('requirementproduct_set',queryset = queryset_requirement_product)).
            prefetch_related(
                Prefetch('requirementmaterial_set',queryset = queryset_requirement_material)).exclude(process_type=process_type_subcont).select_related('process_type','product')))

        dataProduct = {}
        productOrdered = {}
        productionPriority = []
        storageProduct = {}

        for product in queryset_product:
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

        prioritySeriz = self.get_serializer(productionPriority,many=True)
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


class ProductionReportReadOnlyViewSet(ReadOnlyModelViewSet):
    permission_classes = [PpicPermission]
    serializer_class = ProductionReportReadOnlySerializer
    queryset = ProductionReport.objects.prefetch_related(
        Prefetch('productproductionreport_set',ProductProductionReport.objects.select_related('product','product__customer','product__type')),
        Prefetch('materialproductionreport_set',MaterialProductionReport.objects.select_related('material','material__uom','material__supplier'))).select_related('operator','machine','product','product__customer','product__type','process','process__product','process__process_type').order_by('-date')


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



class ProductionListViewSet(ReadOnlyModelViewSet):
    permission_classes = [PpicPermission]
    serializer_class = OneDepthProductNestedProcessSerializer
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
                Prefetch('requirementmaterial_set',queryset = queryset_requirement_material)).select_related('process_type','product')))

class ReceiptSubcontScheduleManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a viewset to handle cud schedule of product in subconstruction
    '''
    permission_classes = [PpicPermission,CanManageProduction]
    serializer_class = ReceiptSubcontScheduleManagementSerializer
    queryset = ReceiptSubcontSchedule.objects.select_related('product_subcont').prefetch_related('product_subcont__subcontreceipt_set')

    def destroy(self, request, *args, **kwargs):

        pk = kwargs['pk']
        instance = get_object_or_404(self.queryset,pk=pk)
        if instance.fulfilled_quantity > 0:
            invalid()

        return super().destroy(request, *args, **kwargs)

class ProductDeliverSubcontReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    a viewset for get product in subconstruction, nested to requirement material subcont, requirement product subcont, and arrival schedule
    '''
    permission_classes = [PpicPermission]
    serializer_class = ProductDeliverSubcontReadOnlySerializer
    queryset = ProductDeliverSubcont.objects.select_related('deliver_note_subcont','product','process','deliver_note_subcont__driver','deliver_note_subcont__vehicle','deliver_note_subcont__supplier','product__customer','product__type','process__process_type','process__product').annotate(received=Sum('subcontreceipt__quantity')).prefetch_related(
        Prefetch('requirementmaterialsubcont_set',queryset=RequirementMaterialSubcont.objects.select_related('product_subcont','material','material__uom','material__supplier') )).prefetch_related(
            Prefetch('requirementproductsubcont_set',queryset=RequirementProductsubcont.objects.select_related('product_subcont','product','product__customer','product__type'))).prefetch_related(Prefetch('receiptsubcontschedule_set',queryset=ReceiptSubcontSchedule.objects.select_related('product_subcont'))).order_by('deliver_note_subcont__date')
