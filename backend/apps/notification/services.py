"""
Notification services for M7.
Handles sending messages through various channels.
"""
import re
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional, Tuple, Any
from django.utils import timezone
from django.conf import settings as django_settings
from celery import shared_task

from .models import (
    MessageTemplate, MessageLog, Notification, ChannelConfig, Blacklist
)


class NotificationService:
    """Service for sending notifications through various channels."""

    def send(
        self,
        channel: str,
        recipients: List[str],
        template_code: str = None,
        subject: str = None,
        content: str = None,
        params: Dict = None,
        business_type: str = None,
        business_id: str = None
    ) -> List[int]:
        """
        Send message to recipients through specified channel.
        Returns list of message log IDs.
        """
        params = params or {}
        log_ids = []

        # Get template if specified
        template = None
        if template_code:
            try:
                template = MessageTemplate.objects.get(code=template_code, channel=channel, status='active')
                if not subject:
                    subject = template.subject
                if not content:
                    content = template.content
            except MessageTemplate.DoesNotExist:
                raise ValueError(f'模板不存在或未启用: {template_code}')

        if not content:
            raise ValueError('消息内容不能为空')

        # Render template variables
        rendered_subject = self._render_template(subject or '', params)
        rendered_content = self._render_template(content, params)

        # Filter blacklisted recipients
        recipients = self._filter_blacklist(channel, recipients)

        # Create message logs and send
        for recipient in recipients:
            log = MessageLog.objects.create(
                template=template,
                channel=channel,
                recipient=recipient,
                subject=rendered_subject,
                content=rendered_content,
                params=params,
                status='pending',
                business_type=business_type,
                business_id=business_id
            )
            log_ids.append(log.id)

            # Send asynchronously
            self.send_message_async(log.id)

        return log_ids

    def send_message_async(self, log_id: int):
        """Trigger async message sending."""
        send_message_task.delay(log_id)

    def send_internal_notification(
        self,
        user_id: int,
        title: str,
        content: str = None,
        notif_type: str = 'system',
        level: str = 'info',
        link_url: str = None,
        business_type: str = None,
        business_id: str = None
    ) -> Notification:
        """Create internal notification for a user."""
        return Notification.objects.create(
            user_id=user_id,
            title=title,
            content=content,
            type=notif_type,
            level=level,
            link_url=link_url,
            business_type=business_type,
            business_id=business_id
        )

    def send_batch_internal_notifications(
        self,
        user_ids: List[int],
        title: str,
        content: str = None,
        notif_type: str = 'system',
        level: str = 'info',
        link_url: str = None,
        business_type: str = None,
        business_id: str = None
    ) -> List[Notification]:
        """Create internal notifications for multiple users."""
        notifications = []
        for user_id in user_ids:
            notifications.append(Notification(
                user_id=user_id,
                title=title,
                content=content,
                type=notif_type,
                level=level,
                link_url=link_url,
                business_type=business_type,
                business_id=business_id
            ))
        return Notification.objects.bulk_create(notifications)

    def test_channel(self, channel: str, recipient: str, config: Dict) -> Tuple[bool, str]:
        """Test channel configuration by sending a test message."""
        try:
            if channel == 'email':
                return self._test_email(recipient, config)
            elif channel == 'sms':
                return self._test_sms(recipient, config)
            elif channel == 'dingtalk':
                return self._test_dingtalk(recipient, config)
            elif channel == 'feishu':
                return self._test_feishu(recipient, config)
            elif channel == 'wechat':
                return self._test_wechat(recipient, config)
            else:
                return False, f'不支持的渠道: {channel}'
        except Exception as e:
            return False, str(e)

    def _render_template(self, template: str, params: Dict) -> str:
        """Render template with parameters."""
        result = template
        for key, value in params.items():
            result = result.replace(f'${{{key}}}', str(value))
        return result

    def _filter_blacklist(self, channel: str, recipients: List[str]) -> List[str]:
        """Filter out blacklisted recipients."""
        if channel == 'email':
            bl_type = 'email'
        elif channel == 'sms':
            bl_type = 'phone'
        else:
            bl_type = 'user'

        blacklisted = set(
            Blacklist.objects.filter(type=bl_type, value__in=recipients)
            .values_list('value', flat=True)
        )
        return [r for r in recipients if r not in blacklisted]

    def _test_email(self, recipient: str, config: Dict) -> Tuple[bool, str]:
        """Test email configuration."""
        try:
            smtp_host = config.get('smtp_host')
            smtp_port = config.get('smtp_port', 587)
            smtp_user = config.get('smtp_user')
            smtp_password = config.get('smtp_password')
            use_tls = config.get('use_tls', True)

            msg = MIMEText('This is a test message from OPS notification system.')
            msg['Subject'] = 'OPS Notification Test'
            msg['From'] = smtp_user
            msg['To'] = recipient

            if use_tls:
                server = smtplib.SMTP(smtp_host, smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port)

            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            server.quit()
            return True, 'Email sent successfully'
        except Exception as e:
            return False, str(e)

    def _test_sms(self, recipient: str, config: Dict) -> Tuple[bool, str]:
        """Test SMS configuration."""
        provider = config.get('provider', 'aliyun')

        if provider == 'aliyun':
            # Aliyun SMS implementation would go here
            return True, 'SMS test skipped (placeholder)'
        elif provider == 'tencent':
            # Tencent SMS implementation would go here
            return True, 'SMS test skipped (placeholder)'
        else:
            return False, f'Unknown SMS provider: {provider}'

    def _test_dingtalk(self, recipient: str, config: Dict) -> Tuple[bool, str]:
        """Test DingTalk configuration."""
        webhook_url = config.get('webhook_url')
        if not webhook_url:
            return False, 'Missing webhook_url'

        try:
            response = requests.post(webhook_url, json={
                'msgtype': 'text',
                'text': {'content': 'OPS Notification Test'}
            }, timeout=10)
            result = response.json()
            if result.get('errcode') == 0:
                return True, 'DingTalk message sent'
            return False, result.get('errmsg', 'Unknown error')
        except Exception as e:
            return False, str(e)

    def _test_feishu(self, recipient: str, config: Dict) -> Tuple[bool, str]:
        """Test Feishu configuration."""
        webhook_url = config.get('webhook_url')
        if not webhook_url:
            return False, 'Missing webhook_url'

        try:
            response = requests.post(webhook_url, json={
                'msg_type': 'text',
                'content': {'text': 'OPS Notification Test'}
            }, timeout=10)
            result = response.json()
            if result.get('code') == 0:
                return True, 'Feishu message sent'
            return False, result.get('msg', 'Unknown error')
        except Exception as e:
            return False, str(e)

    def _test_wechat(self, recipient: str, config: Dict) -> Tuple[bool, str]:
        """Test WeChat Work configuration."""
        webhook_url = config.get('webhook_url')
        if not webhook_url:
            return False, 'Missing webhook_url'

        try:
            response = requests.post(webhook_url, json={
                'msgtype': 'text',
                'text': {'content': 'OPS Notification Test'}
            }, timeout=10)
            result = response.json()
            if result.get('errcode') == 0:
                return True, 'WeChat message sent'
            return False, result.get('errmsg', 'Unknown error')
        except Exception as e:
            return False, str(e)


