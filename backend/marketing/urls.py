from rest_framework.routers import DefaultRouter
from .views import CustomerViewset,SalesOrderManagementViewSet,SalesOrderReadOnlyViewSet,DeliveryNoteReadOnlyViewSet,ProductDeliveryManagementSerializer,ProductOrderManagementViewSet,CustomerDetailReadOnlyViewSet,SalesOrderListReadOnlyViewSet

from django.urls import path,include

router = DefaultRouter()

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
router.register(r'customer-detail',CustomerDetailReadOnlyViewSet,basename='detail-customer')
router.register(r'delivery-note',DeliveryNoteReadOnlyViewSet,basename='delivery-note')
router.register(r'data-sales-order',SalesOrderReadOnlyViewSet,basename='data-sales-order')
router.register(r'sales-order-management',SalesOrderManagementViewSet,basename='sales-order-management')
router.register(r'sales-order-list',SalesOrderListReadOnlyViewSet,basename='sales-order-list')


urlpatterns = [
    path('',include(router.urls)),
    path('productdelivery-management-put/<int:pk>/',put_product_delivery_management,name='productdelivery-management'),
    path('product-order-management/',post_product_order_management,name='productorder-management'),
    path('product-order-management/<int:pk>/',put_and_delete_product_order_management,name='productorder-management')

]
