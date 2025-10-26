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
    
    # Chat endpoint (import inside to avoid issues)
    path('chat/', include('ai_assistant.urls.rag_urls')),
]