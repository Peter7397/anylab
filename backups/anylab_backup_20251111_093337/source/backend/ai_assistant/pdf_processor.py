"""
PDF Document Processor

This module provides comprehensive PDF document processing capabilities
including text extraction, metadata extraction, OCR, and content analysis.
"""

import logging
import fitz  # PyMuPDF
import hashlib
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
from PIL import Image
import pytesseract
import cv2
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class PDFMetadata:
    """PDF metadata structure"""
    title: str
    author: str
    subject: str
    creator: str
    producer: str
    creation_date: Optional[datetime]
    modification_date: Optional[datetime]
    page_count: int
    file_size: int
    file_hash: str
    language: Optional[str]
    keywords: List[str]
    pdf_version: str
    is_encrypted: bool
    has_images: bool
    has_tables: bool
    has_forms: bool
    has_annotations: bool


@dataclass
class PDFPage:
    """PDF page structure"""
    page_number: int
    text: str
    images: List[Dict[str, Any]]
    tables: List[Dict[str, Any]]
    forms: List[Dict[str, Any]]
    annotations: List[Dict[str, Any]]
    dimensions: Tuple[float, float]
    rotation: int
    has_text: bool
    has_images: bool
    has_tables: bool
    has_forms: bool
    has_annotations: bool


@dataclass
class PDFContent:
    """PDF content structure"""
    metadata: PDFMetadata
    pages: List[PDFPage]
    full_text: str
    extracted_images: List[Dict[str, Any]]
    extracted_tables: List[Dict[str, Any]]
    extracted_forms: List[Dict[str, Any]]
    extracted_annotations: List[Dict[str, Any]]
    content_summary: str
    keywords: List[str]
    topics: List[str]
    quality_score: float
    processing_time: float


