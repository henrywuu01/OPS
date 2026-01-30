"""
Scheduler views for M2 - Job Scheduling Center.
"""
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count
from django.utils import timezone

from .models import Job, JobFlow, JobFlowNode, JobLog
from .serializers import (
    JobSerializer, JobCreateUpdateSerializer,
    JobLogSerializer, JobLogDetailSerializer,
    JobFlowSerializer, JobFlowCreateUpdateSerializer
)
from .tasks import execute_job, execute_job_flow


class JobListCreateView(generics.ListCreateAPIView):
    """Job list and create view."""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Job.objects.all()

        # Search filter
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )

        # Type filter
        job_type = self.request.query_params.get('job_type')
        if job_type:
            queryset = queryset.filter(job_type=job_type)

        # Status filter
        job_status = self.request.query_params.get('status')
        if job_status:
            queryset = queryset.filter(status=job_status)

        return queryset.order_by('-created_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return JobCreateUpdateSerializer
        return JobSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        start = (page - 1) * page_size
        end = start + page_size

        total = queryset.count()
        jobs = queryset[start:end]
        serializer = JobSerializer(jobs, many=True)

        return Response({
            'total': total,
            'page': page,
            'page_size': page_size,
            'results': serializer.data
        })


class JobDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Job detail, update and delete view."""
    permission_classes = [IsAuthenticated]
    queryset = Job.objects.all()

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return JobCreateUpdateSerializer
        return JobSerializer


class JobTriggerView(APIView):
    """Manually trigger a job execution."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            job = Job.objects.get(pk=pk)
        except Job.DoesNotExist:
            return Response(
                {'error': '任务不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        if job.status != 'enabled':
            return Response(
                {'error': '任务已禁用，无法执行'},
                status=status.HTTP_400_BAD_REQUEST
            )

        input_params = request.data.get('params', {})

        # Trigger job execution asynchronously
        task = execute_job.delay(
            job_id=job.id,
            trigger_type='manual',
            trigger_user_id=request.user.id,
            input_params=input_params
        )

        return Response({
            'message': '任务已触发',
            'task_id': task.id
        })


class JobPauseView(APIView):
    """Pause a job (disable)."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            job = Job.objects.get(pk=pk)
        except Job.DoesNotExist:
            return Response(
                {'error': '任务不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        job.status = 'disabled'
        job.save(update_fields=['status'])

        return Response({
            'message': '任务已暂停',
            'status': job.status
        })


class JobResumeView(APIView):
    """Resume a job (enable)."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            job = Job.objects.get(pk=pk)
        except Job.DoesNotExist:
            return Response(
                {'error': '任务不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        job.status = 'enabled'
        job.save(update_fields=['status'])

        return Response({
            'message': '任务已恢复',
            'status': job.status
        })


class JobLogListView(APIView):
    """List job execution logs."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            job = Job.objects.get(pk=pk)
        except Job.DoesNotExist:
            return Response(
                {'error': '任务不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        queryset = JobLog.objects.filter(job=job)

        # Status filter
        log_status = request.query_params.get('status')
        if log_status:
            queryset = queryset.filter(status=log_status)

        # Date range filter
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(start_time__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(start_time__date__lte=end_date)

        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        start = (page - 1) * page_size
        end = start + page_size

        total = queryset.count()
        logs = queryset.order_by('-start_time')[start:end]
        serializer = JobLogSerializer(logs, many=True)

        return Response({
            'total': total,
            'page': page,
            'page_size': page_size,
            'results': serializer.data
        })


class JobLogDetailView(APIView):
    """Get job log detail."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, log_id):
        try:
            log = JobLog.objects.select_related('job', 'flow', 'trigger_user').get(
                pk=log_id, job_id=pk
            )
        except JobLog.DoesNotExist:
            return Response(
                {'error': '日志不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = JobLogDetailSerializer(log)
        return Response(serializer.data)


class JobFlowListCreateView(generics.ListCreateAPIView):
    """Job flow list and create view."""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = JobFlow.objects.all()

        # Search filter
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )

        # Status filter
        flow_status = self.request.query_params.get('status')
        if flow_status:
            queryset = queryset.filter(status=flow_status)

        return queryset.order_by('-created_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return JobFlowCreateUpdateSerializer
        return JobFlowSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        start = (page - 1) * page_size
        end = start + page_size

        total = queryset.count()
        flows = queryset[start:end]
        serializer = JobFlowSerializer(flows, many=True)

        return Response({
            'total': total,
            'page': page,
            'page_size': page_size,
            'results': serializer.data
        })


class JobFlowDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Job flow detail, update and delete view."""
    permission_classes = [IsAuthenticated]
    queryset = JobFlow.objects.all()

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return JobFlowCreateUpdateSerializer
        return JobFlowSerializer


class JobFlowTriggerView(APIView):
    """Manually trigger a job flow execution."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            flow = JobFlow.objects.get(pk=pk)
        except JobFlow.DoesNotExist:
            return Response(
                {'error': '工作流不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        if flow.status != 'enabled':
            return Response(
                {'error': '工作流已禁用，无法执行'},
                status=status.HTTP_400_BAD_REQUEST
            )

        input_params = request.data.get('params', {})

        # Trigger flow execution asynchronously
        task = execute_job_flow.delay(
            flow_id=flow.id,
            trigger_user_id=request.user.id,
            input_params=input_params
        )

        return Response({
            'message': '工作流已触发',
            'task_id': task.id
        })


class JobStatisticsView(APIView):
    """Get job execution statistics."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get date range
        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timezone.timedelta(days=days)

        # Total jobs
        total_jobs = Job.objects.count()
        enabled_jobs = Job.objects.filter(status='enabled').count()

        # Execution statistics
        recent_logs = JobLog.objects.filter(start_time__gte=start_date)
        total_executions = recent_logs.count()
        success_count = recent_logs.filter(status='success').count()
        failed_count = recent_logs.filter(status='failed').count()
        timeout_count = recent_logs.filter(status='timeout').count()

        # Average duration
        avg_duration = recent_logs.filter(
            status='success', duration__isnull=False
        ).values_list('duration', flat=True)
        avg_duration = sum(avg_duration) / len(avg_duration) if avg_duration else 0

        # Daily statistics
        daily_stats = recent_logs.values('start_time__date').annotate(
            total=Count('id'),
            success=Count('id', filter=Q(status='success')),
            failed=Count('id', filter=Q(status='failed'))
        ).order_by('start_time__date')

        return Response({
            'total_jobs': total_jobs,
            'enabled_jobs': enabled_jobs,
            'total_executions': total_executions,
            'success_count': success_count,
            'failed_count': failed_count,
            'timeout_count': timeout_count,
            'success_rate': round(success_count / total_executions * 100, 2) if total_executions else 0,
            'avg_duration_ms': round(avg_duration, 2),
            'daily_stats': list(daily_stats)
        })
