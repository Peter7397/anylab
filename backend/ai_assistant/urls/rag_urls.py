"""
RAG URL Configuration

This module contains URL patterns for RAG (Retrieval-Augmented Generation) operations.
"""

from django.urls import path
from ..views.rag_views import (
    chat_with_ollama, rag_search, advanced_rag_search, 
    comprehensive_rag_search, vector_search, upload_pdf_enhanced, 
    upload_document_enhanced
)

urlpatterns = [
    # Chat endpoints (accessible from both /api/ai/rag/ and /api/ai/chat/)
    path('', chat_with_ollama, name='rag_chat'),  # Match root when included
    path('ollama/', chat_with_ollama, name='chat_ollama'),  # /api/ai/chat/ollama/ or /api/ai/rag/ollama/
    
    # Search endpoints
    path('search/', rag_search, name='rag_search'),
    path('search/advanced/', advanced_rag_search, name='rag_search_advanced'),
    path('search/comprehensive/', comprehensive_rag_search, name='rag_search_comprehensive'),
    path('search/vector/', vector_search, name='rag_search_vector'),
    
    # Upload endpoints
    path('upload/pdf/', upload_pdf_enhanced, name='rag_upload_pdf'),
    path('upload/document/', upload_document_enhanced, name='rag_upload_document'),
]
