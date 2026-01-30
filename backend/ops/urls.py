"""
URL configuration for OPS project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView


def health_check(request):
    """Health check endpoint for container orchestration."""
    health = {'status': 'healthy', 'checks': {}}

    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        health['checks']['database'] = 'ok'
    except Exception as e:
        health['checks']['database'] = f'error: {str(e)}'
        health['status'] = 'unhealthy'

    # Redis check
    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            health['checks']['cache'] = 'ok'
        else:
            health['checks']['cache'] = 'error: cache not responding'
            health['status'] = 'unhealthy'
    except Exception as e:
        health['checks']['cache'] = f'error: {str(e)}'
        health['status'] = 'unhealthy'

    status_code = 200 if health['status'] == 'healthy' else 503
    return JsonResponse(health, status=status_code)


urlpatterns = [
    # Health check
    path('api/health/', health_check, name='health_check'),

    # Admin
    path('admin/', admin.site.urls),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # API v1
    path('api/v1/auth/', include('apps.auth.urls')),
    path('api/v1/users/', include('apps.auth.urls_users')),
    path('api/v1/departments/', include('apps.auth.urls_departments')),
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
