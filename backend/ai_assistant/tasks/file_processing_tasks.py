"""
File processing Celery tasks.
"""

import logging
import os
import uuid
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
from celery import shared_task, group
from django.utils import timezone
from django.db import transaction
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import requests

from ..models import UploadedFile, UploadJob, DocumentFile, DocumentChunk
from ..automatic_file_processor import automatic_file_processor
from ..service_classes.upload_queue_manager import upload_queue_manager
from ..service_classes.rag_service import RAGService
from .task_helpers import (
    calculate_file_priority,
    update_file_status_in_job,
    update_file_processing_status,
    increment_file_retry_count,
    reset_file_retry_count,
    recalculate_job_status,
)

logger = logging.getLogger(__name__)


@shared_task(name='ai_assistant.tasks.build_graph_for_file')
def build_graph_for_file(uploaded_file_id: int):
    """
    Build GraphRAG for a file asynchronously
    
    This task runs after the file is marked as ready, so it doesn't delay
    the file from becoming searchable. GraphRAG is an optional enhancement.
    
    Args:
        uploaded_file_id: ID of the UploadedFile to build GraphRAG for
    """
    try:
        uploaded_file = UploadedFile.objects.get(id=uploaded_file_id)
        logger.info(f"Building GraphRAG for {uploaded_file.filename} (ID: {uploaded_file_id})")
        
        from ..service_classes.graph_builder import GraphBuilder
        graph_builder = GraphBuilder()
        
        # Get chunks from database
        chunks = DocumentChunk.objects.filter(uploaded_file=uploaded_file)
        
        if not chunks.exists():
            logger.warning(f"No chunks found for file {uploaded_file_id}, skipping GraphRAG")
            return {
                'status': 'skipped',
                'uploaded_file_id': uploaded_file_id,
                'reason': 'No chunks found'
            }
        
        # Build graph from document (creates entities and relationships)
        graph_result = graph_builder.build_graph_from_document(uploaded_file, list(chunks))
        
        if graph_result.get('success', False):
            entity_count = graph_result.get('entity_nodes_created', 0)
            relationship_count = graph_result.get('relationships_created', 0)
            logger.info(
                f"GraphRAG built successfully for {uploaded_file.filename}: "
                f"{entity_count} entities, {relationship_count} relationships"
            )
            return {
                'status': 'success',
                'uploaded_file_id': uploaded_file_id,
                'entity_count': entity_count,
                'relationship_count': relationship_count
            }
        else:
            logger.warning(
                f"GraphRAG building failed for {uploaded_file.filename}: "
                f"{graph_result.get('error', 'Unknown error')}"
            )
            return {
                'status': 'failed',
                'uploaded_file_id': uploaded_file_id,
                'error': graph_result.get('error', 'Unknown error')
            }
            
    except ImportError:
        logger.warning("GraphBuilder not available, skipping GraphRAG construction")
        return {
            'status': 'skipped',
            'uploaded_file_id': uploaded_file_id,
            'reason': 'GraphBuilder not available'
        }
    except UploadedFile.DoesNotExist:
        logger.error(f"UploadedFile {uploaded_file_id} not found for GraphRAG building")
        return {
            'status': 'error',
            'uploaded_file_id': uploaded_file_id,
            'error': 'UploadedFile not found'
        }
    except Exception as e:
        logger.error(f"GraphRAG task failed for file {uploaded_file_id}: {e}", exc_info=True)
        return {
            'status': 'error',
            'uploaded_file_id': uploaded_file_id,
            'error': str(e)
        }


