from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path('o/',include('oauth2_provider.urls',namespace='oauth2_provider')),
    path('api/',include('marketing.urls')),
    path('api/',include('manager.urls')),
    path('api/',include('purchasing.urls')),
    path('api/',include('ppic.urls')),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

