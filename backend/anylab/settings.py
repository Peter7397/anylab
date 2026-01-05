"""
Django settings for anylab project.
"""

from pathlib import Path
import os
import sys
# Removed dotenv dependency - all values are hardcoded now

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# ============================================================================
# HARDCODED CONFIGURATION - All values are hardcoded for reliability
# ============================================================================

# SECURITY WARNING: keep the secret key used in production secret!
# HARDCODED: Secret key for Django security
SECRET_KEY = 'django-insecure-anylab-production-key-change-in-production-deployment'

# SECURITY WARNING: don't run with debug turned on in production!
# HARDCODED: Debug mode enabled for development
DEBUG = True

# HARDCODED: Allowed hosts for hybrid deployment
# Includes localhost, LAN IPs, and known network interfaces
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    '192.168.1.24',
    '192.168.1.216',
    '192.168.1.15',
    '10.96.17.21',
    'anylab.dpdns.org',
    '*',  # Allow all hosts for hybrid setup
]

# OCR Settings
# Enable/disable OCR processing for files without extractable text
ENABLE_OCR_FOR_SCANNED_FILES = False  # Set to False to disable OCR processing
# OCR Language support: comma-separated language codes (e.g., 'eng,chi_sim,spa')
# Common languages: eng (English), chi_sim (Simplified Chinese), chi_tra (Traditional Chinese),
# spa (Spanish), fra (French), deu (German), jpn (Japanese), kor (Korean)
# See: https://tesseract-ocr.github.io/tessdoc/Data-Files-in-different-versions.html
OCR_LANGUAGES = os.getenv('OCR_LANGUAGES', 'eng').split(',')  # Default: English only


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    
    # Local apps
    'users',
    'ai_assistant',
    'forum',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # Add after SessionMiddleware for i18n
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'ai_assistant.middleware.request_logging.RequestLoggingMiddleware',  # Request logging for debugging
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'anylab.middleware.LoginRequiredMiddleware',
]

ROOT_URLCONF = 'anylab.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'anylab.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# Database Configuration - Docker-aware
# ============================================================================
# Detects if running in Docker container and uses appropriate connection settings
# - Docker: Uses service names (postgres, redis, neo4j)
# - Local: Uses localhost with port mappings
# ============================================================================
import os
IS_DOCKER = os.path.exists('/.dockerenv')  # Check if running in Docker

if IS_DOCKER:
    # Running in Docker - use service names
    DB_HOST = os.getenv('DATABASE_HOST', 'postgres')
    DB_PORT = os.getenv('DATABASE_PORT', '5432')
    REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
    NEO4J_HOST = os.getenv('NEO4J_HOST', 'neo4j')
else:
    # Running on host - use localhost with port mappings
    DB_HOST = os.getenv('DATABASE_HOST', '127.0.0.1')
    DB_PORT = os.getenv('DATABASE_PORT', '5433')
    REDIS_HOST = os.getenv('REDIS_HOST', '127.0.0.1')
    NEO4J_HOST = os.getenv('NEO4J_HOST', '127.0.0.1')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DATABASE_NAME', 'anylab'),
        'USER': os.getenv('DATABASE_USER', 'postgres'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', 'password'),
        'HOST': DB_HOST,
        'PORT': DB_PORT,
        'OPTIONS': {
            'connect_timeout': 10,
        },
        # Connection pooling settings for better performance
        # CONN_MAX_AGE: Time (in seconds) to keep database connections alive
        # 0 = Close connection after each request (default, no pooling)
        # 600 = Keep connection alive for 10 minutes (recommended for production)
        # None = Keep connection alive for the lifetime of the process (best performance, use with caution)
        'CONN_MAX_AGE': int(os.getenv('DATABASE_CONN_MAX_AGE', 600)),  # 10 minutes default
        'TEST': {
            'NAME': os.getenv('TEST_DATABASE_NAME', 'test_anylab'),
            'CREATE_DB': True,
        },
    }
}

# Custom test database creation for pgvector extension
# This will be handled by the test_db_setup module


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'zh-hans'  # Simplified Chinese

LANGUAGES = [
    ('zh-hans', '简体中文'),
    ('en', 'English'),
]

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