@shared_task(
    bind=True, 
    name='ai_assistant.tasks.process_file_automatically',
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 10},
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
    priority=None
)
def process_file_automatically(self, uploaded_file_id: int, file_priority: Optional[int] = None) -> Dict[str, Any]:
    """
    Background task for automatic file processing
    
    SIMPLIFIED APPROACH: All files treated equally, immediate processing
    - Unlimited chunks
    - BGE-M3 only
    - Per-file retry mechanism with independent retry counts
    - All files processed equally (no priority differentiation)
    - Fast processing (reduced retry delays)
    
    Args:
        uploaded_file_id: ID of the UploadedFile to process
        file_priority: Optional priority (ignored - all files treated equally)
    """
    try:
        # CRITICAL: Check if file is already successfully processed BEFORE doing anything
        # This prevents unnecessary retries and processing of already-complete files
        from ai_assistant.models import UploadedFile, DocumentChunk
        from django.db import transaction
        
        with transaction.atomic():
            uploaded_file = UploadedFile.objects.select_for_update().get(id=uploaded_file_id)
            
            # Check if file is already ready
            if uploaded_file.processing_status == 'ready':
                # Verify it's truly ready by checking chunks/embeddings
                chunks = DocumentChunk.objects.filter(uploaded_file=uploaded_file).count()
                if chunks > 0 and uploaded_file.embedding_count > 0:
                    logger.info(
                        f'File {uploaded_file_id} is already ready '
                        f'({chunks} chunks, {uploaded_file.embedding_count} embeddings). Skipping processing.'
                    )
                    return {
                        'status': 'success',
                        'uploaded_file_id': uploaded_file_id,
                        'result': {
                            'chunk_count': chunks,
                            'embedding_count': uploaded_file.embedding_count,
                            'skipped': True,
                            'reason': 'Already processed'
                        }
                    }
                else:
                    # Status says ready but no chunks - reset to pending
                    logger.warning(
                        f'File {uploaded_file_id} marked as ready but has no chunks. Resetting to pending.'
                    )
                    uploaded_file.processing_status = 'pending'
                    uploaded_file.save()
            
            # Check if file is in a terminal state that shouldn't be retried
            if uploaded_file.processing_status in ['corrupted', 'no_text_available']:
                logger.info(
                    f'File {uploaded_file_id} is in terminal state ({uploaded_file.processing_status}). '
                    f'Skipping processing.'
                )
                return {
                    'status': uploaded_file.processing_status,
                    'uploaded_file_id': uploaded_file_id,
                    'error': uploaded_file.processing_error or f'File is {uploaded_file.processing_status}',
                    'skipped': True
                }
        
        current_attempt = self.request.retries + 1
        logger.info(f'Processing file {uploaded_file_id} in background (attempt {current_attempt})')
        
        # Update processing status in UploadJob if file is part of a job
        update_file_processing_status(uploaded_file_id, 'processing')
        
        # Update per-file retry count in UploadJob
        increment_file_retry_count(uploaded_file_id, current_attempt)
        
        # Use the automatic processor with all quality guarantees
        result = automatic_file_processor.process_file_fully(uploaded_file_id)
        
        # Check if processing was successful or if file was marked as corrupted/no_text
        if result.get('status') in ['corrupted', 'no_text_available']:
            logger.info(f'File {uploaded_file_id} marked as {result.get("status")}: {result.get("error", "Unknown reason")}')
            # Update status in UploadJob
            update_file_processing_status(uploaded_file_id, result.get('status'), error=result.get('error'))
            return {
                'status': result.get('status'),
                'uploaded_file_id': uploaded_file_id,
                'error': result.get('error')
            }
        
        logger.info(f'File {uploaded_file_id} processed successfully: {result}')
        
        # Update processing status to ready in UploadJob
        update_file_processing_status(uploaded_file_id, 'ready', result)
        
        # Reset retry count on success
        reset_file_retry_count(uploaded_file_id)
        
        return {
            'status': 'success',
            'uploaded_file_id': uploaded_file_id,
            'result': result
        }
        
    except Exception as e:
        logger.error(f'Background processing failed for file {uploaded_file_id}: {e}', exc_info=True)
        
        current_attempt = self.request.retries + 1
        max_retries = 3
        
        # Mark current attempt status in database
        try:
            from ai_assistant.models import UploadedFile, DocumentChunk
            from django.db import transaction
            
            with transaction.atomic():
                uploaded_file = UploadedFile.objects.select_for_update().get(id=uploaded_file_id)
                
                # CRITICAL: Check if file was actually successfully processed despite the error
                # This handles cases where processing succeeded but a subsequent check (e.g., file existence) failed
                chunks = DocumentChunk.objects.filter(uploaded_file=uploaded_file).count()
                
                # If file has chunks and embeddings, it was successfully processed
                # Mark as ready immediately and prevent further retries
                if chunks > 0 and uploaded_file.embedding_count > 0:
                    logger.info(
                        f'File {uploaded_file_id} has {chunks} chunks and {uploaded_file.embedding_count} embeddings. '
                        f'Processing was successful - marking as ready and preventing retries.'
                    )
                    uploaded_file.processing_status = 'ready'
                    uploaded_file.processing_error = None
                    uploaded_file.processing_completed_at = timezone.now()
                    uploaded_file.save()
                    update_file_processing_status(uploaded_file_id, 'ready', result={
                        'chunk_count': chunks,
                        'embedding_count': uploaded_file.embedding_count
                    })
                    reset_file_retry_count(uploaded_file_id)
                    # Return success - don't retry
                    return {
                        'status': 'success',
                        'uploaded_file_id': uploaded_file_id,
                        'result': {
                            'chunk_count': chunks,
                            'embedding_count': uploaded_file.embedding_count
                        }
                    }
                
                # File is not ready - check if we should retry
                # Don't retry if file is already in a terminal state
                if uploaded_file.processing_status in ['ready', 'corrupted', 'no_text_available']:
                    logger.info(
                        f'File {uploaded_file_id} is in terminal state ({uploaded_file.processing_status}). '
                        f'Not retrying despite error: {str(e)}'
                    )
                    # Don't raise - return the current status
                    return {
                        'status': uploaded_file.processing_status,
                        'uploaded_file_id': uploaded_file_id,
                        'error': str(e),
                        'skipped': True
                    }
                
                uploaded_file.processing_error = f"Attempt {current_attempt}/{max_retries} failed: {str(e)}"
                uploaded_file.save()
                
                # Check if we've exceeded max retries for this file
                if current_attempt >= max_retries:
                    # Final failure - update status to failed
                    uploaded_file.processing_status = 'failed'
                    uploaded_file.save()
                    update_file_processing_status(uploaded_file_id, 'failed', error=str(e))
                    logger.warning(f'File {uploaded_file_id} failed after {max_retries} attempts')
                    # Don't retry - return failure
                    return {
                        'status': 'failed',
                        'uploaded_file_id': uploaded_file_id,
                        'error': str(e)
                    }
                else:
                    # Still retrying - keep status as processing but update error
                    update_file_processing_status(uploaded_file_id, 'processing', error=f"Retrying ({current_attempt}/{max_retries}): {str(e)}")
        except UploadedFile.DoesNotExist:
            logger.error(f'UploadedFile {uploaded_file_id} not found')
            # Don't retry if file doesn't exist
            return {
                'status': 'failed',
                'uploaded_file_id': uploaded_file_id,
                'error': 'File not found'
            }
        
        # Let Celery handle retry (with autoretry_for) only if we haven't returned yet
        raise


