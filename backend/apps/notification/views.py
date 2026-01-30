"""
Notification views for M7 - Message Notification Center.
"""
import re
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone

from .models import (
    MessageTemplate, MessageLog, Notification, ChannelConfig,
    UserNotificationSetting, Blacklist
)
from .serializers import (
    MessageTemplateSerializer, MessageLogSerializer, NotificationSerializer,
    ChannelConfigSerializer, UserNotificationSettingSerializer,
    BlacklistSerializer, SendMessageSerializer
)
from .services import NotificationService


# Message template views
class MessageTemplateListCreateView(generics.ListCreateAPIView):
    """Message template list and create view."""
    permission_classes = [IsAuthenticated]
    serializer_class = MessageTemplateSerializer

    def get_queryset(self):
        queryset = MessageTemplate.objects.all()

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search)
            )

        channel = self.request.query_params.get('channel')
        if channel:
            queryset = queryset.filter(channel=channel)

        tpl_status = self.request.query_params.get('status')
        if tpl_status:
            queryset = queryset.filter(status=tpl_status)

        return queryset.order_by('-created_at')


class MessageTemplateDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Message template detail view."""
    permission_classes = [IsAuthenticated]
    serializer_class = MessageTemplateSerializer
    queryset = MessageTemplate.objects.all()


class MessageTemplatePreviewView(APIView):
    """Preview rendered message template."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            template = MessageTemplate.objects.get(pk=pk)
        except MessageTemplate.DoesNotExist:
            return Response({'error': '模板不存在'}, status=status.HTTP_404_NOT_FOUND)

        params = request.data.get('params', {})

        # Render template
        content = template.content
        subject = template.subject or ''

        for key, value in params.items():
            content = content.replace(f'${{{key}}}', str(value))
            subject = subject.replace(f'${{{key}}}', str(value))

        return Response({
            'subject': subject,
            'content': content,
            'channel': template.channel
        })


# Message log views
class MessageLogListView(APIView):
    """List message logs."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = MessageLog.objects.all()

        channel = request.query_params.get('channel')
        if channel:
            queryset = queryset.filter(channel=channel)

        log_status = request.query_params.get('status')
        if log_status:
            queryset = queryset.filter(status=log_status)

        recipient = request.query_params.get('recipient')
        if recipient:
            queryset = queryset.filter(recipient__icontains=recipient)

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
        serializer = MessageLogSerializer(logs, many=True)

        return Response({
            'total': total,
            'page': page,
            'page_size': page_size,
            'results': serializer.data
        })


class MessageLogDetailView(APIView):
    """Get message log detail."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            log = MessageLog.objects.get(pk=pk)
        except MessageLog.DoesNotExist:
            return Response({'error': '记录不存在'}, status=status.HTTP_404_NOT_FOUND)
        return Response(MessageLogSerializer(log).data)


class MessageLogRetryView(APIView):
    """Retry failed message."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            log = MessageLog.objects.get(pk=pk)
        except MessageLog.DoesNotExist:
            return Response({'error': '记录不存在'}, status=status.HTTP_404_NOT_FOUND)

        if log.status != 'failed':
            return Response({'error': '只能重试失败的消息'}, status=status.HTTP_400_BAD_REQUEST)

        if log.retry_count >= log.max_retry:
            return Response({'error': '已达到最大重试次数'}, status=status.HTTP_400_BAD_REQUEST)

        # Reset status and increment retry count
        log.status = 'pending'
        log.retry_count += 1
        log.error_msg = None
        log.save()

        # Trigger async send
        service = NotificationService()
        service.send_message_async(log.id)

        return Response({'message': '已加入重发队列'})


# Send message views
class SendMessageView(APIView):
    """Send message through specified channel."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        service = NotificationService()

        try:
            log_ids = service.send(
                channel=data['channel'],
                recipients=data['recipients'],
                template_code=data.get('template_code'),
                subject=data.get('subject'),
                content=data.get('content'),
                params=data.get('params', {}),
                business_type=data.get('business_type'),
                business_id=data.get('business_id')
            )
            return Response({
                'message': '消息已发送',
                'log_ids': log_ids
            })
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SendBatchMessageView(APIView):
    """Send batch messages."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        messages = request.data.get('messages', [])
        if not messages:
            return Response({'error': '请提供消息列表'}, status=status.HTTP_400_BAD_REQUEST)

        service = NotificationService()
        results = []

        for msg in messages:
            try:
                log_ids = service.send(
                    channel=msg.get('channel'),
                    recipients=msg.get('recipients', []),
                    template_code=msg.get('template_code'),
                    subject=msg.get('subject'),
                    content=msg.get('content'),
                    params=msg.get('params', {}),
                    business_type=msg.get('business_type'),
                    business_id=msg.get('business_id')
                )
                results.append({'success': True, 'log_ids': log_ids})
            except Exception as e:
                results.append({'success': False, 'error': str(e)})

        return Response({
            'message': f'批量发送完成，共{len(messages)}条',
            'results': results
        })


# Internal notification views
class MyNotificationListView(APIView):
    """List my notifications."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = Notification.objects.filter(user=request.user)

        notif_type = request.query_params.get('type')
        if notif_type:
            queryset = queryset.filter(type=notif_type)

        is_read = request.query_params.get('is_read')
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == 'true')

        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size

        total = queryset.count()
        notifications = queryset.order_by('-created_at')[start:end]
        serializer = NotificationSerializer(notifications, many=True)

        return Response({
            'total': total,
            'page': page,
            'page_size': page_size,
            'results': serializer.data
        })


