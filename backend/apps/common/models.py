"""
Base models for OPS system.
"""
from django.db import models
from django.conf import settings


class BaseModel(models.Model):
    """
    Abstract base model with common fields.
    """
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created',
        verbose_name='创建人'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated',
        verbose_name='更新人'
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # Auto set created_by and updated_by from request
        from apps.common.middleware import get_current_user
        user = get_current_user()
        if user and user.is_authenticated:
            if not self.pk:
                self.created_by = user
            self.updated_by = user
        super().save(*args, **kwargs)


class SoftDeleteModel(BaseModel):
    """
    Abstract model with soft delete support.
    """
    is_deleted = models.BooleanField('是否删除', default=False, db_index=True)
    deleted_at = models.DateTimeField('删除时间', null=True, blank=True)

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at', 'updated_at', 'updated_by'])

    def hard_delete(self):
        super().delete()


class SoftDeleteManager(models.Manager):
    """
    Manager that excludes soft-deleted objects by default.
    """
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

    def all_with_deleted(self):
        return super().get_queryset()

    def deleted_only(self):
        return super().get_queryset().filter(is_deleted=True)
