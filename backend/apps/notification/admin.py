from django.contrib import admin
from .models import MessageTemplate, MessageLog, Notification, ChannelConfig, UserNotificationSetting, Blacklist


@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'channel', 'status', 'created_at']
    list_filter = ['channel', 'status']
    search_fields = ['name', 'code', 'content']
    ordering = ['channel', 'code']


@admin.register(MessageLog)
class MessageLogAdmin(admin.ModelAdmin):
    list_display = ['channel', 'recipient', 'subject', 'status', 'retry_count', 'sent_at', 'created_at']
    list_filter = ['channel', 'status']
    search_fields = ['recipient', 'subject', 'content']
    ordering = ['-created_at']
    readonly_fields = ['template', 'channel', 'recipient', 'content', 'status', 'retry_count',
                       'error_msg', 'external_id', 'sent_at', 'created_at']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'type', 'level', 'is_read', 'created_at']
    list_filter = ['type', 'level', 'is_read']
    search_fields = ['user__username', 'title', 'content']
    ordering = ['-created_at']


@admin.register(ChannelConfig)
class ChannelConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'channel', 'status', 'last_test_time', 'last_test_result']
    list_filter = ['channel', 'status']


@admin.register(UserNotificationSetting)
class UserNotificationSettingAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'email_enabled', 'sms_enabled', 'im_enabled', 'internal_enabled']
    list_filter = ['notification_type']
    search_fields = ['user__username']


@admin.register(Blacklist)
class BlacklistAdmin(admin.ModelAdmin):
    list_display = ['type', 'value', 'reason', 'created_at']
    list_filter = ['type', 'reason']
    search_fields = ['value', 'remark']
