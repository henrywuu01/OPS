from django.contrib import admin
from .models import MetaTable, ConfigHistory, SystemConfig, ConfigApproval


@admin.register(MetaTable)
class MetaTableAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'need_audit', 'need_history', 'status', 'sort_order']
    list_filter = ['status', 'need_audit', 'need_history']
    search_fields = ['name', 'display_name', 'description']
    ordering = ['sort_order', 'name']


@admin.register(ConfigHistory)
class ConfigHistoryAdmin(admin.ModelAdmin):
    list_display = ['table_name', 'record_id', 'action', 'version', 'operator', 'created_at']
    list_filter = ['action', 'table_name']
    search_fields = ['table_name', 'record_id']
    ordering = ['-created_at']
    readonly_fields = ['table_name', 'record_id', 'action', 'version', 'old_data', 'new_data', 'changes', 'operator', 'created_at']


@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    list_display = ['key', 'category', 'is_encrypted', 'is_readonly', 'effective_time', 'updated_at']
    list_filter = ['category', 'is_encrypted', 'is_readonly']
    search_fields = ['key', 'description']


@admin.register(ConfigApproval)
class ConfigApprovalAdmin(admin.ModelAdmin):
    list_display = ['table_name', 'record_id', 'action', 'status', 'applicant', 'approver', 'created_at']
    list_filter = ['status', 'action', 'table_name']
    search_fields = ['table_name', 'record_id']
    ordering = ['-created_at']
