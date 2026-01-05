"""
Structured Logging Utilities
Provides consistent, structured logging across all services
"""
import logging
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime
from functools import wraps


class StructuredLogger:
    """
    Structured logger that outputs JSON-formatted logs
    Makes logs easier to parse and analyze
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.name = name
    
    def _create_log_entry(
        self,
        level: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None,
        duration_ms: Optional[float] = None
    ) -> Dict[str, Any]:
        """Create structured log entry"""
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level,
            'logger': self.name,
            'message': message,
            **(context or {})
        }
        
        if error:
            entry['error'] = {
                'type': type(error).__name__,
                'message': str(error),
                'traceback': None  # Can be added if needed
            }
        
        if duration_ms is not None:
            entry['duration_ms'] = duration_ms
        
        return entry
    
    def info(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log info message with context"""
        entry = self._create_log_entry('INFO', message, context, **kwargs)
        self.logger.info(json.dumps(entry))
    
    def warning(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log warning message with context"""
        entry = self._create_log_entry('WARNING', message, context, **kwargs)
        self.logger.warning(json.dumps(entry))
    
    def error(self, message: str, context: Optional[Dict[str, Any]] = None, error: Optional[Exception] = None, **kwargs):
        """Log error message with context"""
        entry = self._create_log_entry('ERROR', message, context, error=error, **kwargs)
        self.logger.error(json.dumps(entry))
    
    def debug(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log debug message with context"""
        entry = self._create_log_entry('DEBUG', message, context, **kwargs)
        self.logger.debug(json.dumps(entry))
    
    def critical(self, message: str, context: Optional[Dict[str, Any]] = None, error: Optional[Exception] = None, **kwargs):
        """Log critical message with context"""
        entry = self._create_log_entry('CRITICAL', message, context, error=error, **kwargs)
        self.logger.critical(json.dumps(entry))
    
    def log_operation(
        self,
        operation: str,
        context: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None
    ):
        """Log operation with standardized format"""
        op_context = {'operation': operation, **(context or {})}
        if duration_ms is not None:
            op_context['duration_ms'] = duration_ms
        self.info(f"Operation: {operation}", context=op_context)
    
    def log_performance(
        self,
        operation: str,
        duration_ms: float,
        metrics: Optional[Dict[str, Any]] = None
    ):
        """Log performance metrics"""
        context = {
            'operation': operation,
            'duration_ms': duration_ms,
            'performance': True,
            **(metrics or {})
        }
        self.info(f"Performance: {operation}", context=context)


def get_structured_logger(name: str) -> StructuredLogger:
    """Get or create structured logger"""
    return StructuredLogger(name)


def log_execution_time(operation_name: str = None):
    """
    Decorator to log execution time of functions
    
    Usage:
        @log_execution_time("embedding_generation")
        def generate_embedding(text):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or func.__name__
            logger = get_structured_logger(func.__module__)
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                logger.log_performance(op_name, duration_ms, {'success': True})
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.log_performance(op_name, duration_ms, {'success': False, 'error': str(e)})
                raise
        
        return wrapper
    return decorator


# Standard log levels for different scenarios
class LogLevel:
    """Standard log levels for consistency"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL
    
    # Standardized levels for common operations
    OPERATION_START = logging.INFO
    OPERATION_SUCCESS = logging.INFO
    OPERATION_FAILURE = logging.ERROR
    PERFORMANCE = logging.INFO
    CACHE_HIT = logging.DEBUG
    CACHE_MISS = logging.DEBUG
    EXTERNAL_API_CALL = logging.INFO
    EXTERNAL_API_ERROR = logging.ERROR

