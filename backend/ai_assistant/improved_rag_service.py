"""
Improved RAG Service with enhanced chunking and similarity scoring
"""
import requests
import os
import fitz  # PyMuPDF
import hashlib
import numpy as np
from django.db import connection
from django.conf import settings
from django.core.cache import cache
from .models import DocumentFile, UploadedFile, DocumentChunk, QueryHistory
from .enhanced_chunking import semantic_chunker, advanced_chunker
import logging
import json

logger = logging.getLogger(__name__)

class ImprovedRAGService:
    """Enhanced RAG service with better chunking and similarity scoring"""
    
    def __init__(self, model_name=None):
        self.model_name = model_name or getattr(settings, 'OLLAMA_MODEL', 'qwen2.5:latest')
        self.ollama_url = getattr(settings, 'OLLAMA_API_URL', 'http://ollama:11434')
        self.embedding_model = getattr(settings, 'EMBEDDING_MODEL', 'bge-m3')
        
        # Enhanced cache settings
        self.embedding_cache_ttl = getattr(settings, 'EMBEDDING_CACHE_TTL', 24 * 3600)  # 24 hours
        self.search_cache_ttl = getattr(settings, 'SEARCH_CACHE_TTL', 3600)  # 1 hour
        self.response_cache_ttl = getattr(settings, 'RESPONSE_CACHE_TTL', 1800)  # 30 minutes
        
        # Search quality settings
        self.similarity_threshold = 0.5  # Only return relevant results (adjusted for better recall)
        self.top_k_candidates = 20       # Retrieve more candidates
        self.final_top_k = 8            # Return best results
        
        # Use advanced chunker by default
        self.chunker = advanced_chunker
        
    def get_embedding_from_ollama(self, text):
        """Get embedding from Ollama with improved caching"""
        # Create cache key based on text hash and model
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        cache_key = f"embedding_{self.embedding_model}_{text_hash}"
        
        # Try to get from cache first
        cached_embedding = cache.get(cache_key)
        if cached_embedding is not None:
            logger.debug(f"Using cached embedding for text hash: {text_hash[:8]}...")
            return cached_embedding
        
        # Try BGE-M3 first (only use models that generate 1024 dimensions)
        models_to_try = ['bge-m3']
        
        for model in models_to_try:
            try:
                response = requests.post(
                    f"{self.ollama_url}/api/embeddings",
                    json={
                        "model": model,
                        "prompt": text
                    },
                    timeout=15
                )
                response.raise_for_status()
                embedding = response.json()["embedding"]
                
                # Ensure embedding has correct dimensions (1024)
                if len(embedding) != 1024:
                    logger.warning(f"Model {model} generated {len(embedding)} dimensions, expected 1024. Skipping.")
                    continue
                
                # Cache the embedding for longer (24 hours)
                cache.set(cache_key, embedding, self.embedding_cache_ttl)
                logger.debug(f"Successfully used {model} for embedding and cached it")
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
        # Create a simple 1024-dimensional embedding based on text hash
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Convert hash to 1024-dimensional vector (BGE-M3 dimensions)
        embedding = []
        for i in range(1024):
            embedding.append((hash_bytes[i % 16] / 255.0) * 2 - 1)
        
        return embedding
    
    def compute_file_hash(self, file_path):
        """Compute SHA256 hash of file for deduplication"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def process_document_with_enhanced_chunking(self, document_file, title=None, file_hash=None, request=None):
        """Process document with enhanced semantic chunking"""
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
            
            # Extract text based on file type
            file_extension = document_file.name.split('.')[-1].lower() if '.' in document_file.name else 'pdf'
            page_texts = []
            
            if file_extension == 'pdf':
                # Process PDF with PyMuPDF
                doc = None
                try:
                    doc = fitz.open(file_path)
                    for page_num, page in enumerate(doc, start=1):
                        text = page.get_text()
                        if text.strip():
                            page_texts.append(text)
                    total_pages = len(doc)
                finally:
                    if doc:
                        doc.close()
                        
            elif file_extension in ['txt', 'rtf']:
                # Process text files
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                    if text.strip():
                        page_texts.append(text)
                total_pages = 1
            else:
                # For other document types, basic handling
                page_texts = [f"Document: {title or document_file.name}"]
                total_pages = 1
            
            if not page_texts:
                return {
                    'success': False,
                    'error': 'No text content found in document'
                }
            
            # Enhanced chunking with semantic awareness
            text_chunks = self.chunker.chunk_document_pages(page_texts)
            
            if not text_chunks:
                return {
                    'success': False,
                    'error': 'No valid chunks created from document'
                }
            
            # Create UploadedFile record
            uploaded_file = UploadedFile.objects.create(
                filename=title or document_file.name,
                file_hash=file_hash,
                file_size=os.path.getsize(file_path),
                page_count=total_pages,
                intro=text_chunks[0].content[:200] if text_chunks else None,
                uploaded_by=request.user if request and hasattr(request, 'user') else None
            )
            
            # Store document chunks with embeddings
            chunk_data = []
            for text_chunk in text_chunks:
                try:
                    # Generate embedding for this chunk
                    embedding = self.get_embedding_from_ollama(text_chunk.content)
                    
                    # Create DocumentChunk
                    doc_chunk = DocumentChunk.objects.create(
                        uploaded_file=uploaded_file,
                        content=text_chunk.content,
                        embedding=embedding,
                        page_number=text_chunk.page_number,
                        chunk_index=text_chunk.chunk_index
                    )
                    
                    chunk_data.append({
                        'content': text_chunk.content,
                        'page_number': text_chunk.page_number,
                        'chunk_index': text_chunk.chunk_index,
                        'section_title': text_chunk.section_title
                    })
                    
                except Exception as e:
                    logger.error(f"Error creating chunk {text_chunk.chunk_index}: {e}")
                    continue
            
            logger.info(f"Successfully processed document with {len(chunk_data)} chunks")
            
            return {
                'success': True,
                'uploaded_file_id': uploaded_file.id,
                'chunks': chunk_data,
                'total_chunks': len(chunk_data),
                'page_count': total_pages
            }
            
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def search_relevant_documents_with_scoring(self, query, top_k=None):
        """Enhanced search with similarity scoring and filtering"""
        if top_k is None:
            top_k = self.final_top_k
            
        try:
            # Create cache key for search results
            query_hash = hashlib.md5(query.encode('utf-8')).hexdigest()
            cache_key = f"search_scored_{query_hash}_{top_k}_{self.similarity_threshold}"
            
            # Try to get from cache first
            cached_results = cache.get(cache_key)
            if cached_results is not None:
                logger.info(f"Using cached search results for query: {query[:30]}...")
                return cached_results
            
            # Generate query embedding
            query_embedding = self.get_embedding_from_ollama(query)
            
            # Search using pgvector with more candidates
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT dc.id, dc.content, dc.uploaded_file_id, dc.page_number, dc.chunk_index,
                           COALESCE(uf.filename, 'Unknown Document') as filename,
                           COALESCE(uf.file_hash, '') as file_hash, 
                           COALESCE(uf.file_size, 0) as file_size,
                           1 - (dc.embedding <=> %s::vector) as similarity
                    FROM ai_assistant_documentchunk dc
                    LEFT JOIN ai_assistant_uploadedfile uf ON dc.uploaded_file_id = uf.id
                    WHERE dc.embedding IS NOT NULL
                    ORDER BY dc.embedding <=> %s::vector
                    LIMIT %s;
                """, [query_embedding, query_embedding, self.top_k_candidates])
                results = cursor.fetchall()
            
            # Filter by similarity threshold and format results
            filtered_results = []
            for row in results:
                similarity = float(row[8])
                
                # Only include results above threshold
                if similarity >= self.similarity_threshold:
                    uploaded_file_id = row[2]
                    page_number = row[3] or 1
                    filename = row[5] or "Unknown Document"
                    content = row[1]
                    
                    # Generate title: use filename if valid, otherwise extract from content
                    if filename and filename != "Unknown Document":
                        title = filename
                    else:
                        # Extract first meaningful words from content as title
                        words = content.split()[:10]  # First 10 words
                        title = " ".join(words)
                        if len(title) > 100:
                            title = title[:100] + "..."
                    
                    # Create view URL for PDF viewer if uploaded_file_id exists
                    view_url = None
                    if uploaded_file_id:
                        view_url = f"/api/ai/pdf/{uploaded_file_id}/view/?page={page_number}"
                    
                    filtered_results.append({
                        "id": row[0],
                        "content": content,
                        "uploaded_file_id": uploaded_file_id,
                        "page_number": page_number,
                        "chunk_index": row[4],
                        "filename": filename,
                        "title": title,  # Smart title: filename or content excerpt
                        "file_hash": row[6],
                        "file_size": row[7],
                        "similarity": similarity,
                        "download_url": f"/api/ai/documents/{uploaded_file_id}/download/" if uploaded_file_id else None,
                        "view_url": view_url,  # URL to open PDF at specific page
                        "source_display": f"{filename} (Page {page_number})" if filename != "Unknown Document" else f"Page {page_number}"
                    })
            
            # Sort by similarity (highest first) and limit to top_k
            filtered_results.sort(key=lambda x: x['similarity'], reverse=True)
            final_results = filtered_results[:top_k]
            
            # Cache the results
            cache.set(cache_key, final_results, self.search_cache_ttl)
            logger.info(f"Found {len(final_results)} relevant results (threshold: {self.similarity_threshold})")
            
            return final_results
            
        except Exception as e:
            logger.error(f"Error in enhanced vector search: {e}")
            return []
    
    def generate_enhanced_response(self, query, context_documents):
        """Generate response with improved context handling"""
        if not context_documents:
            return "I don't know."
        
        # Build context with similarity scores and better formatting
        context_lines = []
        for idx, doc in enumerate(context_documents, 1):
            similarity = doc.get('similarity', 0)
            content = doc['content']
            filename = doc.get('filename', 'Unknown')
            page = doc.get('page_number', 1)
            
            # Truncate content but keep more for better context
            if len(content) > 800:
                content = content[:800] + "..."
            
            context_lines.append(
                f"[{idx}] {filename} (Page {page}, Similarity: {similarity:.3f})\n{content}"
            )
        
        context = "\n\n".join(context_lines)
        
        # Enhanced prompt with better instructions
        prompt = (
            "You are an expert assistant. Answer the user's question using ONLY the provided context.\n"
            "IMPORTANT RULES:\n"
            "1. Use ONLY information from the context below - do not use external knowledge\n"
            "2. Cite sources using reference numbers [1], [2], etc.\n"
            "3. If information is not in the context, say 'I don't know'\n"
            "4. Provide comprehensive answers using all relevant sources\n"
            "5. Mention similarity scores when information quality varies\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {query}\n\n"
            "Answer:"
        )
        
        return self.ollama_generate(prompt)
    
    def ollama_generate(self, prompt, model=None):
        """Generate response using Ollama with enhanced caching"""
        if model is None:
            model = self.model_name
            
        # Create cache key for response
        prompt_hash = hashlib.md5(prompt.encode('utf-8')).hexdigest()
        cache_key = f"response_{model}_{prompt_hash}"
        
        # Try to get from cache first
        cached_response = cache.get(cache_key)
        if cached_response is not None:
            logger.debug(f"Using cached response for prompt hash: {prompt_hash[:8]}...")
            return cached_response
            
        try:
            response = requests.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "stream": False,
                    "options": {
                        "num_predict": 1024,      # Increased for comprehensive responses
                        "temperature": 0.2,       # Lower for more focused responses
                        "top_p": 0.9,
                        "top_k": 40,
                        "repeat_penalty": 1.1,
                        "num_ctx": 4096          # Increased context window
                    }
                },
                timeout=getattr(settings, 'OLLAMA_REQUEST_TIMEOUT', 120)
            )
            response.raise_for_status()
            response_text = response.json()["message"]["content"]
            
            # Cache the response
            cache.set(cache_key, response_text, self.response_cache_ttl)
            logger.debug(f"Cached response for prompt hash: {prompt_hash[:8]}...")
            
            return response_text
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    def query_with_enhanced_rag(self, query, top_k=None, user=None):
        """Enhanced RAG pipeline with scoring and better caching"""
        if top_k is None:
            top_k = self.final_top_k
            
        try:
            # Create cache key for entire RAG query
            query_hash = hashlib.md5(query.encode('utf-8')).hexdigest()
            cache_key = f"enhanced_rag_{query_hash}_{top_k}_{self.similarity_threshold}"
            
            # Try to get from cache first
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.info(f"Using cached enhanced RAG result for query: {query[:30]}...")
                return cached_result
            
            # Search for relevant documents with scoring
            relevant_docs = self.search_relevant_documents_with_scoring(query, top_k)
            
            if not relevant_docs:
                response = "I don't know."
                result = {
                    "response": response,
                    "sources": [],
                    "query": query,
                    "search_stats": {
                        "total_candidates": 0,
                        "filtered_results": 0,
                        "similarity_threshold": self.similarity_threshold
                    }
                }
            else:
                # Generate enhanced response
                response = self.generate_enhanced_response(query, relevant_docs)
                result = {
                    "response": response,
                    "sources": relevant_docs,
                    "query": query,
                    "search_stats": {
                        "total_candidates": self.top_k_candidates,
                        "filtered_results": len(relevant_docs),
                        "similarity_threshold": self.similarity_threshold,
                        "avg_similarity": sum(doc['similarity'] for doc in relevant_docs) / len(relevant_docs)
                    }
                }
            
            # Cache the result
            cache.set(cache_key, result, self.response_cache_ttl)
            logger.info(f"Enhanced RAG complete: {len(relevant_docs)} sources, avg similarity: {result['search_stats'].get('avg_similarity', 0):.3f}")
            
            # Save to history
            if user:
                QueryHistory.objects.create(
                    query=query,
                    response=response,
                    sources=relevant_docs,
                    query_type='enhanced_rag',
                    user=user
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in enhanced RAG query: {e}")
            return {
                "response": f"Error processing query: {str(e)}",
                "sources": [],
                "query": query,
                "search_stats": {"error": str(e)}
            }

# Global enhanced RAG service instance
enhanced_rag_service = ImprovedRAGService()
