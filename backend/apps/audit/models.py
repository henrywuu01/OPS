"""
Audit models for operation audit and monitoring.
Based on system design document.
"""
from django.db import models
from django.conf import settings


class AuditLog(models.Model):
    """Operation audit log model - t_audit_log."""

    class Meta:
        db_table = 't_audit_log'
        verbose_name = '操作审计日志'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id', 'created_at']),
            models.Index(fields=['request_path']),
            models.Index(fields=['created_at']),
        ]

    user_id = models.BigIntegerField('用户ID', null=True, blank=True, db_index=True)
    user_name = models.CharField('用户名', max_length=50, blank=True, null=True)
    ip_address = models.GenericIPAddressField('IP地址', blank=True, null=True)
    user_agent = models.CharField('User-Agent', max_length=500, blank=True, null=True)
    request_path = models.CharField('请求路径', max_length=500)
    request_method = models.CharField('请求方法', max_length=10)
    request_body = models.TextField('请求体', blank=True, null=True)
    request_params = models.JSONField('请求参数', default=dict, blank=True)
    response_code = models.IntegerField('响应状态码', null=True, blank=True)
    response_body = models.TextField('响应体', blank=True, null=True)
    duration = models.DecimalField('耗时(秒)', max_digits=10, decimal_places=3, null=True, blank=True)
    module = models.CharField('所属模块', max_length=50, blank=True, null=True)
    action = models.CharField('操作类型', max_length=50, blank=True, null=True)
    resource_type = models.CharField('资源类型', max_length=50, blank=True, null=True)
    resource_id = models.CharField('资源ID', max_length=100, blank=True, null=True)
    trace_id = models.CharField('追踪ID', max_length=36, blank=True, null=True, db_index=True)
    created_at = models.DateTimeField('操作时间', auto_now_add=True)

    def __str__(self):
        return f'{self.user_name} - {self.request_method} {self.request_path}'


class DataChangeLog(models.Model):
    """Data change log model - t_data_change_log."""

    class Meta:
        db_table = 't_data_change_log'
        verbose_name = '数据变更日志'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['table_name', 'record_id']),
            models.Index(fields=['created_at']),
        ]

    ACTION_CHOICES = [
        ('insert', '新增'),
        ('update', '修改'),
        ('delete', '删除'),
    ]

    table_name = models.CharField('表名', max_length=100)
    record_id = models.BigIntegerField('记录ID')
    action = models.CharField('操作类型', max_length=20, choices=ACTION_CHOICES)
    old_data = models.JSONField('变更前数据', null=True, blank=True)
    new_data = models.JSONField('变更后数据', null=True, blank=True)
    changes = models.JSONField('变更字段', null=True, blank=True, help_text='字段级变更详情')
    operator_id = models.BigIntegerField('操作人ID', null=True, blank=True)
    operator_name = models.CharField('操作人', max_length=50, blank=True, null=True)
    trace_id = models.CharField('追踪ID', max_length=36, blank=True, null=True, db_index=True)
    created_at = models.DateTimeField('操作时间', auto_now_add=True)

    def __str__(self):
        return f'{self.table_name}:{self.record_id} - {self.action}'


class LoginLog(models.Model):
    """Login log model - t_login_log."""

    class Meta:
        db_table = 't_login_log'
        verbose_name = '登录日志'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id', 'created_at']),
            models.Index(fields=['created_at']),
        ]

    LOGIN_TYPE_CHOICES = [
        ('password', '密码登录'),
        ('sso', 'SSO单点登录'),
        ('mfa', 'MFA验证'),
        ('oauth', 'OAuth登录'),
    ]

    STATUS_CHOICES = [
        ('success', '成功'),
        ('failed', '失败'),
    ]

    user_id = models.BigIntegerField('用户ID', null=True, blank=True, db_index=True)
    user_name = models.CharField('用户名', max_length=50, blank=True, null=True)
    login_type = models.CharField('登录方式', max_length=20, choices=LOGIN_TYPE_CHOICES)
    ip_address = models.GenericIPAddressField('IP地址', blank=True, null=True)
    location = models.CharField('登录地点', max_length=100, blank=True, null=True)
    device = models.CharField('设备信息', max_length=200, blank=True, null=True)
    browser = models.CharField('浏览器', max_length=100, blank=True, null=True)
    os = models.CharField('操作系统', max_length=100, blank=True, null=True)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES)
    fail_reason = models.CharField('失败原因', max_length=200, blank=True, null=True)
    created_at = models.DateTimeField('登录时间', auto_now_add=True)

    def __str__(self):
        return f'{self.user_name} - {self.status}'


class AlertRule(models.Model):
    """Alert rule model - t_alert_rule."""

    class Meta:
        db_table = 't_alert_rule'
        verbose_name = '告警规则'
        verbose_name_plural = verbose_name

    LEVEL_CHOICES = [
        ('P0', '紧急'),
        ('P1', '重要'),
        ('P2', '一般'),
        ('P3', '提示'),
    ]

    METRIC_TYPE_CHOICES = [
        ('job_failure', '任务失败'),
        ('job_timeout', '任务超时'),
        ('api_error', 'API错误'),
        ('api_latency', 'API延迟'),
        ('login_failure', '登录失败'),
        ('custom', '自定义'),
    ]

    STATUS_CHOICES = [
        ('active', '启用'),
        ('inactive', '停用'),
    ]

    name = models.CharField('规则名称', max_length=100)
    description = models.TextField('描述', blank=True, null=True)
    metric_type = models.CharField('指标类型', max_length=50, choices=METRIC_TYPE_CHOICES)
    condition = models.JSONField('触发条件', help_text='告警条件配置')
    level = models.CharField('告警级别', max_length=10, choices=LEVEL_CHOICES, default='P2')
    notify_channels = models.JSONField('通知渠道', default=list, help_text='邮件/钉钉/飞书等')
    notify_users = models.JSONField('通知用户', default=list, blank=True)
    cooldown_minutes = models.IntegerField('冷却时间(分钟)', default=30, help_text='告警抑制时间')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    def __str__(self):
        return f'{self.name} ({self.level})'


class AlertHistory(models.Model):
    """Alert history model - t_alert_history."""

    class Meta:
        db_table = 't_alert_history'
        verbose_name = '告警历史'
        verbose_name_plural = verbose_name
        ordering = ['-triggered_at']

    STATUS_CHOICES = [
        ('triggered', '已触发'),
        ('acknowledged', '已确认'),
        ('resolved', '已解决'),
    ]

    rule = models.ForeignKey(
        AlertRule,
        on_delete=models.SET_NULL,
        null=True,
        related_name='histories',
        verbose_name='告警规则'
    )
    rule_name = models.CharField('规则名称', max_length=100)
    level = models.CharField('告警级别', max_length=10)
    title = models.CharField('告警标题', max_length=200)
    content = models.TextField('告警内容')
    metric_value = models.JSONField('指标值', null=True, blank=True)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='triggered')
    triggered_at = models.DateTimeField('触发时间', auto_now_add=True)
    acknowledged_at = models.DateTimeField('确认时间', null=True, blank=True)
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_alerts',
        verbose_name='确认人'
    )
    resolved_at = models.DateTimeField('解决时间', null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_alerts',
        verbose_name='解决人'
    )
    resolve_comment = models.TextField('解决说明', blank=True, null=True)

    def __str__(self):
        return f'{self.title} ({self.status})'
