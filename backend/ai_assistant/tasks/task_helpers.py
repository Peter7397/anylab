"""
Shared helper functions for Celery tasks.
"""

import logging
import os
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


def calculate_file_priority(file_size):
    """
    Calculate processing priority for a file based on its size.
    
    Smaller files get higher priority (processed first) to show faster progress.
    
    Priority scale (0-9, higher = more priority):
    - Less than 1 MB: priority 9 (highest - process first)
    - 1 to 10 MB: priority 7 (high)
    - 10 to 100 MB: priority 5 (medium)
    - More than 100 MB: priority 3 (low - process last)
    
    Args:
        file_size: File size in bytes
        
    Returns:
        int: Priority value (0-9)
    """
    if not file_size or file_size == 0:
        return 5  # Default priority for unknown size
    
    # Convert to MB
    size_mb = file_size / (1024 * 1024)
    
    if size_mb < 1:
        return 9  # Highest priority for small files
    elif size_mb < 10:
        return 7  # High priority for medium-small files
    elif size_mb < 100:
        return 5  # Medium priority for medium files
    else:
        return 3  # Low priority for large files


def update_file_status_in_job(job_id, filename, status_updates):
    """
    Update per-file status in UploadJob source_files JSON
    
    Args:
        job_id: UploadJob ID
        filename: File name to update
        status_updates: Dict with status fields to update
    """
    from ..models import UploadJob
    
    try:
        # Use select_for_update to prevent race conditions
        with transaction.atomic():
            job = UploadJob.objects.select_for_update().get(job_id=job_id)
            source_files = job.source_files or []
            
            # Find and update the file entry - improved matching logic
            updated = False
            for idx, file_info in enumerate(source_files):
                # Try multiple matching strategies
                file_name = file_info.get('name', '')
                file_path = file_info.get('path', '')
                
                # Exact match (most reliable)
                if file_name == filename:
                    file_info.update(status_updates)
                    source_files[idx] = file_info
                    updated = True
                    break
                # Path ends with filename
                elif file_path and filename in file_path:
                    file_info.update(status_updates)
                    source_files[idx] = file_info
                    updated = True
                    break
                # Filename in path (basename match)
                elif file_path and os.path.basename(file_path) == filename:
                    file_info.update(status_updates)
                    source_files[idx] = file_info
                    updated = True
                    break
                # Filename in name (partial match for encoded filenames)
                elif file_name and filename in file_name:
                    file_info.update(status_updates)
                    source_files[idx] = file_info
                    updated = True
                    break
            
            if updated:
                # Force update by creating new list to ensure JSON field is properly updated
                job.source_files = list(source_files)  # Create new list to trigger JSON field update
                job.save(update_fields=['source_files'])
                logger.debug(f"Updated status for file {filename} in job {job_id}: {status_updates}")
            else:
                logger.warning(f"Could not find file {filename} in job {job_id} to update status. Available files: {[f.get('name', 'unknown') for f in source_files[:5]]}")
    except UploadJob.DoesNotExist:
        logger.warning(f"UploadJob {job_id} not found for status update")
    except Exception as e:
        logger.error(f"Failed to update file status in job {job_id} for {filename}: {e}", exc_info=True)


def bulk_update_file_statuses_in_job(job_id, file_updates):
    """
    OPTIMIZATION: Batch update multiple file statuses in a single database operation
    
    Args:
        job_id: UploadJob ID
        file_updates: List of dicts with 'filename' and 'status_updates' keys
                     Example: [{'filename': 'file1.pdf', 'status_updates': {'upload_status': 'uploaded'}}, ...]
    
    Returns:
        Dict with 'updated_count' and 'failed_count'
    """
    from ..models import UploadJob
    
    if not file_updates:
        return {'updated_count': 0, 'failed_count': 0}
    
    try:
        with transaction.atomic():
            job = UploadJob.objects.select_for_update().get(job_id=job_id)
            source_files = job.source_files or []
            
            updated_count = 0
            failed_count = 0
            
            # Process all updates in one pass
            for update_info in file_updates:
                filename = update_info.get('filename')
                status_updates = update_info.get('status_updates', {})
                
                if not filename:
                    failed_count += 1
                    continue
                
                # Find and update the file entry
                updated = False
                for idx, file_info in enumerate(source_files):
                    file_name = file_info.get('name', '')
                    file_path = file_info.get('path', '')
                    
                    # Try multiple matching strategies
                    if (file_name == filename or
                        (file_path and filename in file_path) or
                        (file_path and os.path.basename(file_path) == filename) or
                        (file_name and filename in file_name)):
                        file_info.update(status_updates)
                        source_files[idx] = file_info
                        updated = True
                        updated_count += 1
                        break
                
                if not updated:
                    failed_count += 1
                    logger.debug(f"Could not find file {filename} in job {job_id} for batch update")
            
            # Save all updates in a single database operation
            if updated_count > 0:
                job.source_files = list(source_files)
                job.save(update_fields=['source_files'])
                logger.debug(f"Bulk updated {updated_count} file(s) in job {job_id} in single operation")
            
            return {
                'updated_count': updated_count,
                'failed_count': failed_count,
                'total': len(file_updates)
            }
            
    except UploadJob.DoesNotExist:
        logger.warning(f"UploadJob {job_id} not found for batch status update")
        return {'updated_count': 0, 'failed_count': len(file_updates), 'total': len(file_updates)}
    except Exception as e:
        logger.error(f"Failed to batch update file statuses in job {job_id}: {e}", exc_info=True)
        return {'updated_count': 0, 'failed_count': len(file_updates), 'total': len(file_updates)}


