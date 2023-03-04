from rest_framework.routers import DefaultRouter
from django.urls import path,include

from purchasing.views.supplier_module_view import SupplierViewSet,SupplierManagementViewSet,SupplierReadOnlyViewSet

from purchasing.views.purchase_order_module_view import MaterialListViewSet,PurchaseOrderReadOnlyViewSet,MaterialReceiptListViewSet,MaterialReceiptScheduleManagementViewSet,MaterialReceiptScheduleReadOnlyViewSet,MaterialOrderManagementViewSet,PurchaseOrderManagementViewSet,StatusPurchaseOrderManagementViewSet,CloseStatusPurchaseOrderViewSet,MrpReadOnlyViewSet

from purchasing.views.purchasing_dashboard_view import MaterialUsageAndOrderViewSet

router = DefaultRouter()


router.register(r'suppliers',SupplierViewSet,basename='supplier')
router.register(r'supplier-management',SupplierManagementViewSet,basename='supplier-management')  
router.register(r'supplier-detail',SupplierReadOnlyViewSet,basename='supplier-detail')
router.register(r'supplier-material-list',MaterialListViewSet,basename='supplier-material-list')
router.register(r'supplier-mrps',MrpReadOnlyViewSet,basename='supplier-mrps')

router.register(r'purchase-order',PurchaseOrderReadOnlyViewSet,basename='purchase-order')
router.register(r'material-receipt-list',MaterialReceiptListViewSet,basename='material-receipt-list')
router.register(r'material-receipt-schedule-management',MaterialReceiptScheduleManagementViewSet,basename='material-receipt-schedule-management')
router.register(r'material-receipt-schedule',MaterialReceiptScheduleReadOnlyViewSet,basename='material-receipt-schedule')
router.register(r'material-order-management',MaterialOrderManagementViewSet,basename='material-order-management')
router.register(r'purchase-order-management',PurchaseOrderManagementViewSet,basename='purchase-order-management')
router.register(r'status-purchase-order-management',StatusPurchaseOrderManagementViewSet,basename='status-purchase-order-management')
router.register(r'close-purchase-order-management',CloseStatusPurchaseOrderViewSet,basename='close-purchase-order-management')


router.register(r'report-material-usage-and-order',MaterialUsageAndOrderViewSet,basename='report-material-usage-and-order')


urlpatterns = [
   path('',include(router.urls)),
]
