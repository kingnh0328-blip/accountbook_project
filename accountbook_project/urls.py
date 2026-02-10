from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('transactions/', include('transactions.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('report/', include('report.urls')),
    path('presentation/', TemplateView.as_view(template_name='presentation.html'), name='presentation'),
]



if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)