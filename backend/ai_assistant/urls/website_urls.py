"""
Website Management URL Configuration
"""

from django.urls import path
from ..views import website_views

urlpatterns = [
    # Website management endpoints
    path('', website_views.list_websites, name='website-list'),
    path('add/', website_views.add_website, name='website-add'),
    path('statistics/', website_views.get_website_statistics, name='website-statistics'),
    
    # Individual website operations
    path('<int:website_id>/', website_views.get_website_status, name='website-detail'),
    path('<int:website_id>/status/', website_views.get_website_status, name='website-status'),
    path('<int:website_id>/refresh/', website_views.refresh_website, name='website-refresh'),
    path('<int:website_id>/retry/', website_views.retry_website_processing, name='website-retry'),
    path('<int:website_id>/settings/', website_views.update_website_settings, name='website-settings'),
    path('<int:website_id>/delete/', website_views.delete_website, name='website-delete'),
]
