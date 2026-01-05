"""
Metadata extraction coordinator for all file types.
"""

import logging
import os
from pathlib import Path
from django.conf import settings
from django.core.cache import cache
from ...utils.file_utils import get_file_path

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Extract metadata from various file types"""
    
    def extract_all_metadata(self, uploaded_file) -> dict:
        """
        Extract all metadata for an uploaded file with caching.
        
        Args:
            uploaded_file: UploadedFile instance
            
        Returns:
            Dictionary with metadata
        """
        # Check cache first
        cache_key = f"metadata_{uploaded_file.id}_{uploaded_file.file_hash}"
        cached_metadata = cache.get(cache_key)
        if cached_metadata:
            logger.debug(f"Using cached metadata for {uploaded_file.filename}")
            return cached_metadata
        
        # Extract ALL metadata from file
        # Extract basic metadata from database record first (always available)
        file_ext = Path(uploaded_file.filename).suffix.lower()
        metadata = {
            'filename': uploaded_file.filename,
            'file_size': uploaded_file.file_size or 0,
            'file_hash': uploaded_file.file_hash or '',
            'uploaded_at': str(uploaded_file.uploaded_at),
            'file_extension': file_ext
        }
        
        try:
            # Get file path
            file_path = get_file_path(uploaded_file)
            
            if not os.path.exists(file_path):
                logger.warning(f"File not found at {file_path}, using basic metadata from database record")
                # Return basic metadata even if file doesn't exist
                # This allows processing to continue with database metadata
                return metadata
            
            # PDF-specific metadata
            if file_ext == '.pdf' and os.path.exists(file_path):
                try:
                    import fitz  # PyMuPDF
                    doc = fitz.open(file_path)
                    # Extract PDF metadata
                    pdf_metadata = doc.metadata
                    metadata.update({
                        'pdf_title': pdf_metadata.get('title', ''),
                        'pdf_author': pdf_metadata.get('author', ''),
                        'pdf_subject': pdf_metadata.get('subject', ''),
                        'pdf_creator': pdf_metadata.get('creator', ''),
                        'pdf_producer': pdf_metadata.get('producer', ''),
                        'pdf_pages': doc.page_count
                    })
                    doc.close()
                except Exception as e:
                    logger.warning(f"Could not extract PDF metadata: {e}")
            
            # Word Document metadata (.docx, .doc)
            elif file_ext in ['.docx', '.doc']:
                try:
                    from docx import Document
                    doc = Document(file_path)
                    core_props = doc.core_properties
                    metadata.update({
                        'word_title': core_props.title or '',
                        'word_author': core_props.author or '',
                        'word_subject': core_props.subject or '',
                        'word_created': str(core_props.created) if core_props.created else '',
                        'word_modified': str(core_props.modified) if core_props.modified else '',
                        'word_paragraphs': len([p for p in doc.paragraphs])
                    })
                except ImportError:
                    logger.warning("python-docx not available for Word metadata extraction")
                except Exception as e:
                    logger.warning(f"Could not extract Word metadata: {e}")
            
            # Excel Spreadsheet metadata (.xlsx, .xls)
            elif file_ext in ['.xlsx', '.xls']:
                try:
                    import openpyxl
                    workbook = openpyxl.load_workbook(file_path, read_only=True)
                    props = workbook.properties
                    metadata.update({
                        'excel_title': props.title or '',
                        'excel_author': props.creator or '',
                        'excel_subject': props.subject or '',
                        'excel_created': str(props.created) if props.created else '',
                        'excel_modified': str(props.modified) if props.modified else '',
                        'excel_sheets': len(workbook.sheetnames),
                        'excel_sheet_names': workbook.sheetnames
                    })
                except ImportError:
                    logger.warning("openpyxl not available for Excel metadata extraction")
                except Exception as e:
                    logger.warning(f"Could not extract Excel metadata: {e}")
            
            # PowerPoint Presentation metadata (.pptx, .ppt)
            elif file_ext in ['.pptx', '.ppt']:
                try:
                    from pptx import Presentation
                    prs = Presentation(file_path)
                    core_props = prs.core_properties
                    metadata.update({
                        'ppt_title': core_props.title or '',
                        'ppt_author': core_props.author or '',
                        'ppt_subject': core_props.subject or '',
                        'ppt_created': str(core_props.created) if core_props.created else '',
                        'ppt_modified': str(core_props.modified) if core_props.modified else '',
                        'ppt_slides': len(prs.slides)
                    })
                except ImportError:
                    logger.warning("python-pptx not available for PowerPoint metadata extraction")
                except Exception as e:
                    logger.warning(f"Could not extract PowerPoint metadata: {e}")
            
            # Image metadata (.jpg, .png, .gif, .bmp, etc.)
            elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']:
                try:
                    from PIL import Image, ExifTags
                    from PIL.ExifTags import TAGS
                    img = Image.open(file_path)
                    metadata.update({
                        'image_format': img.format,
                        'image_mode': img.mode,
                        'image_size': f"{img.width}x{img.height}",
                        'image_width': img.width,
                        'image_height': img.height
                    })
                    
                    # Try to extract EXIF data
                    if hasattr(img, '_getexif'):
                        exifdata = img._getexif()
                        if exifdata:
                            exif_meta = {}
                            for tag_id in exifdata:
                                tag = TAGS.get(tag_id, tag_id)
                                exif_meta[tag] = exifdata.get(tag_id)
                            if exif_meta:
                                metadata['exif_data'] = exif_meta
                except ImportError:
                    logger.warning("Pillow not available for image metadata extraction")
                except Exception as e:
                    logger.warning(f"Could not extract image metadata: {e}")
            
            # Text file metadata
            elif file_ext in ['.txt', '.rtf', '.md']:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        metadata.update({
                            'text_lines': len(lines),
                            'text_words': sum(len(line.split()) for line in lines),
                            'text_size': os.path.getsize(file_path)
                        })
                except Exception as e:
                    logger.warning(f"Could not extract text metadata: {e}")
            
            # HTML metadata
            elif file_ext in ['.html', '.htm', '.mhtml']:
                try:
                    metadata.update({
                        'html_file': True,
                        'mime_type': 'text/html'
                    })
                except Exception as e:
                    logger.warning(f"Could not extract HTML metadata: {e}")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Metadata extraction error: {e}")
            # Return basic metadata from database even if file extraction fails
            # This ensures validation can pass with at least database metadata
            return metadata

