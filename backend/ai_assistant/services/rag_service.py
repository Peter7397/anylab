"""
RAG Service Module

This module provides service layer for RAG (Retrieval-Augmented Generation)
operations including chat, search, and document processing.
"""

import logging
import hashlib
import time
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
        
        # Ollama configuration
        model = getattr(settings, 'OLLAMA_MODEL', 'qwen2.5:latest')
        ollama_url = getattr(settings, 'OLLAMA_API_URL', 'http://localhost:11434')
        timeout_seconds = getattr(settings, 'OLLAMA_REQUEST_TIMEOUT', 120)
        
        # Make API request
        api_url = f"{ollama_url}/api/chat"
        payload = {
            "model": model,
            "stream": False,
            "messages": [
                {"role": "system", "content": getattr(settings, 'OLLAMA_SYSTEM_PROMPT', 'You are a helpful, expert assistant.')},
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
        return {
            'response': response_data["message"]["content"],
            'model': model
        }
    
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
            
            # Set default top_k based on search mode
            if top_k is None:
                top_k = 15 if search_mode == 'comprehensive' else 8
            
            # Perform search based on mode
            search_start = time.time()
            if search_mode == 'comprehensive':
                result = comprehensive_rag_service.query_with_comprehensive_rag(query, top_k=top_k, user=user)
            elif search_mode == 'advanced':
                result = advanced_rag_service.query_with_advanced_rag(query, top_k=top_k, user=user)
            elif search_mode == 'enhanced':
                result = enhanced_rag_service.query_with_enhanced_rag(query, top_k=top_k, user=user)
            else:
                result = self.rag_service.query_with_rag(query, top_k=top_k, user=user)
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
            
            # Process document based on file type
            file_extension = file.name.split('.')[-1].lower()
            
            # Process all document types - PDF, text, HTML/MHTML files all get processed for RAG
            if file_extension == 'pdf':
                result = self.rag_service.process_pdf_and_build_index(file_path, user)
            else:
                # Process text files, HTML, MHTML, and other formats
                # Pass the file object, file_path, and user
                result = self.rag_service.process_document_and_build_index(file, file_path, file_hash, user)
            
            # Clean up temporary file
            fs.delete(filename)
            
            return self.success_response("Document uploaded and processed successfully", result)
            
        except Exception as e:
            self.log_error('upload_document_enhanced', e)
            return self.error_response('Failed to upload and process document')
