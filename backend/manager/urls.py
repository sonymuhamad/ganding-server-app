from rest_framework.routers import DefaultRouter
from django.urls import path,include
from .auth import AuthViewSet,LogoutViewSet

from manager.views.user_module_view import UserManagementViewSet,UserReadOnlyViewSet,GroupReadOnlyViewSet,UserGroupManagementAddViewSet,UserGroupManagementDeleteViewSet,PermissionListReadOnlyViewSet,UserPermissionAddManagementViewSet,UserPermissionDeleteManagementViewSet

from manager.views.purchase_report_module_view import ReportMaterialOrderReadOnlyViewSet,ReportSupplierOrderReadOnlyViewSet,MaterialOrderListReadOnlyViewSet,MaterialReceiptListReadOnlyViewSet

from views.production_report_module_view import ReportProductionReadOnlyViewSet,OperatorReadOnlyViewSet,MachineReadOnlyViewSet

from views.sales_report_module_view import ReportCustomerAndOrderedProductViewSet,ReportProductDeliverCustomerReadOnlyViewSet,ReportProductInProgressReadOnlyViewSet,ReportProductOrderReadOnlyViewSet


from views.manager_dashboard_view import ReportPresentageDeliveryTimeLinessReadOnlyViewSet,ReportPresentageTimeLinessMaterialOrder,DeliveryNoteCustomerReadOnlyViewSet,DeliveryNoteMaterialReadOnlyViewSet,ProductionReportReadOnlyViewSet

router = DefaultRouter()

auth_list = AuthViewSet.as_view({
    'post':'auth'
})
router.register(r'sign-out',LogoutViewSet,basename='logout')


router.register(r'user-management',UserManagementViewSet,basename='user-management')
router.register(r'user',UserReadOnlyViewSet,basename='user')
router.register(r'group',GroupReadOnlyViewSet,basename='group')
router.register(r'user-add-group',UserGroupManagementAddViewSet,basename='user-add-group')
router.register(r'user-remove-group',UserGroupManagementDeleteViewSet,basename='user-remove-group')

router.register(r'permission-list',PermissionListReadOnlyViewSet,basename='permission-list')
router.register(r'user-add-permission-management',UserPermissionAddManagementViewSet,basename='permission-management')
router.register(r'user-remove-permission-management',UserPermissionDeleteManagementViewSet,basename='permission-remove-management')

router.register(r'report-sales-order',ReportProductOrderReadOnlyViewSet,basename='report-sales-order')
router.register(r'report-customer-product-order',ReportCustomerAndOrderedProductViewSet,basename='report-customer-product-order')
router.register(r'report-product-in-progress',ReportProductInProgressReadOnlyViewSet,basename='report-product-in-progress')
router.register(r'product-delivery-list',ReportProductDeliverCustomerReadOnlyViewSet,basename='product-delivery-list')

router.register(r'report-purchase-order',ReportMaterialOrderReadOnlyViewSet,basename='report-purchase-order')
router.register(r'material-order-list',MaterialOrderListReadOnlyViewSet,basename='material-order-list')
router.register(r'material-receipt-list',MaterialReceiptListReadOnlyViewSet,basename='material-receipt-list')
router.register(r'report-supplier-material-order',ReportSupplierOrderReadOnlyViewSet,basename='report-supplier-material-order')


router.register(r'report-production',ReportProductionReadOnlyViewSet,basename='report-production')
router.register(r'report-operator',OperatorReadOnlyViewSet,basename='report-operator')
router.register(r'report-machine',MachineReadOnlyViewSet,basename='report-machine')

router.register(r'report-timeliness-delivery',ReportPresentageDeliveryTimeLinessReadOnlyViewSet,basename='report-timeliness-delivery')
router.register(r'report-timeliness-receipt',ReportPresentageTimeLinessMaterialOrder,basename='report-timeliness-receipt')
router.register(r'report-delivery-product',DeliveryNoteCustomerReadOnlyViewSet,basename='report-delivery-product')
router.register(r'report-receipt-material',DeliveryNoteMaterialReadOnlyViewSet,basename='report-receipt-material')
router.register(r'report-production-weekly',ProductionReportReadOnlyViewSet,basename='report-production-weekly')


urlpatterns = [
    path('',include(router.urls)),
    path('sign-in/',auth_list,name='auth'),  
]
