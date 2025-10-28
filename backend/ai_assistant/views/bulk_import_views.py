"""
Bulk Import and Folder Scanning Views

CRITICAL QUALITY RULES:
- NO performance compromises
- Accuracy over speed
- Process ALL files completely
- BGE-M3 only for embeddings
- Unlimited chunks
"""

import logging
import os
import hashlib
from pathlib import Path
from django.utils import timezone
from django.db import transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from ..models import UploadedFile
from ..automatic_file_processor import automatic_file_processor

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def scan_folder(request):
    """
    Scan a folder and discover supported files
    
    QUALITY FOCUS: Scan recursively, find all supported file types
    """
    try:
        folder_path = request.data.get('folder_path', '')
        
        if not folder_path:
            return Response(
                {'error': 'folder_path is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not os.path.exists(folder_path):
            return Response(
                {'error': f'Folder path does not exist: {folder_path}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Supported file types
        supported_extensions = [
            '.pdf', '.doc', '.docx', '.txt', '.rtf', '.html', '.mhtml', '.md',
            '.xls', '.xlsx', '.csv',
            '.ppt', '.pptx',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp',
            '.mp3', '.wav', '.flac', '.aac', '.ogg',
            '.mp4', '.avi', '.mov', '.wmv', '.webm',
            '.zip', '.rar', '.7z', '.tar', '.gz'
        ]
        
        discovered_files = []
        total_size = 0
        
        # Scan recursively
        for root, dirs, files in os.walk(folder_path):
            for filename in files:
                file_path = os.path.join(root, filename)
                file_ext = Path(filename).suffix.lower()
                
                if file_ext in supported_extensions:
                    file_size = os.path.getsize(file_path)
                    total_size += file_size
                    
                    discovered_files.append({
                        'filename': filename,
                        'file_path': file_path,
                        'file_size': file_size,
                        'file_extension': file_ext,
                        'relative_path': os.path.relpath(file_path, folder_path)
                    })
        
        return Response({
            'success': True,
            'folder_path': folder_path,
            'file_count': len(discovered_files),
            'total_size': total_size,
            'files': discovered_files
        })
        
    except Exception as e:
        logger.error(f"Error scanning folder: {e}", exc_info=True)
        return Response(
            {'error': f'Failed to scan folder: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_import_files(request):
    """
    Bulk import multiple files from a list
    
    QUALITY FOCUS: Process all files, ensure ALL get metadata + chunks + embeddings
    
    COMPREHENSIVE ERROR HANDLING:
    - Per-file error tracking
    - Detailed logging at every step
    - Recovery mechanisms
    - Progress reporting
    """
    import traceback
    
    try:
        files_to_import = request.data.get('files', [])
        
        if not files_to_import:
            return Response(
                {'error': 'files list is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        results = {
            'total': len(files_to_import),
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'details': [],
            'errors': []  # Track all errors
        }
        
        logger.info(f"Starting bulk import of {len(files_to_import)} files for user {request.user.username}")
        
        with transaction.atomic():
            for idx, file_info in enumerate(files_to_import, 1):
                file_path = file_info.get('file_path')
                filename = file_info.get('filename', 'unknown')
                
                try:
                    logger.debug(f"Processing file {idx}/{len(files_to_import)}: {filename}")
                    
                    if not file_path or not os.path.exists(file_path):
                        error_msg = f'File not found: {file_path}'
                        logger.warning(error_msg)
                        results['failed'] += 1
                        results['errors'].append({
                            'file': filename,
                            'error': error_msg,
                            'type': 'file_not_found'
                        })
                        results['details'].append({
                            'filename': filename,
                            'status': 'failed',
                            'error': error_msg
                        })
                        continue
                    
                    # Calculate file hash for deduplication
                    file_hash = _calculate_file_hash(file_path)
                    file_size = os.path.getsize(file_path)
                    
                    # ENHANCED: Check for duplicates using BOTH hash and filename
                    duplicates = UploadedFile.find_duplicates(
                        file_hash=file_hash,
                        filename=os.path.basename(file_path),
                        file_size=file_size
                    )
                    
                    if duplicates:
                        logger.info(f"Duplicate detected for {filename}: {duplicates[0].id}")
                        results['skipped'] += 1
                        results['details'].append({
                            'filename': filename,
                            'status': 'skipped',
                            'error': f'File already exists (hash: {file_hash[:8]}...)',
                            'existing_file_id': duplicates[0].id
                        })
                        continue
                    
                    # Create UploadedFile record
                    filename = os.path.basename(file_path)
                    
                    uploaded_file = UploadedFile.objects.create(
                        filename=filename,
                        file_hash=file_hash,
                        file_size=file_size,
                        uploaded_by=request.user,
                        processing_status='pending'
                    )
                    
                    logger.info(f"Created UploadedFile record for {filename} (ID: {uploaded_file.id})")
                    
                    # Trigger automatic processing (will be handled by signal)
                    # automatic_file_processor.process_file_fully(uploaded_file.id)
                    
                    results['successful'] += 1
                    results['details'].append({
                        'filename': filename,
                        'status': 'success',
                        'uploaded_file_id': uploaded_file.id
                    })
                    
                except Exception as e:
                    # Comprehensive error logging
                    error_trace = traceback.format_exc()
                    logger.error(f"Error importing file {filename}: {e}", exc_info=True)
                    
                    results['failed'] += 1
                    results['errors'].append({
                        'file': filename,
                        'error': str(e),
                        'traceback': error_trace,
                        'type': 'processing_error'
                    })
                    results['details'].append({
                        'filename': filename,
                        'status': 'failed',
                        'error': str(e)
                    })
                    continue
        
        logger.info(f"Bulk import completed: {results['successful']} successful, {results['failed']} failed, {results['skipped']} skipped")
        
        return Response({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Critical error in bulk import: {e}", exc_info=True)
        return Response(
            {'error': f'Bulk import failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def bulk_import_status(request):
    """
    Get status of bulk import operations
    
    Shows files being processed, pending, ready, or failed
    """
    try:
        status_filter = request.GET.get('status', None)
        
        query = UploadedFile.objects.all()
        
        if status_filter:
            query = query.filter(processing_status=status_filter)
        
        files = query.order_by('-uploaded_at')[:100]  # Limit to 100 most recent
        
        files_data = []
        for file in files:
            files_data.append({
                'id': file.id,
                'filename': file.filename,
                'file_size': file.file_size,
                'processing_status': file.processing_status,
                'chunk_count': file.chunk_count,
                'embedding_count': file.embedding_count,
                'metadata_extracted': file.metadata_extracted,
                'chunks_created': file.chunks_created,
                'embeddings_created': file.embeddings_created,
                'is_ready': file.is_ready_for_search(),
                'processing_error': file.processing_error,
                'uploaded_at': file.uploaded_at.isoformat() if file.uploaded_at else None
            })
        
        # Get statistics
        stats = {
            'total': UploadedFile.objects.count(),
            'pending': UploadedFile.objects.filter(processing_status='pending').count(),
            'metadata_extracting': UploadedFile.objects.filter(processing_status='metadata_extracting').count(),
            'chunking': UploadedFile.objects.filter(processing_status='chunking').count(),
            'embedding': UploadedFile.objects.filter(processing_status='embedding').count(),
            'ready': UploadedFile.objects.filter(processing_status='ready').count(),
            'failed': UploadedFile.objects.filter(processing_status='failed').count()
        }
        
        return Response({
            'success': True,
            'files': files_data,
            'statistics': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting bulk import status: {e}", exc_info=True)
        return Response(
            {'error': f'Failed to get status: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _calculate_file_hash(file_path: str) -> str:
    """Calculate SHA256 hash of file for deduplication"""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

