"""
Report serializers for M3.
"""
from rest_framework import serializers
from .models import DataSource, Report, ReportSubscription, ReportFavorite


class DataSourceSerializer(serializers.ModelSerializer):
    """DataSource serializer for list and detail views."""
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = DataSource
        fields = [
            'id', 'name', 'type', 'type_display', 'host', 'port',
            'database_name', 'username', 'extra_config', 'status',
            'status_display', 'last_check_time', 'last_check_result',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['last_check_time', 'last_check_result', 'created_at', 'updated_at']


class DataSourceCreateUpdateSerializer(serializers.ModelSerializer):
    """DataSource serializer for create and update operations."""

    class Meta:
        model = DataSource
        fields = [
            'name', 'type', 'host', 'port', 'database_name',
            'username', 'password', 'extra_config', 'status'
        ]

    def validate(self, attrs):
        """Validate datasource configuration."""
        ds_type = attrs.get('type')
        if ds_type in ['mysql', 'postgresql', 'clickhouse']:
            if not attrs.get('database_name'):
                raise serializers.ValidationError('数据库名称不能为空')
        return attrs


class ReportSerializer(serializers.ModelSerializer):
    """Report serializer for list and detail views."""
    datasource_name = serializers.CharField(source='datasource.name', read_only=True)
    display_type_display = serializers.CharField(source='get_display_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = [
            'id', 'name', 'description', 'datasource', 'datasource_name',
            'query_config', 'display_type', 'display_type_display',
            'display_config', 'filter_config', 'format_config',
            'status', 'status_display', 'is_public', 'view_count',
            'enable_watermark', 'is_favorited', 'created_at', 'updated_at'
        ]
        read_only_fields = ['view_count', 'created_at', 'updated_at']

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.favorites.filter(user=request.user).exists()
        return False


class ReportCreateUpdateSerializer(serializers.ModelSerializer):
    """Report serializer for create and update operations."""

    class Meta:
        model = Report
        fields = [
            'name', 'description', 'datasource', 'query_config',
            'display_type', 'display_config', 'filter_config',
            'format_config', 'status', 'is_public', 'enable_watermark'
        ]

    def validate_query_config(self, value):
        """Validate query configuration."""
        if not isinstance(value, dict):
            raise serializers.ValidationError('查询配置必须是JSON对象')
        if 'sql' not in value and 'query' not in value:
            raise serializers.ValidationError('查询配置必须包含sql或query字段')
        return value


class ReportSubscriptionSerializer(serializers.ModelSerializer):
    """Report subscription serializer."""
    user_name = serializers.CharField(source='user.real_name', read_only=True)
    schedule_type_display = serializers.CharField(source='get_schedule_type_display', read_only=True)
    channel_display = serializers.CharField(source='get_channel_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ReportSubscription
        fields = [
            'id', 'report', 'user', 'user_name', 'schedule_type',
            'schedule_type_display', 'schedule_config', 'channel',
            'channel_display', 'export_format', 'status', 'status_display',
            'last_sent_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['last_sent_at', 'created_at', 'updated_at']


class ReportSubscriptionCreateUpdateSerializer(serializers.ModelSerializer):
    """Report subscription serializer for create and update."""

    class Meta:
        model = ReportSubscription
        fields = [
            'schedule_type', 'schedule_config', 'channel',
            'export_format', 'status'
        ]

    def validate_schedule_config(self, value):
        """Validate schedule configuration."""
        if not isinstance(value, dict):
            raise serializers.ValidationError('时间配置必须是JSON对象')
        return value


class ReportFavoriteSerializer(serializers.ModelSerializer):
    """Report favorite serializer."""
    report_name = serializers.CharField(source='report.name', read_only=True)
    report_description = serializers.CharField(source='report.description', read_only=True)

    class Meta:
        model = ReportFavorite
        fields = ['id', 'report', 'report_name', 'report_description', 'created_at']
        read_only_fields = ['created_at']
