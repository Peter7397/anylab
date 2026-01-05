"""
Upload Queue Manager

Manages unified upload queue for all upload types (file, folder, webpage)
with priority scheduling, pause/resume, and workload balancing.

ENHANCED: Now uses Redis for fast, non-blocking job creation while maintaining
PostgreSQL for persistence and querying.
"""

import logging
import psutil
import threading
import requests
import re
import os
import uuid
import json
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse
from django.db import transaction
from django.utils import timezone
from django.db.models import Q, F
from datetime import timedelta
from bs4 import BeautifulSoup
from ..models import UploadJob

# Import Redis job queue manager
try:
    from .redis_job_queue_manager import redis_job_queue_manager
    REDIS_AVAILABLE = True
except Exception as e:
    logging.warning(f"Redis job queue manager not available: {e}")
    REDIS_AVAILABLE = False
    redis_job_queue_manager = None

logger = logging.getLogger(__name__)


class UploadQueueManager:
    """Manages upload queue with priority scheduling and control"""
    
    def __init__(self):
        self.max_concurrent_jobs = 3  # Maximum concurrent jobs
        self.max_files_per_job = 5  # Maximum concurrent files per job
        self.resource_check_interval = 60  # Check resources every 60 seconds
        self.cpu_threshold = 80.0  # Pause low-priority jobs if CPU > 80%
        self.memory_threshold = 90.0  # Pause low-priority jobs if memory > 90% (increased for OCR workloads)
        self._last_resource_check = None
        self._resource_check_lock = threading.Lock()
        self._last_job_type_processed = None  # For fair scheduling
        
        # File size thresholds for routing (in bytes)
        self.SMALL_FILE_THRESHOLD = 1 * 1024 * 1024  # 1MB
        self.MEDIUM_FILE_THRESHOLD = 10 * 1024 * 1024  # 10MB
        self.LARGE_FILE_THRESHOLD = 100 * 1024 * 1024  # 100MB
        
        # Adaptive concurrency settings
        self.SMALL_FILE_CONCURRENCY = 20
        self.MEDIUM_FILE_CONCURRENCY = 10
        self.LARGE_FILE_CONCURRENCY = 3
        self.VERY_LARGE_FILE_CONCURRENCY = 1
    
    def _analyze_file_size(self, file_info: Dict[str, Any]) -> str:
        """
        Analyze file size and return category
        
        Returns:
            'small', 'medium', 'large', or 'very_large'
        """
        size = file_info.get('size', 0)
        if size < self.SMALL_FILE_THRESHOLD:
            return 'small'
        elif size < self.MEDIUM_FILE_THRESHOLD:
            return 'medium'
        elif size < self.LARGE_FILE_THRESHOLD:
            return 'large'
        else:
            return 'very_large'
    
    def _calculate_file_priority(self, file_info: Dict[str, Any]) -> int:
        """
        Calculate priority for a file based on size
        Smaller files get higher priority for faster user feedback
        
        Returns:
            Priority value (1-10, higher = more important)
        """
        size_category = self._analyze_file_size(file_info)
        if size_category == 'small':
            return 10
        elif size_category == 'medium':
            return 7
        elif size_category == 'large':
            return 5
        else:
            return 3
    
    def _determine_queue_name(self, file_info: Dict[str, Any]) -> str:
        """
        Determine which Celery queue should process this file
        
        Returns:
            Queue name: 'fast_queue', 'normal_queue', 'slow_queue', or 'ocr_queue'
        """
        size_category = self._analyze_file_size(file_info)
        file_type = file_info.get('type', '').lower()
        
        # Check if file needs OCR (scanned PDF, image, etc.)
        needs_ocr = (
            'image' in file_type or
            file_type == 'application/pdf' or  # Will be determined during processing
            file_info.get('needs_ocr', False)
        )
        
        if needs_ocr:
            return 'ocr_queue'
        elif size_category == 'small':
            return 'fast_queue'
        elif size_category == 'medium':
            return 'normal_queue'
        else:
            return 'slow_queue'
    
    def _calculate_adaptive_concurrency(self, file_info: Dict[str, Any]) -> int:
        """
        Calculate adaptive concurrency for a file based on size
        
        Returns:
            Number of concurrent workers to use
        """
        size_category = self._analyze_file_size(file_info)
        if size_category == 'small':
            return self.SMALL_FILE_CONCURRENCY
        elif size_category == 'medium':
            return self.MEDIUM_FILE_CONCURRENCY
        elif size_category == 'large':
            return self.LARGE_FILE_CONCURRENCY
        else:
            return self.VERY_LARGE_FILE_CONCURRENCY
    
    def add_job(
        self,
        job_type: str,
        source_path: str,
        source_files: List[Dict[str, Any]],
        priority: int = 5,
        metadata: Optional[Dict[str, Any]] = None,
        user=None,
        use_redis: bool = True
    ) -> UploadJob:
        """
        Add new job to upload queue
        
        ENHANCED: Uses Redis for fast, non-blocking job creation if available.
        Falls back to direct PostgreSQL write if Redis is unavailable.
        
        Args:
            job_type: 'file', 'folder', or 'webpage'
            source_path: File path, folder path, or URL
            source_files: List of files to process
            priority: Priority 1-10 (default 5)
            metadata: Optional metadata dict
            user: User who created the job
            use_redis: Whether to use Redis for fast job creation (default: True)
            
        Returns:
            UploadJob instance (may be a temporary object if using Redis)
        """
        try:
            # Validate priority
            priority = max(1, min(10, priority))
            
            # Analyze files and add metadata
            for file_info in source_files:
                # Add file size category
                file_info['size_category'] = self._analyze_file_size(file_info)
                # Add calculated priority
                file_info['calculated_priority'] = self._calculate_file_priority(file_info)
                # Add queue routing info
                file_info['target_queue'] = self._determine_queue_name(file_info)
                # Add adaptive concurrency
                file_info['suggested_concurrency'] = self._calculate_adaptive_concurrency(file_info)
            
            # Calculate job priority based on file priorities (use highest file priority)
            if source_files:
                max_file_priority = max(f.get('calculated_priority', 5) for f in source_files)
                # Use the higher of user-provided priority or max file priority
                effective_priority = max(priority, max_file_priority)
            else:
                effective_priority = priority
            
            # Generate job_id upfront
            job_id = str(uuid.uuid4())
            
            # Try Redis first for fast job creation
            if use_redis and REDIS_AVAILABLE and redis_job_queue_manager and redis_job_queue_manager.is_available():
                try:
                    # Add to Redis queue immediately (<5ms)
                    redis_result = redis_job_queue_manager.add_job_fast(
                        job_id=job_id,
                        job_type=job_type,
                        source_path=source_path,
                        source_files=source_files,
                        priority=effective_priority,
                        metadata=metadata or {},
                        user_id=user.id if user else None
                    )
                    
                    logger.info(
                        f"Job {job_id} added to Redis queue - type: {job_type}, "
                        f"items: {len(source_files)}, priority: {effective_priority}"
                    )
                    
                    # Create a temporary UploadJob object for return (not saved to DB yet)
                    # Background worker will persist it to PostgreSQL
                    job = UploadJob(
                        job_id=uuid.UUID(job_id),
                        job_type=job_type,
                        source_path=source_path,
                        source_files=source_files,
                        priority=effective_priority,
                        total_items=len(source_files),
                        metadata=metadata or {},
                        created_by=user,
                        status='queued'
                    )
                    # Mark as not saved (for compatibility)
                    job._state = {'add': True, 'db': None}
                    
                    return job
                    
                except Exception as redis_error:
                    logger.warning(
                        f"Redis job creation failed, falling back to PostgreSQL: {redis_error}"
                    )
                    # Fall through to PostgreSQL write
            
            # Fallback: Direct PostgreSQL write (original behavior)
            job = UploadJob.objects.create(
                job_id=uuid.UUID(job_id),
                job_type=job_type,
                source_path=source_path,
                source_files=source_files,
                priority=effective_priority,
                total_items=len(source_files),
                metadata=metadata or {},
                created_by=user,
                status='queued'
            )
            
            logger.info(
                f"Created upload job {job.job_id} in PostgreSQL - type: {job_type}, "
                f"items: {len(source_files)}, priority: {effective_priority}"
            )
            
            return job
            
        except Exception as e:
            logger.error(f"Failed to create upload job: {e}", exc_info=True)
            raise
    
    def get_job(self, job_id: str) -> Optional[UploadJob]:
        """
        Get job by job_id
        
        ENHANCED: Checks Redis cache first, then falls back to PostgreSQL
        """
        try:
            # Try Redis first (fast lookup)
            if REDIS_AVAILABLE and redis_job_queue_manager and redis_job_queue_manager.is_available():
                redis_job = redis_job_queue_manager.get_job_from_redis(job_id)
                if redis_job:
                    # Try to get from PostgreSQL (may not exist yet if not persisted)
                    try:
                        db_job = UploadJob.objects.get(job_id=job_id)
                        return db_job
                    except UploadJob.DoesNotExist:
                        # Job exists in Redis but not yet in DB - return None
                        # Caller should handle this case
                        logger.debug(f"Job {job_id} found in Redis but not yet in PostgreSQL")
                        return None
            
            # Fallback to PostgreSQL
            return UploadJob.objects.get(job_id=job_id)
            
        except UploadJob.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error getting job {job_id}: {e}", exc_info=True)
            return None
    
    def get_queue_status(self, user=None, status_filter=None, active_only: bool = False) -> Dict[str, Any]:
        """
        Get queue status with all jobs
        
        ENHANCED: Combines Redis and PostgreSQL data for comprehensive status
        
        Args:
            user: Filter by user (optional)
            status_filter: Filter by status (optional)
            active_only: If True, exclude completed jobs (default: False for backward compatibility)
            
        Returns:
            Dict with queue statistics and job list
        """
        # Phase 4: Query active jobs from Redis, completed from PostgreSQL
        serialized_jobs = []
        stats = {
            'total': 0,
            'queued': 0,
            'uploading': 0,
            'processing': 0,
            'paused': 0,
            'completed': 0,
            'failed': 0,
            'cancelled': 0,
            'by_type': {
                'file': 0,
                'folder': 0,
                'webpage': 0,
            }
        }
        
        # Step 1: Get active jobs from Redis (Phase 4)
        active_job_ids = []
        if REDIS_AVAILABLE and redis_job_queue_manager and redis_job_queue_manager.is_available():
            try:
                active_job_ids = redis_job_queue_manager.get_active_jobs()
                redis_stats = redis_job_queue_manager.get_queue_stats()
                stats['redis'] = {
                    'total_queued': redis_stats.get('total_queued', 0),
                    'by_priority': redis_stats.get('by_priority', {}),
                    'active_jobs': redis_stats.get('active_jobs', 0),
                    'pending_persist': redis_stats.get('pending_persist', 0)
                }
            except Exception as e:
                logger.warning(f"Error getting active jobs from Redis: {e}")
        
        # Step 2: Query active jobs from PostgreSQL
        # Filter out cancelled, completed, and jobs with all files skipped
        if active_job_ids:
            active_queryset = UploadJob.objects.filter(
                job_id__in=active_job_ids
            ).exclude(
                cancelled=True  # Exclude cancelled jobs
            ).exclude(
                status='completed'  # Exclude completed jobs
            )
            
            if user:
                active_queryset = active_queryset.filter(created_by=user)
            
            if status_filter:
                active_queryset = active_queryset.filter(status=status_filter)
            
            # Additional filter: Exclude jobs where all files are skipped (duplicates)
            # These should be marked as completed but check anyway
            active_jobs_list = []
            for job in active_queryset.order_by('-created_at', '-priority'):
                source_files = job.source_files or []
                if source_files:
                    # Check if all files are skipped
                    all_skipped = all(
                        f.get('upload_status') == 'skipped' or f.get('processing_status') == 'skipped'
                        for f in source_files
                    )
                    if all_skipped:
                        # All files skipped - mark as completed and skip
                        job.status = 'completed'
                        if not job.completed_at:
                            job.completed_at = timezone.now()
                        job.save(update_fields=['status', 'completed_at'])
                        # Remove from Redis
                        try:
                            if REDIS_AVAILABLE and redis_job_queue_manager and redis_job_queue_manager.is_available():
                                redis_job_queue_manager.remove_job_from_redis(str(job.job_id))
                                logger.info(f'Job {job.job_id} marked as completed (all files skipped) and removed from Redis')
                        except Exception as e:
                            logger.warning(f'Error removing all-skipped job from Redis: {e}')
                        continue
                active_jobs_list.append(job)
            
            active_jobs = active_jobs_list
            
            for job in active_jobs:
                serialized_jobs.append(self._serialize_job(job))
                
                # Update stats
                stats['total'] += 1
                if job.status == 'queued':
                    stats['queued'] += 1
                elif job.status == 'uploading':
                    stats['uploading'] += 1
                elif job.status == 'processing':
                    stats['processing'] += 1
                if job.paused:
                    stats['paused'] += 1
                if job.cancelled:
                    stats['cancelled'] += 1
                stats['by_type'][job.job_type] += 1
        
        # Step 3: Query completed jobs from PostgreSQL (if not active_only)
        if not active_only:
            completed_queryset = UploadJob.objects.filter(status='completed')
            
            if user:
                completed_queryset = completed_queryset.filter(created_by=user)
            
            if status_filter == 'completed':
                # Only return completed jobs
                pass
            elif status_filter:
                # Other status filters don't apply to completed jobs
                completed_queryset = completed_queryset.none()
            
            # Limit completed jobs to recent ones (last 100)
            completed_jobs = completed_queryset.order_by('-created_at')[:100]
            
            for job in completed_jobs:
                serialized_jobs.append(self._serialize_job(job))
                
                # Update stats
                stats['total'] += 1
                stats['completed'] += 1
                if job.failed_items > 0:
                    stats['failed'] += 1
                stats['by_type'][job.job_type] += 1
        else:
            # active_only=True: Only include completed jobs with failures
            failed_queryset = UploadJob.objects.filter(status='completed', failed_items__gt=0)
            if user:
                failed_queryset = failed_queryset.filter(created_by=user)
            
            failed_jobs = failed_queryset.order_by('-created_at')[:50]  # Limit to 50
            
            for job in failed_jobs:
                serialized_jobs.append(self._serialize_job(job))
                stats['total'] += 1
                stats['completed'] += 1
                stats['failed'] += 1
                stats['by_type'][job.job_type] += 1
        
        # Step 4: Include Redis-only jobs (not yet persisted to PostgreSQL)
        if REDIS_AVAILABLE and redis_job_queue_manager and redis_job_queue_manager.is_available():
            try:
                job_ids_in_db = {job.job_id for job in serialized_jobs if hasattr(job, 'job_id')}
                job_ids_in_db.update([j.get('job_id') for j in serialized_jobs if isinstance(j, dict) and 'job_id' in j])
                
                for job_id in active_job_ids:
                    if job_id in job_ids_in_db:
                        continue
                    
                    # Get job data from Redis
                    redis_job = redis_job_queue_manager.get_job_from_redis(job_id)
                    if redis_job:
                        redis_status = redis_job.get('status', 'queued')
                        if redis_status not in ['completed']:  # Only active jobs
                            try:
                                from django.contrib.auth import get_user_model
                                User = get_user_model()
                                user_id = redis_job.get('user_id', '')
                                user = User.objects.get(id=int(user_id)) if user_id and user_id.isdigit() else None
                                
                                import json
                                source_files = json.loads(redis_job.get('source_files', '[]'))
                                metadata = json.loads(redis_job.get('metadata', '{}'))
                                
                                redis_job_dict = {
                                    'job_id': job_id,
                                    'job_type': redis_job.get('job_type', 'file'),
                                    'source_path': redis_job.get('source_path', ''),
                                    'source_files': source_files,
                                    'priority': int(redis_job.get('priority', 5)),
                                    'total_items': int(redis_job.get('total_items', 0)),
                                    'completed_items': int(redis_job.get('completed_items', 0)),
                                    'failed_items': int(redis_job.get('failed_items', 0)),
                                    'status': redis_status,
                                    'paused': redis_job.get('paused', 'False').lower() == 'true',
                                    'cancelled': redis_job.get('cancelled', 'False').lower() == 'true',
                                    'metadata': metadata,
                                    'created_by': user,
                                    'created_at': timezone.datetime.fromisoformat(redis_job.get('created_at', timezone.now().isoformat())),
                                    'started_at': timezone.datetime.fromisoformat(redis_job.get('started_at')) if redis_job.get('started_at') else None,
                                    'completed_at': timezone.datetime.fromisoformat(redis_job.get('completed_at')) if redis_job.get('completed_at') else None,
                                }
                                
                                serialized_redis_job = self._serialize_job_dict(redis_job_dict)
                                serialized_jobs.append(serialized_redis_job)
                                
                                stats['total'] += 1
                                if redis_status == 'queued':
                                    stats['queued'] += 1
                                    
                            except Exception as e:
                                logger.warning(f"Error serializing Redis job {job_id}: {e}")
                                continue
            except Exception as e:
                logger.warning(f"Error getting Redis-only jobs: {e}")
        
        job_ids_in_db = {job.job_id for job in serialized_jobs if hasattr(job, 'job_id')}
        job_ids_in_db.update([j.get('job_id') for j in serialized_jobs if isinstance(j, dict) and 'job_id' in j])
        
        # Add Redis queue stats and include Redis-only jobs (not yet persisted)
        if REDIS_AVAILABLE and redis_job_queue_manager and redis_job_queue_manager.is_available():
            try:
                redis_stats = redis_job_queue_manager.get_queue_stats()
                stats['redis'] = {
                    'total_queued': redis_stats.get('total_queued', 0),
                    'by_priority': redis_stats.get('by_priority', {}),
                    'active_jobs': redis_stats.get('active_jobs', 0),
                    'pending_persist': redis_stats.get('pending_persist', 0)
                }
                
                # Get active job IDs from Redis
                active_job_ids = redis_job_queue_manager.redis_client.smembers(
                    redis_job_queue_manager.ACTIVE_JOBS_KEY
                )
                
                # Include Redis jobs that aren't in PostgreSQL yet (not yet persisted)
                for job_id_bytes in active_job_ids:
                    job_id = job_id_bytes.decode() if isinstance(job_id_bytes, bytes) else job_id_bytes
                    
                    # Skip if already in PostgreSQL
                    if job_id in job_ids_in_db:
                        continue
                    
                    # Get job data from Redis
                    redis_job = redis_job_queue_manager.get_job_from_redis(job_id)
                    if redis_job:
                        # Only include if it's an active status (not completed)
                        redis_status = redis_job.get('status', 'queued')
                        if redis_status not in ['completed', 'cancelled']:
                            # Create a temporary job representation
                            try:
                                from django.contrib.auth import get_user_model
                                User = get_user_model()
                                user_id = redis_job.get('user_id', '')
                                user = User.objects.get(id=int(user_id)) if user_id and user_id.isdigit() else None
                                
                                # Parse source_files and metadata
                                import json
                                source_files = json.loads(redis_job.get('source_files', '[]'))
                                metadata = json.loads(redis_job.get('metadata', '{}'))
                                
                                # Create a mock UploadJob-like dict for serialization
                                redis_job_dict = {
                                    'job_id': job_id,
                                    'job_type': redis_job.get('job_type', 'file'),
                                    'source_path': redis_job.get('source_path', ''),
                                    'source_files': source_files,
                                    'priority': int(redis_job.get('priority', 5)),
                                    'total_items': int(redis_job.get('total_items', 0)),
                                    'completed_items': int(redis_job.get('completed_items', 0)),
                                    'failed_items': int(redis_job.get('failed_items', 0)),
                                    'status': redis_status,
                                    'paused': redis_job.get('paused', 'False').lower() == 'true',
                                    'cancelled': redis_job.get('cancelled', 'False').lower() == 'true',
                                    'metadata': metadata,
                                    'created_by': user,
                                    'created_at': timezone.datetime.fromisoformat(redis_job.get('created_at', timezone.now().isoformat())),
                                    'started_at': timezone.datetime.fromisoformat(redis_job.get('started_at')) if redis_job.get('started_at') else None,
                                    'completed_at': timezone.datetime.fromisoformat(redis_job.get('completed_at')) if redis_job.get('completed_at') else None,
                                }
                                
                                # Serialize the Redis job
                                serialized_redis_job = self._serialize_job_dict(redis_job_dict)
                                serialized_jobs.append(serialized_redis_job)
                                
                                # Add to stats
                                stats['total'] += 1
                                if redis_status == 'queued':
                                    stats['queued'] += 1
                                    
                            except Exception as e:
                                logger.warning(f"Error serializing Redis job {job_id}: {e}")
                                continue
                
                # Add Redis queued jobs to total
                stats['total'] += redis_stats.get('total_queued', 0)
                stats['queued'] += redis_stats.get('total_queued', 0)
            except Exception as e:
                logger.warning(f"Error getting Redis queue stats: {e}")
        
        # Sort all jobs by created_at DESC (newest first)
        serialized_jobs.sort(key=lambda j: j.get('created_at', ''), reverse=True)
        
        return {
            'stats': stats,
            'jobs': serialized_jobs[:100]  # Limit to 100 most recent
        }
    
    def check_system_resources(self) -> Dict[str, Any]:
        """
        Check system resources (CPU, memory)
        
        Returns:
            Dict with resource status and recommendations
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            resources_ok = cpu_percent < self.cpu_threshold and memory_percent < self.memory_threshold
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'memory_available_gb': memory.available / (1024**3),
                'resources_ok': resources_ok,
                'should_pause_low_priority': not resources_ok
            }
        except Exception as e:
            logger.warning(f"Error checking system resources: {e}")
            # If we can't check resources, assume they're OK
            return {
                'cpu_percent': 0,
                'memory_percent': 0,
                'memory_available_gb': 0,
                'resources_ok': True,
                'should_pause_low_priority': False
            }
    
    def get_next_job(self) -> Optional[UploadJob]:
        """
        Get next job to process based on priority and fair scheduling
        
        Returns:
            Next UploadJob to process, or None if none available
        """
        # Check concurrent job limit
        active_jobs = UploadJob.objects.filter(
            status__in=['uploading', 'processing'],
            paused=False,
            cancelled=False
        ).count()
        
        if active_jobs >= self.max_concurrent_jobs:
            logger.debug(f"Max concurrent jobs reached ({active_jobs}/{self.max_concurrent_jobs})")
            return None
        
        # Get next job - simplified approach: all jobs treated equally
        try:
            with transaction.atomic():
                # Build query - no priority filtering, all jobs treated equally
                queryset = UploadJob.objects.select_for_update().filter(
                    status='queued',
                    paused=False,
                    cancelled=False
                )
                
                # IMPROVED: Prioritize stuck jobs (>30 minutes) to prevent starvation
                # Check for jobs queued >30 minutes and boost their effective priority
                stuck_cutoff = timezone.now() - timedelta(minutes=30)
                stuck_jobs = queryset.filter(created_at__lt=stuck_cutoff)
                
                if stuck_jobs.exists():
                    # Process oldest stuck job first (prevent starvation)
                    job = stuck_jobs.order_by('created_at').first()
                    if job:
                        age_minutes = (timezone.now() - job.created_at).total_seconds() / 60
                        logger.warning(
                            f"Selected stuck job {job.job_id} for processing "
                            f"(age: {age_minutes:.1f} min, priority: {job.priority}) - preventing starvation"
                        )
                        self._last_job_type_processed = job.job_type
                        job.status = 'uploading'
                        job.started_at = timezone.now()
                        job.save()
                        return job
                
                # Simple first-come-first-served: get oldest job
                job = queryset.order_by('created_at').first()
                
                if job:
                    self._last_job_type_processed = job.job_type
                    # Mark as uploading
                    job.status = 'uploading'
                    job.started_at = timezone.now()
                    job.save()
                    logger.info(f"Selected job {job.job_id} for processing (type: {job.job_type}, priority: {job.priority})")
                
                return job
                
        except Exception as e:
            logger.error(f"Error getting next job: {e}", exc_info=True)
            return None
    
    def pause_job(self, job_id: str) -> bool:
        """
        Pause a job
        
        Args:
            job_id: Job UUID
            
        Returns:
            True if paused, False if not found
        """
        try:
            job = UploadJob.objects.get(job_id=job_id)
            job.paused = True
            # Keep current status, paused is handled via flag
            job.save()
            logger.info(f"Paused job {job_id} (status: {job.status})")
            return True
        except UploadJob.DoesNotExist:
            logger.warning(f"Job {job_id} not found for pause")
            return False
        except Exception as e:
            logger.error(f"Error pausing job {job_id}: {e}", exc_info=True)
            return False
    
    def resume_job(self, job_id: str) -> bool:
        """
        Resume a paused job
        
        Args:
            job_id: Job UUID
            
        Returns:
            True if resumed, False if not found
        """
        try:
            job = UploadJob.objects.get(job_id=job_id)
            if not job.paused:
                logger.warning(f"Job {job_id} is not paused")
                return False
            
            job.paused = False
            # Resume job - status will be recalculated by recalculate_job_status if needed
            job.save()
            logger.info(f"Resumed job {job_id} (status: {job.status})")
            return True
        except UploadJob.DoesNotExist:
            logger.warning(f"Job {job_id} not found for resume")
            return False
        except Exception as e:
            logger.error(f"Error resuming job {job_id}: {e}", exc_info=True)
            return False
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a job and remove from Redis (cancelled jobs are not active)
        
        Args:
            job_id: Job UUID
            
        Returns:
            True if cancelled, False if not found
        """
        try:
            job = UploadJob.objects.get(job_id=job_id)
            job.cancelled = True
            # Mark as completed since cancelled jobs are terminal
            job.status = 'completed'
            if not job.completed_at:
                job.completed_at = timezone.now()
            job.save(update_fields=['cancelled', 'status', 'completed_at'])
            
            # Remove from Redis (cancelled jobs should not be in active jobs)
            try:
                if REDIS_AVAILABLE and redis_job_queue_manager and redis_job_queue_manager.is_available():
                    redis_job_queue_manager.remove_job_from_redis(job_id)
                    logger.info(f"Cancelled job {job_id} and removed from Redis")
                else:
                    logger.info(f"Cancelled job {job_id} (Redis not available)")
            except Exception as e:
                logger.warning(f"Error removing cancelled job {job_id} from Redis: {e}")
            
            return True
        except UploadJob.DoesNotExist:
            logger.warning(f"Job {job_id} not found for cancel")
            return False
        except Exception as e:
            logger.error(f"Error cancelling job {job_id}: {e}", exc_info=True)
            return False
    
    def update_job_progress(
        self,
        job_id: str,
        completed_items: int = None,
        failed_items: int = None,
        status: str = None,
        error_message: str = None,
        file_error: Dict[str, str] = None,
        last_processed_index: int = None
    ) -> bool:
        """
        Update job progress
        
        ENHANCED: Updates both Redis cache and PostgreSQL
        
        Args:
            job_id: Job UUID
            completed_items: Number of completed items
            failed_items: Number of failed items
            status: New status (optional)
            error_message: Job-level error (optional)
            file_error: Dict with {file_path: error_message} (optional)
            
        Returns:
            True if updated, False if not found
        """
        # Update Redis cache first (fast)
        if REDIS_AVAILABLE and redis_job_queue_manager and redis_job_queue_manager.is_available():
            redis_job_queue_manager.update_job_status(
                job_id=job_id,
                status=status,
                completed_items=completed_items,
                failed_items=failed_items,
                error_message=error_message
            )
        
        # Update PostgreSQL (persistent)
        try:
            job = UploadJob.objects.get(job_id=job_id)
            
            if completed_items is not None:
                job.completed_items = completed_items
                job.last_processed_file_index = completed_items
            
            if failed_items is not None:
                job.failed_items = failed_items
            
            if status:
                job.status = status
                if status == 'completed':
                    job.completed_at = timezone.now()
            
            if error_message:
                job.error_message = error_message
            
            if file_error:
                if not job.file_errors:
                    job.file_errors = {}
                job.file_errors.update(file_error)
            
            if last_processed_index is not None:
                job.last_processed_file_index = last_processed_index
            
            job.save()
            return True
            
        except UploadJob.DoesNotExist:
            logger.warning(f"Job {job_id} not found for progress update")
            return False
        except Exception as e:
            logger.error(f"Error updating job progress {job_id}: {e}", exc_info=True)
            return False
    
    def pause_low_priority_jobs_if_needed(self):
        """
        Check resources and pause low-priority jobs if resources are high
        
        This should be called periodically (e.g., by Celery Beat)
        """
        try:
            resources = self.check_system_resources()
            
            if resources['should_pause_low_priority']:
                # Pause low-priority jobs (priority < 7) that are currently processing
                paused_count = UploadJob.objects.filter(
                    status__in=['uploading', 'processing'],
                    priority__lt=7,
                    paused=False,
                    cancelled=False
                ).update(paused=True)  # Only update paused flag, keep status
                
                if paused_count > 0:
                    logger.warning(f"Paused {paused_count} low-priority jobs due to high resource usage")
                    return paused_count
            else:
                # Resume paused low-priority jobs if resources are OK
                resumed_count = UploadJob.objects.filter(
                    priority__lt=7,
                    paused=True,  # Use paused flag, not status
                    cancelled=False,
                    completed_items__lt=F('total_items')  # Not completed
                ).update(paused=False, status='queued')
                
                if resumed_count > 0:
                    logger.info(f"Resumed {resumed_count} low-priority jobs - resources OK")
                    return -resumed_count  # Negative to indicate resume
            
            return 0
        except Exception as e:
            logger.error(f"Error in pause_low_priority_jobs_if_needed: {e}", exc_info=True)
            return 0
    
    def validate_url(self, url: str) -> Dict[str, Any]:
        """
        Validate and check accessibility of a URL
        
        Returns:
            Dict with 'valid', 'accessible', 'error' keys
        """
        try:
            # Basic URL validation
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return {'valid': False, 'accessible': False, 'error': 'Invalid URL format'}
            
            if parsed.scheme not in ['http', 'https']:
                return {'valid': False, 'accessible': False, 'error': 'URL must use http or https'}
            
            # Check accessibility
            try:
                response = requests.head(url, timeout=10, allow_redirects=True)
                accessible = response.status_code < 400
                return {
                    'valid': True,
                    'accessible': accessible,
                    'status_code': response.status_code,
                    'error': None if accessible else f'HTTP {response.status_code}'
                }
            except requests.exceptions.RequestException as e:
                return {
                    'valid': True,
                    'accessible': False,
                    'error': f'Cannot access URL: {str(e)}'
                }
                
        except Exception as e:
            return {'valid': False, 'accessible': False, 'error': str(e)}
    
    def discover_webpage_files(self, url: str, max_files: int = 50) -> List[Dict[str, Any]]:
        """
        Discover downloadable files from a webpage URL
        
        Args:
            url: Webpage URL to scan
            max_files: Maximum number of files to discover
            
        Returns:
            List of file info dicts with 'url', 'name', 'type', 'size' keys
        """
        try:
            logger.info(f"Discovering files from webpage: {url}")
            
            # Validate URL first
            validation = self.validate_url(url)
            if not validation['valid'] or not validation['accessible']:
                raise Exception(validation.get('error', 'URL validation failed'))
            
            # Fetch webpage
            response = requests.get(url, timeout=30, allow_redirects=True)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            base_url = response.url  # Get final URL after redirects
            
            # File extensions to look for
            file_extensions = {
                'pdf': ['pdf'],
                'doc': ['doc', 'docx'],
                'xls': ['xls', 'xlsx'],
                'ppt': ['ppt', 'pptx'],
                'txt': ['txt', 'md'],
                'csv': ['csv'],
                'zip': ['zip', 'rar', '7z'],
                'image': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg'],
            }
            
            all_extensions = []
            for ext_list in file_extensions.values():
                all_extensions.extend(ext_list)
            
            discovered_files = []
            
            # Find all links
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link.get('href', '')
                if not href:
                    continue
                
                # Resolve relative URLs
                full_url = urljoin(base_url, href)
                
                # Check if it's a file link
                parsed_url = urlparse(full_url)
                path = parsed_url.path.lower()
                
                # Check file extension
                for ext in all_extensions:
                    if path.endswith(f'.{ext}'):
                        # Get file name
                        filename = os.path.basename(parsed_url.path) or f"file_{len(discovered_files)}.{ext}"
                        
                        # Determine file type
                        file_type = 'other'
                        for type_name, ext_list in file_extensions.items():
                            if ext in ext_list:
                                file_type = type_name
                                break
                        
                        discovered_files.append({
                            'url': full_url,
                            'name': filename,
                            'type': file_type,
                            'size': None,  # Will be determined when downloading
                        })
                        
                        if len(discovered_files) >= max_files:
                            break
                
                if len(discovered_files) >= max_files:
                    break
            
            # Also check for direct file links in page content (e.g., embedded PDFs)
            if len(discovered_files) < max_files:
                # Look for iframe, embed, object tags
                for tag in soup.find_all(['iframe', 'embed', 'object']):
                    src = tag.get('src') or tag.get('data')
                    if src:
                        full_url = urljoin(base_url, src)
                        parsed_url = urlparse(full_url)
                        path = parsed_url.path.lower()
                        
                        for ext in all_extensions:
                            if path.endswith(f'.{ext}'):
                                filename = os.path.basename(parsed_url.path) or f"file_{len(discovered_files)}.{ext}"
                                
                                # Check if already added
                                if not any(f['url'] == full_url for f in discovered_files):
                                    file_type = 'other'
                                    for type_name, ext_list in file_extensions.items():
                                        if ext in ext_list:
                                            file_type = type_name
                                            break
                                    
                                    discovered_files.append({
                                        'url': full_url,
                                        'name': filename,
                                        'type': file_type,
                                        'size': None,
                                    })
                                    
                                    if len(discovered_files) >= max_files:
                                        break
                        
                        if len(discovered_files) >= max_files:
                            break
            
            logger.info(f"Discovered {len(discovered_files)} files from {url}")
            return discovered_files
            
        except Exception as e:
            logger.error(f"Error discovering files from webpage {url}: {e}", exc_info=True)
            raise
    
    def _serialize_job(self, job: UploadJob) -> Dict[str, Any]:
        """Serialize job for API response with per-file status details"""
        source_files = job.source_files or []
        
        # Calculate per-file statistics
        file_stats = {
            'total': len(source_files),
            'pending_upload': sum(1 for f in source_files if f.get('upload_status') == 'pending'),
            'uploading': sum(1 for f in source_files if f.get('upload_status') == 'uploading'),
            'uploaded': sum(1 for f in source_files if f.get('upload_status') == 'uploaded'),
            'upload_failed': sum(1 for f in source_files if f.get('upload_status') == 'failed'),
            'pending_processing': sum(1 for f in source_files if f.get('processing_status') == 'pending'),
            'processing': sum(1 for f in source_files if f.get('processing_status') in ['processing', 'chunking', 'embedding', 'metadata_extracting']),
            'ready': sum(1 for f in source_files if f.get('processing_status') == 'ready'),
            'processing_failed': sum(1 for f in source_files if f.get('processing_status') == 'failed'),
        }
        
        return {
            'job_id': str(job.job_id),
            'job_type': job.job_type,
            'source_path': job.source_path,
            'source_files': source_files,  # Include full per-file status details
            'status': job.status,
            'priority': job.priority,
            'total_items': job.total_items,
            'completed_items': job.completed_items,
            'failed_items': job.failed_items,
            'progress_percentage': job.get_progress_percentage(),
            'paused': job.paused,
            'cancelled': job.cancelled,
            'metadata': job.metadata,
            'error_message': job.error_message,
            'file_errors': job.file_errors,
            'created_at': job.created_at.isoformat() if job.created_at else None,
            'started_at': job.started_at.isoformat() if job.started_at else None,
            'completed_at': job.completed_at.isoformat() if job.completed_at else None,
            'created_by': job.created_by.username if job.created_by else None,
            # Per-file statistics for easy UI display
            'file_stats': file_stats,
        }
    
    def _serialize_job_dict(self, job_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize job dict (from Redis) for API response"""
        source_files = job_dict.get('source_files', [])
        
        # Calculate per-file statistics
        file_stats = {
            'total': len(source_files),
            'pending_upload': sum(1 for f in source_files if f.get('upload_status') == 'pending'),
            'uploading': sum(1 for f in source_files if f.get('upload_status') == 'uploading'),
            'uploaded': sum(1 for f in source_files if f.get('upload_status') == 'uploaded'),
            'upload_failed': sum(1 for f in source_files if f.get('upload_status') == 'failed'),
            'pending_processing': sum(1 for f in source_files if f.get('processing_status') == 'pending'),
            'processing': sum(1 for f in source_files if f.get('processing_status') in ['processing', 'chunking', 'embedding', 'metadata_extracting']),
            'ready': sum(1 for f in source_files if f.get('processing_status') == 'ready'),
            'processing_failed': sum(1 for f in source_files if f.get('processing_status') == 'failed'),
        }
        
        total_items = job_dict.get('total_items', 0)
        completed_items = job_dict.get('completed_items', 0)
        failed_items = job_dict.get('failed_items', 0)
        
        # Calculate progress based on file states:
        # - Upload phase: 0-50% (based on files uploaded)
        # - If still processing: stay at 50% (all files uploaded but processing)
        # - Complete phase: 50-100% (only when files become ready)
        if total_items > 0:
            # Count files by state
            uploaded_count = sum(1 for f in source_files if 
                f.get('upload_status') == 'uploaded' or f.get('uploaded_file_id'))
            processing_count = sum(1 for f in source_files if 
                f.get('processing_status') in ['processing', 'chunking', 'embedding', 'metadata_extracting'])
            ready_count = sum(1 for f in source_files if 
                f.get('processing_status') == 'ready')
            skipped_count = sum(1 for f in source_files if 
                f.get('upload_status') == 'skipped' or f.get('processing_status') == 'skipped')
            failed_count = sum(1 for f in source_files if 
                f.get('upload_status') == 'failed' or f.get('processing_status') == 'failed')
            
            # Upload progress: 0-50% (50% when all files uploaded)
            upload_progress = (uploaded_count + skipped_count + failed_count) / total_items * 50 if total_items > 0 else 0
            
            # If all files are uploaded but still processing: stay at 50%
            all_uploaded = (uploaded_count + skipped_count + failed_count) == total_items
            if all_uploaded and processing_count > 0:
                # All uploaded, but still processing - stay at 50%
                progress_percentage = 50
            else:
                # Calculate based on ready files: 50-100%
                completed_count = ready_count + skipped_count + failed_count
                if completed_count == total_items:
                    # All files completed - 100%
                    progress_percentage = 100
                elif ready_count > 0:
                    # Some files ready: 50% + (ready/total * 50%)
                    ready_progress = ready_count / total_items * 50
                    progress_percentage = int(50 + ready_progress)
                else:
                    # Still uploading or no files ready yet
                    progress_percentage = int(upload_progress)
            
            # Ensure it's between 0-100
            progress_percentage = max(0, min(100, progress_percentage))
        else:
            progress_percentage = 0
        
        # Handle date fields - they might be strings or datetime objects
        created_at = job_dict.get('created_at')
        if isinstance(created_at, str):
            created_at = created_at
        elif hasattr(created_at, 'isoformat'):
            created_at = created_at.isoformat()
        else:
            created_at = timezone.now().isoformat()
        
        started_at = job_dict.get('started_at')
        if started_at and hasattr(started_at, 'isoformat'):
            started_at = started_at.isoformat()
        elif started_at:
            started_at = str(started_at)
        else:
            started_at = None
        
        completed_at = job_dict.get('completed_at')
        if completed_at and hasattr(completed_at, 'isoformat'):
            completed_at = completed_at.isoformat()
        elif completed_at:
            completed_at = str(completed_at)
        else:
            completed_at = None
        
        # Handle created_by - might be user object or string
        created_by = job_dict.get('created_by')
        if created_by and hasattr(created_by, 'username'):
            created_by = created_by.username
        elif isinstance(created_by, str):
            created_by = created_by
        else:
            created_by = None
        
        return {
            'job_id': str(job_dict.get('job_id', '')),
            'job_type': job_dict.get('job_type', 'file'),
            'source_path': job_dict.get('source_path', ''),
            'source_files': source_files,
            'status': job_dict.get('status', 'queued'),
            'priority': job_dict.get('priority', 5),
            'total_items': total_items,
            'completed_items': completed_items,
            'failed_items': failed_items,
            'progress_percentage': progress_percentage,
            'paused': job_dict.get('paused', False),
            'cancelled': job_dict.get('cancelled', False),
            'metadata': job_dict.get('metadata', {}),
            'error_message': job_dict.get('error_message'),
            'file_errors': job_dict.get('file_errors', {}),
            'created_at': created_at,
            'started_at': started_at,
            'completed_at': completed_at,
            'created_by': created_by,
            # Per-file statistics for easy UI display
            'file_stats': file_stats,
        }


# Singleton instance
upload_queue_manager = UploadQueueManager()

