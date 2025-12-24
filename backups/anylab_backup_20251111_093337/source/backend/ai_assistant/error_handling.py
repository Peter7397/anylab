"""
Error Handling Module

This module provides comprehensive error handling for the AI Assistant application.
"""

import logging
import traceback
from typing import Dict, Any, Optional, List
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException, ValidationError, PermissionDenied, NotFound
import requests
import json

logger = logging.getLogger(__name__)


class AIAssistantException(APIException):
    """Base exception class for AI Assistant"""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'An error occurred in the AI Assistant'
    default_code = 'ai_assistant_error'


class RAGServiceException(AIAssistantException):
    """Exception for RAG service errors"""
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'RAG service is currently unavailable'
    default_code = 'rag_service_error'


class ScrapingException(AIAssistantException):
    """Exception for scraping errors"""
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = 'Scraping service failed'
    default_code = 'scraping_error'


class ValidationException(AIAssistantException):
    """Exception for validation errors"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Validation failed'
    default_code = 'validation_error'


class AuthenticationException(AIAssistantException):
    """Exception for authentication errors"""
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Authentication required'
    default_code = 'authentication_error'


class PermissionException(AIAssistantException):
    """Exception for permission errors"""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'Permission denied'
    default_code = 'permission_error'


class NotFoundException(AIAssistantException):
    """Exception for not found errors"""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Resource not found'
    default_code = 'not_found_error'


class RateLimitException(AIAssistantException):
    """Exception for rate limit errors"""
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = 'Rate limit exceeded'
    default_code = 'rate_limit_error'


class ExternalServiceException(AIAssistantException):
    """Exception for external service errors"""
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = 'External service unavailable'
    default_code = 'external_service_error'


class ErrorHandler:
    """Comprehensive error handler for AI Assistant"""
    
    @staticmethod
    def handle_exception(exc, context=None):
        """Handle exceptions with proper logging and response formatting"""
        logger.error(f"Exception occurred: {str(exc)}", exc_info=True)
        
        # Get the exception handler from DRF
        response = exception_handler(exc, context)
        
        if response is not None:
            # Customize the error response
            custom_response_data = {
                'error': {
                    'type': exc.__class__.__name__,
                    'message': str(exc),
                    'code': getattr(exc, 'default_code', 'unknown_error'),
                    'timestamp': timezone.now().isoformat(),
                    'details': getattr(exc, 'details', None)
                }
            }
            
            # Add traceback in development
            if hasattr(exc, 'traceback') and exc.traceback:
                custom_response_data['error']['traceback'] = exc.traceback
            
            response.data = custom_response_data
            
        return response
    
    @staticmethod
    def handle_rag_error(error: Exception, context: str = None) -> Response:
        """Handle RAG service specific errors"""
        logger.error(f"RAG service error: {str(error)}", exc_info=True)
        
        if isinstance(error, requests.exceptions.Timeout):
            return Response({
                'error': {
                    'type': 'RAGTimeoutError',
                    'message': 'RAG service request timed out',
                    'code': 'rag_timeout',
                    'timestamp': timezone.now().isoformat(),
                    'suggestion': 'Please try again with a shorter query or check if the RAG service is running'
                }
            }, status=status.HTTP_408_REQUEST_TIMEOUT)
        
        elif isinstance(error, requests.exceptions.ConnectionError):
            return Response({
                'error': {
                    'type': 'RAGConnectionError',
                    'message': 'Cannot connect to RAG service',
                    'code': 'rag_connection_error',
                    'timestamp': timezone.now().isoformat(),
                    'suggestion': 'Please check if the RAG service is running and accessible'
                }
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        else:
            return Response({
                'error': {
                    'type': 'RAGServiceError',
                    'message': 'RAG service error occurred',
                    'code': 'rag_service_error',
                    'timestamp': timezone.now().isoformat(),
                    'details': str(error)
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staticmethod
    def handle_scraping_error(error: Exception, context: str = None) -> Response:
        """Handle scraping specific errors"""
        logger.error(f"Scraping error: {str(error)}", exc_info=True)
        
        if isinstance(error, requests.exceptions.Timeout):
            return Response({
                'error': {
                    'type': 'ScrapingTimeoutError',
                    'message': 'Scraping request timed out',
                    'code': 'scraping_timeout',
                    'timestamp': timezone.now().isoformat(),
                    'suggestion': 'Please try again or check if the target website is accessible'
                }
            }, status=status.HTTP_408_REQUEST_TIMEOUT)
        
        elif isinstance(error, requests.exceptions.ConnectionError):
            return Response({
                'error': {
                    'type': 'ScrapingConnectionError',
                    'message': 'Cannot connect to target website',
                    'code': 'scraping_connection_error',
                    'timestamp': timezone.now().isoformat(),
                    'suggestion': 'Please check if the target website is accessible'
                }
            }, status=status.HTTP_502_BAD_GATEWAY)
        
        else:
            return Response({
                'error': {
                    'type': 'ScrapingError',
                    'message': 'Scraping error occurred',
                    'code': 'scraping_error',
                    'timestamp': timezone.now().isoformat(),
                    'details': str(error)
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staticmethod
    def handle_validation_error(error: Exception, context: str = None) -> Response:
        """Handle validation specific errors"""
        logger.error(f"Validation error: {str(error)}", exc_info=True)
        
        if isinstance(error, ValidationError):
            return Response({
                'error': {
                    'type': 'ValidationError',
                    'message': 'Validation failed',
                    'code': 'validation_error',
                    'timestamp': timezone.now().isoformat(),
                    'details': error.detail
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        else:
            return Response({
                'error': {
                    'type': 'ValidationError',
                    'message': 'Validation error occurred',
                    'code': 'validation_error',
                    'timestamp': timezone.now().isoformat(),
                    'details': str(error)
                }
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @staticmethod
    def handle_authentication_error(error: Exception, context: str = None) -> Response:
        """Handle authentication specific errors"""
        logger.error(f"Authentication error: {str(error)}", exc_info=True)
        
        return Response({
            'error': {
                'type': 'AuthenticationError',
                'message': 'Authentication required',
                'code': 'authentication_error',
                'timestamp': timezone.now().isoformat(),
                'suggestion': 'Please log in to access this resource'
            }
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    @staticmethod
    def handle_permission_error(error: Exception, context: str = None) -> Response:
        """Handle permission specific errors"""
        logger.error(f"Permission error: {str(error)}", exc_info=True)
        
        return Response({
            'error': {
                'type': 'PermissionError',
                'message': 'Permission denied',
                'code': 'permission_error',
                'timestamp': timezone.now().isoformat(),
                'suggestion': 'You do not have permission to access this resource'
            }
        }, status=status.HTTP_403_FORBIDDEN)
    
    @staticmethod
    def handle_not_found_error(error: Exception, context: str = None) -> Response:
        """Handle not found specific errors"""
        logger.error(f"Not found error: {str(error)}", exc_info=True)
        
        return Response({
            'error': {
                'type': 'NotFoundError',
                'message': 'Resource not found',
                'code': 'not_found_error',
                'timestamp': timezone.now().isoformat(),
                'suggestion': 'Please check if the resource exists or try a different search'
            }
        }, status=status.HTTP_404_NOT_FOUND)
    
    @staticmethod
    def handle_rate_limit_error(error: Exception, context: str = None) -> Response:
        """Handle rate limit specific errors"""
        logger.error(f"Rate limit error: {str(error)}", exc_info=True)
        
        return Response({
            'error': {
                'type': 'RateLimitError',
                'message': 'Rate limit exceeded',
                'code': 'rate_limit_error',
                'timestamp': timezone.now().isoformat(),
                'suggestion': 'Please wait before making another request'
            }
        }, status=status.HTTP_429_TOO_MANY_REQUESTS)
    
    @staticmethod
    def handle_external_service_error(error: Exception, context: str = None) -> Response:
        """Handle external service specific errors"""
        logger.error(f"External service error: {str(error)}", exc_info=True)
        
        return Response({
            'error': {
                'type': 'ExternalServiceError',
                'message': 'External service unavailable',
                'code': 'external_service_error',
                'timestamp': timezone.now().isoformat(),
                'suggestion': 'Please try again later or contact support'
            }
        }, status=status.HTTP_502_BAD_GATEWAY)
    
    @staticmethod
    def handle_generic_error(error: Exception, context: str = None) -> Response:
        """Handle generic errors"""
        logger.error(f"Generic error: {str(error)}", exc_info=True)
        
        return Response({
            'error': {
                'type': 'GenericError',
                'message': 'An unexpected error occurred',
                'code': 'generic_error',
                'timestamp': timezone.now().isoformat(),
                'details': str(error),
                'suggestion': 'Please try again or contact support if the problem persists'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def custom_exception_handler(exc, context):
    """Custom exception handler for AI Assistant"""
    handler = ErrorHandler()
    
    # Handle specific exception types
    if isinstance(exc, RAGServiceException):
        return handler.handle_rag_error(exc, context)
    elif isinstance(exc, ScrapingException):
        return handler.handle_scraping_error(exc, context)
    elif isinstance(exc, ValidationException):
        return handler.handle_validation_error(exc, context)
    elif isinstance(exc, AuthenticationException):
        return handler.handle_authentication_error(exc, context)
    elif isinstance(exc, PermissionException):
        return handler.handle_permission_error(exc, context)
    elif isinstance(exc, NotFoundException):
        return handler.handle_not_found_error(exc, context)
    elif isinstance(exc, RateLimitException):
        return handler.handle_rate_limit_error(exc, context)
    elif isinstance(exc, ExternalServiceException):
        return handler.handle_external_service_error(exc, context)
    else:
        return handler.handle_exception(exc, context)
