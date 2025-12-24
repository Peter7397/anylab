"""
Content URL Configuration

This module contains URL patterns for Content Management operations.
"""

from django.urls import path
from ..views.content_views import (
    filter_documents, get_filter_suggestions, save_filter_preset,
    load_filter_preset, list_filter_presets, get_document_metadata,
    update_document_metadata, get_filter_analytics
)

urlpatterns = [
    # Filtering endpoints
    path('filter/', filter_documents, name='content_filter'),
    path('filter/suggestions/', get_filter_suggestions, name='content_filter_suggestions'),
    path('filter/analytics/', get_filter_analytics, name='content_filter_analytics'),
    
    # Preset management endpoints
    path('presets/save/', save_filter_preset, name='content_presets_save'),
    path('presets/load/', load_filter_preset, name='content_presets_load'),
    path('presets/list/', list_filter_presets, name='content_presets_list'),
    
    # Metadata management endpoints
    path('metadata/<int:document_id>/', get_document_metadata, name='content_metadata_get'),
    path('metadata/<int:document_id>/update/', update_document_metadata, name='content_metadata_update'),
]
