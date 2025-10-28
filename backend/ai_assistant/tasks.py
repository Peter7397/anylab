"""
Celery tasks for AI Assistant operations including SSB scraping.
"""

import logging
from celery import shared_task
from django.core.management import call_command
from django.utils import timezone
from django.core.cache import cache
from .models import DocumentFile, UploadedFile
from .automatic_file_processor import automatic_file_processor

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


@shared_task(bind=True, name='ai_assistant.tasks.process_file_automatically')
def process_file_automatically(self, uploaded_file_id):
    """
    Background task for automatic file processing
    
    QUALITY FOCUS: Uses automatic processor with full quality guarantees
    - Unlimited chunks
    - BGE-M3 only
    - 3 retry attempts
    - Performance over speed
    """
    try:
        logger.info(f'Processing file {uploaded_file_id} in background')
        
        # Use the automatic processor with all quality guarantees
        result = automatic_file_processor.process_file_fully(uploaded_file_id)
        
        logger.info(f'File {uploaded_file_id} processed successfully: {result}')
        
        return {
            'status': 'success',
            'uploaded_file_id': uploaded_file_id,
            'result': result
        }
        
    except Exception as e:
        logger.error(f'Background processing failed for file {uploaded_file_id}: {e}', exc_info=True)
        
        # Mark as failed in database
        try:
            uploaded_file = UploadedFile.objects.get(id=uploaded_file_id)
            uploaded_file.processing_status = 'failed'
            uploaded_file.processing_error = str(e)
            uploaded_file.save()
        except UploadedFile.DoesNotExist:
            logger.error(f'UploadedFile {uploaded_file_id} not found')
        
        raise


@shared_task(bind=True, name='ai_assistant.tasks.process_bulk_upload')
def process_bulk_upload(self, uploaded_file_ids):
    """
    Process multiple files in background
    
    QUALITY FOCUS: Process ALL files with full quality guarantees
    - No compromises on chunking
    - BGE-M3 only for embeddings
    - Performance over speed
    """
    try:
        logger.info(f'Processing {len(uploaded_file_ids)} files in bulk')
        
        results = {
            'successful': 0,
            'failed': 0,
            'details': []
        }
        
        for uploaded_file_id in uploaded_file_ids:
            try:
                # Process each file using automatic processor
                result = automatic_file_processor.process_file_fully(uploaded_file_id)
                
                results['successful'] += 1
                results['details'].append({
                    'uploaded_file_id': uploaded_file_id,
                    'status': 'success',
                    'chunk_count': result.get('chunk_count', 0),
                    'embedding_count': result.get('embedding_count', 0)
                })
                
            except Exception as e:
                logger.error(f'Error processing file {uploaded_file_id}: {e}', exc_info=True)
                results['failed'] += 1
                results['details'].append({
                    'uploaded_file_id': uploaded_file_id,
                    'status': 'failed',
                    'error': str(e)
                })
        
        logger.info(f'Bulk processing completed: {results["successful"]} successful, {results["failed"]} failed')
        
        return results
        
    except Exception as e:
        logger.error(f'Bulk processing failed: {e}', exc_info=True)
        raise


@shared_task(name='ai_assistant.tasks.process_pending_files')
def process_pending_files():
    """
    Process any pending files in the queue
    
    Runs periodically to process files that are stuck in pending state
    """
    try:
        # Get files stuck in pending for more than 1 minute
        from datetime import timedelta
        cutoff = timezone.now() - timedelta(minutes=1)
        
        pending_files = UploadedFile.objects.filter(
            processing_status='pending',
            uploaded_at__lt=cutoff
        )[:10]
        
        if pending_files.exists():
            logger.info(f'Processing {pending_files.count()} pending files')
            
            for uploaded_file in pending_files:
                try:
                    # Trigger processing
                    process_file_automatically.delay(uploaded_file.id)
                    
                except Exception as e:
                    logger.error(f'Error triggering processing for file {uploaded_file.id}: {e}')
        else:
            logger.debug('No pending files to process')
            
    except Exception as e:
        logger.error(f'Error processing pending files: {e}', exc_info=True)

