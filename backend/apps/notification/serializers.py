"""
Notification serializers for M7.
"""
from rest_framework import serializers
from .models import (
    MessageTemplate, MessageLog, Notification, ChannelConfig,
    UserNotificationSetting, Blacklist
)


class MessageTemplateSerializer(serializers.ModelSerializer):
    """Message template serializer."""
    channel_display = serializers.CharField(source='get_channel_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = MessageTemplate
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class MessageLogSerializer(serializers.ModelSerializer):
    """Message log serializer."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = MessageLog
        fields = '__all__'


class NotificationSerializer(serializers.ModelSerializer):
    """Notification serializer."""
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    level_display = serializers.CharField(source='get_level_display', read_only=True)

    class Meta:
        model = Notification
        fields = '__all__'


class ChannelConfigSerializer(serializers.ModelSerializer):
    """Channel config serializer."""
    channel_display = serializers.CharField(source='get_channel_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ChannelConfig
        fields = '__all__'
        read_only_fields = ['last_test_time', 'last_test_result', 'created_at', 'updated_at']


class UserNotificationSettingSerializer(serializers.ModelSerializer):
    """User notification setting serializer."""

    class Meta:
        model = UserNotificationSetting
        fields = [
            'id', 'notification_type', 'email_enabled', 'sms_enabled',
            'im_enabled', 'internal_enabled', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class BlacklistSerializer(serializers.ModelSerializer):
    """Blacklist serializer."""
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    reason_display = serializers.CharField(source='get_reason_display', read_only=True)

    class Meta:
        model = Blacklist
        fields = '__all__'


class SendMessageSerializer(serializers.Serializer):
    """Send message serializer."""
    template_code = serializers.CharField(required=False)
    channel = serializers.CharField()
    recipients = serializers.ListField(child=serializers.CharField())
    subject = serializers.CharField(required=False, allow_blank=True)
    content = serializers.CharField(required=False, allow_blank=True)
    params = serializers.DictField(required=False, default=dict)
    business_type = serializers.CharField(required=False, allow_blank=True)
    business_id = serializers.CharField(required=False, allow_blank=True)
