"""
SSB URL Configuration

This module contains URL patterns for SSB (Service Support Bulletin) operations.
"""

from django.urls import path
from ..views.ssb_views import (
    scrape_ssb_database, scrape_openlab_help_portal, get_ssb_scraping_status,
    schedule_ssb_scraping, get_ssb_scraping_schedule, test_ssb_scraping
)

urlpatterns = [
    # Scraping endpoints
    path('scrape/database/', scrape_ssb_database, name='ssb_scrape_database'),
    path('scrape/help-portal/', scrape_openlab_help_portal, name='ssb_scrape_help_portal'),
    
    # Status and monitoring endpoints
    path('status/', get_ssb_scraping_status, name='ssb_status'),
    path('schedule/', schedule_ssb_scraping, name='ssb_schedule'),
    path('schedule/get/', get_ssb_scraping_schedule, name='ssb_schedule_get'),
    
    # Testing endpoints
    path('test/', test_ssb_scraping, name='ssb_test'),
]
