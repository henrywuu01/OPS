"""
Django settings for OPS project.
"""
import os
import sys
import configparser
from pathlib import Path
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load configuration from sys.ini
CONFIG_PATH = BASE_DIR.parent / 'config' / 'sys.ini'
config = configparser.ConfigParser()
config.read(CONFIG_PATH)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-ops-system-change-this-in-production'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config.getboolean('sys_info', 'sys_debug', fallback=True)

ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'django_celery_beat',
    'django_celery_results',
    'simple_history',
    'drf_spectacular',
    # Local apps
    'apps.common',
    'apps.auth',
    'apps.scheduler',
    'apps.report',
    'apps.config',
    'apps.workflow',
    'apps.audit',
    'apps.notification',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
    'apps.common.middleware.CurrentUserMiddleware',
    'apps.audit.middleware.AuditLogMiddleware',
    # Security & Performance middleware
    'apps.common.security.SecurityHeadersMiddleware',
    'apps.common.security.RateLimitMiddleware',
]

ROOT_URLCONF = 'ops.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ops.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'db_ops',
        'HOST': config.get('db', 'host', fallback='127.0.0.1'),
        'PORT': config.getint('db', 'port', fallback=3306),
        'USER': config.get('db', 'user', fallback='root'),
        'PASSWORD': config.get('db', 'password', fallback=''),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
        'CONN_MAX_AGE': 600,
    }
}

# Redis Cache
REDIS_URL = config.get('redis', 'redis_url', fallback='redis://127.0.0.1:6379/0')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'user_auth.User'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'apps.common.pagination.StandardPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'apps.common.exceptions.custom_exception_handler',
    'DEFAULT_RENDERER_CLASSES': [
        'apps.common.renderers.CustomJSONRenderer',
    ],
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# CORS Settings
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
]

# Celery Settings
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'default'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = False
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# API Documentation
SPECTACULAR_SETTINGS = {
    'TITLE': 'OPS System API',
    'DESCRIPTION': '智能运营系统 API 文档',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# Logging
LOG_LEVEL = config.get('xlog', 'log_level', fallback='INFO')
LOG_PATH = config.get('xlog', 'file_log_path', fallback=str(BASE_DIR / 'logs'))

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_PATH, 'ops.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'] if not DEBUG else ['console'],
        'level': LOG_LEVEL,
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'] if not DEBUG else ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
    },
}

# Ensure log directory exists
os.makedirs(LOG_PATH, exist_ok=True)

# Rate Limiting Configuration
# Format: (max_requests, window_seconds)
RATE_LIMIT = {
    'DEFAULT': (200, 60),      # Authenticated users: 200 requests per minute
    'ANONYMOUS': (60, 60),     # Anonymous users: 60 requests per minute
    'STRICT': (10, 60),        # Sensitive endpoints: 10 requests per minute
}

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Session Security
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# Database connection pool settings (for better performance)
CONN_MAX_AGE = 600  # Keep database connections alive for 10 minutes

# ==================== SSO Configuration ====================

# WeChat Work (企业微信) SSO
WECHAT_WORK_CORP_ID = config.get('sso', 'wechat_work_corp_id', fallback='')
WECHAT_WORK_AGENT_ID = config.get('sso', 'wechat_work_agent_id', fallback='')
WECHAT_WORK_SECRET = config.get('sso', 'wechat_work_secret', fallback='')
WECHAT_WORK_REDIRECT_URI = config.get('sso', 'wechat_work_redirect_uri', fallback='')

# DingTalk (钉钉) SSO
DINGTALK_APP_KEY = config.get('sso', 'dingtalk_app_key', fallback='')
DINGTALK_APP_SECRET = config.get('sso', 'dingtalk_app_secret', fallback='')
DINGTALK_REDIRECT_URI = config.get('sso', 'dingtalk_redirect_uri', fallback='')

# Feishu (飞书) SSO
FEISHU_APP_ID = config.get('sso', 'feishu_app_id', fallback='')
FEISHU_APP_SECRET = config.get('sso', 'feishu_app_secret', fallback='')
FEISHU_REDIRECT_URI = config.get('sso', 'feishu_redirect_uri', fallback='')
