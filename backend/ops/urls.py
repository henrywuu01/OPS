"""
URL configuration for OPS project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # API v1
    path('api/v1/auth/', include('apps.auth.urls')),
    path('api/v1/users/', include('apps.auth.urls_users')),
    path('api/v1/roles/', include('apps.auth.urls_roles')),
    path('api/v1/jobs/', include('apps.scheduler.urls')),
    path('api/v1/job-flows/', include('apps.scheduler.urls_flows')),
    path('api/v1/reports/', include('apps.report.urls')),
    path('api/v1/datasources/', include('apps.report.urls_datasources')),
    path('api/v1/config/', include('apps.config.urls')),
    path('api/v1/workflows/', include('apps.workflow.urls')),
    path('api/v1/approvals/', include('apps.workflow.urls_approvals')),
    path('api/v1/audit/', include('apps.audit.urls')),
    path('api/v1/messages/', include('apps.notification.urls')),
    path('api/v1/notifications/', include('apps.notification.urls_notifications')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
