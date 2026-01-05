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
from ..models import UploadedFile, DocumentFile
from ..automatic_file_processor import automatic_file_processor

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_folders(request):
    """
    List folders/directories at a given path
    
    Returns list of folders and files for browsing
    """
    try:
        from ..views.base_views import success_response, error_response
        
        path = request.query_params.get('path', '/')
        
        # Security: Validate path to prevent directory traversal
        if '..' in path or path.startswith('~'):
            return error_response('Invalid path', status.HTTP_400_BAD_REQUEST)
        
        # Normalize path
        if not os.path.isabs(path):
            # If relative path, make it absolute from a safe base
            base_path = os.path.expanduser('~') if os.path.exists(os.path.expanduser('~')) else '/'
            path = os.path.join(base_path, path)
        
        path = os.path.normpath(path)
        
        if not os.path.exists(path):
            return error_response(f'Path does not exist: {path}', status.HTTP_404_NOT_FOUND)
        
        if not os.path.isdir(path):
            return error_response(f'Path is not a directory: {path}', status.HTTP_400_BAD_REQUEST)
        
        # List directories and files
        items = []
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                try:
                    is_dir = os.path.isdir(item_path)
                    stat_info = os.stat(item_path)
                    items.append({
                        'name': item,
                        'path': item_path,
                        'is_directory': is_dir,
                        'size': stat_info.st_size if not is_dir else None,
                        'modified': stat_info.st_mtime,
                    })
                except (OSError, PermissionError):
                    # Skip items we can't access
                    continue
            
            # Sort: directories first, then by name
            items.sort(key=lambda x: (not x['is_directory'], x['name'].lower()))
            
        except PermissionError:
            return error_response(f'Permission denied: {path}', status.HTTP_403_FORBIDDEN)
        
        return success_response('Folders listed', {
            'current_path': path,
            'parent_path': os.path.dirname(path) if path != '/' else None,
            'items': items
        })
        
    except Exception as e:
        logger.error(f"Error listing folders: {e}", exc_info=True)
        return Response(
            {'error': f'Failed to list folders: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def scan_folder(request):
    """
    Scan a folder and discover supported files
    
    NEW: Creates UploadJob with job_type='folder' instead of immediate processing
    QUALITY FOCUS: Scan recursively, find all supported file types
    """
    try:
        folder_path = request.data.get('folder_path', '')
        priority = 5  # Default priority, no longer user-configurable
        auto_upload = request.data.get('auto_upload', True)  # Create job automatically
        
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
                        'name': filename,
                        'file_path': file_path,
                        'path': file_path,  # Alias for compatibility
                        'size': file_size,
                        'file_size': file_size,  # Alias
                        'file_extension': file_ext,
                        'relative_path': os.path.relpath(file_path, folder_path)
                    })
        
        # If auto_upload is True, create UploadJob and queue processing
        job_id = None
        if auto_upload and discovered_files:
            from ..service_classes.upload_queue_manager import upload_queue_manager
            from ..tasks import process_upload_job
            
            # Create job
            job = upload_queue_manager.add_job(
                job_type='folder',
                source_path=folder_path,
                source_files=discovered_files,
                priority=priority,
                metadata={
                    'folder_path': folder_path,
                    'total_size': total_size,
                    'scan_type': 'recursive'
                },
                user=request.user
            )
            
            job_id = str(job.job_id)
            
            # Queue processing
            process_upload_job.delay(job_id)
            
            logger.info(f"Created folder upload job {job_id} with {len(discovered_files)} files")
        
        return Response({
            'success': True,
            'folder_path': folder_path,
            'file_count': len(discovered_files),
            'total_size': total_size,
            'files': discovered_files,
            'job_id': job_id,  # Return job_id if auto_upload is True
            'auto_upload': auto_upload
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
                    
                    # Create DocumentFile record (CRITICAL: Links to UploadedFile for processing tracking)
                    document_file = None
                    try:
                        filename_base = os.path.splitext(filename)[0]
                        document_type = _determine_document_type(filename)
                        metadata = _extract_metadata_from_filename(filename, file_path)
                        
                        document_file = DocumentFile.objects.create(
                            title=filename_base,
                            filename=filename,
                            document_type=document_type,
                            description=f"Bulk imported file: {filename}",
                            uploaded_by=request.user,
                            page_count=0,  # Will be updated during processing
                            file_size=file_size,
                            uploaded_file=uploaded_file,  # CRITICAL: Link to UploadedFile
                            metadata=metadata
                        )
                        
                        logger.info(f"Created DocumentFile record for {filename} (ID: {document_file.id})")
                        
                    except Exception as doc_ex:
                        logger.error(f"Error creating DocumentFile for {filename}: {doc_ex}", exc_info=True)
                        # Log error but continue - UploadedFile is still valid
                        # Signal will still trigger processing
                        results['errors'].append({
                            'file': filename,
                            'error': f'DocumentFile creation failed: {str(doc_ex)}',
                            'type': 'documentfile_creation_error'
                        })
                    
                    # Trigger automatic processing (will be handled by signal)
                    # automatic_file_processor.process_file_fully(uploaded_file.id)
                    
                    results['successful'] += 1
                    
                    # Build detailed response
                    file_detail = {
                        'filename': filename,
                        'status': 'success',
                        'uploaded_file_id': uploaded_file.id
                    }
                    
                    # Add DocumentFile info if created successfully
                    if document_file:
                        file_detail['document_id'] = document_file.id
                        file_detail['document_type'] = document_type
                        
                        # Generate proper file URL using the same logic as serializer
                        # For SSB_KPR documents, use HTML view endpoint
                        if document_type == 'SSB_KPR':
                            file_detail['file_url'] = request.build_absolute_uri(f'/api/ai/documents/{document_file.id}/html/')
                        else:
                            # Generate media URL from UploadedFile.filename
                            # uploaded_file.filename is stored as 'uploads/filename.ext'
                            file_detail['file_url'] = request.build_absolute_uri(f'/media/{uploaded_file.filename}')
                    
                    results['details'].append(file_detail)
                    
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
            # Get related DocumentFile if exists
            document_file = None
            try:
                document_file = DocumentFile.objects.filter(uploaded_file=file).first()
            except Exception as e:
                logger.warning(f"Error getting DocumentFile for UploadedFile {file.id}: {e}")
            
            file_data = {
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
            }
            
            # Add DocumentFile info if exists
            if document_file:
                file_data['document_id'] = document_file.id
                file_data['document_title'] = document_file.title
                file_data['document_type'] = document_file.document_type
                
                # Generate proper file URL using the same logic as serializer
                # For SSB_KPR documents, use HTML view endpoint
                if document_file.document_type == 'SSB_KPR':
                    file_data['file_url'] = request.build_absolute_uri(f'/api/ai/documents/{document_file.id}/html/')
                else:
                    # Generate media URL from UploadedFile.filename
                    # uploaded_file.filename is stored as 'uploads/filename.ext'
                    file_data['file_url'] = request.build_absolute_uri(f'/media/{file.filename}')
            
            files_data.append(file_data)
        
        # Get statistics for UploadedFile
        stats = {
            'total': UploadedFile.objects.count(),
            'pending': UploadedFile.objects.filter(processing_status='pending').count(),
            'metadata_extracting': UploadedFile.objects.filter(processing_status='metadata_extracting').count(),
            'chunking': UploadedFile.objects.filter(processing_status='chunking').count(),
            'embedding': UploadedFile.objects.filter(processing_status='embedding').count(),
            'ready': UploadedFile.objects.filter(processing_status='ready').count(),
            'failed': UploadedFile.objects.filter(processing_status='failed').count(),
            
            # DocumentFile statistics
            'document_files_total': DocumentFile.objects.count(),
            'document_files_with_uploaded_files': DocumentFile.objects.filter(
                uploaded_file__isnull=False
            ).count(),
            'document_files_ready': DocumentFile.objects.filter(
                uploaded_file__isnull=False,
                uploaded_file__processing_status='ready'
            ).count(),
            'document_files_processing': DocumentFile.objects.filter(
                uploaded_file__isnull=False,
                uploaded_file__processing_status__in=['pending', 'metadata_extracting', 'chunking', 'embedding']
            ).count()
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


def _determine_document_type(filename: str) -> str:
    """Determine document_type from file extension"""
    file_ext = Path(filename).suffix.lower()
    
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
    
    return doc_type_map.get(file_ext, 'pdf')


def _extract_metadata_from_filename(filename: str, file_path: str) -> dict:
    """Extract basic metadata from filename and path"""
    metadata = {
        'bulk_import': True,
        'import_source': 'bulk_import',
        'original_filename': filename
    }
    
    try:
        # Try to import and use detection utilities if available
        from ..utils.version_detector import detect_version
        from ..utils.product_detector import detect_product, detect_content_type
        
        # Detect document classification
        product_category = detect_product(filename)
        content_type = detect_content_type(filename)
        version = detect_version(filename)
        
        if product_category:
            metadata['product_category'] = product_category
        if content_type:
            metadata['content_type'] = content_type
        if version:
            metadata['version'] = version
    except ImportError:
        # Utilities not available, skip advanced metadata extraction
        logger.debug("Metadata detection utilities not available, using basic metadata")
    except Exception as e:
        logger.warning(f"Error extracting metadata from filename: {e}")
    
    return metadata

