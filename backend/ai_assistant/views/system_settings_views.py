"""
System Settings Views

Expose consolidated system settings and simple connection tests.
"""

import logging
import json
import redis
import requests
import importlib.util

from django.conf import settings as dj_settings
from django.utils import timezone
from django.core.cache import cache
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from ..utils.model_settings import get_ollama_model, get_model_for_ai_mode, set_ollama_model, get_current_ai_mode, AI_MODE_MODELS, DYNAMIC_SETTINGS_CACHE_KEY, DYNAMIC_SETTINGS_CACHE_TTL, get_ocr_enabled, set_ocr_enabled

logger = logging.getLogger(__name__)


def _get_dynamic_settings():
    """Get dynamic settings from cache, with fallback to defaults."""
    cached = cache.get(DYNAMIC_SETTINGS_CACHE_KEY)
    if cached:
        return cached
    return {
        'ollama_model': get_ollama_model(),
        'ai_mode': None,  # Will be inferred from model if not set
    }


def _get_settings_snapshot():
    dynamic_settings = _get_dynamic_settings()
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
            'enable_ocr_for_scanned_files': get_ocr_enabled(),  # Use dynamic setting
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
            'ollama_url': getattr(dj_settings, 'OLLAMA_API_URL', 'http://ollama:11434'),
            'model': get_ollama_model(),
            'ai_mode': get_current_ai_mode(),
            'recommended_models': {
                'performance': AI_MODE_MODELS['performance'],
                'lightweight': AI_MODE_MODELS['lightweight'],
            },
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
    """Return consolidated system settings."""
    return Response(_get_settings_snapshot())


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_available_models(request):
    """Get list of available Ollama models."""
    try:
        ollama_url = getattr(dj_settings, 'OLLAMA_API_URL', 'http://ollama:11434')
        r = requests.get(f"{ollama_url}/api/tags", timeout=5)
        if r.status_code == 200:
            models_data = r.json().get('models', [])
            available_models = [tag.get('name', '') for tag in models_data if tag.get('name')]
            return Response({
                'success': True,
                'models': available_models
            })
        else:
            return Response({
                'success': False,
                'error': f'Ollama API returned status {r.status_code}',
                'models': []
            }, status=400)
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Ollama models: {e}")
        return Response({
            'success': False,
            'error': f'Could not connect to Ollama at {ollama_url}. Make sure Ollama is running.',
            'models': []
        }, status=400)
    except Exception as e:
        logger.error(f"Error fetching Ollama models: {e}")
        return Response({
            'success': False,
            'error': str(e),
            'models': []
        }, status=500)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAdminUser])
