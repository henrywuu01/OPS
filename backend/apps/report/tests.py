"""
Report tests for M3.
"""
import pytest
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from apps.auth.models import User
from .models import DataSource, Report, ReportSubscription, ReportFavorite


class DataSourceTests(APITestCase):
    """Test datasource endpoints."""

    def setUp(self):
        """Set up test data."""
        self.admin = User.objects.create_superuser(
            username='admin',
            password='AdminPass123!',
            email='admin@example.com'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

        self.datasource = DataSource.objects.create(
            name='Test MySQL',
            type='mysql',
            host='localhost',
            port=3306,
            database_name='test_db',
            username='root',
            status='active'
        )

    def test_datasource_list(self):
        """Test listing datasources."""
        url = reverse('datasource_list_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(response.data['total'], 1)

    def test_datasource_create(self):
        """Test creating a datasource."""
        url = reverse('datasource_list_create')
        data = {
            'name': 'New PostgreSQL',
            'type': 'postgresql',
            'host': 'localhost',
            'port': 5432,
            'database_name': 'new_db',
            'username': 'postgres'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_datasource_detail(self):
        """Test getting datasource detail."""
        url = reverse('datasource_detail', args=[self.datasource.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test MySQL')


class ReportTests(APITestCase):
    """Test report endpoints."""

    def setUp(self):
        """Set up test data."""
        self.admin = User.objects.create_superuser(
            username='admin',
            password='AdminPass123!',
            email='admin@example.com'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

        self.datasource = DataSource.objects.create(
            name='Test MySQL',
            type='mysql',
            host='localhost',
            port=3306,
            database_name='test_db',
            username='root'
        )

        self.report = Report.objects.create(
            name='Test Report',
            description='A test report',
            datasource=self.datasource,
            query_config={'sql': 'SELECT * FROM users'},
            display_type='table',
            status='draft'
        )

    def test_report_list(self):
        """Test listing reports."""
        url = reverse('report_list_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(response.data['total'], 1)

    def test_report_create(self):
        """Test creating a report."""
        url = reverse('report_list_create')
        data = {
            'name': 'New Report',
            'description': 'A new report',
            'datasource': self.datasource.id,
            'query_config': {'sql': 'SELECT * FROM orders'},
            'display_type': 'bar'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_report_detail(self):
        """Test getting report detail."""
        url = reverse('report_detail', args=[self.report.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Report')

    def test_report_update(self):
        """Test updating a report."""
        url = reverse('report_detail', args=[self.report.id])
        data = {'name': 'Updated Report Name'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.report.refresh_from_db()
        self.assertEqual(self.report.name, 'Updated Report Name')

    def test_report_delete(self):
        """Test deleting a report."""
        url = reverse('report_detail', args=[self.report.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Report.objects.count(), 0)

    def test_report_publish(self):
        """Test publishing a report."""
        url = reverse('report_publish', args=[self.report.id])
        response = self.client.post(url, {'action': 'publish'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, 'published')


class ReportFavoriteTests(APITestCase):
    """Test report favorite endpoints."""

    def setUp(self):
        """Set up test data."""
        self.admin = User.objects.create_superuser(
            username='admin',
            password='AdminPass123!',
            email='admin@example.com'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

        self.datasource = DataSource.objects.create(
            name='Test MySQL',
            type='mysql',
            host='localhost',
            port=3306,
            database_name='test_db'
        )

        self.report = Report.objects.create(
            name='Test Report',
            datasource=self.datasource,
            query_config={'sql': 'SELECT 1'}
        )

    def test_favorite_report(self):
        """Test favoriting a report."""
        url = reverse('report_favorite', args=[self.report.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            ReportFavorite.objects.filter(report=self.report, user=self.admin).exists()
        )

    def test_unfavorite_report(self):
        """Test unfavoriting a report."""
        ReportFavorite.objects.create(report=self.report, user=self.admin)
        url = reverse('report_favorite', args=[self.report.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(
            ReportFavorite.objects.filter(report=self.report, user=self.admin).exists()
        )

    def test_my_favorites(self):
        """Test getting favorite reports."""
        ReportFavorite.objects.create(report=self.report, user=self.admin)
        url = reverse('my_favorite_reports')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total'], 1)


class ReportSubscriptionTests(APITestCase):
    """Test report subscription endpoints."""

    def setUp(self):
        """Set up test data."""
        self.admin = User.objects.create_superuser(
            username='admin',
            password='AdminPass123!',
            email='admin@example.com'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

        self.datasource = DataSource.objects.create(
            name='Test MySQL',
            type='mysql',
            host='localhost',
            port=3306,
            database_name='test_db'
        )

        self.report = Report.objects.create(
            name='Test Report',
            datasource=self.datasource,
            query_config={'sql': 'SELECT 1'},
            status='published'
        )

    def test_subscription_create(self):
        """Test creating a subscription."""
        url = reverse('report_subscription_list_create', args=[self.report.id])
        data = {
            'schedule_type': 'daily',
            'schedule_config': {'hour': 9, 'minute': 0},
            'channel': 'email',
            'export_format': 'excel'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_subscription_list(self):
        """Test listing subscriptions."""
        ReportSubscription.objects.create(
            report=self.report,
            user=self.admin,
            schedule_type='daily',
            schedule_config={'hour': 9},
            channel='email'
        )
        url = reverse('report_subscription_list_create', args=[self.report.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
