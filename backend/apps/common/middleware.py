"""
Common middleware for OPS system.
"""
import threading

_thread_locals = threading.local()


def get_current_user():
    """Get the current user from thread local storage."""
    return getattr(_thread_locals, 'user', None)


def get_current_request():
    """Get the current request from thread local storage."""
    return getattr(_thread_locals, 'request', None)


class CurrentUserMiddleware:
    """
    Middleware to store current user in thread local storage.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.user = getattr(request, 'user', None)
        _thread_locals.request = request
        response = self.get_response(request)
        return response