def update_settings(request):
    """Update system settings (supports Ollama model and OCR setting)."""
    try:
        dynamic_settings = _get_dynamic_settings()
        updated = False
        
        # Update OCR setting if provided
        if 'file_upload' in request.data and 'enable_ocr_for_scanned_files' in request.data['file_upload']:
            ocr_enabled = request.data['file_upload']['enable_ocr_for_scanned_files']
            if not isinstance(ocr_enabled, bool):
                return Response({'error': 'enable_ocr_for_scanned_files must be a boolean'}, status=400)
            
            set_ocr_enabled(ocr_enabled)
            logger.info(f"OCR setting updated to: {ocr_enabled} by user {request.user.username}")
            updated = True
        
        # Update Ollama model if provided
        if 'rag' in request.data and 'model' in request.data['rag']:
            new_model = request.data['rag']['model'].strip()
            if not new_model:
                return Response({'error': 'Model name cannot be empty'}, status=400)
            
            # Validate model exists in Ollama (optional check)
            ollama_url = getattr(dj_settings, 'OLLAMA_API_URL', 'http://ollama:11434')
            try:
                r = requests.get(f"{ollama_url}/api/tags", timeout=5)
                if r.status_code == 200:
                    models_data = r.json().get('models', [])
                    available_models = [tag.get('name', '') for tag in models_data]
                    if new_model not in available_models:
                        # Check for similar model names (e.g., qwen2:2b vs qwen2.5:2b)
                        similar_models = [m for m in available_models if new_model.split(':')[0] in m or m.split(':')[0] in new_model]
                        if similar_models:
                            logger.warning(f"Model {new_model} not found, but similar models available: {similar_models}")
                            return Response({
                                'error': f'Model "{new_model}" not found in Ollama. Available similar models: {", ".join(similar_models)}. Please use one of these model names.',
                                'available_models': available_models,
                                'similar_models': similar_models
                            }, status=400)
                        else:
                            logger.warning(f"Model {new_model} not found in Ollama. Available: {available_models}")
                            return Response({
                                'error': f'Model "{new_model}" not found in Ollama. Available models: {", ".join(available_models[:10])}',
                                'available_models': available_models
                            }, status=400)
            except requests.exceptions.RequestException as e:
                logger.warning(f"Could not validate model with Ollama (connection error): {e}")
                # Don't block the update if we can't connect - just warn
            except Exception as e:
                logger.warning(f"Could not validate model with Ollama: {e}")
            
            # Update cache using utility function (preserve AI mode if set)
            current_mode = get_current_ai_mode()
            set_ollama_model(new_model, ai_mode=current_mode if current_mode else None)
            
            logger.info(f"Ollama model updated to: {new_model} by user {request.user.username}")
            updated = True
        
        if not updated:
            return Response({'error': 'No valid settings to update'}, status=400)
        
        return Response({
            'success': True,
            'message': 'Settings updated successfully',
            'settings': _get_settings_snapshot()
        })
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def test_connection(request):
    """Test a connection (ollama or redis). Expects { type: 'ollama'|'redis', config?: {} }"""
    
    @api_view(['GET'])
    @permission_classes([IsAuthenticated])
    def health_check(request):
        """Comprehensive health check for all services"""
        health = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'services': {}
        }
        
        # Check PostgreSQL
        try:
            from django.db import connection
            connection.ensure_connection()
            health['services']['postgresql'] = {'status': 'healthy'}
        except Exception as e:
            health['status'] = 'degraded'
            health['services']['postgresql'] = {'status': 'unhealthy', 'error': str(e)[:100]}
        
        # Check Redis
        try:
            from django.core.cache import cache
            cache.set('health_check', 'ok', 10)
            if cache.get('health_check') == 'ok':
                health['services']['redis'] = {'status': 'healthy'}
            else:
                health['status'] = 'degraded'
                health['services']['redis'] = {'status': 'unhealthy', 'error': 'Cache test failed'}
        except Exception as e:
            health['status'] = 'degraded'
            health['services']['redis'] = {'status': 'unhealthy', 'error': str(e)[:100]}
        
        # Check Neo4j
        try:
            from ai_assistant.service_classes.neo4j_service import get_neo4j_service
            neo4j = get_neo4j_service()
            if neo4j.test_connection():
                stats = neo4j.get_graph_stats()
                health['services']['neo4j'] = {
                    'status': 'healthy',
                    'nodes': stats.get('nodes', 0),
                    'relationships': stats.get('relationships', 0)
                }
            else:
                health['status'] = 'degraded'
                health['services']['neo4j'] = {'status': 'unhealthy', 'error': 'Connection test failed'}
        except Exception as e:
            health['status'] = 'degraded'
            health['services']['neo4j'] = {'status': 'unhealthy', 'error': str(e)[:100]}
        
        status_code = 200 if health['status'] == 'healthy' else 503
        return Response(health, status=status_code)
    try:
        payload = request.data if isinstance(request.data, dict) else json.loads(request.body or '{}')
    except Exception:
        payload = {}

    conn_type = payload.get('type')
    config = payload.get('config', {})

    if conn_type == 'ollama':
        url = config.get('url') or getattr(dj_settings, 'OLLAMA_API_URL', 'http://ollama:11434')
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def switch_ai_mode(request):
    """Switch AI mode (performance/lightweight) for the current user.
    
    This updates both:
    1. Embedding service mode (for vector embeddings)
    2. Ollama model (for RAG query generation)
    """
    try:
        mode = request.data.get('mode')
        if mode not in ['performance', 'lightweight']:
            return Response(
                {'error': 'Invalid mode. Must be "performance" or "lightweight"'},
                status=400
            )
        
        # Update the global embedding service mode
        from ai_assistant.services import embedding_service
        embedding_success = embedding_service.switch_mode(mode)
        
        # Update Ollama model based on AI mode
        recommended_model = get_model_for_ai_mode(mode)
        
        # Validate the recommended model exists in Ollama
        ollama_url = getattr(dj_settings, 'OLLAMA_API_URL', 'http://ollama:11434')
        try:
            r = requests.get(f"{ollama_url}/api/tags", timeout=5)
            if r.status_code == 200:
                models_data = r.json().get('models', [])
                available_models = [tag.get('name', '') for tag in models_data]
                
                if recommended_model not in available_models:
                    # Try to find a similar model
                    model_family = recommended_model.split(':')[0]  # e.g., 'qwen2.5' or 'qwen2'
                    similar_models = [m for m in available_models if model_family in m or m.split(':')[0] in model_family]
                    
                    if similar_models:
                        # Use the first similar model found (prefer smaller for lightweight, larger for performance)
                        if mode == 'lightweight':
                            # Prefer smaller models (1.5b, 2b, etc.)
                            lightweight_models = [m for m in similar_models if any(size in m for size in ['1.5b', '2b', '3b'])]
                            if lightweight_models:
                                recommended_model = lightweight_models[0]
                            else:
                                recommended_model = similar_models[0]
                        else:
                            # Prefer larger models (7b, 8b, etc.)
                            performance_models = [m for m in similar_models if any(size in m for size in ['7b', '8b', '13b'])]
                            if performance_models:
                                recommended_model = performance_models[0]
                            else:
                                recommended_model = similar_models[0]
                        
                        logger.info(f"Model {get_model_for_ai_mode(mode)} not found, using similar model: {recommended_model}")
                    else:
                        logger.warning(f"Recommended model {recommended_model} not found and no similar models available. Available: {available_models}")
        except Exception as e:
            logger.warning(f"Could not validate model with Ollama: {e}. Proceeding with recommended model: {recommended_model}")
        
        set_ollama_model(recommended_model, ai_mode=mode)
        
        if embedding_success:
            logger.info(f"User {request.user.username} switched to {mode} mode (Ollama model: {recommended_model})")
            return Response({
                'success': True,
                'mode': mode,
                'ollama_model': recommended_model,
                'message': f'Switched to {mode} mode successfully. Ollama model set to {recommended_model}'
            })
        else:
            # Even if embedding switch fails, Ollama model was updated
            logger.warning(f"Embedding mode switch failed, but Ollama model updated to {recommended_model}")
            return Response({
                'success': True,
                'mode': mode,
                'ollama_model': recommended_model,
                'message': f'Ollama model set to {recommended_model}. Embedding mode switch may have failed.',
                'warning': 'Embedding mode switch failed, but Ollama model was updated'
            })
    except Exception as e:
        logger.error(f"Error switching AI mode: {e}")
        return Response(
            {'error': str(e)},
            status=500
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def health_check(request):
    """Comprehensive health check for all services"""
    health = {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'services': {}
    }
    
    # Check PostgreSQL
    try:
        from django.db import connection
        connection.ensure_connection()
        health['services']['postgresql'] = {'status': 'healthy'}
    except Exception as e:
        health['status'] = 'degraded'
        health['services']['postgresql'] = {'status': 'unhealthy', 'error': str(e)[:100]}
    
    # Check Redis
    try:
        from django.core.cache import cache
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            health['services']['redis'] = {'status': 'healthy'}
        else:
            health['status'] = 'degraded'
            health['services']['redis'] = {'status': 'unhealthy', 'error': 'Cache test failed'}
    except Exception as e:
        health['status'] = 'degraded'
        health['services']['redis'] = {'status': 'unhealthy', 'error': str(e)[:100]}
    
    # Check Neo4j
    try:
        from ai_assistant.service_classes.neo4j_service import get_neo4j_service
        neo4j = get_neo4j_service()
        if neo4j.test_connection():
            stats = neo4j.get_graph_stats()
            health['services']['neo4j'] = {
                'status': 'healthy',
                'nodes': stats.get('nodes', 0),
                'relationships': stats.get('relationships', 0)
            }
        else:
            health['status'] = 'degraded'
            health['services']['neo4j'] = {'status': 'unhealthy', 'error': 'Connection test failed'}
    except Exception as e:
        health['status'] = 'degraded'
        health['services']['neo4j'] = {'status': 'unhealthy', 'error': str(e)[:100]}
    
    status_code = 200 if health['status'] == 'healthy' else 503
    return Response(health, status=status_code)

    return Response({'ok': False, 'error': 'Unsupported type'}, status=400)


