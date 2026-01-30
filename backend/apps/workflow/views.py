"""
Workflow views - placeholder for M0.
Views will be fully implemented in M5.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated


# Workflow definition views
class WorkflowDefinitionListCreateView(APIView):
    """Workflow definition list and create view - to be implemented in M5."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'message': 'Workflow definition list endpoint - M5'}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def post(self, request):
        return Response({'message': 'Workflow definition create endpoint - M5'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class WorkflowDefinitionDetailView(APIView):
    """Workflow definition detail view - to be implemented in M5."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        return Response({'message': 'Workflow definition detail endpoint - M5'}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def put(self, request, pk):
        return Response({'message': 'Workflow definition update endpoint - M5'}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def delete(self, request, pk):
        return Response({'message': 'Workflow definition delete endpoint - M5'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class WorkflowDefinitionPublishView(APIView):
    """Workflow definition publish view - to be implemented in M5."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        return Response({'message': 'Workflow definition publish endpoint - M5'}, status=status.HTTP_501_NOT_IMPLEMENTED)


# Approval instance views
class ApprovalListView(APIView):
    """Approval list view (my applications/my approvals) - to be implemented in M5."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'message': 'Approval list endpoint - M5'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class ApprovalCreateView(APIView):
    """Approval create view - to be implemented in M5."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response({'message': 'Approval create endpoint - M5'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class ApprovalDetailView(APIView):
    """Approval detail view - to be implemented in M5."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        return Response({'message': 'Approval detail endpoint - M5'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class ApprovalApproveView(APIView):
    """Approval approve view - to be implemented in M5."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        return Response({'message': 'Approval approve endpoint - M5'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class ApprovalRejectView(APIView):
    """Approval reject view - to be implemented in M5."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        return Response({'message': 'Approval reject endpoint - M5'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class ApprovalTransferView(APIView):
    """Approval transfer view - to be implemented in M5."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        return Response({'message': 'Approval transfer endpoint - M5'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class ApprovalWithdrawView(APIView):
    """Approval withdraw view - to be implemented in M5."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        return Response({'message': 'Approval withdraw endpoint - M5'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class ApprovalUrgeView(APIView):
    """Approval urge view - to be implemented in M5."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        return Response({'message': 'Approval urge endpoint - M5'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class ApprovalAddApproverView(APIView):
    """Approval add approver (co-sign) view - to be implemented in M5."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        return Response({'message': 'Approval add approver endpoint - M5'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class ApprovalCommentView(APIView):
    """Approval comment view - to be implemented in M5."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        return Response({'message': 'Approval comment endpoint - M5'}, status=status.HTTP_501_NOT_IMPLEMENTED)


# Task views
class MyPendingTasksView(APIView):
    """My pending approval tasks view - to be implemented in M5."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'message': 'My pending tasks endpoint - M5'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class MyCompletedTasksView(APIView):
    """My completed approval tasks view - to be implemented in M5."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'message': 'My completed tasks endpoint - M5'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class MyCcApprovalsView(APIView):
    """My CC approvals view - to be implemented in M5."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'message': 'My CC approvals endpoint - M5'}, status=status.HTTP_501_NOT_IMPLEMENTED)