class NotificationDetailView(APIView):
    """Get notification detail."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, user=request.user)
        except Notification.DoesNotExist:
            return Response({'error': '通知不存在'}, status=status.HTTP_404_NOT_FOUND)
        return Response(NotificationSerializer(notification).data)


class NotificationMarkReadView(APIView):
    """Mark notification as read."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, user=request.user)
        except Notification.DoesNotExist:
            return Response({'error': '通知不存在'}, status=status.HTTP_404_NOT_FOUND)

        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save()

        return Response({'message': '已标记为已读'})


class NotificationMarkAllReadView(APIView):
    """Mark all notifications as read."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        count = Notification.objects.filter(
            user=request.user, is_read=False
        ).update(is_read=True, read_at=timezone.now())
        return Response({'message': f'已将{count}条通知标记为已读'})


class NotificationDeleteView(APIView):
    """Delete notification."""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, user=request.user)
        except Notification.DoesNotExist:
            return Response({'error': '通知不存在'}, status=status.HTTP_404_NOT_FOUND)

        notification.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotificationUnreadCountView(APIView):
    """Get unread notification count."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({'unread_count': count})


# Channel config views
class ChannelConfigListView(APIView):
    """List channel configs."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        configs = ChannelConfig.objects.all().order_by('channel')
        serializer = ChannelConfigSerializer(configs, many=True)
        return Response(serializer.data)


class ChannelConfigDetailView(APIView):
    """Get/update channel config."""
    permission_classes = [IsAuthenticated]

    def get(self, request, channel):
        try:
            config = ChannelConfig.objects.get(channel=channel)
        except ChannelConfig.DoesNotExist:
            return Response({'error': '渠道配置不存在'}, status=status.HTTP_404_NOT_FOUND)
        return Response(ChannelConfigSerializer(config).data)

    def put(self, request, channel):
        config, created = ChannelConfig.objects.get_or_create(
            channel=channel,
            defaults={'name': dict(ChannelConfig.CHANNEL_CHOICES).get(channel, channel)}
        )
        serializer = ChannelConfigSerializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ChannelConfigTestView(APIView):
    """Test channel config."""
    permission_classes = [IsAuthenticated]

    def post(self, request, channel):
        try:
            config = ChannelConfig.objects.get(channel=channel)
        except ChannelConfig.DoesNotExist:
            return Response({'error': '渠道配置不存在'}, status=status.HTTP_404_NOT_FOUND)

        test_recipient = request.data.get('recipient')
        if not test_recipient:
            return Response({'error': '请提供测试接收人'}, status=status.HTTP_400_BAD_REQUEST)

        service = NotificationService()
        try:
            success, message = service.test_channel(channel, test_recipient, config.config)

            # Update test result
            config.last_test_time = timezone.now()
            config.last_test_result = '成功' if success else f'失败: {message}'
            config.save()

            if success:
                return Response({'message': '测试成功'})
            else:
                return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            config.last_test_time = timezone.now()
            config.last_test_result = f'异常: {str(e)}'
            config.save()
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# User notification setting views
class MyNotificationSettingsView(APIView):
    """Get/update my notification settings."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        settings = UserNotificationSetting.objects.filter(user=request.user)
        serializer = UserNotificationSettingSerializer(settings, many=True)
        return Response(serializer.data)

    def put(self, request):
        settings_data = request.data.get('settings', [])

        for setting_data in settings_data:
            notification_type = setting_data.get('notification_type')
            if not notification_type:
                continue

            setting, created = UserNotificationSetting.objects.get_or_create(
                user=request.user,
                notification_type=notification_type
            )
            for field in ['email_enabled', 'sms_enabled', 'im_enabled', 'internal_enabled']:
                if field in setting_data:
                    setattr(setting, field, setting_data[field])
            setting.save()

        return Response({'message': '设置已更新'})


# Blacklist views
class BlacklistListCreateView(APIView):
    """List and create blacklist entries."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = Blacklist.objects.all()

        bl_type = request.query_params.get('type')
        if bl_type:
            queryset = queryset.filter(type=bl_type)

        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(value__icontains=search)

        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size

        total = queryset.count()
        items = queryset.order_by('-created_at')[start:end]
        serializer = BlacklistSerializer(items, many=True)

        return Response({
            'total': total,
            'page': page,
            'page_size': page_size,
            'results': serializer.data
        })

    def post(self, request):
        serializer = BlacklistSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BlacklistDeleteView(APIView):
    """Delete blacklist entry."""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            item = Blacklist.objects.get(pk=pk)
        except Blacklist.DoesNotExist:
            return Response({'error': '记录不存在'}, status=status.HTTP_404_NOT_FOUND)

        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Statistics views
class MessageStatisticsView(APIView):
    """Get message statistics."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timezone.timedelta(days=days)

        # Total counts by status
        total_sent = MessageLog.objects.filter(
            created_at__gte=start_date, status='sent'
        ).count()
        total_failed = MessageLog.objects.filter(
            created_at__gte=start_date, status='failed'
        ).count()
        total_pending = MessageLog.objects.filter(
            created_at__gte=start_date, status='pending'
        ).count()

        # Counts by channel
        from django.db.models import Count
        channel_stats = MessageLog.objects.filter(
            created_at__gte=start_date
        ).values('channel').annotate(
            total=Count('id'),
            sent=Count('id', filter=Q(status='sent')),
            failed=Count('id', filter=Q(status='failed'))
        )

        return Response({
            'total_sent': total_sent,
            'total_failed': total_failed,
            'total_pending': total_pending,
            'success_rate': round(total_sent / (total_sent + total_failed) * 100, 2) if (total_sent + total_failed) > 0 else 0,
            'channel_stats': list(channel_stats)
        })
