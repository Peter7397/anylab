"""
Dashboard URL Configuration
"""

from django.urls import path
from ..views.dashboard_views import dashboard_stats, dashboard_stats_global

urlpatterns = [
    path('stats/', dashboard_stats, name='dashboard_stats'),
    path('stats/global/', dashboard_stats_global, name='dashboard_stats_global'),
]


