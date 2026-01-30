"""
Audit log middleware.
"""
import json
import traceback
from django.utils import timezone
from django.conf import settings


class AuditLogMiddleware:
    """
    Middleware to log all API requests for auditing.
    """

    EXCLUDE_PATHS = [
        '/api/docs/',
        '/api/schema/',
        '/admin/',
        '/static/',
        '/media/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip excluded paths
        if any(request.path.startswith(path) for path in self.EXCLUDE_PATHS):
            return self.get_response(request)

        # Record request start time
        request._audit_start_time = timezone.now()

        # Get request body
        try:
            if request.content_type == 'application/json':
                request._audit_body = request.body.decode('utf-8')
            else:
                request._audit_body = None
        except Exception:
            request._audit_body = None

        response = self.get_response(request)

        # Log the request (will be implemented in M6)
        # self._log_request(request, response)

        return response

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip
