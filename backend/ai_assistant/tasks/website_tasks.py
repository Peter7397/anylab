"""
Website processing Celery tasks.
"""

import logging
from celery import shared_task
from ..models import WebsiteSource

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name='ai_assistant.tasks.process_website_automatically',
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
def process_website_automatically(self, website_source_id):
    """
    Background task for automatic website processing
    
    QUALITY FOCUS: Uses website processor with full quality guarantees
    - HTML fetching and parsing
    - Conversion to UploadedFile format
    - Integration with AutomaticFileProcessor
    - Same chunking and embedding standards
    - 3 retry attempts (Celery-level) + 3 attempts (process-level) = up to 9 total
    """
    try:
        logger.info(f'Processing website {website_source_id} in background (attempt {self.request.retries + 1})')
        
        # Use the website processor with all quality guarantees
        from ..website_processor import website_processor
        result = website_processor.process_website_fully(website_source_id)
        
        logger.info(f'Website {website_source_id} processed successfully: {result}')
        
        return {
            'status': 'success',
            'website_source_id': website_source_id,
            'result': result
        }
        
    except Exception as e:
        logger.error(f'Background website processing failed for {website_source_id}: {e}', exc_info=True)
        
        # Mark current attempt status in database
        try:
            website_source = WebsiteSource.objects.get(id=website_source_id)
            website_source.processing_error = f"Attempt {self.request.retries + 1} failed: {str(e)}"
            website_source.save()
        except WebsiteSource.DoesNotExist:
            logger.error(f'WebsiteSource {website_source_id} not found')
        
        # Let Celery handle retry (with autoretry_for)
        raise


@shared_task(name='ai_assistant.tasks.refresh_expired_websites')
def refresh_expired_websites():
    """
    Refresh websites that have expired (older than configured TTL)
    
    Runs periodically to refresh website content
    """
    try:
        from django.utils import timezone
        from datetime import timedelta
        from django.conf import settings
        
        # Get TTL from settings (default 7 days)
        ttl_days = getattr(settings, 'WEBSITE_REFRESH_TTL_DAYS', 7)
        cutoff = timezone.now() - timedelta(days=ttl_days)
        
        # Find expired websites
        expired_websites = WebsiteSource.objects.filter(
            last_refreshed_at__lt=cutoff,
            is_active=True
        )
        
        refreshed_count = 0
        for website in expired_websites:
            try:
                logger.info(f'Refreshing expired website: {website.id} ({website.url})')
                process_website_automatically.delay(website.id)
                refreshed_count += 1
            except Exception as e:
                logger.error(f'Error queuing refresh for website {website.id}: {e}')
        
        if refreshed_count > 0:
            logger.info(f'Queued refresh for {refreshed_count} expired websites')
        
        return {
            'status': 'success',
            'refreshed': refreshed_count
        }
    except Exception as e:
        logger.error(f'Error refreshing expired websites: {e}', exc_info=True)
        return {'status': 'error', 'message': str(e)}

