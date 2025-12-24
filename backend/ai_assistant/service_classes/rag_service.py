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
        
        ollama_url = getattr(settings, 'OLLAMA_API_URL', 'http://localhost:11434')
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
        """Upload and process document file"""
        try:
            self.log_operation('upload_document_enhanced', {
                'file_name': file.name,
                'file_size': file.size
            })
            
            # Calculate file hash first for deduplication
            # Read file content into memory to calculate hash
            file_content = file.read()
            file_hash = hashlib.md5(file_content).hexdigest()
            
            # Check for duplicates BEFORE saving file
            existing_file = UploadedFile.objects.filter(file_hash=file_hash).first()
            if existing_file:
                # Verify the physical file exists; if missing, restore it and requeue processing
                try:
                    existing_path = existing_file.filename
                    if not existing_path.startswith('uploads/'):
                        existing_path = os.path.join('uploads', existing_path)
                    full_existing_path = os.path.join(settings.MEDIA_ROOT, existing_path)
                except Exception:
                    full_existing_path = None

                if not full_existing_path or not os.path.exists(full_existing_path):
                    # Save current file content to disk under a safe filename
                    uploads_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
                    os.makedirs(uploads_dir, exist_ok=True)

                    from django.core.files.storage import default_storage
                    original_filename = getattr(file, 'name', 'uploaded_file')
                    safe_filename = default_storage.get_valid_name(original_filename)
                    restore_path = os.path.join(uploads_dir, safe_filename)
                    base_name, ext = os.path.splitext(safe_filename)
                    counter = 1
                    while os.path.exists(restore_path):
                        safe_filename = f"{base_name}_{counter}{ext}"
                        restore_path = os.path.join(uploads_dir, safe_filename)
                        counter += 1

                    with open(restore_path, 'wb') as f:
                        f.write(file_content)

                    # Update DB record to point to restored file
                    existing_file.filename = os.path.join('uploads', safe_filename)
                    try:
                        existing_file.file_size = os.path.getsize(restore_path)
                    except Exception:
                        pass
                    existing_file.processing_status = 'pending'
                    existing_file.processing_error = ''
                    existing_file.save(update_fields=['filename', 'file_size', 'processing_status', 'processing_error'])

                    # Manually enqueue processing since post_save(created=False) won't trigger the signal
                    try:
                        from ai_assistant.tasks import process_file_automatically
                        process_file_automatically.delay(existing_file.id)
                    except Exception:
                        logger.warning("Could not enqueue processing task for restored file", exc_info=True)

                    return self.success_response("File restored and scheduled for processing", {
                        'uploaded_file_id': existing_file.id,
                        'filename': existing_file.filename,
                        'message': 'File was missing on disk and has been restored. Processing scheduled.'
                    })

                # Physical file exists; return existing record
                return self.success_response("File already exists", {
                    'uploaded_file_id': existing_file.id,
                    'filename': existing_file.filename,
                    'message': 'This file has already been uploaded'
                })
            
            # Save file to media/uploads directory so Celery can access it
            uploads_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)  # Create directory if it doesn't exist
            
            # Save file content directly to ensure it's written
            # FileSystemStorage might have issues with file pointer after read()
            from django.core.files.base import ContentFile
            from django.core.files.storage import default_storage
            
            # Generate unique filename if needed
            original_filename = file.name
            safe_filename = default_storage.get_valid_name(original_filename)
            file_path = os.path.join(uploads_dir, safe_filename)
            
            # Handle filename conflicts by adding suffix
            counter = 1
            base_name, ext = os.path.splitext(safe_filename)
            while os.path.exists(file_path):
                safe_filename = f"{base_name}_{counter}{ext}"
                file_path = os.path.join(uploads_dir, safe_filename)
                counter += 1
            
            # Write file content directly
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            relative_path = os.path.join('uploads', safe_filename)
            
            # Create UploadedFile record FIRST (before processing)
            # This will trigger the signal that queues Celery processing
            file_size = os.path.getsize(file_path)
            
            # Store the relative file path in filename so Celery can find it
            uploaded_file = UploadedFile.objects.create(
                filename=relative_path,  # Store relative path: 'uploads/filename.ext'
                file_hash=file_hash,
                file_size=file_size,
                uploaded_by=user,
                processing_status='pending'  # Start as pending, Celery will process
            )
            
            # Signal will automatically trigger process_file_automatically.delay()
            # Celery will process the file from media/uploads/ directory
            # File will stay there until processing is complete
            
            result = {
                'uploaded_file_id': uploaded_file.id,
                'filename': uploaded_file.filename,
                'file_size': uploaded_file.file_size,
                'status': 'pending',
                'message': 'File uploaded successfully. Processing will begin automatically.'
            }
            
            return self.success_response("Document uploaded successfully", result)
            
        except Exception as e:
            self.log_error('upload_document_enhanced', e)
            return self.error_response('Failed to upload and process document')
