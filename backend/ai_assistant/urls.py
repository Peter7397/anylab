from django.urls import path
from . import views

urlpatterns = [
    # Enhanced AI endpoints
    path('chat/ollama/', views.chat_with_ollama, name='chat_with_ollama'),
    path('rag/search/', views.rag_search, name='rag_search'),
    path('rag/advanced/', views.advanced_rag_search, name='advanced_rag_search'),
    path('rag/comprehensive/', views.comprehensive_rag_search, name='comprehensive_rag_search'),
    path('vector/search/', views.vector_search, name='vector_search'),
    path('upload/pdf/enhanced/', views.upload_pdf_enhanced, name='upload_pdf_enhanced'),
    
    # History and management endpoints
    path('history/', views.get_query_history, name='get_query_history'),
    path('index/info/', views.get_index_info, name='get_index_info'),
    path('files/', views.list_uploaded_files, name='list_uploaded_files'),
    path('performance/stats/', views.get_performance_stats, name='get_performance_stats'),
    path('search/analytics/', views.get_search_analytics, name='get_search_analytics'),
    
    # Document Management endpoints (for frontend compatibility)
    path('documents/', views.documents, name='documents'),
    path('documents/upload/', views.upload_document_enhanced, name='document_upload'),
    path('documents/upload/enhanced/', views.upload_document_enhanced, name='upload_document_enhanced'),
    path('documents/<int:doc_id>/download/', views.document_download, name='document_download'),
    path('documents/<int:doc_id>/delete/', views.document_delete, name='document_delete'),
    path('documents/search/', views.document_search, name='document_search'),
    
    # Enhanced PDF viewer (must come before legacy patterns)
    path('pdf/<int:file_id>/view/', views.pdf_view, name='pdf_view'),
    
    # PDF Management endpoints (legacy for backward compatibility)
    path('pdfs/', views.pdf_documents, name='pdf_documents'),
    path('pdfs/upload/', views.upload_pdf_enhanced, name='pdf_upload'),  # Redirect to enhanced upload
    path('pdfs/<int:pdf_id>/download/', views.pdf_download, name='pdf_download'),
    path('pdfs/<int:pdf_id>/delete/', views.pdf_delete, name='pdf_delete'),
    path('pdfs/search/', views.pdf_search, name='pdf_search'),
    
    # Legacy endpoints for backward compatibility
    path('pdf/', views.pdf_documents, name='pdf_documents'),
    path('weblinks/', views.web_links, name='web_links'),
    path('knowledge-share/', views.knowledge_share, name='knowledge_share'),
] 