@shared_task
def send_message_task(log_id: int):
    """Celery task to send message."""
    try:
        log = MessageLog.objects.get(pk=log_id)
    except MessageLog.DoesNotExist:
        return

    if log.status != 'pending':
        return

    try:
        config = ChannelConfig.objects.get(channel=log.channel, status='active')
    except ChannelConfig.DoesNotExist:
        log.status = 'failed'
        log.error_msg = f'Channel config not found: {log.channel}'
        log.save()
        return

    sender = MessageSender(config.config)

    try:
        success, external_id, error = sender.send(log.channel, log.recipient, log.subject, log.content)

        if success:
            log.status = 'sent'
            log.external_id = external_id
            log.sent_at = timezone.now()
        else:
            log.status = 'failed'
            log.error_msg = error

        log.save()
    except Exception as e:
        log.status = 'failed'
        log.error_msg = str(e)
        log.save()


class MessageSender:
    """Handles actual message sending through various channels."""

    def __init__(self, config: Dict):
        self.config = config

    def send(self, channel: str, recipient: str, subject: str, content: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Send message through specified channel.
        Returns (success, external_id, error_message).
        """
        if channel == 'email':
            return self._send_email(recipient, subject, content)
        elif channel == 'sms':
            return self._send_sms(recipient, content)
        elif channel == 'dingtalk':
            return self._send_dingtalk(recipient, content)
        elif channel == 'feishu':
            return self._send_feishu(recipient, content)
        elif channel == 'wechat':
            return self._send_wechat(recipient, content)
        elif channel == 'webhook':
            return self._send_webhook(recipient, subject, content)
        elif channel == 'internal':
            return True, None, None  # Internal notifications are handled separately
        else:
            return False, None, f'Unknown channel: {channel}'

    def _send_email(self, recipient: str, subject: str, content: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Send email."""
        try:
            smtp_host = self.config.get('smtp_host')
            smtp_port = self.config.get('smtp_port', 587)
            smtp_user = self.config.get('smtp_user')
            smtp_password = self.config.get('smtp_password')
            use_tls = self.config.get('use_tls', True)
            from_name = self.config.get('from_name', 'OPS System')

            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f'{from_name} <{smtp_user}>'
            msg['To'] = recipient

            # Add both plain text and HTML versions
            text_part = MIMEText(content, 'plain', 'utf-8')
            html_part = MIMEText(content, 'html', 'utf-8')
            msg.attach(text_part)
            msg.attach(html_part)

            if use_tls:
                server = smtplib.SMTP(smtp_host, smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port)

            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            server.quit()

            return True, None, None
        except Exception as e:
            return False, None, str(e)

    def _send_sms(self, recipient: str, content: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Send SMS."""
        provider = self.config.get('provider', 'aliyun')

        if provider == 'aliyun':
            return self._send_aliyun_sms(recipient, content)
        elif provider == 'tencent':
            return self._send_tencent_sms(recipient, content)
        else:
            return False, None, f'Unknown SMS provider: {provider}'

    def _send_aliyun_sms(self, recipient: str, content: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Send SMS via Aliyun."""
        # Placeholder implementation
        # Would use aliyun-python-sdk-dysmsapi in production
        return True, 'aliyun-msg-id', None

    def _send_tencent_sms(self, recipient: str, content: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Send SMS via Tencent Cloud."""
        # Placeholder implementation
        # Would use tencentcloud-sdk-python in production
        return True, 'tencent-msg-id', None

    def _send_dingtalk(self, recipient: str, content: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Send DingTalk message."""
        webhook_url = self.config.get('webhook_url')
        if not webhook_url:
            return False, None, 'Missing webhook_url'

        try:
            response = requests.post(webhook_url, json={
                'msgtype': 'text',
                'text': {'content': content}
            }, timeout=10)
            result = response.json()
            if result.get('errcode') == 0:
                return True, None, None
            return False, None, result.get('errmsg', 'Unknown error')
        except Exception as e:
            return False, None, str(e)

    def _send_feishu(self, recipient: str, content: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Send Feishu message."""
        webhook_url = self.config.get('webhook_url')
        if not webhook_url:
            return False, None, 'Missing webhook_url'

        try:
            response = requests.post(webhook_url, json={
                'msg_type': 'text',
                'content': {'text': content}
            }, timeout=10)
            result = response.json()
            if result.get('code') == 0:
                return True, result.get('data', {}).get('message_id'), None
            return False, None, result.get('msg', 'Unknown error')
        except Exception as e:
            return False, None, str(e)

    def _send_wechat(self, recipient: str, content: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Send WeChat Work message."""
        webhook_url = self.config.get('webhook_url')
        if not webhook_url:
            return False, None, 'Missing webhook_url'

        try:
            response = requests.post(webhook_url, json={
                'msgtype': 'text',
                'text': {'content': content}
            }, timeout=10)
            result = response.json()
            if result.get('errcode') == 0:
                return True, None, None
            return False, None, result.get('errmsg', 'Unknown error')
        except Exception as e:
            return False, None, str(e)

    def _send_webhook(self, url: str, subject: str, content: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Send webhook notification."""
        try:
            response = requests.post(url, json={
                'subject': subject,
                'content': content,
                'timestamp': timezone.now().isoformat()
            }, timeout=10)
            if response.status_code == 200:
                return True, None, None
            return False, None, f'HTTP {response.status_code}'
        except Exception as e:
            return False, None, str(e)
