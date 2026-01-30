"""
Audit views for M6 - Audit Log Center.
"""
import io
import pandas as pd
from django.http import HttpResponse
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count
from django.utils import timezone

from .models import AuditLog, DataChangeLog, LoginLog, AlertRule, AlertHistory
from .serializers import (
    AuditLogSerializer, DataChangeLogSerializer, LoginLogSerializer,
    AlertRuleSerializer, AlertRuleCreateUpdateSerializer, AlertHistorySerializer
)


class AuditLogListView(APIView):
    """List audit logs."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = AuditLog.objects.all()

        user_id = request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        module = request.query_params.get('module')
        if module:
            queryset = queryset.filter(module=module)

        action = request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)

        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(user_name__icontains=search) |
                Q(request_path__icontains=search) |
                Q(ip_address__icontains=search)
            )

        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size

        total = queryset.count()
        logs = queryset.order_by('-created_at')[start:end]
        serializer = AuditLogSerializer(logs, many=True)

        return Response({
            'total': total,
            'page': page,
            'page_size': page_size,
            'results': serializer.data
        })


class AuditLogDetailView(APIView):
    """Get audit log detail."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            log = AuditLog.objects.get(pk=pk)
        except AuditLog.DoesNotExist:
            return Response({'error': '日志不存在'}, status=status.HTTP_404_NOT_FOUND)
        return Response(AuditLogSerializer(log).data)


class AuditLogExportView(APIView):
    """Export audit logs to Excel."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        queryset = AuditLog.objects.all()

        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)

        logs = queryset.order_by('-created_at')[:10000]
        data = AuditLogSerializer(logs, many=True).data

        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='AuditLog')
        output.seek(0)

        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="audit_log.xlsx"'
        return response


class DataChangeLogListView(APIView):
    """List data change logs."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = DataChangeLog.objects.all()

        table_name = request.query_params.get('table_name')
        if table_name:
            queryset = queryset.filter(table_name=table_name)

        record_id = request.query_params.get('record_id')
        if record_id:
            queryset = queryset.filter(record_id=record_id)

        action = request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)

        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size

        total = queryset.count()
        logs = queryset.order_by('-created_at')[start:end]
        serializer = DataChangeLogSerializer(logs, many=True)

        return Response({
            'total': total,
            'page': page,
            'page_size': page_size,
            'results': serializer.data
        })


class DataChangeLogDetailView(APIView):
    """Get data change log detail."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            log = DataChangeLog.objects.get(pk=pk)
        except DataChangeLog.DoesNotExist:
            return Response({'error': '日志不存在'}, status=status.HTTP_404_NOT_FOUND)
        return Response(DataChangeLogSerializer(log).data)


class LoginLogListView(APIView):
    """List login logs."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = LoginLog.objects.all()

        user_id = request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        login_status = request.query_params.get('status')
        if login_status:
            queryset = queryset.filter(status=login_status)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)

        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size

        total = queryset.count()
        logs = queryset.order_by('-created_at')[start:end]
        serializer = LoginLogSerializer(logs, many=True)

        return Response({
            'total': total,
            'page': page,
            'page_size': page_size,
            'results': serializer.data
        })


