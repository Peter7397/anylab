"""
Document utility functions for DocumentFile creation and management.
"""

import logging
import os
from pathlib import Path
from ..models import DocumentFile

logger = logging.getLogger(__name__)


def create_document_file_for_uploaded_file(uploaded_file) -> DocumentFile:
    """
    Create a DocumentFile record for an UploadedFile that doesn't have one
    This is a safety mechanism for legacy imports or manual UploadedFile creation
    """
    filename = uploaded_file.filename
    filename_base = os.path.splitext(filename)[0]
    file_ext = Path(filename).suffix.lower()
    
    # Map extensions to document types
    doc_type_map = {
        '.pdf': 'pdf',
        '.docx': 'docx',
        '.doc': 'doc',
        '.xlsx': 'xlsx',
        '.xls': 'xls',
        '.pptx': 'pptx',
        '.ppt': 'ppt',
        '.txt': 'txt',
        '.md': 'txt',
        '.html': 'html',
        '.htm': 'html',
        '.mhtml': 'html',
        '.rtf': 'rtf',
    }
    document_type = doc_type_map.get(file_ext, 'pdf')
    
    # Create DocumentFile
    # Ensure file_size is set correctly from UploadedFile
    file_size = uploaded_file.file_size if uploaded_file.file_size and uploaded_file.file_size > 0 else 0
    
    document_file = DocumentFile.objects.create(
        title=filename_base,
        filename=filename,
        document_type=document_type,
        description=f"Auto-created DocumentFile for: {filename}",
        uploaded_by=uploaded_file.uploaded_by,
        page_count=0,
        file_size=file_size,  # Use UploadedFile's file_size
        uploaded_file=uploaded_file,  # Link to UploadedFile
        metadata={
            'auto_created': True,
            'bulk_import': True,
            'import_source': 'automatic_processor'
        }
    )
    
    # If file_size was 0, try to get it from the actual file
    if file_size == 0:
        try:
            from .file_utils import get_file_path
            # os is already imported at module level
            file_path = get_file_path(uploaded_file)
            if os.path.exists(file_path):
                actual_size = os.path.getsize(file_path)
                if actual_size > 0:
                    document_file.file_size = actual_size
                    document_file.save()
                    logger.info(f"Updated DocumentFile {document_file.id} file_size to {actual_size} bytes from actual file")
        except Exception as e:
            logger.warning(f"Could not update DocumentFile file_size: {e}")
    
    logger.info(f"Created DocumentFile {document_file.id} for UploadedFile {uploaded_file.id}")
    return document_file