@shared_task(
    bind=True,
    name='ai_assistant.tasks.process_upload_job',
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 30},
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True
)
def process_upload_job(self, job_id: str) -> Dict[str, Any]:
    """
    Process an upload job - handles file uploads and creates DocumentFile records
    
    This task processes files from an UploadJob:
    1. Checks if job is paused/cancelled
    2. Processes each file in the job
    3. Uploads files, creates DocumentFile records
    4. Queues processing for each file
    5. Updates job progress
    """
    try:
        logger.info(f'Processing upload job {job_id} (attempt {self.request.retries + 1})')
        
        # Get job - may be in Redis but not yet in PostgreSQL
        job = upload_queue_manager.get_job(job_id)
        
        # If job not in PostgreSQL, try to get from Redis and persist it
        if not job:
            try:
                from ..service_classes.redis_job_queue_manager import redis_job_queue_manager
                if redis_job_queue_manager and redis_job_queue_manager.is_available():
                    redis_job = redis_job_queue_manager.get_job_from_redis(job_id)
                    if redis_job:
                        logger.info(f'Job {job_id} found in Redis but not in PostgreSQL, triggering immediate persistence')
                        # Trigger immediate persistence
                        from .job_persistence_tasks import persist_jobs_to_database
                        persist_result = persist_jobs_to_database(batch_size=1)
                        # Try to get job again after persistence
                        job = upload_queue_manager.get_job(job_id)
                        if not job:
                            logger.warning(f'Job {job_id} still not found after persistence attempt')
            except Exception as e:
                logger.warning(f'Error checking Redis for job {job_id}: {e}')
        
        if not job:
            logger.error(f'Upload job {job_id} not found in PostgreSQL or Redis')
            return {'status': 'error', 'message': 'Job not found'}
        
        # Check if cancelled
        if job.cancelled:
            logger.info(f'Job {job_id} is cancelled, skipping')
            return {'status': 'cancelled', 'job_id': job_id}
        
        # Check if paused
        if job.paused:
            logger.info(f'Job {job_id} is paused, will retry later')
            # Don't raise exception, just return - will be retried when resumed
            return {'status': 'paused', 'job_id': job_id}
        
        # Check system resources before starting
        resources = upload_queue_manager.check_system_resources()
        if resources['should_pause_low_priority'] and job.priority < 7:
            logger.info(f'Job {job_id} is low priority and resources are high - pausing')
            upload_queue_manager.pause_job(job_id)
            return {'status': 'paused', 'job_id': job_id, 'reason': 'high_resource_usage'}
        
        # Update status to processing
        upload_queue_manager.update_job_progress(job_id, status='processing')
        
        rag_service = RAGService()
        completed = job.completed_items
        failed = job.failed_items
        
        # Process files starting from checkpoint - PARALLEL PROCESSING (Phase 3)
        start_index = job.last_processed_file_index
        remaining_files = job.source_files[start_index:]
        
        logger.info(f'Processing {len(remaining_files)} files in parallel (Phase 3 optimization) in job {job_id}')
        
        # Phase 3: Parallel file processing using Celery groups
        # Process multiple files concurrently for better throughput
        # Create parallel upload tasks for remaining files
        upload_tasks = []
        file_indices = []
        
        for index, file_info in enumerate(remaining_files, start=start_index):
            # Check if paused or cancelled before creating tasks
            job.refresh_from_db()
            if job.paused or job.cancelled:
                logger.info(f'Job {job_id} paused/cancelled before creating task for file {index}')
                break
            
            filename = file_info.get('name', f'file_{index}')
            
            # Update status to 'uploading' before creating task
            update_file_status_in_job(job_id, filename, {
                'upload_status': 'uploading',
                'upload_error': None
            })
            
            # Create a task for this file upload
            upload_tasks.append(
                _process_single_file_async.s(job_id, file_info, index)
            )
            file_indices.append(index)
        
        # Execute all upload tasks in parallel using Celery group
        # FIXED: Don't call .get() within a task - causes deadlock
        # Tasks will complete asynchronously and update job status via callbacks
        if upload_tasks:
            logger.info(f'Executing {len(upload_tasks)} file upload tasks in parallel (async)')
            job_group = group(upload_tasks)
            results = job_group.apply_async()
            
            # Don't wait for results here - tasks will update job status asynchronously
            # Each _process_single_file_async task will:
            # 1. Process the file upload
            # 2. Update job status via update_file_status_in_job
            # 3. Queue processing task if successful
            logger.info(f'Queued {len(upload_tasks)} upload tasks - they will complete asynchronously and update job status')
        
        # Recalculate job status based on file states (simplified 4-state model)
        # Status will be determined by recalculate_job_status based on file states
        from ..tasks.task_helpers import recalculate_job_status
        recalculate_job_status(job_id)
        
        logger.info(f'Job {job_id} status recalculated: {completed} completed, {failed} failed out of {job.total_items} total')
        
        return {
            'status': 'success',
            'job_id': job_id,
            'completed': completed,
            'failed': failed,
            'total': job.total_items
        }
        
    except Exception as e:
        logger.error(f'Error processing upload job {job_id}: {e}', exc_info=True)
        upload_queue_manager.update_job_progress(
            job_id,
            status='failed',
            error_message=str(e)
        )
        raise


