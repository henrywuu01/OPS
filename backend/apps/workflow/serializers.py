"""
Workflow serializers for M5.
"""
from rest_framework import serializers
from .models import (
    WorkflowDefinition, ApprovalInstance, ApprovalRecord,
    ApprovalTask, ApprovalCc
)


class WorkflowDefinitionSerializer(serializers.ModelSerializer):
    """Workflow definition serializer."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = WorkflowDefinition
        fields = [
            'id', 'name', 'code', 'description', 'nodes', 'edges',
            'form_config', 'status', 'status_display', 'version',
            'trigger_business_types', 'callback_config',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['version', 'created_at', 'updated_at']


class WorkflowDefinitionCreateUpdateSerializer(serializers.ModelSerializer):
    """Workflow definition create/update serializer."""

    class Meta:
        model = WorkflowDefinition
        fields = [
            'name', 'code', 'description', 'nodes', 'edges',
            'form_config', 'trigger_business_types', 'callback_config'
        ]

    def validate_nodes(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError('节点配置必须是数组')
        if len(value) < 2:
            raise serializers.ValidationError('至少需要开始节点和结束节点')
        return value

    def validate_edges(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError('边配置必须是数组')
        return value


class ApprovalRecordSerializer(serializers.ModelSerializer):
    """Approval record serializer."""
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    approver_name = serializers.CharField(source='approver.real_name', read_only=True)
    transfer_to_name = serializers.CharField(source='transfer_to.real_name', read_only=True, allow_null=True)

    class Meta:
        model = ApprovalRecord
        fields = [
            'id', 'node_id', 'node_name', 'approver', 'approver_name',
            'action', 'action_display', 'comment', 'attachments',
            'transfer_to', 'transfer_to_name', 'created_at'
        ]


class ApprovalTaskSerializer(serializers.ModelSerializer):
    """Approval task serializer."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    assignee_name = serializers.CharField(source='assignee.real_name', read_only=True)
    instance_title = serializers.CharField(source='instance.title', read_only=True)

    class Meta:
        model = ApprovalTask
        fields = [
            'id', 'instance', 'instance_title', 'node_id', 'node_name',
            'assign_type', 'assignee', 'assignee_name', 'status',
            'status_display', 'due_time', 'reminded_count',
            'created_at', 'completed_at'
        ]


class ApprovalInstanceSerializer(serializers.ModelSerializer):
    """Approval instance serializer."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    urgency_display = serializers.CharField(source='get_urgency_display', read_only=True)
    workflow_name = serializers.CharField(source='workflow.name', read_only=True)
    applicant_name = serializers.CharField(source='applicant.real_name', read_only=True)
    records = ApprovalRecordSerializer(many=True, read_only=True)
    current_tasks = serializers.SerializerMethodField()

    class Meta:
        model = ApprovalInstance
        fields = [
            'id', 'workflow', 'workflow_name', 'title', 'business_type',
            'business_id', 'form_data', 'current_node', 'status',
            'status_display', 'applicant', 'applicant_name', 'urgency',
            'urgency_display', 'submitted_at', 'completed_at',
            'records', 'current_tasks', 'created_at', 'updated_at'
        ]
        read_only_fields = ['current_node', 'submitted_at', 'completed_at', 'created_at', 'updated_at']

    def get_current_tasks(self, obj):
        tasks = obj.tasks.filter(status='pending')
        return ApprovalTaskSerializer(tasks, many=True).data


class ApprovalInstanceCreateSerializer(serializers.ModelSerializer):
    """Approval instance create serializer."""

    class Meta:
        model = ApprovalInstance
        fields = [
            'workflow', 'title', 'business_type', 'business_id',
            'form_data', 'urgency'
        ]

    def create(self, validated_data):
        validated_data['applicant'] = self.context['request'].user
        return super().create(validated_data)


class ApprovalActionSerializer(serializers.Serializer):
    """Approval action serializer."""
    comment = serializers.CharField(required=False, allow_blank=True)
    attachments = serializers.ListField(
        child=serializers.URLField(),
        required=False,
        default=[]
    )


class ApprovalTransferSerializer(serializers.Serializer):
    """Approval transfer serializer."""
    transfer_to = serializers.IntegerField(required=True)
    comment = serializers.CharField(required=False, allow_blank=True)


class ApprovalCcSerializer(serializers.ModelSerializer):
    """Approval CC serializer."""
    user_name = serializers.CharField(source='user.real_name', read_only=True)
    instance_title = serializers.CharField(source='instance.title', read_only=True)

    class Meta:
        model = ApprovalCc
        fields = [
            'id', 'instance', 'instance_title', 'user', 'user_name',
            'node_id', 'is_read', 'read_at', 'created_at'
        ]
