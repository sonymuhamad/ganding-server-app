from rest_framework.routers import DefaultRouter
from .views import AuthViewSet,UserViewSet,ReportMrpViewSet,ReportSupplierPurchaseOrderViewSet,ReportCustomerSalesOrderViewSet,ReportDeliveryNoteCustomerViewSet,LogoutViewSet
from django.urls import path,include

router = DefaultRouter()

auth_list = AuthViewSet.as_view({
    'post':'auth'
})


report_mrp = ReportMrpViewSet.as_view({
    'get':'list'
})

report_purchaseorder = ReportSupplierPurchaseOrderViewSet.as_view({
    'get':'list'
})


router.register(r'user',UserViewSet,basename='user')
router.register(r'report-delivery-note',ReportDeliveryNoteCustomerViewSet,basename='report-delivery-note')
router.register(r'report-salesorder',ReportCustomerSalesOrderViewSet,basename='report-salesorder')
router.register(r'sign-out',LogoutViewSet,basename='logout')

urlpatterns = [
    path('',include(router.urls)),
    path('sign-in/',auth_list,name='auth'),
    path('report-mrp/',report_mrp,name='reportmrp'),
    path('report-purchaseorder/',report_purchaseorder,name='reportpurchaseorder'),
    
]
