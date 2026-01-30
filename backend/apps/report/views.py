"""
Report views - placeholder for M0.
Views will be fully implemented in M3.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated


# DataSource views
class DataSourceListCreateView(APIView):
    """DataSource list and create view - to be implemented in M3."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'message': 'DataSource list endpoint - M3'}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def post(self, request):
        return Response({'message': 'DataSource create endpoint - M3'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class DataSourceDetailView(APIView):
    """DataSource detail view - to be implemented in M3."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        return Response({'message': 'DataSource detail endpoint - M3'}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def put(self, request, pk):
        return Response({'message': 'DataSource update endpoint - M3'}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def delete(self, request, pk):
        return Response({'message': 'DataSource delete endpoint - M3'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class DataSourceTestView(APIView):
    """DataSource connection test view - to be implemented in M3."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        return Response({'message': 'DataSource test endpoint - M3'}, status=status.HTTP_501_NOT_IMPLEMENTED)


# Report views
class ReportListCreateView(APIView):
    """Report list and create view - to be implemented in M3."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'message': 'Report list endpoint - M3'}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def post(self, request):
        return Response({'message': 'Report create endpoint - M3'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class ReportDetailView(APIView):
    """Report detail view - to be implemented in M3."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        return Response({'message': 'Report detail endpoint - M3'}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def put(self, request, pk):
        return Response({'message': 'Report update endpoint - M3'}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def delete(self, request, pk):
        return Response({'message': 'Report delete endpoint - M3'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class ReportQueryView(APIView):
    """Report query/execute view - to be implemented in M3."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        return Response({'message': 'Report query endpoint - M3'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class ReportExportView(APIView):
    """Report export view - to be implemented in M3."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        return Response({'message': 'Report export endpoint - M3'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class ReportPublishView(APIView):
    """Report publish view - to be implemented in M3."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        return Response({'message': 'Report publish endpoint - M3'}, status=status.HTTP_501_NOT_IMPLEMENTED)


# Subscription views
class ReportSubscriptionListCreateView(APIView):
    """Report subscription list and create view - to be implemented in M3."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        return Response({'message': 'Report subscription list endpoint - M3'}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def post(self, request, pk):
        return Response({'message': 'Report subscription create endpoint - M3'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class ReportSubscriptionDetailView(APIView):
    """Report subscription detail view - to be implemented in M3."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, sub_id):
        return Response({'message': 'Report subscription detail endpoint - M3'}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def put(self, request, pk, sub_id):
        return Response({'message': 'Report subscription update endpoint - M3'}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def delete(self, request, pk, sub_id):
        return Response({'message': 'Report subscription delete endpoint - M3'}, status=status.HTTP_501_NOT_IMPLEMENTED)


# Favorite views
class ReportFavoriteView(APIView):
    """Report favorite toggle view - to be implemented in M3."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        return Response({'message': 'Report favorite endpoint - M3'}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def delete(self, request, pk):
        return Response({'message': 'Report unfavorite endpoint - M3'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class MyFavoriteReportsView(APIView):
    """My favorite reports list view - to be implemented in M3."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'message': 'My favorite reports endpoint - M3'}, status=status.HTTP_501_NOT_IMPLEMENTED)
