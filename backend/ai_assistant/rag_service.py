import requests
import os
import fitz  # PyMuPDF
import hashlib
import numpy as np
from django.db import connection
from django.conf import settings
from django.core.cache import cache
from .models import DocumentFile, UploadedFile, DocumentChunk, QueryHistory
import logging
import json

logger = logging.getLogger(__name__)

class EnhancedRAGService:
    def __init__(self, model_name=None):
        self.model_name = model_name or getattr(settings, 'OLLAMA_MODEL', 'qwen2.5:latest')
        self.ollama_url = getattr(settings, 'OLLAMA_API_URL', 'http://ollama:11434')
        self.embedding_model = getattr(settings, 'EMBEDDING_MODEL', 'bge-m3')
        # Cache settings
        self.embedding_cache_ttl = getattr(settings, 'EMBEDDING_CACHE_TTL', 3600)  # 1 hour
        self.response_cache_ttl = getattr(settings, 'RESPONSE_CACHE_TTL', 1800)  # 30 minutes
        
    def get_embedding_from_ollama(self, text):
        """Get embedding from Ollama using the embedding model with caching"""
        # Create cache key based on text hash
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        cache_key = f"embedding_{text_hash}"
        
        # Try to get from cache first
        cached_embedding = cache.get(cache_key)
        if cached_embedding is not None:
            logger.info(f"Using cached embedding for text hash: {text_hash[:8]}...")
            return cached_embedding
        
        # Try BGE-M3 first, then fallback to nomic-embed-text
        models_to_try = ['bge-m3', 'nomic-embed-text']
        
        for model in models_to_try:
            try:
                response = requests.post(
                    f"{self.ollama_url}/api/embeddings",
                    json={
                        "model": model,
                        "prompt": text
                    },
                    timeout=15  # Reduced timeout for faster failure
                )
                response.raise_for_status()
                embedding = response.json()["embedding"]
                
                # Cache the embedding
                cache.set(cache_key, embedding, self.embedding_cache_ttl)
                logger.info(f"Successfully used {model} for embedding and cached it")
                return embedding
            except Exception as e:
                logger.warning(f"Failed to use {model} for embedding: {e}")
                continue
        
        # If all models fail, use fallback
        logger.warning("All embedding models failed, using fallback")
        fallback_embedding = self._simple_embedding_fallback(text)
        cache.set(cache_key, fallback_embedding, self.embedding_cache_ttl)
        return fallback_embedding
    
    def _simple_embedding_fallback(self, text):
        """Simple fallback embedding when Ollama embedding fails"""
        # Create a simple 384-dimensional embedding based on text hash
        import hashlib
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Convert hash to 384-dimensional vector
        embedding = []
        for i in range(384):
            embedding.append((hash_bytes[i % 16] / 255.0) * 2 - 1)
        
        return embedding

    def compute_file_hash(self, file_path):
        """Compute SHA256 hash of file for deduplication"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def compute_file_hash_from_upload(self, uploaded_file):
        """Compute SHA256 hash of uploaded file for deduplication"""
        sha256 = hashlib.sha256()
        uploaded_file.seek(0)  # Reset file pointer
        for chunk in uploaded_file.chunks():
            sha256.update(chunk)
        uploaded_file.seek(0)  # Reset file pointer again
        return sha256.hexdigest()

    def process_pdf_and_build_index(self, pdf_file, title=None, file_hash=None, request=None):
        """Process PDF file and build vector index using Ollama embeddings"""
        try:
            # Handle different file types
            if hasattr(pdf_file, 'temporary_file_path'):
                file_path = pdf_file.temporary_file_path()
            elif hasattr(pdf_file, 'path'):
                file_path = pdf_file.path
            else:
                # For InMemoryUploadedFile, save to temp file
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                    for chunk in pdf_file.chunks():
                        temp_file.write(chunk)
                    file_path = temp_file.name
            
            # Use provided file hash or compute it
            if file_hash is None:
                file_hash = self.compute_file_hash(file_path)
            
            # Check for duplicates
            if UploadedFile.objects.filter(file_hash=file_hash).exists():
                return {
                    'success': False,
                    'error': 'File already exists in database'
                }
            
            # Process PDF with PyMuPDF
            doc = None
            chunks = []
            vectors = []
            
            try:
                doc = fitz.open(file_path)
                for page_num, page in enumerate(doc, start=1):
                    text = page.get_text()
                    if text.strip():
                        # Generate embedding using Ollama
                        embedding = self.get_embedding_from_ollama(text)
                        chunks.append(text)
                        vectors.append(embedding)
            finally:
                if doc:
                    doc.close()
            
            # Create UploadedFile record
            uploaded_file = UploadedFile.objects.create(
                filename=title or pdf_file.name,
                file_hash=file_hash,
                file_size=os.path.getsize(file_path),
                page_count=len(chunks),
                intro=chunks[0][:200] if chunks else None,
                uploaded_by=request.user if hasattr(request, 'user') else None
            )
            
            # Store document chunks with embeddings
            for idx, (content, embedding) in enumerate(zip(chunks, vectors)):
                DocumentChunk.objects.create(
                    uploaded_file=uploaded_file,
                    content=content,
                    embedding=embedding,
                    page_number=idx + 1,
                    chunk_index=idx
                )
            
            doc.close()
            
            return {
                'success': True,
                'uploaded_file_id': uploaded_file.id,
                'chunks': chunks,
                'vectors': vectors,
                'page_count': len(doc)
            }
            
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def process_document_and_build_index(self, document_file, title=None, file_hash=None, request=None):
        """Process various document types and build vector index using Ollama embeddings"""
        try:
            # Handle different file types
            if hasattr(document_file, 'temporary_file_path'):
                file_path = document_file.temporary_file_path()
            elif hasattr(document_file, 'path'):
                file_path = document_file.path
            else:
                # For InMemoryUploadedFile, save to temp file
                import tempfile
                file_extension = document_file.name.split('.')[-1].lower() if '.' in document_file.name else 'pdf'
                with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as temp_file:
                    for chunk in document_file.chunks():
                        temp_file.write(chunk)
                    file_path = temp_file.name
            
            # Use provided file hash or compute it
            if file_hash is None:
                file_hash = self.compute_file_hash(file_path)
            
            # Check for duplicates
            if UploadedFile.objects.filter(file_hash=file_hash).exists():
                return {
                    'success': False,
                    'error': 'File already exists in database'
                }
            
            # Determine document type and process accordingly
            file_extension = document_file.name.split('.')[-1].lower() if '.' in document_file.name else 'pdf'
            chunks = []
            vectors = []
            
            if file_extension == 'pdf':
                # Process PDF with PyMuPDF
                doc = None
                try:
                    doc = fitz.open(file_path)
                    for page_num, page in enumerate(doc, start=1):
                        text = page.get_text()
                        if text.strip():
                            embedding = self.get_embedding_from_ollama(text)
                            chunks.append(text)
                            vectors.append(embedding)
                    page_count = len(doc)
                finally:
                    if doc:
                        doc.close()
                
            elif file_extension in ['txt', 'rtf']:
                # Process text files
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                    if text.strip():
                        embedding = self.get_embedding_from_ollama(text)
                        chunks.append(text)
                        vectors.append(embedding)
                page_count = 1
                
            else:
                # For other document types, just store basic info for now
                # TODO: Add support for Word, Excel, PowerPoint processing
                chunks = [f"Document: {title or document_file.name}"]
                vectors = [self.get_embedding_from_ollama(chunks[0])]
                page_count = 1
            
            # Create UploadedFile record
            uploaded_file = UploadedFile.objects.create(
                filename=title or document_file.name,
                file_hash=file_hash,
                file_size=os.path.getsize(file_path),
                page_count=page_count,
                intro=chunks[0][:200] if chunks else None,
                uploaded_by=request.user if request and hasattr(request, 'user') else None
            )
            
            # Store document chunks with embeddings
            for idx, (content, embedding) in enumerate(zip(chunks, vectors)):
                DocumentChunk.objects.create(
                    uploaded_file=uploaded_file,
                    content=content,
                    embedding=embedding,
                    page_number=idx + 1,
                    chunk_index=idx
                )
            
            return {
                'success': True,
                'uploaded_file_id': uploaded_file.id,
                'chunks': chunks,
                'vectors': vectors,
                'page_count': page_count
            }
            
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def search_relevant_documents(self, query, top_k=10):  # Increased from 8 to 10 for maximum comprehensive results
        """Search for relevant documents using vector similarity with Ollama embeddings and caching"""
        try:
            # Create cache key for search results
            query_hash = hashlib.md5(query.encode('utf-8')).hexdigest()
            cache_key = f"search_{query_hash}_{top_k}"
            
            # Try to get from cache first
            cached_results = cache.get(cache_key)
            if cached_results is not None:
                logger.info(f"Using cached search results for query: {query[:30]}...")
                return cached_results
            
            # Generate query embedding using Ollama
            query_embedding = self.get_embedding_from_ollama(query)
            
            # Search using pgvector with file information
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT dc.id, dc.content, dc.uploaded_file_id, dc.page_number, dc.chunk_index,
                           uf.filename, uf.file_hash, uf.file_size
                    FROM ai_assistant_documentchunk dc
                    LEFT JOIN ai_assistant_uploadedfile uf ON dc.uploaded_file_id = uf.id
                    ORDER BY dc.embedding <#> %s::vector
                    LIMIT %s;
                """, [query_embedding, top_k])
                results = cursor.fetchall()
            
            formatted_results = [
                {
                    "id": row[0], 
                    "content": row[1], 
                    "uploaded_file_id": row[2], 
                    "page_number": row[3],
                    "chunk_index": row[4],
                    "filename": row[5] or "Unknown Document",
                    "file_hash": row[6],
                    "file_size": row[7],
                    "download_url": f"/api/ai/documents/{row[2]}/download/" if row[2] else None
                } for row in results
            ]
            
            # Cache the results
            cache.set(cache_key, formatted_results, self.response_cache_ttl)
            logger.info(f"Cached search results for query: {query[:30]}...")
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []

    def ollama_generate(self, prompt, model=None):
        """Generate response using Ollama with caching"""
        if model is None:
            model = self.model_name
            
        # Create cache key for response
        prompt_hash = hashlib.md5(prompt.encode('utf-8')).hexdigest()
        cache_key = f"response_{prompt_hash}"
        
        # Try to get from cache first
        cached_response = cache.get(cache_key)
        if cached_response is not None:
            logger.info(f"Using cached response for prompt hash: {prompt_hash[:8]}...")
            return cached_response
            
        try:
            response = requests.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant. Use only the following context to answer the question. Be concise and accurate."},
                        {"role": "user", "content": prompt}
                    ],
                    "stream": False,
                    "options": {
                        "num_predict": 768,  # Increased from 512 for maximum comprehensive responses
                        "temperature": 0.3,  # Lower temperature for more focused responses
                        "top_p": 0.9,
                        "top_k": 40,
                        "repeat_penalty": 1.1,
                        "num_ctx": 4096  # Increased from 2048 for maximum context
                    }
                },
                timeout=getattr(settings, 'OLLAMA_REQUEST_TIMEOUT', 120)  # Reduced timeout
            )
            response.raise_for_status()
            response_text = response.json()["message"]["content"]
            
            # Cache the response
            cache.set(cache_key, response_text, self.response_cache_ttl)
            logger.info(f"Cached response for prompt hash: {prompt_hash[:8]}...")
            
            return response_text
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise

    def generate_response(self, query, context_documents):
        """Generate response with proper context handling - optimized for maximum comprehensive answers"""
        if not context_documents:
            return "I don't know."
        
        # Build context with reference numbers - use all 10 documents for maximum comprehensive responses
        context_lines = []
        for idx, doc in enumerate(context_documents[:10], 1):  # Increased from 6 to 10 documents
            # Truncate long content to avoid token limits but allow more content
            content = doc['content'][:600] if len(doc['content']) > 600 else doc['content']  # Keep 600 chars per document
            similarity = doc.get('similarity', 0)
            context_lines.append(f"[{idx}] (Similarity: {similarity:.3f})\n{content}")
        
        context = "\n\n".join(context_lines)
        
        # Improved RAG prompt that ensures context-only responses with proper citations
        prompt = (
            "You are a helpful assistant.\n"
            "Answer the user's question ONLY using the provided context below.\n"
            "Cite all information derived from the context using bracketed reference numbers (e.g., [1], or multiple [1][3]).\n"
            "If the requested information is not found in the context, respond directly with: \"I don't know.\"\n"
            "Do not use your internal knowledge base or common sense to answer questions.\n"
            "Provide comprehensive answers using all relevant information from the context.\n"
            "If multiple sources contain relevant information, synthesize them into a complete response.\n"
            "Use as many relevant sources as possible to provide a thorough answer.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {query}\n\n"
            "Answer:"
        )
        
        return self.ollama_generate(prompt)

    def query_with_rag(self, query, top_k=10, user=None):  # Increased from 8 to 10
        """Main RAG pipeline with caching"""
        try:
            # Create cache key for entire RAG query
            query_hash = hashlib.md5(query.encode('utf-8')).hexdigest()
            cache_key = f"rag_query_{query_hash}_{top_k}"
            
            # Try to get from cache first
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.info(f"Using cached RAG result for query: {query[:30]}...")
                return cached_result
            
            # Search for relevant documents
            relevant_docs = self.search_relevant_documents(query, top_k)
            
            if not relevant_docs:
                response = "I don't know."
                result = {
                    "response": response,
                    "sources": [],
                    "query": query
                }
            else:
                # Generate response
                response = self.generate_response(query, relevant_docs)
                result = {
                    "response": response,
                    "sources": relevant_docs,
                    "query": query
                }
            
            # Cache the result
            cache.set(cache_key, result, self.response_cache_ttl)
            logger.info(f"Cached RAG result for query: {query[:30]}...")
            
            # Save to history
            if user:
                QueryHistory.objects.create(
                    query=query,
                    response=response,
                    sources=relevant_docs,
                    query_type='rag',
                    user=user
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in RAG query: {e}")
            return {
                "response": f"Error processing query: {str(e)}",
                "sources": [],
                "query": query
            }

    def get_index_info(self):
        """Get information about the vector index"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM ai_assistant_documentchunk")
                doc_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM ai_assistant_uploadedfile")
                file_count = cursor.fetchone()[0]
            
            return {
                "document_chunks": doc_count,
                "uploaded_files": file_count,
                "embedding_model": f"Ollama ({self.embedding_model})"
            }
        except Exception as e:
            logger.error(f"Error getting index info: {e}")
            return {"error": str(e)}

# Global instance
rag_service = EnhancedRAGService()
