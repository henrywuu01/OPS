from django.contrib import admin
from .models import DataSource, Report, ReportSubscription, ReportFavorite


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'host', 'port', 'database_name', 'status', 'created_at']
    list_filter = ['type', 'status']
    search_fields = ['name', 'host', 'database_name']
    ordering = ['name']
    exclude = ['password']  # Don't show password in admin


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['name', 'datasource', 'display_type', 'status', 'is_public', 'view_count', 'created_at']
    list_filter = ['display_type', 'status', 'is_public', 'datasource']
    search_fields = ['name', 'description']
    ordering = ['-created_at']


@admin.register(ReportSubscription)
class ReportSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['report', 'user', 'schedule_type', 'channel', 'status', 'last_sent_at']
    list_filter = ['schedule_type', 'channel', 'status']
    search_fields = ['report__name', 'user__username']


@admin.register(ReportFavorite)
class ReportFavoriteAdmin(admin.ModelAdmin):
    list_display = ['report', 'user', 'created_at']
    search_fields = ['report__name', 'user__username']
