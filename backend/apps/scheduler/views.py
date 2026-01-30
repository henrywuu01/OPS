"""
Scheduler views - placeholder for M0.
Views will be fully implemented in M2.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated


class JobListCreateView(APIView):
    """Job list and create view - to be implemented in M2."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'message': 'Job list endpoint - M2'}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def post(self, request):
        return Response({'message': 'Job create endpoint - M2'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class JobDetailView(APIView):
    """Job detail view - to be implemented in M2."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        return Response({'message': 'Job detail endpoint - M2'}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def put(self, request, pk):
        return Response({'message': 'Job update endpoint - M2'}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def delete(self, request, pk):
        return Response({'message': 'Job delete endpoint - M2'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class JobTriggerView(APIView):
    """Job manual trigger view - to be implemented in M2."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        return Response({'message': 'Job trigger endpoint - M2'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class JobPauseView(APIView):
    """Job pause view - to be implemented in M2."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        return Response({'message': 'Job pause endpoint - M2'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class JobResumeView(APIView):
    """Job resume view - to be implemented in M2."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        return Response({'message': 'Job resume endpoint - M2'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class JobLogListView(APIView):
    """Job log list view - to be implemented in M2."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        return Response({'message': 'Job log list endpoint - M2'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class JobLogDetailView(APIView):
    """Job log detail view - to be implemented in M2."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, log_id):
        return Response({'message': 'Job log detail endpoint - M2'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class JobFlowListCreateView(APIView):
    """Job flow list and create view - to be implemented in M2."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'message': 'Job flow list endpoint - M2'}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def post(self, request):
        return Response({'message': 'Job flow create endpoint - M2'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class JobFlowDetailView(APIView):
    """Job flow detail view - to be implemented in M2."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        return Response({'message': 'Job flow detail endpoint - M2'}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def put(self, request, pk):
        return Response({'message': 'Job flow update endpoint - M2'}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def delete(self, request, pk):
        return Response({'message': 'Job flow delete endpoint - M2'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class JobFlowTriggerView(APIView):
    """Job flow manual trigger view - to be implemented in M2."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        return Response({'message': 'Job flow trigger endpoint - M2'}, status=status.HTTP_501_NOT_IMPLEMENTED)
