"""
Forum URL Configuration

This module contains URL patterns for Forum Integration operations.
"""

from django.urls import path
from ..views.forum_views import (
    scrape_forum_posts, get_forum_scraping_status, schedule_forum_scraping,
    get_forum_scraping_schedule, test_forum_scraping, get_community_analytics
)

urlpatterns = [
    # Scraping endpoints
    path('scrape/posts/', scrape_forum_posts, name='forum_scrape_posts'),
    
    # Status and monitoring endpoints
    path('status/', get_forum_scraping_status, name='forum_status'),
    path('schedule/', schedule_forum_scraping, name='forum_schedule'),
    path('schedule/get/', get_forum_scraping_schedule, name='forum_schedule_get'),
    
    # Testing endpoints
    path('test/', test_forum_scraping, name='forum_test'),
    
    # Analytics endpoints
    path('analytics/', get_community_analytics, name='forum_analytics'),
]