def update_file_processing_status(uploaded_file_id, status, result=None, error=None):
    """
    Update processing status in UploadJob when file processing completes/fails
    
    Args:
        uploaded_file_id: UploadedFile ID
        status: 'processing', 'ready', or 'failed'
        result: Processing result dict (optional)
        error: Error message (optional)
    """
    from ..models import UploadedFile, UploadJob
    
    try:
        # Find UploadJob that contains this file
        uploaded_file = UploadedFile.objects.get(id=uploaded_file_id)
        
        # Normalize filenames for matching
        uf_basename = os.path.basename(uploaded_file.filename)
        uf_name_no_ext = os.path.splitext(uf_basename)[0]
        # Remove common suffixes like "_1" that Django adds for duplicates
        uf_name_normalized = uf_name_no_ext.rstrip('_0123456789')
        
        # Find job by searching source_files for uploaded_file_id or filename
        all_jobs = UploadJob.objects.all()
        matching_jobs = []
        
        for job in all_jobs:
            source_files = job.source_files or []
            for file_info in source_files:
                # Match by uploaded_file_id (most reliable)
                if file_info.get('uploaded_file_id') == uploaded_file_id:
                    matching_jobs.append((job, file_info))
                    break
                
                # Fallback: match by filename (handle various formats)
                file_name = file_info.get('name', '')
                file_path = file_info.get('path', '')
                
                # Normalize job file name
                job_basename = os.path.basename(file_name) if file_name else os.path.basename(file_path) if file_path else ''
                job_name_no_ext = os.path.splitext(job_basename)[0] if job_basename else ''
                job_name_normalized = job_name_no_ext.rstrip('_0123456789') if job_name_no_ext else ''
                
                # Match by normalized basename (handles _1, _2 suffixes)
                if job_name_normalized and uf_name_normalized and job_name_normalized == uf_name_normalized:
                    matching_jobs.append((job, file_info))
                    break
                # Match by exact basename
                elif job_basename == uf_basename:
                    matching_jobs.append((job, file_info))
                    break
                # Match by filename in path
                elif uf_basename in file_path or uf_basename in file_name:
                    matching_jobs.append((job, file_info))
                    break
                # Match by job filename in uploaded_file filename
                elif job_basename and job_basename in uploaded_file.filename:
                    matching_jobs.append((job, file_info))
                    break
        
        if not matching_jobs:
            logger.warning(f"Could not find UploadJob containing file {uploaded_file_id} ({uploaded_file.filename})")
            return
        
        # Update all matching jobs (in case file appears in multiple jobs)
        for job, file_info in matching_jobs:
            source_files = job.source_files or []
            updated = False
            
            for idx, sf in enumerate(source_files):
                # Match by uploaded_file_id (most reliable)
                if sf.get('uploaded_file_id') == uploaded_file_id:
                    # Update processing status
                    sf['processing_status'] = status
                    sf['processed_at'] = timezone.now().isoformat()
                    
                    if status == 'ready':
                        sf['processing_error'] = None
                        # Update chunk/embedding counts if available
                        if result:
                            sf['chunk_count'] = result.get('chunk_count', 0)
                            sf['embedding_count'] = result.get('embedding_count', 0)
                    elif status == 'failed':
                        sf['processing_error'] = error or 'Processing failed'
                    
                    source_files[idx] = sf
                    updated = True
                    break
                # Fallback: match by filename
                elif sf.get('name') == uploaded_file.filename:
                    # Update processing status
                    sf['processing_status'] = status
                    sf['processed_at'] = timezone.now().isoformat()
                    # Also update uploaded_file_id if not set
                    if not sf.get('uploaded_file_id'):
                        sf['uploaded_file_id'] = uploaded_file_id
                    
                    if status == 'ready':
                        sf['processing_error'] = None
                        if result:
                            sf['chunk_count'] = result.get('chunk_count', 0)
                            sf['embedding_count'] = result.get('embedding_count', 0)
                    elif status == 'failed':
                        sf['processing_error'] = error or 'Processing failed'
                    
                    source_files[idx] = sf
                    updated = True
                    break
            
            if updated:
                # Use transaction to ensure atomic update
                with transaction.atomic():
                    # Refresh job to get latest data before saving (use select_for_update to lock)
                    job_to_update = UploadJob.objects.select_for_update().get(job_id=job.job_id)
                    # Get fresh source_files to avoid overwriting concurrent updates
                    fresh_source_files = job_to_update.source_files or []
                    # Find and update the same file in fresh data
                    for idx, sf in enumerate(fresh_source_files):
                        if sf.get('uploaded_file_id') == uploaded_file_id or sf.get('name') == uploaded_file.filename:
                            # Apply the same updates to fresh data
                            sf['processing_status'] = status
                            sf['processed_at'] = timezone.now().isoformat()
                            if status == 'ready':
                                sf['processing_error'] = None
                                if result:
                                    sf['chunk_count'] = result.get('chunk_count', 0)
                                    sf['embedding_count'] = result.get('embedding_count', 0)
                            elif status == 'failed':
                                sf['processing_error'] = error or 'Processing failed'
                            if not sf.get('uploaded_file_id'):
                                sf['uploaded_file_id'] = uploaded_file_id
                            fresh_source_files[idx] = sf
                            break
                    # Force update by creating new list to ensure JSON field is properly updated
                    job_to_update.source_files = list(fresh_source_files)  # Create new list to trigger JSON field update
                    job_to_update.save(update_fields=['source_files'])
                    logger.debug(f"Updated processing status for file {uploaded_file_id} in job {job_to_update.job_id} to {status}")
                    
                    # Recalculate job status based on all files
                    recalculate_job_status(job_to_update.job_id)
            else:
                logger.warning(f"Could not find file {uploaded_file_id} in job {job.job_id} source_files to update processing status")
                
    except UploadedFile.DoesNotExist:
        logger.warning(f"UploadedFile {uploaded_file_id} not found for status update")
    except Exception as e:
        logger.error(f"Failed to update processing status for file {uploaded_file_id}: {e}", exc_info=True)


