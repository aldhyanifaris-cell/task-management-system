"""
Accounts App Models
===================
Custom User model extending Django's AbstractUser.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom User model with additional fields.
    Extends Django's AbstractUser for flexibility.
    """

    email = models.EmailField(
        _('email address'),
        unique=True,
        help_text=_('Required. Enter a valid email address.')
    )
    bio = models.TextField(
        _('biography'),
        max_length=500,
        blank=True,
        help_text=_('Short biography or description.')
    )
    avatar = models.ImageField(
        _('avatar'),
        upload_to='avatars/',
        null=True,
        blank=True,
        help_text=_('Profile picture.')
    )
    is_verified = models.BooleanField(
        _('verified'),
        default=False,
        help_text=_('Whether the user email is verified.')
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.get_full_name()} <{self.email}>"

    def get_full_name(self) -> str:
        """Return user full name or username as fallback."""
        full_name = super().get_full_name()
        return full_name if full_name.strip() else self.username

    @property
    def task_count(self) -> int:
        """Return total number of tasks for this user."""
        return self.tasks.count()
