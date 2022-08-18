from rest_framework.routers import DefaultRouter
from .views import CustomerViewset
from django.urls import path,include

router = DefaultRouter()


router.register(r'customer',CustomerViewset,basename='customer')


urlpatterns = [
    # path('',customer_list,name='customer_list')
    path('',include(router.urls)),
]
