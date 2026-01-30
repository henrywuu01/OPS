"""
Security utilities and middleware for M9 - Security Hardening.
"""
import time
import hashlib
import secrets
from typing import Optional
from django.core.cache import cache
from django.http import JsonResponse
from django.conf import settings


class RateLimiter:
    """
    Token bucket rate limiter using Redis.

    Usage:
        limiter = RateLimiter()
        if limiter.is_allowed('user:123', limit=10, window=60):
            # Process request
        else:
            # Rate limited
    """

    def __init__(self, prefix: str = 'ratelimit'):
        self.prefix = prefix

    def _get_key(self, identifier: str) -> str:
        return f"{self.prefix}:{identifier}"

    def is_allowed(
        self,
        identifier: str,
        limit: int = 60,
        window: int = 60
    ) -> bool:
        """
        Check if request is allowed within rate limit.

        Args:
            identifier: Unique identifier (e.g., IP, user_id)
            limit: Maximum requests allowed
            window: Time window in seconds

        Returns:
            True if allowed, False if rate limited
        """
        key = self._get_key(identifier)
        current = cache.get(key, 0)

        if current >= limit:
            return False

        # Increment counter
        cache.set(key, current + 1, window)
        return True

    def get_remaining(self, identifier: str, limit: int = 60) -> int:
        """Get remaining requests for identifier."""
        key = self._get_key(identifier)
        current = cache.get(key, 0)
        return max(0, limit - current)


class RateLimitMiddleware:
    """
    Middleware for API rate limiting.

    Add to MIDDLEWARE in settings:
        'apps.common.security.RateLimitMiddleware',

    Configure in settings:
        RATE_LIMIT = {
            'DEFAULT': (100, 60),  # 100 requests per 60 seconds
            'STRICT': (10, 60),    # For sensitive endpoints
        }
    """

    EXEMPT_PATHS = [
        '/api/health/',
        '/api/docs/',
        '/api/schema/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response
        self.limiter = RateLimiter()

    def __call__(self, request):
        # Skip rate limiting for exempt paths
        if any(request.path.startswith(path) for path in self.EXEMPT_PATHS):
            return self.get_response(request)

        # Get identifier (prefer user ID, fallback to IP)
        if hasattr(request, 'user') and request.user.is_authenticated:
            identifier = f"user:{request.user.id}"
            limit, window = getattr(settings, 'RATE_LIMIT', {}).get('DEFAULT', (200, 60))
        else:
            identifier = f"ip:{self._get_client_ip(request)}"
            limit, window = getattr(settings, 'RATE_LIMIT', {}).get('ANONYMOUS', (60, 60))

        # Check rate limit
        if not self.limiter.is_allowed(identifier, limit, window):
            return JsonResponse({
                'error': '请求过于频繁，请稍后再试',
                'code': 'rate_limited'
            }, status=429)

        response = self.get_response(request)

        # Add rate limit headers
        remaining = self.limiter.get_remaining(identifier, limit)
        response['X-RateLimit-Limit'] = str(limit)
        response['X-RateLimit-Remaining'] = str(remaining)
        response['X-RateLimit-Reset'] = str(window)

        return response

    def _get_client_ip(self, request) -> str:
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '127.0.0.1')


class SecurityHeadersMiddleware:
    """
    Middleware to add security headers.

    Add to MIDDLEWARE in settings:
        'apps.common.security.SecurityHeadersMiddleware',
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Content Security Policy (customize as needed)
        if not response.get('Content-Security-Policy'):
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self'"
            )

        # Strict Transport Security (only in production with HTTPS)
        if not settings.DEBUG:
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        return response


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(length)


def hash_sensitive_data(data: str, salt: str = None) -> str:
    """Hash sensitive data with optional salt."""
    if salt is None:
        salt = getattr(settings, 'SECRET_KEY', '')[:16]
    return hashlib.sha256(f"{salt}{data}".encode()).hexdigest()


def mask_email(email: str) -> str:
    """Mask email address for display."""
    if '@' not in email:
        return email
    local, domain = email.split('@')
    if len(local) <= 2:
        masked_local = '*' * len(local)
    else:
        masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
    return f"{masked_local}@{domain}"


def mask_phone(phone: str) -> str:
    """Mask phone number for display."""
    if len(phone) <= 4:
        return '*' * len(phone)
    return phone[:3] + '*' * (len(phone) - 7) + phone[-4:]


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal attacks."""
    import os
    import re
    # Remove path components
    filename = os.path.basename(filename)
    # Remove potentially dangerous characters
    filename = re.sub(r'[^\w\s\-\.]', '', filename)
    # Limit length
    return filename[:255]


class IPWhitelist:
    """IP whitelist checker."""

    def __init__(self, whitelist: list = None):
        self.whitelist = set(whitelist or [])

    def is_allowed(self, ip: str) -> bool:
        if not self.whitelist:
            return True
        return ip in self.whitelist or self._match_cidr(ip)

    def _match_cidr(self, ip: str) -> bool:
        """Check if IP matches any CIDR in whitelist."""
        import ipaddress
        try:
            ip_obj = ipaddress.ip_address(ip)
            for entry in self.whitelist:
                if '/' in entry:
                    network = ipaddress.ip_network(entry, strict=False)
                    if ip_obj in network:
                        return True
        except ValueError:
            pass
        return False
