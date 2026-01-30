"""
Configuration views for M4 - Configuration Center.
"""
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone

from .models import MetaTable, ConfigHistory, SystemConfig, ConfigApproval
from .serializers import (
    MetaTableSerializer, MetaTableCreateUpdateSerializer,
    ConfigHistorySerializer, SystemConfigSerializer, SystemConfigUpdateSerializer,
    ConfigApprovalSerializer, DynamicConfigDataSerializer
)
from .services import DynamicTableService


# MetaTable views
class MetaTableListCreateView(generics.ListCreateAPIView):
    """MetaTable list and create view."""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = MetaTable.objects.all()

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(display_name__icontains=search)
            )

        meta_status = self.request.query_params.get('status')
        if meta_status:
            queryset = queryset.filter(status=meta_status)

        return queryset.order_by('sort_order', 'name')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MetaTableCreateUpdateSerializer
        return MetaTableSerializer

    def perform_create(self, serializer):
        meta_table = serializer.save()
        # Create dynamic table
        DynamicTableService.create_dynamic_table(meta_table)


class MetaTableDetailView(generics.RetrieveUpdateDestroyAPIView):
    """MetaTable detail, update and delete view."""
    permission_classes = [IsAuthenticated]
    queryset = MetaTable.objects.all()

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return MetaTableCreateUpdateSerializer
        return MetaTableSerializer


