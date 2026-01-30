from django.contrib import admin
from .models import AuditLog, DataChangeLog, LoginLog, AlertRule, AlertHistory


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user_name', 'request_method', 'request_path', 'response_code', 'duration', 'created_at']
    list_filter = ['request_method', 'response_code', 'module']
    search_fields = ['user_name', 'request_path', 'ip_address']
    ordering = ['-created_at']
    readonly_fields = ['user_id', 'user_name', 'ip_address', 'user_agent', 'request_path', 'request_method',
                       'request_body', 'request_params', 'response_code', 'response_body', 'duration',
                       'module', 'action', 'resource_type', 'resource_id', 'trace_id', 'created_at']


@admin.register(DataChangeLog)
class DataChangeLogAdmin(admin.ModelAdmin):
    list_display = ['table_name', 'record_id', 'action', 'operator_name', 'created_at']
    list_filter = ['action', 'table_name']
    search_fields = ['table_name', 'record_id', 'operator_name']
    ordering = ['-created_at']
    readonly_fields = ['table_name', 'record_id', 'action', 'old_data', 'new_data', 'changes',
                       'operator_id', 'operator_name', 'trace_id', 'created_at']


@admin.register(LoginLog)
class LoginLogAdmin(admin.ModelAdmin):
    list_display = ['user_name', 'login_type', 'ip_address', 'location', 'status', 'created_at']
    list_filter = ['login_type', 'status']
    search_fields = ['user_name', 'ip_address', 'location']
    ordering = ['-created_at']
    readonly_fields = ['user_id', 'user_name', 'login_type', 'ip_address', 'location', 'device',
                       'browser', 'os', 'status', 'fail_reason', 'created_at']


@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'metric_type', 'level', 'status', 'cooldown_minutes', 'created_at']
    list_filter = ['level', 'status', 'metric_type']
    search_fields = ['name', 'description']


@admin.register(AlertHistory)
class AlertHistoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'rule_name', 'level', 'status', 'triggered_at', 'resolved_at']
    list_filter = ['level', 'status']
    search_fields = ['title', 'rule_name', 'content']
    ordering = ['-triggered_at']
