"""
Configuration serializers for M4.
"""
from rest_framework import serializers
from .models import MetaTable, ConfigHistory, SystemConfig, ConfigApproval


class MetaTableSerializer(serializers.ModelSerializer):
    """MetaTable serializer for list and detail views."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = MetaTable
        fields = [
            'id', 'name', 'display_name', 'description', 'field_config',
            'need_audit', 'need_history', 'status', 'status_display',
            'sort_order', 'read_roles', 'write_roles',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class MetaTableCreateUpdateSerializer(serializers.ModelSerializer):
    """MetaTable serializer for create and update operations."""

    class Meta:
        model = MetaTable
        fields = [
            'name', 'display_name', 'description', 'field_config',
            'need_audit', 'need_history', 'status', 'sort_order',
            'read_roles', 'write_roles'
        ]

    def validate_name(self, value):
        """Validate table name format."""
        if not value.isidentifier():
            raise serializers.ValidationError('表名格式不正确，只能包含字母、数字和下划线')
        return value

    def validate_field_config(self, value):
        """Validate field configuration."""
        if not isinstance(value, list):
            raise serializers.ValidationError('字段配置必须是数组')
        for field in value:
            if 'name' not in field:
                raise serializers.ValidationError('每个字段必须包含name')
            if 'type' not in field:
                raise serializers.ValidationError('每个字段必须包含type')
        return value


class ConfigHistorySerializer(serializers.ModelSerializer):
    """Config history serializer."""
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    operator_name = serializers.CharField(source='operator.real_name', read_only=True)

    class Meta:
        model = ConfigHistory
        fields = [
            'id', 'table_name', 'record_id', 'action', 'action_display',
            'version', 'old_data', 'new_data', 'changes', 'remark',
            'operator', 'operator_name', 'created_at'
        ]


class SystemConfigSerializer(serializers.ModelSerializer):
    """System config serializer."""
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = SystemConfig
        fields = [
            'id', 'key', 'value', 'category', 'category_display',
            'description', 'is_encrypted', 'is_readonly', 'effective_time',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['is_encrypted', 'created_at', 'updated_at']


class SystemConfigUpdateSerializer(serializers.ModelSerializer):
    """System config update serializer."""

    class Meta:
        model = SystemConfig
        fields = ['value', 'description', 'effective_time']


class ConfigApprovalSerializer(serializers.ModelSerializer):
    """Config approval serializer."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    applicant_name = serializers.CharField(source='applicant.real_name', read_only=True)
    approver_name = serializers.CharField(source='approver.real_name', read_only=True, allow_null=True)

    class Meta:
        model = ConfigApproval
        fields = [
            'id', 'table_name', 'record_id', 'action', 'action_display',
            'old_data', 'new_data', 'remark', 'status', 'status_display',
            'applicant', 'applicant_name', 'approver', 'approver_name',
            'approved_at', 'approve_remark', 'created_at', 'updated_at'
        ]
        read_only_fields = ['approved_at', 'created_at', 'updated_at']


class DynamicConfigDataSerializer(serializers.Serializer):
    """Dynamic serializer for config table data."""

    def __init__(self, *args, meta_table=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.meta_table = meta_table
        if meta_table:
            self._build_fields()

    def _build_fields(self):
        """Build fields dynamically based on meta table config."""
        field_config = self.meta_table.field_config or []

        for field_def in field_config:
            field_name = field_def.get('name')
            field_type = field_def.get('type')
            required = field_def.get('required', False)
            label = field_def.get('label', field_name)

            if field_type == 'string':
                self.fields[field_name] = serializers.CharField(
                    required=required,
                    label=label,
                    max_length=field_def.get('max_length', 255),
                    allow_blank=not required
                )
            elif field_type == 'text':
                self.fields[field_name] = serializers.CharField(
                    required=required,
                    label=label,
                    allow_blank=not required
                )
            elif field_type == 'integer':
                self.fields[field_name] = serializers.IntegerField(
                    required=required,
                    label=label
                )
            elif field_type == 'decimal':
                self.fields[field_name] = serializers.DecimalField(
                    required=required,
                    label=label,
                    max_digits=field_def.get('max_digits', 10),
                    decimal_places=field_def.get('decimal_places', 2)
                )
            elif field_type == 'boolean':
                self.fields[field_name] = serializers.BooleanField(
                    required=required,
                    label=label
                )
            elif field_type == 'date':
                self.fields[field_name] = serializers.DateField(
                    required=required,
                    label=label
                )
            elif field_type == 'datetime':
                self.fields[field_name] = serializers.DateTimeField(
                    required=required,
                    label=label
                )
            elif field_type == 'json':
                self.fields[field_name] = serializers.JSONField(
                    required=required,
                    label=label
                )
            elif field_type == 'select':
                choices = field_def.get('choices', [])
                self.fields[field_name] = serializers.ChoiceField(
                    choices=[(c['value'], c['label']) for c in choices],
                    required=required,
                    label=label
                )
            elif field_type == 'foreign_key':
                self.fields[field_name] = serializers.IntegerField(
                    required=required,
                    label=label
                )
            else:
                self.fields[field_name] = serializers.CharField(
                    required=required,
                    label=label,
                    allow_blank=not required
                )
