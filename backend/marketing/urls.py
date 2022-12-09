from rest_framework.routers import DefaultRouter
from .views import *
from django.urls import path,include

router = DefaultRouter()

put_product_delivery_management = ProductDeliveryManagementSerializer.as_view({
    'put':'update'
})

router.register(r'customer',CustomerViewset,basename='customer')
router.register(r'customer-management',CustomerManagementViewSet,basename='customer-management') ######
router.register(r'customer-detail',CustomerDetailReadOnlyViewSet,basename='detail-customer')

router.register(r'delivery-note',DeliveryNoteReadOnlyViewSet,basename='delivery-note')
router.register(r'data-sales-order',SalesOrderReadOnlyViewSet,basename='data-sales-order')
router.register(r'sales-order-management',SalesOrderManagementViewSet,basename='sales-order-management')
router.register(r'sales-order-list',SalesOrderListReadOnlyViewSet,basename='sales-order-list')

router.register(r'product-order-management',ProductOrderManagementViewSet,basename='product-order-management')
router.register(r'product-customer',ProductCustomerViewSet,basename='product-customer')
router.register(r'delivery-notes',DeliveryNoteListViewSet,basename='delivery-notes')
router.register(r'product-detail',ProductDetailViewSet,basename='product-detail')
router.register(r'sales-order-this-month',SalesOrderListThisMonthViewSet,basename='sales-order-this-month')
router.register(r'delivery-notes-pending',PendingDeliveryNoteListViewSet,basename='delivery-notes-pending')

urlpatterns = [
    path('',include(router.urls)),
    path('productdelivery-management-put/<int:pk>/',put_product_delivery_management,name='productdelivery-management'),
]
