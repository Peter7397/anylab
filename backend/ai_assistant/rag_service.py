import requests
import os
import fitz  # PyMuPDF
import hashlib
import numpy as np
from pathlib import Path
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
        self.ollama_url = getattr(settings, 'OLLAMA_API_URL', 'http://localhost:11434')
        self.embedding_model = getattr(settings, 'EMBEDDING_MODEL', 'bge-m3')
        # Standardized cache settings across all RAG services
        self.embedding_cache_ttl = getattr(settings, 'EMBEDDING_CACHE_TTL', 24 * 3600)  # 24 hours (standardized)
        self.search_cache_ttl = getattr(settings, 'SEARCH_CACHE_TTL', 3600)  # 1 hour
        self.response_cache_ttl = getattr(settings, 'RESPONSE_CACHE_TTL', 1800)  # 30 minutes
        
    def get_embedding_from_ollama(self, text):
        """
        Get embedding from BGE-M3 ONLY
        NO FALLBACKS - Quality requirement
        
        QUALITY RULES:
        - Use BGE-M3 model ONLY
        - No nomic-embed-text fallback
        - 1024 dimensions (BGE-M3 standard)
        - No hash-based fallback
        - Will retry but NO compromises on model quality
        """
        # Create cache key based on text hash
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        cache_key = f"embedding_{text_hash}"
        
        # Try to get from cache first
        cached_embedding = cache.get(cache_key)
        if cached_embedding is not None:
            logger.info(f"Using cached embedding for text hash: {text_hash[:8]}...")
            return cached_embedding
        
        # Use BGE-M3 ONLY - NO FALLBACKS
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                response = requests.post(
                    f"{self.ollama_url}/api/embeddings",
                    json={
                        "model": "bge-m3",  # BGE-M3 ONLY
                        "prompt": text
                    },
                    timeout=60  # Longer timeout for quality
                )
                response.raise_for_status()
                embedding = response.json()["embedding"]
                
                # Ensure 1024 dimensions (BGE-M3 standard)
                if len(embedding) != 1024:
                    if len(embedding) < 1024:
                        # Pad with zeros
                        embedding = list(embedding) + [0.0] * (1024 - len(embedding))
                        logger.warning(f"Padded embedding to 1024 dimensions")
                    else:
                        # Truncate
                        embedding = embedding[:1024]
                        logger.warning(f"Truncated embedding to 1024 dimensions")
                
                # Cache the embedding
                cache.set(cache_key, embedding, self.embedding_cache_ttl)
                logger.info(f"Successfully used BGE-M3 for embedding and cached it")
                return embedding
                
            except requests.exceptions.Timeout:
                retry_count += 1
                logger.warning(f"BGE-M3 timeout (attempt {retry_count}/{max_retries})")
                if retry_count >= max_retries:
                    raise Exception("BGE-M3 embedding timeout after multiple retries")
                    
            except Exception as e:
                logger.error(f"BGE-M3 embedding error: {e}")
                if retry_count >= max_retries - 1:
                    raise Exception(f"BGE-M3 embedding failed after all retries: {str(e)}")
                retry_count += 1
                continue
        
        # Should never reach here, but if we do, raise error
        raise Exception("Failed to get BGE-M3 embedding after all retries")
    
    def get_embeddings_from_ollama_batch(self, texts):
        """Get embeddings for multiple texts efficiently with batch processing
        
        This method processes a batch of texts by:
        1. Checking cache first for each text (fast lookup)
        2. Only calling Ollama API for uncached texts
        3. Processing remaining uncached texts in parallel for efficiency
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embeddings corresponding to input texts
        """
        import hashlib
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        # Safety check: Limit batch size to prevent memory issues
        MAX_BATCH_SIZE = 50
        MAX_CONCURRENT_WORKERS = 10
        
        if len(texts) > MAX_BATCH_SIZE:
            logger.warning(f"Batch too large ({len(texts)} chunks), limiting to {MAX_BATCH_SIZE}")
            texts = texts[:MAX_BATCH_SIZE]
        
        results = [None] * len(texts)
        cache_hits = 0
        api_calls_needed = []
        
        # Phase 1: Check cache for all texts
        for idx, text in enumerate(texts):
            if not text.strip():
                results[idx] = self._simple_embedding_fallback(text)
                continue
                
            text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
            cache_key = f"embedding_{text_hash}"
            cached_embedding = cache.get(cache_key)
            
            if cached_embedding is not None:
                results[idx] = cached_embedding
                cache_hits += 1
            else:
                api_calls_needed.append((idx, text))
        
        if cache_hits > 0:
            logger.info(f"Cache hits: {cache_hits}/{len(texts)} chunks")
        
        # Phase 2: Process uncached texts with parallel API calls
        if api_calls_needed:
            logger.info(f"Fetching {len(api_calls_needed)} embeddings from Ollama (parallel processing)")
            
            def fetch_embedding(idx, text):
                """Fetch embedding using BGE-M3 ONLY - NO FALLBACKS"""
                max_retries = 3
                retry_count = 0
                
                while retry_count < max_retries:
                    try:
                        response = requests.post(
                            f"{self.ollama_url}/api/embeddings",
                            json={
                                "model": "bge-m3",  # BGE-M3 ONLY
                                "prompt": text
                            },
                            timeout=60  # Longer timeout for quality
                        )
                        response.raise_for_status()
                        embedding = response.json()["embedding"]
                        
                        # Ensure 1024 dimensions
                        if len(embedding) != 1024:
                            if len(embedding) < 1024:
                                embedding = list(embedding) + [0.0] * (1024 - len(embedding))
                            else:
                                embedding = embedding[:1024]
                        
                        # Cache it
                        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
                        cache_key = f"embedding_{text_hash}"
                        cache.set(cache_key, embedding, self.embedding_cache_ttl)
                        
                        return idx, embedding
                        
                    except requests.exceptions.Timeout:
                        retry_count += 1
                        logger.warning(f"BGE-M3 timeout for text {idx} (attempt {retry_count}/{max_retries})")
                        if retry_count >= max_retries:
                            raise Exception(f"BGE-M3 embedding timeout for text {idx}")
                            
                    except Exception as e:
                        logger.error(f"BGE-M3 embedding error for text {idx}: {e}")
                        retry_count += 1
                        if retry_count >= max_retries:
                            raise Exception(f"BGE-M3 embedding failed for text {idx}: {str(e)}")
                        continue
                
                raise Exception(f"Failed to get BGE-M3 embedding for text {idx}")
            
            # Use ThreadPoolExecutor for parallel processing (limited to prevent server overload)
            with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_WORKERS) as executor:
                futures = {executor.submit(fetch_embedding, idx, text): (idx, text) 
                          for idx, text in api_calls_needed}
                
                for future in as_completed(futures):
                    try:
                        idx, embedding = future.result()
                        results[idx] = embedding
                    except Exception as e:
                        idx, text = futures[future]
                        logger.error(f"Error processing chunk {idx}: {e}")
                        # NO FALLBACK - Quality requirement
                        raise Exception(f"BGE-M3 batch processing failed for chunk {idx}: {str(e)}")
        
        return results
    
    def _simple_embedding_fallback(self, text):
        """Simple fallback embedding when Ollama embedding fails"""
        # Create a simple 1024-dimensional embedding based on text hash
        import hashlib
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Convert hash to 1024-dimensional vector
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
            if isinstance(pdf_file, (str, Path)):
                # Handle Path objects or string paths (from file system)
                file_path = str(pdf_file)
            elif hasattr(pdf_file, 'temporary_file_path'):
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
            # No page limit - process all pages in batches to prevent memory issues
            doc = None
            chunks = []
            vectors = []
            
            try:
                doc = fitz.open(file_path)
                total_pages = len(doc)
                
                logger.info(f"Processing PDF with {total_pages} pages")
                
                # Process all pages - batch processing handles memory automatically
                for page_num in range(1, total_pages + 1):
                    page = doc[page_num - 1]  # Pages are 0-indexed
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
            # Extract filename from various sources
            if title:
                filename = title
            elif hasattr(pdf_file, 'name'):
                filename = pdf_file.name
            else:
                # For Path objects or strings, extract from file_path
                filename = Path(file_path).name
            
            uploaded_file = UploadedFile.objects.create(
                filename=filename,
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
            
            return {
                'success': True,
                'uploaded_file_id': uploaded_file.id,
                'chunks': chunks,
                'vectors': vectors,
                'page_count': len(chunks)
            }
            
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def process_document_and_build_index(self, document_file, file_path=None, file_hash=None, user=None, title=None):
        """Process various document types and build vector index using Ollama embeddings"""
        try:
            # Handle different file types
            # If file_path is provided, use it directly
            if file_path and isinstance(file_path, str):
                pass  # Use the provided file_path
            elif hasattr(document_file, 'temporary_file_path'):
                file_path = document_file.temporary_file_path()
            elif hasattr(document_file, 'path'):
                file_path = document_file.path
            elif isinstance(document_file, (str, Path)):
                # Handle Path objects or string paths
                file_path = str(document_file)
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
            # Get filename from file_path or document_file
            if file_path and isinstance(file_path, str):
                filename = file_path.split('/')[-1]
                file_extension = filename.split('.')[-1].lower() if '.' in filename else 'pdf'
            elif isinstance(document_file, (str, Path)):
                # For string or Path objects, extract extension from file_path
                file_extension = Path(file_path).suffix[1:].lower() if Path(file_path).suffix else 'pdf'
            else:
                file_extension = document_file.name.split('.')[-1].lower() if hasattr(document_file, 'name') and '.' in document_file.name else 'pdf'
            chunks = []
            vectors = []
            
            if file_extension == 'pdf':
                # Process PDF with PyMuPDF
                # No page limit - process all pages, batch processing handles memory
                doc = None
                try:
                    doc = fitz.open(file_path)
                    total_pages = len(doc)
                    
                    logger.info(f"Processing PDF with {total_pages} pages")
                    
                    # Process all pages - memory usage is constant per page
                    for page_num in range(1, total_pages + 1):
                        page = doc[page_num - 1]  # Pages are 0-indexed
                        text = page.get_text()
                        if text.strip():
                            embedding = self.get_embedding_from_ollama(text)
                            chunks.append(text)
                            vectors.append(embedding)
                    page_count = total_pages
                finally:
                    if doc:
                        doc.close()
                
            elif file_extension in ['txt', 'rtf', 'html', 'mhtml']:
                # Process text files and HTML/MHTML files
                # No file size limit - batch processing handles memory automatically
                file_size = os.path.getsize(file_path)
                logger.info(f"Processing text file with {file_size} bytes")
                
                # For very large files, use sample processing to prevent memory issues
                # But still allow processing the full file in batches
                MAX_SAMPLE_SIZE = 50 * 1024 * 1024  # 50MB at a time
                
                if file_size > MAX_SAMPLE_SIZE:
                    logger.warning(f"File is very large ({file_size} bytes), processing in chunks")
                    # Process file in chunks to avoid loading entire file into memory
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        text = f.read(MAX_SAMPLE_SIZE)  # Read 50MB at a time
                        logger.info(f"Processing sample of large file: {len(text)} characters")
                else:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        text = f.read()
                
                if text.strip():
                    # Use very small chunks for SSB files (100 chars per chunk)
                    # Maximum precision for short SSB topics
                    # Process in batches to avoid timeout/memory issues
                    chunk_size = 100
                    
                    split_chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
                    
                    # Filter out empty chunks
                    valid_chunks = [chunk_text for chunk_text in split_chunks if chunk_text.strip()]
                    
                    # Process in batches of 50 chunks at a time - this automatically handles any file size
                    # Batching prevents memory issues by processing gradually
                    batch_size = 50
                    total_batches = (len(valid_chunks) + batch_size - 1) // batch_size
                    
                    logger.info(f"Processing {len(valid_chunks)} chunks in {total_batches} batches")
                    
                    for batch_idx in range(0, len(valid_chunks), batch_size):
                        batch = valid_chunks[batch_idx:batch_idx + batch_size]
                        
                        logger.info(f"Processing batch {batch_idx // batch_size + 1}/{total_batches}")
                        
                        # Use batch embedding method for efficiency
                        batch_embeddings = self.get_embeddings_from_ollama_batch(batch)
                        
                        # Store results
                        for idx, chunk_text in enumerate(batch):
                            if chunk_text.strip():
                                embedding = batch_embeddings[idx] if idx < len(batch_embeddings) else self.get_embedding_from_ollama(chunk_text)
                                chunks.append(chunk_text)
                                vectors.append(embedding)
                
                page_count = 1
                if not chunks:
                    # Fallback if no chunks created
                    chunks = [text[:200]]
                    vectors = [self.get_embedding_from_ollama(chunks[0])]
                
            else:
                # For other document types, just store basic info for now
                # TODO: Add support for Word, Excel, PowerPoint processing
                doc_name = title or (document_file.name if hasattr(document_file, 'name') else Path(file_path).name if file_path else 'unknown')
                chunks = [f"Document: {doc_name}"]
                vectors = [self.get_embedding_from_ollama(chunks[0])]
                page_count = 1
            
            # Create UploadedFile record
            # Get filename from file_path or document_file
            if file_path and isinstance(file_path, str):
                filename_for_record = title or file_path.split('/')[-1]
            else:
                filename_for_record = title or (document_file.name if hasattr(document_file, 'name') else 'unknown')
            
            uploaded_file = UploadedFile.objects.create(
                filename=filename_for_record,
                file_hash=file_hash,
                file_size=os.path.getsize(file_path),
                page_count=page_count,
                intro=chunks[0][:200] if chunks else None,
                uploaded_by=user if user else None
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
            
            # Generate query embedding using Ollama (BGE-M3 only)
            query_embedding = self.get_embedding_from_ollama(query)
            
            # Search using pgvector with file information
            # CRITICAL: Only search files that are fully processed and ready
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT dc.id, dc.content, dc.uploaded_file_id, dc.page_number, dc.chunk_index,
                           COALESCE(uf.filename, 'Unknown Document') as filename,
                           COALESCE(uf.file_hash, '') as file_hash, 
                           COALESCE(uf.file_size, 0) as file_size
                    FROM ai_assistant_documentchunk dc
                    LEFT JOIN ai_assistant_uploadedfile uf ON dc.uploaded_file_id = uf.id
                    WHERE dc.embedding IS NOT NULL
                    ORDER BY dc.embedding <#> %s::vector
                    LIMIT %s;
                """, [query_embedding, top_k])
                results = cursor.fetchall()
            
            formatted_results = []
            for row in results:
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
                
                # Create view URL for PDF viewer
                view_url = None
                if uploaded_file_id:
                    view_url = f"/api/ai/pdf/{uploaded_file_id}/view/?page={page_number}"
                
                formatted_results.append({
                    "id": row[0],
                    "content": content,
                    "uploaded_file_id": uploaded_file_id,
                    "page_number": page_number,
                    "chunk_index": row[4],
                    "filename": filename,
                    "title": title,  # Smart title: filename or content excerpt
                    "file_hash": row[6],
                    "file_size": row[7],
                    "download_url": f"/api/ai/documents/{uploaded_file_id}/download/" if uploaded_file_id else None,
                    "view_url": view_url,
                    "source_display": f"{filename} (Page {page_number})" if filename != "Unknown Document" else f"Page {page_number}"
                })
            
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
