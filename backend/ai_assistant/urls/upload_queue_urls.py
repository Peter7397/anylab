"""
Upload Queue URL Configuration
"""

from django.urls import path
from ai_assistant.views.upload_queue_views import (
    create_upload_job,
    get_job_detail,
    pause_job,
    resume_job,
    retry_job,
    delete_job,
    update_job,
    get_queue_stats,
    discover_webpage_files,
    queue_webpage_files,
    upload_file_content,
)

urlpatterns = [
    # Create upload job (POST) and get queue status (GET) - same endpoint, different methods
    path('queue/', create_upload_job, name='upload_queue'),
    
    # Queue statistics - MUST come before parameterized routes to avoid matching "stats" as job_id
    path('queue/stats/', get_queue_stats, name='get_queue_stats'),
    
    # Job detail
    path('queue/<str:job_id>/', get_job_detail, name='get_job_detail'),
    
    # Job control
    path('queue/<str:job_id>/pause/', pause_job, name='pause_job'),
    path('queue/<str:job_id>/resume/', resume_job, name='resume_job'),
    path('queue/<str:job_id>/retry/', retry_job, name='retry_job'),
    path('queue/<str:job_id>/delete/', delete_job, name='delete_job'),
    path('queue/<str:job_id>/update/', update_job, name='update_job'),
    
    # File content upload (for jobs created with metadata only)
    path('queue/<str:job_id>/upload-file/', upload_file_content, name='upload_file_content'),
    
    # Webpage discovery and queuing
    path('discover-webpage/', discover_webpage_files, name='discover_webpage_files'),
    path('queue-webpage-files/', queue_webpage_files, name='queue_webpage_files'),
]