class AlertRuleListCreateView(generics.ListCreateAPIView):
    """Alert rule list and create view."""
    permission_classes = [IsAuthenticated]
    queryset = AlertRule.objects.all().order_by('-created_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AlertRuleCreateUpdateSerializer
        return AlertRuleSerializer


class AlertRuleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Alert rule detail view."""
    permission_classes = [IsAuthenticated]
    queryset = AlertRule.objects.all()

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return AlertRuleCreateUpdateSerializer
        return AlertRuleSerializer


class AlertRuleStatusView(APIView):
    """Toggle alert rule status."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            rule = AlertRule.objects.get(pk=pk)
        except AlertRule.DoesNotExist:
            return Response({'error': '规则不存在'}, status=status.HTTP_404_NOT_FOUND)

        rule.status = 'inactive' if rule.status == 'active' else 'active'
        rule.save(update_fields=['status'])
        return Response({'message': '状态已更新', 'status': rule.status})


class AlertHistoryListView(APIView):
    """List alert history."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = AlertHistory.objects.all()

        alert_status = request.query_params.get('status')
        if alert_status:
            queryset = queryset.filter(status=alert_status)

        level = request.query_params.get('level')
        if level:
            queryset = queryset.filter(level=level)

        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size

        total = queryset.count()
        alerts = queryset.order_by('-triggered_at')[start:end]
        serializer = AlertHistorySerializer(alerts, many=True)

        return Response({
            'total': total,
            'page': page,
            'page_size': page_size,
            'results': serializer.data
        })


class AlertHistoryDetailView(APIView):
    """Get alert history detail."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            alert = AlertHistory.objects.get(pk=pk)
        except AlertHistory.DoesNotExist:
            return Response({'error': '告警不存在'}, status=status.HTTP_404_NOT_FOUND)
        return Response(AlertHistorySerializer(alert).data)


class AlertHistoryAcknowledgeView(APIView):
    """Acknowledge an alert."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            alert = AlertHistory.objects.get(pk=pk)
        except AlertHistory.DoesNotExist:
            return Response({'error': '告警不存在'}, status=status.HTTP_404_NOT_FOUND)

        if alert.status != 'triggered':
            return Response({'error': '该告警已处理'}, status=status.HTTP_400_BAD_REQUEST)

        alert.status = 'acknowledged'
        alert.acknowledged_by = request.user
        alert.acknowledged_at = timezone.now()
        alert.save()
        return Response({'message': '告警已确认'})


class AlertHistoryResolveView(APIView):
    """Resolve an alert."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            alert = AlertHistory.objects.get(pk=pk)
        except AlertHistory.DoesNotExist:
            return Response({'error': '告警不存在'}, status=status.HTTP_404_NOT_FOUND)

        if alert.status == 'resolved':
            return Response({'error': '该告警已解决'}, status=status.HTTP_400_BAD_REQUEST)

        alert.status = 'resolved'
        alert.resolved_by = request.user
        alert.resolved_at = timezone.now()
        alert.resolve_comment = request.data.get('comment', '')
        alert.save()
        return Response({'message': '告警已解决'})


class SystemHealthDashboardView(APIView):
    """System health dashboard data."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        today = now.date()
        last_hour = now - timezone.timedelta(hours=1)
        last_24h = now - timezone.timedelta(hours=24)

        # API statistics
        total_requests_24h = AuditLog.objects.filter(created_at__gte=last_24h).count()
        error_requests_24h = AuditLog.objects.filter(
            created_at__gte=last_24h, response_code__gte=400
        ).count()

        # Login statistics
        login_success_24h = LoginLog.objects.filter(
            created_at__gte=last_24h, status='success'
        ).count()
        login_failed_24h = LoginLog.objects.filter(
            created_at__gte=last_24h, status='failed'
        ).count()

        # Active alerts
        active_alerts = AlertHistory.objects.filter(
            status__in=['triggered', 'acknowledged']
        ).count()

        return Response({
            'total_requests_24h': total_requests_24h,
            'error_requests_24h': error_requests_24h,
            'error_rate': round(error_requests_24h / total_requests_24h * 100, 2) if total_requests_24h else 0,
            'login_success_24h': login_success_24h,
            'login_failed_24h': login_failed_24h,
            'active_alerts': active_alerts
        })


class ApiStatisticsView(APIView):
    """API call statistics."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timezone.timedelta(days=days)

        # Group by date
        daily_stats = AuditLog.objects.filter(
            created_at__gte=start_date
        ).extra(
            select={'date': 'DATE(created_at)'}
        ).values('date').annotate(
            total=Count('id'),
            errors=Count('id', filter=Q(response_code__gte=400))
        ).order_by('date')

        # Top endpoints
        top_endpoints = AuditLog.objects.filter(
            created_at__gte=start_date
        ).values('request_path', 'request_method').annotate(
            count=Count('id')
        ).order_by('-count')[:10]

        return Response({
            'daily_stats': list(daily_stats),
            'top_endpoints': list(top_endpoints)
        })


class OnlineUsersView(APIView):
    """Get currently online users (based on recent activity)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Consider users active in last 30 minutes as online
        active_threshold = timezone.now() - timezone.timedelta(minutes=30)

        active_users = AuditLog.objects.filter(
            created_at__gte=active_threshold,
            user_id__isnull=False
        ).values('user_id', 'user_name').distinct()

        return Response({
            'online_count': active_users.count(),
            'users': list(active_users)
        })
