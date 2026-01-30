"""
Scheduler models for job scheduling and DAG workflow management.
Based on system design document.
"""
from django.db import models
from django.conf import settings
from simple_history.models import HistoricalRecords
from apps.common.models import BaseModel


class Job(BaseModel):
    """Job definition model - t_job."""

    class Meta:
        db_table = 't_job'
        verbose_name = '任务'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    JOB_TYPE_CHOICES = [
        ('http', 'HTTP请求'),
        ('shell', 'Shell脚本'),
        ('sql', 'SQL脚本'),
        ('python', 'Python脚本'),
    ]

    STATUS_CHOICES = [
        ('enabled', '启用'),
        ('disabled', '禁用'),
    ]

    name = models.CharField('任务名称', max_length=100)
    description = models.TextField('任务描述', blank=True, null=True)
    job_type = models.CharField('任务类型', max_length=20, choices=JOB_TYPE_CHOICES)
    cron_expr = models.CharField('Cron表达式', max_length=50, blank=True, null=True)
    config = models.JSONField('任务配置', help_text='任务配置(url/script等)')
    retry_count = models.IntegerField('重试次数', default=3)
    retry_interval = models.IntegerField('重试间隔(秒)', default=60)
    timeout = models.IntegerField('超时时间(秒)', default=60)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='enabled')

    # Alert settings
    alert_on_failure = models.BooleanField('失败告警', default=True)
    alert_on_timeout = models.BooleanField('超时告警', default=True)
    alert_channels = models.JSONField('告警渠道', default=list, blank=True)

    # History tracking
    history = HistoricalRecords()

    def __str__(self):
        return self.name


class JobFlow(BaseModel):
    """Job flow (DAG workflow) definition model - t_job_flow."""

    class Meta:
        db_table = 't_job_flow'
        verbose_name = '工作流'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    STATUS_CHOICES = [
        ('enabled', '启用'),
        ('disabled', '禁用'),
    ]

    name = models.CharField('工作流名称', max_length=100)
    description = models.TextField('描述', blank=True, null=True)
    dag_config = models.JSONField('DAG配置', help_text='节点和边的配置')
    cron_expr = models.CharField('Cron表达式', max_length=50, blank=True, null=True)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='enabled')

    # History tracking
    history = HistoricalRecords()

    def __str__(self):
        return self.name


class JobFlowNode(BaseModel):
    """Job flow node model - t_job_flow_node."""

    class Meta:
        db_table = 't_job_flow_node'
        verbose_name = '工作流节点'
        verbose_name_plural = verbose_name

    flow = models.ForeignKey(
        JobFlow,
        on_delete=models.CASCADE,
        related_name='nodes',
        verbose_name='所属工作流'
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='flow_nodes',
        verbose_name='关联任务'
    )
    node_id = models.CharField('节点ID', max_length=50)
    position_x = models.IntegerField('X坐标', default=0)
    position_y = models.IntegerField('Y坐标', default=0)
    config = models.JSONField('节点配置', default=dict, blank=True)

    def __str__(self):
        return f'{self.flow.name} - {self.node_id}'


class JobLog(models.Model):
    """Job execution log model - t_job_log."""

    class Meta:
        db_table = 't_job_log'
        verbose_name = '任务执行日志'
        verbose_name_plural = verbose_name
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['job', 'start_time']),
            models.Index(fields=['trace_id']),
        ]

    STATUS_CHOICES = [
        ('pending', '等待中'),
        ('running', '运行中'),
        ('success', '成功'),
        ('failed', '失败'),
        ('timeout', '超时'),
        ('cancelled', '已取消'),
        ('skipped', '已跳过'),
    ]

    TRIGGER_TYPE_CHOICES = [
        ('cron', '定时触发'),
        ('manual', '手动触发'),
        ('flow', '工作流触发'),
        ('retry', '重试触发'),
    ]

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name='任务'
    )
    flow = models.ForeignKey(
        JobFlow,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs',
        verbose_name='所属工作流'
    )
    flow_instance_id = models.CharField('工作流实例ID', max_length=50, blank=True, null=True)
    trace_id = models.CharField('追踪ID', max_length=36, db_index=True)
    trigger_type = models.CharField('触发类型', max_length=20, choices=TRIGGER_TYPE_CHOICES, default='cron')
    trigger_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='triggered_jobs',
        verbose_name='触发人'
    )
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    start_time = models.DateTimeField('开始时间')
    end_time = models.DateTimeField('结束时间', null=True, blank=True)
    duration = models.IntegerField('耗时(毫秒)', null=True, blank=True)
    input_params = models.JSONField('输入参数', default=dict, blank=True)
    result = models.TextField('执行结果', blank=True, null=True)
    error_msg = models.TextField('错误信息', blank=True, null=True)
    retry_count = models.IntegerField('重试次数', default=0)

    def __str__(self):
        return f'{self.job.name} - {self.trace_id}'