class PDFProcessor:
    """Comprehensive PDF document processor"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize PDF processor with configuration"""
        self.config = config or {}
        self.ocr_enabled = self.config.get('ocr_enabled', True)
        self.table_extraction_enabled = self.config.get('table_extraction_enabled', True)
        self.form_extraction_enabled = self.config.get('form_extraction_enabled', True)
        self.annotation_extraction_enabled = self.config.get('annotation_extraction_enabled', True)
        self.image_extraction_enabled = self.config.get('image_extraction_enabled', True)
        self.language_detection_enabled = self.config.get('language_detection_enabled', True)
        self.content_analysis_enabled = self.config.get('content_analysis_enabled', True)
        
        # OCR configuration
        self.ocr_language = self.config.get('ocr_language', 'eng')
        self.ocr_config = self.config.get('ocr_config', '--psm 6')
        
        # Image processing configuration
        self.image_dpi = self.config.get('image_dpi', 300)
        self.image_quality = self.config.get('image_quality', 95)
        
        # Content analysis configuration
        self.min_text_length = self.config.get('min_text_length', 100)
        self.max_keywords = self.config.get('max_keywords', 20)
        
        logger.info("PDF Processor initialized with configuration")
    
    def process_pdf(self, file_path: str) -> PDFContent:
        """Process a PDF file and extract all content"""
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting PDF processing for: {file_path}")
            
            # Open PDF document
            doc = fitz.open(file_path)
            
            # Extract metadata
            metadata = self._extract_metadata(doc, file_path)
            
            # Extract pages
            pages = self._extract_pages(doc)
            
            # Extract full text
            full_text = self._extract_full_text(pages)
            
            # Extract images
            extracted_images = self._extract_images(doc) if self.image_extraction_enabled else []
            
            # Extract tables
            extracted_tables = self._extract_tables(pages) if self.table_extraction_enabled else []
            
            # Extract forms
            extracted_forms = self._extract_forms(pages) if self.form_extraction_enabled else []
            
            # Extract annotations
            extracted_annotations = self._extract_annotations(pages) if self.annotation_extraction_enabled else []
            
            # Analyze content
            content_summary = self._analyze_content(full_text) if self.content_analysis_enabled else ""
            keywords = self._extract_keywords(full_text) if self.content_analysis_enabled else []
            topics = self._extract_topics(full_text) if self.content_analysis_enabled else []
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(metadata, pages, full_text)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Create PDF content object
            pdf_content = PDFContent(
                metadata=metadata,
                pages=pages,
                full_text=full_text,
                extracted_images=extracted_images,
                extracted_tables=extracted_tables,
                extracted_forms=extracted_forms,
                extracted_annotations=extracted_annotations,
                content_summary=content_summary,
                keywords=keywords,
                topics=topics,
                quality_score=quality_score,
                processing_time=processing_time
            )
            
            logger.info(f"PDF processing completed in {processing_time:.2f} seconds")
            return pdf_content
            
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            raise
        finally:
            if 'doc' in locals():
                doc.close()
    
    def _extract_metadata(self, doc: fitz.Document, file_path: str) -> PDFMetadata:
        """Extract PDF metadata"""
        try:
            metadata = doc.metadata
            
            # Get file information
            file_size = Path(file_path).stat().st_size
            file_hash = self._calculate_file_hash(file_path)
            
            # Parse dates
            creation_date = self._parse_date(metadata.get('creationDate', ''))
            modification_date = self._parse_date(metadata.get('modDate', ''))
            
            # Check for various content types
            has_images = self._check_for_images(doc)
            has_tables = self._check_for_tables(doc)
            has_forms = self._check_for_forms(doc)
            has_annotations = self._check_for_annotations(doc)
            
            # Detect language
            language = self._detect_language(doc) if self.language_detection_enabled else None
            
            # Extract keywords
            keywords = self._extract_metadata_keywords(metadata)
            
            return PDFMetadata(
                title=metadata.get('title', ''),
                author=metadata.get('author', ''),
                subject=metadata.get('subject', ''),
                creator=metadata.get('creator', ''),
                producer=metadata.get('producer', ''),
                creation_date=creation_date,
                modification_date=modification_date,
                page_count=doc.page_count,
                file_size=file_size,
                file_hash=file_hash,
                language=language,
                keywords=keywords,
                pdf_version=doc.metadata.get('format', ''),
                is_encrypted=doc.is_encrypted,
                has_images=has_images,
                has_tables=has_tables,
                has_forms=has_forms,
                has_annotations=has_annotations
            )
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            raise
    
    def _extract_pages(self, doc: fitz.Document) -> List[PDFPage]:
        """Extract content from all pages"""
        pages = []
        
        for page_num in range(doc.page_count):
            try:
                page = doc[page_num]
                
                # Extract text
                text = page.get_text()
                
                # Extract images
                images = self._extract_page_images(page, page_num) if self.image_extraction_enabled else []
                
                # Extract tables
                tables = self._extract_page_tables(page, page_num) if self.table_extraction_enabled else []
                
                # Extract forms
                forms = self._extract_page_forms(page, page_num) if self.form_extraction_enabled else []
                
                # Extract annotations
                annotations = self._extract_page_annotations(page, page_num) if self.annotation_extraction_enabled else []
                
                # Get page dimensions and rotation
                rect = page.rect
                dimensions = (rect.width, rect.height)
                rotation = page.rotation
                
                # Create page object
                pdf_page = PDFPage(
                    page_number=page_num + 1,
                    text=text,
                    images=images,
                    tables=tables,
                    forms=forms,
                    annotations=annotations,
                    dimensions=dimensions,
                    rotation=rotation,
                    has_text=len(text.strip()) > 0,
                    has_images=len(images) > 0,
                    has_tables=len(tables) > 0,
                    has_forms=len(forms) > 0,
                    has_annotations=len(annotations) > 0
                )
                
                pages.append(pdf_page)
                
            except Exception as e:
                logger.error(f"Error processing page {page_num + 1}: {e}")
                continue
        
        return pages
    
    def _extract_full_text(self, pages: List[PDFPage]) -> str:
        """Extract full text from all pages"""
        full_text = ""
        
        for page in pages:
            if page.text:
                full_text += page.text + "\n"
        
        return full_text.strip()
    
    def _extract_images(self, doc: fitz.Document) -> List[Dict[str, Any]]:
        """Extract images from PDF"""
        images = []
        
        for page_num in range(doc.page_count):
            try:
                page = doc[page_num]
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    try:
                        # Get image data
                        xref = img[0]
                        pix = fitz.Pixmap(doc, xref)
                        
                        if pix.n - pix.alpha < 4:  # GRAY or RGB
                            # Convert to PIL Image
                            img_data = pix.tobytes("png")
                            pil_image = Image.open(io.BytesIO(img_data))
                            
                            # Perform OCR if enabled
                            ocr_text = ""
                            if self.ocr_enabled:
                                ocr_text = self._perform_ocr(pil_image)
                            
                            # Extract image metadata
                            image_info = {
                                'page_number': page_num + 1,
                                'image_index': img_index,
                                'width': pix.width,
                                'height': pix.height,
                                'colorspace': pix.colorspace.name if pix.colorspace else 'Unknown',
                                'has_alpha': pix.alpha > 0,
                                'ocr_text': ocr_text,
                                'file_size': len(img_data),
                                'format': 'PNG'
                            }
                            
                            images.append(image_info)
                            
                        pix = None
                        
                    except Exception as e:
                        logger.error(f"Error processing image {img_index} on page {page_num + 1}: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"Error processing images on page {page_num + 1}: {e}")
                continue
        
        return images
    
    def _extract_tables(self, pages: List[PDFPage]) -> List[Dict[str, Any]]:
        """Extract tables from PDF pages"""
        tables = []
        
        for page in pages:
            try:
                # Use PyMuPDF's table extraction
                page_tables = page.get_tables()
                
                for table_index, table in enumerate(page_tables):
                    table_info = {
                        'page_number': page.page_number,
                        'table_index': table_index,
                        'rows': len(table),
                        'columns': len(table[0]) if table else 0,
                        'data': table,
                        'has_header': self._detect_table_header(table),
                        'structure': self._analyze_table_structure(table)
                    }
                    
                    tables.append(table_info)
                    
            except Exception as e:
                logger.error(f"Error extracting tables from page {page.page_number}: {e}")
                continue
        
        return tables
    
    def _extract_forms(self, pages: List[PDFPage]) -> List[Dict[str, Any]]:
        """Extract form fields from PDF pages"""
        forms = []
        
        for page in pages:
            try:
                # Extract form fields
                form_fields = page.get_form_fields()
                
                for field_name, field_info in form_fields.items():
                    form_info = {
                        'page_number': page.page_number,
                        'field_name': field_name,
                        'field_type': field_info.get('field_type', 'Unknown'),
                        'field_value': field_info.get('field_value', ''),
                        'is_required': field_info.get('required', False),
                        'is_readonly': field_info.get('readonly', False),
                        'rect': field_info.get('rect', None)
                    }
                    
                    forms.append(form_info)
                    
            except Exception as e:
                logger.error(f"Error extracting forms from page {page.page_number}: {e}")
                continue
        
        return forms
    
    def _extract_annotations(self, pages: List[PDFPage]) -> List[Dict[str, Any]]:
        """Extract annotations from PDF pages"""
        annotations = []
        
        for page in pages:
            try:
                # Extract annotations
                page_annotations = page.get_annotations()
                
                for ann_index, ann in enumerate(page_annotations):
                    ann_info = {
                        'page_number': page.page_number,
                        'annotation_index': ann_index,
                        'type': ann.get('type', 'Unknown'),
                        'content': ann.get('content', ''),
                        'author': ann.get('author', ''),
                        'subject': ann.get('subject', ''),
                        'rect': ann.get('rect', None),
                        'created_date': ann.get('created_date', None),
                        'modified_date': ann.get('modified_date', None)
                    }
                    
                    annotations.append(ann_info)
                    
            except Exception as e:
                logger.error(f"Error extracting annotations from page {page.page_number}: {e}")
                continue
        
        return annotations
    
    def _analyze_content(self, text: str) -> str:
        """Analyze content and generate summary"""
        if not text or len(text) < self.min_text_length:
            return "Content too short for analysis"
        
        # Simple content analysis
        sentences = text.split('.')
        word_count = len(text.split())
        
        # Generate basic summary
        summary = f"Document contains {word_count} words across {len(sentences)} sentences. "
        
        # Add content type analysis
        if 'troubleshooting' in text.lower():
            summary += "Content appears to be troubleshooting-related. "
        if 'error' in text.lower():
            summary += "Content mentions errors or issues. "
        if 'solution' in text.lower():
            summary += "Content provides solutions. "
        
        return summary.strip()
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        if not text:
            return []
        
        # Simple keyword extraction
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        word_freq = {}
        
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and return top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        keywords = [word for word, freq in sorted_words[:self.max_keywords]]
        
        return keywords
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract topics from text"""
        if not text:
            return []
        
        # Simple topic extraction based on common patterns
        topics = []
        
        # Check for common Agilent/Lab topics
        if 'openlab' in text.lower():
            topics.append('OpenLab')
        if 'masshunter' in text.lower():
            topics.append('MassHunter')
        if 'chemstation' in text.lower():
            topics.append('ChemStation')
        if 'vnmrj' in text.lower():
            topics.append('VNMRJ')
        if 'troubleshooting' in text.lower():
            topics.append('Troubleshooting')
        if 'maintenance' in text.lower():
            topics.append('Maintenance')
        if 'installation' in text.lower():
            topics.append('Installation')
        if 'configuration' in text.lower():
            topics.append('Configuration')
        
        return topics
    
    def _calculate_quality_score(self, metadata: PDFMetadata, pages: List[PDFPage], text: str) -> float:
        """Calculate quality score for the PDF"""
        score = 0.0
        
        # Base score
        score += 0.1
        
        # Text content score
        if text and len(text) > 100:
            score += 0.3
        
        # Metadata completeness score
        if metadata.title:
            score += 0.1
        if metadata.author:
            score += 0.1
        if metadata.subject:
            score += 0.1
        
        # Content diversity score
        if metadata.has_images:
            score += 0.1
        if metadata.has_tables:
            score += 0.1
        if metadata.has_forms:
            score += 0.1
        
        # Page count score
        if metadata.page_count > 0:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate file hash"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse PDF date string"""
        if not date_str:
            return None
        
        try:
            # PDF date format: D:YYYYMMDDHHmmSSOHH'mm'
            if date_str.startswith('D:'):
                date_str = date_str[2:]
            
            # Extract date components
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            hour = int(date_str[8:10])
            minute = int(date_str[10:12])
            second = int(date_str[12:14])
            
            return datetime(year, month, day, hour, minute, second)
            
        except (ValueError, IndexError):
            return None
    
    def _check_for_images(self, doc: fitz.Document) -> bool:
        """Check if PDF contains images"""
        for page_num in range(min(doc.page_count, 5)):  # Check first 5 pages
            page = doc[page_num]
            if page.get_images():
                return True
        return False
    
    def _check_for_tables(self, doc: fitz.Document) -> bool:
        """Check if PDF contains tables"""
        for page_num in range(min(doc.page_count, 5)):  # Check first 5 pages
            page = doc[page_num]
            if page.get_tables():
                return True
        return False
    
    def _check_for_forms(self, doc: fitz.Document) -> bool:
        """Check if PDF contains forms"""
        for page_num in range(min(doc.page_count, 5)):  # Check first 5 pages
            page = doc[page_num]
            if page.get_form_fields():
                return True
        return False
    
    def _check_for_annotations(self, doc: fitz.Document) -> bool:
        """Check if PDF contains annotations"""
        for page_num in range(min(doc.page_count, 5)):  # Check first 5 pages
            page = doc[page_num]
            if page.get_annotations():
                return True
        return False
    
    def _detect_language(self, doc: fitz.Document) -> Optional[str]:
        """Detect document language"""
        # Simple language detection based on common words
        text = ""
        for page_num in range(min(doc.page_count, 3)):  # Check first 3 pages
            page = doc[page_num]
            text += page.get_text()
        
        if not text:
            return None
        
        # Check for common English words
        english_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        text_lower = text.lower()
        english_count = sum(1 for word in english_words if word in text_lower)
        
        if english_count > 5:
            return 'en'
        
        return None
    
    def _extract_metadata_keywords(self, metadata: Dict[str, str]) -> List[str]:
        """Extract keywords from metadata"""
        keywords = []
        
        # Extract from subject
        if metadata.get('subject'):
            keywords.extend(metadata['subject'].split(','))
        
        # Extract from keywords field
        if metadata.get('keywords'):
            keywords.extend(metadata['keywords'].split(','))
        
        # Clean and filter keywords
        keywords = [kw.strip() for kw in keywords if kw.strip()]
        return keywords[:10]  # Limit to 10 keywords
    
    def _extract_page_images(self, page: fitz.Page, page_num: int) -> List[Dict[str, Any]]:
        """Extract images from a specific page"""
        images = []
        image_list = page.get_images()
        
        for img_index, img in enumerate(image_list):
            try:
                xref = img[0]
                pix = fitz.Pixmap(page.parent, xref)
                
                if pix.n - pix.alpha < 4:  # GRAY or RGB
                    image_info = {
                        'image_index': img_index,
                        'width': pix.width,
                        'height': pix.height,
                        'colorspace': pix.colorspace.name if pix.colorspace else 'Unknown',
                        'has_alpha': pix.alpha > 0
                    }
                    images.append(image_info)
                
                pix = None
                
            except Exception as e:
                logger.error(f"Error processing image {img_index} on page {page_num + 1}: {e}")
                continue
        
        return images
    
    def _extract_page_tables(self, page: fitz.Page, page_num: int) -> List[Dict[str, Any]]:
        """Extract tables from a specific page"""
        tables = []
        page_tables = page.get_tables()
        
        for table_index, table in enumerate(page_tables):
            table_info = {
                'table_index': table_index,
                'rows': len(table),
                'columns': len(table[0]) if table else 0,
                'data': table
            }
            tables.append(table_info)
        
        return tables
    
    def _extract_page_forms(self, page: fitz.Page, page_num: int) -> List[Dict[str, Any]]:
        """Extract forms from a specific page"""
        forms = []
        form_fields = page.get_form_fields()
        
        for field_name, field_info in form_fields.items():
            form_info = {
                'field_name': field_name,
                'field_type': field_info.get('field_type', 'Unknown'),
                'field_value': field_info.get('field_value', ''),
                'is_required': field_info.get('required', False),
                'is_readonly': field_info.get('readonly', False)
            }
            forms.append(form_info)
        
        return forms
    
    def _extract_page_annotations(self, page: fitz.Page, page_num: int) -> List[Dict[str, Any]]:
        """Extract annotations from a specific page"""
        annotations = []
        page_annotations = page.get_annotations()
        
        for ann_index, ann in enumerate(page_annotations):
            ann_info = {
                'annotation_index': ann_index,
                'type': ann.get('type', 'Unknown'),
                'content': ann.get('content', ''),
                'author': ann.get('author', ''),
                'subject': ann.get('subject', '')
            }
            annotations.append(ann_info)
        
        return annotations
    
    def _perform_ocr(self, image: Image.Image) -> str:
        """Perform OCR on image"""
        try:
            # Convert PIL image to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Preprocess image for better OCR
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Apply thresholding
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Convert back to PIL
            pil_image = Image.fromarray(thresh)
            
            # Perform OCR
            ocr_text = pytesseract.image_to_string(pil_image, lang=self.ocr_language, config=self.ocr_config)
            
            return ocr_text.strip()
            
        except Exception as e:
            logger.error(f"Error performing OCR: {e}")
            return ""
    
    def _detect_table_header(self, table: List[List[str]]) -> bool:
        """Detect if table has a header row"""
        if not table or len(table) < 2:
            return False
        
        # Simple header detection
        first_row = table[0]
        second_row = table[1]
        
        # Check if first row contains mostly text (not numbers)
        text_count = sum(1 for cell in first_row if not cell.replace('.', '').replace(',', '').isdigit())
        
        return text_count > len(first_row) / 2
    
    def _analyze_table_structure(self, table: List[List[str]]) -> Dict[str, Any]:
        """Analyze table structure"""
        if not table:
            return {}
        
        structure = {
            'row_count': len(table),
            'column_count': len(table[0]) if table else 0,
            'has_header': self._detect_table_header(table),
            'is_regular': self._is_regular_table(table),
            'data_types': self._analyze_data_types(table)
        }
        
        return structure
    
    def _is_regular_table(self, table: List[List[str]]) -> bool:
        """Check if table has regular structure"""
        if not table:
            return False
        
        expected_columns = len(table[0])
        for row in table[1:]:
            if len(row) != expected_columns:
                return False
        
        return True
    
    def _analyze_data_types(self, table: List[List[str]]) -> List[str]:
        """Analyze data types in table columns"""
        if not table:
            return []
        
        data_types = []
        for col_index in range(len(table[0])):
            column_data = [row[col_index] for row in table if col_index < len(row)]
            
            # Analyze column data type
            if all(cell.replace('.', '').replace(',', '').isdigit() for cell in column_data if cell):
                data_types.append('numeric')
            elif all(cell.lower() in ['true', 'false', 'yes', 'no'] for cell in column_data if cell):
                data_types.append('boolean')
            else:
                data_types.append('text')
        
        return data_types
