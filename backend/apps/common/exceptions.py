"""
Custom exception handlers and exceptions.
"""
from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from rest_framework import status
from django.utils import timezone


class BusinessException(APIException):
    """Base exception for business logic errors."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '业务处理失败'
    default_code = 'business_error'


class PermissionDeniedException(APIException):
    """Permission denied exception."""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = '无权限访问'
    default_code = 'permission_denied'


class ResourceNotFoundException(APIException):
    """Resource not found exception."""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = '资源不存在'
    default_code = 'not_found'


class ResourceConflictException(APIException):
    """Resource conflict exception."""
    status_code = status.HTTP_409_CONFLICT
    default_detail = '资源冲突'
    default_code = 'conflict'


# Error code mapping
ERROR_CODES = {
    400: 40001,
    401: 40101,
    403: 40301,
    404: 40401,
    409: 40901,
    500: 50001,
    503: 50301,
}


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns standardized error responses.
    """
    response = exception_handler(exc, context)

    if response is not None:
        # Get error code
        status_code = response.status_code
        error_code = ERROR_CODES.get(status_code, status_code * 100 + 1)

        # Build error response
        error_data = {
            'code': error_code,
            'message': str(exc.detail) if hasattr(exc, 'detail') else str(exc),
            'timestamp': int(timezone.now().timestamp() * 1000),
        }

        # Add field errors if available
        if hasattr(exc, 'detail') and isinstance(exc.detail, dict):
            errors = []
            for field, messages in exc.detail.items():
                if isinstance(messages, list):
                    for msg in messages:
                        errors.append({'field': field, 'message': str(msg)})
                else:
                    errors.append({'field': field, 'message': str(messages)})
            if errors:
                error_data['errors'] = errors

        response.data = error_data

    return response
