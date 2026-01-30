"""
Notification views - placeholder for M0.
Views will be fully implemented in M7.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated


# Message template views
class MessageTemplateListCreateView(APIView):
    """Message template list and create view - to be implemented in M7."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'message': 'Message template list endpoint - M7'}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def post(self, request):
        return Response({'message': 'Message template create endpoint - M7'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class MessageTemplateDetailView(APIView):
    """Message template detail view - to be implemented in M7."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        return Response({'message': 'Message template detail endpoint - M7'}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def put(self, request, pk):
        return Response({'message': 'Message template update endpoint - M7'}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def delete(self, request, pk):
        return Response({'message': 'Message template delete endpoint - M7'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class MessageTemplatePreviewView(APIView):
    """Message template preview view - to be implemented in M7."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        return Response({'message': 'Message template preview endpoint - M7'}, status=status.HTTP_501_NOT_IMPLEMENTED)


# Message log views
class MessageLogListView(APIView):
    """Message log list view - to be implemented in M7."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'message': 'Message log list endpoint - M7'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class MessageLogDetailView(APIView):
    """Message log detail view - to be implemented in M7."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        return Response({'message': 'Message log detail endpoint - M7'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class MessageLogRetryView(APIView):
    """Message log retry view - to be implemented in M7."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        return Response({'message': 'Message log retry endpoint - M7'}, status=status.HTTP_501_NOT_IMPLEMENTED)


# Send message views
class SendMessageView(APIView):
    """Send message view - to be implemented in M7."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response({'message': 'Send message endpoint - M7'}, status=status.HTTP_501_NOT_IMPLEMENTED)


# Internal notification views
class MyNotificationListView(APIView):
    """My notification list view - to be implemented in M7."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'message': 'My notification list endpoint - M7'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class NotificationDetailView(APIView):
    """Notification detail view - to be implemented in M7."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        return Response({'message': 'Notification detail endpoint - M7'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class NotificationMarkReadView(APIView):
    """Mark notification as read view - to be implemented in M7."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        return Response({'message': 'Notification mark read endpoint - M7'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class NotificationMarkAllReadView(APIView):
    """Mark all notifications as read view - to be implemented in M7."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response({'message': 'Notification mark all read endpoint - M7'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class NotificationUnreadCountView(APIView):
    """Unread notification count view - to be implemented in M7."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'message': 'Notification unread count endpoint - M7'}, status=status.HTTP_501_NOT_IMPLEMENTED)


# Channel config views
class ChannelConfigListView(APIView):
    """Channel config list view - to be implemented in M7."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'message': 'Channel config list endpoint - M7'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class ChannelConfigDetailView(APIView):
    """Channel config detail view - to be implemented in M7."""
    permission_classes = [IsAuthenticated]

    def get(self, request, channel):
        return Response({'message': f'Channel config {channel} detail endpoint - M7'}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def put(self, request, channel):
        return Response({'message': f'Channel config {channel} update endpoint - M7'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class ChannelConfigTestView(APIView):
    """Channel config test view - to be implemented in M7."""
    permission_classes = [IsAuthenticated]

    def post(self, request, channel):
        return Response({'message': f'Channel config {channel} test endpoint - M7'}, status=status.HTTP_501_NOT_IMPLEMENTED)


# User notification setting views
class MyNotificationSettingsView(APIView):
    """My notification settings view - to be implemented in M7."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'message': 'My notification settings endpoint - M7'}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def put(self, request):
        return Response({'message': 'My notification settings update endpoint - M7'}, status=status.HTTP_501_NOT_IMPLEMENTED)


# Blacklist views
class BlacklistListCreateView(APIView):
    """Blacklist list and create view - to be implemented in M7."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'message': 'Blacklist list endpoint - M7'}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def post(self, request):
        return Response({'message': 'Blacklist create endpoint - M7'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class BlacklistDeleteView(APIView):
    """Blacklist delete view - to be implemented in M7."""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        return Response({'message': 'Blacklist delete endpoint - M7'}, status=status.HTTP_501_NOT_IMPLEMENTED)
