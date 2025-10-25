import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'onlab.settings')

app = Celery('onlab')

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
    
    # Task serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task execution
    task_always_eager=False,  # Set to True for testing
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
    },
)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}') 