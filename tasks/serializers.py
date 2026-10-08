"""
Tasks App Serializers
=====================
Serializers for Task, Category, and TaskComment models.
"""

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from accounts.serializers import UserPublicSerializer
from .models import Task, Category, TaskComment

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for Category model.
    Includes task count as a read-only field.
    """
    task_count = serializers.ReadOnlyField()
    created_by = UserPublicSerializer(read_only=True)

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'description', 'color', 'icon',
            'task_count', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class CategoryWriteSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating categories."""

    class Meta:
        model = Category
        fields = ['name', 'description', 'color', 'icon']

    def validate_color(self, value: str) -> str:
        """Validate hex color code format."""
        if not value.startswith('#') or len(value) not in [4, 7]:
            raise serializers.ValidationError(
                'Color must be a valid hex code (e.g. #fff or #ffffff).'
            )
        return value


class TaskCommentSerializer(serializers.ModelSerializer):
    """Serializer for task comments."""
    author = UserPublicSerializer(read_only=True)

    class Meta:
        model = TaskComment
        fields = ['id', 'task', 'author', 'content', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']


class TaskListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing tasks.
    Returns only essential fields for performance.
    """
    owner = UserPublicSerializer(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    is_overdue = serializers.ReadOnlyField()
    tags_list = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'status', 'status_display', 'priority', 'priority_display',
            'owner', 'category', 'category_name', 'due_date', 'is_overdue',
            'is_archived', 'tags', 'tags_list', 'created_at', 'updated_at'
        ]

    def get_tags_list(self, obj: Task) -> list:
        return obj.get_tags_list()


class TaskDetailSerializer(serializers.ModelSerializer):
    """
    Full serializer for task details.
    Includes all fields and nested relationships.
    """
    owner = UserPublicSerializer(read_only=True)
    assigned_to = UserPublicSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    comments = TaskCommentSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    is_overdue = serializers.ReadOnlyField()
    tags_list = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'status_display',
            'priority', 'priority_display', 'owner', 'assigned_to',
            'category', 'due_date', 'completed_at', 'is_archived',
            'tags', 'tags_list', 'is_overdue', 'comments', 'comment_count',
            'created_at', 'updated_at'
        ]

    def get_tags_list(self, obj: Task) -> list:
        return obj.get_tags_list()

    def get_comment_count(self, obj: Task) -> int:
        return obj.comments.count()


class TaskWriteSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating tasks.
    Handles write operations with proper validation.
    Uses integer IDs for foreign key writes (category, assigned_to).
    """
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        required=False,
        allow_null=True
    )
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='assigned_to',
        required=False,
        allow_null=True
    )

    class Meta:
        model = Task
        fields = [
            'title', 'description', 'status', 'priority',
            'category_id', 'assigned_to_id', 'due_date',
            'is_archived', 'tags'
        ]

    def validate_due_date(self, value):
        """Ensure due date is in the future for new tasks."""
        if value and self.instance is None:
            if value < timezone.now():
                raise serializers.ValidationError(
                    'Due date must be in the future.'
                )
        return value

    def validate_title(self, value: str) -> str:
        """Ensure title is not empty or whitespace."""
        if not value.strip():
            raise serializers.ValidationError('Title cannot be empty.')
        return value.strip()
