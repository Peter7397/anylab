"""
RAG Views Module

This module contains all RAG (Retrieval-Augmented Generation) related views
including chat, search, and document upload functionality.
"""

import logging
import hashlib
import os
import fitz  # PyMuPDF
import re
from django.conf import settings
from django.core.cache import cache
from django.core.files.storage import FileSystemStorage
from django.utils import timezone
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse, Http404
import requests

from ..utils.version_detector import detect_version
from ..utils.product_detector import detect_product, detect_content_type
from ..utils.metadata_validator import validate_metadata, sanitize_metadata

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
    """Enhanced document upload with automatic processing and metadata"""
    try:
        BaseViewMixin.log_request(request, 'upload_document_enhanced')
        
        if 'file' not in request.FILES:
            return bad_request_response('No file provided')
        
        file = request.FILES['file']
        
        # Extract metadata from request
        product_category = request.POST.get('product_category', '')
        content_type = request.POST.get('content_type', '')
        version = request.POST.get('version', '')
        title = request.POST.get('title', file.name)
        description = request.POST.get('description', '')
        document_type = request.POST.get('document_type', 'pdf')
        
        # Auto-detect metadata if not provided
        search_text = f"{title} {file.name} {description}"
        
        if not product_category:
            product_category = detect_product(search_text) or ''
        
        if not content_type:
            content_type = detect_content_type(search_text) or ''
        
        # Auto-detect version if not provided
        if not version:
            version = detect_version(title) or detect_version(file.name)
        
        # Create and validate metadata
        metadata = {
            'product_category': product_category,
            'content_type': content_type,
            'version': version,
            'document_type': document_type
        }
        
        # Sanitize metadata
        metadata = sanitize_metadata(metadata)
        
        # Validate metadata (warn but don't block for now)
        is_valid, errors = validate_metadata(metadata)
        if not is_valid and metadata['product_category']:  # Only validate if product is set
            logger.warning(f"Metadata validation errors: {errors}")
        
        # Use service layer to process document
        result = rag_service.upload_document_enhanced(file, request.user)
        
        if result['success']:
            # Create DocumentFile record with metadata
            import json
            from ai_assistant.models import DocumentChunk
            
            # Find the uploaded file
            uploaded_file_id = result['data'].get('uploaded_file_id')
            uploaded_file = None
            if uploaded_file_id:
                uploaded_file = UploadedFile.objects.get(id=uploaded_file_id)
            
            # Create DocumentFile record
            document_file = DocumentFile.objects.create(
                title=title,
                filename=file.name,
                document_type=document_type,
                description=description,
                metadata=metadata,  # Django JSONField can store dict directly
                uploaded_by=request.user,
                page_count=result['data'].get('page_count', 1),
                file_size=file.size
            )
            
            # Link all chunks from UploadedFile to DocumentFile
            if uploaded_file:
                chunks_updated = DocumentChunk.objects.filter(
                    uploaded_file=uploaded_file,
                    document_file__isnull=True
                ).update(document_file=document_file)
                logger.info(f"Linked {chunks_updated} chunks to DocumentFile {document_file.id}")
            
            result['data']['document_id'] = document_file.id
            result['data']['metadata'] = metadata
            
            BaseViewMixin.log_response(result['data'], 'upload_document_enhanced')
            return success_response(result['message'], result['data'])
        
        else:
            return error_response(result['message'])
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'upload_document_enhanced')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def extract_documents_metadata(request):
    """Extract metadata for all documents missing product/content/version"""
    try:
        BaseViewMixin.log_request(request, 'extract_documents_metadata')
        
        import json
        
        # Get all documents
        all_docs = DocumentFile.objects.all()
        
        updated_count = 0
        skipped_count = 0
        
        for doc in all_docs:
            try:
                # Check if metadata already exists
                current_metadata = {}
                if doc.metadata:
                    try:
                        current_metadata = json.loads(doc.metadata) if isinstance(doc.metadata, str) else doc.metadata
                    except json.JSONDecodeError:
                        pass
                
                # Skip if already has product/content/version
                if (current_metadata.get('product_category') and 
                    current_metadata.get('content_type')):
                    skipped_count += 1
                    continue
                
                # Create search text from title, filename, and description
                search_text = f"{doc.title} {doc.filename} {doc.description or ''}"
                
                # Auto-detect metadata
                product_category = detect_product(search_text) or ''
                content_type = detect_content_type(search_text) or ''
                version = detect_version(search_text) or ''
                
                # Only update if we detected something
                if product_category or content_type or version:
                    # Prepare metadata
                    new_metadata = {
                        'product_category': product_category,
                        'content_type': content_type,
                        'version': version,
                        'document_type': doc.document_type
                    }
                    
                    # Merge with existing metadata
                    if current_metadata:
                        new_metadata.update(current_metadata)
                    
                    # Update the document - store as dict (Django JSONField handles both)
                    doc.metadata = new_metadata
                    doc.save()
                    
                    updated_count += 1
            except Exception as e:
                logger.error(f"Error processing document {doc.id}: {e}")
                continue
        
        result = {
            'updated_count': updated_count,
            'skipped_count': skipped_count,
            'total_processed': updated_count + skipped_count
        }
        
        BaseViewMixin.log_response(result, 'extract_documents_metadata')
        return success_response(f"Metadata extracted for {updated_count} documents", result)
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'extract_documents_metadata')


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
            
            serializer = DocumentSerializer(docs[start:end], many=True, context={'request': request})
            
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
        
        # Delete associated chunks - find via document_file or uploaded_file
        # First try via document_file (new way)
        chunks_via_doc = DocumentChunk.objects.filter(document_file=doc)
        if chunks_via_doc.exists():
            chunks_via_doc.delete()
        
        # Also check for chunks via uploaded_file (legacy way)
        # Find UploadedFile that matches this document's filename
        uploaded_files = UploadedFile.objects.filter(filename=doc.filename)
        for uf in uploaded_files:
            chunks_via_uf = DocumentChunk.objects.filter(uploaded_file=uf)
            if chunks_via_uf.exists():
                chunks_via_uf.delete()
        
        # Delete file if exists
        if doc.file and hasattr(doc.file, 'path'):
            import os
            if os.path.exists(doc.file.path):
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
        search_type = request.data.get('search_type', 'both')
        document_type = request.data.get('document_type', 'all')
        
        # Get queryset - filter by document_type if specified
        if document_type and document_type != 'all':
            docs = DocumentFile.objects.filter(document_type=document_type)
        else:
            docs = DocumentFile.objects.all()
        
        # Apply search filter only if query provided
        if query:
            if search_type == 'title':
                docs = docs.filter(title__icontains=query)
            elif search_type == 'content' or search_type == 'description':
                docs = docs.filter(description__icontains=query)
            else:  # both
                docs = docs.filter(
                    Q(title__icontains=query) | Q(description__icontains=query)
                )
        
        # Debug logging
        logger.info(f"Document search: query='{query}', document_type='{document_type}', results={docs.count()}")
        
        serializer = DocumentSerializer(docs, many=True, context={'request': request})
        
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
        
        serializer = PDFDocumentSerializer(pdfs, many=True, context={'request': request})
        
        return success_response(
            "PDFs found",
            {'results': serializer.data, 'count': pdfs.count()}
        )
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'pdf_search')


