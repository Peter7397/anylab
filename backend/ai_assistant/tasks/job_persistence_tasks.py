"""
Job Persistence Tasks

Background tasks for persisting Redis job queue entries to PostgreSQL.
Ensures data durability while maintaining fast job creation via Redis.
"""

import logging
import json
from typing import Dict, Any, List
from django.utils import timezone
from django.db import transaction
from celery import shared_task
from ..models import UploadJob
from ..service_classes.redis_job_queue_manager import redis_job_queue_manager
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task(name='ai_assistant.tasks.persist_jobs_to_database', bind=True)
def persist_jobs_to_database(self, batch_size: int = 50) -> Dict[str, Any]:
    """
    Persist jobs from Redis queue to PostgreSQL database
    
    This task runs periodically (via Celery Beat) to batch-write jobs
    from Redis to PostgreSQL for persistence and querying.
    
    Args:
        batch_size: Maximum number of jobs to process per run
        
    Returns:
        Dict with processing statistics
    """
    if not redis_job_queue_manager or not redis_job_queue_manager.is_available():
        logger.debug("Redis job queue manager not available, skipping persistence")
        return {
            'status': 'skipped',
            'reason': 'redis_unavailable',
            'processed': 0
        }
    
    try:
        # Get pending jobs from Redis
        pending_jobs = redis_job_queue_manager.get_pending_persist_jobs(count=batch_size)
        
        if not pending_jobs:
            return {
                'status': 'success',
                'processed': 0,
                'message': 'No pending jobs to persist'
            }
        
        logger.info(f"Persisting {len(pending_jobs)} jobs from Redis to PostgreSQL")
        
        processed = 0
        failed = 0
        skipped = 0
        
        # Process jobs in batches for efficiency
        with transaction.atomic():
            for job_info in pending_jobs:
                try:
                    job_id = job_info.get('job_id')
                    queue_name = job_info.get('queue_name')
                    stream_id = job_info.get('stream_id')
                    
                    if not job_id:
                        logger.warning(f"Invalid job info (missing job_id): {job_info}")
                        failed += 1
                        continue
                    
                    # Check if job already exists in PostgreSQL
                    existing_job = UploadJob.objects.filter(job_id=job_id).first()
                    if existing_job:
                        # Phase 4: Skip completed jobs (they should be removed from Redis)
                        if existing_job.status == 'completed':
                            logger.debug(f"Job {job_id} is completed, skipping persistence and removing from Redis")
                            # Remove from Redis if it's still there
                            if redis_job_queue_manager and redis_job_queue_manager.is_available():
                                redis_job_queue_manager.remove_job_from_redis(job_id)
                            skipped += 1
                            continue
                        else:
                            logger.debug(f"Job {job_id} already exists in PostgreSQL, skipping")
                            skipped += 1
                            continue
                    
                    # Get job data from Redis Hash (more reliable than stream)
                    # The hash contains all job data needed for persistence
                    job_data = redis_job_queue_manager.get_job_from_redis(job_id)
                    
                    if not job_data:
                        # Fallback: try to read from stream
                        job_data = _get_job_data_from_redis_stream(queue_name, stream_id)
                    
                    if not job_data:
                        logger.warning(f"Could not retrieve job data for {job_id} from Redis")
                        failed += 1
                        continue
                    
                    # Deserialize JSON fields (from hash or stream)
                    source_files = json.loads(job_data.get('source_files', '[]'))
                    metadata = json.loads(job_data.get('metadata', '{}'))
                    user_id = job_data.get('user_id', '')
                    
                    # Get user if user_id provided
                    user = None
                    if user_id:
                        try:
                            user = User.objects.get(id=int(user_id))
                        except (User.DoesNotExist, ValueError):
                            logger.warning(f"User {user_id} not found for job {job_id}")
                    
                    # Create UploadJob in PostgreSQL
                    job = UploadJob.objects.create(
                        job_id=job_id,
                        job_type=job_data.get('job_type', 'file'),
                        source_path=job_data.get('source_path', ''),
                        source_files=source_files,
                        priority=int(job_data.get('priority', 5)),
                        total_items=int(job_data.get('total_items', len(source_files))),
                        metadata=metadata,
                        created_by=user,
                        status='queued'
                    )
                    
                    processed += 1
                    logger.debug(f"Persisted job {job_id} to PostgreSQL")
                    
                except Exception as e:
                    logger.error(f"Error persisting job {job_info.get('job_id', 'unknown')}: {e}", exc_info=True)
                    failed += 1
                    # Put job back in pending list for retry
                    try:
                        redis_job_queue_manager.redis_client.lpush(
                            redis_job_queue_manager.PENDING_PERSIST_KEY,
                            json.dumps(job_info)
                        )
                    except Exception as retry_error:
                        logger.error(f"Failed to requeue job for retry: {retry_error}")
        
        result = {
            'status': 'success',
            'processed': processed,
            'failed': failed,
            'skipped': skipped,
            'total': len(pending_jobs)
        }
        
        logger.info(
            f"Job persistence completed: {processed} persisted, "
            f"{failed} failed, {skipped} skipped"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in persist_jobs_to_database task: {e}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e),
            'processed': 0
        }


