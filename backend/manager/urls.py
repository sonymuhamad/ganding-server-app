from rest_framework.routers import DefaultRouter
from .views import AuthViewSet, ReportSalesOrderViewSet,UserViewSet,UserActivityViewSet,ReportMrpViewSet
from django.urls import path,include

router = DefaultRouter()

auth_list = AuthViewSet.as_view({
    'post':'auth'
})

user_activity = UserActivityViewSet.as_view({
    'get':'list'
})

report_mrp = ReportMrpViewSet.as_view({
    'get':'list'
})

report_salesorder = ReportSalesOrderViewSet.as_view({
    'get':'list'
})

router.register(r'user',UserViewSet,basename='user')

urlpatterns = [
    path('',include(router.urls)),
    path('auth/',auth_list,name='auth_list'),
    path('activity/',user_activity,name='activity'),
    path('report-mrp/',report_mrp,name='reportmrp'),
    path('report-salesorder/',report_salesorder,name='reportsalesorder'),
]
