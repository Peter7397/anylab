"""
Automatic File Processing System

BALANCED QUALITY AND PERFORMANCE RULES:
1. Use BGE-M3 ONLY - NO FALLBACKS EVER
2. 600 char chunks - balanced for semantic understanding and performance
3. 120 char overlap (20%) - maintains context between chunks
4. 2000 chunk limit - prevents server crashes on large documents
5. Batch embedding - 50 chunks per API call for efficiency

This ensures ALL imported files automatically become:
- Metadata ready
- Chunked with balanced strategy (max 2000 chunks per doc)
- Embedded with BGE-M3 only in batches of 50
- Ready for RAG search
"""

import logging
import os
import hashlib
import fitz  # PyMuPDF
from pathlib import Path
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from .models import UploadedFile, DocumentChunk, DocumentFile
from .rag_service import EnhancedRAGService
from .enhanced_chunking import semantic_chunker, advanced_chunker
import requests
import zipfile
import tempfile
import shutil
import io
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from typing import TYPE_CHECKING

# Import utilities
from .utils.file_utils import get_file_path, is_archive_file, extract_archive_contents
from .utils.validation import validate_metadata_completeness, verify_ollama_connection
from .utils.document_utils import create_document_file_for_uploaded_file
from .processors.metadata import MetadataExtractor
from .processors.chunking import ChunkGenerator
from .processors.chunking.pdf_chunker import PDFChunker
from .processors.ocr import OCRProcessor
from .processors.embeddings import EmbeddingGenerator

logger = logging.getLogger(__name__)

# OCR support for scanned PDFs
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    if TYPE_CHECKING:
        from PIL import Image
    else:
        Image = None  # Placeholder for runtime when import fails
    logger.warning("pytesseract or Pillow not available - OCR will be disabled")

# OCR enable/disable setting
def is_ocr_enabled():
    """Check if OCR is enabled in system settings"""
    if not OCR_AVAILABLE:
        return False  # OCR not available if libraries not installed
    # Check dynamic settings (cache) first, then fall back to settings.py
    from ai_assistant.utils.model_settings import get_ocr_enabled
    return get_ocr_enabled()

