"""
Document Processing Views Module

This module contains all document processing related views including
video transcript extraction and image OCR processing.
"""

import logging
import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from ..models import DocumentFile, UploadedFile, DocumentChunk
try:
    from ..video_transcript_extractor import VideoTranscriptExtractor
    from ..image_ocr_processor import ImageOCRProcessor
    VIDEO_PROCESSING_AVAILABLE = True
except ImportError:
    VIDEO_PROCESSING_AVAILABLE = False
    VideoTranscriptExtractor = None
    ImageOCRProcessor = None

from .base_views import (
    BaseViewMixin, success_response, error_response, bad_request_response
)

logger = logging.getLogger(__name__)

# Initialize processors
if VIDEO_PROCESSING_AVAILABLE:
    video_processor = VideoTranscriptExtractor()
    image_processor = ImageOCRProcessor()
else:
    video_processor = None
    image_processor = None


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_video(request):
    """Extract transcript from video file"""
    if not VIDEO_PROCESSING_AVAILABLE:
        return error_response('Video processing is not available. Install librosa and whisper.')
    
    try:
        BaseViewMixin.log_request(request, 'process_video')
        
        if 'file' not in request.FILES:
            return bad_request_response('Video file is required')
        
        video_file = request.FILES['file']
        title = request.data.get('title', video_file.name)
        description = request.data.get('description', '')
        
        # Save video file temporarily
        fs = FileSystemStorage()
        filename = fs.save(f'videos/{video_file.name}', video_file)
        file_path = os.path.join(settings.MEDIA_ROOT, filename)
        
        try:
            # Extract transcript
            logger.info(f"Processing video: {file_path}")
            if not video_processor:
                return error_response('Video processor not initialized')
            transcript_result = video_processor.extract_transcript(file_path)
            
            if not transcript_result or not transcript_result.segments:
                return error_response('Failed to extract transcript from video')
            
            # Save transcript as DocumentFile
            doc_file = DocumentFile.objects.create(
                title=title,
                filename=os.path.basename(filename),
                document_type='video',
                description=description,
                source_url=request.data.get('source_url', ''),
                metadata={
                    'duration': transcript_result.metadata.duration,
                    'language': transcript_result.language,
                    'word_count': transcript_result.word_count,
                    'confidence': transcript_result.confidence,
                    'segments_count': len(transcript_result.segments)
                },
                uploaded_by=request.user,
                file_size=video_file.size
            )
            
            # Create chunks from segments
            for idx, segment in enumerate(transcript_result.segments):
                UploadedFile.objects.create(
                    filename=f"{title}_segment_{idx}",
                    file_hash=f"video_{doc_file.id}_{idx}",
                    intro=segment.text[:100],
                    uploaded_by=request.user
                )
            
            result = {
                'document_id': doc_file.id,
                'title': doc_file.title,
                'transcript': transcript_result.full_text,
                'segments_count': len(transcript_result.segments),
                'word_count': transcript_result.word_count,
                'language': transcript_result.language,
                'confidence': transcript_result.confidence
            }
            
            BaseViewMixin.log_response(result, 'process_video')
            return success_response("Video processed successfully", result)
            
        finally:
            # Clean up temporary file
            if os.path.exists(file_path):
                os.remove(file_path)
                
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'process_video')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_image(request):
    """Extract text from image using OCR"""
    if not VIDEO_PROCESSING_AVAILABLE:
        return error_response('Image processing is not available. Install required dependencies.')
    
    try:
        BaseViewMixin.log_request(request, 'process_image')
        
        if 'file' not in request.FILES:
            return bad_request_response('Image file is required')
        
        image_file = request.FILES['file']
        title = request.data.get('title', image_file.name)
        description = request.data.get('description', '')
        
        # Save image file
        fs = FileSystemStorage()
        filename = fs.save(f'images/{image_file.name}', image_file)
        file_path = os.path.join(settings.MEDIA_ROOT, filename)
        
        if not image_processor:
            return error_response('Image processor not initialized')
        
        try:
            # Process image with OCR
            logger.info(f"Processing image: {file_path}")
            ocr_result = image_processor.process_image(file_path)
            
            if not ocr_result or not ocr_result.text:
                return error_response('Failed to extract text from image')
            
            # Save OCR result as DocumentFile
            doc_file = DocumentFile.objects.create(
                title=title,
                filename=os.path.basename(filename),
                document_type='image',
                description=description,
                source_url=request.data.get('source_url', ''),
                metadata={
                    'dimensions': ocr_result.metadata.dimensions,
                    'confidence': ocr_result.confidence,
                    'word_count': len(ocr_result.words),
                    'language': ocr_result.language,
                    'processing_time': ocr_result.processing_time
                },
                uploaded_by=request.user,
                file_size=image_file.size
            )
            
            result = {
                'document_id': doc_file.id,
                'title': doc_file.title,
                'extracted_text': ocr_result.text,
                'confidence': ocr_result.confidence,
                'word_count': len(ocr_result.words),
                'language': ocr_result.language,
                'bounding_boxes': ocr_result.bounding_boxes
            }
            
            BaseViewMixin.log_response(result, 'process_image')
            return success_response("Image processed successfully", result)
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return error_response(f'Failed to process image: {str(e)}')
                
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'process_image')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_video_transcripts(request):
    """Get all video transcripts"""
    try:
        BaseViewMixin.log_request(request, 'get_video_transcripts')
        
        video_docs = DocumentFile.objects.filter(document_type='video')
        transcripts = []
        
        for doc in video_docs:
            transcripts.append({
                'id': doc.id,
                'title': doc.title,
                'uploaded_at': doc.uploaded_at,
                'duration': doc.metadata.get('duration', 0),
                'word_count': doc.metadata.get('word_count', 0),
                'language': doc.metadata.get('language', 'unknown')
            })
        
        BaseViewMixin.log_response({'transcripts': transcripts}, 'get_video_transcripts')
        return success_response("Video transcripts retrieved successfully", {'transcripts': transcripts})
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'get_video_transcripts')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ocr_results(request):
    """Get all OCR results"""
    try:
        BaseViewMixin.log_request(request, 'get_ocr_results')
        
        image_docs = DocumentFile.objects.filter(document_type='image')
        ocr_results = []
        
        for doc in image_docs:
            ocr_results.append({
                'id': doc.id,
                'title': doc.title,
                'uploaded_at': doc.uploaded_at,
                'confidence': doc.metadata.get('confidence', 0),
                'word_count': doc.metadata.get('word_count', 0),
                'language': doc.metadata.get('language', 'unknown')
            })
        
        BaseViewMixin.log_response({'ocr_results': ocr_results}, 'get_ocr_results')
        return success_response("OCR results retrieved successfully", {'ocr_results': ocr_results})
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'get_ocr_results')

