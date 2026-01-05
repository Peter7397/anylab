"""
Metrics Dashboard URL Configuration
"""

from django.urls import path
from ai_assistant.views.metrics_dashboard_views import (
    get_processing_metrics,
    get_processing_timeline,
    get_error_summary,
)

urlpatterns = [
    path('processing/', get_processing_metrics, name='metrics-processing'),
    path('processing/timeline/', get_processing_timeline, name='metrics-timeline'),
    path('errors/', get_error_summary, name='metrics-errors'),
]