USE_I18N = True
USE_L10N = True  # Enable localization of numbers, dates, etc.
USE_TZ = True

TIME_ZONE = 'Asia/Shanghai'  # Chinese timezone


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files - HARDCODED
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# File Upload Configuration - Docker-aware
# Increased limits for Docker environment to support large document uploads
FILE_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB - files larger than this use temp file
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB - max size for request body
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000  # Increased for complex forms
FILE_UPLOAD_TEMP_DIR = os.path.join(MEDIA_ROOT, 'temp')

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'users.User'

# X-Frame-Options: Allow same-origin iframe embedding for document viewer
X_FRAME_OPTIONS = 'SAMEORIGIN'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # Enable session auth for browser access
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
}

# JWT Settings - HARDCODED
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=5),  # HARDCODED: 5 hours
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),  # HARDCODED: 1 day
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,  # HARDCODED: Disabled (blacklist app not installed)
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,  # HARDCODED: Use SECRET_KEY
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# CORS settings
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://192.168.1.24:3000',
    'http://192.168.1.216:3000',
    'http://192.168.1.15:3000',  # Client PC access
    'http://10.96.17.21:3000',
    'https://anylab.dpdns.org',
    'http://anylab.dpdns.org',  # Allow HTTP for initial setup
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Celery Configuration - Docker-aware
# =====================================
# Detects Docker environment and uses appropriate Redis connection
# =====================================
if IS_DOCKER:
    REDIS_URL = os.getenv('REDIS_URL', f'redis://{REDIS_HOST}:6379/0')
else:
    REDIS_URL = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/0')

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_WORKER_CONCURRENCY = 4
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

# Redis Configuration - Docker-aware (already set above)
# REDIS_URL is set in Celery Configuration section

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',  # Using django-redis for better control
        'LOCATION': REDIS_URL,
        'TIMEOUT': 3600,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'IGNORE_EXCEPTIONS': True,  # Don't crash if Redis is down
        }
    }
}

# Use Redis for session storage as well
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# AI Model Settings - Docker-aware
AI_MODEL_PATH = '/path/to/qwen-model'  # Not used with Ollama
EMBEDDING_MODEL_PATH = '/path/to/bge-model'  # Not used with Ollama

# Ollama Configuration - Detects Docker and uses appropriate URL
if IS_DOCKER:
    # In Docker: Ollama is a service in the same network
    OLLAMA_API_URL = os.getenv('OLLAMA_API_URL', 'http://ollama:11434')
else:
    # On host: Ollama may be on host or in Docker
    OLLAMA_API_URL = os.getenv('OLLAMA_API_URL', 'http://localhost:11434')

OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3:8b')  # Can be overridden by env
OLLAMA_REQUEST_TIMEOUT = 120  # HARDCODED: Request timeout in seconds
OLLAMA_NUM_CTX = 1024  # HARDCODED: Context size for faster processing
OLLAMA_DEFAULT_MAX_TOKENS = 256  # HARDCODED: Max tokens for faster response
OLLAMA_TEMPERATURE = 0.3  # HARDCODED: Temperature for focused responses

# System prompts for different languages - HARDCODED
OLLAMA_SYSTEM_PROMPT = 'You are a helpful, expert assistant. Provide concise and accurate answers. Keep responses focused and to the point.'  # HARDCODED: Default English system prompt

OLLAMA_SYSTEM_PROMPT_ZH = '你是一个专业的实验室知识助手。请用简体中文回答所有问题。提供准确、详细、专业的回答，保持回答简洁明了。'  # HARDCODED: Chinese system prompt

OLLAMA_SYSTEM_PROMPT_EN = 'You are a helpful, expert assistant. Provide concise and accurate answers. Keep responses focused and to the point.'  # HARDCODED: English system prompt

# Cache TTL settings for AI responses - HARDCODED
EMBEDDING_CACHE_TTL = 3600  # HARDCODED: 1 hour
RESPONSE_CACHE_TTL = 1800  # HARDCODED: 30 minutes
SEARCH_CACHE_TTL = 3600  # HARDCODED: 1 hour

