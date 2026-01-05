"""
RAG Service Module

This module provides service layer for RAG (Retrieval-Augmented Generation)
operations including chat, search, and document processing.
"""

import logging
import hashlib
import time
import os
from typing import Dict, Any, List, Optional
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import requests

from .base_service import BaseService
from ..models import QueryHistory, UploadedFile
from ..rag_service import EnhancedRAGService
from ..improved_rag_service import enhanced_rag_service
from ..advanced_rag_service import advanced_rag_service
from ..comprehensive_rag_service import comprehensive_rag_service

logger = logging.getLogger(__name__)


class RAGService(BaseService):
    """Service for RAG operations"""
    
    def __init__(self):
        super().__init__()
        self.rag_service = EnhancedRAGService()
    
    def chat_with_ollama(self, prompt: str, user, **kwargs) -> Dict[str, Any]:
        """Generate chat response using Ollama"""
        try:
            self.log_operation('chat_with_ollama', {'prompt_length': len(prompt)})
            
            if not prompt.strip():
                return self.error_response('Prompt is required')
            
            # Check cache first
            prompt_hash = hashlib.md5(prompt.encode('utf-8')).hexdigest()
            cache_key = f"chat_response_{prompt_hash}"
            cached_response = self.get_cached_result(cache_key)
            
            if cached_response:
                return self.success_response("Chat response retrieved from cache", cached_response)
            
            # Generate response
            response_data = self._generate_ollama_response(prompt, **kwargs)
            
            # Cache response
            self.cache_result(cache_key, response_data, 1800)  # 30 minutes
            
            # Save to history
            QueryHistory.objects.create(
                query=prompt,
                response=response_data['response'],
                sources=[],
                query_type='chat',
                user=user
            )
            
            return self.success_response("Chat response generated successfully", response_data)
            
        except requests.exceptions.Timeout:
            self.log_error('chat_with_ollama', Exception("Request timeout"))
            return self.error_response(
                'Request timed out. The model is taking too long to respond.'
            )
        except Exception as e:
            self.log_error('chat_with_ollama', e)
            return self.error_response('Failed to generate chat response')
    
    def _generate_ollama_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate response using Ollama API"""
        # Get generation parameters
        max_tokens = kwargs.get('max_tokens', getattr(settings, 'OLLAMA_DEFAULT_MAX_TOKENS', 256))
        temperature = kwargs.get('temperature', getattr(settings, 'OLLAMA_TEMPERATURE', 0.3))
        top_p = kwargs.get('top_p', 0.9)
        top_k = kwargs.get('top_k', 40)
        repeat_penalty = kwargs.get('repeat_penalty', 1.1)
        num_ctx = kwargs.get('num_ctx', getattr(settings, 'OLLAMA_NUM_CTX', 1024))
        
        # Get language preference and select appropriate system prompt
        language = kwargs.get('language', 'en-US')
        if 'zh' in language.lower():
            system_prompt = getattr(settings, 'OLLAMA_SYSTEM_PROMPT_ZH', 
                                  '你是一个专业的实验室知识助手。请用简体中文回答所有问题。')
        else:
            system_prompt = getattr(settings, 'OLLAMA_SYSTEM_PROMPT_EN', 
                                  getattr(settings, 'OLLAMA_SYSTEM_PROMPT', 
                                        'You are a helpful, expert assistant.'))
        
        # Ollama configuration
        from ai_assistant.utils.model_settings import get_ollama_model
        model = get_ollama_model()
        
        # Validate model is set
        if not model:
            logger.error("Ollama model is not set! Please configure OLLAMA_MODEL in settings or via System Settings.")
            raise ValueError("Ollama model is not configured. Please set a model in System Settings.")
        
        ollama_url = getattr(settings, 'OLLAMA_API_URL', 'http://ollama:11434')
        timeout_seconds = getattr(settings, 'OLLAMA_REQUEST_TIMEOUT', 120)
        
        # Make API request
        api_url = f"{ollama_url}/api/chat"
        payload = {
            "model": model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
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
        
        try:
            logger.debug(f"Calling Ollama API: {api_url} with model: {model}")
            resp = requests.post(api_url, json=payload, timeout=timeout_seconds)
            resp.raise_for_status()
            
            response_data = resp.json()
            response_text = response_data.get("message", {}).get("content", "")
            
            if not response_text:
                logger.error(f"Empty response from Ollama. Response: {response_data}")
                raise ValueError("Empty response from Ollama API")
            
            return {
                'response': response_text,
                'model': model
            }
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.error(f"Ollama API endpoint not found (404). URL: {api_url}, Model: {model}. Check if Ollama is running and the URL is correct.")
                raise ValueError(f"Ollama API endpoint not found. Please check if Ollama is running at {ollama_url} and the model '{model}' exists.")
            else:
                logger.error(f"HTTP error from Ollama: {e.response.status_code} - {e.response.text}")
                raise
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Cannot connect to Ollama at {ollama_url}. Make sure Ollama is running.")
            raise ValueError(f"Cannot connect to Ollama at {ollama_url}. Please ensure Ollama is running.")
        except Exception as e:
            logger.error(f"Error calling Ollama API: {e}")
            raise
    
    def rag_search(self, query: str, user, search_mode: str = 'comprehensive', 
                  top_k: int = None, **kwargs) -> Dict[str, Any]:
        """Perform RAG search with performance monitoring"""
        start_time = time.time()
        
        try:
            self.log_operation('rag_search', {
                'query_length': len(query),
                'search_mode': search_mode
            })
            
            if not query.strip():
                return self.error_response('Query is required')
            
            # Extract language from kwargs
            language = kwargs.get('language', 'en-US')
            
            # Set default top_k based on search mode
            if top_k is None:
                top_k = 15 if search_mode == 'comprehensive' else 8
            
            # Perform search based on mode with language support
            search_start = time.time()
            if search_mode == 'comprehensive':
                result = comprehensive_rag_service.query_with_comprehensive_rag(query, top_k=top_k, user=user, language=language)
            elif search_mode == 'advanced':
                result = advanced_rag_service.query_with_advanced_rag(query, top_k=top_k, user=user, language=language)
            elif search_mode == 'enhanced':
                result = enhanced_rag_service.query_with_enhanced_rag(query, top_k=top_k, user=user, language=language)
            else:
                result = self.rag_service.query_with_rag(query, top_k=top_k, user=user, language=language)
            search_time = (time.time() - search_start) * 1000  # Convert to milliseconds
            
            total_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Add performance metrics to response
            if isinstance(result, dict):
                result['performance'] = {
                    'search_time_ms': search_time,
                    'total_time_ms': total_time,
                    'search_mode': search_mode,
                    'top_k': top_k
                }
            
            logger.info(f"RAG Search Performance - Mode: {search_mode}, Time: {total_time:.2f}ms, Top K: {top_k}")
            
            return self.success_response("RAG search completed successfully", result)
            
        except Exception as e:
            total_time = (time.time() - start_time) * 1000
            logger.error(f"RAG Search Error - Mode: {search_mode}, Time: {total_time:.2f}ms")
            self.log_error('rag_search', e)
            return self.error_response('Failed to perform RAG search')
    
    def vector_search(self, query: str, user=None, search_mode: str = 'comprehensive', 
                     top_k: int = None, **kwargs) -> Dict[str, Any]:
        """Perform vector similarity search with performance monitoring"""
        start_time = time.time()
        
        try:
            self.log_operation('vector_search', {
                'query_length': len(query),
                'search_mode': search_mode
            })
            
            if not query.strip():
                return self.error_response('Query is required')
            
            # Set default top_k based on search mode
            if top_k is None:
                top_k = 12 if search_mode == 'comprehensive' else 5
            
            # Search for relevant documents
            search_start = time.time()
            if search_mode == 'comprehensive':
                relevant_docs = comprehensive_rag_service.search_for_comprehensive_results(query, top_k)
            elif search_mode == 'advanced':
                relevant_docs = advanced_rag_service.search_with_hybrid_and_reranking(query, top_k)
            elif search_mode == 'enhanced':
                relevant_docs = enhanced_rag_service.search_relevant_documents_with_scoring(query, top_k)
            else:
                relevant_docs = self.rag_service.search_relevant_documents(query, top_k)
            search_time = (time.time() - search_start) * 1000
            
            total_time = (time.time() - start_time) * 1000
            
            # Add performance metrics
            response_data = {
                'documents': relevant_docs,
                'performance': {
                    'search_time_ms': search_time,
                    'total_time_ms': total_time,
                    'search_mode': search_mode,
                    'top_k': top_k,
                    'results_count': len(relevant_docs)
                }
            }
            
            logger.info(f"Vector Search Performance - Mode: {search_mode}, Time: {total_time:.2f}ms, Results: {len(relevant_docs)}")
            
            # Save to history if user is authenticated
            if user and user.is_authenticated:
                QueryHistory.objects.create(
                    query=query,
                    response=f"Found {len(relevant_docs)} relevant documents",
                    sources=relevant_docs,
                    query_type='vector',
                    user=user
                )
            
            return self.success_response("Vector search completed successfully", response_data)
            
        except Exception as e:
            total_time = (time.time() - start_time) * 1000
            logger.error(f"Vector Search Error - Mode: {search_mode}, Time: {total_time:.2f}ms")
            self.log_error('vector_search', e)
            return self.error_response('Failed to perform vector search')
    
    def upload_pdf_enhanced(self, file, user, **kwargs) -> Dict[str, Any]:
        """Upload and process PDF file"""
        try:
            self.log_operation('upload_pdf_enhanced', {
                'file_name': file.name,
                'file_size': file.size
            })
            
            if not file.name.lower().endswith('.pdf'):
                return self.error_response('Only PDF files are allowed')
            
            # Save file
            fs = FileSystemStorage()
            filename = fs.save(file.name, file)
            file_path = fs.path(filename)
            
            # Calculate file hash for deduplication
            file_hash = hashlib.md5(file.read()).hexdigest()
            file.seek(0)  # Reset file pointer
            
            # Check for duplicates
            existing_file = UploadedFile.objects.filter(file_hash=file_hash).first()
            if existing_file:
                fs.delete(filename)
                return self.success_response("File already exists", {
                    'file_id': existing_file.id,
                    'filename': existing_file.filename,
                    'message': 'This file has already been uploaded'
                })
            
            # Process PDF and build index
            result = self.rag_service.process_pdf_and_build_index(file_path, user)
            
            # Clean up temporary file
            fs.delete(filename)
            
            return self.success_response("PDF uploaded and processed successfully", result)
            
        except Exception as e:
            self.log_error('upload_pdf_enhanced', e)
            return self.error_response('Failed to upload and process PDF')
    
    def upload_document_enhanced(self, file, user, **kwargs) -> Dict[str, Any]:
        """
        SIMPLIFIED DOCKER-FIRST UPLOAD - COMPLETE REPLACEMENT
        
        This method has been completely rewritten with a simplified, Docker-first approach.
        Uses Django's storage API exclusively for reliable file saving in Docker.
        """
        import sys
        import os
        import hashlib
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile
        from django.conf import settings
        
        def log_upload(message, level='INFO'):
            """Force log to stdout for Docker visibility"""
            msg = f"[UPLOAD] {message}"
            print(msg, file=sys.stdout)
            sys.stdout.flush()
            if level == 'ERROR':
                logger.error(message)
            elif level == 'WARNING':
                logger.warning(message)
            else:
                logger.info(message)
        
        try:
            log_upload(f"=== UPLOAD START: {file.name} ({file.size} bytes) ===")
            
            # Step 1: Read file content
            log_upload(f"Reading file content...")
            if hasattr(file, 'seek'):
                file.seek(0)
            
            file_content = file.read()
            if not file_content or len(file_content) == 0:
                error_msg = "File content is empty"
                log_upload(f"ERROR: {error_msg}", 'ERROR')
                raise ValueError(error_msg)
            
            # Clean null bytes from text-based file content early
            # This prevents "string literal cannot contain NUL" errors during processing
            # CRITICAL: Only clean actual text files, NEVER modify binary files (PDFs, images, etc.)
            if isinstance(file_content, bytes):
                # Check file extension to determine if it's binary
                # Binary file extensions that should NEVER be modified
                binary_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', 
                                   '.zip', '.rar', '.7z', '.tar', '.gz', '.docx', '.xlsx', '.pptx',
                                   '.doc', '.xls', '.ppt', '.odt', '.ods', '.odp'}
                
                # Get file extension from filename
                file_ext = None
                if hasattr(file, 'name'):
                    from pathlib import Path
                    file_ext = Path(file.name).suffix.lower()
                
                # Only process if it's NOT a known binary file type
                if file_ext not in binary_extensions:
                    # Check if file appears to be text-based
                    # Only clean text files, preserve binary files
                    try:
                        # Try to decode as UTF-8 to check if it's text
                        text_content = file_content.decode('utf-8', errors='ignore')
                        # Additional check: if file has high ratio of null bytes, it's likely binary
                        null_ratio = file_content.count(b'\x00') / len(file_content) if len(file_content) > 0 else 0
                        # If it decodes successfully, has null bytes, but low null ratio (< 1%), clean them
                        if b'\x00' in file_content and null_ratio < 0.01:
                            log_upload(f"Cleaning null bytes from text file...")
                            cleaned_text = text_content.replace('\x00', '').replace('\0', '')
                            # Remove other problematic control characters (keep \n, \r, \t)
                            cleaned_text = ''.join(char for char in cleaned_text if ord(char) >= 32 or char in ['\n', '\r', '\t'])
                            file_content = cleaned_text.encode('utf-8')
                            log_upload(f"Cleaned null bytes from file content")
                        elif null_ratio >= 0.01:
                            # High null byte ratio indicates binary file - don't modify
                            log_upload(f"File has high null byte ratio ({null_ratio:.2%}), treating as binary - preserving original")
                    except (UnicodeDecodeError, AttributeError):
                        # Binary file - don't modify
                        # Null bytes in binary files are normal and should be preserved
                        pass
                else:
                    # Known binary file type - NEVER modify, preserve original
                    log_upload(f"Binary file type ({file_ext}) detected - preserving original content without modification")
            
            log_upload(f"File read: {len(file_content)} bytes")
            
            # Step 2: Calculate hash
            log_upload(f"Calculating hash...")
            file_hash = hashlib.md5(file_content).hexdigest()
            log_upload(f"Hash: {file_hash[:8]}...")
            
            # Step 3: Check for duplicates - Enhanced duplicate detection
            # First check by hash (most reliable)
            existing_file = UploadedFile.objects.filter(file_hash=file_hash).first()
            if existing_file:
                log_upload(f"Duplicate found by hash: ID={existing_file.id}, Status={existing_file.processing_status}")
                
                # Allow re-upload if existing file is corrupted or failed (no chunks/embeddings)
                from ai_assistant.models import DocumentChunk
                has_chunks = DocumentChunk.objects.filter(uploaded_file=existing_file).exists()
                
                # If file is corrupted/failed and has no chunks, allow re-upload by deleting old record
                if existing_file.processing_status in ['corrupted', 'failed', 'no_text_available'] and not has_chunks:
                    file_id = existing_file.id
                    log_upload(f"Existing file is {existing_file.processing_status} with no chunks - allowing re-upload by deleting old record")
                    # Delete the corrupted/failed record to allow fresh upload
                    existing_file.delete()
                    log_upload(f"Deleted corrupted/failed file record (ID: {file_id}) to allow re-upload")
                    existing_file = None  # Clear reference to continue with upload
                # Verify file exists on disk using storage API
                elif default_storage.exists(existing_file.filename):
                    log_upload(f"Duplicate file exists on disk, returning existing record")
                    status_msg = existing_file.processing_status
                    if status_msg == 'ready':
                        status_msg = 'processed and ready'
                    elif status_msg == 'processing':
                        status_msg = 'currently being processed'
                    elif status_msg == 'pending':
                        status_msg = 'pending processing'
                    else:
                        status_msg = f'status: {status_msg}'
                    
                    return self.success_response(
                        f"Same file already exists (ID: {existing_file.id}, {status_msg})",
                        {
                            'uploaded_file_id': existing_file.id,
                            'filename': existing_file.filename,
                            'message': f'This file has already been uploaded. File ID: {existing_file.id}, Status: {existing_file.processing_status}. Skipping duplicate upload.',
                            'is_duplicate': True,
                            'existing_status': existing_file.processing_status
                        }
                    )
                else:
                    log_upload(f"Duplicate record exists but file missing on disk - cleaning up orphaned record")
                    # OPTION A: Automatically delete the orphaned record and allow re-upload
                    # This prevents the "File record exists but physical file is missing" error
                    file_id = existing_file.id
                    filename = existing_file.filename
                    status = existing_file.processing_status
                    
                    # Count related records for logging
                    from ai_assistant.models import DocumentChunk, DocumentFile
                    chunks_count = DocumentChunk.objects.filter(uploaded_file=existing_file).count()
                    doc_files_count = DocumentFile.objects.filter(uploaded_file=existing_file).count()
                    
                    log_upload(f"Deleting orphaned record (ID: {file_id}): {chunks_count} chunks, {doc_files_count} document files")
                    
                    # Delete related records first
                    DocumentChunk.objects.filter(uploaded_file=existing_file).delete()
                    DocumentFile.objects.filter(uploaded_file=existing_file).delete()
                    
                    # Delete the orphaned UploadedFile record
                    existing_file.delete()
                    
                    log_upload(f"Deleted orphaned record (ID: {file_id}), allowing fresh upload")
                    existing_file = None  # Clear reference to continue with upload
            
            # Also check by filename (normalize _1, _2 suffixes) to catch re-uploads of same file
            # This helps when the same file is uploaded again but hash differs due to corruption
            original_filename = file.name
            safe_filename = default_storage.get_valid_name(original_filename)
            base_name, ext = os.path.splitext(safe_filename)
            
            # Check for existing files with same base name (ignoring _1, _2 suffixes)
            # Look for files that are already processed and working
            existing_by_name = UploadedFile.objects.filter(
                filename__startswith=f'uploads/{base_name}',
                filename__endswith=ext
            ).exclude(processing_status__in=['corrupted', 'failed']).order_by('-uploaded_at').first()
            
            if existing_by_name:
                # Check if existing file is significantly larger (likely complete)
                if existing_by_name.file_size > len(file_content) * 0.8:  # Existing is at least 80% of new file size
                    log_upload(f"Found existing working file by name: ID={existing_by_name.id}, size={existing_by_name.file_size}")
                    # Verify it exists and is working
                    if default_storage.exists(existing_by_name.filename):
                        status_msg = existing_by_name.processing_status
                        if status_msg == 'ready':
                            status_msg = 'processed and ready'
                        elif status_msg == 'processing':
                            status_msg = 'currently being processed'
                        elif status_msg == 'pending':
                            status_msg = 'pending processing'
                        else:
                            status_msg = f'status: {status_msg}'
                        
                        log_upload(f"Reusing existing working file instead of potentially corrupted upload")
                        return self.success_response(
                            f"Same file already exists (ID: {existing_by_name.id}, {status_msg})",
                            {
                                'uploaded_file_id': existing_by_name.id,
                                'filename': existing_by_name.filename,
                                'message': f'A working version of this file already exists. File ID: {existing_by_name.id}, Status: {existing_by_name.processing_status}. Skipping duplicate upload.',
                                'is_duplicate': True,
                                'existing_status': existing_by_name.processing_status
                            }
                        )
                    else:
                        # File missing but record exists - clean up orphaned record
                        log_upload(f"Found existing file by name but file missing on disk - cleaning up orphaned record")
                        from ai_assistant.models import DocumentChunk, DocumentFile
                        file_id = existing_by_name.id
                        chunks_count = DocumentChunk.objects.filter(uploaded_file=existing_by_name).count()
                        doc_files_count = DocumentFile.objects.filter(uploaded_file=existing_by_name).count()
                        
                        log_upload(f"Deleting orphaned record (ID: {file_id}): {chunks_count} chunks, {doc_files_count} document files")
                        DocumentChunk.objects.filter(uploaded_file=existing_by_name).delete()
                        DocumentFile.objects.filter(uploaded_file=existing_by_name).delete()
                        existing_by_name.delete()
                        log_upload(f"Deleted orphaned record (ID: {file_id}), allowing fresh upload")
            
            # Step 4: Save file using Django storage
            log_upload(f"Saving file to storage...")
            log_upload(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")
            
            # Generate safe filename
            original_filename = file.name
            safe_filename = default_storage.get_valid_name(original_filename)
            relative_path = f'uploads/{safe_filename}'
            
            # Handle filename conflicts
            counter = 1
            base_name, ext = os.path.splitext(safe_filename)
            while default_storage.exists(relative_path):
                safe_filename = f"{base_name}_{counter}{ext}"
                relative_path = f'uploads/{safe_filename}'
                counter += 1
                log_upload(f"Filename conflict, trying: {relative_path}")
            
            log_upload(f"Saving to: {relative_path}")
            
            # Track what we've created so we can clean up on failure
            saved_path = None
            uploaded_file = None
            
            try:
                # Store original file size for validation
                original_file_size = len(file_content)
                log_upload(f"Original file size: {original_file_size:,} bytes")
                
                # Save file - this is the critical step
                saved_path = default_storage.save(relative_path, ContentFile(file_content))
                log_upload(f"File saved: {saved_path}")
                
                # Quick verification
                if not default_storage.exists(saved_path):
                    error_msg = f"File save failed: {saved_path}"
                    log_upload(f"ERROR: {error_msg}", 'ERROR')
                    raise Exception(error_msg)
                
                file_size = default_storage.size(saved_path)
                log_upload(f"Saved file size: {file_size:,} bytes")
                
                # CRITICAL: Verify file size matches original (file integrity check)
                if file_size != original_file_size:
                    error_msg = (
                        f"File size mismatch detected! "
                        f"Original: {original_file_size:,} bytes, "
                        f"Saved: {file_size:,} bytes, "
                        f"Difference: {abs(file_size - original_file_size):,} bytes. "
                        f"File may have been corrupted during upload. Upload aborted."
                    )
                    log_upload(f"ERROR: {error_msg}", 'ERROR')
                    # Clean up the corrupted file
                    try:
                        default_storage.delete(saved_path)
                        log_upload(f"Deleted corrupted file: {saved_path}")
                    except Exception as cleanup_error:
                        log_upload(f"Warning: Failed to delete corrupted file: {cleanup_error}", 'WARNING')
                    raise Exception(error_msg)
                
                log_upload(f"✓ File size verified: {file_size:,} bytes (matches original)")
                
                # Step 5: Create DB record ONLY if file save succeeded
                # Use get_or_create to handle race conditions where duplicate might be created between check and create
                log_upload(f"Creating database record...")
                uploaded_file, created = UploadedFile.objects.get_or_create(
                    file_hash=file_hash,
                    defaults={
                        'filename': saved_path,  # Store relative path
                        'file_size': file_size,
                        'uploaded_by': user,
                        'processing_status': 'pending'
                    }
                )
                
                if not created:
                    # Record already exists (race condition or duplicate check missed it)
                    log_upload(f"Database record already exists (ID: {uploaded_file.id}), updating filename if needed")
                    # Update filename if it's different (in case file was saved with different path)
                    if uploaded_file.filename != saved_path and default_storage.exists(saved_path):
                        # Only update if new file exists and old one doesn't
                        if not default_storage.exists(uploaded_file.filename):
                            uploaded_file.filename = saved_path
                            uploaded_file.save(update_fields=['filename'])
                            log_upload(f"Updated filename to: {saved_path}")
                    # Return existing record - but clean up the file we just saved since it's a duplicate
                    if saved_path and default_storage.exists(saved_path):
                        try:
                            default_storage.delete(saved_path)
                            log_upload(f"Cleaned up duplicate file: {saved_path}")
                        except Exception as cleanup_error:
                            log_upload(f"Warning: Could not delete duplicate file {saved_path}: {cleanup_error}", 'WARNING')
                    
                    return self.success_response(
                        f"File already exists (ID: {uploaded_file.id})",
                        {
                            'uploaded_file_id': uploaded_file.id,
                            'filename': uploaded_file.filename,
                            'message': f'File already exists in database. File ID: {uploaded_file.id}, Status: {uploaded_file.processing_status}.',
                            'is_duplicate': True,
                            'existing_status': uploaded_file.processing_status
                        }
                    )
                
                log_upload(f"Database record created: ID={uploaded_file.id}")
                
                # Step 6: Final verification - if this fails, we need to clean up both file and DB record
                if not default_storage.exists(saved_path):
                    error_msg = f"File disappeared after DB creation: {saved_path}"
                    log_upload(f"ERROR: {error_msg}", 'ERROR')
                    # Clean up: Delete DB record (which frees the hash) and file
                    if uploaded_file:
                        uploaded_file.delete()
                        log_upload(f"Cleaned up DB record (ID: {uploaded_file.id}) to free hash value")
                    if saved_path and default_storage.exists(saved_path):
                        try:
                            default_storage.delete(saved_path)
                            log_upload(f"Cleaned up file: {saved_path}")
                        except Exception as cleanup_error:
                            log_upload(f"Warning: Could not delete file {saved_path}: {cleanup_error}", 'WARNING')
                    raise Exception(error_msg)
                
                log_upload(f"=== UPLOAD SUCCESS: ID={uploaded_file.id} ===")
                
                result = {
                    'uploaded_file_id': uploaded_file.id,
                    'filename': uploaded_file.filename,
                    'file_size': uploaded_file.file_size,
                    'status': 'pending',
                    'message': 'File uploaded successfully. Processing will begin automatically.'
                }
                
                return self.success_response("Document uploaded successfully", result)
                
            except Exception as inner_e:
                # Clean up on any error: Delete file and DB record if they were created
                error_msg = f"Upload failed: {str(inner_e)}"
                log_upload(f"ERROR: {error_msg}", 'ERROR')
                
                # Clean up DB record if it was created (this frees the hash value)
                if uploaded_file:
                    try:
                        uploaded_file.delete()
                        log_upload(f"Cleaned up DB record (ID: {uploaded_file.id}) to free hash value")
                    except Exception as cleanup_error:
                        log_upload(f"Warning: Could not delete DB record {uploaded_file.id}: {cleanup_error}", 'WARNING')
                
                # Clean up physical file if it was saved
                if saved_path and default_storage.exists(saved_path):
                    try:
                        default_storage.delete(saved_path)
                        log_upload(f"Cleaned up file: {saved_path}")
                    except Exception as cleanup_error:
                        log_upload(f"Warning: Could not delete file {saved_path}: {cleanup_error}", 'WARNING')
                
                # Re-raise the exception to be caught by outer handler
                raise
            
        except Exception as e:
            error_msg = f"Upload failed: {str(e)}"
            log_upload(f"ERROR: {error_msg}", 'ERROR')
            import traceback
            log_upload(f"Traceback:\n{traceback.format_exc()}", 'ERROR')
            logger.error(error_msg, exc_info=True)
            self.log_error('upload_document_enhanced', e)
            return self.error_response(f'Failed to upload document: {str(e)}')
