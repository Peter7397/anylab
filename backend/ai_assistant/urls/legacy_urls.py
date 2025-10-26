"""
Legacy URL Configuration

This module contains URL patterns for Legacy endpoints (backward compatibility).
"""

from django.urls import path
from ..views.legacy_views import pdf_documents, web_links, knowledge_share

urlpatterns = [
    # Legacy endpoints for backward compatibility
    path('pdf/', pdf_documents, name='legacy_pdf'),
    path('weblinks/', web_links, name='legacy_weblinks'),
    path('knowledge-share/', knowledge_share, name='legacy_knowledge_share'),
]
