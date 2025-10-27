"""
AI Assistant URL Configuration

This module provides organized URL patterns for the AI Assistant application.
"""

from django.urls import path, include

# Re-export from urls.py to match Django's import behavior
urlpatterns = [
    # RAG endpoints
    path('rag/', include('ai_assistant.urls.rag_urls')),
    
    # Document Management endpoints
    path('documents/', include('ai_assistant.urls.document_urls')),
    
    # Content Management endpoints
    path('content/', include('ai_assistant.urls.content_urls')),
    
    # Chat endpoint (import inside to avoid issues)
    path('chat/', include('ai_assistant.urls.rag_urls')),
    
    # Scraper endpoints
    path('ssb/', include('ai_assistant.urls.ssb_urls')),
    path('github/', include('ai_assistant.urls.github_urls')),
    path('forum/', include('ai_assistant.urls.forum_urls')),
    path('html/', include('ai_assistant.urls.html_urls')),
    
    # Troubleshooting AI endpoints
    path('troubleshoot/', include('ai_assistant.urls.troubleshooting_urls')),
    
    # Product endpoints
    path('products/', include('ai_assistant.urls.product_urls')),
]

# Optional endpoints (may fail if dependencies not installed)
try:
    from . import document_processing_urls
    urlpatterns.append(path('process/', include('ai_assistant.urls.document_processing_urls')))
except ImportError as e:
    print(f"Warning: Document processing URLs not available: {e}")

try:
    from . import analytics_urls
    urlpatterns.append(path('analytics/', include('ai_assistant.urls.analytics_urls')))
except ImportError as e:
    print(f"Warning: Analytics URLs not available: {e}")
