"""
RAG Views Module

This module contains all RAG (Retrieval-Augmented Generation) related views
including chat, search, and document upload functionality.
"""

import logging
import hashlib
import os
import fitz  # PyMuPDF
from django.conf import settings
from django.core.cache import cache
from django.core.files.storage import FileSystemStorage
from django.utils import timezone
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import requests

from ..models import (
    PDFDocument, WebLink, KnowledgeShare, 
    UploadedFile, DocumentChunk, DocumentFile, QueryHistory
)
from ..rag_service import EnhancedRAGService
from ..improved_rag_service import enhanced_rag_service
from ..advanced_rag_service import advanced_rag_service
from ..comprehensive_rag_service import comprehensive_rag_service
from ..serializers import (
    PDFDocumentSerializer, WebLinkSerializer, 
    KnowledgeShareSerializer, QueryHistorySerializer, DocumentSerializer
)
from ..services.rag_service import RAGService
from .base_views import (
    BaseViewMixin, success_response, error_response, bad_request_response,
    internal_error_response, unauthorized_response
)

logger = logging.getLogger(__name__)

# Initialize RAG service
rag_service = RAGService()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_with_ollama(request):
    """Enhanced chat endpoint with history tracking and optimized parameters for Qwen 7B"""
    try:
        BaseViewMixin.log_request(request, 'chat_with_ollama')
        
        prompt = request.data.get('prompt', '').strip()
        if not prompt:
            return bad_request_response('Prompt is required')

        # Get generation parameters
        generation_params = {
            'max_tokens': request.data.get('max_tokens'),
            'temperature': request.data.get('temperature'),
            'top_p': request.data.get('top_p'),
            'top_k': request.data.get('top_k'),
            'repeat_penalty': request.data.get('repeat_penalty'),
            'num_ctx': request.data.get('num_ctx')
        }
        
        # Use service layer
        result = rag_service.chat_with_ollama(prompt, request.user, **generation_params)
        
        if result['success']:
            BaseViewMixin.log_response(result['data'], 'chat_with_ollama')
            return success_response(result['message'], result['data'])
        else:
            return error_response(result['message'])
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'chat_with_ollama')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rag_search(request):
    """Enhanced RAG search with improved chunking and similarity scoring"""
    try:
        BaseViewMixin.log_request(request, 'rag_search')
        
        query = request.data.get('query', '').strip()
        if not query:
            return bad_request_response('Query is required')
        
        # Get search parameters
        top_k = int(request.data.get('top_k', 0)) or None
        search_mode = request.data.get('search_mode', 'comprehensive')
        
        # Use service layer
        result = rag_service.rag_search(query, request.user, search_mode, top_k)
        
        if result['success']:
            BaseViewMixin.log_response(result['data'], 'rag_search')
            return success_response(result['message'], result['data'])
        else:
            return error_response(result['message'])
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'rag_search')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def advanced_rag_search(request):
    """Advanced RAG search with hybrid search and reranking"""
    try:
        BaseViewMixin.log_request(request, 'advanced_rag_search')
        
        query = request.data.get('query', '').strip()
        if not query:
            return bad_request_response('Query is required')
        
        top_k = int(request.data.get('top_k', 8))
        search_mode = request.data.get('search_mode', 'hybrid')
        
        result = advanced_rag_service.query_with_advanced_rag(query, top_k=top_k, user=request.user)
        
        BaseViewMixin.log_response(result, 'advanced_rag_search')
        return success_response("Advanced RAG search completed successfully", result)
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'advanced_rag_search')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def comprehensive_rag_search(request):
    """Comprehensive RAG search with maximum detail and complete answers"""
    try:
        BaseViewMixin.log_request(request, 'comprehensive_rag_search')
        
        query = request.data.get('query', '').strip()
        if not query:
            return bad_request_response('Query is required')
        
        top_k = int(request.data.get('top_k', 10))
        include_stats = request.data.get('include_stats', False)
        
        result = comprehensive_rag_service.query_with_comprehensive_rag(query, top_k=top_k, user=request.user)
        
        BaseViewMixin.log_response(result, 'comprehensive_rag_search')
        return success_response("Comprehensive RAG search completed successfully", result)
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'comprehensive_rag_search')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def vector_search(request):
    """Vector similarity search with history tracking"""
    try:
        BaseViewMixin.log_request(request, 'vector_search')
        
        query = request.data.get('query', '').strip()
        if not query:
            return bad_request_response('Query is required')
        
        # Get search parameters
        top_k = int(request.data.get('top_k', 0)) or None
        search_mode = request.data.get('search_mode', 'comprehensive')
        
        # Use service layer
        result = rag_service.vector_search(query, request.user, search_mode, top_k)
        
        if result['success']:
            BaseViewMixin.log_response(result['data'], 'vector_search')
            return success_response(result['message'], result['data'])
        else:
            return error_response(result['message'])
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'vector_search')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_pdf_enhanced(request):
    """Enhanced PDF upload with automatic processing and RAG indexing"""
    try:
        BaseViewMixin.log_request(request, 'upload_pdf_enhanced')
        
        if 'file' not in request.FILES:
            return bad_request_response('No file provided')
        
        file = request.FILES['file']
        
        # Use service layer
        result = rag_service.upload_pdf_enhanced(file, request.user)
        
        if result['success']:
            BaseViewMixin.log_response(result['data'], 'upload_pdf_enhanced')
            return success_response(result['message'], result['data'])
        else:
            return error_response(result['message'])
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'upload_pdf_enhanced')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_document_enhanced(request):
    """Enhanced document upload with automatic processing"""
    try:
        BaseViewMixin.log_request(request, 'upload_document_enhanced')
        
        if 'file' not in request.FILES:
            return bad_request_response('No file provided')
        
        file = request.FILES['file']
        
        # Use service layer
        result = rag_service.upload_document_enhanced(file, request.user)
        
        if result['success']:
            BaseViewMixin.log_response(result['data'], 'upload_document_enhanced')
            return success_response(result['message'], result['data'])
        else:
            return error_response(result['message'])
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'upload_document_enhanced')


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def documents(request):
    """List or create documents"""
    try:
        BaseViewMixin.log_request(request, 'documents')
        
        if request.method == 'GET':
            # Get all documents with pagination
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))
            
            docs = DocumentFile.objects.all().order_by('-uploaded_at')
            start = (page - 1) * page_size
            end = start + page_size
            
            serializer = DocumentSerializer(docs[start:end], many=True)
            
            return success_response(
                "Documents retrieved successfully",
                {
                    'documents': serializer.data,
                    'total': docs.count(),
                    'page': page,
                    'page_size': page_size
                }
            )
        
        elif request.method == 'POST':
            # Create new document
            serializer = DocumentSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(uploaded_by=request.user)
                return success_response("Document created successfully", serializer.data)
            else:
                return bad_request_response(f"Validation error: {serializer.errors}")
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'documents')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def document_download(request, doc_id):
    """Download a document"""
    try:
        BaseViewMixin.log_request(request, 'document_download')
        
        doc = DocumentFile.objects.get(id=doc_id)
        if doc.file:
            from django.http import FileResponse
            import os
            return FileResponse(open(doc.file.path, 'rb'))
        else:
            return error_response("File not found")
        
    except DocumentFile.DoesNotExist:
        return error_response("Document not found")
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'document_download')


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def document_delete(request, doc_id):
    """Delete a document"""
    try:
        BaseViewMixin.log_request(request, 'document_delete')
        
        doc = DocumentFile.objects.get(id=doc_id)
        
        # Delete associated chunks
        DocumentChunk.objects.filter(uploaded_file=doc.uploaded_file).delete()
        
        # Delete file if exists
        if doc.file:
            os.remove(doc.file.path)
        
        doc.delete()
        
        return success_response("Document deleted successfully", {})
        
    except DocumentFile.DoesNotExist:
        return error_response("Document not found")
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'document_delete')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def document_search(request):
    """Search documents"""
    try:
        BaseViewMixin.log_request(request, 'document_search')
        
        query = request.data.get('query', '').strip()
        if not query:
            return bad_request_response('Query is required')
        
        search_type = request.data.get('search_type', 'title')
        
        if search_type == 'title':
            docs = DocumentFile.objects.filter(title__icontains=query)
        elif search_type == 'description':
            docs = DocumentFile.objects.filter(description__icontains=query)
        else:  # both
            docs = DocumentFile.objects.filter(
                Q(title__icontains=query) | Q(description__icontains=query)
            )
        
        serializer = DocumentSerializer(docs, many=True)
        
        return success_response(
            "Documents found",
            {'results': serializer.data, 'count': docs.count()}
        )
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'document_search')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pdf_view(request, file_id):
    """View PDF document"""
    try:
        BaseViewMixin.log_request(request, 'pdf_view')
        
        uploaded_file = UploadedFile.objects.get(id=file_id)
        
        file_info = {
            'id': uploaded_file.id,
            'filename': uploaded_file.filename,
            'page_count': uploaded_file.page_count,
            'file_size': uploaded_file.file_size,
            'uploaded_at': uploaded_file.uploaded_at
        }
        
        return success_response("PDF information retrieved", file_info)
        
    except UploadedFile.DoesNotExist:
        return error_response("File not found")
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'pdf_view')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pdf_download(request, pdf_id):
    """Download a PDF"""
    try:
        BaseViewMixin.log_request(request, 'pdf_download')
        
        pdf = PDFDocument.objects.get(id=pdf_id)
        if pdf.file:
            from django.http import FileResponse
            return FileResponse(open(pdf.file.path, 'rb'), content_type='application/pdf')
        else:
            return error_response("File not found")
        
    except PDFDocument.DoesNotExist:
        return error_response("PDF not found")
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'pdf_download')


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def pdf_delete(request, pdf_id):
    """Delete a PDF"""
    try:
        BaseViewMixin.log_request(request, 'pdf_delete')
        
        pdf = PDFDocument.objects.get(id=pdf_id)
        
        # Delete associated chunks
        DocumentChunk.objects.filter(uploaded_file__file_hash=pdf.file.hash).delete()
        
        if pdf.file and os.path.exists(pdf.file.path):
            os.remove(pdf.file.path)
        
        pdf.delete()
        
        return success_response("PDF deleted successfully", {})
        
    except PDFDocument.DoesNotExist:
        return error_response("PDF not found")
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'pdf_delete')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pdf_search(request):
    """Search PDFs"""
    try:
        BaseViewMixin.log_request(request, 'pdf_search')
        
        query = request.data.get('query', '').strip()
        search_type = request.data.get('search_type', 'title')
        
        if not query:
            return bad_request_response('Query is required')
        
        if search_type == 'title':
            pdfs = PDFDocument.objects.filter(title__icontains=query)
        elif search_type == 'content':
            # Search in chunks
            chunks = DocumentChunk.objects.filter(content__icontains=query)
            pdfs = PDFDocument.objects.filter(uploaded_file__chunks__in=chunks).distinct()
        else:
            pdfs = PDFDocument.objects.filter(title__icontains=query)
        
        serializer = PDFDocumentSerializer(pdfs, many=True)
        
        return success_response(
            "PDFs found",
            {'results': serializer.data, 'count': pdfs.count()}
        )
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'pdf_search')
