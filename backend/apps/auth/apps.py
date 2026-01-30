from django.apps import AppConfig


class AuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.auth'
    label = 'user_auth'  # Avoid conflict with django.contrib.auth
    verbose_name = '用户认证'
