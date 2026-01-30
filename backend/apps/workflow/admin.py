from django.contrib import admin
from .models import WorkflowDefinition, ApprovalInstance, ApprovalRecord, ApprovalTask, ApprovalCc


@admin.register(WorkflowDefinition)
class WorkflowDefinitionAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'status', 'version', 'created_at']
    list_filter = ['status']
    search_fields = ['name', 'code', 'description']
    ordering = ['-created_at']


@admin.register(ApprovalInstance)
class ApprovalInstanceAdmin(admin.ModelAdmin):
    list_display = ['title', 'workflow', 'business_type', 'status', 'urgency', 'applicant', 'submitted_at']
    list_filter = ['status', 'urgency', 'business_type', 'workflow']
    search_fields = ['title', 'applicant__username']
    ordering = ['-created_at']


@admin.register(ApprovalRecord)
class ApprovalRecordAdmin(admin.ModelAdmin):
    list_display = ['instance', 'node_name', 'approver', 'action', 'created_at']
    list_filter = ['action']
    search_fields = ['instance__title', 'approver__username']
    ordering = ['-created_at']


@admin.register(ApprovalTask)
class ApprovalTaskAdmin(admin.ModelAdmin):
    list_display = ['instance', 'node_name', 'assignee', 'status', 'due_time', 'created_at']
    list_filter = ['status', 'assign_type']
    search_fields = ['instance__title', 'assignee__username']
    ordering = ['-created_at']


@admin.register(ApprovalCc)
class ApprovalCcAdmin(admin.ModelAdmin):
    list_display = ['instance', 'user', 'is_read', 'created_at']
    list_filter = ['is_read']
    search_fields = ['instance__title', 'user__username']