@shared_task(name='ai_assistant.tasks._process_single_file_async')
def _process_single_file_async(job_id: str, file_info: Dict[str, Any], index: int) -> Dict[str, Any]:
    """
    Async task for processing a single file in parallel (Phase 3)
    
    FIXED: This task now updates job status directly instead of returning results
    This avoids the "Never call result.get() within a task!" deadlock issue
    
    Args:
        job_id: UploadJob ID
        file_info: File information dict
        index: File index in job
        
    Returns:
        Dict with 'success', 'error', 'filename', 'uploaded_file_id', 'is_duplicate'
    """
    filename = file_info.get('name', f'file_{index}')
    
    try:
        job = UploadJob.objects.get(job_id=job_id)
        rag_service = RAGService()
        
        logger.info(f'Processing file {index + 1}/{job.total_items} in job {job_id}: {filename} (async)')
        
        # Handle different job types
        if job.job_type == 'file':
            result = _process_file_upload(job, file_info, rag_service)
        elif job.job_type == 'folder':
            result = _process_folder_file(job, file_info, rag_service)
        elif job.job_type == 'webpage':
            result = _process_webpage_file(job, file_info, rag_service)
        else:
            raise ValueError(f"Unknown job type: {job.job_type}")
        
        result['filename'] = filename
        
        # Check if result indicates duplicate
        if result.get('success') and result.get('data', {}).get('is_duplicate'):
            result['is_duplicate'] = True
            result['message'] = result.get('data', {}).get('message', 'Duplicate file - already exists')
        
        # Update job status directly (instead of returning for parent task to process)
        if result.get('success'):
            uploaded_file_id = result.get('uploaded_file_id')
            
            # Check if this was a duplicate
            if result.get('is_duplicate'):
                logger.info(f'File {filename} is a duplicate, skipping processing')
                update_file_status_in_job(job_id, filename, {
                    'upload_status': 'skipped',
                    'uploaded_file_id': uploaded_file_id,
                    'uploaded_at': timezone.now().isoformat(),
                    'upload_error': result.get('message', 'Duplicate file - already exists'),
                    'processing_status': 'skipped'
                })
            else:
                # Update per-file status in source_files
                update_file_status_in_job(job_id, filename, {
                    'upload_status': 'uploaded',
                    'uploaded_file_id': uploaded_file_id,
                    'uploaded_at': timezone.now().isoformat(),
                    'upload_error': None,
                    'processing_status': 'pending'
                })
                
                # Queue processing task immediately (progressive processing)
                if uploaded_file_id:
                    # Get queue routing from UploadQueueManager
                    target_queue = file_info.get('target_queue', 'celery')
                    
                    # Calculate file priority
                    file_size = file_info.get('size', 0)
                    file_priority = calculate_file_priority(file_size)
                    
                    # Phase 3: Time-based scheduling for OCR
                    if target_queue == 'ocr_queue':
                        from datetime import datetime
                        current_hour = datetime.now().hour
                        if 9 <= current_hour <= 18:
                            file_priority = max(3, file_priority - 2)
                            logger.info(f"OCR file {uploaded_file_id} scheduled with lower priority during peak hours")
                    
                    # Check system resources before queuing
                    resources = upload_queue_manager.check_system_resources()
                    if resources['should_pause_low_priority'] and file_priority < 5:
                        logger.warning(f"High resource usage - deferring low-priority file {uploaded_file_id}")
                        update_file_status_in_job(job_id, filename, {
                            'processing_status': 'pending',
                            'processing_error': 'Queued for processing when resources available'
                        })
                    else:
                        update_file_status_in_job(job_id, filename, {
                            'processing_status': 'pending'
                        })
                        
                        # Route to appropriate queue with priority
                        # Use the function directly since it's in the same module
                        process_file_automatically.apply_async(
                            args=[uploaded_file_id, file_priority],
                            queue=target_queue,
                            priority=file_priority
                        )
                        logger.info(f"Queued processing task for file {uploaded_file_id} ({filename}) to queue: {target_queue} with priority: {file_priority}")
        else:
            # Upload failed
            error_msg = result.get('error', 'Unknown error')
            update_file_status_in_job(job_id, filename, {
                'upload_status': 'failed',
                'upload_error': error_msg,
                'uploaded_at': timezone.now().isoformat()
            })
            
            upload_queue_manager.update_job_progress(
                job_id,
                file_error={filename: error_msg}
            )
        
        return result
        
    except Exception as e:
        logger.error(f'Error in _process_single_file_async for {filename}: {e}', exc_info=True)
        
        # Update job status with error
        update_file_status_in_job(job_id, filename, {
            'upload_status': 'failed',
            'upload_error': str(e),
            'uploaded_at': timezone.now().isoformat()
        })
        
        return {'success': False, 'error': str(e), 'filename': filename}


