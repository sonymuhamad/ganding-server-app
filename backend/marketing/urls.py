from rest_framework.routers import DefaultRouter
from .views import CustomerViewset,SalesOrderManagementViewSet,SalesOrderReadOnlyViewSet,DeliveryNoteReadOnlyViewSet,ProductDeliveryManagementSerializer,ProductOrderManagementViewSet

from django.urls import path,include

router = DefaultRouter()

list_read_only = SalesOrderReadOnlyViewSet.as_view({
    'get':'list'
})
retrieve_read_only = SalesOrderReadOnlyViewSet.as_view({
    'get':'retrieve'
})

post_sales_order_management = SalesOrderManagementViewSet.as_view({
    'post':'create'
})

put_delete_sales_order_management = SalesOrderManagementViewSet.as_view({
    'put':'update',
    'delete':'destroy',
})

put_product_delivery_management = ProductDeliveryManagementSerializer.as_view({
    'put':'update'
})

post_product_order_management = ProductOrderManagementViewSet.as_view({
    'post':'create',
})

put_and_delete_product_order_management = ProductOrderManagementViewSet.as_view({
    'put':'update',
    'delete':'destroy',
})

router.register(r'customer',CustomerViewset,basename='customer')
router.register(r'delivery-note',DeliveryNoteReadOnlyViewSet,basename='delivery-note')

urlpatterns = [
    path('',include(router.urls)),
    path('salesorder-management/',list_read_only,name='salesorder-management'),
    path('salesorder-management-post/',post_sales_order_management,name='salesorder-management'),
    path('salesorder-management/<int:pk>/',retrieve_read_only,name='salesorder-management'),
    path('salesorder-management-put/<int:pk>/',put_delete_sales_order_management,name='salesorder-management'),
    path('productdelivery-management-put/<int:pk>/',put_product_delivery_management,name='productdelivery-management'),
    path('product-order-management/',post_product_order_management,name='productorder-management'),
    path('product-order-management/<int:pk>/',put_and_delete_product_order_management,name='productorder-management')

]
