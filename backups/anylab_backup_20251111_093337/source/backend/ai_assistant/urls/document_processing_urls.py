"""
Document Processing URL Configuration

This module contains URL patterns for document processing operations
including video transcript extraction and image OCR.
"""

from django.urls import path

try:
    from ..views.document_processing_views import (
        process_video,
        process_image,
        get_video_transcripts,
        get_ocr_results
    )
    PROCESSING_AVAILABLE = True
except ImportError as e:
    PROCESSING_AVAILABLE = False
    print(f"Warning: Document processing views not available: {e}")

try:
    from ..views.bulk_import_views import (
        scan_folder,
        bulk_import_files,
        bulk_import_status
    )
    BULK_IMPORT_AVAILABLE = True
except ImportError as e:
    BULK_IMPORT_AVAILABLE = False
    print(f"Warning: Bulk import views not available: {e}")

urlpatterns = []

if PROCESSING_AVAILABLE:
    urlpatterns.extend([
        # Video processing endpoints
        path('video/process/', process_video, name='process_video'),
        path('video/transcripts/', get_video_transcripts, name='get_video_transcripts'),
        
        # Image processing endpoints
        path('image/process/', process_image, name='process_image'),
        path('image/ocr-results/', get_ocr_results, name='get_ocr_results'),
    ])

if BULK_IMPORT_AVAILABLE:
    urlpatterns.extend([
        # Bulk import endpoints
        path('bulk/scan-folder/', scan_folder, name='scan_folder'),
        path('bulk/import-files/', bulk_import_files, name='bulk_import_files'),
        path('bulk/status/', bulk_import_status, name='bulk_import_status'),
    ])

