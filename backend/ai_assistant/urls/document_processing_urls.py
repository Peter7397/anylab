"""
Document Processing URL Configuration

This module contains URL patterns for document processing operations
including video transcript extraction and image OCR.
"""

from django.urls import path
from ..views.document_processing_views import (
    process_video,
    process_image,
    get_video_transcripts,
    get_ocr_results
)

urlpatterns = [
    # Video processing endpoints
    path('video/process/', process_video, name='process_video'),
    path('video/transcripts/', get_video_transcripts, name='get_video_transcripts'),
    
    # Image processing endpoints
    path('image/process/', process_image, name='process_image'),
    path('image/ocr-results/', get_ocr_results, name='get_ocr_results'),
]

