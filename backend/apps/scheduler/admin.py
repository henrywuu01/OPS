from django.contrib import admin
from .models import Job, JobFlow, JobFlowNode, JobLog


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['name', 'job_type', 'cron_expr', 'status', 'retry_count', 'timeout', 'created_at']
    list_filter = ['job_type', 'status', 'alert_on_failure']
    search_fields = ['name', 'description']
    ordering = ['-created_at']


@admin.register(JobFlow)
class JobFlowAdmin(admin.ModelAdmin):
    list_display = ['name', 'cron_expr', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['name', 'description']
    ordering = ['-created_at']


@admin.register(JobFlowNode)
class JobFlowNodeAdmin(admin.ModelAdmin):
    list_display = ['flow', 'node_id', 'job', 'position_x', 'position_y']
    list_filter = ['flow']
    search_fields = ['node_id']


@admin.register(JobLog)
class JobLogAdmin(admin.ModelAdmin):
    list_display = ['job', 'trace_id', 'trigger_type', 'status', 'start_time', 'duration']
    list_filter = ['status', 'trigger_type', 'job']
    search_fields = ['trace_id', 'job__name']
    ordering = ['-start_time']
    readonly_fields = ['job', 'flow', 'trace_id', 'status', 'start_time', 'end_time', 'duration', 'result', 'error_msg']