def extract_html_from_mhtml(content: str) -> str:
    """Extract HTML content from MHTML format"""
    try:
        # Look for Content-Type: text/html boundaries
        html_start_pattern = r'Content-Type:\s*text/html.*?\r\n\r\n'
        html_match = re.search(html_start_pattern, content, re.IGNORECASE | re.DOTALL)
        
        if html_match:
            # Find the position where HTML starts
            html_start = html_match.end()
            # Look for the next boundary marker
            boundary_pattern = r'\r\n\r\n------Multipart'
            boundary_match = re.search(boundary_pattern, content[html_start:])
            
            if boundary_match:
                html_content = content[html_start:html_start + boundary_match.start()]
                # Decode quoted-printable encoding if present
                html_content = html_content.replace('=\r\n', '').replace('=\n', '')
                html_content = html_content.replace('=3D', '=').replace('=0D', '\r').replace('=0A', '\n')
                return html_content
            else:
                # No boundary found, return everything after HTML marker
                return content[html_start:]
        
        # If no HTML section found, return the original content
        return content
    except Exception as e:
        logger.error(f"Error extracting HTML from MHTML: {e}")
        return content


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def document_html_view(request, doc_id):
    """Extract and serve HTML content from documents (handles MHTML)"""
    try:
        doc = DocumentFile.objects.get(id=doc_id)
        
        if not doc.file:
            raise Http404("Document file not found")
        
        # Read file content
        doc.file.open('r')
        content = doc.file.read()
        doc.file.close()
        
        # Check if it's MHTML
        if 'multipart/related' in content[:2000].lower() or 'multipartboundary' in content[:2000].lower():
            # Extract HTML from MHTML
            html_content = extract_html_from_mhtml(content)
        else:
            # Regular HTML file
            html_content = content
        
        # Return HTML response
        response = HttpResponse(html_content, content_type='text/html; charset=utf-8')
        # Allow same-origin iframe embedding
        response['X-Frame-Options'] = 'SAMEORIGIN'
        return response
        
    except DocumentFile.DoesNotExist:
        raise Http404("Document not found")
    except Exception as e:
        logger.error(f"Error serving document HTML: {e}")
        raise Http404("Error processing document")

