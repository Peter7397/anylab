"""
System Settings Views

Expose consolidated system settings and simple connection tests.
"""

import logging
import json
import redis
import requests

from django.conf import settings as dj_settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

logger = logging.getLogger(__name__)


def _get_settings_snapshot():
    return {
        'app': {
            'debug': getattr(dj_settings, 'DEBUG', False),
            'allowed_hosts': getattr(dj_settings, 'ALLOWED_HOSTS', []),
            'static_url': getattr(dj_settings, 'STATIC_URL', '/static/'),
            'media_url': getattr(dj_settings, 'MEDIA_URL', '/media/'),
        },
        'file_upload': {
            'max_file_size': 500 * 1024 * 1024,
            'allowed_extensions': [
                '.pdf', '.doc', '.docx', '.txt', '.rtf', '.mhtml', '.html',
                '.ppt', '.pptx', '.xls', '.xlsx'
            ],
            'enable_async_processing': getattr(dj_settings, 'ENABLE_ASYNC_FILE_PROCESSING', False),
        },
        'embeddings': {
            'mode': getattr(dj_settings, 'EMBEDDING_MODE', 'lightweight'),
            'offline_only': getattr(dj_settings, 'EMBEDDING_OFFLINE_ONLY', True),
            'model_name': getattr(dj_settings, 'EMBEDDING_MODEL_NAME', 'bge-m3:latest'),
            'fallback_model': getattr(dj_settings, 'EMBEDDING_MODEL_FALLBACK', 'sentence-transformers/all-MiniLM-L6-v2'),
            'dimension': getattr(dj_settings, 'EMBEDDING_DIM', 384),
            'cache_ttl': getattr(dj_settings, 'EMBEDDING_CACHE_TTL', 3600),
        },
        'rag': {
            'ollama_url': getattr(dj_settings, 'OLLAMA_API_URL', 'http://localhost:11434'),
            'model': getattr(dj_settings, 'OLLAMA_MODEL', 'qwen2.5:latest'),
            'request_timeout': getattr(dj_settings, 'OLLAMA_REQUEST_TIMEOUT', 120),
            'num_ctx': getattr(dj_settings, 'OLLAMA_NUM_CTX', 1024),
            'max_tokens': getattr(dj_settings, 'OLLAMA_DEFAULT_MAX_TOKENS', 256),
            'temperature': getattr(dj_settings, 'OLLAMA_TEMPERATURE', 0.3),
        },
        'cache': {
            'default_timeout': getattr(dj_settings, 'CACHES', {}).get('default', {}).get('TIMEOUT', 3600),
            'search_cache_ttl': getattr(dj_settings, 'SEARCH_CACHE_TTL', 3600),
            'response_cache_ttl': getattr(dj_settings, 'RESPONSE_CACHE_TTL', 1800),
            'redis_url': getattr(dj_settings, 'REDIS_URL', ''),
        },
        'workers': {
            'broker_url': getattr(dj_settings, 'CELERY_BROKER_URL', ''),
            'result_backend': getattr(dj_settings, 'CELERY_RESULT_BACKEND', ''),
            'concurrency': getattr(dj_settings, 'CELERY_WORKER_CONCURRENCY', None),
        },
        'security': {
            'cors_allowed_origins': getattr(dj_settings, 'CORS_ALLOWED_ORIGINS', []),
            'cors_allow_credentials': getattr(dj_settings, 'CORS_ALLOW_CREDENTIALS', False),
            'x_frame_options': getattr(dj_settings, 'X_FRAME_OPTIONS', 'SAMEORIGIN'),
        },
    }


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_settings(request):
    """Return consolidated system settings (read-only for now)."""
    return Response(_get_settings_snapshot())


@api_view(['POST'])
@permission_classes([IsAdminUser])
def test_connection(request):
    """Test a connection (ollama or redis). Expects { type: 'ollama'|'redis', config?: {} }"""
    try:
        payload = request.data if isinstance(request.data, dict) else json.loads(request.body or '{}')
    except Exception:
        payload = {}

    conn_type = payload.get('type')
    config = payload.get('config', {})

    if conn_type == 'ollama':
        url = config.get('url') or getattr(dj_settings, 'OLLAMA_API_URL', 'http://localhost:11434')
        try:
            r = requests.get(f"{url}/api/tags", timeout=10)
            ok = r.status_code == 200
            return Response({'ok': ok, 'status': r.status_code, 'url': url})
        except Exception as e:
            return Response({'ok': False, 'error': str(e), 'url': url}, status=400)

    if conn_type == 'redis':
        redis_url = config.get('url') or getattr(dj_settings, 'REDIS_URL', 'redis://redis:6379/0')
        try:
            client = redis.from_url(redis_url)
            pong = client.ping()
            return Response({'ok': bool(pong), 'url': redis_url})
        except Exception as e:
            return Response({'ok': False, 'error': str(e), 'url': redis_url}, status=400)

    return Response({'ok': False, 'error': 'Unsupported type'}, status=400)


