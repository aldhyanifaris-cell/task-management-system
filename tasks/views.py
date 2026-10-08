"""
Tasks App Views
===============
ViewSets for Task and Category with filtering, search, and permissions.
"""

from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from .filters import TaskFilter
from .models import Task, Category, TaskComment
from .permissions import IsOwnerOrReadOnly, IsTaskOwner
from .serializers import (
    TaskListSerializer,
    TaskDetailSerializer,
    TaskWriteSerializer,
    CategorySerializer,
    CategoryWriteSerializer,
    TaskCommentSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Task Categories.

    - list:   GET  /api/v1/categories/
    - create: POST /api/v1/categories/
    - retrieve: GET /api/v1/categories/{id}/
    - update: PUT  /api/v1/categories/{id}/
    - partial_update: PATCH /api/v1/categories/{id}/
    - destroy: DELETE /api/v1/categories/{id}/
    """
    queryset = Category.objects.all().select_related('created_by')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CategoryWriteSerializer
        return CategorySerializer

    def perform_create(self, serializer) -> None:
        """Auto-assign the current user as creator."""
        serializer.save(created_by=self.request.user)


class TaskViewSet(viewsets.ModelViewSet):
    """
    Full CRUD + extra actions for Tasks.

    Extra actions:
    - POST /api/v1/tasks/{id}/complete/     - Mark as done
    - POST /api/v1/tasks/{id}/reopen/      - Reopen a closed task
    - POST /api/v1/tasks/{id}/archive/     - Archive a task
    - GET  /api/v1/tasks/{id}/comments/    - List comments
    - POST /api/v1/tasks/{id}/add-comment/ - Add a comment
    - GET  /api/v1/tasks/my-tasks/         - List current user tasks
    - GET  /api/v1/tasks/overdue/          - List overdue tasks
    - GET  /api/v1/tasks/stats/            - Task statistics
    """
    permission_classes = [permissions.IsAuthenticated, IsTaskOwner]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TaskFilter
    search_fields = ['title', 'description', 'tags']
    ordering_fields = ['created_at', 'updated_at', 'due_date', 'priority', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        """Return tasks owned by or assigned to the current user."""
        user = self.request.user
        return (
            Task.objects.filter(owner=user)
            .select_related('owner', 'category', 'assigned_to')
            .prefetch_related('comments')
        )

    def get_serializer_class(self):
        """Use different serializers for list vs detail vs write."""
        if self.action == 'list':
            return TaskListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return TaskWriteSerializer
        return TaskDetailSerializer

    def perform_create(self, serializer) -> None:
        """Auto-assign the current user as owner."""
        serializer.save(owner=self.request.user)

    # ── Extra Actions ────────────────────────────────────────────────

    @action(detail=True, methods=['post'])
    def complete(self, request: Request, pk=None) -> Response:
        """Mark a task as completed."""
        task = self.get_object()
        task.status = Task.Status.DONE
        task.completed_at = timezone.now()
        task.save(update_fields=['status', 'completed_at', 'updated_at'])
        return Response(
            {'message': f'Task "{task.title}" marked as completed.'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def reopen(self, request: Request, pk=None) -> Response:
        """Reopen a completed or cancelled task."""
        task = self.get_object()
        task.status = Task.Status.TODO
        task.completed_at = None
        task.save(update_fields=['status', 'completed_at', 'updated_at'])
        return Response(
            {'message': f'Task "{task.title}" reopened.'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def archive(self, request: Request, pk=None) -> Response:
        """Toggle archive status for a task."""
        task = self.get_object()
        task.is_archived = not task.is_archived
        task.save(update_fields=['is_archived', 'updated_at'])
        action_word = 'archived' if task.is_archived else 'unarchived'
        return Response(
            {'message': f'Task "{task.title}" {action_word}.'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get'])
    def comments(self, request: Request, pk=None) -> Response:
        """List all comments for a specific task."""
        task = self.get_object()
        comments = task.comments.select_related('author').order_by('created_at')
        serializer = TaskCommentSerializer(comments, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='add-comment')
    def add_comment(self, request: Request, pk=None) -> Response:
        """Add a comment to a task."""
        task = self.get_object()
        serializer = TaskCommentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(task=task, author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='my-tasks')
    def my_tasks(self, request: Request) -> Response:
        """List only the current user's tasks."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = TaskListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = TaskListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def overdue(self, request: Request) -> Response:
        """List all overdue tasks (past due date but not done/cancelled)."""
        now = timezone.now()
        queryset = self.get_queryset().filter(
            due_date__lt=now,
            status__in=[Task.Status.TODO, Task.Status.IN_PROGRESS, Task.Status.REVIEW],
            is_archived=False
        )
        serializer = TaskListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request: Request) -> Response:
        """Return task statistics for the current user."""
        queryset = self.get_queryset()
        now = timezone.now()

        stats_data = {
            'total': queryset.count(),
            'by_status': {
                status_key: queryset.filter(status=status_key).count()
                for status_key, _ in Task.Status.choices
            },
            'by_priority': {
                priority_key: queryset.filter(priority=priority_key).count()
                for priority_key, _ in Task.Priority.choices
            },
            'overdue': queryset.filter(
                due_date__lt=now,
                status__in=[Task.Status.TODO, Task.Status.IN_PROGRESS]
            ).count(),
            'completed_today': queryset.filter(
                completed_at__date=now.date()
            ).count(),
            'archived': queryset.filter(is_archived=True).count(),
        }
        return Response(stats_data)
