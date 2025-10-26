"""
Test Configuration and Base Classes

This module provides base test classes and configuration for AI Assistant tests.
"""

import os
import json
import tempfile
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
import logging

# Disable logging during tests
logging.disable(logging.CRITICAL)


class BaseAIAssistantTestCase(TestCase):
    """Base test case for AI Assistant tests"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
    
    def create_test_file(self, filename='test.pdf', content=b'Test PDF content'):
        """Create a test file"""
        return SimpleUploadedFile(filename, content, content_type='application/pdf')
    
    def login_user(self, user=None):
        """Login a user"""
        if user is None:
            user = self.user
        self.client.force_login(user)
        return user


class BaseAIAssistantAPITestCase(APITestCase):
    """Base API test case for AI Assistant tests"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
    
    def authenticate_user(self, user=None):
        """Authenticate a user"""
        if user is None:
            user = self.user
        self.client.force_authenticate(user=user)
        return user
    
    def create_test_file(self, filename='test.pdf', content=b'Test PDF content'):
        """Create a test file"""
        return SimpleUploadedFile(filename, content, content_type='application/pdf')
    
    def assert_success_response(self, response, expected_message=None):
        """Assert that response is successful"""
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if expected_message:
            self.assertIn(expected_message, response.data.get('message', ''))
    
    def assert_error_response(self, response, expected_status=status.HTTP_400_BAD_REQUEST):
        """Assert that response is an error"""
        self.assertEqual(response.status_code, expected_status)
        self.assertIn('error', response.data)
    
    def assert_unauthorized_response(self, response):
        """Assert that response is unauthorized"""
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MockServiceMixin:
    """Mixin for mocking services in tests"""
    
    def mock_rag_service(self, return_data=None):
        """Mock RAG service"""
        if return_data is None:
            return_data = {
                'success': True,
                'message': 'Test response',
                'data': {'response': 'Test response'}
            }
        
        with patch('ai_assistant.services.rag_service.RAGService') as mock_service:
            mock_instance = MagicMock()
            mock_instance.chat_with_ollama.return_value = return_data
            mock_instance.rag_search.return_value = return_data
            mock_instance.vector_search.return_value = return_data
            mock_service.return_value = mock_instance
            return mock_instance
    
    def mock_ssb_service(self, return_data=None):
        """Mock SSB service"""
        if return_data is None:
            return_data = {
                'success': True,
                'message': 'SSB scraping completed',
                'data': {'scraped_count': 10}
            }
        
        with patch('ai_assistant.services.ssb_service.SSBService') as mock_service:
            mock_instance = MagicMock()
            mock_instance.scrape_ssb_database.return_value = return_data
            mock_instance.get_ssb_scraping_status.return_value = return_data
            mock_service.return_value = mock_instance
            return mock_instance
    
    def mock_content_service(self, return_data=None):
        """Mock Content service"""
        if return_data is None:
            return_data = {
                'success': True,
                'message': 'Content filtered',
                'data': {'documents': []}
            }
        
        with patch('ai_assistant.services.content_service.ContentService') as mock_service:
            mock_instance = MagicMock()
            mock_instance.filter_documents.return_value = return_data
            mock_instance.get_filter_suggestions.return_value = return_data
            mock_service.return_value = mock_instance
            return mock_instance


class TestDataFactory:
    """Factory for creating test data"""
    
    @staticmethod
    def create_user(username='testuser', email='test@example.com', password='testpass123'):
        """Create a test user"""
        return User.objects.create_user(username=username, email=email, password=password)
    
    @staticmethod
    def create_admin_user(username='admin', email='admin@example.com', password='adminpass123'):
        """Create a test admin user"""
        return User.objects.create_superuser(username=username, email=email, password=password)
    
    @staticmethod
    def create_test_file(filename='test.pdf', content=b'Test PDF content'):
        """Create a test file"""
        return SimpleUploadedFile(filename, content, content_type='application/pdf')
    
    @staticmethod
    def create_chat_request_data(prompt='Test prompt'):
        """Create chat request data"""
        return {
            'prompt': prompt,
            'max_tokens': 256,
            'temperature': 0.3
        }
    
    @staticmethod
    def create_search_request_data(query='Test query'):
        """Create search request data"""
        return {
            'query': query,
            'search_mode': 'comprehensive',
            'top_k': 10
        }
    
    @staticmethod
    def create_filter_request_data():
        """Create filter request data"""
        return {
            'query': 'Test query',
            'organization_mode': 'general',
            'filters': [
                {
                    'field': 'document_type',
                    'operator': 'eq',
                    'value': 'PDF'
                }
            ],
            'sort_order': 'relevance',
            'page': 1,
            'page_size': 20
        }
    
    @staticmethod
    def create_scraping_config_data():
        """Create scraping configuration data"""
        return {
            'config': {
                'max_pages': 10,
                'delay_between_requests': 1.0,
                'timeout': 30,
                'retry_attempts': 3
            }
        }
