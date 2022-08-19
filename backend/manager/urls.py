from rest_framework.routers import DefaultRouter
from .views import AuthViewSet
from django.urls import path,include

router = DefaultRouter()

auth_list = AuthViewSet.as_view({
    'post':'auth'
}) 


urlpatterns = [
    path('auth/',auth_list,name='auth_list'),
]
