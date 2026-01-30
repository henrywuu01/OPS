"""
Caching utilities for performance optimization.
"""
import functools
import hashlib
import json
from typing import Optional, Callable, Any
from django.core.cache import cache
from django.conf import settings


def cache_key(*args, **kwargs) -> str:
    """Generate a cache key from arguments."""
    key_data = json.dumps({'args': args, 'kwargs': kwargs}, sort_keys=True, default=str)
    return hashlib.md5(key_data.encode()).hexdigest()


def cached(
    timeout: int = 300,
    key_prefix: str = '',
    key_func: Callable = None
):
    """
    Decorator for caching function results.

    Usage:
        @cached(timeout=60, key_prefix='user')
        def get_user(user_id):
            return User.objects.get(id=user_id)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if key_func:
                cache_key_str = key_func(*args, **kwargs)
            else:
                cache_key_str = cache_key(*args, **kwargs)

            full_key = f"{key_prefix}:{func.__name__}:{cache_key_str}"

            result = cache.get(full_key)
            if result is not None:
                return result

            result = func(*args, **kwargs)
            cache.set(full_key, result, timeout)
            return result

        wrapper.invalidate = lambda *args, **kwargs: cache.delete(
            f"{key_prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"
        )

        return wrapper
    return decorator


def cached_method(timeout: int = 300, key_prefix: str = ''):
    """
    Decorator for caching instance method results.
    Uses instance id in cache key.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            instance_key = getattr(self, 'id', id(self))
            cache_key_str = cache_key(instance_key, *args, **kwargs)
            full_key = f"{key_prefix}:{func.__name__}:{cache_key_str}"

            result = cache.get(full_key)
            if result is not None:
                return result

            result = func(self, *args, **kwargs)
            cache.set(full_key, result, timeout)
            return result
        return wrapper
    return decorator


class CacheService:
    """Service for common caching operations."""

    # Cache timeouts (in seconds)
    SHORT = 60           # 1 minute
    MEDIUM = 300         # 5 minutes
    LONG = 3600          # 1 hour
    VERY_LONG = 86400    # 1 day

    @staticmethod
    def get_or_set(key: str, func: Callable, timeout: int = 300) -> Any:
        """Get value from cache or compute and set it."""
        result = cache.get(key)
        if result is None:
            result = func()
            cache.set(key, result, timeout)
        return result

    @staticmethod
    def invalidate_pattern(pattern: str):
        """Invalidate all keys matching pattern (Redis only)."""
        if hasattr(cache, 'delete_pattern'):
            cache.delete_pattern(pattern)

    @staticmethod
    def invalidate_keys(*keys: str):
        """Invalidate multiple cache keys."""
        cache.delete_many(keys)

    # Common cache key builders
    @staticmethod
    def user_key(user_id: int, suffix: str = '') -> str:
        return f"user:{user_id}:{suffix}" if suffix else f"user:{user_id}"

    @staticmethod
    def permission_key(user_id: int) -> str:
        return f"permissions:{user_id}"

    @staticmethod
    def role_key(role_id: int) -> str:
        return f"role:{role_id}"

    @staticmethod
    def config_key(table: str, record_id: int = None) -> str:
        if record_id:
            return f"config:{table}:{record_id}"
        return f"config:{table}"


# Cache invalidation signals
def invalidate_user_cache(user_id: int):
    """Invalidate all user-related caches."""
    cache.delete(CacheService.user_key(user_id))
    cache.delete(CacheService.permission_key(user_id))


def invalidate_role_cache(role_id: int):
    """Invalidate role and related user permission caches."""
    cache.delete(CacheService.role_key(role_id))
    # Note: Would need to invalidate all users with this role


def invalidate_config_cache(table: str, record_id: int = None):
    """Invalidate configuration caches."""
    if record_id:
        cache.delete(CacheService.config_key(table, record_id))
    else:
        cache.delete(CacheService.config_key(table))
