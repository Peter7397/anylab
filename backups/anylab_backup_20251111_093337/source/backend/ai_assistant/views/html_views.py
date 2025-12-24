"""
HTML Views Module

This module contains all HTML parsing related views including
URL parsing, text parsing, and analytics.
"""

import logging
import json
from django.core.cache import cache
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from ..models import DocumentFile
from ..html_parser import HTMLParser, HTMLProcessor, HTMLParsingConfig
from .base_views import (
    BaseViewMixin, success_response, error_response, bad_request_response,
    internal_error_response
)

logger = logging.getLogger(__name__)

# Initialize HTML parser and processor
html_parser = HTMLParser()
html_processor = HTMLProcessor()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def parse_html_url(request):
    """Parse HTML content from a URL"""
    try:
        BaseViewMixin.log_request(request, 'parse_html_url')
        
        url = request.data.get('url')
        if not url:
            return bad_request_response('URL is required')
        
        # Get parsing configuration from request
        config_data = request.data.get('config', {})
        config = HTMLParsingConfig(
            timeout=config_data.get('timeout', 30),
            retry_attempts=config_data.get('retry_attempts', 3),
            min_content_length=config_data.get('min_content_length', 100),
            max_content_length=config_data.get('max_content_length', 1000000),
            extract_images=config_data.get('extract_images', True),
            extract_tables=config_data.get('extract_tables', True),
            extract_forms=config_data.get('extract_forms', True),
            extract_code=config_data.get('extract_code', True),
            extract_links=config_data.get('extract_links', True),
            clean_html=config_data.get('clean_html', True),
            remove_scripts=config_data.get('remove_scripts', True),
            remove_styles=config_data.get('remove_styles', True),
            remove_comments=config_data.get('remove_comments', True),
            preserve_structure=config_data.get('preserve_structure', True),
            language_detection=config_data.get('language_detection', True),
            content_classification=config_data.get('content_classification', True)
        )
        
        # Create parser with custom config
        parser = HTMLParser(config)
        
        # Parse HTML content
        logger.info(f"Parsing HTML content from {url}")
        html_content = parser.parse_url(url)
        
        if not html_content:
            return bad_request_response('Could not fetch or parse the URL')
        
        # Process HTML content
        logger.info(f"Processing HTML content from {url}")
        processing_result = html_processor.process_html_content(html_content)
        
        result = {
            'url': url,
            'html_content': {
                'title': html_content.title,
                'description': html_content.description,
                'content_length': len(html_content.clean_content),
                'language': html_content.language,
                'encoding': html_content.encoding,
                'content_type': html_content.content_type,
                'quality_score': html_content.quality_score,
                'relevance_score': html_content.relevance_score,
                'links_count': len(html_content.links),
                'images_count': len(html_content.images),
                'tables_count': len(html_content.tables),
                'headings_count': len(html_content.headings),
                'paragraphs_count': len(html_content.paragraphs),
                'lists_count': len(html_content.lists),
                'code_blocks_count': len(html_content.code_blocks),
                'forms_count': len(html_content.forms),
                'processing_metadata': html_content.processing_metadata
            },
            'processing_result': processing_result,
            'parsed_at': timezone.now().isoformat()
        }
        
        BaseViewMixin.log_response(result, 'parse_html_url')
        return success_response("HTML parsing completed successfully", result)
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'parse_html_url')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def parse_html_text(request):
    """Parse HTML content from text"""
    try:
        BaseViewMixin.log_request(request, 'parse_html_text')
        
        html_text = request.data.get('html_text')
        if not html_text:
            return bad_request_response('HTML text is required')
        
        url = request.data.get('url', '')
        
        # Get parsing configuration from request
        config_data = request.data.get('config', {})
        config = HTMLParsingConfig(
            timeout=config_data.get('timeout', 30),
            retry_attempts=config_data.get('retry_attempts', 3),
            min_content_length=config_data.get('min_content_length', 100),
            max_content_length=config_data.get('max_content_length', 1000000),
            extract_images=config_data.get('extract_images', True),
            extract_tables=config_data.get('extract_tables', True),
            extract_forms=config_data.get('extract_forms', True),
            extract_code=config_data.get('extract_code', True),
            extract_links=config_data.get('extract_links', True),
            clean_html=config_data.get('clean_html', True),
            remove_scripts=config_data.get('remove_scripts', True),
            remove_styles=config_data.get('remove_styles', True),
            remove_comments=config_data.get('remove_comments', True),
            preserve_structure=config_data.get('preserve_structure', True),
            language_detection=config_data.get('language_detection', True),
            content_classification=config_data.get('content_classification', True)
        )
        
        # Create parser with custom config
        parser = HTMLParser(config)
        
        # Parse HTML content
        logger.info("Parsing HTML content from text")
        html_content = parser.parse_html_text(html_text, url)
        
        if not html_content:
            return bad_request_response('Could not parse the HTML text')
        
        # Process HTML content
        logger.info("Processing HTML content from text")
        processing_result = html_processor.process_html_content(html_content)
        
        result = {
            'html_content': {
                'title': html_content.title,
                'description': html_content.description,
                'content_length': len(html_content.clean_content),
                'language': html_content.language,
                'encoding': html_content.encoding,
                'content_type': html_content.content_type,
                'quality_score': html_content.quality_score,
                'relevance_score': html_content.relevance_score,
                'links_count': len(html_content.links),
                'images_count': len(html_content.images),
                'tables_count': len(html_content.tables),
                'headings_count': len(html_content.headings),
                'paragraphs_count': len(html_content.paragraphs),
                'lists_count': len(html_content.lists),
                'code_blocks_count': len(html_content.code_blocks),
                'forms_count': len(html_content.forms),
                'processing_metadata': html_content.processing_metadata
            },
            'processing_result': processing_result,
            'parsed_at': timezone.now().isoformat()
        }
        
        BaseViewMixin.log_response(result, 'parse_html_text')
        return success_response("HTML parsing completed successfully", result)
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'parse_html_text')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_html_parsing_status(request):
    """Get current HTML parsing status and statistics"""
    try:
        BaseViewMixin.log_request(request, 'get_html_parsing_status')
        
        # Get HTML documents count
        html_documents = DocumentFile.objects.filter(document_type='HTML_PAGE')
        total_html_count = html_documents.count()
        
        # Get recent HTML documents
        recent_html = html_documents.order_by('-created_at')[:10]
        recent_html_data = [
            {
                'id': doc.id,
                'title': doc.title,
                'created_at': doc.created_at.isoformat() if doc.created_at else None,
                'metadata': json.loads(doc.metadata) if doc.metadata else {}
            }
            for doc in recent_html
        ]
        
        # Get HTML statistics
        html_stats = {
            'total_html_documents': total_html_count,
            'recent_html_documents': recent_html_data,
            'last_parsing_run': cache.get('last_html_parsing_run'),
            'parsing_in_progress': cache.get('html_parsing_in_progress', False)
        }
        
        BaseViewMixin.log_response(html_stats, 'get_html_parsing_status')
        return success_response("HTML parsing status retrieved successfully", html_stats)
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'get_html_parsing_status')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def schedule_html_parsing(request):
    """Schedule automatic HTML parsing"""
    try:
        BaseViewMixin.log_request(request, 'schedule_html_parsing')
        
        schedule_config = request.data.get('schedule', {})
        
        # Schedule configuration
        schedule_data = {
            'enabled': schedule_config.get('enabled', True),
            'frequency': schedule_config.get('frequency', 'daily'),  # daily, weekly, monthly
            'time': schedule_config.get('time', '05:00'),  # HH:MM format
            'urls': schedule_config.get('urls', []),
            'notify_on_completion': schedule_config.get('notify_on_completion', True)
        }
        
        # Store schedule in cache
        cache.set('html_parsing_schedule', schedule_data, 86400 * 30)  # 30 days
        
        BaseViewMixin.log_response(schedule_data, 'schedule_html_parsing')
        return success_response("HTML parsing schedule updated successfully", {'schedule': schedule_data})
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'schedule_html_parsing')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_html_parsing_schedule(request):
    """Get current HTML parsing schedule"""
    try:
        BaseViewMixin.log_request(request, 'get_html_parsing_schedule')
        
        schedule = cache.get('html_parsing_schedule', {
            'enabled': False,
            'frequency': 'daily',
            'time': '05:00',
            'urls': [],
            'notify_on_completion': True
        })
        
        BaseViewMixin.log_response(schedule, 'get_html_parsing_schedule')
        return success_response("HTML parsing schedule retrieved successfully", {'schedule': schedule})
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'get_html_parsing_schedule')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_html_parsing(request):
    """Test HTML parsing with a single URL"""
    try:
        BaseViewMixin.log_request(request, 'test_html_parsing')
        
        test_url = request.data.get('test_url')
        if not test_url:
            return bad_request_response('Test URL is required')
        
        # Create parser
        parser = HTMLParser()
        
        # Test parsing single URL
        html_content = parser.parse_url(test_url)
        if not html_content:
            return bad_request_response('Failed to parse HTML content')
        
        result = {
            'html_content': {
                'url': html_content.url,
                'title': html_content.title,
                'description': html_content.description,
                'content_length': len(html_content.clean_content),
                'language': html_content.language,
                'encoding': html_content.encoding,
                'content_type': html_content.content_type,
                'quality_score': html_content.quality_score,
                'relevance_score': html_content.relevance_score,
                'links_count': len(html_content.links),
                'images_count': len(html_content.images),
                'tables_count': len(html_content.tables),
                'headings_count': len(html_content.headings),
                'paragraphs_count': len(html_content.paragraphs),
                'lists_count': len(html_content.lists),
                'code_blocks_count': len(html_content.code_blocks),
                'forms_count': len(html_content.forms),
                'processing_metadata': html_content.processing_metadata
            }
        }
        
        BaseViewMixin.log_response(result, 'test_html_parsing')
        return success_response("HTML parsing test successful", result)
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'test_html_parsing')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_html_analytics(request):
    """Get analytics for HTML content"""
    try:
        BaseViewMixin.log_request(request, 'get_html_analytics')
        
        # Get HTML documents count
        html_documents = DocumentFile.objects.filter(document_type='HTML_PAGE')
        total_html_count = html_documents.count()
        
        # Get domain distribution
        domain_stats = {}
        for doc in html_documents:
            if doc.metadata:
                try:
                    metadata = json.loads(doc.metadata)
                    domain = metadata.get('domain', 'Unknown')
                    domain_stats[domain] = domain_stats.get(domain, 0) + 1
                except (json.JSONDecodeError, TypeError):
                    continue
        
        # Get content type distribution
        content_type_stats = {}
        for doc in html_documents:
            if doc.metadata:
                try:
                    metadata = json.loads(doc.metadata)
                    content_type = metadata.get('content_type', 'Unknown')
                    content_type_stats[content_type] = content_type_stats.get(content_type, 0) + 1
                except (json.JSONDecodeError, TypeError):
                    continue
        
        # Get recent HTML documents
        recent_html = html_documents.order_by('-created_at')[:10]
        recent_html_data = [
            {
                'id': doc.id,
                'title': doc.title,
                'created_at': doc.created_at.isoformat() if doc.created_at else None,
                'metadata': json.loads(doc.metadata) if doc.metadata else {}
            }
            for doc in recent_html
        ]
        
        # Get HTML statistics
        html_stats = {
            'total_html_documents': total_html_count,
            'domain_distribution': domain_stats,
            'content_type_distribution': content_type_stats,
            'recent_html_documents': recent_html_data,
            'last_parsing_run': cache.get('last_html_parsing_run'),
            'parsing_in_progress': cache.get('html_parsing_in_progress', False)
        }
        
        BaseViewMixin.log_response(html_stats, 'get_html_analytics')
        return success_response("HTML analytics retrieved successfully", html_stats)
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'get_html_analytics')
