"""
Document URL Configuration

This module contains URL patterns for Document Management operations.
"""

from django.urls import path
from ..views import (
    get_query_history, get_index_info, list_uploaded_files, get_performance_stats,
    get_search_analytics, documents, document_download, document_delete,
    document_search, pdf_view, pdf_download, pdf_delete, pdf_search,
    upload_document_enhanced, pdf_documents, upload_pdf_enhanced
)

urlpatterns = [
    # Document management endpoints
    path('', documents, name='documents_list'),
    path('upload/', upload_document_enhanced, name='documents_upload'),
    path('upload/enhanced/', upload_document_enhanced, name='documents_upload_enhanced'),
    path('<int:doc_id>/download/', document_download, name='documents_download'),
    path('<int:doc_id>/delete/', document_delete, name='documents_delete'),
    path('search/', document_search, name='documents_search'),
    
    # PDF management endpoints
    path('pdf/<int:file_id>/view/', pdf_view, name='documents_pdf_view'),
    path('pdfs/', pdf_documents, name='documents_pdfs'),
    path('pdfs/upload/', upload_pdf_enhanced, name='documents_pdfs_upload'),
    path('pdfs/<int:pdf_id>/download/', pdf_download, name='documents_pdfs_download'),
    path('pdfs/<int:pdf_id>/delete/', pdf_delete, name='documents_pdfs_delete'),
    path('pdfs/search/', pdf_search, name='documents_pdfs_search'),
    
    # History and analytics endpoints
    path('history/', get_query_history, name='documents_history'),
    path('index/info/', get_index_info, name='documents_index_info'),
    path('files/', list_uploaded_files, name='documents_files'),
    path('performance/stats/', get_performance_stats, name='documents_performance_stats'),
    path('search/analytics/', get_search_analytics, name='documents_search_analytics'),
]
