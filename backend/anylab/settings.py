"""
Django settings for anylab project.
"""

from pathlib import Path
import os
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
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
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

# Database Configuration - HYBRID SETUP (Docker PostgreSQL + Local Django)
# ============================================================================
# HARDCODED for Hybrid Architecture:
# - Docker Services: PostgreSQL (port 5433), Redis (port 6379), Neo4j (ports 7474, 7687)
# - Local Services: Django Backend (port 8000), React Frontend (port 3000), Celery Worker
# - All connections use localhost/127.0.0.1 to connect from local to Docker via exposed ports
# ============================================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'anylab',  # HARDCODED: Database name
        'USER': 'postgres',  # HARDCODED: Database user
        'PASSWORD': 'password',  # HARDCODED: Database password
        'HOST': '127.0.0.1',  # HARDCODED: localhost for hybrid (Docker on 5433)
        'PORT': '5433',  # HARDCODED: Docker port mapping
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}


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

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files - HARDCODED
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

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
    'BLACKLIST_AFTER_ROTATION': True,
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

# Celery Configuration - HYBRID SETUP - HARDCODED
# =====================================
# HARDCODED: Use localhost to connect to Docker Redis container
# =====================================
CELERY_BROKER_URL = 'redis://localhost:6379/0'  # HARDCODED: localhost for hybrid
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'  # HARDCODED: localhost for hybrid
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_WORKER_CONCURRENCY = 4
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

# Redis Configuration - HYBRID SETUP - HARDCODED
# ====================================
# HARDCODED: Use localhost to connect to Docker Redis container
# ====================================
REDIS_URL = 'redis://localhost:6379/0'  # HARDCODED: localhost for hybrid

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': REDIS_URL,
        'TIMEOUT': 3600,  # Default cache timeout: 1 hour
    }
}

# Use Redis for session storage as well
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# AI Model Settings - HARDCODED
AI_MODEL_PATH = '/path/to/qwen-model'  # HARDCODED: AI model path
EMBEDDING_MODEL_PATH = '/path/to/bge-model'  # HARDCODED: Embedding model path
OLLAMA_API_URL = 'http://localhost:11434'  # HARDCODED: Ollama API URL
OLLAMA_MODEL = 'llama3:8b'  # HARDCODED: Ollama model name
OLLAMA_REQUEST_TIMEOUT = 120  # HARDCODED: Request timeout in seconds
OLLAMA_NUM_CTX = 1024  # HARDCODED: Context size for faster processing
OLLAMA_DEFAULT_MAX_TOKENS = 256  # HARDCODED: Max tokens for faster response
OLLAMA_TEMPERATURE = 0.3  # HARDCODED: Temperature for focused responses
OLLAMA_SYSTEM_PROMPT = 'You are a helpful, expert assistant. Provide concise and accurate answers. Keep responses focused and to the point.'  # HARDCODED: System prompt

# Cache TTL settings for AI responses - HARDCODED
EMBEDDING_CACHE_TTL = 3600  # HARDCODED: 1 hour
RESPONSE_CACHE_TTL = 1800  # HARDCODED: 30 minutes
SEARCH_CACHE_TTL = 3600  # HARDCODED: 1 hour

# File Processing Settings - HARDCODED
# Set to False for synchronous processing (faster for development)
ENABLE_ASYNC_FILE_PROCESSING = False  # HARDCODED: Use synchronous processing

# Embedding Model Settings - HARDCODED
EMBEDDING_MODEL_NAME = 'bge-m3:latest'  # HARDCODED: Primary embedding model
EMBEDDING_MODEL_FALLBACK = 'nomic-embed-text:latest'  # HARDCODED: Fallback embedding model
EMBEDDING_DEVICE = 'cpu'  # HARDCODED: Device for embeddings

# Neo4j Graph Database Settings - HARDCODED
NEO4J_URI = 'bolt://localhost:7687'  # HARDCODED: Neo4j URI
NEO4J_USER = 'neo4j'  # HARDCODED: Neo4j username
NEO4J_PASSWORD = 'anylab_neo4j_password'  # HARDCODED: Neo4j password (matches docker-compose.yml)
NEO4J_DATABASE = 'neo4j'  # HARDCODED: Neo4j database name

# Dual Mode Settings - HARDCODED
EMBEDDING_MODE = 'lightweight'  # HARDCODED: 'auto', 'performance', 'lightweight'
EMBEDDING_OFFLINE_ONLY = True  # HARDCODED: Force offline embeddings
EMBEDDING_DIM = 1024  # HARDCODED: Embedding dimension for BGE-M3
EMBEDDING_PERFORMANCE_MODEL = 'BAAI/bge-m3'  # HARDCODED: Performance model
EMBEDDING_LIGHTWEIGHT_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'  # HARDCODED: Lightweight model

# Logging Configuration
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
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'anylab.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
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
