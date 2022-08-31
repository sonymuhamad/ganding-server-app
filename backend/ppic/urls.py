from rest_framework.routers import DefaultRouter
from django.urls import path,include

from .views import MrpManagementViewSet, ProductCustomerReadOnlyViewSet,ProductManagementViewSet,MaterialSupplierReadOnlyViewSet,MaterialSerializer,MrpReadOnlyViewSet


router = DefaultRouter()

product_management_post = ProductManagementViewSet.as_view({
    'post':'create',
}) 
product_management_put_and_delete = ProductManagementViewSet.as_view({
    'put':'update',
    'delete':'destroy',
}) 

mrp_management_post = MrpManagementViewSet.as_view({
    'post':'create',
})

mrp_management_put_and_delete = MrpManagementViewSet.as_view({
    'put':'update',
    'delete':'destroy',
})

router.register(r'product-detail',ProductCustomerReadOnlyViewSet,basename='product-detail')
router.register(r'material-detail',MaterialSupplierReadOnlyViewSet,basename='material-detail')
router.register(r'material',MaterialSerializer,basename='material')
router.register(r'mrp-details',MrpReadOnlyViewSet,basename='mrp-details')

urlpatterns = [
    path('',include(router.urls)),
    path('product-management/',product_management_post,name='produt-management'),
    path('product-management/<int:pk>/',product_management_put_and_delete,name='product-management'),
    path('mrp-management/',mrp_management_post,name='mrp-management'),
    path('mrp-management/<int:pk>/',mrp_management_put_and_delete,name='mrp-management'),    
]
