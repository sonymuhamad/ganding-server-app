from rest_framework.routers import DefaultRouter
from .views import *
from django.urls import path,include
from .auth import AuthViewSet,LogoutViewSet

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


router.register(r'report-delivery-note',ReportDeliveryNoteCustomerViewSet,basename='report-delivery-note')
router.register(r'report-salesorder',ReportCustomerSalesOrderViewSet,basename='report-salesorder')
router.register(r'report-mrp',ReportMrpViewSet)
router.register(r'report-purchaseorder',ReportSupplierPurchaseOrderViewSet)

urlpatterns = [
    path('',include(router.urls)),
    path('sign-in/',auth_list,name='auth'),  
]
