"""
OCR processing coordinator.
"""

import logging
from .pdf_ocr import PDFOCRProcessor
from .image_ocr import ImageOCRProcessor

logger = logging.getLogger(__name__)


class OCRProcessor:
    """OCR processing coordinator"""
    
    def __init__(self):
        self.image_ocr = ImageOCRProcessor()
        self.pdf_ocr = PDFOCRProcessor(image_ocr_processor=self.image_ocr)
    
    def process_pdf_with_ocr(self, doc, file_path: str, total_pages: int, 
                             skip_pages_with_text: bool = False, 
                             uploaded_file=None, batch_size: int = 50):
        """
        Process PDF with OCR
        
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
        return self.pdf_ocr.process_pdf_with_ocr(
            doc, file_path, total_pages, skip_pages_with_text, uploaded_file, batch_size
        )

