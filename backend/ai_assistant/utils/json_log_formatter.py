"""
JSON Log Formatter for Structured Logging

This module provides a JSON formatter for structured logging that is compatible
with log aggregation systems like ELK stack, Loki, etc.
"""

import json
import logging
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
from ai_assistant.middleware.request_logging import get_correlation_id


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    
    Formats log records as JSON with standard fields:
    - timestamp: ISO 8601 formatted timestamp
    - level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - logger: Logger name
    - message: Log message
    - module: Module name
    - function: Function name
    - line: Line number
    - correlation_id: Request correlation ID (if available)
    - exception: Exception details (if present)
    - extra: Additional context fields
    """
    
    def __init__(self, include_correlation_id: bool = True, **kwargs):
        """
        Initialize JSON formatter.
        
        Args:
            include_correlation_id: Whether to include correlation ID in logs
            **kwargs: Additional arguments passed to parent Formatter
        """
        super().__init__(**kwargs)
        self.include_correlation_id = include_correlation_id
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON string.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON string representation of log record
        """
        # Base log data
        log_data: Dict[str, Any] = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add correlation ID if available and enabled
        if self.include_correlation_id:
            correlation_id = get_correlation_id()
            if correlation_id != 'unknown':
                log_data['correlation_id'] = correlation_id
        
        # Add process and thread information
        log_data['process_id'] = record.process
        log_data['thread_id'] = record.thread
        log_data['thread_name'] = record.threadName
        
        # Add exception information if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': self.formatException(record.exc_info),
            }
        
        # Add extra fields from record
        if hasattr(record, 'extra') and record.extra:
            log_data['extra'] = record.extra
        else:
            # Extract extra fields from record attributes
            extra_fields = {}
            for key, value in record.__dict__.items():
                if key not in [
                    'name', 'msg', 'args', 'created', 'filename', 'funcName',
                    'levelname', 'levelno', 'lineno', 'module', 'msecs',
                    'message', 'pathname', 'process', 'processName', 'relativeCreated',
                    'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info',
                    'asctime', 'correlation_id', 'request_id'
                ]:
                    # Only include serializable values
                    try:
                        json.dumps(value)
                        extra_fields[key] = value
                    except (TypeError, ValueError):
                        extra_fields[key] = str(value)
            
            if extra_fields:
                log_data['extra'] = extra_fields
        
        # Add request-specific fields if available
        if hasattr(record, 'request_path'):
            log_data['request_path'] = record.request_path
        if hasattr(record, 'request_method'):
            log_data['request_method'] = record.request_method
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'ip_address'):
            log_data['ip_address'] = record.ip_address
        
        # Convert to JSON string
        try:
            return json.dumps(log_data, ensure_ascii=False, default=str)
        except (TypeError, ValueError) as e:
            # Fallback to simple format if JSON serialization fails
            return json.dumps({
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'error': f'JSON serialization failed: {str(e)}',
            }, ensure_ascii=False)


class StructuredLoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that adds structured context to log records.
    
    Usage:
        logger = StructuredLoggerAdapter(logging.getLogger(__name__), {'component': 'file_processor'})
        logger.info('Processing file', extra={'file_id': 123, 'filename': 'test.pdf'})
    """
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """
        Process log message and add context.
        
        Args:
            msg: Log message
            kwargs: Keyword arguments (may contain 'extra' dict)
            
        Returns:
            Tuple of (message, kwargs) with context added
        """
        # Add context from adapter
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        
        # Merge adapter context
        kwargs['extra'].update(self.extra)
        
        return msg, kwargs