class AutomaticFileProcessor:
    """
    Automatically processes ALL uploaded files to ensure they are:
    1. Fully metadata extracted
    2. Intelligently chunked (600 char chunks, max 2000 per doc)
    3. Batch embedded (50 chunks per API call, BGE-M3 only)
    4. Ready for search
    
    BALANCED APPROACH: Quality with performance safeguards
    """
    
    def __init__(self):
        # BALANCED RULES - Quality with performance safeguards
        self.CHUNK_SIZE = 600           # Balanced size for semantic precision
        self.CHUNK_OVERLAP = 120        # 20% overlap maintains context
        
        # IMPROVED: Increased chunk limit from 2000 to 5000 for better large document coverage
        # Calculate max chunks based on available memory if possible
        try:
            import psutil
            available_memory_gb = psutil.virtual_memory().available / (1024 ** 3)
            # Estimate: Each chunk + embedding = ~10KB
            # Use 20% of available memory for chunks
            memory_for_chunks_gb = available_memory_gb * 0.2
            estimated_max_chunks = int((memory_for_chunks_gb * 1024 * 1024) / 10)  # KB to chunks
            # Clamp between reasonable bounds
            self.MAX_CHUNKS_PER_DOC = max(2000, min(estimated_max_chunks, 10000))
            logger.info(f"Calculated MAX_CHUNKS_PER_DOC: {self.MAX_CHUNKS_PER_DOC} (available memory: {available_memory_gb:.2f} GB)")
        except Exception:
            # Fallback to increased default
            self.MAX_CHUNKS_PER_DOC = 5000
            logger.warning("Could not calculate dynamic chunk limit, using default 5000")
        
        self.EMBEDDING_MODEL = 'bge-m3'  # ONLY model - NO FALLBACKS
        self.EMBEDDING_DIMS = 1024     # BGE-M3 dimensions
        self.BATCH_SIZE = 50            # Process 50 chunks per Ollama API call
        
        self.rag_service = EnhancedRAGService()
        self.ollama_url = getattr(settings, 'OLLAMA_API_URL', 'http://ollama:11434')
        self.metadata_extractor = MetadataExtractor()
        self.chunk_generator = ChunkGenerator(max_chunks_per_doc=self.MAX_CHUNKS_PER_DOC)
        self.pdf_chunker = PDFChunker(max_chunks_per_doc=self.MAX_CHUNKS_PER_DOC)
        self.ocr_processor = OCRProcessor()
        self.embedding_generator = EmbeddingGenerator(
            ollama_url=self.ollama_url,
            embedding_model=self.EMBEDDING_MODEL,
            batch_size=self.BATCH_SIZE,
            embedding_dims=self.EMBEDDING_DIMS
        )
        
    def process_file_fully(self, uploaded_file_id: int, max_retries: int = 3):
        """
        Complete automatic processing workflow:
        Upload → Extract Metadata → Generate Chunks (max 2000) → Batch Embeddings (50 per call) → Ready
        
        RETRY MECHANISM: Retries are handled by Celery task (autoretry_for), not here
        This simplifies error handling and makes retry behavior consistent
        """
        uploaded_file = UploadedFile.objects.get(id=uploaded_file_id)
        
        # SAFETY CHECK: Ensure DocumentFile exists (catches legacy imports without DocumentFile)
        document_files = DocumentFile.objects.filter(uploaded_file=uploaded_file)
        if document_files.count() == 0:
            # Auto-create missing DocumentFile
            logger.warning(f"DocumentFile missing for UploadedFile {uploaded_file_id}, creating now")
            try:
                document_file = create_document_file_for_uploaded_file(uploaded_file)
                logger.info(f"Auto-created DocumentFile {document_file.id} for UploadedFile {uploaded_file_id}")
            except Exception as e:
                logger.error(f"Failed to auto-create DocumentFile for UploadedFile {uploaded_file_id}: {e}", exc_info=True)
                # Continue processing anyway - DocumentFile creation is not critical for processing
        
        # PRE-CHECK: Verify Ollama is accessible before starting processing
        try:
            verify_ollama_connection(self.ollama_url)
        except Exception as e:
            error_msg = f"Ollama service is not accessible at {self.ollama_url}: {str(e)}. Please ensure Ollama is running."
            logger.error(error_msg)
            uploaded_file.processing_status = 'failed'
            uploaded_file.processing_error = error_msg
            uploaded_file.save()
            raise Exception(error_msg)
        
        # SIMPLIFIED: Single attempt - Celery handles retries via autoretry_for
        try:
            logger.info(f"Starting automatic processing for: {uploaded_file.filename}")
            
            # Step 1: Verify file exists BEFORE starting processing
            # BUT: If processing is already complete (chunks/embeddings exist), skip file check
            if (uploaded_file.chunks_created and uploaded_file.chunk_count > 0 and
                uploaded_file.embeddings_created and uploaded_file.embedding_count > 0):
                logger.info(
                    f"File {uploaded_file.filename} already has chunks/embeddings. "
                    f"Skipping file existence check and marking as ready."
                )
                uploaded_file.processing_status = 'ready'
                uploaded_file.processing_completed_at = timezone.now()
                uploaded_file.save()
                return {
                    'success': True,
                    'chunk_count': uploaded_file.chunk_count,
                    'embedding_count': uploaded_file.embedding_count,
                    'status': 'ready',
                    'attempts': 1,
                    'note': 'Processing already completed in previous attempt'
                }
            
            # Get file path and verify it exists
            file_path = get_file_path(uploaded_file)
            if not os.path.exists(file_path):
                raise FileNotFoundError(
                    f"File not found before processing: {file_path}. "
                    f"This file may not have been saved correctly during upload. "
                    f"Please re-upload the file."
                )
            logger.info(f"File verified exists before processing: {file_path}")
            
            # Step 2: Update status - extracting metadata
            uploaded_file.processing_status = 'metadata_extracting'
            uploaded_file.processing_started_at = timezone.now()
            uploaded_file.save()
            
            # Step 3: Extract ALL metadata
            metadata = self.metadata_extractor.extract_all_metadata(uploaded_file)
            
            # VALIDATION: Check metadata completeness
            if metadata is None:
                raise Exception("Metadata extraction returned None - this should not happen")
            
            if not validate_metadata_completeness(metadata, uploaded_file):
                raise Exception("Metadata extraction incomplete")
            
            uploaded_file.metadata_extracted = True
            uploaded_file.processing_status = 'chunking'
            uploaded_file.save()
            
            # Step 4: Verify file still exists before chunking
            # BUT: If chunks/embeddings already exist, skip this check (file may have been deleted after processing)
            if not os.path.exists(file_path):
                # Check if processing was already completed
                if (uploaded_file.chunks_created and uploaded_file.chunk_count > 0 and
                    uploaded_file.embeddings_created and uploaded_file.embedding_count > 0):
                    logger.warning(
                        f"File {file_path} not found, but chunks/embeddings exist. "
                        f"Assuming processing was completed and file was deleted. Marking as ready."
                    )
                    # Mark as ready since processing is complete
                    uploaded_file.processing_status = 'ready'
                    uploaded_file.processing_completed_at = timezone.now()
                    uploaded_file.save()
                    return {
                        'success': True,
                        'chunk_count': uploaded_file.chunk_count,
                        'embedding_count': uploaded_file.embedding_count,
                        'status': 'ready',
                        'attempts': 1,
                        'note': 'File was deleted but processing was already complete'
                    }
                else:
                    # File doesn't exist and processing not complete - this is an error
                    raise FileNotFoundError(
                        f"File disappeared during processing: {file_path}. "
                        f"This may indicate a volume sync issue. Please re-upload."
                    )
            
            # Step 5: Generate chunks (UNLIMITED for quality)
            chunks_data = self._generate_chunks(uploaded_file)
            
            # Check if file was marked as "no text available" (OCR disabled scenario)
            uploaded_file.refresh_from_db()
            if uploaded_file.processing_status == 'no_text_available':
                logger.info(f"File {uploaded_file.filename} has no text available (OCR disabled). Skipping chunking and embedding.")
                return {
                    'success': True,
                    'chunk_count': 0,
                    'embedding_count': 0,
                    'status': 'no_text_available',
                    'message': uploaded_file.processing_error or "File uploaded but has no extractable text. OCR is disabled.",
                    'attempts': 1
                }
            
            # VALIDATION: Check chunks were created
            if not chunks_data or len(chunks_data) == 0:
                # Provide more detailed error message based on file type
                from pathlib import Path
                file_ext = Path(uploaded_file.filename).suffix.lower()
                if file_ext == '.pdf':
                    error_msg = (
                        "No chunks generated from PDF. This may be because: "
                        "1) PDF is image-based/scanned (requires OCR), "
                        "2) PDF has no text content, "
                        "3) PDF is corrupted or encrypted. "
                        "Please check the file and try again."
                    )
                else:
                    error_msg = (
                        f"No chunks generated from {file_ext} file. "
                        "The file may be empty, corrupted, or in an unsupported format."
                    )
                logger.error(f"{error_msg} File: {uploaded_file.filename}")
                raise Exception(error_msg)
            
            uploaded_file.chunks_created = True
            uploaded_file.chunk_count = len(chunks_data)
            uploaded_file.processing_status = 'embedding'
            uploaded_file.save()
            
            logger.info(f"Created {len(chunks_data)} chunks for {uploaded_file.filename}")
            
            # Step 6: Generate embeddings (BGE-M3 ONLY, NO FALLBACKS)
            # DATA INTEGRITY: Wrap in transaction to prevent orphaned chunks on failure
            from django.db import transaction
            
            # PERFORMANCE: Add progress callback for real-time updates
            def _update_embedding_progress(current_count, total_count):
                """Update embedding progress in database"""
                uploaded_file.embedding_count = current_count
                uploaded_file.save(update_fields=['embedding_count'])
                logger.debug(f"Embedding progress: {current_count}/{total_count} ({current_count/total_count*100:.1f}%)")
            
            try:
                with transaction.atomic():
                    # DATA INTEGRITY: Delete any existing chunks for this file (in case of retry)
                    existing_chunks = DocumentChunk.objects.filter(uploaded_file=uploaded_file)
                    if existing_chunks.exists():
                        logger.warning(f"Found {existing_chunks.count()} existing chunks for {uploaded_file.filename}, deleting before reprocessing")
                        existing_chunks.delete()
                    
                    embedding_count = self.embedding_generator.generate_embeddings(
                        chunks_data, 
                        uploaded_file,
                        progress_callback=_update_embedding_progress
                    )
                    
                    # VALIDATION: Check embeddings were created and match chunk count
                    if embedding_count == 0:
                        raise Exception("No embeddings generated")
                    
                    if embedding_count != len(chunks_data):
                        logger.warning(
                            f"Embedding count ({embedding_count}) doesn't match chunk count ({len(chunks_data)}) "
                            f"for {uploaded_file.filename}"
                        )
                    
                    # DATA INTEGRITY: Update status atomically with embedding count
                    uploaded_file.embeddings_created = True
                    uploaded_file.embedding_count = embedding_count
                    uploaded_file.processing_status = 'ready'
                    uploaded_file.processing_completed_at = timezone.now()
                    uploaded_file.processing_error = None  # Clear any previous errors
                    uploaded_file.save()
                    
                    # Transaction commits here if no exception
                    logger.info(
                        f"File {uploaded_file.filename} marked as READY immediately after embedding creation: "
                        f"{embedding_count} embeddings created"
                    )
                    
            except Exception as e:
                # Transaction will rollback automatically, preventing orphaned chunks
                logger.error(f"Embedding generation failed for {uploaded_file.filename}: {e}", exc_info=True)
                uploaded_file.processing_status = 'failed'
                uploaded_file.processing_error = f"Embedding failed: {str(e)}"
                uploaded_file.save()
                raise  # Re-raise for Celery retry mechanism
            
            # Step 7: Build GraphRAG (moved to async task - doesn't delay ready status)
            # PERFORMANCE: GraphRAG is now built asynchronously to not delay file ready status
            try:
                from ..tasks.file_processing_tasks import build_graph_for_file
                logger.info(f"Scheduling GraphRAG build for {uploaded_file.filename} (async, non-blocking)")
                build_graph_for_file.delay(uploaded_file.id)  # Async, non-blocking
            except ImportError:
                logger.warning("GraphRAG task not available, skipping GraphRAG construction")
            except Exception as e:
                logger.warning(f"Failed to schedule GraphRAG task for {uploaded_file.filename}: {e}")
                # Don't fail the entire processing if GraphRAG scheduling fails
                # The file is still searchable with vector search
                
                # FINAL VALIDATION: Verify file is truly ready
                # Status was already set to 'ready' above, but verify consistency
                # Skip validation if file is marked as corrupted or no_text_available
                if uploaded_file.processing_status not in ['corrupted', 'no_text_available']:
                    is_ready_now = (
                        uploaded_file.processing_status == 'ready' and
                        uploaded_file.metadata_extracted and
                        uploaded_file.chunks_created and uploaded_file.chunk_count > 0 and
                        uploaded_file.embeddings_created and uploaded_file.embedding_count == uploaded_file.chunk_count
                    )
                    if not is_ready_now:
                        # This should never happen if status was set correctly above
                        logger.error(
                            f"Status inconsistency detected for {uploaded_file.filename}: "
                            f"status={uploaded_file.processing_status}, "
                            f"metadata={uploaded_file.metadata_extracted}, "
                            f"chunks={uploaded_file.chunks_created} ({uploaded_file.chunk_count}), "
                            f"embeddings={uploaded_file.embeddings_created} ({uploaded_file.embedding_count})"
                        )
                        # Fix the status if it's wrong
                        if uploaded_file.chunk_count > 0 and uploaded_file.embedding_count > 0:
                            uploaded_file.processing_status = 'ready'
                            uploaded_file.save()
                            logger.warning(f"Fixed status for {uploaded_file.filename} - set to ready")
                    
                    logger.info(f"Processing complete: {uploaded_file.filename} with {embedding_count} embeddings")
                    
                    return {
                        'success': True,
                        'chunk_count': len(chunks_data),
                        'embedding_count': embedding_count,
                        'status': 'ready',
                        'attempts': 1
                    }
                else:
                    # File was marked as corrupted or no_text during processing
                    logger.info(f"Processing stopped: {uploaded_file.filename} marked as {uploaded_file.processing_status}")
                    return {
                        'success': False,
                        'chunk_count': 0,
                        'embedding_count': 0,
                        'status': uploaded_file.processing_status,
                        'error': uploaded_file.processing_error or f"File marked as {uploaded_file.processing_status}",
                        'attempts': 1
                    }
                
        except Exception as e:
            # SIMPLIFIED: Let Celery handle retries - just raise exception
            error_str = str(e)
            
            # Refresh from DB to get latest status (may have been set to 'corrupted' or 'no_text_available')
            uploaded_file.refresh_from_db()
            
            # Don't retry if file is already marked as corrupted or no_text_available
            if uploaded_file.processing_status in ['corrupted', 'no_text_available']:
                logger.info(f"File {uploaded_file.filename} marked as {uploaded_file.processing_status}, not retrying")
                return {
                    'success': False,
                    'chunk_count': 0,
                    'embedding_count': 0,
                    'status': uploaded_file.processing_status,
                    'error': uploaded_file.processing_error or error_str,
                    'attempts': 1
                }
            
            logger.error(f"Processing failed for {uploaded_file.filename}: {error_str}", exc_info=True)
            
            # IMPORTANT: Check if chunks and embeddings were actually created despite error
            # If they were, the file is actually ready even if error occurred
            if (uploaded_file.chunks_created and uploaded_file.chunk_count > 0 and
                uploaded_file.embeddings_created and uploaded_file.embedding_count > 0 and
                uploaded_file.embedding_count == uploaded_file.chunk_count):
                # Processing was actually successful! Mark as ready
                logger.warning(
                    f"File {uploaded_file.filename} has chunks/embeddings but error occurred. "
                    f"Marking as ready."
                )
                uploaded_file.processing_status = 'ready'
                uploaded_file.processing_completed_at = timezone.now()
                uploaded_file.processing_error = None  # Clear error since processing succeeded
                uploaded_file.save()
                
                return {
                    'success': True,
                    'chunk_count': uploaded_file.chunk_count,
                    'embedding_count': uploaded_file.embedding_count,
                    'status': 'ready',
                    'attempts': 1,
                    'note': 'File marked as ready despite error (chunks/embeddings exist)'
                }
            
            # Store error details in database for debugging
            detailed_error = (
                f"Processing failed: {error_str}. "
                f"File: {uploaded_file.filename} (ID: {uploaded_file.id}). "
                f"Status at failure: metadata_extracted={uploaded_file.metadata_extracted}, "
                f"chunks_created={uploaded_file.chunks_created} ({uploaded_file.chunk_count} chunks), "
                f"embeddings_created={uploaded_file.embeddings_created} ({uploaded_file.embedding_count} embeddings). "
                f"Please check logs for more details or try re-uploading the file."
            )
            
            uploaded_file.processing_status = 'failed'
            uploaded_file.processing_error = detailed_error
            uploaded_file.save()
            
            # Re-raise for Celery to handle retry
            raise Exception(detailed_error) from e
    
    def _extract_archive_contents(self, file_path: str, uploaded_file: UploadedFile) -> list:
        """
        Extract archive and return list of extracted file paths
        
        QUALITY FOCUS: Process ALL contents, unlimited chunks for each file
        """
        return extract_archive_contents(file_path, uploaded_file)
    def _generate_chunks(self, uploaded_file: UploadedFile) -> list:
        """Generate chunks with UNLIMITED approach for maximum quality"""
        try:
            # If this upload has an associated DocumentFile with website content metadata, use that path
            doc_file = DocumentFile.objects.filter(uploaded_file=uploaded_file).first()
            if doc_file and isinstance(getattr(doc_file, 'metadata', None), dict):
                if doc_file.metadata.get('content_type') == 'website' or doc_file.metadata.get('html_content'):
                    return self.chunk_generator.generate_html_chunks(uploaded_file)
            
            file_path = get_file_path(uploaded_file)
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            file_ext = Path(uploaded_file.filename).suffix.lower()
            chunks_data = []
            
            # PDF processing with unlimited chunks - use PDF chunker
            if file_ext == '.pdf':
                chunks_data = self.pdf_chunker.chunk_pdf(
                    uploaded_file,
                    file_path=file_path,
                    ocr_processor=self.ocr_processor if OCR_AVAILABLE and is_ocr_enabled() else None
                )
                # PDF chunker handles all PDF processing including OCR
                return chunks_data
            
            # Text file processing
            elif file_ext in ['.txt', '.rtf', '.html', '.mhtml', '.md']:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Clean null bytes and problematic control characters early
                if isinstance(content, str):
                    content = content.replace('\x00', '').replace('\0', '')
                    # Remove other problematic control characters (keep \n, \r, \t)
                    content = ''.join(char for char in content if ord(char) >= 32 or char in ['\n', '\r', '\t'])
                
                if content.strip():
                    # Use advanced chunker with NO limits
                    content_chunks = semantic_chunker.chunk_by_sentences(content, page_number=1)
                    
                    for chunk in content_chunks:
                        chunks_data.append({
                            'content': chunk.content,
                            'page_number': chunk.page_number,
                            'chunk_index': len(chunks_data)
                        })
            
            # Word, Excel, PowerPoint processing - use chunk generator
            elif file_ext in ['.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt']:
                # Use chunk generator for Office documents
                chunks_data = self.chunk_generator.generate_chunks(
                    uploaded_file,
                    file_path=file_path,
                    file_ext=file_ext
                )
            
            chunks_count = len(chunks_data)
            logger.info(f"Generated {chunks_count} chunks from {uploaded_file.filename}")
            
            return chunks_data
            
        except Exception as e:
            logger.error(f"Chunking error: {e}")
            raise
    


# Global instance
automatic_file_processor = AutomaticFileProcessor()

