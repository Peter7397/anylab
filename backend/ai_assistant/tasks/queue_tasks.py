"""
Queue management Celery tasks.
"""

import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from ..models import UploadedFile, UploadJob
from ..service_classes.upload_queue_manager import upload_queue_manager

logger = logging.getLogger(__name__)


@shared_task(name='ai_assistant.tasks.monitor_queue_resources')
def monitor_queue_resources():
    """
    Periodic task to monitor system resources and pause/resume jobs accordingly
    
    Should be called every 60 seconds by Celery Beat
    """
    try:
        logger.debug('Monitoring queue resources')
        result = upload_queue_manager.pause_low_priority_jobs_if_needed()
        
        if result > 0:
            logger.info(f'Paused {result} low-priority jobs due to resource constraints')
        elif result < 0:
            logger.info(f'Resumed {abs(result)} low-priority jobs - resources OK')
        
        return {
            'status': 'success',
            'paused': result if result > 0 else 0,
            'resumed': abs(result) if result < 0 else 0
        }
    except Exception as e:
        logger.error(f'Error monitoring queue resources: {e}', exc_info=True)
        return {'status': 'error', 'message': str(e)}


@shared_task(name='ai_assistant.tasks.process_pending_files')
def process_pending_files():
    """
    Process any pending files in the queue
    
    SIMPLIFIED: Runs periodically (every 30 seconds) to process files that:
    1. Are stuck in pending state (fallback for signal failures)
    2. Were created but never queued (e.g., Celery was down)
    3. Need retry after system recovery
    
    This ensures NO files are left unprocessed.
    """
    try:
        cutoff = timezone.now() - timedelta(seconds=30)
        
        # Get files stuck in pending for more than 30 seconds
        pending_files = UploadedFile.objects.filter(
            processing_status='pending',
            uploaded_at__lt=cutoff
        ).order_by('uploaded_at')[:20]  # Process up to 20 files per run
        
        if pending_files.exists():
            logger.info(f'[Periodic Task] Processing {pending_files.count()} pending files (older than 1 minute)')
            
            from .file_processing_tasks import process_file_automatically
            
            for uploaded_file in pending_files:
                try:
                    # Queue processing task
                    process_file_automatically.delay(uploaded_file.id)
                    logger.debug(f'Queued processing for pending file: {uploaded_file.id} ({uploaded_file.filename})')
                except Exception as e:
                    logger.error(f'Error queuing pending file {uploaded_file.id}: {e}')
        
        return {
            'status': 'success',
            'processed': pending_files.count()
        }
    except Exception as e:
        logger.error(f'Error processing pending files: {e}', exc_info=True)
        return {'status': 'error', 'message': str(e)}


@shared_task(name='ai_assistant.tasks.cleanup_stuck_jobs')
def cleanup_stuck_jobs():
    """
    Cleanup jobs that have been stuck for too long
    
    Runs periodically to identify and fix stuck jobs
    """
    try:
        from datetime import timedelta
        cutoff = timezone.now() - timedelta(hours=24)
        
        # Find jobs stuck in processing/uploading for more than 24 hours
        stuck_jobs = UploadJob.objects.filter(
            status__in=['processing', 'uploading'],
            updated_at__lt=cutoff
        )
        
        cleaned_count = 0
        for job in stuck_jobs:
            try:
                logger.warning(f'Found stuck job {job.job_id}, resetting to queued')
                job.status = 'queued'
                job.save(update_fields=['status'])
                cleaned_count += 1
            except Exception as e:
                logger.error(f'Error cleaning up stuck job {job.job_id}: {e}')
        
        if cleaned_count > 0:
            logger.info(f'Cleaned up {cleaned_count} stuck jobs')
        
        return {
            'status': 'success',
            'cleaned': cleaned_count
        }
    except Exception as e:
        logger.error(f'Error cleaning up stuck jobs: {e}', exc_info=True)
        return {'status': 'error', 'message': str(e)}


@shared_task(name='ai_assistant.tasks.monitor_stuck_jobs')
def monitor_stuck_jobs():
    """
    Monitor and log stuck jobs for debugging
    
    Runs periodically to identify jobs that may be stuck
    """
    try:
        from datetime import timedelta
        cutoff = timezone.now() - timedelta(hours=2)
        
        # Find jobs that have been in processing/uploading for more than 2 hours
        potentially_stuck = UploadJob.objects.filter(
            status__in=['processing', 'uploading'],
            updated_at__lt=cutoff
        )
        
        if potentially_stuck.exists():
            logger.warning(f'Found {potentially_stuck.count()} potentially stuck jobs')
            for job in potentially_stuck:
                logger.warning(
                    f'Potentially stuck job {job.job_id}: status={job.status}, '
                    f'updated_at={job.updated_at}, completed={job.completed_items}/{job.total_items}'
                )
        
        return {
            'status': 'success',
            'potentially_stuck': potentially_stuck.count()
        }
    except Exception as e:
        logger.error(f'Error monitoring stuck jobs: {e}', exc_info=True)
        return {'status': 'error', 'message': str(e)}

