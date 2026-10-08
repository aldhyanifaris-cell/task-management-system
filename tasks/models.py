"""
Tasks App Models
================
Defines Task, Category, and TaskComment models with relationships.
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    """
    Category model for organizing tasks.
    Each category can have multiple tasks.
    """

    name = models.CharField(
        _('name'),
        max_length=100,
        unique=True,
        help_text=_('Unique category name.')
    )
    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Brief description of this category.')
    )
    color = models.CharField(
        _('color'),
        max_length=7,
        default='#007bff',
        help_text=_('Hex color code for this category (e.g. #007bff).')
    )
    icon = models.CharField(
        _('icon'),
        max_length=50,
        blank=True,
        help_text=_('Optional icon identifier (e.g. FontAwesome class).')
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='categories',
        verbose_name=_('created by')
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        ordering = ['name']

    def __str__(self) -> str:
        return self.name

    @property
    def task_count(self) -> int:
        """Return total number of tasks in this category."""
        return self.tasks.count()


class Task(models.Model):
    """
    Task model - core entity of the task management system.
    Supports status tracking, priorities, due dates, and categories.
    """

    class Status(models.TextChoices):
        TODO = 'todo', _('To Do')
        IN_PROGRESS = 'in_progress', _('In Progress')
        REVIEW = 'review', _('In Review')
        DONE = 'done', _('Done')
        CANCELLED = 'cancelled', _('Cancelled')

    class Priority(models.TextChoices):
        LOW = 'low', _('Low')
        MEDIUM = 'medium', _('Medium')
        HIGH = 'high', _('High')
        URGENT = 'urgent', _('Urgent')

    # Core fields
    title = models.CharField(
        _('title'),
        max_length=255,
        help_text=_('Brief, descriptive title for the task.')
    )
    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Detailed description of what needs to be done.')
    )
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=Status.choices,
        default=Status.TODO,
        db_index=True,
        help_text=_('Current status of the task.')
    )
    priority = models.CharField(
        _('priority'),
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        db_index=True,
        help_text=_('Task priority level.')
    )

    # Relationships
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name=_('owner'),
        help_text=_('User who owns this task.')
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks',
        verbose_name=_('category'),
        help_text=_('Category this task belongs to.')
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks',
        verbose_name=_('assigned to'),
        help_text=_('User assigned to complete this task.')
    )

    # Date fields
    due_date = models.DateTimeField(
        _('due date'),
        null=True,
        blank=True,
        db_index=True,
        help_text=_('Deadline for task completion.')
    )
    completed_at = models.DateTimeField(
        _('completed at'),
        null=True,
        blank=True,
        help_text=_('When the task was completed.')
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True,
        db_index=True
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True
    )

    # Additional fields
    is_archived = models.BooleanField(
        _('archived'),
        default=False,
        help_text=_('Whether this task is archived.')
    )
    tags = models.CharField(
        _('tags'),
        max_length=255,
        blank=True,
        help_text=_('Comma-separated tags for the task.')
    )

    class Meta:
        verbose_name = _('task')
        verbose_name_plural = _('tasks')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', 'status']),
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['due_date', 'status']),
        ]

    def __str__(self) -> str:
        return f"[{self.get_status_display()}] {self.title}"

    @property
    def is_overdue(self) -> bool:
        """Check if the task is past its due date."""
        from django.utils import timezone
        if self.due_date and self.status not in [self.Status.DONE, self.Status.CANCELLED]:
            return timezone.now() > self.due_date
        return False

    def get_tags_list(self) -> list:
        """Return tags as a list."""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []


class TaskComment(models.Model):
    """
    Comments on tasks for collaboration and notes.
    """

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_('task')
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='task_comments',
        verbose_name=_('author')
    )
    content = models.TextField(
        _('content'),
        help_text=_('Comment content.')
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('task comment')
        verbose_name_plural = _('task comments')
        ordering = ['created_at']

    def __str__(self) -> str:
        return f"Comment by {self.author.username} on {self.task.title}"
