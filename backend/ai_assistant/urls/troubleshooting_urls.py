"""
URL Configuration for Troubleshooting AI
"""
from django.urls import path
from ai_assistant.views.troubleshooting_views import analyze_logs

urlpatterns = [
    path('analyze/', analyze_logs, name='analyze_logs'),
]

