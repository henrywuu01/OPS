"""
Notification models for message notification center.
Based on system design document.
"""
from django.db import models
from django.conf import settings
from apps.common.models import BaseModel


class MessageTemplate(BaseModel):
    """Message template model - t_message_template."""

    class Meta:
        db_table = 't_message_template'
        verbose_name = '消息模板'
        verbose_name_plural = verbose_name
        unique_together = ['code', 'channel']

    CHANNEL_CHOICES = [
        ('email', '邮件'),
        ('sms', '短信'),
        ('dingtalk', '钉钉'),
        ('feishu', '飞书'),
        ('wechat', '企业微信'),
        ('webhook', 'Webhook'),
        ('internal', '站内信'),
    ]

    STATUS_CHOICES = [
        ('active', '启用'),
        ('disabled', '禁用'),
    ]

    code = models.CharField('模板编码', max_length=50)
    name = models.CharField('模板名称', max_length=100)
    channel = models.CharField('渠道', max_length=20, choices=CHANNEL_CHOICES)
    subject = models.CharField('主题/标题', max_length=200, blank=True, null=True, help_text='邮件主题等')
    content = models.TextField('模板内容', help_text='支持变量如 ${userName}, ${taskName}')
    params = models.JSONField('参数说明', default=list, blank=True, help_text='模板支持的参数列表')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='active')

    def __str__(self):
        return f'{self.name} ({self.channel})'


class MessageLog(models.Model):
    """Message send log model - t_message_log."""

    class Meta:
        db_table = 't_message_log'
        verbose_name = '消息发送记录'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['channel', 'created_at']),
        ]

    STATUS_CHOICES = [
        ('pending', '待发送'),
        ('sent', '已发送'),
        ('failed', '发送失败'),
    ]

    template = models.ForeignKey(
        MessageTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs',
        verbose_name='消息模板'
    )
    channel = models.CharField('渠道', max_length=20)
    recipient = models.CharField('接收人', max_length=200, help_text='邮箱/手机号/用户ID等')
    recipient_name = models.CharField('接收人名称', max_length=100, blank=True, null=True)
    subject = models.CharField('主题', max_length=200, blank=True, null=True)
    content = models.TextField('消息内容')
    params = models.JSONField('模板参数', default=dict, blank=True)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    retry_count = models.IntegerField('重试次数', default=0)
    max_retry = models.IntegerField('最大重试次数', default=3)
    error_msg = models.CharField('错误信息', max_length=500, blank=True, null=True)
    external_id = models.CharField('外部ID', max_length=100, blank=True, null=True, help_text='第三方平台返回的消息ID')
    sent_at = models.DateTimeField('发送时间', null=True, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    # Related business
    business_type = models.CharField('业务类型', max_length=50, blank=True, null=True)
    business_id = models.CharField('业务ID', max_length=100, blank=True, null=True)

    def __str__(self):
        return f'{self.channel} -> {self.recipient} ({self.status})'


class Notification(models.Model):
    """Internal notification model - t_notification."""

    class Meta:
        db_table = 't_notification'
        verbose_name = '站内通知'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
        ]

    TYPE_CHOICES = [
        ('system', '系统公告'),
        ('approval', '审批通知'),
        ('task', '任务通知'),
        ('alert', '告警通知'),
        ('personal', '个人消息'),
    ]

    LEVEL_CHOICES = [
        ('info', '普通'),
        ('warning', '警告'),
        ('error', '错误'),
        ('success', '成功'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='用户'
    )
    title = models.CharField('标题', max_length=200)
    content = models.TextField('内容', blank=True, null=True)
    type = models.CharField('类型', max_length=20, choices=TYPE_CHOICES, default='system')
    level = models.CharField('级别', max_length=20, choices=LEVEL_CHOICES, default='info')
    is_read = models.BooleanField('是否已读', default=False)
    read_at = models.DateTimeField('阅读时间', null=True, blank=True)

    # Link to related resource
    link_url = models.CharField('链接地址', max_length=500, blank=True, null=True)
    business_type = models.CharField('业务类型', max_length=50, blank=True, null=True)
    business_id = models.CharField('业务ID', max_length=100, blank=True, null=True)

    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.title}'


class ChannelConfig(BaseModel):
    """Channel configuration model - t_channel_config."""

    class Meta:
        db_table = 't_channel_config'
        verbose_name = '渠道配置'
        verbose_name_plural = verbose_name

    CHANNEL_CHOICES = [
        ('email', '邮件'),
        ('sms', '短信'),
        ('dingtalk', '钉钉'),
        ('feishu', '飞书'),
        ('wechat', '企业微信'),
    ]

    STATUS_CHOICES = [
        ('active', '启用'),
        ('disabled', '禁用'),
    ]

    channel = models.CharField('渠道', max_length=20, choices=CHANNEL_CHOICES, unique=True)
    name = models.CharField('渠道名称', max_length=50)
    config = models.JSONField('配置信息', help_text='API密钥、服务器配置等')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='active')
    last_test_time = models.DateTimeField('最后测试时间', null=True, blank=True)
    last_test_result = models.CharField('最后测试结果', max_length=200, blank=True, null=True)

    def __str__(self):
        return f'{self.name} ({self.channel})'


class UserNotificationSetting(models.Model):
    """User notification setting model - t_user_notification_setting."""

    class Meta:
        db_table = 't_user_notification_setting'
        verbose_name = '用户通知设置'
        verbose_name_plural = verbose_name
        unique_together = ['user', 'notification_type']

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_settings',
        verbose_name='用户'
    )
    notification_type = models.CharField('通知类型', max_length=50, help_text='如 approval, task, alert')
    email_enabled = models.BooleanField('邮件通知', default=True)
    sms_enabled = models.BooleanField('短信通知', default=False)
    im_enabled = models.BooleanField('IM通知', default=True)
    internal_enabled = models.BooleanField('站内信通知', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    def __str__(self):
        return f'{self.user.username} - {self.notification_type}'


class Blacklist(models.Model):
    """Notification blacklist model - t_notification_blacklist."""

    class Meta:
        db_table = 't_notification_blacklist'
        verbose_name = '通知黑名单'
        verbose_name_plural = verbose_name

    TYPE_CHOICES = [
        ('email', '邮箱'),
        ('phone', '手机号'),
        ('user', '用户'),
    ]

    REASON_CHOICES = [
        ('unsubscribe', '用户退订'),
        ('bounce', '邮件退信'),
        ('complaint', '用户投诉'),
        ('manual', '手动添加'),
    ]

    type = models.CharField('类型', max_length=20, choices=TYPE_CHOICES)
    value = models.CharField('值', max_length=200, help_text='邮箱/手机号/用户ID')
    reason = models.CharField('原因', max_length=20, choices=REASON_CHOICES)
    remark = models.TextField('备注', blank=True, null=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    def __str__(self):
        return f'{self.type}: {self.value}'
