"""
Cross-platform configuration helper for OneLab
Handles differences between Mac and Windows environments
"""

import os
import platform
from pathlib import Path

def get_platform_info():
    """Get current platform information"""
    return {
        'system': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'python_version': platform.python_version(),
    }

def is_windows():
    """Check if running on Windows"""
    return platform.system().lower() == 'windows'

def is_mac():
    """Check if running on macOS"""
    return platform.system().lower() == 'darwin'

def is_linux():
    """Check if running on Linux"""
    return platform.system().lower() == 'linux'

def get_base_dir():
    """Get base directory using pathlib for cross-platform compatibility"""
    return Path(__file__).resolve().parent.parent

def get_media_root():
    """Get media root directory"""
    base_dir = get_base_dir()
    media_root = os.getenv('MEDIA_ROOT', 'media')
    return base_dir / media_root

def get_static_root():
    """Get static root directory"""
    base_dir = get_base_dir()
    return base_dir / 'staticfiles'

def get_logs_dir():
    """Get logs directory"""
    base_dir = get_base_dir()
    return base_dir / 'logs'

def get_database_config():
    """Get database configuration based on platform"""
    if is_windows():
        # Windows-specific database settings
        return {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'onlab'),
            'USER': os.getenv('DB_USER', 'postgres'),
            'PASSWORD': os.getenv('DB_PASSWORD', 'password'),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
            'OPTIONS': {
                'charset': 'utf8',
            },
        }
    else:
        # Mac/Linux database settings
        return {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'onlab'),
            'USER': os.getenv('DB_USER', 'postgres'),
            'PASSWORD': os.getenv('DB_PASSWORD', 'password'),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
        }

def get_redis_config():
    """Get Redis configuration based on platform"""
    if is_windows():
        # Windows-specific Redis settings
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        return {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': redis_url,
            'TIMEOUT': 3600,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    else:
        # Mac/Linux Redis settings
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        return {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': redis_url,
            'TIMEOUT': 3600,
        }

def get_celery_config():
    """Get Celery configuration based on platform"""
    if is_windows():
        # Windows-specific Celery settings
        return {
            'broker_url': os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
            'result_backend': os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
            'task_serializer': 'json',
            'result_serializer': 'json',
            'accept_content': ['json'],
            'timezone': 'UTC',
            'enable_utc': True,
            'worker_concurrency': 2,  # Lower for Windows
            'worker_max_tasks_per_child': 1000,
            'broker_connection_retry_on_startup': True,
        }
    else:
        # Mac/Linux Celery settings
        return {
            'broker_url': os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
            'result_backend': os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
            'task_serializer': 'json',
            'result_serializer': 'json',
            'accept_content': ['json'],
            'timezone': 'UTC',
            'enable_utc': True,
            'worker_concurrency': 4,  # Higher for Unix systems
            'worker_max_tasks_per_child': 1000,
        }

def get_file_upload_config():
    """Get file upload configuration based on platform"""
    if is_windows():
        # Windows-specific file upload settings
        return {
            'FILE_UPLOAD_MAX_MEMORY_SIZE': 2621440,  # 2.5MB
            'FILE_UPLOAD_TEMP_DIR': get_media_root() / 'temp',
            'DATA_UPLOAD_MAX_MEMORY_SIZE': 2621440,  # 2.5MB
        }
    else:
        # Mac/Linux file upload settings
        return {
            'FILE_UPLOAD_MAX_MEMORY_SIZE': 5242880,  # 5MB
            'FILE_UPLOAD_TEMP_DIR': get_media_root() / 'temp',
            'DATA_UPLOAD_MAX_MEMORY_SIZE': 5242880,  # 5MB
        }

def create_directories():
    """Create necessary directories for the application"""
    directories = [
        get_media_root(),
        get_static_root(),
        get_logs_dir(),
        get_media_root() / 'temp',
        get_media_root() / 'uploads',
        get_media_root() / 'pdfs',
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    return directories

def get_environment_info():
    """Get comprehensive environment information"""
    return {
        'platform': get_platform_info(),
        'base_dir': str(get_base_dir()),
        'media_root': str(get_media_root()),
        'static_root': str(get_static_root()),
        'logs_dir': str(get_logs_dir()),
        'is_windows': is_windows(),
        'is_mac': is_mac(),
        'is_linux': is_linux(),
    }
