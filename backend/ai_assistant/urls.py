"""
AI Assistant URL Configuration

This module provides organized URL patterns for the AI Assistant application.
"""

from django.urls import path, include

urlpatterns = [
    # RAG endpoints
    path('rag/', include('ai_assistant.urls.rag_urls')),
    
    # Document Management endpoints
    path('documents/', include('ai_assistant.urls.document_urls')),
    
    # Content Management endpoints
    path('content/', include('ai_assistant.urls.content_urls')),
    
    # Chat endpoint
    path('chat/', include('ai_assistant.urls.rag_urls')),
    
    # Scraper endpoints
    path('ssb/', include('ai_assistant.urls.ssb_urls')),
    path('github/', include('ai_assistant.urls.github_urls')),
    path('forum/', include('ai_assistant.urls.forum_urls')),
    path('html/', include('ai_assistant.urls.html_urls')),
]