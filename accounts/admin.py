"""
Accounts App Admin Configuration
=================================
Custom admin interface for User model.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom admin interface for the User model.
    Extends Django's built-in UserAdmin with additional fields.
    """

    # Fields to display in the list view
    list_display = [
        'email', 'username', 'first_name', 'last_name',
        'is_verified', 'is_staff', 'is_active', 'created_at'
    ]
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'is_verified', 'created_at']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'last_login', 'date_joined']

    # Fieldsets for the detail view
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        (_('Personal Info'), {
            'fields': ('first_name', 'last_name', 'bio', 'avatar')
        }),
        (_('Status'), {
            'fields': ('is_verified', 'is_active', 'is_staff', 'is_superuser')
        }),
        (_('Permissions'), {
            'fields': ('groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')
        }),
    )

    # Fieldsets for the add user form
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'username', 'first_name', 'last_name',
                'password1', 'password2', 'is_staff', 'is_active'
            ),
        }),
    )