def increment_file_retry_count(uploaded_file_id, current_attempt):
    """
    Increment retry count for a file in UploadJob source_files
    
    Args:
        uploaded_file_id: UploadedFile ID
        current_attempt: Current attempt number
    """
    from ..models import UploadedFile, UploadJob
    
    try:
        uploaded_file = UploadedFile.objects.get(id=uploaded_file_id)
        
        # Find job by searching all jobs (more reliable than JSON contains)
        all_jobs = UploadJob.objects.all()
        
        for job in all_jobs:
            source_files = job.source_files or []
            updated = False
            
            for idx, file_info in enumerate(source_files):
                if file_info.get('uploaded_file_id') == uploaded_file_id or file_info.get('name') == uploaded_file.filename:
                    # Increment retry count
                    file_info['retry_count'] = current_attempt
                    source_files[idx] = file_info
                    updated = True
                    break
            
            if updated:
                job.source_files = list(source_files)  # Force JSON update
                job.save(update_fields=['source_files'])
                logger.debug(f"Updated retry count for file {uploaded_file_id} to {current_attempt}")
                break  # Only update first matching job
            
    except UploadedFile.DoesNotExist:
        logger.warning(f"UploadedFile {uploaded_file_id} not found for retry count update")
    except Exception as e:
        logger.warning(f"Failed to increment retry count for file {uploaded_file_id}: {e}")


def reset_file_retry_count(uploaded_file_id):
    """
    Reset retry count for a file in UploadJob source_files after successful processing
    
    Args:
        uploaded_file_id: UploadedFile ID
    """
    from ..models import UploadedFile, UploadJob
    
    try:
        uploaded_file = UploadedFile.objects.get(id=uploaded_file_id)
        
        # Find job by searching all jobs (more reliable than JSON contains)
        all_jobs = UploadJob.objects.all()
        
        for job in all_jobs:
            source_files = job.source_files or []
            updated = False
            
            for idx, file_info in enumerate(source_files):
                if file_info.get('uploaded_file_id') == uploaded_file_id or file_info.get('name') == uploaded_file.filename:
                    # Reset retry count
                    file_info['retry_count'] = 0
                    source_files[idx] = file_info
                    updated = True
                    break
            
            if updated:
                job.source_files = list(source_files)  # Force JSON update
                job.save(update_fields=['source_files'])
                logger.debug(f"Reset retry count for file {uploaded_file_id}")
                break  # Only update first matching job
            
    except UploadedFile.DoesNotExist:
        pass  # Ignore if file not found
    except Exception as e:
        logger.warning(f"Failed to reset retry count for file {uploaded_file_id}: {e}")


