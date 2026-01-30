"""
Scheduler tests for M2.
"""
import pytest
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from apps.auth.models import User
from .models import Job, JobFlow, JobLog


class JobTests(APITestCase):
    """Test job management endpoints."""

    def setUp(self):
        """Set up test data."""
        self.admin = User.objects.create_superuser(
            username='admin',
            password='AdminPass123!',
            email='admin@example.com'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

        self.job = Job.objects.create(
            name='Test HTTP Job',
            description='A test HTTP job',
            job_type='http',
            cron_expr='0 * * * *',
            config={'url': 'https://httpbin.org/get', 'method': 'GET'},
            status='enabled'
        )

    def test_job_list(self):
        """Test listing jobs."""
        url = reverse('job_list_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(response.data['total'], 1)

    def test_job_create(self):
        """Test creating a job."""
        url = reverse('job_list_create')
        data = {
            'name': 'New Shell Job',
            'description': 'A new shell job',
            'job_type': 'shell',
            'cron_expr': '*/5 * * * *',
            'config': {'script': 'echo hello'},
            'retry_count': 3,
            'timeout': 60
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Job.objects.count(), 2)

    def test_job_detail(self):
        """Test getting job detail."""
        url = reverse('job_detail', args=[self.job.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test HTTP Job')

    def test_job_update(self):
        """Test updating a job."""
        url = reverse('job_detail', args=[self.job.id])
        data = {'name': 'Updated Job Name'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.job.refresh_from_db()
        self.assertEqual(self.job.name, 'Updated Job Name')

    def test_job_delete(self):
        """Test deleting a job."""
        url = reverse('job_detail', args=[self.job.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Job.objects.count(), 0)

    def test_job_pause(self):
        """Test pausing a job."""
        url = reverse('job_pause', args=[self.job.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, 'disabled')

    def test_job_resume(self):
        """Test resuming a job."""
        self.job.status = 'disabled'
        self.job.save()
        url = reverse('job_resume', args=[self.job.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, 'enabled')

    def test_job_trigger(self):
        """Test manually triggering a job."""
        url = reverse('job_trigger', args=[self.job.id])
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('task_id', response.data)

    def test_job_statistics(self):
        """Test getting job statistics."""
        url = reverse('job_statistics')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_jobs', response.data)
        self.assertEqual(response.data['total_jobs'], 1)


class JobFlowTests(APITestCase):
    """Test job flow endpoints."""

    def setUp(self):
        """Set up test data."""
        self.admin = User.objects.create_superuser(
            username='admin',
            password='AdminPass123!',
            email='admin@example.com'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

        self.job = Job.objects.create(
            name='Test Job',
            job_type='shell',
            config={'script': 'echo hello'}
        )

        self.flow = JobFlow.objects.create(
            name='Test Flow',
            description='A test flow',
            dag_config={
                'nodes': [{'id': 'node1', 'job_id': self.job.id}],
                'edges': []
            },
            status='enabled'
        )

    def test_flow_list(self):
        """Test listing flows."""
        url = reverse('flow_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_flow_create(self):
        """Test creating a flow."""
        url = reverse('flow_list')
        data = {
            'name': 'New Flow',
            'description': 'A new flow',
            'dag_config': {
                'nodes': [{'id': 'node1', 'job_id': self.job.id}],
                'edges': []
            }
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_flow_detail(self):
        """Test getting flow detail."""
        url = reverse('flow_detail', args=[self.flow.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Flow')

    def test_flow_trigger(self):
        """Test triggering a flow."""
        url = reverse('flow_trigger', args=[self.flow.id])
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('task_id', response.data)


class JobLogTests(APITestCase):
    """Test job log endpoints."""

    def setUp(self):
        """Set up test data."""
        from django.utils import timezone

        self.admin = User.objects.create_superuser(
            username='admin',
            password='AdminPass123!',
            email='admin@example.com'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

        self.job = Job.objects.create(
            name='Test Job',
            job_type='shell',
            config={'script': 'echo hello'}
        )

        self.log = JobLog.objects.create(
            job=self.job,
            trace_id='test-trace-id-123',
            trigger_type='manual',
            trigger_user=self.admin,
            status='success',
            start_time=timezone.now(),
            end_time=timezone.now(),
            duration=1000,
            result='hello'
        )

    def test_job_logs_list(self):
        """Test listing job logs."""
        url = reverse('job_logs', args=[self.job.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(response.data['total'], 1)

    def test_job_log_detail(self):
        """Test getting job log detail."""
        url = reverse('job_log_detail', args=[self.job.id, self.log.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['trace_id'], 'test-trace-id-123')
