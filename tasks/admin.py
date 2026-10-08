"""
Tasks App Admin Configuration
==============================
Custom Django admin interface for Task, Category, and TaskComment models.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Task, Category, TaskComment


class TaskCommentInline(admin.TabularInline):
    """Inline admin for task comments."""
    model = TaskComment
    extra = 0
    readonly_fields = ['author', 'created_at']
    fields = ['author', 'content', 'created_at']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin interface for Category model."""

    list_display = ['name', 'color_preview', 'task_count', 'created_by', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']

    @admin.display(description=_('Color'))
    def color_preview(self, obj: Category) -> str:
        """Show a color swatch in the admin list."""
        return format_html(
            '<span style="background-color: {}; padding: 3px 15px; '
            'border-radius: 3px; color: white;">{}</span>',
            obj.color,
            obj.color
        )


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """
    Admin interface for Task model.
    Shows important fields and supports filtering/searching.
    """

    list_display = [
        'title', 'status_badge', 'priority', 'owner',
        'category', 'due_date', 'is_archived', 'created_at'
    ]
    list_filter = [
        'status', 'priority', 'is_archived', 'category',
        'created_at', 'due_date'
    ]
    search_fields = ['title', 'description', 'tags', 'owner__email', 'owner__username']
    readonly_fields = ['created_at', 'updated_at', 'completed_at']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    inlines = [TaskCommentInline]

    fieldsets = (
        (_('Task Information'), {
            'fields': ('title', 'description', 'tags')
        }),
        (_('Status & Priority'), {
            'fields': ('status', 'priority', 'is_archived')
        }),
        (_('Assignments'), {
            'fields': ('owner', 'assigned_to', 'category')
        }),
        (_('Dates'), {
            'fields': ('due_date', 'completed_at', 'created_at', 'updated_at')
        }),
    )

    @admin.display(description=_('Status'))
    def status_badge(self, obj: Task) -> str:
        """Show status as a colored badge."""
        colors = {
            'todo': '#6c757d',
            'in_progress': '#007bff',
            'review': '#fd7e14',
            'done': '#28a745',
            'cancelled': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 4px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )

    def get_queryset(self, request):
        """Optimize queryset with related fields."""
        return super().get_queryset(request).select_related(
            'owner', 'category', 'assigned_to'
        )


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    """Admin interface for TaskComment model."""

    list_display = ['task', 'author', 'content_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content', 'author__username', 'task__title']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    @admin.display(description=_('Content'))
    def content_preview(self, obj: TaskComment) -> str:
        """Show truncated content in list view."""
        return obj.content[:80] + '...' if len(obj.content) > 80 else obj.content
