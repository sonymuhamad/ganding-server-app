from rest_framework.viewsets import ReadOnlyModelViewSet
from django.db.models import Prefetch,Sum

from purchasing.permissions import PurchasingPermission

from ppic.serializer import DeliveryNoteSubcontReadOnlySerializer,DeliveryNoteMaterialReadOnlySerializer,ReceiptNoteSubcontReadOnlySerializer
from ppic.models import DeliveryNoteMaterial,ReceiptNoteSubcont,SubcontReceipt,MaterialReceipt,DeliveryNoteSubcont,ProductDeliverSubcont,RequirementMaterialSubcont,RequirementProductsubcont


class DeliveryNoteMaterialReadOnlyViewSet(ReadOnlyModelViewSet):
    permission_classes = [PurchasingPermission]
    serializer_class = DeliveryNoteMaterialReadOnlySerializer
    queryset = DeliveryNoteMaterial.objects.prefetch_related(
            Prefetch('materialreceipt_set',queryset=MaterialReceipt.objects.select_related('material_order','material_order__material','material_order__purchase_order_material','schedules','schedules__material_order','schedules__material_order__material','schedules__material_order__purchase_order_material','material_order__material__supplier','material_order__material__uom','material_order__purchase_order_material__supplier','delivery_note_material','delivery_note_material__supplier'))).select_related('supplier')


class ReceiptNoteSubcontReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    a viewset for get and retrieve receipt note subcont nested to product that received
    '''
    permission_classes = [PurchasingPermission]
    serializer_class = ReceiptNoteSubcontReadOnlySerializer
    queryset = ReceiptNoteSubcont.objects.prefetch_related(
        Prefetch('subcontreceipt_set',queryset=SubcontReceipt.objects.select_related('product_subcont','receipt_note','schedules','product_subcont__product','product_subcont__process','product_subcont__deliver_note_subcont','product_subcont__product__customer','product_subcont__product__type','product_subcont__process__product','product_subcont__process__process_type','product_subcont__deliver_note_subcont__driver','product_subcont__deliver_note_subcont__vehicle','product_subcont__deliver_note_subcont__supplier','schedules__product_subcont','schedules__product_subcont__product','schedules__product_subcont__process','schedules__product_subcont__deliver_note_subcont','receipt_note__supplier'))).select_related('supplier')


class DeliveryNoteSubcontReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    a view set to get and retrieve delivery product subconstruction
    '''
    permission_classes = [PurchasingPermission]
    serializer_class = DeliveryNoteSubcontReadOnlySerializer
    queryset = DeliveryNoteSubcont.objects.prefetch_related(
        Prefetch('productdeliversubcont_set',queryset=ProductDeliverSubcont.objects.select_related('deliver_note_subcont','product','process','deliver_note_subcont__driver','deliver_note_subcont__vehicle','deliver_note_subcont__supplier','product__customer','product__type','process__process_type','process__product').annotate(received=Sum('subcontreceipt__quantity')).prefetch_related(
        Prefetch('requirementmaterialsubcont_set',queryset=RequirementMaterialSubcont.objects.select_related('product_subcont','material','material__uom','material__supplier') )).prefetch_related(
            Prefetch('requirementproductsubcont_set',queryset=RequirementProductsubcont.objects.select_related('product_subcont','product','product__customer','product__type'))).prefetch_related('receiptsubcontschedule_set'))).select_related('driver','vehicle','supplier')

