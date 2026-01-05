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
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import SessionAuthentication
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
from ..service_classes.graph_rag_service import graph_rag_service
from ..serializers import (
    PDFDocumentSerializer, WebLinkSerializer, 
    KnowledgeShareSerializer, QueryHistorySerializer, DocumentSerializer
)
from ..service_classes.rag_service import RAGService
from .base_views import (
    BaseViewMixin, success_response, error_response, bad_request_response,
    internal_error_response, unauthorized_response
)
from users.permissions import HasFeaturePermission

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

        # Get language preference from Accept-Language header
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', 'en-US')
        # Extract primary language (e.g., 'zh-CN' or 'en-US')
        language = accept_language.split(',')[0].strip() if accept_language else 'en-US'

        # Get generation parameters
        generation_params = {
            'max_tokens': request.data.get('max_tokens'),
            'temperature': request.data.get('temperature'),
            'top_p': request.data.get('top_p'),
            'top_k': request.data.get('top_k'),
            'repeat_penalty': request.data.get('repeat_penalty'),
            'num_ctx': request.data.get('num_ctx'),
            'language': language  # Pass language to service
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
@permission_classes([IsAuthenticated, HasFeaturePermission.require('ai.rag')])
def rag_search(request):
    """Enhanced RAG search with improved chunking and similarity scoring"""
    try:
        BaseViewMixin.log_request(request, 'rag_search')
        
        query = request.data.get('query', '').strip()
        if not query:
            return bad_request_response('Query is required')
        
        # Get language preference from Accept-Language header
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', 'en-US')
        language = accept_language.split(',')[0].strip() if accept_language else 'en-US'
        
        # Get search parameters
        top_k = int(request.data.get('top_k', 0)) or None
        search_mode = request.data.get('search_mode', 'comprehensive')
        
        # Use service layer with language parameter
        result = rag_service.rag_search(query, request.user, search_mode, top_k, language=language)
        
        if result['success']:
            BaseViewMixin.log_response(result['data'], 'rag_search')
            return success_response(result['message'], result['data'])
        else:
            return error_response(result['message'])
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'rag_search')


@api_view(['POST'])
@permission_classes([IsAuthenticated, HasFeaturePermission.require('ai.rag')])
def advanced_rag_search(request):
    """Advanced RAG search with hybrid search and reranking"""
    try:
        BaseViewMixin.log_request(request, 'advanced_rag_search')
        
        query = request.data.get('query', '').strip()
        if not query:
            return bad_request_response('Query is required')
        
        # Get language preference from Accept-Language header
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', 'en-US')
        language = accept_language.split(',')[0].strip() if accept_language else 'en-US'
        
        top_k = int(request.data.get('top_k', 8))
        search_mode = request.data.get('search_mode', 'hybrid')
        
        result = advanced_rag_service.query_with_advanced_rag(query, top_k=top_k, user=request.user, language=language)
        
        BaseViewMixin.log_response(result, 'advanced_rag_search')
        return success_response("Advanced RAG search completed successfully", result)
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'advanced_rag_search')


@api_view(['POST'])
@permission_classes([IsAuthenticated, HasFeaturePermission.require('ai.rag')])
def comprehensive_rag_search(request):
    """Comprehensive RAG search with maximum detail and complete answers"""
    try:
        BaseViewMixin.log_request(request, 'comprehensive_rag_search')
        
        query = request.data.get('query', '').strip()
        if not query:
            return bad_request_response('Query is required')
        
        # Get language preference from Accept-Language header
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', 'en-US')
        language = accept_language.split(',')[0].strip() if accept_language else 'en-US'
        
        top_k = int(request.data.get('top_k', 10))
        include_stats = request.data.get('include_stats', False)
        
        result = comprehensive_rag_service.query_with_comprehensive_rag(query, top_k=top_k, user=request.user, language=language)
        
        BaseViewMixin.log_response(result, 'comprehensive_rag_search')
        return success_response("Comprehensive RAG search completed successfully", result)
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'comprehensive_rag_search')