def mark_job_completed(job_id: str) -> bool:
    """
    Mark job as completed and remove from Redis (Phase 4: Redis for active jobs only)
    
    Args:
        job_id: Job UUID
        
    Returns:
        True if successful, False otherwise
    """
    from ..models import UploadJob
    
    try:
        # Update PostgreSQL
        job = UploadJob.objects.get(job_id=job_id)
        job.status = 'completed'
        if not job.completed_at:
            job.completed_at = timezone.now()
        job.save(update_fields=['status', 'completed_at'])
        
        # Remove from Redis
        try:
            from ..service_classes.redis_job_queue_manager import redis_job_queue_manager
            if redis_job_queue_manager and redis_job_queue_manager.is_available():
                redis_job_queue_manager.remove_job_from_redis(job_id)
                logger.info(f"Marked job {job_id} as completed and removed from Redis")
        except Exception as e:
            logger.warning(f"Error removing job {job_id} from Redis: {e}")
        
        return True
        
    except UploadJob.DoesNotExist:
        logger.warning(f"Job {job_id} not found for completion")
        return False
    except Exception as e:
        logger.error(f"Error marking job {job_id} as completed: {e}", exc_info=True)
        return False


def recalculate_job_status(job_id):
    """
    Recalculate UploadJob status based on individual file statuses
    
    SIMPLIFIED: 4-state model
    - 'queued': All files pending (not started)
    - 'uploading': Some files being uploaded (status = processing, no uploaded_file_id)
    - 'processing': Some files being processed (status = processing, has uploaded_file_id)
    - 'completed': All files completed (ready, skipped, or failed - terminal state)
    """
    from ..models import UploadJob
    
    try:
        job = UploadJob.objects.get(job_id=job_id)
        source_files = job.source_files or []
        
        if not source_files:
            return
        
        total = len(source_files)
        
        # Count files by state
        pending = 0  # Not started (pending upload or processing)
        uploading = 0  # Being uploaded (processing status, no uploaded_file_id)
        processing = 0  # Being processed (processing status, has uploaded_file_id)
        completed = 0  # Done (ready, skipped, or failed - terminal state)
        
        for f in source_files:
            upload_status = f.get('upload_status', 'pending')
            processing_status = f.get('processing_status', 'pending')
            uploaded_file_id = f.get('uploaded_file_id')
            
            # Check if file is skipped (duplicate) - terminal state
            if upload_status == 'skipped' or processing_status == 'skipped':
                completed += 1
            # Check if file is ready (fully processed) - terminal state
            elif processing_status == 'ready' and uploaded_file_id:
                completed += 1
            # Check if file processing failed - terminal state
            elif processing_status == 'failed' or upload_status == 'failed':
                completed += 1
            # Check if file is being processed (has uploaded_file_id)
            elif processing_status in ['processing', 'chunking', 'embedding', 'metadata_extracting'] and uploaded_file_id:
                processing += 1
            # Check if file is being uploaded (no uploaded_file_id yet)
            elif upload_status == 'uploading' or (upload_status == 'uploaded' and not uploaded_file_id):
                uploading += 1
            # Otherwise, pending
            else:
                pending += 1
        
        # Determine job status based on file states
        if completed == total:
            # All files are in terminal state (ready, skipped, or failed)
            new_status = 'completed'
        elif processing > 0:
            # Some files are being processed
            new_status = 'processing'
        elif uploading > 0:
            # Some files are being uploaded
            new_status = 'uploading'
        else:
            # All files are pending
            new_status = 'queued'
        
        # Update job status if changed
        if job.status != new_status:
            old_status = job.status
            job.status = new_status
            if new_status == 'completed':
                job.completed_at = timezone.now()
            job.save(update_fields=['status', 'completed_at'])
            logger.info(
                f"Job {job_id} status updated to {new_status} "
                f"(pending: {pending}, uploading: {uploading}, processing: {processing}, completed: {completed}/{total})"
            )
            
            # If job became completed, remove from Redis (active jobs only)
            if new_status == 'completed' and old_status != 'completed':
                try:
                    from ..service_classes.redis_job_queue_manager import redis_job_queue_manager
                    if redis_job_queue_manager and redis_job_queue_manager.is_available():
                        redis_job_queue_manager.remove_job_from_redis(job_id)
                        logger.info(f"Removed completed job {job_id} from Redis")
                except Exception as e:
                    logger.warning(f"Error removing completed job {job_id} from Redis: {e}")
            
    except UploadJob.DoesNotExist:
        logger.warning(f"UploadJob {job_id} not found for status recalculation")
    except Exception as e:
        logger.warning(f"Failed to recalculate job status for {job_id}: {e}")

