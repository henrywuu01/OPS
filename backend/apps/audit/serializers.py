"""
Audit serializers for M6.
"""
from rest_framework import serializers
from .models import AuditLog, DataChangeLog, LoginLog, AlertRule, AlertHistory


class AuditLogSerializer(serializers.ModelSerializer):
    """Audit log serializer."""

    class Meta:
        model = AuditLog
        fields = '__all__'


class DataChangeLogSerializer(serializers.ModelSerializer):
    """Data change log serializer."""
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = DataChangeLog
        fields = '__all__'


class LoginLogSerializer(serializers.ModelSerializer):
    """Login log serializer."""
    login_type_display = serializers.CharField(source='get_login_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = LoginLog
        fields = '__all__'


class AlertRuleSerializer(serializers.ModelSerializer):
    """Alert rule serializer."""
    level_display = serializers.CharField(source='get_level_display', read_only=True)
    metric_type_display = serializers.CharField(source='get_metric_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = AlertRule
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class AlertRuleCreateUpdateSerializer(serializers.ModelSerializer):
    """Alert rule create/update serializer."""

    class Meta:
        model = AlertRule
        fields = [
            'name', 'description', 'metric_type', 'condition', 'level',
            'notify_channels', 'notify_users', 'cooldown_minutes', 'status'
        ]


class AlertHistorySerializer(serializers.ModelSerializer):
    """Alert history serializer."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    acknowledged_by_name = serializers.CharField(
        source='acknowledged_by.real_name', read_only=True, allow_null=True
    )
    resolved_by_name = serializers.CharField(
        source='resolved_by.real_name', read_only=True, allow_null=True
    )

    class Meta:
        model = AlertHistory
        fields = '__all__'
