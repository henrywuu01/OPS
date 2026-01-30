"""
Configuration tests for M4.
"""
import pytest
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from apps.auth.models import User
from .models import MetaTable, SystemConfig, ConfigApproval


class MetaTableTests(APITestCase):
    """Test meta table endpoints."""

    def setUp(self):
        """Set up test data."""
        self.admin = User.objects.create_superuser(
            username='admin',
            password='AdminPass123!',
            email='admin@example.com'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

        self.meta_table = MetaTable.objects.create(
            name='products',
            display_name='产品配置',
            description='产品配置表',
            field_config=[
                {'name': 'name', 'type': 'string', 'label': '产品名称', 'required': True},
                {'name': 'price', 'type': 'decimal', 'label': '价格', 'required': True},
                {'name': 'status', 'type': 'select', 'label': '状态', 'choices': [
                    {'value': 'active', 'label': '启用'},
                    {'value': 'inactive', 'label': '停用'}
                ]}
            ],
            status='active'
        )

    def test_meta_table_list(self):
        """Test listing meta tables."""
        url = reverse('meta_table_list_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_meta_table_create(self):
        """Test creating a meta table."""
        url = reverse('meta_table_list_create')
        data = {
            'name': 'categories',
            'display_name': '分类配置',
            'field_config': [
                {'name': 'name', 'type': 'string', 'label': '分类名称', 'required': True}
            ]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_meta_table_detail(self):
        """Test getting meta table detail."""
        url = reverse('meta_table_detail', args=[self.meta_table.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'products')


class SystemConfigTests(APITestCase):
    """Test system config endpoints."""

    def setUp(self):
        """Set up test data."""
        self.admin = User.objects.create_superuser(
            username='admin',
            password='AdminPass123!',
            email='admin@example.com'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

        self.config = SystemConfig.objects.create(
            key='site_name',
            value='OPS System',
            category='system',
            description='网站名称'
        )

    def test_system_config_list(self):
        """Test listing system configs."""
        url = reverse('system_config_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_system_config_detail(self):
        """Test getting system config detail."""
        url = reverse('system_config_detail', args=['site_name'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['key'], 'site_name')

    def test_system_config_update(self):
        """Test updating system config."""
        url = reverse('system_config_detail', args=['site_name'])
        data = {'value': 'New Site Name'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.config.refresh_from_db()
        self.assertEqual(self.config.value, 'New Site Name')


class ConfigApprovalTests(APITestCase):
    """Test config approval endpoints."""

    def setUp(self):
        """Set up test data."""
        self.admin = User.objects.create_superuser(
            username='admin',
            password='AdminPass123!',
            email='admin@example.com'
        )
        self.user = User.objects.create_user(
            username='user',
            password='UserPass123!',
            email='user@example.com'
        )
        self.client = APIClient()

        self.meta_table = MetaTable.objects.create(
            name='test_table',
            display_name='测试配置',
            field_config=[
                {'name': 'name', 'type': 'string', 'required': True}
            ],
            need_audit=True,
            status='active'
        )

        self.approval = ConfigApproval.objects.create(
            table_name='test_table',
            action='insert',
            new_data={'name': 'Test Item'},
            applicant=self.user,
            status='pending'
        )

    def test_approval_list(self):
        """Test listing approvals."""
        self.client.force_authenticate(user=self.admin)
        url = reverse('config_approval_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_approval_detail(self):
        """Test getting approval detail."""
        self.client.force_authenticate(user=self.admin)
        url = reverse('config_approval_detail', args=[self.approval.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_approval_approve(self):
        """Test approving a request."""
        self.client.force_authenticate(user=self.admin)
        url = reverse('config_approval_approve', args=[self.approval.id])
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.approval.refresh_from_db()
        self.assertEqual(self.approval.status, 'approved')

    def test_approval_reject(self):
        """Test rejecting a request."""
        self.client.force_authenticate(user=self.admin)
        approval2 = ConfigApproval.objects.create(
            table_name='test_table',
            action='insert',
            new_data={'name': 'Another Item'},
            applicant=self.user,
            status='pending'
        )
        url = reverse('config_approval_reject', args=[approval2.id])
        response = self.client.post(url, {'remark': 'Not approved'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        approval2.refresh_from_db()
        self.assertEqual(approval2.status, 'rejected')
