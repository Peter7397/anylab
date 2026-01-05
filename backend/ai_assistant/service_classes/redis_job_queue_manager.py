"""
Redis Job Queue Manager

Fast, non-blocking job queue using Redis Streams for upload job creation.
Jobs are persisted to PostgreSQL in the background for reliability.
"""

import logging
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
import redis
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class RedisJobQueueManager:
    """Manages upload job queue using Redis for fast, non-blocking job creation"""
    
    # Redis key prefixes
    QUEUE_KEY_PREFIX = 'upload_job_queue'
    JOB_STATUS_KEY_PREFIX = 'upload_job'
    ACTIVE_JOBS_KEY = 'upload_jobs:active'
    PENDING_PERSIST_KEY = 'upload_jobs:pending_persist'
    
    # Priority queue names
    PRIORITY_QUEUES = {
        'high': 'high',      # Priority 8-10
        'normal': 'normal',  # Priority 4-7
        'low': 'low'        # Priority 1-3
    }
    
    # TTL for job status cache (7 days)
    JOB_STATUS_TTL = 7 * 24 * 60 * 60  # 7 days in seconds
    
    def __init__(self):
        """Initialize Redis connection"""
        try:
            # Get Redis connection from django-redis
            # Use get_redis_connection which is the recommended method
            from django_redis import get_redis_connection
            self.redis_client = get_redis_connection("default")
            self._test_connection()
            logger.info("RedisJobQueueManager initialized successfully")
        except ImportError:
            # Fallback: try using cache client
            try:
                cache_client = cache.get_client(None)
                self.redis_client = cache_client.get_client(write=True)
                self._test_connection()
                logger.info("RedisJobQueueManager initialized using cache client")
            except Exception as e:
                logger.error(f"Failed to initialize Redis connection: {e}", exc_info=True)
                self.redis_client = None
        except Exception as e:
            logger.error(f"Failed to initialize Redis connection: {e}", exc_info=True)
            self.redis_client = None
    
    def _test_connection(self):
        """Test Redis connection"""
        if self.redis_client:
            self.redis_client.ping()
    
    def _get_priority_queue_name(self, priority: int) -> str:
        """Get queue name based on priority"""
        if priority >= 8:
            return f"{self.QUEUE_KEY_PREFIX}:{self.PRIORITY_QUEUES['high']}"
        elif priority >= 4:
            return f"{self.QUEUE_KEY_PREFIX}:{self.PRIORITY_QUEUES['normal']}"
        else:
            return f"{self.QUEUE_KEY_PREFIX}:{self.PRIORITY_QUEUES['low']}"
    
    def _get_job_status_key(self, job_id: str) -> str:
        """Get Redis key for job status"""
        return f"{self.JOB_STATUS_KEY_PREFIX}:{job_id}"
    
    def add_job_fast(
        self,
        job_id: str,
        job_type: str,
        source_path: str,
        source_files: List[Dict[str, Any]],
        priority: int,
        metadata: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Add job to Redis queue immediately (non-blocking, <5ms)
        
        Args:
            job_id: UUID string
            job_type: 'file', 'folder', or 'webpage'
            source_path: File path, folder path, or URL
            source_files: List of files to process
            priority: Priority 1-10
            metadata: Job metadata dict
            user_id: User ID who created the job
            
        Returns:
            Dict with job_id and status
        """
        if not self.redis_client:
            raise Exception("Redis client not available")
        
        try:
            # Prepare job data
            job_data = {
                'job_id': job_id,
                'job_type': job_type,
                'source_path': source_path,
                'source_files': json.dumps(source_files),  # Serialize list
                'metadata': json.dumps(metadata),  # Serialize dict
                'priority': str(priority),
                'user_id': str(user_id) if user_id else '',
                'created_at': timezone.now().isoformat(),
                'status': 'queued',
                'total_items': str(len(source_files)),
                'completed_items': '0',
                'failed_items': '0'
            }
            
            # Get priority queue name
            queue_name = self._get_priority_queue_name(priority)
            
            # Add to Redis Stream (ordered queue)
            stream_id = self.redis_client.xadd(
                queue_name,
                job_data,
                maxlen=10000  # Keep last 10,000 jobs per priority
            )
            
            # Store full job data in Redis Hash for fast lookup and persistence
            status_key = self._get_job_status_key(job_id)
            status_data = {
                'job_id': job_id,
                'job_type': job_type,
                'status': 'queued',
                'priority': str(priority),
                'total_items': str(len(source_files)),
                'completed_items': '0',
                'failed_items': '0',
                'created_at': timezone.now().isoformat(),
                'updated_at': timezone.now().isoformat(),
                'source_path': source_path[:200],  # Truncate for storage
                # Store full data for persistence (will be used by persistence worker)
                'source_files': json.dumps(source_files),
                'metadata': json.dumps(metadata),
                'user_id': str(user_id) if user_id else '',
                'stream_id': stream_id.decode() if isinstance(stream_id, bytes) else stream_id,
                'queue_name': queue_name
            }
            self.redis_client.hset(status_key, mapping=status_data)
            self.redis_client.expire(status_key, self.JOB_STATUS_TTL)
            
            # Add to active jobs set
            self.redis_client.sadd(self.ACTIVE_JOBS_KEY, job_id)
            
            # Add to pending persist list (for background worker)
            persist_data = {
                'job_id': job_id,
                'stream_id': stream_id.decode() if isinstance(stream_id, bytes) else stream_id,
                'queue_name': queue_name,
                'created_at': timezone.now().isoformat()
            }
            self.redis_client.lpush(
                self.PENDING_PERSIST_KEY,
                json.dumps(persist_data)
            )
            
            logger.info(f"Job {job_id} added to Redis queue: {queue_name} (priority: {priority})")
            
            return {
                'job_id': job_id,
                'status': 'queued',
                'queue_name': queue_name,
                'stream_id': stream_id.decode() if isinstance(stream_id, bytes) else stream_id
            }
            
        except Exception as e:
            logger.error(f"Failed to add job {job_id} to Redis: {e}", exc_info=True)
            raise
    
    def get_job_from_redis(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job data from Redis (fast lookup)
        
        Args:
            job_id: Job UUID
            
        Returns:
            Job data dict or None if not found
        """
        if not self.redis_client:
            return None
        
        try:
            status_key = self._get_job_status_key(job_id)
            status_data = self.redis_client.hgetall(status_key)
            
            if not status_data:
                return None
            
            # Decode bytes to strings
            job_data = {k.decode() if isinstance(k, bytes) else k: 
                       v.decode() if isinstance(v, bytes) else v 
                       for k, v in status_data.items()}
            
            return job_data
            
        except Exception as e:
            logger.warning(f"Error getting job {job_id} from Redis: {e}")
            return None
    
    def update_job_status(
        self,
        job_id: str,
        status: str = None,
        completed_items: int = None,
        failed_items: int = None,
        error_message: str = None
    ) -> bool:
        """
        Update job status in Redis cache (Phase 4: Auto-remove when completed)
        
        Args:
            job_id: Job UUID
            status: New status (optional)
            completed_items: Number of completed items (optional)
            failed_items: Number of failed items (optional)
            error_message: Error message (optional)
            
        Returns:
            True if updated, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            # If job is completed, remove from Redis (Phase 4: Redis for active jobs only)
            if status == 'completed':
                self.remove_job_from_redis(job_id)
                return True
            
            status_key = self._get_job_status_key(job_id)
            
            updates = {}
            if status:
                updates['status'] = status
            if completed_items is not None:
                updates['completed_items'] = str(completed_items)
            if failed_items is not None:
                updates['failed_items'] = str(failed_items)
            if error_message:
                updates['error_message'] = error_message[:500]  # Truncate
            
            updates['updated_at'] = timezone.now().isoformat()
            
            if updates:
                self.redis_client.hset(status_key, mapping=updates)
                # Refresh TTL
                self.redis_client.expire(status_key, self.JOB_STATUS_TTL)
            
            return True
            
        except Exception as e:
            logger.warning(f"Error updating job {job_id} status in Redis: {e}")
            return False
    
    def get_next_job_from_queue(self, priority: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get next job from Redis queue (for processing)
        
        Args:
            priority: 'high', 'normal', or 'low' (optional, checks all if None)
            
        Returns:
            Job data dict or None if no jobs available
        """
        if not self.redis_client:
            return None
        
        try:
            # Determine which queues to check
            if priority:
                queue_names = [f"{self.QUEUE_KEY_PREFIX}:{priority}"]
            else:
                # Check in priority order: high -> normal -> low
                queue_names = [
                    f"{self.QUEUE_KEY_PREFIX}:{self.PRIORITY_QUEUES['high']}",
                    f"{self.QUEUE_KEY_PREFIX}:{self.PRIORITY_QUEUES['normal']}",
                    f"{self.QUEUE_KEY_PREFIX}:{self.PRIORITY_QUEUES['low']}"
                ]
            
            # Try to read from each queue (non-blocking)
            for queue_name in queue_names:
                # Read one entry from stream (non-blocking)
                messages = self.redis_client.xread(
                    {queue_name: '0'},  # Start from beginning
                    count=1,
                    block=0  # Non-blocking
                )
                
                if messages:
                    stream_name, entries = messages[0]
                    if entries:
                        stream_id, job_data = entries[0]
                        
                        # Decode bytes to strings
                        decoded_data = {
                            k.decode() if isinstance(k, bytes) else k:
                            v.decode() if isinstance(v, bytes) else v
                            for k, v in job_data.items()
                        }
                        
                        # Deserialize JSON fields
                        if 'source_files' in decoded_data:
                            decoded_data['source_files'] = json.loads(decoded_data['source_files'])
                        if 'metadata' in decoded_data:
                            decoded_data['metadata'] = json.loads(decoded_data['metadata'])
                        
                        decoded_data['stream_id'] = stream_id.decode() if isinstance(stream_id, bytes) else stream_id
                        decoded_data['queue_name'] = queue_name.decode() if isinstance(queue_name, bytes) else queue_name
                        
                        return decoded_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting next job from Redis queue: {e}", exc_info=True)
            return None
    
    def remove_job_from_queue(self, queue_name: str, stream_id: str) -> bool:
        """
        Remove job from Redis queue (after processing)
        
        Args:
            queue_name: Queue name
            stream_id: Stream entry ID
            
        Returns:
            True if removed, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            # Delete the stream entry
            deleted = self.redis_client.xdel(queue_name, stream_id)
            return deleted > 0
            
        except Exception as e:
            logger.warning(f"Error removing job from queue {queue_name}: {e}")
            return False
    
    def get_pending_persist_jobs(self, count: int = 50) -> List[Dict[str, Any]]:
        """
        Get jobs pending persistence to PostgreSQL
        
        Args:
            count: Maximum number of jobs to retrieve
            
        Returns:
            List of job data dicts
        """
        if not self.redis_client:
            return []
        
        try:
            # Get jobs from pending persist list
            jobs_data = []
            for _ in range(count):
                job_json = self.redis_client.rpop(self.PENDING_PERSIST_KEY)
                if not job_json:
                    break
                
                try:
                    job_data = json.loads(job_json.decode() if isinstance(job_json, bytes) else job_json)
                    jobs_data.append(job_data)
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON in pending persist list: {e}")
                    continue
            
            return jobs_data
            
        except Exception as e:
            logger.error(f"Error getting pending persist jobs: {e}", exc_info=True)
            return []
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get queue statistics from Redis
        
        Returns:
            Dict with queue statistics
        """
        if not self.redis_client:
            return {
                'total_queued': 0,
                'by_priority': {'high': 0, 'normal': 0, 'low': 0},
                'active_jobs': 0,
                'pending_persist': 0
            }
        
        try:
            stats = {
                'total_queued': 0,
                'by_priority': {},
                'active_jobs': 0,
                'pending_persist': 0
            }
            
            # Count jobs in each priority queue
            for priority_name in self.PRIORITY_QUEUES.values():
                queue_name = f"{self.QUEUE_KEY_PREFIX}:{priority_name}"
                queue_length = self.redis_client.xlen(queue_name)
                stats['by_priority'][priority_name] = queue_length
                stats['total_queued'] += queue_length
            
            # Count active jobs
            stats['active_jobs'] = self.redis_client.scard(self.ACTIVE_JOBS_KEY)
            
            # Count pending persist
            stats['pending_persist'] = self.redis_client.llen(self.PENDING_PERSIST_KEY)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting queue stats from Redis: {e}", exc_info=True)
            return {
                'total_queued': 0,
                'by_priority': {'high': 0, 'normal': 0, 'low': 0},
                'active_jobs': 0,
                'pending_persist': 0
            }
    
    def remove_job_from_redis(self, job_id: str) -> bool:
        """
        Remove completed job from Redis (Phase 4: Redis for active jobs only)
        
        Args:
            job_id: Job UUID
            
        Returns:
            True if removed, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            # Remove from active jobs set
            self.redis_client.srem(self.ACTIVE_JOBS_KEY, job_id)
            
            # Remove job status hash (optional - can keep for history with shorter TTL)
            status_key = self._get_job_status_key(job_id)
            self.redis_client.delete(status_key)
            
            logger.info(f"Removed completed job {job_id} from Redis")
            return True
            
        except Exception as e:
            logger.warning(f"Error removing job {job_id} from Redis: {e}")
            return False
    
    def get_active_jobs(self) -> List[str]:
        """
        Get list of active job IDs from Redis (Phase 4: Redis for active jobs only)
        
        Returns:
            List of job_id strings
        """
        if not self.redis_client:
            return []
        
        try:
            # Get all active job IDs from set
            job_ids = self.redis_client.smembers(self.ACTIVE_JOBS_KEY)
            # Decode bytes to strings
            return [jid.decode() if isinstance(jid, bytes) else jid for jid in job_ids]
            
        except Exception as e:
            logger.warning(f"Error getting active jobs from Redis: {e}")
            return []
    
    def is_available(self) -> bool:
        """Check if Redis is available"""
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.ping()
            return True
        except Exception:
            return False


# Singleton instance
redis_job_queue_manager = RedisJobQueueManager()

