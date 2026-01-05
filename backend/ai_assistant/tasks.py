"""
Celery tasks for AI Assistant operations.

This module maintains backward compatibility by importing all tasks from
the refactored task modules in the tasks/ directory.

For new code, import directly from the specific task modules:
- from ai_assistant.tasks.file_processing_tasks import process_file_automatically
- from ai_assistant.tasks.scraping_tasks import scrape_ssb_weekly
- etc.
"""

# Import all tasks from refactored modules for backward compatibility
from .tasks import (
    # File processing tasks
    process_file_automatically,
    process_upload_job,
    _process_single_file_async,
    process_bulk_upload,
    process_document_queue,
    # Scraping tasks
    scrape_ssb_weekly,
    scrape_ssb_on_demand,
    # Queue management tasks
    monitor_queue_resources,
    process_pending_files,
    cleanup_stuck_jobs,
    monitor_stuck_jobs,
    # Website processing tasks
    process_website_automatically,
    refresh_expired_websites,
    # Maintenance tasks
    purge_old_chat_messages,
    # Task helpers (for backward compatibility)
    calculate_file_priority,
    update_file_status_in_job,
    update_file_processing_status,
    increment_file_retry_count,
    reset_file_retry_count,
    recalculate_job_status,
)

# Re-export for backward compatibility
__all__ = [
    # File processing
    'process_file_automatically',
    'process_upload_job',
    '_process_single_file_async',
    'process_bulk_upload',
    'process_document_queue',
    # Scraping
    'scrape_ssb_weekly',
    'scrape_ssb_on_demand',
    # Queue management
    'monitor_queue_resources',
    'process_pending_files',
    'cleanup_stuck_jobs',
    'monitor_stuck_jobs',
    # Website processing
    'process_website_automatically',
    'refresh_expired_websites',
    # Maintenance
    'purge_old_chat_messages',
    # Task helpers
    'calculate_file_priority',
    'update_file_status_in_job',
    'update_file_processing_status',
    'increment_file_retry_count',
    'reset_file_retry_count',
    'recalculate_job_status',
]
