from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path('o/',include('oauth2_provider.urls',namespace='oauth2_provider')),
    path('',include('marketing.urls')),
    path('',include('manager.urls')),
    path('',include('purchasing.urls')),
    path('',include('ppic.urls')),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

