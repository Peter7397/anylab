"""
Celery tasks organized by category.

This module exports all tasks for backward compatibility.
"""

# Import all tasks to maintain backward compatibility
from .file_processing_tasks import (
    process_file_automatically,
    process_upload_job,
    _process_single_file_async,
    process_bulk_upload,
    process_document_queue,
    build_graph_for_file,
)

from .scraping_tasks import (
    scrape_ssb_weekly,
    scrape_ssb_on_demand,
)

from .queue_tasks import (
    monitor_queue_resources,
    process_pending_files,
    cleanup_stuck_jobs,
    monitor_stuck_jobs,
)

from .job_persistence_tasks import (
    persist_jobs_to_database,
    sync_redis_job_status,
)

from .website_tasks import (
    process_website_automatically,
    refresh_expired_websites,
)

from .maintenance_tasks import (
    purge_old_chat_messages,
)

__all__ = [
    # File processing
    'process_file_automatically',
    'process_upload_job',
    '_process_single_file_async',
    'process_bulk_upload',
    'process_document_queue',
    'build_graph_for_file',
    # Scraping
    'scrape_ssb_weekly',
    'scrape_ssb_on_demand',
    # Queue management
    'monitor_queue_resources',
    'process_pending_files',
    'cleanup_stuck_jobs',
    'monitor_stuck_jobs',
    # Job persistence
    'persist_jobs_to_database',
    'sync_redis_job_status',
    # Website processing
    'process_website_automatically',
    'refresh_expired_websites',
    # Maintenance
    'purge_old_chat_messages',
]

