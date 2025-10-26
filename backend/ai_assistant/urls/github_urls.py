"""
GitHub URL Configuration

This module contains URL patterns for GitHub Scanner operations.
"""

from django.urls import path
from ..views.github_views import (
    scan_github_repositories, scan_repository_files, get_github_scanning_status,
    schedule_github_scanning, get_github_scanning_schedule, test_github_scanning,
    get_github_analytics
)

urlpatterns = [
    # Scanning endpoints
    path('scan/repositories/', scan_github_repositories, name='github_scan_repositories'),
    path('scan/files/', scan_repository_files, name='github_scan_files'),
    
    # Status and monitoring endpoints
    path('status/', get_github_scanning_status, name='github_status'),
    path('schedule/', schedule_github_scanning, name='github_schedule'),
    path('schedule/get/', get_github_scanning_schedule, name='github_schedule_get'),
    
    # Testing endpoints
    path('test/', test_github_scanning, name='github_test'),
    
    # Analytics endpoints
    path('analytics/', get_github_analytics, name='github_analytics'),
]