# Webpage Crawler Configuration
WEBPAGE_CRAWLER_CONFIG = {
    'default_max_depth': 2,  # Default crawl depth (max: 5)
    'default_max_pages': 50,  # Maximum pages to crawl
    'default_max_files': 200,  # Maximum files to discover
    'default_delay_seconds': 1.0,  # Delay between requests
    'default_concurrent_requests': 3,  # Concurrent page requests
    'default_timeout_seconds': 30,  # Timeout per page
    'respect_robots_txt': True,  # Respect robots.txt
}

# File Processing Settings - HARDCODED
# Set to False for synchronous processing (faster for development)
ENABLE_ASYNC_FILE_PROCESSING = False  # HARDCODED: Use synchronous processing

# Embedding Model Settings - HARDCODED
EMBEDDING_MODEL_NAME = 'bge-m3:latest'  # HARDCODED: Primary embedding model
EMBEDDING_MODEL_FALLBACK = 'nomic-embed-text:latest'  # HARDCODED: Fallback embedding model
EMBEDDING_DEVICE = 'cpu'  # HARDCODED: Device for embeddings

# Neo4j Graph Database Settings - Docker-aware
if IS_DOCKER:
    NEO4J_URI = os.getenv('NEO4J_URI', f'bolt://{NEO4J_HOST}:7687')
else:
    NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://127.0.0.1:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'anylab_neo4j_password')
NEO4J_DATABASE = os.getenv('NEO4J_DATABASE', 'neo4j')

# Dual Mode Settings - HARDCODED
EMBEDDING_MODE = 'lightweight'  # HARDCODED: 'auto', 'performance', 'lightweight'
EMBEDDING_OFFLINE_ONLY = True  # HARDCODED: Force offline embeddings
EMBEDDING_DIM = 1024  # HARDCODED: Embedding dimension for BGE-M3
EMBEDDING_PERFORMANCE_MODEL = 'BAAI/bge-m3'  # HARDCODED: Performance model
EMBEDDING_LIGHTWEIGHT_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'  # HARDCODED: Lightweight model
EMBEDDING_CONCURRENCY = 3  # Limit concurrent embedding requests to Ollama for stability

# Logging Configuration
# Enable structured JSON logging via environment variable (default: False for backward compatibility)
ENABLE_JSON_LOGGING = os.getenv('ENABLE_JSON_LOGGING', 'False').lower() == 'true'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'json': {
            '()': 'ai_assistant.utils.json_log_formatter.JSONFormatter',
            'include_correlation_id': True,
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'anylab.log'),
            'formatter': 'json' if ENABLE_JSON_LOGGING else 'verbose',
        },
        'json_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'anylab.json.log'),
            'formatter': 'json',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'json' if ENABLE_JSON_LOGGING else 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'] + (['json_file'] if ENABLE_JSON_LOGGING else []),
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'] + (['json_file'] if ENABLE_JSON_LOGGING else []),
            'level': 'INFO',
            'propagate': False,
        },
        'ai_assistant': {
            'handlers': ['console', 'file'] + (['json_file'] if ENABLE_JSON_LOGGING else []),
            'level': 'INFO',
            'propagate': False,
        },
        'ai_assistant.service_classes.rag_service': {
            'handlers': ['console', 'file'] + (['json_file'] if ENABLE_JSON_LOGGING else []),
            'level': 'INFO',
            'propagate': False,
        },
        'ai_assistant.views.rag_views': {
            'handlers': ['console', 'file'] + (['json_file'] if ENABLE_JSON_LOGGING else []),
            'level': 'INFO',
            'propagate': False,
        },
        'ai_assistant.middleware.request_logging': {
            'handlers': ['console', 'file'] + (['json_file'] if ENABLE_JSON_LOGGING else []),
            'level': 'INFO',
            'propagate': False,
        },
        'ai_assistant.views.debug_views': {
            'handlers': ['console', 'file'] + (['json_file'] if ENABLE_JSON_LOGGING else []),
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

# Celery Beat Schedule
from celery.schedules import crontab
CELERY_BEAT_SCHEDULE = {
    'purge-old-chat-messages-daily': {
        'task': 'ai_assistant.tasks.purge_old_chat_messages',
        'schedule': crontab(hour=3, minute=0),  # Daily at 03:00 UTC
    },
}
