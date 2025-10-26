"""
SSB Service Module

This module provides service layer for SSB (Service Support Bulletin)
operations including scraping, processing, and status monitoring.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from django.utils import timezone

from .base_service import BaseService
from ..models import DocumentFile
from ..ssb_scraper import SSBScraper, SSBProcessor, ScrapingConfig

logger = logging.getLogger(__name__)


class SSBService(BaseService):
    """Service for SSB operations"""
    
    def __init__(self):
        super().__init__()
        self.ssb_scraper = SSBScraper()
        self.ssb_processor = SSBProcessor()
    
    def scrape_ssb_database(self, config_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Scrape SSB database and process entries"""
        try:
            self.log_operation('scrape_ssb_database', {'config': config_data})
            
            # Create scraping configuration
            config = ScrapingConfig(
                max_pages=config_data.get('max_pages', 100) if config_data else 100,
                delay_between_requests=config_data.get('delay_between_requests', 1.0) if config_data else 1.0,
                timeout=config_data.get('timeout', 30) if config_data else 30,
                retry_attempts=config_data.get('retry_attempts', 3) if config_data else 3
            )
            
            # Create scraper with custom config
            scraper = SSBScraper(config)
            
            # Scrape SSB entries
            ssb_entries = scraper.scrape_all_ssbs()
            
            if not ssb_entries:
                return self.success_response("No SSB entries found", {
                    'scraped_count': 0,
                    'processed_count': 0
                })
            
            # Process SSB entries
            processing_results = self.ssb_processor.process_ssb_entries(ssb_entries)
            
            result = {
                'scraped_count': len(ssb_entries),
                'processing_results': processing_results,
                'scraped_at': timezone.now().isoformat()
            }
            
            return self.success_response("SSB scraping completed successfully", result)
            
        except Exception as e:
            self.log_error('scrape_ssb_database', e)
            return self.error_response('Failed to scrape SSB database')
    
    def scrape_openlab_help_portal(self, config_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Scrape OpenLab Help Portal for troubleshooting information"""
        try:
            self.log_operation('scrape_openlab_help_portal', {'config': config_data})
            
            # Create scraping configuration
            config = ScrapingConfig(
                openlab_help_url=config_data.get('openlab_help_url', 'https://openlab.help.agilent.com/en/index.htm') if config_data else 'https://openlab.help.agilent.com/en/index.htm',
                max_pages=config_data.get('max_pages', 50) if config_data else 50,
                delay_between_requests=config_data.get('delay_between_requests', 1.0) if config_data else 1.0
            )
            
            # Create scraper with custom config
            scraper = SSBScraper(config)
            
            # Scrape help portal
            help_entries = scraper.scrape_openlab_help_portal()
            
            if not help_entries:
                return self.success_response("No help portal entries found", {
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
                    self.logger.error(f"Error processing help entry {entry['title']}: {e}")
                    continue
            
            result = {
                'scraped_count': len(help_entries),
                'processed_count': processed_count,
                'scraped_at': timezone.now().isoformat()
            }
            
            return self.success_response("OpenLab Help Portal scraping completed successfully", result)
            
        except Exception as e:
            self.log_error('scrape_openlab_help_portal', e)
            return self.error_response('Failed to scrape OpenLab Help Portal')
    
    def get_ssb_scraping_status(self) -> Dict[str, Any]:
        """Get current SSB scraping status and statistics"""
        try:
            self.log_operation('get_ssb_scraping_status')
            
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
                'last_scraping_run': self.get_cached_result('last_ssb_scraping_run'),
                'scraping_in_progress': self.get_cached_result('ssb_scraping_in_progress') or False
            }
            
            return self.success_response("SSB scraping status retrieved successfully", ssb_stats)
            
        except Exception as e:
            self.log_error('get_ssb_scraping_status', e)
            return self.error_response('Failed to get SSB scraping status')
    
    def schedule_ssb_scraping(self, schedule_config: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule automatic SSB scraping"""
        try:
            self.log_operation('schedule_ssb_scraping', {'schedule': schedule_config})
            
            # Schedule configuration
            schedule_data = {
                'enabled': schedule_config.get('enabled', True),
                'frequency': schedule_config.get('frequency', 'daily'),
                'time': schedule_config.get('time', '02:00'),
                'max_pages': schedule_config.get('max_pages', 100),
                'notify_on_completion': schedule_config.get('notify_on_completion', True)
            }
            
            # Store schedule in cache
            self.cache_result('ssb_scraping_schedule', schedule_data, 86400 * 30)  # 30 days
            
            return self.success_response("SSB scraping schedule updated successfully", {
                'schedule': schedule_data
            })
            
        except Exception as e:
            self.log_error('schedule_ssb_scraping', e)
            return self.error_response('Failed to schedule SSB scraping')
    
    def get_ssb_scraping_schedule(self) -> Dict[str, Any]:
        """Get current SSB scraping schedule"""
        try:
            self.log_operation('get_ssb_scraping_schedule')
            
            schedule = self.get_cached_result('ssb_scraping_schedule') or {
                'enabled': False,
                'frequency': 'daily',
                'time': '02:00',
                'max_pages': 100,
                'notify_on_completion': True
            }
            
            return self.success_response("SSB scraping schedule retrieved successfully", {
                'schedule': schedule
            })
            
        except Exception as e:
            self.log_error('get_ssb_scraping_schedule', e)
            return self.error_response('Failed to get SSB scraping schedule')
    
    def test_ssb_scraping(self, test_url: str) -> Dict[str, Any]:
        """Test SSB scraping with a single entry"""
        try:
            self.log_operation('test_ssb_scraping', {'test_url': test_url})
            
            if not test_url:
                return self.error_response('Test URL is required')
            
            # Create scraper
            scraper = SSBScraper()
            
            # Test scraping single URL
            html_content = scraper._fetch_page(test_url)
            if not html_content:
                return self.error_response('Failed to fetch test URL')
            
            # Parse the page
            ssb_entry = scraper._parse_ssb_page(html_content, test_url)
            if not ssb_entry:
                return self.error_response('Failed to parse SSB page')
            
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
            
            return self.success_response("SSB scraping test successful", result)
            
        except Exception as e:
            self.log_error('test_ssb_scraping', e)
            return self.error_response('Failed to test SSB scraping')
