from django.contrib import admin
from django.urls import path,include

urlpatterns = [
    path("admin/", admin.site.urls),
    path('o/',include('oauth2_provider.urls',namespace='oauth2_provider')),
    path('',include('marketing.urls')),
    path('',include('manager.urls')),
    path('',include('purchasing.urls')),
    path('',include('ppic.urls')),
]

