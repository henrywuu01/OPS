"""
Report models for low-code BI and reporting engine.
Based on system design document.
"""
from django.db import models
from django.conf import settings
from simple_history.models import HistoricalRecords
from apps.common.models import BaseModel


class DataSource(BaseModel):
    """Data source configuration model - t_datasource."""

    class Meta:
        db_table = 't_datasource'
        verbose_name = '数据源'
        verbose_name_plural = verbose_name
        ordering = ['name']

    TYPE_CHOICES = [
        ('mysql', 'MySQL'),
        ('postgresql', 'PostgreSQL'),
        ('clickhouse', 'ClickHouse'),
        ('elasticsearch', 'Elasticsearch'),
        ('mongodb', 'MongoDB'),
    ]

    STATUS_CHOICES = [
        ('active', '正常'),
        ('inactive', '停用'),
        ('error', '异常'),
    ]

    name = models.CharField('数据源名称', max_length=100)
    type = models.CharField('数据源类型', max_length=20, choices=TYPE_CHOICES)
    host = models.CharField('主机地址', max_length=255)
    port = models.IntegerField('端口')
    database_name = models.CharField('数据库名', max_length=100, blank=True, null=True)
    username = models.CharField('用户名', max_length=100, blank=True, null=True)
    password = models.CharField('密码', max_length=255, blank=True, null=True, help_text='加密存储')
    extra_config = models.JSONField('额外配置', default=dict, blank=True)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='active')
    last_check_time = models.DateTimeField('最后检查时间', null=True, blank=True)
    last_check_result = models.TextField('最后检查结果', blank=True, null=True)

    # History tracking
    history = HistoricalRecords()

    def __str__(self):
        return f'{self.name} ({self.type})'


class Report(BaseModel):
    """Report definition model - t_report."""

    class Meta:
        db_table = 't_report'
        verbose_name = '报表'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    DISPLAY_TYPE_CHOICES = [
        ('table', '表格'),
        ('line', '折线图'),
        ('bar', '柱状图'),
        ('pie', '饼图'),
        ('funnel', '漏斗图'),
        ('gauge', '仪表盘'),
        ('heatmap', '热力图'),
        ('card', '卡片指标'),
        ('progress', '进度条'),
    ]

    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('published', '已发布'),
        ('archived', '已归档'),
    ]

    name = models.CharField('报表名称', max_length=100)
    description = models.TextField('描述', blank=True, null=True)
    datasource = models.ForeignKey(
        DataSource,
        on_delete=models.PROTECT,
        related_name='reports',
        verbose_name='数据源'
    )
    query_config = models.JSONField('查询配置', help_text='SQL查询配置')
    display_type = models.CharField('展示类型', max_length=20, choices=DISPLAY_TYPE_CHOICES, default='table')
    display_config = models.JSONField('展示配置', default=dict, blank=True, help_text='图表类型、列配置等')
    filter_config = models.JSONField('筛选条件配置', default=list, blank=True)
    format_config = models.JSONField('格式化配置', default=dict, blank=True, help_text='金额千分位、百分比等')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='draft')
    is_public = models.BooleanField('是否公开', default=False)
    view_count = models.IntegerField('查看次数', default=0)

    # Watermark settings
    enable_watermark = models.BooleanField('启用水印', default=False)

    # History tracking
    history = HistoricalRecords()

    def __str__(self):
        return self.name


class ReportSubscription(BaseModel):
    """Report subscription model - t_report_subscription."""

    class Meta:
        db_table = 't_report_subscription'
        verbose_name = '报表订阅'
        verbose_name_plural = verbose_name
        unique_together = ['report', 'user']

    SCHEDULE_TYPE_CHOICES = [
        ('daily', '每日'),
        ('weekly', '每周'),
        ('monthly', '每月'),
    ]

    CHANNEL_CHOICES = [
        ('email', '邮件'),
        ('dingtalk', '钉钉'),
        ('feishu', '飞书'),
        ('wechat', '企业微信'),
    ]

    FORMAT_CHOICES = [
        ('excel', 'Excel'),
        ('csv', 'CSV'),
        ('pdf', 'PDF'),
        ('image', '图片'),
    ]

    STATUS_CHOICES = [
        ('active', '启用'),
        ('paused', '暂停'),
    ]

    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='报表'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='report_subscriptions',
        verbose_name='订阅用户'
    )
    schedule_type = models.CharField('推送周期', max_length=20, choices=SCHEDULE_TYPE_CHOICES)
    schedule_config = models.JSONField('具体时间配置', default=dict, help_text='具体推送时间配置')
    channel = models.CharField('推送渠道', max_length=20, choices=CHANNEL_CHOICES)
    export_format = models.CharField('导出格式', max_length=20, choices=FORMAT_CHOICES, default='excel')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='active')
    last_sent_at = models.DateTimeField('最后推送时间', null=True, blank=True)

    def __str__(self):
        return f'{self.user.username} - {self.report.name}'


class ReportFavorite(models.Model):
    """Report favorite model - t_report_favorite."""

    class Meta:
        db_table = 't_report_favorite'
        verbose_name = '报表收藏'
        verbose_name_plural = verbose_name
        unique_together = ['report', 'user']

    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='报表'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorite_reports',
        verbose_name='用户'
    )
    created_at = models.DateTimeField('收藏时间', auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.report.name}'
