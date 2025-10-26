"""
SSB Views Module

This module contains all SSB (Service Support Bulletin) scraper related views
including database scraping, help portal integration, and status monitoring.
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
from ..ssb_scraper import SSBScraper, SSBProcessor, ScrapingConfig
from .base_views import (
    BaseViewMixin, success_response, error_response, bad_request_response,
    internal_error_response
)

logger = logging.getLogger(__name__)

# Initialize SSB scraper and processor
ssb_scraper = SSBScraper()
ssb_processor = SSBProcessor()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def scrape_ssb_database(request):
    """Scrape SSB database and process entries"""
    try:
        BaseViewMixin.log_request(request, 'scrape_ssb_database')
        
        # Get scraping configuration from request
        config_data = request.data.get('config', {})
        config = ScrapingConfig(
            max_pages=config_data.get('max_pages', 100),
            delay_between_requests=config_data.get('delay_between_requests', 1.0),
            timeout=config_data.get('timeout', 30),
            retry_attempts=config_data.get('retry_attempts', 3)
        )
        
        # Create scraper with custom config
        scraper = SSBScraper(config)
        
        # Scrape SSB entries
        logger.info("Starting SSB database scraping")
        ssb_entries = scraper.scrape_all_ssbs()
        
        if not ssb_entries:
            return success_response("No SSB entries found", {
                'scraped_count': 0,
                'processed_count': 0
            })
        
        # Process SSB entries
        logger.info(f"Processing {len(ssb_entries)} SSB entries")
        processing_results = ssb_processor.process_ssb_entries(ssb_entries)
        
        result = {
            'scraped_count': len(ssb_entries),
            'processing_results': processing_results,
            'scraped_at': timezone.now().isoformat()
        }
        
        BaseViewMixin.log_response(result, 'scrape_ssb_database')
        return success_response("SSB scraping completed successfully", result)
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'scrape_ssb_database')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def scrape_openlab_help_portal(request):
    """Scrape OpenLab Help Portal for troubleshooting information"""
    try:
        BaseViewMixin.log_request(request, 'scrape_openlab_help_portal')
        
        # Get scraping configuration from request
        config_data = request.data.get('config', {})
        config = ScrapingConfig(
            openlab_help_url=config_data.get('openlab_help_url', 'https://openlab.help.agilent.com/en/index.htm'),
            max_pages=config_data.get('max_pages', 50),
            delay_between_requests=config_data.get('delay_between_requests', 1.0)
        )
        
        # Create scraper with custom config
        scraper = SSBScraper(config)
        
        # Scrape help portal
        logger.info("Starting OpenLab Help Portal scraping")
        help_entries = scraper.scrape_openlab_help_portal()
        
        if not help_entries:
            return success_response("No help portal entries found", {
                'scraped_count': 0
            })
        
        # Process help entries into documents
        processed_count = 0
        for entry in help_entries:
            try:
                # Create document from help entry
                document = DocumentFile.objects.create(
                    title=entry['title'],
                    filename=f"Help_{hashlib.md5(entry['title'].encode()).hexdigest()[:8]}.html",
                    file_type="HTML",
                    file_size=len(entry['content']),
                    description=entry['content'][:200],
                    document_type="TROUBLESHOOTING_GUIDE",
                    metadata=json.dumps({
                        'source_url': entry['url'],
                        'type': entry['type'],
                        'category': entry['category'],
                        'scraped_at': timezone.now().isoformat(),
                        'organization_mode': 'lab-informatics',
                        'content_category': 'troubleshooting'
                    }),
                    uploaded_by=None,
                    page_count=1
                )
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing help entry {entry['title']}: {e}")
                continue
        
        result = {
            'scraped_count': len(help_entries),
            'processed_count': processed_count,
            'scraped_at': timezone.now().isoformat()
        }
        
        BaseViewMixin.log_response(result, 'scrape_openlab_help_portal')
        return success_response("OpenLab Help Portal scraping completed successfully", result)
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'scrape_openlab_help_portal')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ssb_scraping_status(request):
    """Get current SSB scraping status and statistics"""
    try:
        BaseViewMixin.log_request(request, 'get_ssb_scraping_status')
        
        # Get SSB documents count
        ssb_documents = DocumentFile.objects.filter(document_type='SSB_KPR')
        total_ssb_count = ssb_documents.count()
        
        # Get recent SSB documents
        recent_ssb = ssb_documents.order_by('-created_at')[:10]
        recent_ssb_data = [
            {
                'id': doc.id,
                'title': doc.title,
                'created_at': doc.created_at.isoformat() if doc.created_at else None,
                'metadata': json.loads(doc.metadata) if doc.metadata else {}
            }
            for doc in recent_ssb
        ]
        
        # Get SSB statistics
        ssb_stats = {
            'total_ssb_documents': total_ssb_count,
            'recent_ssb_documents': recent_ssb_data,
            'last_scraping_run': cache.get('last_ssb_scraping_run'),
            'scraping_in_progress': cache.get('ssb_scraping_in_progress', False)
        }
        
        BaseViewMixin.log_response(ssb_stats, 'get_ssb_scraping_status')
        return success_response("SSB scraping status retrieved successfully", ssb_stats)
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'get_ssb_scraping_status')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def schedule_ssb_scraping(request):
    """Schedule automatic SSB scraping"""
    try:
        BaseViewMixin.log_request(request, 'schedule_ssb_scraping')
        
        schedule_config = request.data.get('schedule', {})
        
        # Schedule configuration
        schedule_data = {
            'enabled': schedule_config.get('enabled', True),
            'frequency': schedule_config.get('frequency', 'daily'),  # daily, weekly, monthly
            'time': schedule_config.get('time', '02:00'),  # HH:MM format
            'max_pages': schedule_config.get('max_pages', 100),
            'notify_on_completion': schedule_config.get('notify_on_completion', True)
        }
        
        # Store schedule in cache
        cache.set('ssb_scraping_schedule', schedule_data, 86400 * 30)  # 30 days
        
        BaseViewMixin.log_response(schedule_data, 'schedule_ssb_scraping')
        return success_response("SSB scraping schedule updated successfully", {'schedule': schedule_data})
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'schedule_ssb_scraping')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ssb_scraping_schedule(request):
    """Get current SSB scraping schedule"""
    try:
        BaseViewMixin.log_request(request, 'get_ssb_scraping_schedule')
        
        schedule = cache.get('ssb_scraping_schedule', {
            'enabled': False,
            'frequency': 'daily',
            'time': '02:00',
            'max_pages': 100,
            'notify_on_completion': True
        })
        
        BaseViewMixin.log_response(schedule, 'get_ssb_scraping_schedule')
        return success_response("SSB scraping schedule retrieved successfully", {'schedule': schedule})
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'get_ssb_scraping_schedule')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_ssb_scraping(request):
    """Test SSB scraping with a single entry"""
    try:
        BaseViewMixin.log_request(request, 'test_ssb_scraping')
        
        test_url = request.data.get('test_url')
        if not test_url:
            return bad_request_response('Test URL is required')
        
        # Create scraper
        scraper = SSBScraper()
        
        # Test scraping single URL
        html_content = scraper._fetch_page(test_url)
        if not html_content:
            return bad_request_response('Failed to fetch test URL')
        
        # Parse the page
        ssb_entry = scraper._parse_ssb_page(html_content, test_url)
        if not ssb_entry:
            return bad_request_response('Failed to parse SSB page')
        
        result = {
            'ssb_entry': {
                'kpr_number': ssb_entry.kpr_number,
                'title': ssb_entry.title,
                'description': ssb_entry.description,
                'severity': ssb_entry.severity.value if ssb_entry.severity else 'unknown',
                'software_platform': ssb_entry.software_platform,
                'software_version': ssb_entry.software_version,
                'status': ssb_entry.status,
                'url': ssb_entry.url,
                'metadata': ssb_entry.metadata
            }
        }
        
        BaseViewMixin.log_response(result, 'test_ssb_scraping')
        return success_response("SSB scraping test successful", result)
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'test_ssb_scraping')