@shared_task(name='ai_assistant.tasks.process_document_queue')
def process_document_queue() -> None:
    """
    Process pending documents in the queue.
    This is called periodically by Celery Beat.
    """
    try:
        # Model DocumentFile does not have a 'processed' field.
        # For now, treat this task as a no-op to avoid errors, or
        # adapt to a safe listing of recent documents for visibility.
        pending_docs = DocumentFile.objects.order_by('-uploaded_at')[:0]
        
        if pending_docs.exists():
            logger.info(f'Processing {pending_docs.count()} pending documents')
            
            for doc in pending_docs:
                try:
                    # Placeholder: no processing step defined for DocumentFile
                    pass
                    
                    logger.info(f'Visited document (no-op): {doc.title}')
                    
                except Exception as e:
                    logger.error(f'Error iterating document {doc.id}: {e}')
                    
        else:
            logger.debug('No pending documents to process')
            
    except Exception as e:
        logger.error(f'Document queue processing failed: {e}', exc_info=True)


@shared_task(bind=True, name='ai_assistant.tasks.process_bulk_upload')
def process_bulk_upload(self, uploaded_file_ids: List[int]) -> Dict[str, Any]:
    """
    Process multiple files in background
    
    QUALITY FOCUS: Process ALL files with full quality guarantees
    - No compromises on chunking
    - BGE-M3 only for embeddings
    - Performance over speed
    """
    try:
        logger.info(f'Processing {len(uploaded_file_ids)} files in bulk')
        
        results = {
            'successful': 0,
            'failed': 0,
            'details': []
        }
        
        for uploaded_file_id in uploaded_file_ids:
            try:
                # Process each file using automatic processor
                result = automatic_file_processor.process_file_fully(uploaded_file_id)
                
                results['successful'] += 1
                results['details'].append({
                    'uploaded_file_id': uploaded_file_id,
                    'status': 'success',
                    'chunk_count': result.get('chunk_count', 0),
                    'embedding_count': result.get('embedding_count', 0)
                })
                
            except Exception as e:
                logger.error(f'Error processing file {uploaded_file_id}: {e}', exc_info=True)
                results['failed'] += 1
                results['details'].append({
                    'uploaded_file_id': uploaded_file_id,
                    'status': 'failed',
                    'error': str(e)
                })
        
        logger.info(f'Bulk processing completed: {results["successful"]} successful, {results["failed"]} failed')
        
        return results
        
    except Exception as e:
        logger.error(f'Bulk processing failed: {e}', exc_info=True)
        raise


