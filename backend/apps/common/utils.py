"""
Common utility functions.
"""
import uuid
import hashlib
import secrets
from datetime import datetime, date
from decimal import Decimal
from django.utils import timezone


def generate_uuid():
    """Generate a UUID string."""
    return str(uuid.uuid4())


def generate_trace_id():
    """Generate a trace ID for request tracking."""
    return uuid.uuid4().hex


def generate_random_string(length=32):
    """Generate a random string."""
    return secrets.token_hex(length // 2)


def md5_hash(text):
    """Calculate MD5 hash of a string."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def mask_phone(phone):
    """Mask phone number, e.g., 138****1234"""
    if not phone or len(phone) < 7:
        return phone
    return phone[:3] + '****' + phone[-4:]


def mask_email(email):
    """Mask email address, e.g., ab***@example.com"""
    if not email or '@' not in email:
        return email
    local, domain = email.split('@', 1)
    if len(local) <= 2:
        masked_local = local[0] + '***'
    else:
        masked_local = local[:2] + '***'
    return f'{masked_local}@{domain}'


def mask_id_card(id_card):
    """Mask ID card number, e.g., 110***********1234"""
    if not id_card or len(id_card) < 8:
        return id_card
    return id_card[:3] + '*' * (len(id_card) - 7) + id_card[-4:]


def to_dict(obj, exclude=None):
    """
    Convert model instance to dictionary.
    """
    exclude = exclude or []
    result = {}

    for field in obj._meta.fields:
        if field.name in exclude:
            continue

        value = getattr(obj, field.name)

        # Handle special types
        if isinstance(value, datetime):
            value = value.isoformat()
        elif isinstance(value, date):
            value = value.isoformat()
        elif isinstance(value, Decimal):
            value = float(value)
        elif hasattr(value, 'pk'):
            value = value.pk

        result[field.name] = value

    return result


def get_client_ip(request):
    """Get client IP from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip


def parse_datetime(dt_str, formats=None):
    """Parse datetime string to datetime object."""
    if not dt_str:
        return None

    formats = formats or [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%d',
    ]

    for fmt in formats:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue

    return None
