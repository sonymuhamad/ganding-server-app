from rest_framework.routers import DefaultRouter
# from .views import CustomerViewset
from django.urls import path,include
from .views import MrpReadOnlyViewSet,PurchaseOrderReadOnlyViewSet,PurchaseOrderManagementViewSet,MaterialOrderManagementViewSet

router = DefaultRouter()

po_management_post = PurchaseOrderManagementViewSet.as_view({
   'post':'create',
})

po_management_put_and_delete = PurchaseOrderManagementViewSet.as_view({
   'put':'update',
   'delete':'destroy',
})

mo_management_post = MaterialOrderManagementViewSet.as_view({
   'post':'create',
})

mo_management_put_and_delete = MaterialOrderManagementViewSet.as_view({
   'put':'update',
   'delete':'destroy',
})



router.register(r'mrp-detail',MrpReadOnlyViewSet,basename='mrp_detail')
router.register(r'purchaseorder-detail',PurchaseOrderReadOnlyViewSet,basename='purchaseorder-detail')

# router.register(r'customer',CustomerViewset,basename='customer')


urlpatterns = [
   path('',include(router.urls)),
   path('purchaseorder-management/<int:pk>/',po_management_put_and_delete,name='purchaseorder-management'),
   path('purchaseorder-management/',po_management_post,name='purchaseorder-management'),
   path('materialorder-management/',mo_management_post,name='materialorder-management'),
   path('materialorder-management/<int:pk>/',mo_management_put_and_delete,name='materialorder-management'),

]
