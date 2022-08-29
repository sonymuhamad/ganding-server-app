from rest_framework.routers import DefaultRouter
from django.urls import path,include

from .views import ProductCustomerReadOnlyViewSet,ProductManagementViewSet


router = DefaultRouter()

product_management_post = ProductManagementViewSet.as_view({
    'post':'create',
}) 
product_management_put_and_delete = ProductManagementViewSet.as_view({
    'put':'update',
    'delete':'destroy',
}) 

router.register(r'product-detail',ProductCustomerReadOnlyViewSet,basename='product-detail')


urlpatterns = [
    path('',include(router.urls)),
    path('product-management/',product_management_post,name='produt-management'),
    path('product-management/<int:pk>/',product_management_put_and_delete,name='product-management'),
    
]
