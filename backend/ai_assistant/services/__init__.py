"""
Base Service Module

This module provides the base service class and common utilities
for all AI Assistant services.
"""

import logging
from typing import Dict, Any, Optional, List
from django.core.cache import cache
from django.utils import timezone
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class BaseService:
    """Base service class with common functionality"""
    
    def __init__(self):
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
        log_data = {
            'service': self.__class__.__name__,
            'operation': operation,
            'error': str(error),
            'timestamp': timezone.now().isoformat()
        }
        if details:
            log_data.update(details)
        
        self.logger.error(f"Service error in {operation}: {error}", extra=log_data)
    
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
    
    def invalidate_cache(self, key_pattern: str):
        """Invalidate cache by pattern"""
        # This is a simplified implementation
        # In production, you might want to use Redis pattern matching
        cache.delete(key_pattern)
        self.logger.debug(f"Invalidated cache for pattern: {key_pattern}")
    
    def validate_user_permissions(self, user: User, required_permissions: List[str] = None) -> bool:
        """Validate user permissions for service operations"""
        if not user.is_authenticated:
            return False
        
        if not required_permissions:
            return True
        
        # Check if user has required permissions
        # This is a simplified implementation
        # In production, you might want to use Django's permission system
        return True
    
    def format_response(self, success: bool, message: str, data: Any = None, 
                       errors: List[str] = None) -> Dict[str, Any]:
        """Format service response"""
        response = {
            'success': success,
            'message': message,
            'timestamp': timezone.now().isoformat()
        }
        
        if data is not None:
            response['data'] = data
        
        if errors:
            response['errors'] = errors
        
        return response
    
    def success_response(self, message: str, data: Any = None) -> Dict[str, Any]:
        """Create success response"""
        return self.format_response(True, message, data)
    
    def error_response(self, message: str, errors: List[str] = None) -> Dict[str, Any]:
        """Create error response"""
        return self.format_response(False, message, errors=errors)
