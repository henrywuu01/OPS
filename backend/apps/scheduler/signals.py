"""
Signal handlers for scheduler app.
Auto-sync schedules when jobs/flows are created/updated/deleted.
"""
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender='scheduler.Job')
def sync_job_schedule_on_save(sender, instance, created, **kwargs):
    """Sync job schedule to Celery Beat when job is created or updated."""
    from .services import SchedulerService

    try:
        SchedulerService.sync_job_schedule(instance)
        logger.debug(f'Synced schedule for job {instance.id}')
    except Exception as e:
        logger.error(f'Failed to sync schedule for job {instance.id}: {e}')


@receiver(post_delete, sender='scheduler.Job')
def remove_job_schedule_on_delete(sender, instance, **kwargs):
    """Remove job schedule from Celery Beat when job is deleted."""
    from .services import SchedulerService

    try:
        SchedulerService.remove_job_schedule(instance.id)
        logger.debug(f'Removed schedule for job {instance.id}')
    except Exception as e:
        logger.error(f'Failed to remove schedule for job {instance.id}: {e}')


@receiver(post_save, sender='scheduler.JobFlow')
def sync_flow_schedule_on_save(sender, instance, created, **kwargs):
    """Sync flow schedule to Celery Beat when flow is created or updated."""
    from .services import SchedulerService

    try:
        SchedulerService.sync_flow_schedule(instance)
        logger.debug(f'Synced schedule for flow {instance.id}')
    except Exception as e:
        logger.error(f'Failed to sync schedule for flow {instance.id}: {e}')


@receiver(post_delete, sender='scheduler.JobFlow')
def remove_flow_schedule_on_delete(sender, instance, **kwargs):
    """Remove flow schedule from Celery Beat when flow is deleted."""
    from .services import SchedulerService

    try:
        SchedulerService.remove_flow_schedule(instance.id)
        logger.debug(f'Removed schedule for flow {instance.id}')
    except Exception as e:
        logger.error(f'Failed to remove schedule for flow {instance.id}: {e}')
