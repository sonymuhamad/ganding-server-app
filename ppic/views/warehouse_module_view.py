from django.db.models import Prefetch,Q,F,Count,Sum
from django.shortcuts import get_object_or_404

from manager.shortcuts import invalid
from manager.viewsets import GetModelViewSet,CreateUpdateDeleteModelViewSet,UpdateModelViewSet,ReadOnlyModelViewSet

from ppic.permissions import PpicPermission,CanManageWarehouse
from ppic.models import WarehouseMaterial,WarehouseProduct,WarehouseType,UnitOfMaterial,Material,ReceiptNoteSubcont,MaterialOrder,DeliveryNoteMaterial,MaterialReceipt,SubcontReceipt,MaterialReceiptSchedule,ReceiptSubcontSchedule,ProductDeliverSubcont

from ppic.serializers.material_serializer import UnitOfMaterialNestedSerializer
from ppic.serializers.warehouse_serializer import WarehouseMaterialManagementSerializer,WarehouseTypeReadOnlySerializer,WarehouseProductManagementSerializer,ThreeDepthReceiptSubcontScheduleSerializer,ThreeDepthMaterialReceiptScheduleSerializer,OneDepthReceiptNoteSubcontSerializer,BaseReceiptNoteSubcontSerializer,DeliveryNoteMaterialSerializer,DeliveryNoteMaterialReadOnlySerializer,SubcontReceiptManagementSerializer,MaterialReceiptManagementSerializer

from ppic.serializers.delivery_serializer import OneDepthProductDeliverSubcontSerializer
from purchasing.serializers.purchase_order_serializer import TwoDepthMaterialOrderSerializer

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

class WarehouseFinishGoodViewSet(GetModelViewSet):
    '''
    warehouse type (finish good) -> warehouse product -> product
    '''
    permission_classes = [PpicPermission]
    serializer_class = WarehouseTypeReadOnlySerializer
    queryset = WarehouseType.objects.prefetch_related(
        Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.select_related('process__process_type','process__product').select_related('product__customer','product__type'))).filter(Q(id=1))


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
    serializer_class = UnitOfMaterialNestedSerializer
    queryset = UnitOfMaterial.objects.prefetch_related(
        Prefetch('material_set',queryset=Material.objects.get_queryset_related())).annotate(amount_of_material=Count('material'))

class ReceiptNoteSubcontManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a view set for management receipt note subcont
    '''
    permission_classes = [PpicPermission,CanManageWarehouse]
    serializer_class = BaseReceiptNoteSubcontSerializer
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
    serializer_class = OneDepthReceiptNoteSubcontSerializer
    queryset = ReceiptNoteSubcont.objects.prefetch_related(
        Prefetch('subcontreceipt_set',queryset=SubcontReceipt.objects.select_related('product_subcont','receipt_note','schedules','product_subcont__product','product_subcont__process','product_subcont__deliver_note_subcont','product_subcont__product__customer','product_subcont__product__type','product_subcont__process__product','product_subcont__process__process_type','product_subcont__deliver_note_subcont__driver','product_subcont__deliver_note_subcont__vehicle','product_subcont__deliver_note_subcont__supplier','schedules__product_subcont','schedules__product_subcont__product','schedules__product_subcont__process','schedules__product_subcont__deliver_note_subcont','receipt_note__supplier'))).select_related('supplier')

class DeliveryNoteMaterialManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a view set for cud receipt NOTE material
    '''
    permission_classes = [PpicPermission,CanManageWarehouse]
    serializer_class = DeliveryNoteMaterialSerializer
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

class DeliveryNoteMaterialReadOnlyViewSet(ReadOnlyModelViewSet):
    serializer_class = DeliveryNoteMaterialReadOnlySerializer
    queryset = DeliveryNoteMaterial.objects.prefetch_related(
            Prefetch('materialreceipt_set',queryset=MaterialReceipt.objects.select_related('material_order','material_order__material','material_order__purchase_order_material','schedules','schedules__material_order','schedules__material_order__material','schedules__material_order__purchase_order_material','material_order__material__supplier','material_order__material__uom','material_order__purchase_order_material__supplier','delivery_note_material','delivery_note_material__supplier'))).select_related('supplier')

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

############### 
############### 

class ReceiptSubcontScheduleListViewSet(ReadOnlyModelViewSet):
    '''
    a viewset for get all arrival schedule of product subconstruction
    '''
    permission_classes = [PpicPermission]
    serializer_class = ThreeDepthReceiptSubcontScheduleSerializer
    queryset = ReceiptSubcontSchedule.objects.select_related('product_subcont','product_subcont__deliver_note_subcont','product_subcont__process','product_subcont__product','product_subcont__deliver_note_subcont__supplier','product_subcont__deliver_note_subcont__driver','product_subcont__deliver_note_subcont__vehicle','product_subcont__product__customer','product_subcont__product__type','product_subcont__process__process_type','product_subcont__process__product').annotate(received=Sum('product_subcont__subcontreceipt__quantity')).filter(Q(fulfilled_quantity=0),Q(received__lt=F('product_subcont__quantity')) |Q(received=None) )

class MaterialReceiptScheduleReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    a read only view set for schedule material receipt
    '''
    permission_classes = [PpicPermission]
    serializer_class = ThreeDepthMaterialReceiptScheduleSerializer
    queryset = MaterialReceiptSchedule.objects.select_related('material_order','material_order__material','material_order__purchase_order_material','material_order__material__supplier','material_order__material__uom','material_order__purchase_order_material__supplier').filter(Q(fulfilled_quantity__lte=0)&Q(material_order__arrived__lt=F('material_order__ordered'))).order_by('date')

class ProductDeliverSubcontListViewSet(ReadOnlyModelViewSet):
    '''
    a view set to get all list of product that in subconstruction
    '''
    permission_classes = [PpicPermission]
    serializer_class = OneDepthProductDeliverSubcontSerializer
    queryset = ProductDeliverSubcont.objects.prefetch_related('subcontreceipt_set').select_related('deliver_note_subcont','process','product').annotate(received=Sum('subcontreceipt__quantity')).filter(Q(received__lt=F('quantity'))|Q(received=None))

class MaterialOrderReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    a viewset for get material order list
    '''
    serializer_class = TwoDepthMaterialOrderSerializer
    queryset = MaterialOrder.objects.select_related('material','material__uom','material__supplier','purchase_order_material','purchase_order_material__supplier').filter(arrived__lt=F('ordered'))


