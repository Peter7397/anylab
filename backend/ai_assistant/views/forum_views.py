"""
Forum Views Module

This module contains all forum integration related views including
community forum scraping, status monitoring, and analytics.
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
from ..forum_integration import ForumScraper, ForumProcessor, ForumConfig
from .base_views import (
    BaseViewMixin, success_response, error_response, bad_request_response,
    internal_error_response
)

logger = logging.getLogger(__name__)

# Initialize Forum scraper and processor
forum_scraper = ForumScraper()
forum_processor = ForumProcessor()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def scrape_forum_posts(request):
    """Scrape community forum posts and process them"""
    try:
        BaseViewMixin.log_request(request, 'scrape_forum_posts')
        
        # Get scraping configuration from request
        config_data = request.data.get('config', {})
        config = ForumConfig(
            forum_urls=config_data.get('forum_urls', [
                "https://community.agilent.com",
                "https://forums.agilent.com"
            ]),
            max_posts_per_forum=config_data.get('max_posts_per_forum', 1000),
            delay_between_requests=config_data.get('delay_between_requests', 2.0),
            timeout=config_data.get('timeout', 30),
            retry_attempts=config_data.get('retry_attempts', 3),
            min_content_length=config_data.get('min_content_length', 100),
            min_author_reputation=config_data.get('min_author_reputation', 10)
        )
        
        # Create scraper with custom config
        scraper = ForumScraper(config)
        
        # Scrape forum posts
        logger.info("Starting forum posts scraping")
        forum_posts = scraper.scrape_all_forums()
        
        if not forum_posts:
            return success_response("No forum posts found", {
                'scraped_count': 0,
                'processed_count': 0
            })
        
        # Process forum posts
        logger.info(f"Processing {len(forum_posts)} forum posts")
        processing_results = forum_processor.process_forum_posts(forum_posts)
        
        result = {
            'scraped_count': len(forum_posts),
            'processing_results': processing_results,
            'scraped_at': timezone.now().isoformat()
        }
        
        BaseViewMixin.log_response(result, 'scrape_forum_posts')
        return success_response("Forum scraping completed successfully", result)
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'scrape_forum_posts')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_forum_scraping_status(request):
    """Get current forum scraping status and statistics"""
    try:
        BaseViewMixin.log_request(request, 'get_forum_scraping_status')
        
        # Get forum documents count
        forum_documents = DocumentFile.objects.filter(document_type='COMMUNITY_SOLUTION')
        total_forum_count = forum_documents.count()
        
        # Get recent forum documents
        recent_forum = forum_documents.order_by('-created_at')[:10]
        recent_forum_data = [
            {
                'id': doc.id,
                'title': doc.title,
                'created_at': doc.created_at.isoformat() if doc.created_at else None,
                'metadata': json.loads(doc.metadata) if doc.metadata else {}
            }
            for doc in recent_forum
        ]
        
        # Get forum statistics
        forum_stats = {
            'total_forum_documents': total_forum_count,
            'recent_forum_documents': recent_forum_data,
            'last_scraping_run': cache.get('last_forum_scraping_run'),
            'scraping_in_progress': cache.get('forum_scraping_in_progress', False)
        }
        
        BaseViewMixin.log_response(forum_stats, 'get_forum_scraping_status')
        return success_response("Forum scraping status retrieved successfully", forum_stats)
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'get_forum_scraping_status')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def schedule_forum_scraping(request):
    """Schedule automatic forum scraping"""
    try:
        BaseViewMixin.log_request(request, 'schedule_forum_scraping')
        
        schedule_config = request.data.get('schedule', {})
        
        # Schedule configuration
        schedule_data = {
            'enabled': schedule_config.get('enabled', True),
            'frequency': schedule_config.get('frequency', 'weekly'),  # daily, weekly, monthly
            'time': schedule_config.get('time', '03:00'),  # HH:MM format
            'max_posts_per_forum': schedule_config.get('max_posts_per_forum', 1000),
            'notify_on_completion': schedule_config.get('notify_on_completion', True)
        }
        
        # Store schedule in cache
        cache.set('forum_scraping_schedule', schedule_data, 86400 * 30)  # 30 days
        
        BaseViewMixin.log_response(schedule_data, 'schedule_forum_scraping')
        return success_response("Forum scraping schedule updated successfully", {'schedule': schedule_data})
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'schedule_forum_scraping')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_forum_scraping_schedule(request):
    """Get current forum scraping schedule"""
    try:
        BaseViewMixin.log_request(request, 'get_forum_scraping_schedule')
        
        schedule = cache.get('forum_scraping_schedule', {
            'enabled': False,
            'frequency': 'weekly',
            'time': '03:00',
            'max_posts_per_forum': 1000,
            'notify_on_completion': True
        })
        
        BaseViewMixin.log_response(schedule, 'get_forum_scraping_schedule')
        return success_response("Forum scraping schedule retrieved successfully", {'schedule': schedule})
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'get_forum_scraping_schedule')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_forum_scraping(request):
    """Test forum scraping with a single post"""
    try:
        BaseViewMixin.log_request(request, 'test_forum_scraping')
        
        test_url = request.data.get('test_url')
        if not test_url:
            return bad_request_response('Test URL is required')
        
        # Create scraper
        scraper = ForumScraper()
        
        # Test scraping single URL
        html_content = scraper._fetch_page(test_url)
        if not html_content:
            return bad_request_response('Failed to fetch test URL')
        
        # Parse the page
        forum_post = scraper._parse_forum_post(html_content, test_url, test_url)
        if not forum_post:
            return bad_request_response('Failed to parse forum post')
        
        result = {
            'forum_post': {
                'post_id': forum_post.post_id,
                'title': forum_post.title,
                'author': forum_post.author,
                'author_reputation': forum_post.author_reputation,
                'views': forum_post.views,
                'replies': forum_post.replies,
                'likes': forum_post.likes,
                'is_solution': forum_post.is_solution,
                'solution_rating': forum_post.solution_rating,
                'related_software': forum_post.related_software,
                'related_issues': forum_post.related_issues,
                'metadata': forum_post.metadata
            }
        }
        
        BaseViewMixin.log_response(result, 'test_forum_scraping')
        return success_response("Forum scraping test successful", result)
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'test_forum_scraping')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_community_analytics(request):
    """Get analytics for community forum content"""
    try:
        BaseViewMixin.log_request(request, 'get_community_analytics')
        
        # Get community documents count
        community_documents = DocumentFile.objects.filter(document_type='COMMUNITY_SOLUTION')
        total_community_count = community_documents.count()
        
        # Get solution statistics
        solution_documents = community_documents.filter(metadata__icontains='"is_solution": true')
        solution_count = solution_documents.count()
        
        # Get recent community documents
        recent_community = community_documents.order_by('-created_at')[:10]
        recent_community_data = [
            {
                'id': doc.id,
                'title': doc.title,
                'created_at': doc.created_at.isoformat() if doc.created_at else None,
                'metadata': json.loads(doc.metadata) if doc.metadata else {}
            }
            for doc in recent_community
        ]
        
        # Get community statistics
        community_stats = {
            'total_community_documents': total_community_count,
            'solution_documents': solution_count,
            'solution_percentage': (solution_count / total_community_count * 100) if total_community_count > 0 else 0,
            'recent_community_documents': recent_community_data,
            'last_scraping_run': cache.get('last_forum_scraping_run'),
            'scraping_in_progress': cache.get('forum_scraping_in_progress', False)
        }
        
        BaseViewMixin.log_response(community_stats, 'get_community_analytics')
        return success_response("Community analytics retrieved successfully", community_stats)
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'get_community_analytics')
