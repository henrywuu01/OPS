"""
Scheduler serializers for M2.
"""
from rest_framework import serializers
from .models import Job, JobFlow, JobFlowNode, JobLog


class JobSerializer(serializers.ModelSerializer):
    """Job serializer for list and detail views."""

    class Meta:
        model = Job
        fields = [
            'id', 'name', 'description', 'job_type', 'cron_expr',
            'config', 'retry_count', 'retry_interval', 'timeout',
            'status', 'alert_on_failure', 'alert_on_timeout', 'alert_channels',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class JobCreateUpdateSerializer(serializers.ModelSerializer):
    """Job serializer for create and update operations."""

    class Meta:
        model = Job
        fields = [
            'name', 'description', 'job_type', 'cron_expr',
            'config', 'retry_count', 'retry_interval', 'timeout',
            'status', 'alert_on_failure', 'alert_on_timeout', 'alert_channels'
        ]

    def validate_cron_expr(self, value):
        """Validate cron expression format."""
        if value:
            parts = value.split()
            if len(parts) not in [5, 6]:
                raise serializers.ValidationError('Cron表达式格式错误')
        return value

    def validate_config(self, value):
        """Validate job config based on job_type."""
        job_type = self.initial_data.get('job_type')
        if job_type == 'http':
            if not value.get('url'):
                raise serializers.ValidationError('HTTP任务必须配置url')
        elif job_type == 'shell':
            if not value.get('script'):
                raise serializers.ValidationError('Shell任务必须配置script')
        elif job_type == 'sql':
            if not value.get('sql'):
                raise serializers.ValidationError('SQL任务必须配置sql')
        elif job_type == 'python':
            if not value.get('script'):
                raise serializers.ValidationError('Python任务必须配置script')
        return value


class JobLogSerializer(serializers.ModelSerializer):
    """Job log serializer."""
    job_name = serializers.CharField(source='job.name', read_only=True)
    trigger_user_name = serializers.CharField(
        source='trigger_user.real_name',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = JobLog
        fields = [
            'id', 'job', 'job_name', 'flow', 'flow_instance_id', 'trace_id',
            'trigger_type', 'trigger_user', 'trigger_user_name', 'status',
            'start_time', 'end_time', 'duration', 'input_params',
            'result', 'error_msg', 'retry_count'
        ]


class JobLogDetailSerializer(serializers.ModelSerializer):
    """Job log detail serializer with full result and error info."""
    job_name = serializers.CharField(source='job.name', read_only=True)
    flow_name = serializers.CharField(source='flow.name', read_only=True, allow_null=True)
    trigger_user_name = serializers.CharField(
        source='trigger_user.real_name',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = JobLog
        fields = '__all__'


class JobFlowNodeSerializer(serializers.ModelSerializer):
    """Job flow node serializer."""
    job_name = serializers.CharField(source='job.name', read_only=True)
    job_type = serializers.CharField(source='job.job_type', read_only=True)

    class Meta:
        model = JobFlowNode
        fields = [
            'id', 'node_id', 'job', 'job_name', 'job_type',
            'position_x', 'position_y', 'config'
        ]


class JobFlowSerializer(serializers.ModelSerializer):
    """Job flow serializer for list and detail views."""
    nodes = JobFlowNodeSerializer(many=True, read_only=True)

    class Meta:
        model = JobFlow
        fields = [
            'id', 'name', 'description', 'dag_config', 'cron_expr',
            'status', 'nodes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class JobFlowCreateUpdateSerializer(serializers.ModelSerializer):
    """Job flow serializer for create and update operations."""
    nodes = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        default=[]
    )

    class Meta:
        model = JobFlow
        fields = [
            'name', 'description', 'dag_config', 'cron_expr', 'status', 'nodes'
        ]

    def validate_dag_config(self, value):
        """Validate DAG configuration."""
        if not isinstance(value, dict):
            raise serializers.ValidationError('DAG配置必须是JSON对象')
        if 'nodes' not in value:
            raise serializers.ValidationError('DAG配置必须包含nodes')
        if 'edges' not in value:
            raise serializers.ValidationError('DAG配置必须包含edges')
        return value

    def create(self, validated_data):
        nodes_data = validated_data.pop('nodes', [])
        flow = JobFlow.objects.create(**validated_data)

        for node_data in nodes_data:
            JobFlowNode.objects.create(
                flow=flow,
                job_id=node_data.get('job_id'),
                node_id=node_data.get('node_id'),
                position_x=node_data.get('position_x', 0),
                position_y=node_data.get('position_y', 0),
                config=node_data.get('config', {})
            )

        return flow

    def update(self, instance, validated_data):
        nodes_data = validated_data.pop('nodes', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if nodes_data is not None:
            instance.nodes.all().delete()
            for node_data in nodes_data:
                JobFlowNode.objects.create(
                    flow=instance,
                    job_id=node_data.get('job_id'),
                    node_id=node_data.get('node_id'),
                    position_x=node_data.get('position_x', 0),
                    position_y=node_data.get('position_y', 0),
                    config=node_data.get('config', {})
                )

        return instance
