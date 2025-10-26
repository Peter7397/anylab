"""
Analytics URL Configuration

This module contains URL patterns for analytics operations
including user statistics, contribution analytics, and performance metrics.
"""

from django.urls import path
from ..views.analytics_views import (
    get_user_statistics,
    get_contribution_analytics,
    get_performance_analytics,
    get_document_analytics,
    get_user_behavior_stats
)

urlpatterns = [
    path('user/stats/', get_user_statistics, name='get_user_statistics'),
    path('user/contributions/', get_contribution_analytics, name='get_contribution_analytics'),
    path('performance/', get_performance_analytics, name='get_performance_analytics'),
    path('documents/', get_document_analytics, name='get_document_analytics'),
    path('user/behavior/', get_user_behavior_stats, name='get_user_behavior_stats'),
]

