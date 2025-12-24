"""
Base Service Module

This module provides the base service class that other services can inherit from.
"""

import logging
from typing import Dict, Any, List, Optional
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


class BaseService:
    """Base service class for all AI assistant services"""
    
    def __init__(self):
        """Initialize base service"""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def log_operation(self, operation: str, details: Dict[str, Any] = None):
        """Log service operation"""
        log_data = {
            'service': self.__class__.__name__,
            'operation': operation,
            'timestamp': timezone.now().isoformat()
        }
        if details:
            log_data.update(details)
        
        self.logger.info(f"Service operation: {operation}", extra=log_data)
    
    def log_error(self, operation: str, error: Exception, details: Dict[str, Any] = None):
        """Log service error"""
        error_msg = f"Error in {self.__class__.__name__}: {operation} Context: {str(error)}"
        if details:
            error_msg += f" Details: {details}"
        self.logger.error(error_msg)
    
    def cache_result(self, key: str, data: Any, timeout: int = 3600):
        """Cache service result"""
        cache.set(key, data, timeout)
        self.logger.debug(f"Cached result for key: {key}")
    
    def get_cached_result(self, key: str) -> Optional[Any]:
        """Get cached service result"""
        result = cache.get(key)
        if result:
            self.logger.debug(f"Retrieved cached result for key: {key}")
        return result
    
    def success_response(self, message: str, data: Any = None) -> Dict[str, Any]:
        """Create success response"""
        return {
            'success': True,
            'message': message,
            'data': data,
            'timestamp': timezone.now().isoformat()
        }
    
    def error_response(self, message: str, errors: List[str] = None) -> Dict[str, Any]:
        """Create error response"""
        response = {
            'success': False,
            'message': message,
            'timestamp': timezone.now().isoformat()
        }
        if errors:
            response['errors'] = errors
        return response
    
    def validate_input(self, data: Dict[str, Any], required_fields: List[str]) -> tuple[bool, Optional[str]]:
        """Validate input data"""
        for field in required_fields:
            if field not in data or not data[field]:
                return False, f"Missing required field: {field}"
        return True, None