@api_view(['POST'])
@permission_classes([IsAuthenticated, HasFeaturePermission.require('ai.rag')])
def graph_rag_search(request):
    """Graph-Enhanced RAG search combining vector similarity with knowledge graph traversal"""
    try:
        BaseViewMixin.log_request(request, 'graph_rag_search')
        
        query = request.data.get('query', '').strip()
        if not query:
            return bad_request_response('Query is required')
        
        # Get language preference from Accept-Language header
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', 'en-US')
        language = accept_language.split(',')[0].strip() if accept_language else 'en-US'
        
        top_k = int(request.data.get('top_k', 10))
        
        result = graph_rag_service.query_with_graph_rag(query, top_k=top_k, user=request.user, language=language)
        
        BaseViewMixin.log_response(result, 'graph_rag_search')
        return success_response("Graph RAG search completed successfully", result)
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'graph_rag_search')


@api_view(['POST'])
@permission_classes([IsAuthenticated, HasFeaturePermission.require('ai.rag')])
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
@permission_classes([IsAuthenticated, HasFeaturePermission.require('documents.upload')])
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
@permission_classes([IsAuthenticated, HasFeaturePermission.require('documents.upload')])
def upload_document_enhanced(request):
    """Enhanced document upload with automatic processing and metadata
    
    Optionally routes through unified upload queue if 'use_queue' parameter is True.
    Default behavior (use_queue=False) maintains backward compatibility.
    """
    try:
        BaseViewMixin.log_request(request, 'upload_document_enhanced')
        logger.info(f"Upload request received: method={request.method}, FILES keys={list(request.FILES.keys())}")
        
        if 'file' not in request.FILES:
            logger.warning("Upload request missing 'file' in request.FILES")
            return bad_request_response('No file provided')
        
        file = request.FILES['file']
        logger.info(f"File received: name={file.name}, size={file.size}, content_type={file.content_type}")
        
        # Optional: Route through unified upload queue
        use_queue = request.POST.get('use_queue', 'false').lower() == 'true'
        if use_queue:
            from ..service_classes.upload_queue_manager import upload_queue_manager
            from ..tasks import process_upload_job
            
            # Extract metadata
            product_category = request.POST.get('product_category', '')
            content_type = request.POST.get('content_type', '')
            version = request.POST.get('version', '')
            title = request.POST.get('title', file.name)
            description = request.POST.get('description', '')
            document_type = request.POST.get('document_type', 'pdf')
            priority = int(request.POST.get('priority', 5))
            
            metadata = {
                'product_category': product_category,
                'content_type': content_type,
                'version': version,
                'document_type': document_type,
                'title': title,
                'description': description
            }
            
            # Create job
            job = upload_queue_manager.add_job(
                job_type='file',
                source_path=file.name,
                source_files=[{
                    'name': file.name,
                    'size': file.size,
                    'type': file.content_type,
                    'file_object': file
                }],
                priority=priority,
                metadata=metadata,
                user=request.user
            )
            
            # Queue processing
            process_upload_job.delay(str(job.job_id))
            
            logger.info(f"File upload routed through queue: job_id={job.job_id}")
            return success_response(
                "File upload queued successfully",
                {
                    'job_id': str(job.job_id),
                    'status': job.status,
                    'message': 'File will be processed in the background'
                }
            )
        
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
        
        # Use standard rag_service (now has simplified upload method)
        logger.info(f"[VIEW] Calling rag_service.upload_document_enhanced for file: {file.name}")
        print(f"[VIEW] Starting upload for: {file.name}", flush=True)
        result = rag_service.upload_document_enhanced(file, request.user)
        print(f"[VIEW] Upload result: success={result.get('success')}", flush=True)
        logger.info(f"Upload result: success={result.get('success')}, message={result.get('message', 'N/A')}")
        print(f"[VIEW] Upload result: success={result.get('success')}")
        
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
                file_size=file.size,
                uploaded_file=uploaded_file  # Link to UploadedFile for processing status tracking
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
            result['data']['uploaded_file_id'] = uploaded_file.id if uploaded_file else None
            
            BaseViewMixin.log_response(result['data'], 'upload_document_enhanced')
            return success_response(result['message'], result['data'])
        
        else:
            logger.error(f"Upload failed: {result.get('message', 'Unknown error')}")
            return error_response(result['message'])
        
    except Exception as e:
        logger.error(f"Exception in upload_document_enhanced: {e}", exc_info=True)
        return BaseViewMixin.handle_error(e, 'upload_document_enhanced')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def retry_file_processing(request, file_id):
    """Retry background processing for an UploadedFile"""
    try:
        BaseViewMixin.log_request(request, 'retry_file_processing')
        uploaded_file = UploadedFile.objects.get(id=file_id)
        # reset state
        uploaded_file.processing_status = 'pending'
        uploaded_file.processing_error = None
        uploaded_file.metadata_extracted = False
        uploaded_file.chunks_created = False
        uploaded_file.embeddings_created = False
        uploaded_file.chunk_count = 0
        uploaded_file.embedding_count = 0
        uploaded_file.processing_started_at = None
        uploaded_file.processing_completed_at = None
        uploaded_file.save()

        # enqueue
        from ..tasks import process_file_automatically
        process_file_automatically.delay(uploaded_file.id)

        return success_response('Retry scheduled', {
            'uploaded_file_id': uploaded_file.id,
            'status': uploaded_file.processing_status
        })
    except UploadedFile.DoesNotExist:
        return bad_request_response('Uploaded file not found')
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'retry_file_processing')


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_uploaded_file(request, file_id):
    """Delete an UploadedFile and all associated data"""
    try:
        BaseViewMixin.log_request(request, 'delete_uploaded_file')
        from ai_assistant.models import DocumentChunk, DocumentFile, UploadedFile
        from django.core.files.storage import default_storage
        import os
        from django.conf import settings
        
        uploaded_file = UploadedFile.objects.get(id=file_id)
        filename = uploaded_file.filename
        
        # Check permission - user can only delete their own files unless admin
        if not request.user.is_staff and uploaded_file.uploaded_by != request.user:
            return error_response("Permission denied", status_code=status.HTTP_403_FORBIDDEN)
        
        # Delete associated chunks
        chunks_count = DocumentChunk.objects.filter(uploaded_file=uploaded_file).count()
        DocumentChunk.objects.filter(uploaded_file=uploaded_file).delete()
        
        # Delete associated DocumentFiles
        doc_files_count = DocumentFile.objects.filter(uploaded_file=uploaded_file).count()
        DocumentFile.objects.filter(uploaded_file=uploaded_file).delete()
        
        # Delete physical file if it exists (but always delete DB record regardless)
        file_deleted = False
        file_missing = False
        try:
            if default_storage.exists(filename):
                default_storage.delete(filename)
                file_deleted = True
                logger.info(f"Deleted physical file: {filename}")
            else:
                file_missing = True
                logger.warning(f"Physical file missing during deletion (ID: {uploaded_file.id}, filename: {filename}). Database record will still be deleted.")
        except Exception as e:
            file_missing = True
            logger.warning(f"Could not delete physical file {filename} (ID: {uploaded_file.id}): {e}. Database record will still be deleted.")
        
        # ALWAYS delete the UploadedFile record, even if physical file is missing
        # This prevents orphaned records that cause upload errors
        file_id = uploaded_file.id
        uploaded_file.delete()
        logger.info(f"Deleted UploadedFile record (ID: {file_id}) and all related data")
        
        return success_response("File deleted successfully", {
            'deleted_chunks': chunks_count,
            'deleted_document_files': doc_files_count,
            'file_deleted': file_deleted,
            'file_missing': file_missing
        })
        
    except UploadedFile.DoesNotExist:
        return error_response("Uploaded file not found", status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error deleting uploaded file {file_id}: {e}", exc_info=True)
        return BaseViewMixin.handle_error(e, 'delete_uploaded_file')


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
        import os
        
        doc = DocumentFile.objects.get(id=doc_id)
        
        # Try DocumentFile.file field first (legacy documents)
        if doc.file and hasattr(doc.file, 'path') and os.path.exists(doc.file.path):
            from django.http import FileResponse
            return FileResponse(open(doc.file.path, 'rb'))
        
        # For uploaded documents, file is stored via UploadedFile in media/uploads/
        if hasattr(doc, 'uploaded_file') and doc.uploaded_file:
            from django.http import FileResponse
            from django.conf import settings
            
            # uploaded_file.filename is stored as 'uploads/filename.ext'
            file_path = os.path.join(settings.MEDIA_ROOT, doc.uploaded_file.filename)
            
            if os.path.exists(file_path):
                return FileResponse(open(file_path, 'rb'))
        
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
        
        from ai_assistant.models import UploadedFile, DocumentChunk
        from django.core.files.storage import default_storage
        from django.conf import settings
        
        # Get the linked UploadedFile before deletion (if exists)
        linked_uploaded_file = doc.uploaded_file if hasattr(doc, 'uploaded_file') else None
        
        # Delete associated chunks - find via document_file or uploaded_file
        # First try via document_file (new way)
        chunks_via_doc = DocumentChunk.objects.filter(document_file=doc)
        chunks_count = chunks_via_doc.count()
        if chunks_via_doc.exists():
            chunks_via_doc.delete()
        
        # Also check for chunks via uploaded_file (legacy way)
        # Find UploadedFile that matches this document's filename
        uploaded_files = UploadedFile.objects.filter(filename=doc.filename)
        for uf in uploaded_files:
            chunks_via_uf = DocumentChunk.objects.filter(uploaded_file=uf)
            if chunks_via_uf.exists():
                chunks_via_uf.delete()
        
        # Delete physical file if exists (but always delete DB records regardless)
        file_deleted = False
        file_missing = False
        
        # Try DocumentFile.file field first (legacy documents)
        if doc.file and hasattr(doc.file, 'path'):
            try:
                if os.path.exists(doc.file.path):
                    os.remove(doc.file.path)
                    file_deleted = True
                    logger.info(f"Deleted physical file via DocumentFile.file: {doc.file.path}")
            except Exception as e:
                logger.warning(f"Could not delete physical file {doc.file.path}: {e}")
        
        # For uploaded documents, file is stored via UploadedFile in media/uploads/
        if not file_deleted and linked_uploaded_file:
            try:
                filename = linked_uploaded_file.filename
                if default_storage.exists(filename):
                    default_storage.delete(filename)
                    file_deleted = True
                    logger.info(f"Deleted physical file via UploadedFile: {filename}")
                else:
                    file_missing = True
                    logger.warning(f"Physical file missing during document deletion (UploadedFile ID: {linked_uploaded_file.id}, filename: {filename})")
            except Exception as e:
                file_missing = True
                logger.warning(f"Could not delete physical file for UploadedFile {linked_uploaded_file.id}: {e}")
        
        # Delete the DocumentFile record
        doc.delete()
        logger.info(f"Deleted DocumentFile record (ID: {doc_id})")
        
        # Clean up orphaned UploadedFile if it exists and has no other DocumentFiles
        # This prevents orphaned records that cause upload errors
        orphaned_cleaned = False
        if linked_uploaded_file:
            # Check if this UploadedFile has any other DocumentFiles
            remaining_doc_files = DocumentFile.objects.filter(uploaded_file=linked_uploaded_file).count()
            if remaining_doc_files == 0:
                # No other DocumentFiles reference this UploadedFile, safe to delete
                uploaded_file_id = linked_uploaded_file.id
                uploaded_filename = linked_uploaded_file.filename
                
                # Delete any remaining chunks
                remaining_chunks = DocumentChunk.objects.filter(uploaded_file=linked_uploaded_file).count()
                DocumentChunk.objects.filter(uploaded_file=linked_uploaded_file).delete()
                
                # Delete the orphaned UploadedFile
                linked_uploaded_file.delete()
                orphaned_cleaned = True
                logger.info(f"Cleaned up orphaned UploadedFile record (ID: {uploaded_file_id}, filename: {uploaded_filename}, chunks: {remaining_chunks})")
        
        return success_response("Document deleted successfully", {
            'deleted_chunks': chunks_count,
            'file_deleted': file_deleted,
            'file_missing': file_missing,
            'orphaned_uploaded_file_cleaned': orphaned_cleaned
        })
        
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
@permission_classes([AllowAny])  # Allow access, we'll check auth manually
def pdf_view(request, file_id):
    """
    View PDF document - serves the actual PDF file
    Supports both JWT token authentication (API) and session authentication (browser)
    """
    try:
        BaseViewMixin.log_request(request, 'pdf_view')
        
        # Manual authentication check - support both JWT and session
        authenticated = False
        
        # Method 1: Check JWT token (for API calls)
        from rest_framework_simplejwt.authentication import JWTAuthentication
        jwt_auth = JWTAuthentication()
        try:
            user, token = jwt_auth.authenticate(request)
            if user and user.is_authenticated:
                request.user = user
                authenticated = True
                logger.info(f"PDF view - JWT authentication successful for user {user.username}")
        except Exception as e:
            logger.debug(f"PDF view - JWT authentication failed: {e}")
        
        # Method 2: Check session authentication (for browser access)
        if not authenticated and hasattr(request, 'session'):
            try:
                # Django stores user ID in session with key '_auth_user_id'
                user_id = request.session.get('_auth_user_id')
                if user_id:
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    try:
                        user = User.objects.get(pk=user_id)
                        request.user = user
                        authenticated = True
                        logger.info(f"PDF view - Session authentication successful for user {user.username}")
                    except User.DoesNotExist:
                        logger.warning(f"PDF view - User {user_id} from session does not exist")
                    except Exception as e:
                        logger.error(f"PDF view - Error loading user from session: {e}")
                else:
                    logger.debug(f"PDF view - No _auth_user_id in session. Session keys: {list(request.session.keys())}")
            except Exception as e:
                logger.error(f"PDF view - Error checking session: {e}")
        
        # Method 3: Check if AuthenticationMiddleware already set request.user
        if not authenticated and hasattr(request, 'user') and request.user.is_authenticated:
            authenticated = True
            logger.info(f"PDF view - User already authenticated via middleware: {request.user.username}")
        
        # Final check - require authentication
        if not authenticated or not request.user.is_authenticated:
            # Log detailed debug info
            debug_info = {
                'has_session': hasattr(request, 'session'),
                'session_keys': list(request.session.keys()) if hasattr(request, 'session') else [],
                'has_user': hasattr(request, 'user'),
                'user_authenticated': getattr(request.user, 'is_authenticated', False) if hasattr(request, 'user') else False,
                'auth_header': request.META.get('HTTP_AUTHORIZATION', 'Not present'),
                'cookies': list(request.COOKIES.keys()) if hasattr(request, 'COOKIES') else [],
                'referer': request.META.get('HTTP_REFERER', 'Not present'),
            }
            logger.warning(f"PDF view - Authentication failed. Debug info: {debug_info}")
            return Response(
                {"detail": "Authentication credentials were not provided.", "debug": debug_info},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        uploaded_file = UploadedFile.objects.get(id=file_id)
        
        # Use the same file path resolution logic as processing
        from ai_assistant.utils.file_utils import get_file_path
        from django.http import FileResponse, HttpResponse
        import os
        
        file_path = get_file_path(uploaded_file)
        
        if not os.path.exists(file_path):
            return error_response(f"File not found: {uploaded_file.filename}")
        
        # Read the entire file into memory to ensure complete delivery
        # This prevents streaming issues that can cause blank pages
        with open(file_path, 'rb') as f:
            pdf_content = f.read()
        
        # Verify it's a valid PDF
        if not pdf_content.startswith(b'%PDF'):
            logger.error(f"File {file_id} does not appear to be a valid PDF")
            return error_response("Invalid PDF file")
        
        # Create HttpResponse with PDF content
        # Use HttpResponse instead of FileResponse to ensure complete delivery
        response = HttpResponse(pdf_content, content_type='application/pdf')
        
        # Set proper headers for PDF viewing
        filename = uploaded_file.filename.split("/")[-1] if "/" in uploaded_file.filename else uploaded_file.filename
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        response['Content-Length'] = str(len(pdf_content))
        
        # Add headers to prevent caching issues
        response['Cache-Control'] = 'public, max-age=3600'  # Cache for 1 hour
        response['Accept-Ranges'] = 'bytes'
        
        return response
        
    except UploadedFile.DoesNotExist:
        return error_response("File not found")
    except Exception as e:
        logger.error(f"Error serving PDF file {file_id}: {e}", exc_info=True)
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_file_processing_status(request, file_id):
    """
    Get processing status for a specific uploaded file
    
    Returns detailed processing status including:
    - Current processing stage
    - Completion flags (metadata, chunks, embeddings)
    - Progress metrics (chunk_count, embedding_count)
    - Error messages if failed
    - Timestamps
    """
    try:
        uploaded_file = UploadedFile.objects.get(id=file_id)
        
        # Check if user has permission (optional: verify ownership)
        # if uploaded_file.uploaded_by != request.user:
        #     return unauthorized_response('You do not have permission to view this file')
        
        # Calculate processing duration if started
        processing_duration = None
        if uploaded_file.processing_started_at:
            if uploaded_file.processing_completed_at:
                duration = uploaded_file.processing_completed_at - uploaded_file.processing_started_at
            else:
                duration = timezone.now() - uploaded_file.processing_started_at
            processing_duration = duration.total_seconds()
        
        status_data = {
            'id': uploaded_file.id,
            'filename': uploaded_file.filename,
            'file_size': uploaded_file.file_size,
            'processing_status': uploaded_file.processing_status,
            'metadata_extracted': uploaded_file.metadata_extracted,
            'chunks_created': uploaded_file.chunks_created,
            'embeddings_created': uploaded_file.embeddings_created,
            'chunk_count': uploaded_file.chunk_count,
            'embedding_count': uploaded_file.embedding_count,
            'is_ready': uploaded_file.is_ready_for_search(),
            'processing_error': uploaded_file.processing_error,
            'uploaded_at': uploaded_file.uploaded_at.isoformat() if uploaded_file.uploaded_at else None,
            'processing_started_at': uploaded_file.processing_started_at.isoformat() if uploaded_file.processing_started_at else None,
            'processing_completed_at': uploaded_file.processing_completed_at.isoformat() if uploaded_file.processing_completed_at else None,
            'processing_duration_seconds': processing_duration,
            'is_truncated': uploaded_file.is_truncated,
            'processing_coverage': uploaded_file.processing_coverage,
        }
        
        # Calculate progress percentage if processing
        if uploaded_file.processing_status in ['metadata_extracting', 'chunking', 'embedding']:
            stages_complete = sum([
                uploaded_file.metadata_extracted,
                uploaded_file.chunks_created,
                uploaded_file.embeddings_created
            ])
            status_data['progress_percentage'] = round((stages_complete / 3) * 100, 2)
        elif uploaded_file.processing_status == 'ready':
            status_data['progress_percentage'] = 100
        elif uploaded_file.processing_status == 'failed':
            status_data['progress_percentage'] = 0
        else:
            status_data['progress_percentage'] = 0
        
        return success_response("File status retrieved", status_data)
        
    except UploadedFile.DoesNotExist:
        return error_response('File not found', status_code=404)
    except Exception as e:
        logger.error(f"Error getting file status: {e}")
        return BaseViewMixin.handle_error(e, 'get_file_processing_status')

