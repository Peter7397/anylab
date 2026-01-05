"""
PDF OCR processing module.
"""

import logging
import os
import io
import fitz  # PyMuPDF
import subprocess
import tempfile
import shutil
import glob
import numpy as np
from django.core.cache import cache
from ...enhanced_chunking import semantic_chunker
from ...models import DocumentChunk

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


class PDFOCRProcessor:
    """Process PDF pages with OCR"""
    
    def __init__(self, image_ocr_processor=None):
        self.image_ocr = image_ocr_processor
        # Get OCR languages from settings
        from django.conf import settings
        self.ocr_languages = getattr(settings, 'OCR_LANGUAGES', ['eng'])
        if isinstance(self.ocr_languages, str):
            self.ocr_languages = [lang.strip() for lang in self.ocr_languages.split(',')]
        self.tesseract_lang = '+'.join(self.ocr_languages) if len(self.ocr_languages) > 1 else self.ocr_languages[0]
        logger.info(f"PDFOCRProcessor initialized with languages: {self.tesseract_lang}")
    
    def process_pdf_with_ocr(self, doc, file_path: str, total_pages: int, 
                             skip_pages_with_text: bool = False, 
                             uploaded_file=None, batch_size: int = 50):
        """
        Process scanned PDF pages using OCR
        
        Args:
            doc: PyMuPDF document object
            file_path: Path to PDF file
            total_pages: Total number of pages
            skip_pages_with_text: If True, only OCR pages that have no text
            uploaded_file: UploadedFile instance
            batch_size: Batch size for incremental saving
            
        Returns:
            List of chunk data dictionaries
        """
        if not OCR_AVAILABLE:
            logger.warning("OCR not available - pytesseract or Pillow not installed")
            return []
        
        ocr_chunks = []
        
        # OCR result caching
        file_hash = uploaded_file.file_hash if uploaded_file else None
        cache_key_base = f"ocr_result_{file_hash}" if file_hash else None
        
        pages_per_batch = 5 if total_pages > 50 else 10
        
        try:
            logger.info(f"Starting OCR processing for {total_pages} pages...")
            
            processed_pages = 0
            
            # Handle force OCR mode (PDF with 0 pages but valid structure)
            actual_page_count = len(doc)
            force_ocr_mode = (total_pages == 1 and actual_page_count == 0)
            
            if force_ocr_mode:
                ocr_chunks = self._try_alternative_rendering(file_path, uploaded_file)
                if ocr_chunks:
                    return ocr_chunks
            
            # Process each page
            for page_num in range(total_pages):
                if page_num % 5 == 0 and page_num > 0:
                    progress_pct = (page_num / total_pages) * 100
                    logger.info(f"OCR progress: {page_num}/{total_pages} pages ({progress_pct:.1f}%)")
                    if uploaded_file:
                        try:
                            uploaded_file.processing_progress = progress_pct
                            uploaded_file.save(update_fields=['processing_progress'])
                        except Exception:
                            pass
                
                # Check cache
                page_text = None
                if cache_key_base:
                    cache_key = f"{cache_key_base}_page_{page_num + 1}"
                    cached_text = cache.get(cache_key)
                    if cached_text:
                        logger.debug(f"Using cached OCR result for page {page_num + 1}")
                        page_text = cached_text
                        if page_text and page_text.strip():
                            page_chunks = semantic_chunker.chunk_by_sentences(page_text, page_number=page_num + 1)
                            for chunk in page_chunks:
                                chunk_data = {
                                    'content': chunk.content,
                                    'page_number': chunk.page_number,
                                    'chunk_index': len(ocr_chunks),
                                    'source': 'ocr_cached'
                                }
                                ocr_chunks.append(chunk_data)
                                
                                if uploaded_file and len(ocr_chunks) % batch_size == 0:
                                    self._save_ocr_chunks_batch(ocr_chunks[-batch_size:], uploaded_file)
                        processed_pages += 1
                        continue
                
                try:
                    page = doc[page_num]
                    
                    # Skip pages with text if requested
                    if skip_pages_with_text:
                        existing_text = page.get_text()
                        if existing_text and existing_text.strip():
                            continue
                    
                    # Process embedded images first
                    page_ocr_texts = []
                    images = page.get_images()
                    
                    if images:
                        for img_info in images:
                            try:
                                xref = img_info[0]
                                base_image = doc.extract_image(xref)
                                image_bytes = base_image["image"]
                                pil_image = Image.open(io.BytesIO(image_bytes))
                                
                                if self.image_ocr:
                                    ocr_result = self.image_ocr.ocr_image(pil_image, page_num + 1, f"embedded_image_{xref}")
                                    img_text = ocr_result.get('text', '') if isinstance(ocr_result, dict) else ocr_result
                                else:
                                    img_text = pytesseract.image_to_string(pil_image, lang=self.tesseract_lang)
                                
                                if img_text and img_text.strip():
                                    page_ocr_texts.append(img_text)
                            except Exception as e:
                                logger.debug(f"Error processing embedded image: {e}")
                    
                    # Render page as image and OCR
                    try:
                        # Adaptive DPI based on page size
                        zoom = 2.0  # Default zoom
                        mat = fitz.Matrix(zoom, zoom)
                        pix = page.get_pixmap(matrix=mat)
                        pil_image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        
                        if self.image_ocr:
                            ocr_result = self.image_ocr.ocr_image(pil_image, page_num + 1, "pdf_page")
                            page_text = ocr_result.get('text', '') if isinstance(ocr_result, dict) else ocr_result
                        else:
                            page_text = pytesseract.image_to_string(pil_image, lang=self.tesseract_lang)
                        
                        if page_text and page_text.strip():
                            page_ocr_texts.append(page_text)
                    except Exception as e:
                        logger.warning(f"Error rendering page {page_num + 1} for OCR: {e}")
                    
                    # Combine all OCR text from page
                    combined_text = '\n'.join(page_ocr_texts)
                    
                    if combined_text and combined_text.strip():
                        # Cache the result
                        if cache_key_base:
                            cache_key = f"{cache_key_base}_page_{page_num + 1}"
                            cache.set(cache_key, combined_text, 24 * 3600)  # 24 hours
                        
                        # Chunk the text
                        page_chunks = semantic_chunker.chunk_by_sentences(combined_text, page_number=page_num + 1)
                        for chunk in page_chunks:
                            chunk_data = {
                                'content': chunk.content,
                                'page_number': chunk.page_number,
                                'chunk_index': len(ocr_chunks),
                                'source': 'ocr'
                            }
                            ocr_chunks.append(chunk_data)
                            
                            # Incremental saving
                            if uploaded_file and len(ocr_chunks) % batch_size == 0:
                                self._save_ocr_chunks_batch(ocr_chunks[-batch_size:], uploaded_file)
                        
                        processed_pages += 1
                
                except Exception as e:
                    logger.warning(f"Error processing page {page_num + 1} with OCR: {e}")
                    continue
            
            logger.info(f"OCR completed: {processed_pages}/{total_pages} pages processed, {len(ocr_chunks)} chunks created")
            return ocr_chunks
            
        except Exception as e:
            logger.error(f"OCR processing error: {e}", exc_info=True)
            return []
    
    def _try_alternative_rendering(self, file_path, uploaded_file):
        """Try alternative rendering methods for problematic PDFs"""
        try:
            temp_dir = tempfile.mkdtemp()
            try:
                result = subprocess.run(
                    ['pdftoppm', '-png', '-r', '150', file_path, f'{temp_dir}/page'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    image_files = sorted(glob.glob(f'{temp_dir}/page-*.png'))
                    if image_files:
                        logger.info(f"Successfully rendered {len(image_files)} pages using pdftoppm")
                        ocr_chunks = []
                        for idx, img_path in enumerate(image_files):
                            try:
                                img = Image.open(img_path)
                                if self.image_ocr:
                                    ocr_result = self.image_ocr.ocr_image(img, idx + 1, "pdftoppm")
                                    page_text = ocr_result.get('text', '') if isinstance(ocr_result, dict) else ocr_result
                                else:
                                    page_text = pytesseract.image_to_string(img, lang=self.tesseract_lang)
                                
                                if page_text and page_text.strip():
                                    page_chunks = semantic_chunker.chunk_by_sentences(page_text, page_number=idx + 1)
                                    for chunk in page_chunks:
                                        chunk_data = {
                                            'content': chunk.content,
                                            'page_number': chunk.page_number,
                                            'chunk_index': len(ocr_chunks),
                                            'source': 'ocr_pdftoppm'
                                        }
                                        ocr_chunks.append(chunk_data)
                            except Exception as e:
                                logger.warning(f"Error processing rendered page {idx + 1}: {e}")
                        
                        if ocr_chunks:
                            logger.info(f"OCR successful via pdftoppm: Generated {len(ocr_chunks)} chunks")
                            shutil.rmtree(temp_dir)
                            return ocr_chunks
            finally:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
        except FileNotFoundError:
            logger.warning("pdftoppm not available")
        except Exception as e:
            logger.warning(f"Alternative rendering failed: {e}")
        
        return []
    
    def _save_ocr_chunks_batch(self, chunks_batch, uploaded_file):
        """Save a batch of OCR chunks to database"""
        try:
            saved_count = 0
            for saved_chunk in chunks_batch:
                if not DocumentChunk.objects.filter(
                    uploaded_file=uploaded_file,
                    chunk_index=saved_chunk.get('chunk_index', -1)
                ).exists():
                    DocumentChunk.objects.create(
                        uploaded_file=uploaded_file,
                        content=saved_chunk['content'],
                        page_number=saved_chunk['page_number'],
                        chunk_index=saved_chunk.get('chunk_index', 0)
                    )
                    saved_count += 1
            if saved_count > 0:
                logger.debug(f"Incrementally saved {saved_count} chunks to database")
        except Exception as e:
            logger.warning(f"Failed to save chunks batch: {e}")

