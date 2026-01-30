"""
Configuration models for metadata-driven configuration management.
Based on system design document.
"""
from django.db import models
from django.conf import settings
from simple_history.models import HistoricalRecords
from apps.common.models import BaseModel


class MetaTable(BaseModel):
    """Meta table definition model - t_meta_table."""

    class Meta:
        db_table = 't_meta_table'
        verbose_name = '元数据表'
        verbose_name_plural = verbose_name
        ordering = ['sort_order', 'name']

    FIELD_TYPE_CHOICES = [
        ('string', '文本'),
        ('text', '长文本'),
        ('integer', '整数'),
        ('decimal', '小数'),
        ('boolean', '布尔'),
        ('date', '日期'),
        ('datetime', '日期时间'),
        ('json', 'JSON'),
        ('image', '图片'),
        ('file', '文件'),
        ('richtext', '富文本'),
        ('select', '下拉选择'),
        ('foreign_key', '外键'),
    ]

    STATUS_CHOICES = [
        ('active', '启用'),
        ('inactive', '停用'),
    ]

    name = models.CharField('表名', max_length=100, unique=True)
    display_name = models.CharField('显示名称', max_length=100)
    description = models.TextField('描述', blank=True, null=True)
    field_config = models.JSONField('字段配置', help_text='字段定义JSON配置')
    need_audit = models.BooleanField('需要审批', default=False, help_text='修改是否需要审批')
    need_history = models.BooleanField('记录历史', default=True, help_text='是否记录变更历史')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='active')
    sort_order = models.IntegerField('排序', default=0)

    # Access control
    read_roles = models.JSONField('可读角色', default=list, blank=True)
    write_roles = models.JSONField('可写角色', default=list, blank=True)

    # History tracking
    history = HistoricalRecords()

    def __str__(self):
        return f'{self.display_name} ({self.name})'


class ConfigHistory(models.Model):
    """Configuration history model - t_config_history."""

    class Meta:
        db_table = 't_config_history'
        verbose_name = '配置历史'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['table_name', 'record_id']),
        ]

    ACTION_CHOICES = [
        ('insert', '新增'),
        ('update', '修改'),
        ('delete', '删除'),
        ('rollback', '回滚'),
    ]

    table_name = models.CharField('表名', max_length=100)
    record_id = models.BigIntegerField('记录ID')
    action = models.CharField('操作类型', max_length=20, choices=ACTION_CHOICES)
    version = models.IntegerField('版本号')
    old_data = models.JSONField('变更前数据', null=True, blank=True)
    new_data = models.JSONField('变更后数据', null=True, blank=True)
    changes = models.JSONField('变更字段', null=True, blank=True, help_text='字段级变更详情')
    remark = models.TextField('备注', blank=True, null=True, help_text='修改原因')
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='config_histories',
        verbose_name='操作人'
    )
    created_at = models.DateTimeField('操作时间', auto_now_add=True)

    def __str__(self):
        return f'{self.table_name}:{self.record_id} v{self.version}'


class SystemConfig(BaseModel):
    """System configuration key-value model - t_system_config."""

    class Meta:
        db_table = 't_system_config'
        verbose_name = '系统配置'
        verbose_name_plural = verbose_name

    CATEGORY_CHOICES = [
        ('system', '系统配置'),
        ('security', '安全配置'),
        ('email', '邮件配置'),
        ('sms', '短信配置'),
        ('storage', '存储配置'),
        ('other', '其他'),
    ]

    key = models.CharField('配置键', max_length=100, unique=True)
    value = models.JSONField('配置值')
    category = models.CharField('分类', max_length=50, choices=CATEGORY_CHOICES, default='system')
    description = models.TextField('描述', blank=True, null=True)
    is_encrypted = models.BooleanField('是否加密', default=False)
    is_readonly = models.BooleanField('是否只读', default=False)

    # Scheduled effective time
    effective_time = models.DateTimeField('生效时间', null=True, blank=True)

    # History tracking
    history = HistoricalRecords()

    def __str__(self):
        return self.key


class ConfigApproval(BaseModel):
    """Configuration change approval model - t_config_approval."""

    class Meta:
        db_table = 't_config_approval'
        verbose_name = '配置审批'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    STATUS_CHOICES = [
        ('pending', '待审批'),
        ('approved', '已通过'),
        ('rejected', '已拒绝'),
        ('cancelled', '已取消'),
    ]

    ACTION_CHOICES = [
        ('insert', '新增'),
        ('update', '修改'),
        ('delete', '删除'),
    ]

    table_name = models.CharField('表名', max_length=100)
    record_id = models.BigIntegerField('记录ID', null=True, blank=True, help_text='新增时为空')
    action = models.CharField('操作类型', max_length=20, choices=ACTION_CHOICES)
    old_data = models.JSONField('变更前数据', null=True, blank=True)
    new_data = models.JSONField('变更后数据')
    remark = models.TextField('申请备注', blank=True, null=True)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='config_applications',
        verbose_name='申请人'
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='config_approvals',
        verbose_name='审批人'
    )
    approved_at = models.DateTimeField('审批时间', null=True, blank=True)
    approve_remark = models.TextField('审批备注', blank=True, null=True)

    def __str__(self):
        return f'{self.table_name}:{self.action} - {self.status}'
