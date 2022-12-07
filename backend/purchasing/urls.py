from rest_framework.routers import DefaultRouter
from django.urls import path,include
from .views import *
from ppic.views import MrpReadOnlyViewSet,MaterialListViewSet as MaterialList,DeliveryNoteMaterialReadOnlyViewSet,ReceiptNoteSubcontReadOnlyViewSet,DeliveryNoteSubcontReadOnlyViewSet

router = DefaultRouter()


router.register(r'supplier',SupplierManagementViewSet,basename='supplier')
router.register(r'supplier-detail',SupplierReadOnlyViewSet,basename='supplier-detail')
router.register(r'material-list',MaterialList,basename='material-list')

router.register(r'supplier-material-list',MaterialListViewSet,basename='supplier-material-list')
router.register(r'mrp',MrpReadOnlyViewSet,basename='mrp')
router.register(r'purchase-order',PurchaseOrderReadOnlyViewSet,basename='purchaseorder-detail')
router.register(r'material-receipt-list',MaterialReceiptListViewSet,basename='material-receipt-list')

router.register(r'delivery-note-material',DeliveryNoteMaterialReadOnlyViewSet,basename='delivery-note-material')
router.register(r'delivery-note-subcont',DeliveryNoteSubcontReadOnlyViewSet,basename='delivery-note-subcont')
router.register(r'receipt-note-subcont',ReceiptNoteSubcontReadOnlyViewSet,basename='receipt-note-subcont')

router.register(r'material-receipt-schedule-management',MaterialReceiptScheduleManagementViewSet,basename='material-receipt-schedule-management')
router.register(r'material-receipt-schedule',MaterialReceiptScheduleReadOnlyViewSet,basename='material-receipt-schedule')
router.register(r'report-material-usage-and-order',MaterialUsageAndOrderViewSet,basename='report-material-usage-and-order')


router.register(r'material-order-management',MaterialOrderManagementViewSet,basename='material-order-management')
router.register(r'purchase-order-management',PurchaseOrderManagementViewSet,basename='purchase-order-management')
router.register(r'status-purchase-order-management',StatusPurchaseOrderManagementViewSet,basename='status-purchase-order-management')

urlpatterns = [
   path('',include(router.urls)),
]