def _process_file_upload(job: UploadJob, file_info: Dict[str, Any], rag_service: RAGService) -> Dict[str, Any]:
    """Process a single file upload"""
    try:
        # Get file from storage using the path stored in source_files
        file_path = file_info.get('path')
        filename = file_info.get('name')
        is_temp_file = file_info.get('is_temp', False)
        
        if not file_path:
            # Fallback: try to construct path from filename
            if filename:
                # Try common storage locations
                possible_paths = [
                    f'upload_queue/{filename}',  # Direct in upload_queue
                    f'uploads/{filename}',  # In uploads folder
                ]
                for path in possible_paths:
                    if default_storage.exists(path):
                        file_path = path
                        break
                
                if not file_path:
                    return {'success': False, 'error': f'No file path provided and file not found in common locations for: {filename}'}
            else:
                return {'success': False, 'error': 'No file path or filename provided in file_info'}
        
        if not filename:
            filename = os.path.basename(file_path)
        
        # Handle temp files - check if it's a temp file path (either Django's temp or our manual temp)
        if is_temp_file or (file_path and os.path.exists(file_path) and not default_storage.exists(file_path)):
            # Read from temp file directly (fastest - local file system)
            logger.debug(f'Reading file from temp path: {file_path}')
            if not os.path.exists(file_path):
                return {'success': False, 'error': f'Temp file not found: {file_path}'}
            with open(file_path, 'rb') as temp_file:
                file_content = temp_file.read()
        else:
            # Check if file exists in storage
            if default_storage.exists(file_path):
                # Read file from storage
                logger.debug(f'Reading file from storage: {file_path}')
                with default_storage.open(file_path, 'rb') as storage_file:
                    file_content = storage_file.read()
            elif os.path.exists(file_path):
                # Also check if it's a temp file path (fallback)
                logger.debug(f'Reading file from temp path (not in storage): {file_path}')
                with open(file_path, 'rb') as temp_file:
                    file_content = temp_file.read()
            else:
                return {'success': False, 'error': f'File not found in storage or temp: {file_path}'}
        
        if not file_content:
            return {'success': False, 'error': f'File is empty: {file_path}'}
        
        # Create file-like object for upload
        file = ContentFile(file_content, name=filename)
        
        # Upload using existing service
        logger.debug(f'Uploading file via RAG service: {filename}')
        result = rag_service.upload_document_enhanced(file, job.created_by)
        
        if result.get('success'):
            logger.info(f'Successfully uploaded file: {filename}')
            uploaded_file_id = result.get('data', {}).get('uploaded_file_id')
            
            # Check if this was a duplicate
            is_duplicate = result.get('data', {}).get('is_duplicate', False)
            if is_duplicate:
                logger.info(f'File {filename} is a duplicate (ID: {uploaded_file_id}), skipping further processing')
                return {
                    'success': True,
                    'data': result.get('data'),
                    'uploaded_file_id': uploaded_file_id,
                    'filename': filename,
                    'is_duplicate': True,
                    'message': result.get('data', {}).get('message', 'Duplicate file - already exists'),
                    'file_info': file_info
                }
            
            # Cleanup temp file if it was a temp file (both Django's temp and our manual temp)
            if (is_temp_file or (file_path and os.path.exists(file_path) and not default_storage.exists(file_path))) and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.debug(f'Cleaned up temp file: {file_path}')
                    # Also try to remove parent directory if empty
                    try:
                        parent_dir = os.path.dirname(file_path)
                        if parent_dir and os.path.exists(parent_dir) and not os.listdir(parent_dir):
                            os.rmdir(parent_dir)
                            logger.debug(f'Removed empty temp directory: {parent_dir}')
                    except Exception:
                        pass  # Ignore directory removal errors
                except Exception as e:
                    logger.warning(f'Could not delete temp file {file_path}: {e}')
            
            return {
                'success': True, 
                'data': result.get('data'), 
                'uploaded_file_id': uploaded_file_id,
                'filename': filename,
                'file_info': file_info  # Include file_info for queue routing
            }
        else:
            error_msg = result.get('message', 'Upload failed')
            logger.warning(f'Failed to upload file {filename}: {error_msg}')
            return {'success': False, 'error': error_msg}
            
    except FileNotFoundError as e:
        logger.error(f'File not found in _process_file_upload: {e}')
        return {'success': False, 'error': f'File not found: {str(e)}'}
    except Exception as e:
        logger.error(f'Error in _process_file_upload: {e}', exc_info=True)
        return {'success': False, 'error': str(e)}


