from celery import shared_task
from django.utils import timezone
import logging
import os
import psutil
from datetime import timedelta

logger = logging.getLogger(__name__)

@shared_task
def system_health_check():
    """Periodic system health check task"""
    try:
        # Get system information
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Log system metrics
        logger.info(f"System Health Check - CPU: {cpu_percent}%, "
                   f"Memory: {memory.percent}%, "
                   f"Disk: {disk.percent}%")
        
        # You can store this data in your monitoring models here
        
        return {
            'status': 'success',
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'disk_percent': disk.percent,
            'timestamp': timezone.now().isoformat()
        }
    except Exception as e:
        logger.error(f"System health check failed: {str(e)}")
        return {'status': 'error', 'message': str(e)}

@shared_task
def cleanup_old_logs():
    """Clean up old log files"""
    try:
        log_dir = os.path.join(os.getcwd(), 'logs')
        if not os.path.exists(log_dir):
            return {'status': 'success', 'message': 'No logs directory found'}
        
        cutoff_date = timezone.now() - timedelta(days=30)
        deleted_count = 0
        
        for filename in os.listdir(log_dir):
            file_path = os.path.join(log_dir, filename)
            if os.path.isfile(file_path):
                file_time = timezone.datetime.fromtimestamp(
                    os.path.getmtime(file_path), 
                    tz=timezone.utc
                )
                if file_time < cutoff_date:
                    os.remove(file_path)
                    deleted_count += 1
        
        logger.info(f"Cleaned up {deleted_count} old log files")
        return {
            'status': 'success',
            'deleted_count': deleted_count,
            'message': f'Cleaned up {deleted_count} old log files'
        }
    except Exception as e:
        logger.error(f"Log cleanup failed: {str(e)}")
        return {'status': 'error', 'message': str(e)}

@shared_task
def database_backup():
    """Create database backup"""
    try:
        from django.conf import settings
        import subprocess
        
        backup_dir = os.path.join(os.getcwd(), 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'backup_{timestamp}.sql')
        
        # Create backup using pg_dump
        cmd = [
            'pg_dump',
            '-h', settings.DATABASES['default']['HOST'],
            '-U', settings.DATABASES['default']['USER'],
            '-d', settings.DATABASES['default']['NAME'],
            '-f', backup_file
        ]
        
        # Set password environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = settings.DATABASES['default']['PASSWORD']
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"Database backup created: {backup_file}")
            return {
                'status': 'success',
                'backup_file': backup_file,
                'message': 'Database backup created successfully'
            }
        else:
            logger.error(f"Database backup failed: {result.stderr}")
            return {
                'status': 'error',
                'message': f'Database backup failed: {result.stderr}'
            }
    except Exception as e:
        logger.error(f"Database backup failed: {str(e)}")
        return {'status': 'error', 'message': str(e)}

@shared_task
def send_notification(message, recipient_list):
    """Send notification to users"""
    try:
        # This is a placeholder for notification sending
        # You can implement email, SMS, or other notification methods here
        logger.info(f"Sending notification to {len(recipient_list)} recipients: {message}")
        
        # Simulate notification sending
        import time
        time.sleep(1)  # Simulate processing time
        
        return {
            'status': 'success',
            'message': f'Notification sent to {len(recipient_list)} recipients',
            'recipient_count': len(recipient_list)
        }
    except Exception as e:
        logger.error(f"Notification sending failed: {str(e)}")
        return {'status': 'error', 'message': str(e)} 