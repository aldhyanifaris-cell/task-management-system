"""
Tests for Task Management System API
=====================================
Comprehensive tests for Tasks and Categories API endpoints.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

from tasks.models import Task, Category

User = get_user_model()


class BaseTestCase(APITestCase):
    """Base test case with common setup."""

    def setUp(self) -> None:
        """Set up test data."""
        self.client = APIClient()

        # Create test users
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='user1@test.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User One'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='user2@test.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User Two'
        )

        # Create test category
        self.category = Category.objects.create(
            name='Work',
            description='Work related tasks',
            color='#007bff',
            created_by=self.user1
        )

        # Create test task
        self.task = Task.objects.create(
            title='Test Task',
            description='This is a test task',
            status=Task.Status.TODO,
            priority=Task.Priority.MEDIUM,
            owner=self.user1,
            category=self.category
        )

    def authenticate(self, user=None) -> None:
        """Authenticate a user via JWT."""
        if user is None:
            user = self.user1
        self.client.force_authenticate(user=user)


class UserRegistrationTests(BaseTestCase):
    """Tests for user registration endpoint."""

    def test_user_can_register(self) -> None:
        """Test successful user registration."""
        url = reverse('accounts:register')
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertEqual(User.objects.filter(email='newuser@test.com').count(), 1)

    def test_registration_requires_matching_passwords(self) -> None:
        """Test that mismatched passwords fail validation."""
        url = reverse('accounts:register')
        data = {
            'username': 'newuser2',
            'email': 'newuser2@test.com',
            'password': 'StrongPass123!',
            'password_confirm': 'DifferentPass456!'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_requires_unique_email(self) -> None:
        """Test that duplicate email fails."""
        url = reverse('accounts:register')
        data = {
            'username': 'anotheruser',
            'email': 'user1@test.com',  # Already exists
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CategoryTests(BaseTestCase):
    """Tests for Category API endpoints."""

    def test_list_categories_unauthenticated(self) -> None:
        """Test that categories can be listed without auth (read-only)."""
        url = reverse('tasks:category-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_category_requires_auth(self) -> None:
        """Test that creating a category requires authentication."""
        url = reverse('tasks:category-list')
        data = {'name': 'Personal', 'color': '#ff0000'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_create_category(self) -> None:
        """Test that an authenticated user can create a category."""
        self.authenticate()
        url = reverse('tasks:category-list')
        data = {'name': 'Personal', 'description': 'Personal tasks', 'color': '#ff0000'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Personal')

    def test_can_retrieve_category_detail(self) -> None:
        """Test retrieving a single category."""
        url = reverse('tasks:category-detail', args=[self.category.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Work')

    def test_invalid_color_rejected(self) -> None:
        """Test that invalid hex color is rejected."""
        self.authenticate()
        url = reverse('tasks:category-list')
        data = {'name': 'Bad Category', 'color': 'red'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TaskTests(BaseTestCase):
    """Tests for Task API endpoints."""

    def test_list_tasks_requires_auth(self) -> None:
        """Test that listing tasks requires authentication."""
        url = reverse('tasks:task-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_can_list_their_tasks(self) -> None:
        """Test that authenticated user can list their tasks."""
        self.authenticate()
        url = reverse('tasks:task-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)  # Paginated response

    def test_user_can_create_task(self) -> None:
        """Test task creation."""
        self.authenticate()
        url = reverse('tasks:task-list')
        data = {
            'title': 'New Task',
            'description': 'Task description',
            'status': 'todo',
            'priority': 'high',
            'category_id': self.category.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_cannot_see_other_users_tasks(self) -> None:
        """Test that user2 cannot see user1 tasks."""
        self.authenticate(self.user2)
        url = reverse('tasks:task-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # user2 has no tasks, result should be empty
        self.assertEqual(response.data['count'], 0)

    def test_task_completion(self) -> None:
        """Test marking a task as complete."""
        self.authenticate()
        url = reverse('tasks:task-complete', args=[self.task.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.DONE)
        self.assertIsNotNone(self.task.completed_at)

    def test_task_stats_endpoint(self) -> None:
        """Test the task statistics endpoint."""
        self.authenticate()
        url = reverse('tasks:task-stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total', response.data)
        self.assertIn('by_status', response.data)
        self.assertIn('by_priority', response.data)

    def test_task_filter_by_status(self) -> None:
        """Test filtering tasks by status."""
        self.authenticate()
        url = reverse('tasks:task-list')
        response = self.client.get(url, {'status': 'todo'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for task in response.data['results']:
            self.assertEqual(task['status'], 'todo')

    def test_task_search(self) -> None:
        """Test searching tasks by title."""
        self.authenticate()
        url = reverse('tasks:task-list')
        response = self.client.get(url, {'search': 'Test Task'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(response.data['count'], 0)

    def test_overdue_endpoint(self) -> None:
        """Test the overdue tasks endpoint."""
        self.authenticate()
        # Create an overdue task
        Task.objects.create(
            title='Overdue Task',
            status=Task.Status.TODO,
            priority=Task.Priority.HIGH,
            owner=self.user1,
            due_date=timezone.now() - timedelta(days=1)
        )
        url = reverse('tasks:task-overdue')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)


class TaskCommentTests(BaseTestCase):
    """Tests for task comment functionality."""

    def test_add_comment_to_task(self) -> None:
        """Test adding a comment to a task."""
        self.authenticate()
        url = reverse('tasks:task-add-comment', args=[self.task.id])
        data = {'content': 'This is a test comment', 'task': self.task.id}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], 'This is a test comment')

    def test_list_task_comments(self) -> None:
        """Test listing comments for a task."""
        self.authenticate()
        url = reverse('tasks:task-comments', args=[self.task.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
