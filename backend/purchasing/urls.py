from rest_framework.routers import DefaultRouter
from django.urls import path,include
from .views import MrpReadOnlyViewSet,PurchaseOrderReadOnlyViewSet,PurchaseOrderManagementViewSet,MaterialOrderManagementViewSet,SupplierManagementViewSet

router = DefaultRouter()

router.register(r'mrp-detail',MrpReadOnlyViewSet,basename='mrp_detail')
router.register(r'purchaseorder-detail',PurchaseOrderReadOnlyViewSet,basename='purchaseorder-detail')
router.register(r'supplier',SupplierManagementViewSet,basename='supplier')
router.register(r'material-order-management',MaterialOrderManagementViewSet,basename='material-order-management')
router.register(r'purchase-order-management',PurchaseOrderManagementViewSet,basename='purchase-order-management')

urlpatterns = [
   path('',include(router.urls)),
]
