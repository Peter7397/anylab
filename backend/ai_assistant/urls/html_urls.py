"""
HTML URL Configuration

This module contains URL patterns for HTML Parser operations.
"""

from django.urls import path
from ..views.html_views import (
    parse_html_url, parse_html_text, get_html_parsing_status,
    schedule_html_parsing, get_html_parsing_schedule, test_html_parsing,
    get_html_analytics
)

urlpatterns = [
    # Parsing endpoints
    path('parse/url/', parse_html_url, name='html_parse_url'),
    path('parse/text/', parse_html_text, name='html_parse_text'),
    
    # Status and monitoring endpoints
    path('status/', get_html_parsing_status, name='html_status'),
    path('schedule/', schedule_html_parsing, name='html_schedule'),
    path('schedule/get/', get_html_parsing_schedule, name='html_schedule_get'),
    
    # Testing endpoints
    path('test/', test_html_parsing, name='html_test'),
    
    # Analytics endpoints
    path('analytics/', get_html_analytics, name='html_analytics'),
]
