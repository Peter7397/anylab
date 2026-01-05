import os
from celery import Celery
from kombu import Queue
from django.conf import settings
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anylab.settings')

app = Celery('anylab')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Celery configuration
app.conf.update(
    # Task routing
    task_routes={
        'ai_assistant.tasks.*': {'queue': 'ai_queue'},
        'monitoring.tasks.*': {'queue': 'monitoring_queue'},
        'maintenance.tasks.*': {'queue': 'maintenance_queue'},
        'users.tasks.*': {'queue': 'default'},
    },
    
    # Configure multiple queues for file size-based routing
    task_queues=(
        Queue('celery', routing_key='celery'),  # Default queue
        Queue('ai_queue', routing_key='ai'),  # AI tasks queue
        Queue('fast_queue', routing_key='fast'),  # Small files (<1MB)
        Queue('normal_queue', routing_key='normal'),  # Medium files (1-10MB)
        Queue('slow_queue', routing_key='slow'),  # Large files (>10MB)
        Queue('ocr_queue', routing_key='ocr'),  # Files requiring OCR
    ),
    
    # Task serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task execution (allow override via env CELERY_TASK_ALWAYS_EAGER=true)
    task_always_eager=os.getenv('CELERY_TASK_ALWAYS_EAGER', 'false').lower() == 'true',
    task_eager_propagates=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Result backend
    result_backend=settings.CELERY_RESULT_BACKEND,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        'monitor-systems': {
            'task': 'monitoring.tasks.monitor_systems',
            'schedule': 60.0,  # Every 60 seconds
        },
        'collect-metrics': {
            'task': 'monitoring.tasks.collect_system_metrics',
            'schedule': 300.0,  # Every 5 minutes
        },
        'check-maintenance-schedules': {
            'task': 'maintenance.tasks.check_maintenance_schedules',
            'schedule': 3600.0,  # Every hour
        },
        'process-document-queue': {
            'task': 'ai_assistant.tasks.process_document_queue',
            'schedule': 30.0,  # Every 30 seconds
        },
        'scrape-ssb-weekly': {
            'task': 'ai_assistant.tasks.scrape_ssb_weekly',
            'schedule': crontab(hour=2, minute=0, day_of_week=0),  # Every Sunday at 2 AM
        },
        'refresh-expired-websites': {
            'task': 'ai_assistant.tasks.refresh_expired_websites',
            'schedule': crontab(hour=3, minute=0),  # Every day at 3 AM
        },
        'process-pending-uploads': {
            'task': 'ai_assistant.tasks.process_pending_files',
            'schedule': 60.0,  # Every 60 seconds requeue stale pending uploads
        },
        'monitor-upload-queue-resources': {
            'task': 'ai_assistant.tasks.monitor_queue_resources',
            'schedule': 60.0,  # Every 60 seconds monitor system resources and pause/resume jobs
        },
        'cleanup-stuck-jobs': {
            'task': 'ai_assistant.tasks.cleanup_stuck_jobs',
            'schedule': 300.0,  # Every 5 minutes clean up stuck/abandoned jobs
        },
        'monitor-stuck-jobs': {
            'task': 'ai_assistant.tasks.monitor_stuck_jobs',
            'schedule': 180.0,  # Every 3 minutes monitor and alert on stuck jobs
        },
        'persist-redis-jobs-to-database': {
            'task': 'ai_assistant.tasks.persist_jobs_to_database',
            'schedule': 10.0,  # Every 10 seconds persist Redis jobs to PostgreSQL
        },
    },
)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}') 