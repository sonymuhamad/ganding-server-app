from rest_framework.routers import DefaultRouter
from .views import AuthViewSet,UserViewSet
from django.urls import path,include

router = DefaultRouter()

auth_list = AuthViewSet.as_view({
    'post':'auth'
}) 

router.register(r'user',UserViewSet,basename='user')

urlpatterns = [
    path('',include(router.urls)),
    path('auth/',auth_list,name='auth_list'),
]
