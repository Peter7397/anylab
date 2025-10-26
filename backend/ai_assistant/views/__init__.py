"""
AI Assistant Views Module

This module provides a centralized import point for all AI Assistant views.
It maintains backward compatibility while organizing views into logical modules.
"""

# Import all views for backward compatibility
from .rag_views import *
from .ssb_views import *
from .forum_views import *
from .github_views import *
from .html_views import *
from .content_views import *
from .document_processing_views import *
from .analytics_views import *
from .legacy_views import *

# Export commonly used items
__all__ = [
    # RAG Views
    'chat_with_ollama',
    'comprehensive_rag_search',
    'vector_search',
    'upload_pdf_enhanced',
    'upload_document_enhanced',
    'documents',
    'document_download',
    'document_delete',
    'document_search',
    'pdf_view',
    'pdf_download',
    'pdf_delete',
    'pdf_search',
    
    # SSB Views
    'scrape_ssb_database',
    'scrape_openlab_help_portal',
    'get_ssb_scraping_status',
    'schedule_ssb_scraping',
    'get_ssb_scraping_schedule',
    'test_ssb_scraping',
    
    # Forum Views
    'scrape_forum_posts',
    'get_forum_scraping_status',
    'schedule_forum_scraping',
    'get_forum_scraping_schedule',
    'test_forum_scraping',
    'get_community_analytics',
    
    # GitHub Views
    'scan_github_repositories',
    'scan_repository_files',
    'get_github_scanning_status',
    'schedule_github_scanning',
    'get_github_scanning_schedule',
    'test_github_scanning',
    'get_github_analytics',
    
    # HTML Views
    'parse_html_url',
    'parse_html_text',
    'get_html_parsing_status',
    'schedule_html_parsing',
    'get_html_parsing_schedule',
    'test_html_parsing',
    'get_html_analytics',
    
    # Content Views
    'filter_documents',
    'get_filter_suggestions',
    'save_filter_preset',
    'load_filter_preset',
    'list_filter_presets',
    'get_document_metadata',
    'update_document_metadata',
    'get_filter_analytics',
    
    # Legacy Views
    'pdf_documents',
    'web_links',
    'knowledge_share',
    'get_query_history',
    'get_index_info',
    'list_uploaded_files',
    'get_performance_stats',
    'get_search_analytics',
]
