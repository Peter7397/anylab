"""
AI Assistant URL Configuration

This module provides organized URL patterns for the AI Assistant application.
"""

from django.urls import path, include
from ai_assistant.views.processing_health import processing_health
from ai_assistant.views.rag_views import chat_with_ollama
from ai_assistant.views.chat_history_views import ChatHistoryListView, ChatMessageCreateView

urlpatterns = [
    # Unified Chat History endpoints (explicit paths to avoid include order issues)
    path('chat/history/', ChatHistoryListView.as_view(), name='chat-history-explicit'),
    path('chat/message/', ChatMessageCreateView.as_view(), name='chat-message-create-explicit'),

    # Explicit Ollama chat endpoint under /api/ai/chat/ollama/
    path('chat/ollama/', chat_with_ollama, name='chat_ollama'),
    # RAG endpoints
    path('rag/', include('ai_assistant.urls.rag_urls')),
    
    # Document Management endpoints
    path('documents/', include('ai_assistant.urls.document_urls')),
    
    # Content Management endpoints
    path('content/', include('ai_assistant.urls.content_urls')),
    
    # Chat endpoints (unified history/messages) - keep include as well
    path('chat/', include('ai_assistant.urls.chat_urls')),
    
    # Scraper endpoints
    path('ssb/', include('ai_assistant.urls.ssb_urls')),
    path('github/', include('ai_assistant.urls.github_urls')),
    path('forum/', include('ai_assistant.urls.forum_urls')),
    path('html/', include('ai_assistant.urls.html_urls')),
    
    # Document processing endpoints
    path('process/', include('ai_assistant.urls.document_processing_urls')),
    
    # Analytics endpoints
    path('analytics/', include('ai_assistant.urls.analytics_urls')),
    
    # Troubleshooting AI endpoints
    path('troubleshoot/', include('ai_assistant.urls.troubleshooting_urls')),
    
    # Product endpoints
    path('products/', include('ai_assistant.urls.product_urls')),
    
    # Help Portal endpoints
    path('help-portal/', include('ai_assistant.urls.help_portal_urls')),

    # Website Management endpoints
    path('websites/', include('ai_assistant.urls.website_urls')),

    # Dashboard endpoints
    path('dashboard/', include('ai_assistant.urls.dashboard_urls')),

    # Admin settings endpoints
    path('admin/', include('ai_assistant.urls.admin_settings_urls')),

    # Processing health/metrics
    path('processing/health/', processing_health, name='processing-health'),
]