"""
Base Views Module

This module provides common utilities and base classes for all AI Assistant views.
"""

import logging
import json
from typing import Dict, Any, Optional, List
from django.http import JsonResponse
from django.core.cache import cache
from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView

logger = logging.getLogger(__name__)


class BaseViewMixin:
    """Base mixin for common view functionality"""
    
    @staticmethod
    def log_request(request, view_name: str):
        """Log incoming request"""
        logger.info(f"{view_name} - User: {request.user}, Method: {request.method}")
    
    @staticmethod
    def log_response(response_data: Dict[str, Any], view_name: str):
        """Log outgoing response"""
        logger.info(f"{view_name} - Response: {response_data.get('message', 'No message')}")
    
    @staticmethod
    def handle_error(error: Exception, view_name: str) -> Response:
        """Handle common errors"""
        logger.error(f"{view_name} - Error: {str(error)}")
        return Response({'error': str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: list) -> Optional[str]:
        """Validate required fields in request data"""
        for field in required_fields:
            if field not in data or not data[field]:
                return f"Field '{field}' is required"
        return None


class BaseAPIView(APIView):
    """Base API view class with common functionality"""
    
    permission_classes = [IsAuthenticated]
    
    def log_request(self, request, view_name: str = None):
        """Log incoming request"""
        view_name = view_name or self.__class__.__name__
        logger.info(f"{view_name} - User: {request.user}, Method: {request.method}")
    
    def log_response(self, response_data: Dict[str, Any], view_name: str = None):
        """Log outgoing response"""
        view_name = view_name or self.__class__.__name__
        logger.info(f"{view_name} - Response: {response_data.get('message', 'No message')}")
    
    def handle_error(self, error: Exception, view_name: str = None) -> Response:
        """Handle common errors"""
        view_name = view_name or self.__class__.__name__
        logger.error(f"{view_name} - Error: {str(error)}")
        return Response({'error': str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def validate_required_fields(self, data: Dict[str, Any], required_fields: list) -> Optional[str]:
        """Validate required fields in request data"""
        for field in required_fields:
            if field not in data or not data[field]:
                return f"Field '{field}' is required"
        return None


class BaseGenericAPIView(GenericAPIView):
    """Base generic API view class with common functionality"""
    
    permission_classes = [IsAuthenticated]
    
    def log_request(self, request, view_name: str = None):
        """Log incoming request"""
        view_name = view_name or self.__class__.__name__
        logger.info(f"{view_name} - User: {request.user}, Method: {request.method}")
    
    def log_response(self, response_data: Dict[str, Any], view_name: str = None):
        """Log outgoing response"""
        view_name = view_name or self.__class__.__name__
        logger.info(f"{view_name} - Response: {response_data.get('message', 'No message')}")
    
    def handle_error(self, error: Exception, view_name: str = None) -> Response:
        """Handle common errors"""
        view_name = view_name or self.__class__.__name__
        logger.error(f"{view_name} - Error: {str(error)}")
        return Response({'error': str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def validate_required_fields(self, data: Dict[str, Any], required_fields: list) -> Optional[str]:
        """Validate required fields in request data"""
        for field in required_fields:
            if field not in data or not data[field]:
                return f"Field '{field}' is required"
        return None


class BaseServiceView(BaseAPIView):
    """Base view class that uses service layer"""
    
    def get_service(self):
        """Get the service instance for this view"""
        raise NotImplementedError("Subclasses must implement get_service method")
    
    def post(self, request, *args, **kwargs):
        """Handle POST requests"""
        try:
            self.log_request(request)
            service = self.get_service()
            result = service.handle_request(request.data, request.user, **kwargs)
            
            if result['success']:
                self.log_response(result, 'post')
                return success_response(result['message'], result.get('data'))
            else:
                return error_response(result['message'])
                
        except Exception as e:
            return self.handle_error(e, 'post')
    
    def get(self, request, *args, **kwargs):
        """Handle GET requests"""
        try:
            self.log_request(request)
            service = self.get_service()
            result = service.handle_request(request.GET, request.user, **kwargs)
            
            if result['success']:
                self.log_response(result, 'get')
                return success_response(result['message'], result.get('data'))
            else:
                return error_response(result['message'])
                
        except Exception as e:
            return self.handle_error(e, 'get')


class BaseScrapingView(BaseAPIView):
    """Base view class for scraping operations"""
    
    def get_scraper(self):
        """Get the scraper instance for this view"""
        raise NotImplementedError("Subclasses must implement get_scraper method")
    
    def post(self, request, *args, **kwargs):
        """Handle scraping POST requests"""
        try:
            self.log_request(request)
            scraper = self.get_scraper()
            config_data = request.data.get('config', {})
            result = scraper.scrape(config_data)
            
            if result['success']:
                self.log_response(result, 'scrape')
                return success_response(result['message'], result.get('data'))
            else:
                return error_response(result['message'])
                
        except Exception as e:
            return self.handle_error(e, 'scrape')


class BaseStatusView(BaseAPIView):
    """Base view class for status monitoring"""
    
    def get_status_service(self):
        """Get the status service instance for this view"""
        raise NotImplementedError("Subclasses must implement get_status_service method")
    
    def get(self, request, *args, **kwargs):
        """Handle status GET requests"""
        try:
            self.log_request(request)
            status_service = self.get_status_service()
            result = status_service.get_status()
            
            if result['success']:
                self.log_response(result, 'status')
                return success_response(result['message'], result.get('data'))
            else:
                return error_response(result['message'])
                
        except Exception as e:
            return self.handle_error(e, 'status')


def api_response(message: str, data: Dict[str, Any] = None, status_code: int = 200) -> Response:
    """Create standardized API response"""
    response_data = {
        'message': message,
        'timestamp': timezone.now().isoformat()
    }
    
    if data:
        response_data.update(data)
    
    return Response(response_data, status=status_code)


def error_response(error_message: str, status_code: int = 400) -> Response:
    """Create standardized error response"""
    return Response({
        'error': error_message,
        'timestamp': timezone.now().isoformat()
    }, status=status_code)


def success_response(message: str, data: Dict[str, Any] = None) -> Response:
    """Create standardized success response"""
    return api_response(message, data, status.HTTP_200_OK)


def created_response(message: str, data: Dict[str, Any] = None) -> Response:
    """Create standardized created response"""
    return api_response(message, data, status.HTTP_201_CREATED)


def not_found_response(message: str = "Resource not found") -> Response:
    """Create standardized not found response"""
    return error_response(message, status.HTTP_404_NOT_FOUND)


def bad_request_response(message: str) -> Response:
    """Create standardized bad request response"""
    return error_response(message, status.HTTP_400_BAD_REQUEST)


def unauthorized_response(message: str = "Authentication required") -> Response:
    """Create standardized unauthorized response"""
    return error_response(message, status.HTTP_401_UNAUTHORIZED)


def forbidden_response(message: str = "Permission denied") -> Response:
    """Create standardized forbidden response"""
    return error_response(message, status.HTTP_403_FORBIDDEN)


def internal_error_response(message: str = "Internal server error") -> Response:
    """Create standardized internal error response"""
    return error_response(message, status.HTTP_500_INTERNAL_SERVER_ERROR)
