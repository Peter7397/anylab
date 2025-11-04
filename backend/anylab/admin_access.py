"""
Custom admin access control for Django Admin interface.

This module ensures that only staff and superusers can access the Django admin.
Django admin already has built-in protection, but we add explicit middleware
to provide better error messages and logging.
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def admin_user_test(user):
    """
    Test function to check if user has admin access.
    Only staff and superusers can access admin.
    """
    if not user.is_authenticated:
        return False
    return user.is_staff or user.is_superuser


def require_admin_access(view_func):
    """
    Decorator to require admin access (staff or superuser).
    This is in addition to Django's built-in admin protection.
    """
    decorated_view = user_passes_test(
        admin_user_test,
        login_url='/login/',
        redirect_field_name='next'
    )(view_func)
    return decorated_view