# Dynamic config views (Auto-CRUD)
class ConfigTableDataListCreateView(APIView):
    """Config table data list and create view."""
    permission_classes = [IsAuthenticated]

    def get_meta_table(self, table_name):
        try:
            return MetaTable.objects.get(name=table_name, status='active')
        except MetaTable.DoesNotExist:
            return None

    def get(self, request, table_name):
        meta_table = self.get_meta_table(table_name)
        if not meta_table:
            return Response(
                {'error': '配置表不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Parse filters from query params
        filters = {}
        for key, value in request.query_params.items():
            if key not in ['page', 'page_size']:
                filters[key] = value

        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))

        result = DynamicTableService.list_records(
            meta_table, filters, page, page_size
        )

        return Response(result)

    def post(self, request, table_name):
        meta_table = self.get_meta_table(table_name)
        if not meta_table:
            return Response(
                {'error': '配置表不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Validate data
        serializer = DynamicConfigDataSerializer(
            data=request.data, meta_table=meta_table
        )
        serializer.is_valid(raise_exception=True)

        # Check if audit is required
        if meta_table.need_audit:
            approval = ConfigApproval.objects.create(
                table_name=table_name,
                action='insert',
                new_data=serializer.validated_data,
                applicant=request.user,
                remark=request.data.get('remark', '')
            )
            return Response({
                'message': '已提交审批',
                'approval_id': approval.id
            }, status=status.HTTP_202_ACCEPTED)

        record = DynamicTableService.create_record(
            meta_table, serializer.validated_data, request.user.id
        )

        return Response(record, status=status.HTTP_201_CREATED)


class ConfigTableDataDetailView(APIView):
    """Config table data detail, update and delete view."""
    permission_classes = [IsAuthenticated]

    def get_meta_table(self, table_name):
        try:
            return MetaTable.objects.get(name=table_name, status='active')
        except MetaTable.DoesNotExist:
            return None

    def get(self, request, table_name, pk):
        meta_table = self.get_meta_table(table_name)
        if not meta_table:
            return Response(
                {'error': '配置表不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        record = DynamicTableService.get_record(meta_table, pk)
        if not record:
            return Response(
                {'error': '记录不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(record)

    def put(self, request, table_name, pk):
        meta_table = self.get_meta_table(table_name)
        if not meta_table:
            return Response(
                {'error': '配置表不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        old_record = DynamicTableService.get_record(meta_table, pk)
        if not old_record:
            return Response(
                {'error': '记录不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = DynamicConfigDataSerializer(
            data=request.data, meta_table=meta_table
        )
        serializer.is_valid(raise_exception=True)

        # Check if audit is required
        if meta_table.need_audit:
            approval = ConfigApproval.objects.create(
                table_name=table_name,
                record_id=pk,
                action='update',
                old_data=old_record,
                new_data=serializer.validated_data,
                applicant=request.user,
                remark=request.data.get('remark', '')
            )
            return Response({
                'message': '已提交审批',
                'approval_id': approval.id
            }, status=status.HTTP_202_ACCEPTED)

        record = DynamicTableService.update_record(
            meta_table, pk, serializer.validated_data,
            request.user.id, request.data.get('remark')
        )

        return Response(record)

    def delete(self, request, table_name, pk):
        meta_table = self.get_meta_table(table_name)
        if not meta_table:
            return Response(
                {'error': '配置表不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        old_record = DynamicTableService.get_record(meta_table, pk)
        if not old_record:
            return Response(
                {'error': '记录不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if audit is required
        if meta_table.need_audit:
            approval = ConfigApproval.objects.create(
                table_name=table_name,
                record_id=pk,
                action='delete',
                old_data=old_record,
                new_data={},
                applicant=request.user,
                remark=request.data.get('remark', '')
            )
            return Response({
                'message': '已提交审批',
                'approval_id': approval.id
            }, status=status.HTTP_202_ACCEPTED)

        DynamicTableService.delete_record(meta_table, pk, request.user.id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ConfigTableDataHistoryView(APIView):
    """Config table data history view."""
    permission_classes = [IsAuthenticated]

    def get(self, request, table_name, pk):
        try:
            meta_table = MetaTable.objects.get(name=table_name)
        except MetaTable.DoesNotExist:
            return Response(
                {'error': '配置表不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        histories = ConfigHistory.objects.filter(
            table_name=table_name, record_id=pk
        ).order_by('-version')

        serializer = ConfigHistorySerializer(histories, many=True)
        return Response(serializer.data)


class ConfigTableDataRollbackView(APIView):
    """Config table data rollback view."""
    permission_classes = [IsAuthenticated]

    def post(self, request, table_name, pk):
        try:
            meta_table = MetaTable.objects.get(name=table_name)
        except MetaTable.DoesNotExist:
            return Response(
                {'error': '配置表不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        version = request.data.get('version')
        if not version:
            return Response(
                {'error': '请指定回滚版本'},
                status=status.HTTP_400_BAD_REQUEST
            )

        record = DynamicTableService.rollback_record(
            meta_table, pk, int(version), request.user.id
        )

        if not record:
            return Response(
                {'error': '回滚失败，版本不存在'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({
            'message': f'已回滚到版本 {version}',
            'data': record
        })


class ConfigTableDataDiffView(APIView):
    """Config table data diff/compare view."""
    permission_classes = [IsAuthenticated]

    def get(self, request, table_name, pk):
        try:
            meta_table = MetaTable.objects.get(name=table_name)
        except MetaTable.DoesNotExist:
            return Response(
                {'error': '配置表不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        version1 = request.query_params.get('v1')
        version2 = request.query_params.get('v2')

        if not version1 or not version2:
            return Response(
                {'error': '请指定两个版本号 v1 和 v2'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = DynamicTableService.compare_versions(
            meta_table, pk, int(version1), int(version2)
        )

        if 'error' in result:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        return Response(result)


# System config views
class SystemConfigListView(generics.ListAPIView):
    """System config list view."""
    permission_classes = [IsAuthenticated]
    serializer_class = SystemConfigSerializer

    def get_queryset(self):
        queryset = SystemConfig.objects.all()

        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(key__icontains=search) |
                Q(description__icontains=search)
            )

        return queryset.order_by('category', 'key')


class SystemConfigDetailView(APIView):
    """System config detail and update view."""
    permission_classes = [IsAuthenticated]

    def get(self, request, key):
        try:
            config = SystemConfig.objects.get(key=key)
        except SystemConfig.DoesNotExist:
            return Response(
                {'error': '配置项不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = SystemConfigSerializer(config)
        return Response(serializer.data)

    def put(self, request, key):
        try:
            config = SystemConfig.objects.get(key=key)
        except SystemConfig.DoesNotExist:
            return Response(
                {'error': '配置项不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        if config.is_readonly:
            return Response(
                {'error': '该配置项为只读'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = SystemConfigUpdateSerializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(SystemConfigSerializer(config).data)


# Config approval views
class ConfigApprovalListView(generics.ListAPIView):
    """Config approval list view."""
    permission_classes = [IsAuthenticated]
    serializer_class = ConfigApprovalSerializer

    def get_queryset(self):
        queryset = ConfigApproval.objects.all()

        approval_status = self.request.query_params.get('status')
        if approval_status:
            queryset = queryset.filter(status=approval_status)

        table_name = self.request.query_params.get('table_name')
        if table_name:
            queryset = queryset.filter(table_name=table_name)

        # Filter by applicant or approver
        my_applications = self.request.query_params.get('my_applications')
        if my_applications:
            queryset = queryset.filter(applicant=self.request.user)

        return queryset.order_by('-created_at')


class ConfigApprovalDetailView(APIView):
    """Config approval detail view."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            approval = ConfigApproval.objects.get(pk=pk)
        except ConfigApproval.DoesNotExist:
            return Response(
                {'error': '审批记录不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ConfigApprovalSerializer(approval)
        return Response(serializer.data)


class ConfigApprovalApproveView(APIView):
    """Config approval approve view."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            approval = ConfigApproval.objects.get(pk=pk)
        except ConfigApproval.DoesNotExist:
            return Response(
                {'error': '审批记录不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        if approval.status != 'pending':
            return Response(
                {'error': '该申请已处理'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            meta_table = MetaTable.objects.get(name=approval.table_name)
        except MetaTable.DoesNotExist:
            return Response(
                {'error': '配置表不存在'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Execute the approved action
        if approval.action == 'insert':
            DynamicTableService.create_record(
                meta_table, approval.new_data, approval.applicant_id
            )
        elif approval.action == 'update':
            DynamicTableService.update_record(
                meta_table, approval.record_id,
                approval.new_data, approval.applicant_id
            )
        elif approval.action == 'delete':
            DynamicTableService.delete_record(
                meta_table, approval.record_id, approval.applicant_id
            )

        approval.status = 'approved'
        approval.approver = request.user
        approval.approved_at = timezone.now()
        approval.approve_remark = request.data.get('remark', '')
        approval.save()

        return Response({'message': '审批通过'})


class ConfigApprovalRejectView(APIView):
    """Config approval reject view."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            approval = ConfigApproval.objects.get(pk=pk)
        except ConfigApproval.DoesNotExist:
            return Response(
                {'error': '审批记录不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        if approval.status != 'pending':
            return Response(
                {'error': '该申请已处理'},
                status=status.HTTP_400_BAD_REQUEST
            )

        approval.status = 'rejected'
        approval.approver = request.user
        approval.approved_at = timezone.now()
        approval.approve_remark = request.data.get('remark', '')
        approval.save()

        return Response({'message': '审批已拒绝'})
