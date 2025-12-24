"""
Dashboard URL Configuration
"""

from django.urls import path
from ..views.dashboard_views import dashboard_stats

urlpatterns = [
    path('stats/', dashboard_stats, name='dashboard_stats'),
]


