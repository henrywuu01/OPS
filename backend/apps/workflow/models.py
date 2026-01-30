"""
Workflow models for approval workflow engine.
Based on system design document.
"""
from django.db import models
from django.conf import settings
from simple_history.models import HistoricalRecords
from apps.common.models import BaseModel


class WorkflowDefinition(BaseModel):
    """Workflow definition model - t_workflow_definition."""

    class Meta:
        db_table = 't_workflow_definition'
        verbose_name = '流程定义'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('published', '已发布'),
        ('archived', '已归档'),
    ]

    name = models.CharField('流程名称', max_length=100)
    code = models.CharField('流程编码', max_length=50, unique=True)
    description = models.TextField('描述', blank=True, null=True)
    nodes = models.JSONField('节点配置', help_text='流程节点JSON配置')
    edges = models.JSONField('边配置', help_text='节点连接关系')
    form_config = models.JSONField('表单配置', default=dict, blank=True, help_text='审批表单字段配置')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='draft')
    version = models.IntegerField('版本号', default=1)

    # Trigger configuration
    trigger_business_types = models.JSONField('关联业务类型', default=list, blank=True)

    # Callback configuration
    callback_config = models.JSONField('回调配置', default=dict, blank=True, help_text='审批通过/拒绝后的回调')

    # History tracking
    history = HistoricalRecords()

    def __str__(self):
        return f'{self.name} v{self.version}'


class ApprovalInstance(BaseModel):
    """Approval instance model - t_approval_instance."""

    class Meta:
        db_table = 't_approval_instance'
        verbose_name = '审批实例'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['business_type', 'business_id']),
            models.Index(fields=['applicant', 'status']),
        ]

    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('pending', '审批中'),
        ('approved', '已通过'),
        ('rejected', '已拒绝'),
        ('cancelled', '已取消'),
        ('withdrawn', '已撤回'),
    ]

    workflow = models.ForeignKey(
        WorkflowDefinition,
        on_delete=models.PROTECT,
        related_name='instances',
        verbose_name='流程定义'
    )
    title = models.CharField('审批标题', max_length=200)
    business_type = models.CharField('业务类型', max_length=50, help_text='关联的业务模块')
    business_id = models.BigIntegerField('业务ID', help_text='关联的业务记录ID')
    form_data = models.JSONField('表单数据', default=dict, blank=True)
    current_node = models.CharField('当前节点', max_length=50, blank=True, null=True)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='draft')
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='approval_applications',
        verbose_name='申请人'
    )
    submitted_at = models.DateTimeField('提交时间', null=True, blank=True)
    completed_at = models.DateTimeField('完成时间', null=True, blank=True)

    # Urgency level
    URGENCY_CHOICES = [
        ('normal', '普通'),
        ('urgent', '紧急'),
        ('very_urgent', '非常紧急'),
    ]
    urgency = models.CharField('紧急程度', max_length=20, choices=URGENCY_CHOICES, default='normal')

    def __str__(self):
        return f'{self.title} ({self.status})'


class ApprovalRecord(models.Model):
    """Approval record model - t_approval_record."""

    class Meta:
        db_table = 't_approval_record'
        verbose_name = '审批记录'
        verbose_name_plural = verbose_name
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['instance']),
        ]

    ACTION_CHOICES = [
        ('submit', '提交'),
        ('approve', '同意'),
        ('reject', '拒绝'),
        ('transfer', '转交'),
        ('add_approver', '加签'),
        ('withdraw', '撤回'),
        ('urge', '催办'),
        ('comment', '评论'),
    ]

    instance = models.ForeignKey(
        ApprovalInstance,
        on_delete=models.CASCADE,
        related_name='records',
        verbose_name='审批实例'
    )
    node_id = models.CharField('节点ID', max_length=50)
    node_name = models.CharField('节点名称', max_length=100, blank=True, null=True)
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='approval_records',
        verbose_name='审批人'
    )
    action = models.CharField('操作', max_length=20, choices=ACTION_CHOICES)
    comment = models.TextField('审批意见', blank=True, null=True)
    attachments = models.JSONField('附件列表', default=list, blank=True)
    transfer_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transferred_approvals',
        verbose_name='转交给'
    )
    created_at = models.DateTimeField('操作时间', auto_now_add=True)

    def __str__(self):
        return f'{self.instance.title} - {self.action}'


class ApprovalTask(models.Model):
    """Approval task (pending approval) model - t_approval_task."""

    class Meta:
        db_table = 't_approval_task'
        verbose_name = '审批任务'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['assignee', 'status']),
        ]

    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('completed', '已完成'),
        ('transferred', '已转交'),
        ('cancelled', '已取消'),
    ]

    ASSIGN_TYPE_CHOICES = [
        ('user', '指定用户'),
        ('role', '指定角色'),
        ('department', '部门主管'),
        ('applicant_select', '申请人自选'),
    ]

    instance = models.ForeignKey(
        ApprovalInstance,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='审批实例'
    )
    node_id = models.CharField('节点ID', max_length=50)
    node_name = models.CharField('节点名称', max_length=100, blank=True, null=True)
    assign_type = models.CharField('分配方式', max_length=20, choices=ASSIGN_TYPE_CHOICES, default='user')
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='approval_tasks',
        verbose_name='审批人'
    )
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    due_time = models.DateTimeField('截止时间', null=True, blank=True)
    reminded_count = models.IntegerField('催办次数', default=0)
    last_reminded_at = models.DateTimeField('最后催办时间', null=True, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    completed_at = models.DateTimeField('完成时间', null=True, blank=True)

    def __str__(self):
        return f'{self.instance.title} - {self.assignee.username}'


class ApprovalCc(models.Model):
    """Approval CC (carbon copy) model - t_approval_cc."""

    class Meta:
        db_table = 't_approval_cc'
        verbose_name = '审批抄送'
        verbose_name_plural = verbose_name
        unique_together = ['instance', 'user']

    instance = models.ForeignKey(
        ApprovalInstance,
        on_delete=models.CASCADE,
        related_name='ccs',
        verbose_name='审批实例'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cc_approvals',
        verbose_name='抄送人'
    )
    node_id = models.CharField('抄送节点', max_length=50, blank=True, null=True)
    is_read = models.BooleanField('是否已读', default=False)
    read_at = models.DateTimeField('阅读时间', null=True, blank=True)
    created_at = models.DateTimeField('抄送时间', auto_now_add=True)

    def __str__(self):
        return f'{self.instance.title} -> {self.user.username}'