def _process_folder_file(job: UploadJob, file_info: Dict[str, Any], rag_service: RAGService) -> Dict[str, Any]:
    """Process a file from folder scan"""
    try:
        # Support multiple path field names for compatibility
        file_path = file_info.get('file_path') or file_info.get('path')
        filename = file_info.get('name') or file_info.get('filename')
        
        if not file_path:
            return {'success': False, 'error': 'No file path provided in file_info'}
        
        if not os.path.exists(file_path):
            return {'success': False, 'error': f'File not found: {file_path}'}
        
        # Get filename if not provided
        if not filename:
            filename = os.path.basename(file_path)
        
        # Read file
        logger.debug(f'Reading file from folder: {file_path}')
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        if not file_content:
            return {'success': False, 'error': f'File is empty: {file_path}'}
        
        # Create file-like object
        file = ContentFile(file_content, name=filename)
        
        # Upload using existing service
        logger.debug(f'Uploading file: {filename} ({len(file_content)} bytes)')
        result = rag_service.upload_document_enhanced(file, job.created_by)
        
        if result.get('success'):
            logger.info(f'Successfully uploaded folder file: {filename}')
            uploaded_file_id = result.get('data', {}).get('uploaded_file_id')
            
            # Check if this was a duplicate
            is_duplicate = result.get('data', {}).get('is_duplicate', False)
            if is_duplicate:
                logger.info(f'Folder file {filename} is a duplicate (ID: {uploaded_file_id}), skipping further processing')
                return {
                    'success': True,
                    'data': result.get('data'),
                    'uploaded_file_id': uploaded_file_id,
                    'filename': filename,
                    'is_duplicate': True,
                    'message': result.get('data', {}).get('message', 'Duplicate file - already exists')
                }
            
            return {
                'success': True,
                'data': result.get('data'),
                'uploaded_file_id': uploaded_file_id,
                'filename': filename
            }
        else:
            error_msg = result.get('message', 'Upload failed')
            logger.warning(f'Failed to upload folder file {filename}: {error_msg}')
            return {'success': False, 'error': error_msg}
            
    except FileNotFoundError as e:
        logger.error(f'File not found in _process_folder_file: {e}')
        return {'success': False, 'error': f'File not found: {str(e)}'}
    except PermissionError as e:
        logger.error(f'Permission denied in _process_folder_file: {e}')
        return {'success': False, 'error': f'Permission denied: {str(e)}'}
    except Exception as e:
        logger.error(f'Error in _process_folder_file: {e}', exc_info=True)
        return {'success': False, 'error': str(e)}


