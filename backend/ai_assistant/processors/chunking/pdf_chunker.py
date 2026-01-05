"""
PDF chunking module - handles PDF text extraction and chunking.
"""

import logging
import os
from typing import Optional, List, Dict, Any
import fitz  # PyMuPDF
from pathlib import Path
from ...enhanced_chunking import semantic_chunker
from ...utils.file_utils import get_file_path
from ...models import UploadedFile
from ...processors.exceptions import ProcessingError

logger = logging.getLogger(__name__)

# OCR support
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    Image = None
    logger.warning("pytesseract or Pillow not available - OCR will be disabled")

# OCR enable/disable setting
def is_ocr_enabled():
    """Check if OCR is enabled in system settings"""
    if not OCR_AVAILABLE:
        return False
    from ...utils.model_settings import get_ocr_enabled
    return get_ocr_enabled()


class PDFChunker:
    """Handle PDF chunking with OCR support"""
    
    def __init__(self, max_chunks_per_doc: int = 2000) -> None:
        self.MAX_CHUNKS_PER_DOC = max_chunks_per_doc
    
    def chunk_pdf(self, uploaded_file: UploadedFile, file_path: Optional[str] = None, ocr_processor: Optional[Any] = None) -> List[Dict[str, Any]]:
        """
        Chunk PDF file with text extraction and optional OCR
        
        Args:
            uploaded_file: UploadedFile instance
            file_path: Optional file path
            ocr_processor: Optional OCR processor instance
            
        Returns:
            List of chunk data dictionaries
        """
        # Always re-resolve file path to ensure we're using the correct file
        # This is critical because the file might have been moved or the path might be inconsistent
        # between metadata extraction and chunking stages
        resolved_file_path = get_file_path(uploaded_file)
        
        # If file_path was provided, verify it exists and is the same file
        # If provided path doesn't exist or is different, use the resolved path instead
        if file_path is not None and os.path.exists(file_path) and os.path.exists(resolved_file_path):
            try:
                # Check if they point to the same file
                if os.path.samefile(file_path, resolved_file_path):
                    file_path = file_path  # Use provided path if it's the same file
                else:
                    # Provided path exists but is different - use resolved path to ensure consistency
                    logger.warning(f"Provided file_path {file_path} differs from resolved path {resolved_file_path}. Using resolved path.")
                    file_path = resolved_file_path
            except (OSError, ValueError):
                # samefile() failed (e.g., paths on different filesystems) - use resolved path
                logger.warning(f"Could not compare file paths, using resolved path: {resolved_file_path}")
                file_path = resolved_file_path
        else:
            # Use resolved path (either no path provided or provided path doesn't exist)
            file_path = resolved_file_path
        
        if not os.path.exists(file_path):
            # Check if file exists in Django storage
            from django.core.files.storage import default_storage
            if default_storage.exists(uploaded_file.filename):
                try:
                    file_path = default_storage.path(uploaded_file.filename)
                except (NotImplementedError, AttributeError):
                    # Storage doesn't support path() - read from storage to temp file
                    import tempfile
                    with default_storage.open(uploaded_file.filename, 'rb') as f:
                        temp_fd, temp_path = tempfile.mkstemp(suffix='.pdf')
                        with os.fdopen(temp_fd, 'wb') as temp_file:
                            temp_file.write(f.read())
                        file_path = temp_path
                        logger.info(f"Copied file from storage to temp: {temp_path}")
            else:
                error_msg = (
                    f"File not found: {uploaded_file.filename}. "
                    f"The file may have been deleted. Please re-upload the file."
                )
                if uploaded_file:
                    uploaded_file.processing_status = 'failed'
                    uploaded_file.processing_error = error_msg
                    uploaded_file.save()
                raise ProcessingError(error_msg)
        
        chunks_data = []
        
        # Step 1: Validate PDF structure
        self._validate_pdf_structure(file_path, uploaded_file)
        
        # Step 2: Open PDF
        try:
            doc = fitz.open(file_path)
        except Exception as e:
            error_msg = (
                f"Failed to open PDF file. The file may be corrupted or encrypted. "
                f"File: {uploaded_file.filename} (ID: {uploaded_file.id}). "
                f"Error: {str(e)}. Please verify the file is a valid, unencrypted PDF and try re-uploading."
            )
            if uploaded_file:
                uploaded_file.processing_status = 'corrupted'
                uploaded_file.processing_error = error_msg
                uploaded_file.save()
            raise ProcessingError(error_msg)
        
        try:
            # SIMPLIFIED APPROACH: Just try to process pages sequentially
            # No need to check page count first - just access pages and process them
            # This is more robust and handles edge cases where page count is wrong
            
            pages_with_text = 0
            total_text_length = 0
            total_pages_processed = 0
            max_pages_to_try = 10000  # Reasonable upper limit to prevent infinite loops
            
            logger.info(f"Starting sequential page processing for PDF: {uploaded_file.filename}")
            
            # Process pages sequentially until we can't access any more
            for page_num in range(max_pages_to_try):
                try:
                    page = doc[page_num]
                    total_pages_processed = page_num + 1
                    
                    # Extract text using multiple methods
                    text = self._extract_text_from_page(page, page_num)
                    
                    if text and text.strip():
                        pages_with_text += 1
                        total_text_length += len(text)
                        
                        # Chunk the text
                        page_chunks = semantic_chunker.chunk_by_sentences(text, page_number=page_num + 1)
                        
                        for chunk in page_chunks:
                            chunks_data.append({
                                'content': chunk.content,
                                'page_number': chunk.page_number,
                                'chunk_index': len(chunks_data)
                            })
                            
                except (IndexError, RuntimeError):
                    # No more pages accessible - we've reached the end
                    if page_num == 0:
                        # Couldn't even access page 0 - PDF has no accessible pages
                        logger.warning(f"PDF has no accessible pages (cannot access page 0). File: {uploaded_file.filename}")
                    else:
                        # Successfully processed some pages before hitting the end
                        logger.info(f"Processed {total_pages_processed} pages (stopped at page {page_num + 1})")
                    break
                    
                except Exception as e:
                    # Other errors on this page - log and continue to next page
                    logger.warning(f"Error processing PDF page {page_num + 1}: {e}. Continuing to next page.")
                    continue
            
            # Log summary
            logger.info(f"PDF processing complete: {pages_with_text}/{total_pages_processed} pages with text, {len(chunks_data)} total chunks")
            
            # Check if we processed any pages
            if total_pages_processed == 0:
                # Check if PDF is encrypted/password-protected
                is_encrypted = getattr(doc, 'is_encrypted', False)
                needs_pass = getattr(doc, 'needs_pass', False)
                
                if is_encrypted or needs_pass:
                    error_msg = (
                        f"PDF file is encrypted or password-protected. "
                        f"File: {uploaded_file.filename} (ID: {uploaded_file.id}). "
                        f"Please provide an unencrypted PDF file."
                    )
                    logger.error(error_msg)
                    if uploaded_file:
                        uploaded_file.processing_status = 'corrupted'
                        uploaded_file.processing_error = error_msg
                        uploaded_file.save()
                    doc.close()
                    raise ProcessingError(error_msg)
            
            # Handle OCR if needed (only if we processed pages but found no text)
            if total_pages_processed > 0 and pages_with_text == 0:
                # No text found in any pages - try OCR
                if OCR_AVAILABLE and is_ocr_enabled() and ocr_processor:
                    logger.info(f"PDF has no extractable text ({total_pages_processed} pages processed). Attempting OCR...")
                    ocr_chunks = ocr_processor.process_pdf_with_ocr(
                        doc, file_path, total_pages_processed, uploaded_file=uploaded_file
                    )
                    if ocr_chunks:
                        chunks_data.extend(ocr_chunks)
                        logger.info(f"OCR successful: Generated {len(ocr_chunks)} chunks")
                else:
                    # Mark as no text available
                    if uploaded_file:
                        uploaded_file.processing_status = 'no_text_available'
                        uploaded_file.processing_error = (
                            f"PDF has no extractable text ({total_pages_processed} pages processed). "
                            f"OCR is {'not available' if not OCR_AVAILABLE else 'disabled'}. "
                            f"Please install pytesseract and Pillow to enable OCR for scanned PDFs."
                        )
                        uploaded_file.save()
                    return []
            elif total_pages_processed > 0 and pages_with_text < total_pages_processed * 0.1:
                # Less than 10% pages have text - try OCR on remaining
                if OCR_AVAILABLE and is_ocr_enabled() and ocr_processor:
                    logger.info(f"PDF has text in only {pages_with_text}/{total_pages_processed} pages. Attempting OCR on remaining pages...")
                    ocr_chunks = ocr_processor.process_pdf_with_ocr(
                        doc, file_path, total_pages_processed, skip_pages_with_text=True, uploaded_file=uploaded_file
                    )
                    if ocr_chunks:
                        chunks_data.extend(ocr_chunks)
                        logger.info(f"OCR on remaining pages successful: Generated {len(ocr_chunks)} additional chunks")
            
            return chunks_data
            
        finally:
            try:
                if doc and not doc.is_closed:
                    doc.close()
            except (ValueError, AttributeError):
                pass
    
    def _validate_pdf_structure(self, file_path: str, uploaded_file: UploadedFile) -> None:
        """Validate PDF file structure"""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(4)
                f.seek(-100, 2)
                footer = f.read(100)
            
            if not header.startswith(b'%PDF'):
                error_msg = (
                    f"File is not a valid PDF (missing PDF header). "
                    f"File: {uploaded_file.filename} (ID: {uploaded_file.id}). "
                    f"Please verify the file is a valid PDF and try re-uploading."
                )
                logger.error(error_msg)
                if uploaded_file:
                    uploaded_file.processing_status = 'corrupted'
                    uploaded_file.processing_error = error_msg
                    uploaded_file.save()
                raise ProcessingError(error_msg)
            
            if b'%%EOF' not in footer:
                error_msg = (
                    f"PDF file appears incomplete (missing EOF marker). "
                    f"File: {uploaded_file.filename} (ID: {uploaded_file.id}). "
                    f"Please try re-uploading the file."
                )
                logger.error(error_msg)
                if uploaded_file:
                    uploaded_file.processing_status = 'corrupted'
                    uploaded_file.processing_error = error_msg
                    uploaded_file.save()
                raise ProcessingError(error_msg)
        except Exception as e:
            raise
    
    
    def _extract_text_from_page(self, page: Any, page_num: int) -> str:
        """Extract text from PDF page using multiple methods"""
        text = None
        
        # Method 1: Standard get_text()
        try:
            text = page.get_text()
        except Exception:
            pass
        
        # Method 2: get_text('dict')
        if not text or not text.strip():
            try:
                text_dict = page.get_text('dict')
                text = ''
                for block in text_dict.get('blocks', []):
                    if 'lines' in block:
                        for line in block['lines']:
                            for span in line.get('spans', []):
                                text += span.get('text', '')
            except Exception:
                pass
        
        # Method 3: get_text('words')
        if not text or not text.strip():
            try:
                words = page.get_text('words')
                if words:
                    text = ' '.join([w[4] for w in words if len(w) > 4])
            except Exception:
                pass
        
        # Method 4: get_text('blocks')
        if not text or not text.strip():
            try:
                blocks = page.get_text('blocks')
                text = ''
                for block in blocks:
                    if len(block) >= 5:
                        text += block[4] + ' '
            except Exception:
                pass
        
        # Clean null bytes
        if text and isinstance(text, str):
            text = text.replace('\x00', '').replace('\0', '')
            text = ''.join(char for char in text if ord(char) >= 32 or char in ['\n', '\r', '\t'])
        
        # Ensure we always return a string (empty string if no text found)
        return text if text else ""

