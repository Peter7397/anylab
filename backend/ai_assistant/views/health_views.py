"""
Health check API views.
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from django.core.cache import cache
from django.conf import settings
import requests
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
def health_check(request):
    """
    Basic health check endpoint.
    
    Returns:
        200 OK if system is healthy
        503 Service Unavailable if any critical service is down
    """
    try:
        # Check database
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Check cache
        cache.set('health_check', 'ok', 10)
        cache_ok = cache.get('health_check') == 'ok'
        
        if cache_ok:
            return Response({
                'status': 'healthy',
                'database': 'ok',
                'cache': 'ok'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'status': 'degraded',
                'database': 'ok',
                'cache': 'error'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
    except Exception as e:
        logger.error(f'Health check failed: {e}')
        return Response({
            'status': 'unhealthy',
            'error': str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
def health_detailed(request):
    """
    Detailed health check endpoint with all service statuses.
    
    Returns:
        200 OK with detailed status of all services
    """
    health_status = {
        'status': 'healthy',
        'services': {},
        'timestamp': None
    }
    
    from django.utils import timezone
    health_status['timestamp'] = timezone.now().isoformat()
    
    overall_healthy = True
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            # Check pgvector extension
            cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')")
            pgvector_exists = cursor.fetchone()[0]
            
        health_status['services']['database'] = {
            'status': 'ok',
            'pgvector': 'enabled' if pgvector_exists else 'disabled'
        }
    except Exception as e:
        health_status['services']['database'] = {
            'status': 'error',
            'error': str(e)
        }
        overall_healthy = False
    
    # Cache check
    try:
        cache.set('health_check_detailed', 'ok', 10)
        cache_ok = cache.get('health_check_detailed') == 'ok'
        health_status['services']['cache'] = {
            'status': 'ok' if cache_ok else 'error'
        }
        if not cache_ok:
            overall_healthy = False
    except Exception as e:
        health_status['services']['cache'] = {
            'status': 'error',
            'error': str(e)
        }
        overall_healthy = False
    
    # Ollama check
    try:
        ollama_url = getattr(settings, 'OLLAMA_URL', 'http://localhost:11434')
        response = requests.get(f'{ollama_url}/api/tags', timeout=5)
        if response.status_code == 200:
            health_status['services']['ollama'] = {
                'status': 'ok',
                'url': ollama_url
            }
        else:
            health_status['services']['ollama'] = {
                'status': 'error',
                'http_status': response.status_code
            }
            overall_healthy = False
    except Exception as e:
        health_status['services']['ollama'] = {
            'status': 'error',
            'error': str(e)
        }
        overall_healthy = False
    
    # Processor status
    try:
        from ai_assistant.processors.metadata import MetadataExtractor
        from ai_assistant.processors.chunking import PDFChunker
        from ai_assistant.processors.embeddings import EmbeddingGenerator
        
        health_status['services']['processors'] = {
            'status': 'ok',
            'modules': ['metadata', 'chunking', 'embeddings']
        }
    except Exception as e:
        health_status['services']['processors'] = {
            'status': 'error',
            'error': str(e)
        }
        overall_healthy = False
    
    # Update overall status
    if not overall_healthy:
        health_status['status'] = 'degraded'
    
    http_status = status.HTTP_200_OK if overall_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return Response(health_status, status=http_status)


@api_view(['GET'])
def health_processors(request):
    """
    Health check specifically for processor modules.
    
    Returns:
        200 OK with processor module status
    """
    processors_status = {
        'status': 'healthy',
        'modules': {}
    }
    
    overall_healthy = True
    
    # Check each processor module
    modules_to_check = {
        'metadata': 'ai_assistant.processors.metadata',
        'chunking': 'ai_assistant.processors.chunking',
        'ocr': 'ai_assistant.processors.ocr',
        'embeddings': 'ai_assistant.processors.embeddings',
    }
    
    for module_name, module_path in modules_to_check.items():
        try:
            __import__(module_path)
            processors_status['modules'][module_name] = {
                'status': 'ok',
                'imported': True
            }
        except Exception as e:
            processors_status['modules'][module_name] = {
                'status': 'error',
                'imported': False,
                'error': str(e)
            }
            overall_healthy = False
    
    if not overall_healthy:
        processors_status['status'] = 'degraded'
    
    http_status = status.HTTP_200_OK if overall_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return Response(processors_status, status=http_status)

