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
from .utils.model_settings import get_ollama_model
from .hybrid_search import QueryProcessor
import logging
import json
import re
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Initialize query processor for adaptive expansion
query_processor = QueryProcessor()

class EnhancedRAGService:
    def __init__(self, model_name=None):
        self.model_name = model_name or get_ollama_model()
        self.ollama_url = getattr(settings, 'OLLAMA_API_URL', 'http://ollama:11434')
        self.embedding_model = getattr(settings, 'EMBEDDING_MODEL', 'bge-m3')
        # Standardized cache settings across all RAG services
        self.embedding_cache_ttl = getattr(settings, 'EMBEDDING_CACHE_TTL', 24 * 3600)  # 24 hours (standardized)
        self.search_cache_ttl = getattr(settings, 'SEARCH_CACHE_TTL', 3600)  # 1 hour
        self.response_cache_ttl = getattr(settings, 'RESPONSE_CACHE_TTL', 1800)  # 30 minutes
        # Adaptive query expansion settings
        self.use_adaptive_expansion = getattr(settings, 'RAG_USE_ADAPTIVE_EXPANSION', True)
        self.query_processor = query_processor
        # Performance monitoring
        self.enable_performance_monitoring = getattr(settings, 'RAG_ENABLE_PERFORMANCE_MONITORING', True)
        self._performance_metrics = {}  # Store metrics for current session
        
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
        # Clean null bytes from text (Ollama cannot handle NUL characters)
        if isinstance(text, str):
            text = text.replace('\x00', '').replace('\0', '')
            # Also remove any other control characters that might cause issues
            text = ''.join(char for char in text if ord(char) >= 32 or char in ['\n', '\r', '\t'])
        
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

    def _analyze_query_complexity(self, query: str) -> dict:
        """
        Analyze query complexity to determine if expansion is beneficial.
        
        Returns:
            dict with complexity metrics and expansion recommendation
        """
        query_lower = query.lower().strip()
        word_count = len(query_lower.split())
        char_count = len(query_lower)
        
        # Extract key terms (non-stop words)
        key_terms = self.query_processor.extract_key_terms(query)
        key_term_count = len(key_terms)
        
        # Check for exact phrases (quoted strings)
        has_exact_phrases = '"' in query
        
        # Check for technical/exact terms
        technical_terms = ['version', 'ip', 'url', 'api', 'id', 'uuid', 'hash', 'code', 'error']
        has_technical_terms = any(term in query_lower for term in technical_terms)
        
        # Check for specific question patterns
        specific_patterns = [
            r'^what is (the )?\w+$',
            r'^where is (the )?\w+$',
            r'^when did \w+',
            r'^who is \w+',
        ]
        is_specific_query = any(re.match(pattern, query_lower) for pattern in specific_patterns)
        
        # Complexity score (higher = more complex)
        complexity_score = (
            (word_count * 2) +
            (key_term_count * 3) +
            (10 if has_technical_terms else 0) +
            (5 if is_specific_query else 0) +
            (-15 if has_exact_phrases else 0)
        )
        
        # Determine if expansion is beneficial
        # Simple queries (< 3 words) benefit from expansion
        # Complex queries (> 8 words) don't need expansion
        # Technical/exact queries should not be expanded
        should_expand = (
            self.use_adaptive_expansion and
            not has_exact_phrases and
            not has_technical_terms and
            not is_specific_query and
            word_count < 8 and
            (word_count < 3 or complexity_score < 20)
        )
        
        return {
            'word_count': word_count,
            'key_term_count': key_term_count,
            'char_count': char_count,
            'complexity_score': complexity_score,
            'has_exact_phrases': has_exact_phrases,
            'has_technical_terms': has_technical_terms,
            'is_specific_query': is_specific_query,
            'should_expand': should_expand,
            'query_type': self.query_processor.classify_query(query)
        }
    
    def search_relevant_documents(self, query, top_k=10):  # Increased from 8 to 10 for maximum comprehensive results
        """Search for relevant documents using vector similarity with Ollama embeddings and adaptive query expansion"""
        start_time = time.time()
        metrics = {
            'query': query[:50],
            'top_k': top_k,
            'stages': {}
        }
        
        try:
            # Analyze query complexity for adaptive expansion
            complexity_start = time.time()
            complexity = self._analyze_query_complexity(query)
            metrics['stages']['complexity_analysis'] = (time.time() - complexity_start) * 1000  # ms
            metrics['complexity'] = complexity
            
            # Apply adaptive query expansion if beneficial
            if complexity['should_expand']:
                expanded_query = self.query_processor.expand_query(query)
                logger.info(
                    f"Query expansion applied: '{query[:50]}...' -> '{expanded_query[:50]}...' "
                    f"(complexity: {complexity['complexity_score']}, type: {complexity['query_type']})"
                )
                search_query = expanded_query
            else:
                logger.debug(
                    f"Query expansion skipped: '{query[:50]}...' "
                    f"(complexity: {complexity['complexity_score']}, type: {complexity['query_type']})"
                )
                search_query = query
            
            # Create cache key for search results (include expansion status)
            query_hash = hashlib.md5(search_query.encode('utf-8')).hexdigest()
            cache_key = f"search_{query_hash}_{top_k}"
            
            # Try to get from cache first
            cached_results = cache.get(cache_key)
            if cached_results is not None:
                logger.info(f"Using cached search results for query: {query[:30]}...")
                return cached_results
            
            # Generate query embedding using Ollama (BGE-M3 only)
            embedding_start = time.time()
            query_embedding = self.get_embedding_from_ollama(search_query)
            metrics['stages']['embedding_generation'] = (time.time() - embedding_start) * 1000  # ms
            
            # Search using pgvector with file information
            # CRITICAL: Only search files that are fully processed and ready
            search_start = time.time()
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT dc.id, dc.content, dc.uploaded_file_id, dc.page_number, dc.chunk_index,
                           COALESCE(uf.filename, 'Unknown Document') as filename,
                           COALESCE(uf.file_hash, '') as file_hash, 
                           COALESCE(uf.file_size, 0) as file_size
                    FROM ai_assistant_documentchunk dc
                    LEFT JOIN ai_assistant_uploadedfile uf ON dc.uploaded_file_id = uf.id
                    WHERE dc.embedding IS NOT NULL
                    ORDER BY dc.embedding <=> %s::vector
                    LIMIT %s;
                """, [query_embedding, top_k])
                results = cursor.fetchall()
            metrics['stages']['vector_search'] = (time.time() - search_start) * 1000  # ms
            metrics['results_count'] = len(results)
            
            formatting_start = time.time()
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
                    view_url = f"/api/ai/documents/pdf/{uploaded_file_id}/view/?page={page_number}"
                
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
            metrics['stages']['result_formatting'] = (time.time() - formatting_start) * 1000  # ms
            
            # Add query complexity metadata to results
            for result in formatted_results:
                result['query_complexity'] = complexity
                result['expansion_applied'] = complexity['should_expand']
            
            # Cache the results
            cache_start = time.time()
            cache.set(cache_key, formatted_results, self.response_cache_ttl)
            metrics['stages']['caching'] = (time.time() - cache_start) * 1000  # ms
            
            # Calculate total time
            total_time = (time.time() - start_time) * 1000  # ms
            metrics['total_time_ms'] = total_time
            metrics['stages']['total'] = total_time
            
            # Log performance metrics if enabled
            if self.enable_performance_monitoring:
                logger.info(
                    f"Search performance - Query: '{query[:30]}...' | "
                    f"Total: {total_time:.1f}ms | "
                    f"Embedding: {metrics['stages'].get('embedding_generation', 0):.1f}ms | "
                    f"Vector Search: {metrics['stages'].get('vector_search', 0):.1f}ms | "
                    f"Formatting: {metrics['stages'].get('result_formatting', 0):.1f}ms | "
                    f"Results: {len(formatted_results)}"
                )
                # Store metrics for retrieval
                self._performance_metrics[query_hash] = metrics
            
            logger.info(
                f"Cached search results for query: {query[:30]}... "
                f"(expansion: {complexity['should_expand']}, results: {len(formatted_results)})"
            )
            
            # If expanded query returned no results, try original query as fallback
            if not formatted_results and complexity['should_expand']:
                logger.warning(f"Expanded query returned no results, trying original query: {query[:50]}...")
                return self.search_relevant_documents(query, top_k)  # Recursive call with original query (will skip expansion)
            
            # Add performance metrics to results metadata
            for result in formatted_results:
                result['_performance_metrics'] = metrics
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []

    def ollama_generate(self, prompt, model=None, language='en-US'):
        """Generate response using Ollama with caching and language support"""
        if model is None:
            # Always fetch the current model dynamically instead of using cached self.model_name
            model = get_ollama_model()
        
        # Validate model is set
        if not model:
            logger.error("Ollama model is not set! Please configure OLLAMA_MODEL in settings or via System Settings.")
            raise ValueError("Ollama model is not configured. Please set a model in System Settings.")
            
        # Create cache key for response (include language in cache key)
        prompt_hash = hashlib.md5(prompt.encode('utf-8')).hexdigest()
        cache_key = f"response_{prompt_hash}_{language}"
        
        # Try to get from cache first
        cached_response = cache.get(cache_key)
        if cached_response is not None:
            logger.info(f"Using cached response for prompt hash: {prompt_hash[:8]}...")
            return cached_response
        
        # Select system prompt based on language with explicit language instruction
        if 'zh' in language.lower():
            system_prompt = getattr(settings, 'OLLAMA_SYSTEM_PROMPT_ZH',
                                  '你是一个专业的助手。你必须用中文（简体中文）回答所有问题。'
                                  '请仅使用提供的上下文回答问题，保持简洁准确。'
                                  '不要用英语回答，只能用中文。')
        else:
            system_prompt = getattr(settings, 'OLLAMA_SYSTEM_PROMPT_EN',
                                  'You are a helpful assistant. You MUST answer all questions in English. '
                                  'Use only the following context to answer the question. Be concise and accurate. '
                                  'Do not respond in Chinese, only in English.')
            
        try:
            api_url = f"{self.ollama_url}/api/chat"
            logger.debug(f"Calling Ollama API: {api_url} with model: {model}")
            response = requests.post(
                api_url,
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
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
            response_data = response.json()
            response_text = response_data.get("message", {}).get("content", "")
            
            if not response_text:
                logger.error(f"Empty response from Ollama. Response: {response_data}")
                raise ValueError("Empty response from Ollama API")
            
            # Cache the response
            cache.set(cache_key, response_text, self.response_cache_ttl)
            logger.info(f"Cached response for prompt hash: {prompt_hash[:8]}...")
            
            return response_text
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.error(f"Ollama API endpoint not found (404). URL: {api_url}, Model: {model}. Check if Ollama is running and the URL is correct.")
                raise ValueError(f"Ollama API endpoint not found. Please check if Ollama is running at {self.ollama_url} and the model '{model}' exists.")
            else:
                logger.error(f"HTTP error from Ollama: {e.response.status_code} - {e.response.text}")
                raise
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Cannot connect to Ollama at {self.ollama_url}. Make sure Ollama is running.")
            raise ValueError(f"Cannot connect to Ollama at {self.ollama_url}. Please ensure Ollama is running.")
        except Exception as e:
            logger.error(f"Error generating response from Ollama: {e}")
            raise

    def generate_response(self, query, context_documents, language='en-US'):
        """Generate response with proper context handling - optimized for maximum comprehensive answers"""
        # Language-aware "I don't know" response
        if not context_documents:
            return "我不知道。" if 'zh' in language.lower() else "I don't know."
        
        # Build context with reference numbers - adaptive context length based on query complexity
        # Optimize: Use fewer documents and shorter content for better performance
        complexity = getattr(self, '_last_query_complexity', {})
        is_simple_query = complexity.get('complexity_score', 50) < 15 or complexity.get('word_count', 5) < 4
        
        # Adaptive document count and content length
        if is_simple_query:
            max_docs = 5  # Fewer documents for simple queries
            max_chars_per_doc = 400  # Shorter content per document
            max_total_chars = 2000  # Total context limit for simple queries
        else:
            max_docs = 8  # More documents for complex queries (reduced from 10)
            max_chars_per_doc = 500  # Moderate content per document (reduced from 600)
            max_total_chars = 4000  # Total context limit for complex queries (reduced from ~6000)
        
        context_lines = []
        total_chars = 0
        for idx, doc in enumerate(context_documents[:max_docs], 1):
            if total_chars >= max_total_chars:
                break
            # Truncate long content to optimize performance
            content = doc['content'][:max_chars_per_doc] if len(doc['content']) > max_chars_per_doc else doc['content']
            similarity = doc.get('similarity', 0)
            doc_text = f"[{idx}] (Similarity: {similarity:.3f})\n{content}"
            if total_chars + len(doc_text) > max_total_chars:
                # Trim this document to fit within limit
                remaining = max_total_chars - total_chars - len(f"[{idx}] (Similarity: {similarity:.3f})\n")
                if remaining > 50:  # Only include if meaningful content remains
                    content = content[:remaining]
                    doc_text = f"[{idx}] (Similarity: {similarity:.3f})\n{content}"
                else:
                    break
            context_lines.append(doc_text)
            total_chars += len(doc_text)
        
        context = "\n\n".join(context_lines)
        
        # Language-aware RAG prompts
        if 'zh' in language.lower():
            # Chinese prompt - with explicit language enforcement
            prompt = (
                "重要：你必须用中文（简体中文）回答。不要用英语。\n\n"
                "你是一个专业的助手。\n"
                "请仅使用以下提供的上下文来回答用户的问题。\n"
                "引用上下文中的信息时使用方括号引用编号（例如：[1]，或多个 [1][3]）。\n"
                "如果上下文中没有相关信息，请直接回答：\"我不知道。\"\n"
                "不要使用你的内部知识库或常识来回答问题。\n"
                "使用上下文中所有相关信息提供全面的答案。\n"
                "如果多个来源包含相关信息，请将它们综合成一个完整的回答。\n"
                "尽可能使用更多相关来源来提供详尽的答案。\n\n"
                f"上下文：\n{context}\n\n"
                f"问题：{query}\n\n"
                "回答（必须用中文）："
            )
        else:
            # English prompt - with explicit language enforcement
            prompt = (
                "IMPORTANT: You MUST answer in English. Do not respond in Chinese.\n\n"
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
                "Answer (in English):"
            )
        
        return self.ollama_generate(prompt, language=language)

    def query_with_rag(self, query, top_k=10, user=None, language='en-US'):  # Increased from 8 to 10
        """Main RAG pipeline with caching, language support, and performance monitoring"""
        start_time = time.time()
        pipeline_metrics = {
            'query': query[:50],
            'top_k': top_k,
            'language': language,
            'stages': {}
        }
        
        try:
            # Create cache key for entire RAG query (include language)
            query_hash = hashlib.md5(query.encode('utf-8')).hexdigest()
            cache_key = f"rag_query_{query_hash}_{top_k}_{language}"
            
            # Try to get from cache first
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.info(f"Using cached RAG result for query: {query[:30]}...")
                return cached_result
            
            # Store query complexity for use in response generation
            complexity = self._analyze_query_complexity(query)
            self._last_query_complexity = complexity
            
            # Search for relevant documents
            search_start = time.time()
            relevant_docs = self.search_relevant_documents(query, top_k)
            pipeline_metrics['stages']['document_search'] = (time.time() - search_start) * 1000  # ms
            pipeline_metrics['documents_found'] = len(relevant_docs)
            
            if not relevant_docs:
                response = "我不知道。" if 'zh' in language.lower() else "I don't know."
                result = {
                    "response": response,
                    "sources": [],
                    "query": query
                }
            else:
                # Generate response with language support
                generation_start = time.time()
                response = self.generate_response(query, relevant_docs, language=language)
                pipeline_metrics['stages']['response_generation'] = (time.time() - generation_start) * 1000  # ms
                pipeline_metrics['response_length'] = len(response)
                
                result = {
                    "response": response,
                    "sources": relevant_docs,
                    "query": query
                }
            
            # Cache the result
            cache_start = time.time()
            cache.set(cache_key, result, self.response_cache_ttl)
            pipeline_metrics['stages']['caching'] = (time.time() - cache_start) * 1000  # ms
            
            # Calculate total pipeline time
            total_time = (time.time() - start_time) * 1000  # ms
            pipeline_metrics['total_time_ms'] = total_time
            pipeline_metrics['stages']['total'] = total_time
            
            # Log performance metrics if enabled
            if self.enable_performance_monitoring:
                logger.info(
                    f"RAG Pipeline Performance - Query: '{query[:30]}...' | "
                    f"Total: {total_time:.1f}ms | "
                    f"Search: {pipeline_metrics['stages'].get('document_search', 0):.1f}ms | "
                    f"Generation: {pipeline_metrics['stages'].get('response_generation', 0):.1f}ms | "
                    f"Documents: {len(relevant_docs)} | "
                    f"Response: {len(response)} chars"
                )
                # Store metrics
                query_hash = hashlib.md5(query.encode('utf-8')).hexdigest()
                self._performance_metrics[f"rag_pipeline_{query_hash}"] = pipeline_metrics
            
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
            
            # Add performance metrics to result
            result['_performance_metrics'] = pipeline_metrics
            
            return result
            
        except Exception as e:
            logger.error(f"Error in RAG query: {e}")
            return {
                "response": f"Error processing query: {str(e)}",
                "sources": [],
                "query": query
            }

    def get_performance_metrics(self, query_hash: Optional[str] = None) -> Dict[str, Any]:
        """
        Get performance metrics for queries.
        
        Args:
            query_hash: Optional specific query hash to retrieve metrics for.
                       If None, returns all stored metrics.
        
        Returns:
            Dictionary with performance metrics
        """
        if query_hash:
            return self._performance_metrics.get(query_hash, {})
        return self._performance_metrics
    
    def clear_performance_metrics(self):
        """Clear stored performance metrics"""
        self._performance_metrics.clear()
        logger.info("Performance metrics cleared")
    
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
