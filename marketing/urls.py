from rest_framework.routers import DefaultRouter
from django.urls import path,include

from marketing.views.customer_module_view import CustomerViewset,CustomerManagementViewSet,ProductCustomerViewSet,CustomerProductDeliverCustomerReadOnlyViewSet,CustomerPendingInvoiceReadOnlyViewSet

from marketing.views.sales_order_module_view import SalesOrderListReadOnlyViewSet,DeliveryScheduleManagementViewSet,ProductOrderManagementViewSet,SalesOrderManagementViewSet,DeliveryScheduleReadOnlyViewSet,ProductDeliverCustomerReadOnlyViewSet

from marketing.views.invoice_module_view import InvoiceManagementViewSet,InvoiceReadOnlyViewSet,SalesOrderDoneListViewSet

from marketing.views.marketing_dashboard_view import ReportProductOrderViewSet,InProgressProductOderViewSet,FinishedSalesOrderViewSet

router = DefaultRouter()


router.register(r'customers',CustomerViewset,basename='customers')
router.register(r'customer-management',CustomerManagementViewSet,basename='customer-management') 
router.register(r'customer/products',ProductCustomerViewSet,basename='customer/products')
router.register(r'customer/product-deliveries',CustomerProductDeliverCustomerReadOnlyViewSet,basename='customer/product-deliveries')
router.register(r'customer/pending-invoice',CustomerPendingInvoiceReadOnlyViewSet,basename='customer/pending-invoice')

router.register(r'sales-orders',SalesOrderListReadOnlyViewSet,basename='sales-order-list')
router.register(r'delivery-schedule-management',DeliveryScheduleManagementViewSet,basename='delivery-schedule-management')
router.register(r'product-order-management',ProductOrderManagementViewSet,basename='product-order-management')
router.register(r'sales-order-management',SalesOrderManagementViewSet,basename='sales-order-management')
router.register(r'schedules/delivery',DeliveryScheduleReadOnlyViewSet,basename='delivery-schedule')
router.register(r'product-delivery',ProductDeliverCustomerReadOnlyViewSet,basename='product-delivery')

router.register(r'invoice-management',InvoiceManagementViewSet,basename='invoice-management')
router.register(r'invoice',InvoiceReadOnlyViewSet,basename='invoice')
router.register(r'closed-sales-order-list',SalesOrderDoneListViewSet,basename='closed-sales-order-list')

router.register(r'report-product-order',ReportProductOrderViewSet,basename='report-product-order')
router.register(r'in-progress-product-order',InProgressProductOderViewSet,basename='in-progress-product-order')
router.register(r'finished-sales-order-list',FinishedSalesOrderViewSet,basename='finished-sales-order-list')


urlpatterns = [
    path('',include(router.urls)),
]
