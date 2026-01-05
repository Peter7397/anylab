"""
Debug URL Configuration

Debug endpoints for testing and troubleshooting upload functionality.
"""

from django.urls import path
from ..views.debug_views import debug_upload_info, debug_test_upload

urlpatterns = [
    path('upload/info/', debug_upload_info, name='debug_upload_info'),
    path('upload/test/', debug_test_upload, name='debug_test_upload'),
]

