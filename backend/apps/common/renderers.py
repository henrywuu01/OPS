"""
Custom renderers for standardized API responses.
"""
from rest_framework.renderers import JSONRenderer
from django.utils import timezone


class CustomJSONRenderer(JSONRenderer):
    """
    Custom JSON renderer that wraps responses in standard format.
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get('response') if renderer_context else None

        # If response already has error format (from exception handler), don't wrap
        if isinstance(data, dict) and 'code' in data and 'message' in data:
            return super().render(data, accepted_media_type, renderer_context)

        # Wrap successful responses
        if response and response.status_code < 400:
            wrapped_data = {
                'code': 0,
                'message': 'success',
                'data': data,
                'timestamp': int(timezone.now().timestamp() * 1000),
            }
            return super().render(wrapped_data, accepted_media_type, renderer_context)

        return super().render(data, accepted_media_type, renderer_context)
