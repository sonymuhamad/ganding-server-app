from rest_framework.routers import DefaultRouter
from django.urls import path,include

from views.supplier_module_view import SupplierViewSet,SupplierManagementViewSet,SupplierReadOnlyViewSet

from views.receipt_and_delivery_note_module_view import DeliveryNoteMaterialReadOnlyViewSet,DeliveryNoteSubcontReadOnlyViewSet,ReceiptNoteSubcontReadOnlyViewSet


from views.purchase_order_module_view import MaterialListViewSet,MrpReadOnlyViewSet,PurchaseOrderReadOnlyViewSet,MaterialReceiptListViewSet,MaterialReceiptScheduleManagementViewSet,MaterialReceiptScheduleReadOnlyViewSet,MaterialOrderManagementViewSet,PurchaseOrderManagementViewSet,StatusPurchaseOrderManagementViewSet,CloseStatusPurchaseOrderViewSet

from views.material_module_view import MaterialDetailListViewSet
from views.purchasing_dashboard_view import MaterialUsageAndOrderViewSet

router = DefaultRouter()


router.register(r'supplier',SupplierViewSet,basename='supplier')
router.register(r'supplier-management',SupplierManagementViewSet,basename='supplier-management')  
router.register(r'supplier-detail',SupplierReadOnlyViewSet,basename='supplier-detail')

router.register(r'delivery-note-material',DeliveryNoteMaterialReadOnlyViewSet,basename='delivery-note-material')
router.register(r'delivery-note-subcont',DeliveryNoteSubcontReadOnlyViewSet,basename='delivery-note-subcont')
router.register(r'receipt-note-subcont',ReceiptNoteSubcontReadOnlyViewSet,basename='receipt-note-subcont')

router.register(r'supplier-material-list',MaterialListViewSet,basename='supplier-material-list')
router.register(r'mrp',MrpReadOnlyViewSet,basename='mrp')
router.register(r'purchase-order',PurchaseOrderReadOnlyViewSet,basename='purchaseorder-detail')
router.register(r'material-receipt-list',MaterialReceiptListViewSet,basename='material-receipt-list')
router.register(r'material-receipt-schedule-management',MaterialReceiptScheduleManagementViewSet,basename='material-receipt-schedule-management')
router.register(r'material-receipt-schedule',MaterialReceiptScheduleReadOnlyViewSet,basename='material-receipt-schedule')
router.register(r'material-order-management',MaterialOrderManagementViewSet,basename='material-order-management')
router.register(r'purchase-order-management',PurchaseOrderManagementViewSet,basename='purchase-order-management')
router.register(r'status-purchase-order-management',StatusPurchaseOrderManagementViewSet,basename='status-purchase-order-management')
router.register(r'close-purchase-order-management',CloseStatusPurchaseOrderViewSet,basename='close-purchase-order-management')

router.register(r'material-list',MaterialDetailListViewSet,basename='material-list')

router.register(r'report-material-usage-and-order',MaterialUsageAndOrderViewSet,basename='report-material-usage-and-order')


urlpatterns = [
   path('',include(router.urls)),
]