def _get_job_data_from_redis_stream(queue_name: str, stream_id: str) -> Dict[str, Any]:
    """
    Get job data from Redis stream entry
    
    Args:
        queue_name: Redis stream key
        stream_id: Stream entry ID
        
    Returns:
        Job data dict or None if not found
    """
    if not redis_job_queue_manager or not redis_job_queue_manager.is_available():
        return None
    
    try:
        # Read specific entry from stream
        messages = redis_job_queue_manager.redis_client.xrange(
            queue_name,
            min=stream_id,
            max=stream_id,
            count=1
        )
        
        if messages:
            _, job_data = messages[0]
            # Decode bytes to strings
            decoded_data = {
                k.decode() if isinstance(k, bytes) else k:
                v.decode() if isinstance(v, bytes) else v
                for k, v in job_data.items()
            }
            return decoded_data
        
        return None
        
    except Exception as e:
        logger.error(f"Error reading job data from Redis stream: {e}", exc_info=True)
        return None


@shared_task(name='ai_assistant.tasks.sync_redis_job_status')
def sync_redis_job_status(job_id: str) -> Dict[str, Any]:
    """
    Sync job status from Redis to PostgreSQL
    
    Called when job status changes to keep PostgreSQL in sync with Redis cache.
    
    Args:
        job_id: Job UUID
        
    Returns:
        Dict with sync status
    """
    try:
        # Get job from PostgreSQL
        try:
            job = UploadJob.objects.get(job_id=job_id)
        except UploadJob.DoesNotExist:
            logger.debug(f"Job {job_id} not found in PostgreSQL, may not be persisted yet")
            return {'status': 'not_found', 'job_id': job_id}
        
        # Get status from Redis
        if redis_job_queue_manager and redis_job_queue_manager.is_available():
            redis_job = redis_job_queue_manager.get_job_from_redis(job_id)
            
            if redis_job:
                # Update PostgreSQL with Redis data
                if 'status' in redis_job:
                    job.status = redis_job['status']
                if 'completed_items' in redis_job:
                    try:
                        job.completed_items = int(redis_job['completed_items'])
                    except (ValueError, TypeError):
                        pass
                if 'failed_items' in redis_job:
                    try:
                        job.failed_items = int(redis_job['failed_items'])
                    except (ValueError, TypeError):
                        pass
                if 'error_message' in redis_job:
                    job.error_message = redis_job['error_message']
                
                job.save()
                logger.debug(f"Synced job {job_id} status from Redis to PostgreSQL")
                return {'status': 'synced', 'job_id': job_id}
        
        return {'status': 'no_redis_data', 'job_id': job_id}
        
    except Exception as e:
        logger.error(f"Error syncing job {job_id} status: {e}", exc_info=True)
        return {'status': 'error', 'error': str(e), 'job_id': job_id}

