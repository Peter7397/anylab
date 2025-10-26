import os
import fitz  # PyMuPDF
import hashlib
import json
import logging
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator
from django.conf import settings
from django.db import connection
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
# from sentence_transformers import SentenceTransformer  # temporarily disabled
import numpy as np
import requests

from .models import (
    PDFDocument, WebLink, KnowledgeShare, 
    UploadedFile, DocumentChunk, DocumentFile, QueryHistory
)
from .rag_service import EnhancedRAGService
from .improved_rag_service import enhanced_rag_service
from .advanced_rag_service import advanced_rag_service
from .comprehensive_rag_service import comprehensive_rag_service
from .serializers import (
    PDFDocumentSerializer, WebLinkSerializer, 
    KnowledgeShareSerializer, QueryHistorySerializer, DocumentSerializer
)

logger = logging.getLogger(__name__)

# Initialize RAG service
rag_service = EnhancedRAGService()

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_with_ollama(request):
    """Enhanced chat endpoint with history tracking and optimized parameters for Qwen 7B"""
    try:
        prompt = request.data.get('prompt', '').strip()
        if not prompt:
            return Response({'error': 'Prompt is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Create cache key for chat response
        import hashlib
        from django.core.cache import cache
        
        prompt_hash = hashlib.md5(prompt.encode('utf-8')).hexdigest()
        cache_key = f"chat_response_{prompt_hash}"
        
        # Try to get from cache first
        cached_response = cache.get(cache_key)
        if cached_response is not None:
            logger.info(f"Using cached chat response for prompt: {prompt[:30]}...")
            return Response(cached_response)

        # Get generation parameters with optimized defaults for Qwen 7B
        max_tokens = int(request.data.get('max_tokens') or getattr(settings, 'OLLAMA_DEFAULT_MAX_TOKENS', 256))  # Reduced from 512
        temperature = float(request.data.get('temperature') or getattr(settings, 'OLLAMA_TEMPERATURE', 0.3))
        top_p = float(request.data.get('top_p', 0.9))
        top_k = int(request.data.get('top_k', 40))
        repeat_penalty = float(request.data.get('repeat_penalty', 1.1))
        num_ctx = int(request.data.get('num_ctx') or getattr(settings, 'OLLAMA_NUM_CTX', 1024))  # Reduced from 2048
        
        # Generate response using Ollama
        model = getattr(settings, 'OLLAMA_MODEL', 'qwen:latest')
        ollama_url = getattr(settings, 'OLLAMA_API_URL', 'http://host.docker.internal:11434')
        timeout_seconds = getattr(settings, 'OLLAMA_REQUEST_TIMEOUT', 120)  # Reduced from 300 to 120 seconds
        
        # Use chat API for better responses with optimized parameters
        api_url = f"{ollama_url}/api/chat"
        payload = {
            "model": model,
            "stream": False,
            "messages": [
                {"role": "system", "content": getattr(settings, 'OLLAMA_SYSTEM_PROMPT', 'You are a helpful, expert assistant. Provide concise and accurate answers. Keep responses focused and to the point.')},
                {"role": "user", "content": prompt}
            ],
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "repeat_penalty": repeat_penalty,
                "num_ctx": num_ctx
            }
        }
        
        resp = requests.post(api_url, json=payload, timeout=timeout_seconds)
        resp.raise_for_status()
        
        response_data = resp.json()
        response_text = response_data["message"]["content"]
        
        # Cache the response
        response_obj = {
            'response': response_text,
            'model': model
        }
        cache.set(cache_key, response_obj, 1800)  # Cache for 30 minutes
        logger.info(f"Cached chat response for prompt: {prompt[:30]}...")
        
        # Save to history
        QueryHistory.objects.create(
            query=prompt,
            response=response_text,
            sources=[],
            query_type='chat',
            user=request.user
        )
        
        return Response(response_obj)
        
    except requests.exceptions.Timeout:
        logger.error("Ollama request timed out")
        return Response({
            'error': 'Request timed out. The model is taking too long to respond. Please try a shorter question or check if Ollama is running properly.'
        }, status=status.HTTP_408_REQUEST_TIMEOUT)
    except Exception as e:
        logger.error(f"Ollama request failed: {e}")
        return Response({
            'error': 'Failed to contact Qwen (Ollama). Please ensure the backend Ollama service is running.'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rag_search(request):
    """Enhanced RAG search with improved chunking and similarity scoring"""
    try:
        query = request.data.get('query', '').strip()
        if not query:
            return Response({'error': 'Query is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Default to more results for comprehensive mode
        default_top_k = 15 if request.data.get('search_mode', 'comprehensive') == 'comprehensive' else 8
        top_k = int(request.data.get('top_k', default_top_k))
        search_mode = request.data.get('search_mode', 'comprehensive')  # comprehensive, advanced, enhanced, or basic
        
        if search_mode == 'comprehensive':
            # Use comprehensive RAG for maximum detail and complete answers
            result = comprehensive_rag_service.query_with_comprehensive_rag(query, top_k=top_k, user=request.user)
        elif search_mode == 'advanced':
            # Use advanced RAG with hybrid search and reranking
            result = advanced_rag_service.query_with_advanced_rag(query, top_k=top_k, user=request.user)
        elif search_mode == 'enhanced':
            # Use enhanced RAG with improved chunking and scoring
            result = enhanced_rag_service.query_with_enhanced_rag(query, top_k=top_k, user=request.user)
        else:
            # Fallback to basic RAG service
            result = rag_service.query_with_rag(query, top_k=top_k, user=request.user)
        
        return Response(result)
        
    except Exception as e:
        logger.error(f"RAG search error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def advanced_rag_search(request):
    """Advanced RAG search with hybrid search and reranking"""
    try:
        query = request.data.get('query', '').strip()
        if not query:
            return Response({'error': 'Query is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        top_k = int(request.data.get('top_k', 8))
        search_mode = request.data.get('search_mode', 'hybrid')
        
        result = advanced_rag_service.query_with_advanced_rag(query, top_k=top_k, user=request.user)
        return Response(result)
        
    except Exception as e:
        logger.error(f"Advanced RAG search error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def comprehensive_rag_search(request):
    """Comprehensive RAG search with maximum detail and complete answers"""
    try:
        query = request.data.get('query', '').strip()
        if not query:
            return Response({'error': 'Query is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        top_k = int(request.data.get('top_k', 10))
        include_stats = request.data.get('include_stats', False)
        
        result = comprehensive_rag_service.query_with_comprehensive_rag(query, top_k=top_k, user=request.user)
        return Response(result)
        
    except Exception as e:
        logger.error(f"Comprehensive RAG search error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
# @permission_classes([IsAuthenticated])  # Temporarily disabled for testing
def vector_search(request):
    """Vector similarity search with history tracking"""
    try:
        query = request.data.get('query', '').strip()
        if not query:
            return Response({'error': 'Query is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Default to more results for comprehensive mode
        default_top_k = 12 if request.data.get('search_mode', 'comprehensive') == 'comprehensive' else 5
        top_k = int(request.data.get('top_k', default_top_k))
        
        # Search for relevant documents with comprehensive options
        search_mode = request.data.get('search_mode', 'comprehensive')
        if search_mode == 'comprehensive':
            relevant_docs = comprehensive_rag_service.search_for_comprehensive_results(query, top_k)
        elif search_mode == 'advanced':
            relevant_docs = advanced_rag_service.search_with_hybrid_and_reranking(query, top_k)
        elif search_mode == 'enhanced':
            relevant_docs = enhanced_rag_service.search_relevant_documents_with_scoring(query, top_k)
        else:
            relevant_docs = rag_service.search_relevant_documents(query, top_k)
        
        # Save to history (only if user is authenticated)
        if hasattr(request, 'user') and request.user.is_authenticated:
            QueryHistory.objects.create(
                query=query,
                response=f"Found {len(relevant_docs)} relevant documents",
                sources=relevant_docs,
                query_type='vector',
                user=request.user
            )
        
        return Response({
            'query': query,
            'results': relevant_docs,
            'count': len(relevant_docs)
        })
        
    except Exception as e:
        logger.error(f"Vector search error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_pdf_enhanced(request):
    """Enhanced PDF upload with vector indexing and duplicate detection"""
    try:
        # Handle both 'pdf' and 'file' field names for compatibility
        pdf_file = request.FILES.get('pdf') or request.FILES.get('file')
        if not pdf_file:
            return Response({'error': 'No PDF file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        title = request.data.get('title', pdf_file.name)
        description = request.data.get('description', '')
        
        # First, save the file to get a proper file path
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile
        
        # Generate unique filename to avoid conflicts
        import uuid
        file_extension = pdf_file.name.split('.')[-1] if '.' in pdf_file.name else 'pdf'
        unique_filename = f"pdfs/{uuid.uuid4()}.{file_extension}"
        
        # Save the file
        saved_file = default_storage.save(unique_filename, ContentFile(pdf_file.read()))
        
        # Reset file pointer for processing
        pdf_file.seek(0)
        
        # Check for duplicates using file hash
        file_hash = rag_service.compute_file_hash_from_upload(pdf_file)
        existing_file = UploadedFile.objects.filter(file_hash=file_hash).first()
        
        if existing_file:
            # File already exists - return existing file info
            return Response({
                'message': 'File already exists in database',
                'id': existing_file.id,
                'filename': existing_file.filename,
                'uploaded_at': existing_file.uploaded_at,
                'page_count': existing_file.page_count,
                'file_size': existing_file.file_size,
                'is_duplicate': True
            }, status=status.HTTP_200_OK)
        
        # Process PDF and build vector index
        result = rag_service.process_pdf_and_build_index(pdf_file, title, file_hash, request)
        
        if result['success']:
            # Create UploadedFile record with proper metadata
            uploaded_file = UploadedFile.objects.get(id=result['uploaded_file_id'])
            uploaded_file.file_size = pdf_file.size
            uploaded_file.save()
            
            # Create legacy PDFDocument entry for frontend compatibility
            pdf_doc = PDFDocument.objects.create(
                title=title,
                file=saved_file,  # Use the saved file path
                filename=pdf_file.name,
                description=description,
                uploaded_by=request.user if request.user.is_authenticated else None,
                page_count=result['page_count'],
                file_size=pdf_file.size
            )
            
            return Response({
                'message': 'PDF uploaded and indexed successfully',
                'id': pdf_doc.id,
                'title': pdf_doc.title,
                'filename': pdf_doc.filename,
                'uploaded_at': pdf_doc.uploaded_at,
                'page_count': result['page_count'],
                'file_size': pdf_doc.file_size,
                'uploaded_file_id': result['uploaded_file_id'],
                'is_duplicate': False
            })
        else:
            # If processing fails, clean up the saved file
            default_storage.delete(saved_file)
            return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"PDF upload error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_query_history(request):
    """Get query history for the user"""
    try:
        query_type = request.GET.get('type', 'all')
        limit = int(request.GET.get('limit', 20))
        
        queryset = QueryHistory.objects.filter(user=request.user)
        
        if query_type != 'all':
            queryset = queryset.filter(query_type=query_type)
        
        history = queryset.order_by('-created_at')[:limit]
        
        serializer = QueryHistorySerializer(history, many=True)
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"History retrieval error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_index_info(request):
    """Get information about the vector index"""
    try:
        info = rag_service.get_index_info()
        return Response(info)
    except Exception as e:
        logger.error(f"Index info error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_performance_stats(request):
    """Get performance statistics for AI responses"""
    try:
        from django.core.cache import cache
        from django.db.models import Avg, Count
        from datetime import datetime, timedelta
        
        # Get cache stats
        cache_info = cache.client.info()
        
        # Get recent query performance
        recent_queries = QueryHistory.objects.filter(
            created_at__gte=datetime.now() - timedelta(hours=24)
        ).aggregate(
            total_queries=Count('id'),
            avg_response_time=Avg('response_time') if hasattr(QueryHistory, 'response_time') else None
        )
        
        # Get cache hit rates
        cache_stats = {
            'redis_connected': cache.client.ping(),
            'cache_size': cache_info.get('used_memory_human', 'Unknown'),
            'cache_hits': cache_info.get('keyspace_hits', 0),
            'cache_misses': cache_info.get('keyspace_misses', 0),
        }
        
        if cache_stats['cache_hits'] + cache_stats['cache_misses'] > 0:
            cache_stats['hit_rate'] = round(
                cache_stats['cache_hits'] / (cache_stats['cache_hits'] + cache_stats['cache_misses']) * 100, 2
            )
        else:
            cache_stats['hit_rate'] = 0
        
        return Response({
            'cache_stats': cache_stats,
            'recent_queries': recent_queries,
            'ollama_url': getattr(settings, 'OLLAMA_API_URL', 'http://ollama:11434'),
            'ollama_model': getattr(settings, 'OLLAMA_MODEL', 'qwen:latest'),
            'optimization_settings': {
                'max_tokens': getattr(settings, 'OLLAMA_DEFAULT_MAX_TOKENS', 256),
                'context_window': getattr(settings, 'OLLAMA_NUM_CTX', 1024),
                'temperature': getattr(settings, 'OLLAMA_TEMPERATURE', 0.3),
                'timeout': getattr(settings, 'OLLAMA_REQUEST_TIMEOUT', 120),
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting performance stats: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_uploaded_files(request):
    """List all uploaded files"""
    try:
        files = UploadedFile.objects.all().order_by('-uploaded_at')
        paginator = Paginator(files, 20)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        data = []
        for file in page_obj:
            data.append({
                'id': file.id,
                'filename': file.filename,
                'uploaded_at': file.uploaded_at,
                'file_size': file.file_size,
                'page_count': file.page_count,
                'intro': file.intro
            })
        
        return Response({
            'files': data,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'total_pages': paginator.num_pages,
            'current_page': page_obj.number
        })
        
    except Exception as e:
        logger.error(f"File listing error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Legacy endpoints for backward compatibility
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def pdf_documents(request):
    """Legacy PDF documents endpoint"""
    if request.method == 'GET':
        documents = PDFDocument.objects.all().order_by('-uploaded_at')
        serializer = PDFDocumentSerializer(documents, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = PDFDocumentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(uploaded_by=request.user if request.user.is_authenticated else None)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def web_links(request):
    """Web links endpoint"""
    if request.method == 'GET':
        links = WebLink.objects.all().order_by('-created_at')
        serializer = WebLinkSerializer(links, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = WebLinkSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(added_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def knowledge_share(request):
    """Knowledge share endpoint"""
    if request.method == 'GET':
        shares = KnowledgeShare.objects.all()
        serializer = KnowledgeShareSerializer(shares, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = KnowledgeShareSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# PDF Management endpoints for frontend compatibility
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pdf_download(request, pdf_id):
    """Download PDF file"""
    try:
        pdf = get_object_or_404(PDFDocument, id=pdf_id)
        if pdf.file:
            response = HttpResponse(pdf.file, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{pdf.filename}"'
            return response
        else:
            return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"PDF download error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def pdf_delete(request, pdf_id):
    """Delete PDF file"""
    try:
        pdf = get_object_or_404(PDFDocument, id=pdf_id)
        pdf.delete()
        return Response({'message': 'PDF deleted successfully'})
    except Exception as e:
        logger.error(f"PDF delete error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pdf_search(request):
    """Search PDFs by title or content"""
    try:
        query = request.data.get('query', '').strip()
        search_type = request.data.get('search_type', 'both')
        
        if not query:
            return Response({'error': 'Query is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        pdfs = PDFDocument.objects.all()
        
        if search_type in ['title', 'both']:
            pdfs = pdfs.filter(title__icontains=query)
        elif search_type == 'content':
            # For content search, we would need to implement text extraction
            # For now, just search in title
            pdfs = pdfs.filter(title__icontains=query)
        
        serializer = PDFDocumentSerializer(pdfs, many=True)
        return Response({
            'results': serializer.data,
            'count': len(serializer.data),
            'query': query
        })
        
    except Exception as e:
        logger.error(f"PDF search error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Document Management endpoints for various file types
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def documents(request):
    """Document management endpoint for various file types"""
    if request.method == 'GET':
        documents = DocumentFile.objects.all().order_by('-uploaded_at')
        serializer = DocumentSerializer(documents, many=True, context={'request': request})
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = DocumentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(uploaded_by=request.user if request.user.is_authenticated else None)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_document_enhanced(request):
    """Enhanced document upload with vector indexing and duplicate detection"""
    try:
        # Handle both 'file' and 'document' field names for compatibility
        uploaded_file = request.FILES.get('file') or request.FILES.get('document')
        if not uploaded_file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        title = request.data.get('title', uploaded_file.name)
        description = request.data.get('description', '')
        
        # Determine document type from file extension
        file_extension = uploaded_file.name.split('.')[-1].lower() if '.' in uploaded_file.name else ''
        document_type_map = {
            'pdf': 'pdf',
            'doc': 'doc',
            'docx': 'docx',
            'xls': 'xls',
            'xlsx': 'xlsx',
            'ppt': 'ppt',
            'pptx': 'pptx',
            'txt': 'txt',
            'rtf': 'rtf'
        }
        document_type = document_type_map.get(file_extension, 'pdf')
        
        # First, save the file to get a proper file path
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile
        
        # Generate unique filename to avoid conflicts
        import uuid
        unique_filename = f"documents/{uuid.uuid4()}.{file_extension}"
        
        # Save the file
        saved_file = default_storage.save(unique_filename, ContentFile(uploaded_file.read()))
        
        # Reset file pointer for processing
        uploaded_file.seek(0)
        
        # Check for duplicates using file hash
        file_hash = rag_service.compute_file_hash_from_upload(uploaded_file)
        existing_file = UploadedFile.objects.filter(file_hash=file_hash).first()
        
        if existing_file:
            # File already exists - return existing file info
            return Response({
                'message': 'File already exists in database',
                'id': existing_file.id,
                'filename': existing_file.filename,
                'uploaded_at': existing_file.uploaded_at,
                'page_count': existing_file.page_count,
                'file_size': existing_file.file_size,
                'is_duplicate': True
            }, status=status.HTTP_200_OK)
        
        # Process document and build vector index (only for supported types)
        if document_type in ['pdf', 'txt', 'rtf']:
            result = rag_service.process_document_and_build_index(uploaded_file, title, file_hash, request)
        else:
            # For other document types, just store without vector indexing for now
            result = {'success': True, 'page_count': 0}
        
        if result['success']:
            # Create UploadedFile record with proper metadata
            if 'uploaded_file_id' in result:
                uploaded_file_record = UploadedFile.objects.get(id=result['uploaded_file_id'])
                uploaded_file_record.file_size = uploaded_file.size
                uploaded_file_record.save()
            
            # Create Document entry
            doc = DocumentFile.objects.create(
                title=title,
                file=saved_file,  # Use the saved file path
                filename=uploaded_file.name,
                document_type=document_type,
                description=description,
                uploaded_by=request.user if request.user.is_authenticated else None,
                page_count=result.get('page_count', 0),
                file_size=uploaded_file.size
            )
            
            return Response({
                'message': 'Document uploaded successfully',
                'id': doc.id,
                'title': doc.title,
                'filename': doc.filename,
                'document_type': doc.document_type,
                'uploaded_at': doc.uploaded_at,
                'page_count': doc.page_count,
                'file_size': doc.file_size,
                'uploaded_file_id': result.get('uploaded_file_id'),
                'is_duplicate': False
            })
        else:
            # If processing fails, clean up the saved file
            default_storage.delete(saved_file)
            return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Document upload error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def document_download(request, doc_id):
    """Download document file"""
    try:
        doc = get_object_or_404(DocumentFile, id=doc_id)
        if doc.file:
            response = HttpResponse(doc.file, content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{doc.filename}"'
            return response
        else:
            return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Document download error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def document_delete(request, doc_id):
    """Delete document file"""
    try:
        doc = get_object_or_404(DocumentFile, id=doc_id)
        doc.delete()
        return Response({'message': 'Document deleted successfully'})
    except Exception as e:
        logger.error(f"Document delete error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def document_search(request):
    """Search documents by title or description"""
    try:
        query = request.data.get('query', '').strip()
        if not query:
            return Response({'error': 'Search query is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        from django.db import models
        documents = DocumentFile.objects.filter(
            models.Q(title__icontains=query) | 
            models.Q(description__icontains=query)
        ).order_by('-uploaded_at')
        
        serializer = DocumentSerializer(documents, many=True)
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Document search error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@login_required
def pdf_view(request, file_id):
    """Enhanced PDF viewer with search and highlight functionality"""
    from django.shortcuts import get_object_or_404
    
    # Try to find the file in UploadedFile first (for RAG documents)
    try:
        uploaded_file = get_object_or_404(UploadedFile, id=file_id)
        file_path = os.path.join(settings.MEDIA_ROOT, 'uploaded_pdfs', uploaded_file.filename)
        pdf_url = f"{request.scheme}://{request.get_host()}/media/uploaded_pdfs/{uploaded_file.filename}"
        filename = uploaded_file.filename
    except:
        # If not found in UploadedFile, try DocumentFile (for general documents)
        try:
            document_file = get_object_or_404(DocumentFile, id=file_id)
            if document_file.file:
                file_path = document_file.file.path
                pdf_url = f"{request.scheme}://{request.get_host()}{document_file.file.url}"
                filename = document_file.filename or document_file.title
            else:
                raise Exception("Document file not found")
        except:
            # If not found in DocumentFile, try PDFDocument (legacy)
            try:
                pdf_document = get_object_or_404(PDFDocument, id=file_id)
                file_path = pdf_document.file.path
                pdf_url = f"{request.scheme}://{request.get_host()}{pdf_document.file.url}"
                filename = pdf_document.filename
            except:
                raise Exception("PDF file not found")
    
    page = request.GET.get('page', 1)
    
    # For debugging
    print(f"Generated PDF URL: {pdf_url}")
    print(f"PDF file exists: {os.path.exists(file_path)}")
    print(f"Full PDF path: {file_path}")
    
    return render(request, 'ai_assistant/pdf_view.html', {
        'uploaded_file': {'filename': filename},  # Create a simple object for template compatibility
        'pdf_url': pdf_url,
        'page': page
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_document_enhanced_v2(request):
    """Enhanced document upload with improved chunking (alternative implementation)"""
    try:
        if 'file' not in request.FILES:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_file = request.FILES['file']
        title = request.data.get('title', uploaded_file.name)
        description = request.data.get('description', '')
        
        # Validate file size (50MB limit)
        if uploaded_file.size > 50 * 1024 * 1024:
            return Response({'error': 'File too large. Maximum size is 50MB.'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Validate file type
        allowed_extensions = ['pdf', 'txt', 'rtf', 'doc', 'docx']
        file_extension = uploaded_file.name.split('.')[-1].lower() if '.' in uploaded_file.name else ''
        
        if file_extension not in allowed_extensions:
            return Response({
                'error': f'Unsupported file type. Allowed: {", ".join(allowed_extensions)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Process document with enhanced chunking
        result = enhanced_rag_service.process_document_with_enhanced_chunking(
            uploaded_file, title=title, request=request
        )
        
        if result['success']:
            return Response({
                'message': 'Document uploaded and processed successfully',
                'id': result['uploaded_file_id'],
                'title': title,
                'total_chunks': result['total_chunks'],
                'page_count': result['page_count'],
                'processing_method': 'enhanced_chunking'
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Enhanced document upload error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_search_analytics(request):
    """Get search performance analytics"""
    try:
        analytics = advanced_rag_service.get_search_analytics()
        return Response(analytics)
    except Exception as e:
        logger.error(f"Search analytics error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
