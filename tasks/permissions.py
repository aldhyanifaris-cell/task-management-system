"""
Tasks App Permissions
=====================
Custom DRF permissions for Task and Category access control.
"""

from rest_framework import permissions
from rest_framework.request import Request


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Allow read access to any user, but write access only to the object owner.
    Assumes the model has a `created_by` field.
    """

    def has_object_permission(self, request: Request, view, obj) -> bool:
        # Read permissions for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions only to the owner
        return obj.created_by == request.user


class IsTaskOwner(permissions.BasePermission):
    """
    Allow full access only to the task owner.
    Staff users can access all tasks.
    """

    def has_object_permission(self, request: Request, view, obj) -> bool:
        # Staff can access everything
        if request.user.is_staff:
            return True
        # Only task owner can modify
        return obj.owner == request.user
