from django.apps import AppConfig


class SchedulerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.scheduler'
    verbose_name = '任务调度'

    def ready(self):
        """Load signal handlers when app is ready."""
        from . import signals  # noqa
