"""
Upload Queue Views

Unified upload queue API endpoints for managing upload jobs.
"""

import logging
import uuid
import os
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.core.files.storage import default_storage
from django.conf import settings
from django.core.files.uploadedfile import TemporaryUploadedFile

from ..service_classes.upload_queue_manager import upload_queue_manager
from ..service_classes.webpage_crawler import WebpageCrawler, WebpageCrawlerConfig
from ..models import UploadJob
from .base_views import BaseViewMixin, success_response, error_response, bad_request_response

logger = logging.getLogger(__name__)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def create_upload_job(request):
    """
    Create a new upload job (POST) or get queue status (GET)
    
    POST Request body (NEW: JSON metadata format):
    {
        "job_type": "file" | "folder" | "webpage",
        "source": "path_or_url",
        "files": [
            {
                "name": "file.pdf",
                "size": 1024000,
                "hash": "sha256_hex_string_64_chars",
                "type": "application/pdf"
            }, ...
        ],
        "priority": 5,  // Optional, 1-10 (default: 5)
        "metadata": {}  // Optional
    }
    
    LEGACY: Also supports FormData with file uploads (for backward compatibility)
    
    GET Query params:
    - status: Filter by status (optional)
    - user_only: If true, only show current user's jobs (default: false)
    """
    try:
        # Handle GET request (queue status)
        if request.method == 'GET':
            status_filter = request.query_params.get('status')
            user_only = request.query_params.get('user_only', 'false').lower() == 'true'
            
            user = request.user if user_only else None
            
            queue_data = upload_queue_manager.get_queue_status(user=user, status_filter=status_filter)
            
            return success_response("Queue status retrieved", queue_data)
        
        # Handle POST request (create job)
        BaseViewMixin.log_request(request, 'create_upload_job')
        
        job_type = request.data.get('job_type')
        source = request.data.get('source')
        files = request.data.get('files', [])
        priority = 5  # Default priority, no longer user-configurable
        metadata = request.data.get('metadata', {})
        
        # Validation
        if not job_type or job_type not in ['file', 'folder', 'webpage']:
            return bad_request_response('job_type must be "file", "folder", or "webpage"')
        
        if not source:
            return bad_request_response('source is required')
        
        # Handle different job types
        if job_type == 'file':
            # NEW: Support JSON metadata (with hash) OR FormData (legacy support)
            # Check if files are provided as JSON metadata (new way) or FormData (legacy)
            if files and isinstance(files, list) and len(files) > 0:
                # NEW: JSON metadata format - files come with hash, name, size, type
                # Validate and check for duplicates before creating job
                processed_files = []
                duplicate_count = 0
                
                for file_info in files:
                    # Validate required fields
                    if not isinstance(file_info, dict):
                        return bad_request_response('Each file must be an object with name, size, hash, and type')
                    
                    file_name = file_info.get('name')
                    file_size = file_info.get('size')
                    file_hash = file_info.get('hash')
                    file_type = file_info.get('type', 'application/octet-stream')
                    
                    if not file_name or not file_size or not file_hash:
                        return bad_request_response(f'File missing required fields: name, size, and hash are required')
                    
                    # Validate hash format (SHA-256 hex string, 64 characters)
                    if not isinstance(file_hash, str) or len(file_hash) != 64 or not all(c in '0123456789abcdef' for c in file_hash.lower()):
                        return bad_request_response(f'Invalid hash format for file "{file_name}". Hash must be a 64-character SHA-256 hex string.')
                    
                    # Check for duplicates using hash
                    from ..models import UploadedFile
                    duplicates = UploadedFile.find_duplicates(
                        file_hash=file_hash.lower(),  # Normalize to lowercase
                        filename=file_name,
                        file_size=file_size
                    )
                    
                    if duplicates:
                        # Duplicate found - mark as skipped immediately
                        existing_file = duplicates[0]
                        logger.info(f'Duplicate file detected: {file_name} (hash: {file_hash[:8]}...), existing ID: {existing_file.id}')
                        
                        processed_files.append({
                            'name': file_name,
                            'size': file_size,
                            'type': file_type,
                            'hash': file_hash.lower(),
                            'is_temp': False,  # No temp file needed for duplicates
                            'upload_status': 'skipped',
                            'processing_status': 'skipped',
                            'uploaded_file_id': existing_file.id,
                            'upload_error': f'Duplicate file - already exists (ID: {existing_file.id})',
                            'processing_error': None,
                            'uploaded_at': existing_file.uploaded_at.isoformat() if existing_file.uploaded_at else None,
                            'processed_at': existing_file.processing_completed_at.isoformat() if existing_file.processing_completed_at else None,
                            'retry_count': 0,
                            'is_duplicate': True,
                        })
                        duplicate_count += 1
                    else:
                        # Not a duplicate - add to job normally
                        processed_files.append({
                            'name': file_name,
                            'size': file_size,
                            'type': file_type,
                            'hash': file_hash.lower(),
                            'is_temp': True,  # Will need temp file upload later
                            'upload_status': 'pending',
                            'processing_status': 'pending',
                            'uploaded_file_id': None,
                            'upload_error': None,
                            'processing_error': None,
                            'uploaded_at': None,
                            'processed_at': None,
                            'retry_count': 0,
                            'is_duplicate': False,
                        })
                
                files = processed_files
                logger.info(f'Processed {len(files)} files: {len(files) - duplicate_count} new, {duplicate_count} duplicates')
                
            elif 'files' in request.FILES or 'file' in request.FILES:
                # LEGACY: FormData format - handle as before for backward compatibility
                # OPTIMIZED: Zero-blocking file handling - create job immediately, Celery handles ALL file I/O
                # Support both single file and multiple files
                if 'files' in request.FILES:
                    # Multiple files - prepare metadata immediately, NO file I/O
                    uploaded_files = request.FILES.getlist('files')
                    files = []
                    
                    for f in uploaded_files:
                        # For TemporaryUploadedFile, Django already saved it to temp - use that path
                        if isinstance(f, TemporaryUploadedFile):
                            temp_path = f.temporary_file_path()
                            files.append({
                                'name': f.name,
                                'size': f.size,
                                'type': f.content_type,
                                'path': temp_path,
                                'is_temp': True,
                                # Per-file status tracking
                                'upload_status': 'pending',
                                'processing_status': 'pending',
                                'uploaded_file_id': None,
                                'upload_error': None,
                                'processing_error': None,
                                'uploaded_at': None,
                                'processed_at': None,
                                'retry_count': 0
                            })
                        else:
                            # For InMemoryUploadedFile - save to temp file FAST (optimized for speed)
                            # Read entire file at once (faster for small-medium files) and write in one go
                            # Per-file status tracking
                            file_info = {
                                'name': f.name,
                                'size': f.size,
                                'type': f.content_type,
                                'path': None,  # Will be set below
                                'is_temp': True,
                                'upload_status': 'pending',
                                'processing_status': 'pending',
                                'uploaded_file_id': None,
                                'upload_error': None,
                                'processing_error': None,
                                'uploaded_at': None,
                                'processed_at': None,
                                'retry_count': 0
                            }
                            try:
                                # Create temp file in Django's temp directory
                                temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
                                os.makedirs(temp_dir, exist_ok=True)
                                
                                # Save file content to temp file - optimized for speed
                                temp_file_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{f.name}")
                                
                                # For InMemoryUploadedFile, read all at once (faster than chunks for small files)
                                f.seek(0)  # Reset to beginning
                                file_content = f.read()
                                
                                # Write in one operation (faster than chunked writes)
                                with open(temp_file_path, 'wb') as temp_file:
                                    temp_file.write(file_content)
                                
                                file_info['path'] = temp_file_path
                                files.append(file_info)
                            except Exception as e:
                                logger.error(f"Failed to save temp file {f.name}: {e}", exc_info=True)
                                # Create job anyway - Celery will handle the error
                                file_info['path'] = None
                                file_info['upload_error'] = str(e)
                                file_info['upload_status'] = 'failed'
                                files.append(file_info)
                
            elif 'file' in request.FILES:
                # Single file - handle immediately with zero blocking
                uploaded_file = request.FILES['file']
                
                # For TemporaryUploadedFile, Django already saved it - use that path
                if isinstance(uploaded_file, TemporaryUploadedFile):
                    temp_path = uploaded_file.temporary_file_path()
                    files = [{
                        'name': uploaded_file.name,
                        'size': uploaded_file.size,
                        'type': uploaded_file.content_type,
                        'path': temp_path,
                        'is_temp': True,
                        # Per-file status tracking
                        'upload_status': 'pending',
                        'processing_status': 'pending',
                        'uploaded_file_id': None,
                        'upload_error': None,
                        'processing_error': None,
                        'uploaded_at': None,
                        'processed_at': None,
                        'retry_count': 0
                    }]
                else:
                    # For InMemoryUploadedFile - save to temp file FAST (optimized for speed)
                    # Per-file status tracking
                    file_info = {
                        'name': uploaded_file.name,
                        'size': uploaded_file.size,
                        'type': uploaded_file.content_type,
                        'path': None,  # Will be set below
                        'is_temp': True,
                        'upload_status': 'pending',
                        'processing_status': 'pending',
                        'uploaded_file_id': None,
                        'upload_error': None,
                        'processing_error': None,
                        'uploaded_at': None,
                        'processed_at': None,
                        'retry_count': 0
                    }
                    try:
                        # Create temp file in Django's temp directory
                        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
                        os.makedirs(temp_dir, exist_ok=True)
                        
                        # Save file content to temp file - optimized for speed
                        temp_file_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{uploaded_file.name}")
                        
                        # For InMemoryUploadedFile, read all at once (faster than chunks for small files)
                        uploaded_file.seek(0)  # Reset to beginning
                        file_content = uploaded_file.read()
                        
                        # Write in one operation (faster than chunked writes)
                        with open(temp_file_path, 'wb') as temp_file:
                            temp_file.write(file_content)
                        
                        file_info['path'] = temp_file_path
                        files = [file_info]
                    except Exception as e:
                        logger.error(f"Failed to save temp file {uploaded_file.name}: {e}", exc_info=True)
                        # Create job anyway - Celery will handle the error
                        file_info['path'] = None
                        file_info['upload_error'] = str(e)
                        file_info['upload_status'] = 'failed'
                        files = [file_info]
            else:
                # No files provided
                return bad_request_response('files required for file upload type')
            
        elif job_type == 'webpage':
            # Validate URL
            validation = upload_queue_manager.validate_url(source)
            if not validation['valid']:
                return bad_request_response(f"Invalid URL: {validation.get('error', 'Unknown error')}")
            if not validation['accessible']:
                return bad_request_response(f"URL not accessible: {validation.get('error', 'Unknown error')}")
            
            # Discover files from webpage
            try:
                discovered_files = upload_queue_manager.discover_webpage_files(source)
                if not discovered_files:
                    return bad_request_response('No downloadable files found on webpage')
                
                files = discovered_files
                logger.info(f"Discovered {len(files)} files from webpage {source}")
            except Exception as e:
                logger.error(f"Error discovering files from webpage: {e}", exc_info=True)
                return error_response(f"Failed to discover files from webpage: {str(e)}", status=status.HTTP_400_BAD_REQUEST)
        
        # Check if job needs splitting (50+ files)
        JOB_SPLIT_THRESHOLD = 50
        SUB_JOB_SIZE = 25
        
        if len(files) >= JOB_SPLIT_THRESHOLD:
            # Split into sub-jobs for better resource management
            logger.info(f"Splitting large job with {len(files)} files into sub-jobs")
            sub_jobs = []
            
            for i in range(0, len(files), SUB_JOB_SIZE):
                sub_files = files[i:i + SUB_JOB_SIZE]
                sub_job = upload_queue_manager.add_job(
                    job_type=job_type,
                    source_path=source,
                    source_files=sub_files,
                    priority=priority,
                    metadata={**(metadata or {}), 'parent_job': True, 'sub_job_index': i // SUB_JOB_SIZE + 1, 'total_sub_jobs': (len(files) + SUB_JOB_SIZE - 1) // SUB_JOB_SIZE},
                    user=request.user
                )
                sub_jobs.append(sub_job)
                
                # Queue processing for each sub-job
                from ..tasks import process_upload_job
                process_upload_job.delay(str(sub_job.job_id))
            
            logger.info(f"Created {len(sub_jobs)} sub-jobs for user {request.user.username}")
            
            return success_response(
                "Upload job created successfully (split into sub-jobs)",
                {
                    'job_ids': [str(j.job_id) for j in sub_jobs],
                    'job_type': job_type,
                    'status': 'queued',
                    'total_items': len(files),
                    'sub_jobs_count': len(sub_jobs),
                    'priority': priority
                }
            )
        else:
            # Create single job (normal case)
            # OPTIMIZED: Return immediately after Redis job creation (<5ms)
            # Background worker will persist to PostgreSQL and process files
            job = upload_queue_manager.add_job(
                job_type=job_type,
                source_path=source,
                source_files=files,
                priority=priority,
                metadata=metadata,
                user=request.user,
                use_redis=True  # Use Redis for fast job creation
            )
            
            # Count duplicates and new files for response
            duplicate_count = sum(1 for f in files if f.get('is_duplicate', False))
            new_files_count = len(files) - duplicate_count
            
            # If all files are duplicates, mark job as completed immediately and remove from Redis
            if duplicate_count > 0 and new_files_count == 0:
                # All files are duplicates - mark job as completed
                job.status = 'completed'
                job.completed_at = timezone.now()
                job.save(update_fields=['status', 'completed_at'])
                
                # Remove from Redis (all duplicates = not active)
                try:
                    from ..service_classes.redis_job_queue_manager import redis_job_queue_manager
                    if redis_job_queue_manager and redis_job_queue_manager.is_available():
                        redis_job_queue_manager.remove_job_from_redis(str(job.job_id))
                        logger.info(f'Job {job.job_id} marked as completed (all duplicates) and removed from Redis')
                except Exception as e:
                    logger.warning(f'Error removing duplicate-only job from Redis: {e}')
            else:
                # Queue processing asynchronously (non-blocking) only if there are new files
                # This will be picked up by Celery worker even if job not yet in PostgreSQL
                from ..tasks import process_upload_job
                process_upload_job.delay(str(job.job_id))
            
            logger.info(
                f"Job {job.job_id} queued immediately in Redis - "
                f"type: {job.job_type}, items: {job.total_items}, "
                f"new: {new_files_count}, duplicates: {duplicate_count}, "
                f"priority: {job.priority}. User can continue working."
            )
            
            # Return immediately with job info - user can continue adding more jobs
            return success_response(
                "Upload job queued successfully",
                {
                    'job_id': str(job.job_id),
                    'job_type': job.job_type,
                    'status': job.status,
                    'total_items': job.total_items,
                    'new_files': new_files_count,
                    'duplicates': duplicate_count,
                    'priority': job.priority,
                    'message': f'Job queued successfully. {new_files_count} new file(s), {duplicate_count} duplicate(s) skipped. You can continue adding more jobs while this one processes in the background.'
                }
            )
        
    except Exception as e:
        logger.error(f"Error creating upload job: {e}", exc_info=True)
        return BaseViewMixin.handle_error(e, 'create_upload_job')


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_job(request, job_id):
    """
    Permanently delete a job and ALL associated data
    
    This will delete:
    - Upload job record
    - All uploaded files (UploadedFile records)
    - All chunks and embeddings
    - All document files
    - Physical files
    - Remove from Redis
    
    This allows the user to upload the same file again.
    """
    try:
        # Validate job_id
        try:
            uuid.UUID(str(job_id))
        except (ValueError, AttributeError):
            return bad_request_response(f'Invalid job ID format: {job_id}')
        
        job = upload_queue_manager.get_job(job_id)
        
        if not job:
            return error_response(f"Job {job_id} not found", status_code=status.HTTP_404_NOT_FOUND)
        
        # Check permission
        if not request.user.is_staff and job.created_by != request.user:
            return error_response("Permission denied", status_code=status.HTTP_403_FORBIDDEN)
        
        deleted_files_count = 0
        deleted_chunks_count = 0
        deleted_doc_files_count = 0
        
        # Delete all associated uploaded files and their data
        from ai_assistant.models import UploadedFile, DocumentChunk, DocumentFile
        from django.core.files.storage import default_storage
        
        source_files = job.source_files or []
        uploaded_file_ids = [f.get('uploaded_file_id') for f in source_files if f.get('uploaded_file_id')]
        
        if uploaded_file_ids:
            uploaded_files = UploadedFile.objects.filter(id__in=uploaded_file_ids)
            
            for uploaded_file in uploaded_files:
                try:
                    # Delete chunks
                    chunks = DocumentChunk.objects.filter(uploaded_file=uploaded_file)
                    chunks_count = chunks.count()
                    chunks.delete()
                    deleted_chunks_count += chunks_count
                    
                    # Delete document files
                    doc_files = DocumentFile.objects.filter(uploaded_file=uploaded_file)
                    doc_files_count = doc_files.count()
                    doc_files.delete()
                    deleted_doc_files_count += doc_files_count
                    
                    # Delete physical file
                    filename = uploaded_file.filename
                    if default_storage.exists(filename):
                        try:
                            default_storage.delete(filename)
                            logger.info(f"Deleted physical file: {filename}")
                        except Exception as e:
                            logger.warning(f"Could not delete physical file {filename}: {e}")
                    
                    # Delete UploadedFile record
                    uploaded_file.delete()
                    deleted_files_count += 1
                    logger.info(f"Deleted UploadedFile {uploaded_file.id} and all related data")
                    
                except Exception as e:
                    logger.error(f"Error deleting uploaded file {uploaded_file.id}: {e}", exc_info=True)
        
        # Remove from Redis (if it's still there)
        try:
            from ..service_classes.redis_job_queue_manager import redis_job_queue_manager
            if redis_job_queue_manager and redis_job_queue_manager.is_available():
                redis_job_queue_manager.remove_job_from_redis(job_id)
        except Exception as e:
            logger.warning(f"Error removing job {job_id} from Redis: {e}")
        
        # Delete the job record
        job.delete()
        
        logger.info(
            f"Deleted job {job_id}: {deleted_files_count} files, "
            f"{deleted_chunks_count} chunks, {deleted_doc_files_count} document files"
        )
        
        return success_response(
            "Job and all associated data deleted successfully",
            {
                'job_id': job_id,
                'deleted_files': deleted_files_count,
                'deleted_chunks': deleted_chunks_count,
                'deleted_document_files': deleted_doc_files_count
            }
        )
        
    except Exception as e:
        logger.error(f"Error deleting job: {e}", exc_info=True)
        return BaseViewMixin.handle_error(e, 'delete_job')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_file_content(request, job_id):
    """
    Upload file content for a job created with metadata only
    
    POST Request:
    - FormData with 'file' field containing the actual file content
    - Query param 'filename' to identify which file in the job
    
    This endpoint is called after job creation when files are sent as metadata only.
    Files are saved to temp folder and associated with the job.
    """
    try:
        # Validate job_id
        try:
            uuid.UUID(str(job_id))
        except (ValueError, AttributeError):
            return bad_request_response(f'Invalid job ID format: {job_id}')
        
        # Get job
        job = upload_queue_manager.get_job(job_id)
        if not job:
            return error_response(f"Job {job_id} not found", status_code=status.HTTP_404_NOT_FOUND)
        
        # Check permission
        if not request.user.is_staff and job.created_by != request.user:
            return error_response("Permission denied", status_code=status.HTTP_403_FORBIDDEN)
        
        # Get file from request
        if 'file' not in request.FILES:
            return bad_request_response('File content is required')
        
        uploaded_file = request.FILES['file']
        filename = request.GET.get('filename') or request.POST.get('filename') or uploaded_file.name
        
        # Find the file in job's source_files
        source_files = job.source_files or []
        file_info = None
        file_index = None
        
        for idx, f in enumerate(source_files):
            if f.get('name') == filename or f.get('filename') == filename:
                file_info = f
                file_index = idx
                break
        
        if not file_info:
            return bad_request_response(f'File "{filename}" not found in job {job_id}')
        
        # Check if file is already a duplicate (shouldn't upload content for duplicates)
        if file_info.get('is_duplicate') or file_info.get('upload_status') == 'skipped':
            logger.info(f'File {filename} is a duplicate, skipping file content upload')
            return success_response(
                "File is duplicate, no upload needed",
                {'filename': filename, 'is_duplicate': True}
            )
        
        # Save file to temp folder
        try:
            temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Generate temp file path
            temp_file_path = os.path.join(temp_dir, f"{job_id}_{file_index}_{filename}")
            
            # Save file content
            if isinstance(uploaded_file, TemporaryUploadedFile):
                # Already a temp file, just copy
                import shutil
                shutil.copy(uploaded_file.temporary_file_path(), temp_file_path)
            else:
                # InMemoryUploadedFile - read and write
                uploaded_file.seek(0)
                file_content = uploaded_file.read()
                with open(temp_file_path, 'wb') as temp_file:
                    temp_file.write(file_content)
            
            # Update file info in job
            file_info['path'] = temp_file_path
            file_info['is_temp'] = True
            file_info['upload_status'] = 'pending'  # Ready for processing
            
            # Update job in database
            job.source_files = source_files
            job.save(update_fields=['source_files'])
            
            logger.info(f'File content uploaded for {filename} in job {job_id}, saved to {temp_file_path}')
            
            return success_response(
                "File content uploaded successfully",
                {
                    'filename': filename,
                    'temp_path': temp_file_path,
                    'file_index': file_index
                }
            )
            
        except Exception as e:
            logger.error(f"Error saving file content for {filename}: {e}", exc_info=True)
            return error_response(f"Failed to save file content: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error uploading file content: {e}", exc_info=True)
        return BaseViewMixin.handle_error(e, 'upload_file_content')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_job_detail(request, job_id):
    """
    Get detailed information about a specific job
    """
    try:
        # Validate job_id is a valid UUID format before processing
        try:
            uuid.UUID(str(job_id))
        except (ValueError, AttributeError):
            return bad_request_response(f'Invalid job ID format: {job_id}')
        
        job = upload_queue_manager.get_job(job_id)
        
        if not job:
            return error_response(f"Job {job_id} not found", status_code=status.HTTP_404_NOT_FOUND)
        
        # Check permission (user can only see their own jobs unless admin)
        if not request.user.is_staff and job.created_by != request.user:
            return error_response("Permission denied", status_code=status.HTTP_403_FORBIDDEN)
        
        job_data = upload_queue_manager._serialize_job(job)
        job_data['source_files'] = job.source_files  # Include full file list
        
        return success_response("Job details retrieved", job_data)
        
    except Exception as e:
        logger.error(f"Error getting job detail: {e}", exc_info=True)
        return BaseViewMixin.handle_error(e, 'get_job_detail')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pause_job(request, job_id):
    """Pause a job"""
    try:
        job = upload_queue_manager.get_job(job_id)
        
        if not job:
            return error_response(f"Job {job_id} not found", status_code=status.HTTP_404_NOT_FOUND)
        
        # Check permission
        if not request.user.is_staff and job.created_by != request.user:
            return error_response("Permission denied", status_code=status.HTTP_403_FORBIDDEN)
        
        success = upload_queue_manager.pause_job(job_id)
        
        if success:
            return success_response("Job paused successfully", {'job_id': job_id})
        else:
            return error_response("Failed to pause job")
        
    except Exception as e:
        logger.error(f"Error pausing job: {e}", exc_info=True)
        return BaseViewMixin.handle_error(e, 'pause_job')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resume_job(request, job_id):
    """Resume a paused job"""
    try:
        job = upload_queue_manager.get_job(job_id)
        
        if not job:
            return error_response(f"Job {job_id} not found", status_code=status.HTTP_404_NOT_FOUND)
        
        # Check permission
        if not request.user.is_staff and job.created_by != request.user:
            return error_response("Permission denied", status_code=status.HTTP_403_FORBIDDEN)
        
        success = upload_queue_manager.resume_job(job_id)
        
        if success:
            # Queue processing again
            from ..tasks import process_upload_job
            process_upload_job.delay(job_id)
            
            return success_response("Job resumed successfully", {'job_id': job_id})
        else:
            return error_response("Failed to resume job")
        
    except Exception as e:
        logger.error(f"Error resuming job: {e}", exc_info=True)
        return BaseViewMixin.handle_error(e, 'resume_job')


@api_view(['POST', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_job(request, job_id):
    """
    Update a job (e.g., remove files from source_files)
    """
    try:
        job = upload_queue_manager.get_job(job_id)
        
        if not job:
            return error_response(f"Job {job_id} not found", status_code=status.HTTP_404_NOT_FOUND)
        
        # Check permission
        if not request.user.is_staff and job.created_by != request.user:
            return error_response("Permission denied", status_code=status.HTTP_403_FORBIDDEN)
        
        # Only allow updates to queued or completed jobs
        if job.status not in ['queued', 'completed', 'failed', 'cancelled']:
            return error_response("Cannot update job that is currently processing", status_code=status.HTTP_400_BAD_REQUEST)
        
        data = request.data if isinstance(request.data, dict) else {}
        
        # Update source_files if provided
        if 'source_files' in data:
            job.source_files = data['source_files']
            # Update total_items to match
            if 'total_items' in data:
                job.total_items = data['total_items']
            else:
                job.total_items = len(data['source_files'])
            job.save(update_fields=['source_files', 'total_items'])
            logger.info(f"Updated job {job_id}: {len(data['source_files'])} files remaining")
        
        return success_response("Job updated successfully", upload_queue_manager._serialize_job(job))
        
    except Exception as e:
        logger.error(f"Error updating job: {e}", exc_info=True)
        return BaseViewMixin.handle_error(e, 'update_job')


# Cancel job removed - use delete_job instead which removes everything


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def retry_job(request, job_id):
    """
    Retry a failed or stuck job
    
    Resets job status to 'queued' and triggers processing
    """
    try:
        # Validate job_id
        try:
            uuid.UUID(str(job_id))
        except (ValueError, AttributeError):
            return bad_request_response(f'Invalid job ID format: {job_id}')
        
        job = upload_queue_manager.get_job(job_id)
        
        if not job:
            return error_response(f"Job {job_id} not found", status_code=status.HTTP_404_NOT_FOUND)
        
        # Check permission
        if not request.user.is_staff and job.created_by != request.user:
            return error_response("Permission denied", status_code=status.HTTP_403_FORBIDDEN)
        
        # Only allow retry for failed or stuck jobs
        if job.status == 'completed' and job.failed_items == 0:
            return bad_request_response("Cannot retry a successfully completed job")
        
        # Reset job status to queued
        job.status = 'queued'
        job.paused = False
        job.cancelled = False
        job.error_message = None
        job.save(update_fields=['status', 'paused', 'cancelled', 'error_message'])
        
        # Queue processing
        from ..tasks import process_upload_job
        process_upload_job.delay(job_id)
        
        logger.info(f"Retried job {job_id}")
        return success_response("Job retried successfully", {'job_id': job_id})
        
    except Exception as e:
        logger.error(f"Error retrying job: {e}", exc_info=True)
        return BaseViewMixin.handle_error(e, 'retry_job')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_queue_stats(request):
    """
    Get queue statistics with processing health information
    
    Returns:
    - Total jobs
    - Jobs by status
    - Jobs by type
    - Average wait time
    - Active jobs count
    - System resources
    - File processing status
    - Embedding status
    """
    try:
        from ai_assistant.models import UploadedFile, DocumentChunk
        from django.utils import timezone
        from datetime import timedelta
        
        queue_data = upload_queue_manager.get_queue_status()
        stats = queue_data['stats']
        
        # Calculate average wait time for completed jobs
        completed_jobs = UploadJob.objects.filter(status='completed', started_at__isnull=False)
        if completed_jobs.exists():
            wait_times = []
            for job in completed_jobs:
                if job.started_at and job.created_at:
                    wait_time = (job.started_at - job.created_at).total_seconds()
                    wait_times.append(wait_time)
            
            avg_wait_time = sum(wait_times) / len(wait_times) if wait_times else 0
        else:
            avg_wait_time = 0
        
        stats['average_wait_time_seconds'] = avg_wait_time
        stats['active_jobs'] = stats['uploading'] + stats['processing']
        
        # Add stuck job monitoring
        now = timezone.now()
        warning_jobs = UploadJob.objects.filter(
            status='queued',
            created_at__lt=now - timedelta(minutes=30),
            created_at__gte=now - timedelta(hours=2),
            cancelled=False
        )
        critical_jobs = UploadJob.objects.filter(
            status='queued',
            created_at__lt=now - timedelta(hours=2),
            cancelled=False
        )
        
        stats['stuck_jobs'] = {
            'warning_count': warning_jobs.count(),  # Jobs queued >30 minutes
            'critical_count': critical_jobs.count(),  # Jobs queued >2 hours
            'warning_jobs': [
                {
                    'job_id': str(job.job_id),
                    'job_type': job.job_type,
                    'age_minutes': round((now - job.created_at).total_seconds() / 60, 1),
                    'source_path': job.source_path[:100]
                }
                for job in warning_jobs[:5]
            ],
            'critical_jobs': [
                {
                    'job_id': str(job.job_id),
                    'job_type': job.job_type,
                    'age_hours': round((now - job.created_at).total_seconds() / 3600, 1),
                    'source_path': job.source_path[:100]
                }
                for job in critical_jobs[:5]
            ]
        }
        
        # Add system resource information
        resources = upload_queue_manager.check_system_resources()
        stats['system_resources'] = {
            'cpu_percent': resources['cpu_percent'],
            'memory_percent': resources['memory_percent'],
            'memory_available_gb': round(resources['memory_available_gb'], 2),
            'resources_ok': resources['resources_ok'],
            'should_pause_low_priority': resources['should_pause_low_priority']
        }
        
        # Add file processing status
        now = timezone.now()
        pending_files = UploadedFile.objects.filter(processing_status='pending')
        stuck_files = pending_files.filter(uploaded_at__lt=now - timedelta(minutes=5))
        
        stats['file_processing'] = {
            'total_files': UploadedFile.objects.count(),
            'pending': pending_files.count(),
            'stuck_pending': stuck_files.count(),  # Files pending > 5 minutes
            'processing': UploadedFile.objects.filter(processing_status__in=['metadata_extracting', 'chunking', 'embedding']).count(),
            'ready': UploadedFile.objects.filter(processing_status='ready').count(),
            'failed': UploadedFile.objects.filter(processing_status='failed').count(),
            'ready_percentage': round(UploadedFile.objects.filter(processing_status='ready').count() / max(UploadedFile.objects.count(), 1) * 100, 2),
        }
        
        # Add embedding status
        total_chunks = DocumentChunk.objects.count()
        chunks_with_embeddings = DocumentChunk.objects.exclude(embedding__isnull=True).count()
        
        stats['embedding_status'] = {
            'total_chunks': total_chunks,
            'chunks_with_embeddings': chunks_with_embeddings,
            'chunks_without_embeddings': total_chunks - chunks_with_embeddings,
            'embedding_completion_percentage': round(chunks_with_embeddings / max(total_chunks, 1) * 100, 2),
        }
        
        # Add queue manager settings
        stats['queue_settings'] = {
            'max_concurrent_jobs': upload_queue_manager.max_concurrent_jobs,
            'max_files_per_job': upload_queue_manager.max_files_per_job,
            'cpu_threshold': upload_queue_manager.cpu_threshold,
            'memory_threshold': upload_queue_manager.memory_threshold
        }
        
        return success_response("Queue statistics retrieved", stats)
        
    except Exception as e:
        logger.error(f"Error getting queue stats: {e}", exc_info=True)
        return BaseViewMixin.handle_error(e, 'get_queue_stats')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def discover_webpage_files(request):
    """
    Discover downloadable files from a webpage (recursive crawl)
    
    POST Request body:
    {
        "url": "https://example.com",
        "max_depth": 2,  # Optional, default: 2
        "same_domain_only": true,  # Optional, default: true
        "file_type_filters": ["pdf", "docx"],  # Optional, empty = all types
        "max_file_size_mb": 20  # Optional, default: 20
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "discovered_files": [...],
            "total_pages_crawled": 5,
            "total_files_found": 12,
            "total_files_after_filter": 10,
            "crawl_time_seconds": 8.5
        }
    }
    """
    try:
        url = request.data.get('url', '').strip()
        if not url:
            return bad_request_response('URL is required')
        
        # Get configuration from request or use defaults
        max_depth = int(request.data.get('max_depth', 2))
        same_domain_only = request.data.get('same_domain_only', True)
        file_type_filters = request.data.get('file_type_filters', [])
        max_file_size_mb = int(request.data.get('max_file_size_mb', 20))
        
        # Validate max_depth (0-5)
        if max_depth < 0 or max_depth > 5:
            return bad_request_response('max_depth must be between 0 and 5')
        
        # Validate max_file_size_mb
        if max_file_size_mb < 0:
            return bad_request_response('max_file_size_mb must be >= 0')
        
        # Create crawler config
        config = WebpageCrawlerConfig(
            max_depth=max_depth,
            same_domain_only=same_domain_only,
            file_type_filters=file_type_filters if isinstance(file_type_filters, list) else [],
            max_file_size_mb=max_file_size_mb,
        )
        
        # Get default settings from Django settings if available
        crawler_settings = getattr(settings, 'WEBPAGE_CRAWLER_CONFIG', {})
        if crawler_settings:
            config.max_pages = crawler_settings.get('default_max_pages', 50)
            config.max_files = crawler_settings.get('default_max_files', 200)
            config.delay_between_requests = crawler_settings.get('default_delay_seconds', 1.0)
            config.concurrent_requests = crawler_settings.get('default_concurrent_requests', 3)
            config.timeout_per_page = crawler_settings.get('default_timeout_seconds', 30)
            config.respect_robots_txt = crawler_settings.get('respect_robots_txt', True)
        
        # Create crawler and crawl
        crawler = WebpageCrawler(config)
        result = crawler.crawl_webpage(url, config)
        
        logger.info(f"Webpage discovery completed for {url}: {result['total_files_after_filter']} files from {result['total_pages_crawled']} pages")
        
        return success_response("Files discovered successfully", result)
        
    except ValueError as e:
        logger.warning(f"Invalid request for discover_webpage_files: {e}")
        return bad_request_response(str(e))
    except Exception as e:
        logger.error(f"Error discovering webpage files: {e}", exc_info=True)
        return error_response(f"Failed to discover files: {str(e)}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def queue_webpage_files(request):
    """
    Queue selected files from webpage discovery for download
    
    POST Request body:
    {
        "files": [
            {"url": "https://example.com/file1.pdf", "name": "file1.pdf"},
            {"url": "https://example.com/file2.docx", "name": "file2.docx"}
        ],
        "source": "https://example.com"  # Original webpage URL
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "job_id": "...",
            "job_type": "webpage",
            "status": "pending",
            "total_items": 2
        }
    }
    """
    try:
        files = request.data.get('files', [])
        source = request.data.get('source', '')
        
        if not files or not isinstance(files, list):
            return bad_request_response('files array is required')
        
        if not source:
            return bad_request_response('source URL is required')
        
        if len(files) == 0:
            return bad_request_response('At least one file must be selected')
        
        # Convert discovered files to format expected by upload_queue_manager
        source_files = []
        for file_info in files:
            if not isinstance(file_info, dict) or 'url' not in file_info:
                continue
            
            source_files.append({
                'url': file_info['url'],
                'name': file_info.get('name', 'unknown'),
                'type': file_info.get('type', 'other'),
                'size': file_info.get('size'),
                'size_mb': file_info.get('size_mb'),
            })
        
        if not source_files:
            return bad_request_response('No valid files provided')
        
        # Create upload job
        priority = 5  # Default priority
        job = upload_queue_manager.add_job(
            job_type='webpage',
            source_path=source,
            source_files=source_files,
            priority=priority,
            metadata={'discovered_files_count': len(source_files)},
            user=request.user
        )
        
        # Queue processing
        from ..tasks import process_upload_job
        process_upload_job.delay(str(job.job_id))
        
        logger.info(f"Created webpage upload job {job.job_id} with {len(source_files)} files for user {request.user.username}")
        
        return success_response(
            "Files queued successfully",
            {
                'job_id': str(job.job_id),
                'job_type': job.job_type,
                'status': job.status,
                'total_items': job.total_items,
            }
        )
        
    except Exception as e:
        logger.error(f"Error queuing webpage files: {e}", exc_info=True)
        return BaseViewMixin.handle_error(e, 'queue_webpage_files')

