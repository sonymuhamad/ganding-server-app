from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path('o/',include('oauth2_provider.urls',namespace='oauth2_provider')),
    path('marketing/',include('marketing.urls')),
    path('plant-manager/',include('manager.urls')),
    path('purchasing/',include('purchasing.urls')),
    path('ppic/',include('ppic.urls')),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