def _process_webpage_file(job: UploadJob, file_info: Dict[str, Any], rag_service: RAGService) -> Dict[str, Any]:
    """Process a file from webpage download"""
    try:
        file_url = file_info.get('url') or file_info.get('file_url')
        if not file_url:
            return {'success': False, 'error': 'No URL provided'}
        
        filename = file_info.get('name') or os.path.basename(file_url) or 'downloaded_file'
        
        logger.debug(f'Downloading file from URL: {file_url}')
        
        # Download file with streaming for large files
        response = requests.get(file_url, timeout=60, stream=True, allow_redirects=True)
        response.raise_for_status()
        
        # Get filename from Content-Disposition header if available
        content_disposition = response.headers.get('Content-Disposition', '')
        if content_disposition:
            import re
            fname_match = re.search(r'filename[^;=\n]*=(([\'"]).*?\2|[^\s;]+)', content_disposition)
            if fname_match:
                filename = fname_match.group(1).strip('\'"')
        
        # If still no filename, use URL basename
        if not filename or '.' not in filename:
            parsed_url = urlparse(file_url)
            filename = os.path.basename(parsed_url.path) or f"downloaded_file_{uuid.uuid4().hex[:8]}"
        
        # Read content
        file_content = response.content
        file_size = len(file_content)
        
        if file_size == 0:
            return {'success': False, 'error': 'Downloaded file is empty'}
        
        # Create file-like object
        file = ContentFile(file_content, name=filename)
        
        logger.debug(f'Uploading downloaded file: {filename} ({file_size} bytes)')
        
        # Upload using existing service
        result = rag_service.upload_document_enhanced(file, job.created_by)
        
        if result.get('success'):
            logger.info(f'Successfully downloaded and uploaded file from URL: {file_url}')
            uploaded_file_id = result.get('data', {}).get('uploaded_file_id')
            
            # Check if this was a duplicate
            is_duplicate = result.get('data', {}).get('is_duplicate', False)
            if is_duplicate:
                logger.info(f'Webpage file {filename} is a duplicate (ID: {uploaded_file_id}), skipping further processing')
                return {
                    'success': True,
                    'data': result.get('data'),
                    'uploaded_file_id': uploaded_file_id,
                    'filename': filename,
                    'is_duplicate': True,
                    'message': result.get('data', {}).get('message', 'Duplicate file - already exists')
                }
            
            return {
                'success': True,
                'data': result.get('data'),
                'uploaded_file_id': uploaded_file_id,
                'filename': filename
            }
        else:
            error_msg = result.get('message', 'Upload failed')
            logger.warning(f'Failed to upload downloaded file {filename}: {error_msg}')
            return {'success': False, 'error': error_msg}
            
    except requests.exceptions.RequestException as e:
        logger.error(f'Network error downloading file from {file_url}: {e}', exc_info=True)
        return {'success': False, 'error': f'Network error: {str(e)}'}
    except Exception as e:
        logger.error(f'Error in _process_webpage_file: {e}', exc_info=True)
        return {'success': False, 'error': str(e)}

