"""
Authentication tests for M1.
"""
import pytest
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from .models import User, Department, Role, Permission, UserRole


class AuthenticationTests(APITestCase):
    """Test authentication endpoints."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!',
            email='test@example.com',
            real_name='Test User'
        )
        self.admin = User.objects.create_superuser(
            username='admin',
            password='AdminPass123!',
            email='admin@example.com',
            real_name='Admin User'
        )
        self.client = APIClient()

    def test_login_success(self):
        """Test successful login."""
        url = reverse('login')
        data = {
            'username': 'testuser',
            'password': 'TestPass123!'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)

    def test_login_invalid_password(self):
        """Test login with invalid password."""
        url = reverse('login')
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_nonexistent_user(self):
        """Test login with non-existent user."""
        url = reverse('login')
        data = {
            'username': 'nonexistent',
            'password': 'TestPass123!'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout(self):
        """Test logout."""
        self.client.force_authenticate(user=self.user)
        url = reverse('logout')
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_profile_get(self):
        """Test getting user profile."""
        self.client.force_authenticate(user=self.user)
        url = reverse('profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')

    def test_profile_update(self):
        """Test updating user profile."""
        self.client.force_authenticate(user=self.user)
        url = reverse('profile')
        data = {'phone': '13800138000'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_password_change(self):
        """Test changing password."""
        self.client.force_authenticate(user=self.user)
        url = reverse('password_change')
        data = {
            'old_password': 'TestPass123!',
            'new_password': 'NewTestPass456!'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class UserManagementTests(APITestCase):
    """Test user management endpoints."""

    def setUp(self):
        """Set up test data."""
        self.admin = User.objects.create_superuser(
            username='admin',
            password='AdminPass123!',
            email='admin@example.com',
            real_name='Admin User'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_user_list(self):
        """Test listing users."""
        url = reverse('user_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('total', response.data)

    def test_user_create(self):
        """Test creating a user."""
        url = reverse('user_list')
        data = {
            'username': 'newuser',
            'password': 'NewUserPass123!',
            'email': 'newuser@example.com',
            'real_name': 'New User'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_detail(self):
        """Test getting user detail."""
        user = User.objects.create_user(
            username='testuser2',
            password='TestPass123!',
            email='test2@example.com'
        )
        url = reverse('user_detail', args=[user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_update(self):
        """Test updating a user."""
        user = User.objects.create_user(
            username='testuser3',
            password='TestPass123!',
            email='test3@example.com'
        )
        url = reverse('user_detail', args=[user.id])
        data = {'real_name': 'Updated Name'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_status_toggle(self):
        """Test toggling user status."""
        user = User.objects.create_user(
            username='testuser4',
            password='TestPass123!',
            email='test4@example.com'
        )
        url = reverse('user_status', args=[user.id])
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_reset_password(self):
        """Test resetting user password."""
        user = User.objects.create_user(
            username='testuser5',
            password='TestPass123!',
            email='test5@example.com'
        )
        url = reverse('user_reset_password', args=[user.id])
        data = {'password': 'ResetPass123!'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class RolePermissionTests(APITestCase):
    """Test role and permission endpoints."""

    def setUp(self):
        """Set up test data."""
        self.admin = User.objects.create_superuser(
            username='admin',
            password='AdminPass123!',
            email='admin@example.com'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_role_list(self):
        """Test listing roles."""
        url = reverse('role_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_role_create(self):
        """Test creating a role."""
        url = reverse('role_list')
        data = {
            'name': 'Test Role',
            'code': 'test_role',
            'description': 'A test role'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_permission_list(self):
        """Test listing permissions."""
        url = reverse('permission_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class DepartmentTests(APITestCase):
    """Test department endpoints."""

    def setUp(self):
        """Set up test data."""
        self.admin = User.objects.create_superuser(
            username='admin',
            password='AdminPass123!',
            email='admin@example.com'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_department_list(self):
        """Test listing departments."""
        url = reverse('department_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_department_create(self):
        """Test creating a department."""
        url = reverse('department_list')
        data = {
            'name': 'Engineering',
            'code': 'eng'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_department_tree(self):
        """Test getting department tree."""
        url = reverse('department_tree')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
