"""
Tasks App Filters
=================
Custom django-filter FilterSets for the Task model.
"""

import django_filters
from .models import Task


class TaskFilter(django_filters.FilterSet):
    """
    FilterSet for Task model with multiple filter options.

    Supported query params:
      - status           : exact match (todo, in_progress, review, done, cancelled)
      - priority         : exact match (low, medium, high, urgent)
      - category         : category ID
      - is_archived      : boolean
      - due_date_before  : tasks due before this date
      - due_date_after   : tasks due after this date
      - created_before   : tasks created before this date
      - created_after    : tasks created after this date
      - has_due_date     : boolean - filter tasks with/without due date
    """

    status = django_filters.ChoiceFilter(choices=Task.Status.choices)
    priority = django_filters.ChoiceFilter(choices=Task.Priority.choices)
    category = django_filters.NumberFilter(field_name='category__id')
    category_name = django_filters.CharFilter(field_name='category__name', lookup_expr='icontains')
    is_archived = django_filters.BooleanFilter()
    due_date_before = django_filters.DateTimeFilter(field_name='due_date', lookup_expr='lte')
    due_date_after = django_filters.DateTimeFilter(field_name='due_date', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    has_due_date = django_filters.BooleanFilter(field_name='due_date', lookup_expr='isnull', exclude=True)
    tags = django_filters.CharFilter(field_name='tags', lookup_expr='icontains')

    class Meta:
        model = Task
        fields = [
            'status', 'priority', 'category', 'category_name',
            'is_archived', 'due_date_before', 'due_date_after',
            'created_before', 'created_after', 'has_due_date', 'tags'
        ]
