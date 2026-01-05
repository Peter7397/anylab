"""
Request Logging Middleware for Debugging

This middleware logs all incoming requests, especially POST requests with file uploads,
to help debug upload issues. Also provides request tracing with correlation IDs.
"""

import logging
import time
import uuid
import threading
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('ai_assistant.middleware.request_logging')

# Thread-local storage for request context
_request_context = threading.local()


def get_correlation_id() -> str:
    """
    Get the current request's correlation ID from thread-local storage.
    Returns 'unknown' if not in a request context (e.g., in Celery tasks).
    """
    return getattr(_request_context, 'correlation_id', 'unknown')


def get_request_id() -> str:
    """
    Alias for get_correlation_id() for consistency.
    Returns the correlation ID for the current request.
    """
    return get_correlation_id()


class RequestLoggingMiddleware(MiddlewareMixin):
    """Log all requests for debugging purposes"""
    
    def process_request(self, request):
        """Log incoming request details with correlation ID for tracing"""
        # Generate correlation ID for request tracing
        # Accept correlation ID from client header, or generate new one
        correlation_id = request.META.get('HTTP_X_CORRELATION_ID') or str(uuid.uuid4())
        request.correlation_id = correlation_id
        request.request_id = correlation_id  # Alias for consistency
        
        # Store in thread-local for access in views/services/tasks
        _request_context.correlation_id = correlation_id
        _request_context.request_id = correlation_id
        
        # Also store in thread object for backward compatibility
        if not hasattr(threading.current_thread(), 'request_context'):
            threading.current_thread().request_context = {}
        threading.current_thread().request_context['correlation_id'] = correlation_id
        threading.current_thread().request_context['request_id'] = correlation_id
        
        # Only log POST/PUT requests to reduce noise
        if request.method in ['POST', 'PUT', 'PATCH']:
            # Log request details with correlation ID
            logger.info(
                f"[{correlation_id[:8]}] [REQUEST] {request.method} {request.path} | "
                f"User: {request.user if hasattr(request, 'user') else 'Anonymous'} | "
                f"Content-Type: {request.content_type} | "
                f"FILES: {list(request.FILES.keys()) if hasattr(request, 'FILES') else 'N/A'} | "
                f"POST keys: {list(request.POST.keys()) if hasattr(request, 'POST') else 'N/A'}"
            )
            
            # Log file details if present
            if hasattr(request, 'FILES') and request.FILES:
                for key, file in request.FILES.items():
                    logger.info(
                        f"[{correlation_id[:8]}] [FILE] {key}: name={file.name}, size={file.size}, "
                        f"content_type={file.content_type}"
                    )
        
        # Store start time for duration calculation
        request._start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Log response details with correlation ID"""
        correlation_id = getattr(request, 'correlation_id', 'unknown')
        
        # Log all requests (not just POST/PUT/PATCH) for better tracing
        duration = time.time() - getattr(request, '_start_time', 0)
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            logger.info(
                f"[{correlation_id[:8]}] [RESPONSE] {request.method} {request.path} | "
                f"Status: {response.status_code} | "
                f"Duration: {duration:.3f}s"
            )
        else:
            # Log GET requests at debug level to reduce noise
            logger.debug(
                f"[{correlation_id[:8]}] [RESPONSE] {request.method} {request.path} | "
                f"Status: {response.status_code} | "
                f"Duration: {duration:.3f}s"
            )
        
        # Always add correlation ID to response headers for client tracing
        response['X-Correlation-ID'] = correlation_id
        response['X-Request-ID'] = correlation_id  # Alias for consistency
        
        # Clean up thread-local storage after request
        if hasattr(_request_context, 'correlation_id'):
            delattr(_request_context, 'correlation_id')
        if hasattr(_request_context, 'request_id'):
            delattr(_request_context, 'request_id')
        
        return response
    
    def process_exception(self, request, exception):
        """Log exceptions with correlation ID"""
        correlation_id = getattr(request, 'correlation_id', 'unknown')
        logger.error(
            f"[{correlation_id[:8]}] [EXCEPTION] {request.method} {request.path} | "
            f"Exception: {type(exception).__name__}: {str(exception)}",
            exc_info=True,
            extra={'correlation_id': correlation_id, 'request_id': correlation_id}
        )
        return None

