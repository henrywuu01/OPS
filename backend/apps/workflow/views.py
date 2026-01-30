"""
Workflow views for M5 - Workflow Approval Engine.
"""
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone

from .models import (
    WorkflowDefinition, ApprovalInstance, ApprovalRecord,
    ApprovalTask, ApprovalCc
)
from .serializers import (
    WorkflowDefinitionSerializer, WorkflowDefinitionCreateUpdateSerializer,
    ApprovalInstanceSerializer, ApprovalInstanceCreateSerializer,
    ApprovalRecordSerializer, ApprovalTaskSerializer, ApprovalCcSerializer,
    ApprovalActionSerializer, ApprovalTransferSerializer
)
from .engine import WorkflowEngine
from apps.auth.models import User


# Workflow definition views
class WorkflowDefinitionListCreateView(generics.ListCreateAPIView):
    """Workflow definition list and create view."""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = WorkflowDefinition.objects.all()

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search)
            )

        wf_status = self.request.query_params.get('status')
        if wf_status:
            queryset = queryset.filter(status=wf_status)

        return queryset.order_by('-created_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return WorkflowDefinitionCreateUpdateSerializer
        return WorkflowDefinitionSerializer


class WorkflowDefinitionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Workflow definition detail view."""
    permission_classes = [IsAuthenticated]
    queryset = WorkflowDefinition.objects.all()

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return WorkflowDefinitionCreateUpdateSerializer
        return WorkflowDefinitionSerializer


class WorkflowDefinitionPublishView(APIView):
    """Publish or unpublish workflow definition."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            workflow = WorkflowDefinition.objects.get(pk=pk)
        except WorkflowDefinition.DoesNotExist:
            return Response(
                {'error': '流程定义不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        action = request.data.get('action', 'publish')

        if action == 'publish':
            workflow.status = 'published'
            workflow.version += 1
            message = '流程已发布'
        elif action == 'unpublish':
            workflow.status = 'draft'
            message = '流程已取消发布'
        elif action == 'archive':
            workflow.status = 'archived'
            message = '流程已归档'
        else:
            return Response(
                {'error': '无效的操作'},
                status=status.HTTP_400_BAD_REQUEST
            )

        workflow.save()
        return Response({'message': message, 'status': workflow.status})


# Approval views
class ApprovalListView(APIView):
    """List approvals (applications and pending approvals)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        list_type = request.query_params.get('type', 'my_applications')

        if list_type == 'my_applications':
            queryset = ApprovalInstance.objects.filter(applicant=request.user)
        elif list_type == 'pending':
            instance_ids = ApprovalTask.objects.filter(
                assignee=request.user, status='pending'
            ).values_list('instance_id', flat=True)
            queryset = ApprovalInstance.objects.filter(id__in=instance_ids)
        elif list_type == 'completed':
            instance_ids = ApprovalTask.objects.filter(
                assignee=request.user, status='completed'
            ).values_list('instance_id', flat=True)
            queryset = ApprovalInstance.objects.filter(id__in=instance_ids)
        elif list_type == 'cc':
            instance_ids = ApprovalCc.objects.filter(
                user=request.user
            ).values_list('instance_id', flat=True)
            queryset = ApprovalInstance.objects.filter(id__in=instance_ids)
        else:
            queryset = ApprovalInstance.objects.none()

        # Filters
        approval_status = request.query_params.get('status')
        if approval_status:
            queryset = queryset.filter(status=approval_status)

        business_type = request.query_params.get('business_type')
        if business_type:
            queryset = queryset.filter(business_type=business_type)

        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        start = (page - 1) * page_size
        end = start + page_size

        total = queryset.count()
        instances = queryset.order_by('-created_at')[start:end]
        serializer = ApprovalInstanceSerializer(instances, many=True)

        return Response({
            'total': total,
            'page': page,
            'page_size': page_size,
            'results': serializer.data
        })


class ApprovalCreateView(APIView):
    """Create and submit a new approval."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ApprovalInstanceCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        # Start workflow
        engine = WorkflowEngine(instance)
        engine.start()

        return Response(
            ApprovalInstanceSerializer(instance).data,
            status=status.HTTP_201_CREATED
        )


class ApprovalDetailView(APIView):
    """Get approval detail."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            instance = ApprovalInstance.objects.get(pk=pk)
        except ApprovalInstance.DoesNotExist:
            return Response(
                {'error': '审批不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ApprovalInstanceSerializer(instance)
        return Response(serializer.data)


class ApprovalApproveView(APIView):
    """Approve the current task."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            instance = ApprovalInstance.objects.get(pk=pk)
        except ApprovalInstance.DoesNotExist:
            return Response(
                {'error': '审批不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        task = instance.tasks.filter(
            assignee=request.user, status='pending'
        ).first()

        if not task:
            return Response(
                {'error': '您没有待处理的审批任务'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ApprovalActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        engine = WorkflowEngine(instance)
        engine.approve(
            task, request.user,
            serializer.validated_data.get('comment'),
            serializer.validated_data.get('attachments')
        )

        return Response({
            'message': '审批通过',
            'status': instance.status
        })


class ApprovalRejectView(APIView):
    """Reject the current task."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            instance = ApprovalInstance.objects.get(pk=pk)
        except ApprovalInstance.DoesNotExist:
            return Response(
                {'error': '审批不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        task = instance.tasks.filter(
            assignee=request.user, status='pending'
        ).first()

        if not task:
            return Response(
                {'error': '您没有待处理的审批任务'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ApprovalActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        engine = WorkflowEngine(instance)
        engine.reject(
            task, request.user,
            serializer.validated_data.get('comment'),
            serializer.validated_data.get('attachments')
        )

        return Response({
            'message': '审批已拒绝',
            'status': instance.status
        })


class ApprovalTransferView(APIView):
    """Transfer approval to another user."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            instance = ApprovalInstance.objects.get(pk=pk)
        except ApprovalInstance.DoesNotExist:
            return Response(
                {'error': '审批不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        task = instance.tasks.filter(
            assignee=request.user, status='pending'
        ).first()

        if not task:
            return Response(
                {'error': '您没有待处理的审批任务'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ApprovalTransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            transfer_to = User.objects.get(pk=serializer.validated_data['transfer_to'])
        except User.DoesNotExist:
            return Response(
                {'error': '转交用户不存在'},
                status=status.HTTP_400_BAD_REQUEST
            )

        engine = WorkflowEngine(instance)
        engine.transfer(
            task, request.user, transfer_to,
            serializer.validated_data.get('comment')
        )

        return Response({'message': '已转交'})


class ApprovalWithdrawView(APIView):
    """Withdraw the approval application."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            instance = ApprovalInstance.objects.get(pk=pk)
        except ApprovalInstance.DoesNotExist:
            return Response(
                {'error': '审批不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        engine = WorkflowEngine(instance)
        try:
            engine.withdraw(request.user)
            return Response({'message': '已撤回'})
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class ApprovalUrgeView(APIView):
    """Send urge notification."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            instance = ApprovalInstance.objects.get(pk=pk)
        except ApprovalInstance.DoesNotExist:
            return Response(
                {'error': '审批不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        if instance.applicant != request.user:
            return Response(
                {'error': '只有申请人可以催办'},
                status=status.HTTP_400_BAD_REQUEST
            )

        engine = WorkflowEngine(instance)
        if engine.urge(request.user):
            return Response({'message': '催办成功'})
        else:
            return Response(
                {'error': '没有待处理的审批任务'},
                status=status.HTTP_400_BAD_REQUEST
            )


class ApprovalAddApproverView(APIView):
    """Add additional approver (co-sign)."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            instance = ApprovalInstance.objects.get(pk=pk)
        except ApprovalInstance.DoesNotExist:
            return Response(
                {'error': '审批不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        task = instance.tasks.filter(
            assignee=request.user, status='pending'
        ).first()

        if not task:
            return Response(
                {'error': '您没有待处理的审批任务'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user_id = request.data.get('user_id')
        if not user_id:
            return Response(
                {'error': '请指定加签用户'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            add_user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': '用户不存在'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create additional task
        ApprovalTask.objects.create(
            instance=instance,
            node_id=task.node_id,
            node_name=task.node_name,
            assign_type='user',
            assignee=add_user,
            status='pending'
        )

        # Create record
        ApprovalRecord.objects.create(
            instance=instance,
            node_id=task.node_id,
            node_name=task.node_name,
            approver=request.user,
            action='add_approver',
            comment=f'加签给 {add_user.real_name}'
        )

        return Response({'message': '加签成功'})


class ApprovalCommentView(APIView):
    """Add comment to approval."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            instance = ApprovalInstance.objects.get(pk=pk)
        except ApprovalInstance.DoesNotExist:
            return Response(
                {'error': '审批不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        comment = request.data.get('comment')
        if not comment:
            return Response(
                {'error': '请输入评论内容'},
                status=status.HTTP_400_BAD_REQUEST
            )

        attachments = request.data.get('attachments', [])

        engine = WorkflowEngine(instance)
        engine.add_comment(request.user, comment, attachments)

        return Response({'message': '评论成功'})


# Task views
class MyPendingTasksView(APIView):
    """Get my pending approval tasks."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tasks = ApprovalTask.objects.filter(
            assignee=request.user, status='pending'
        ).select_related('instance').order_by('-created_at')

        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        start = (page - 1) * page_size
        end = start + page_size

        total = tasks.count()
        tasks_page = tasks[start:end]
        serializer = ApprovalTaskSerializer(tasks_page, many=True)

        return Response({
            'total': total,
            'page': page,
            'page_size': page_size,
            'results': serializer.data
        })


class MyCompletedTasksView(APIView):
    """Get my completed approval tasks."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tasks = ApprovalTask.objects.filter(
            assignee=request.user, status='completed'
        ).select_related('instance').order_by('-completed_at')

        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        start = (page - 1) * page_size
        end = start + page_size

        total = tasks.count()
        tasks_page = tasks[start:end]
        serializer = ApprovalTaskSerializer(tasks_page, many=True)

        return Response({
            'total': total,
            'page': page,
            'page_size': page_size,
            'results': serializer.data
        })


class MyCcApprovalsView(APIView):
    """Get approvals I'm CC'd on."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ccs = ApprovalCc.objects.filter(
            user=request.user
        ).select_related('instance').order_by('-created_at')

        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        start = (page - 1) * page_size
        end = start + page_size

        total = ccs.count()
        ccs_page = ccs[start:end]
        serializer = ApprovalCcSerializer(ccs_page, many=True)

        return Response({
            'total': total,
            'page': page,
            'page_size': page_size,
            'results': serializer.data
        })
