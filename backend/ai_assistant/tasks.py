"""
Celery tasks for AI Assistant operations including SSB scraping.
"""

import logging
from celery import shared_task
from django.core.management import call_command
from django.utils import timezone
from django.core.cache import cache
from .models import DocumentFile

logger = logging.getLogger(__name__)


@shared_task(bind=True, name='ai_assistant.tasks.scrape_ssb_weekly')
def scrape_ssb_weekly(self):
    """
    Automatically scrape SSB database weekly.
    Runs every Sunday at 2:00 AM UTC.
    """
    try:
        logger.info('Starting weekly SSB scraping task')
        
        # Mark scraping in progress
        cache.set('ssb_scraping_in_progress', True, 7200)  # 2 hours
        
        # Call the management command
        result = call_command('scrape_ssb', '--full', verbosity=0)
        
        # Get statistics
        ssb_docs = DocumentFile.objects.filter(document_type='SSB_KPR')
        total_count = ssb_docs.count()
        recent_count = ssb_docs.filter(
            created_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).count()
        
        # Store last scraping run timestamp
        cache.set('last_ssb_scraping_run', timezone.now().isoformat(), 604800)  # 7 days
        
        logger.info(f'Weekly SSB scraping completed: {total_count} total SSBs, {recent_count} new')
        
        return {
            'status': 'success',
            'total_ssbs': total_count,
            'new_ssbs': recent_count,
            'completed_at': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f'SSB scraping task failed: {e}', exc_info=True)
        
        # Mark scraping failed
        cache.set('ssb_scraping_in_progress', False, 300)  # 5 minutes
        
        raise
    
    finally:
        # Mark scraping complete
        cache.set('ssb_scraping_in_progress', False, 300)  # 5 minutes


@shared_task(bind=True, name='ai_assistant.tasks.scrape_ssb_on_demand')
def scrape_ssb_on_demand(self, max_pages=100, scrapers=['database', 'help-portal']):
    """
    On-demand SSB scraping task triggered from UI or API.
    
    Args:
        max_pages: Maximum number of pages to scrape
        scrapers: List of scrapers to run ['database', 'help-portal']
    """
    try:
        logger.info(f'Starting on-demand SSB scraping: max_pages={max_pages}, scrapers={scrapers}')
        
        # Mark scraping in progress
        cache.set('ssb_scraping_in_progress', True, 7200)
        
        # Build command arguments
        args = []
        if max_pages:
            args.extend(['--max-pages', str(max_pages)])
        
        if 'database' in scrapers and 'help-portal' in scrapers:
            args.append('--full')
        elif 'help-portal' in scrapers:
            args.append('--help-portal')
        
        # Call the management command
        call_command('scrape_ssb', *args, verbosity=1)
        
        # Get statistics
        ssb_docs = DocumentFile.objects.filter(document_type='SSB_KPR')
        total_count = ssb_docs.count()
        
        # Store results
        cache.set('last_ssb_scraping_run', timezone.now().isoformat(), 604800)
        cache.set('last_ssb_scraping_result', {
            'status': 'success',
            'total_ssbs': total_count,
            'completed_at': timezone.now().isoformat(),
            'max_pages': max_pages,
            'scrapers': scrapers
        }, 86400)  # 24 hours
        
        logger.info(f'On-demand SSB scraping completed: {total_count} total SSBs')
        
        return {
            'status': 'success',
            'total_ssbs': total_count,
            'completed_at': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f'On-demand SSB scraping failed: {e}', exc_info=True)
        
        # Store error
        cache.set('last_ssb_scraping_result', {
            'status': 'error',
            'error': str(e),
            'completed_at': timezone.now().isoformat()
        }, 86400)
        
        raise
    
    finally:
        cache.set('ssb_scraping_in_progress', False, 300)


@shared_task(name='ai_assistant.tasks.process_document_queue')
def process_document_queue():
    """
    Process pending documents in the queue.
    This is called periodically by Celery Beat.
    """
    try:
        # Get pending documents
        pending_docs = DocumentFile.objects.filter(
            processed=False
        ).order_by('created_at')[:10]
        
        if pending_docs.exists():
            logger.info(f'Processing {pending_docs.count()} pending documents')
            
            for doc in pending_docs:
                try:
                    # Mark as processing
                    doc.processed = True
                    doc.save()
                    
                    logger.info(f'Processed document: {doc.title}')
                    
                except Exception as e:
                    logger.error(f'Error processing document {doc.id}: {e}')
                    doc.processed = False
                    doc.save()
                    
        else:
            logger.debug('No pending documents to process')
            
    except Exception as e:
        logger.error(f'Document queue processing failed: {e}', exc_info=True)

