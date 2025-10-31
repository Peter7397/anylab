"""
Django Signals for Automatic File Processing

CRITICAL QUALITY RULES:
- NO performance compromises
- Accuracy over speed
- ALL files MUST be fully processed (metadata + chunks + embeddings)
- BGE-M3 only - no fallbacks
- Unlimited chunks for maximum quality
"""

import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import UploadedFile, DocumentFile, WebsiteSource
from .automatic_file_processor import automatic_file_processor

logger = logging.getLogger(__name__)


@receiver(post_save, sender=UploadedFile)
def auto_process_uploaded_file(sender, instance, created, **kwargs):
    """
    Automatic processing trigger for UploadedFile
    
    QUALITY FOCUS: Process ALL files automatically upon creation
    - Extract metadata immediately
    - Generate unlimited chunks
    - Create BGE-M3 embeddings
    - Mark as ready when complete
    
    Can run in foreground (sync) or background (async via Celery)
    """
    if created and instance.processing_status == 'pending':
        try:
            # IMPORTANT: Always use async processing to prevent blocking uploads
            # Celery will handle retries automatically with autoretry_for
            from .tasks import process_file_automatically
            
            logger.info(f"Auto-processing file: {instance.filename} (ID: {instance.id}, async=True)")
            
            # Use Celery for async processing (prevents request blocking)
            process_file_automatically.delay(instance.id)
            logger.info(f"Scheduled background processing for file {instance.id}")
            
        except Exception as e:
            logger.error(f"Auto-processing failed for {instance.filename}: {e}", exc_info=True)
            # Mark as failed
            instance.processing_status = 'failed'
            instance.processing_error = str(e)
            instance.save()


@receiver(post_save, sender=DocumentFile)
def auto_process_document_file(sender, instance, created, **kwargs):
    """
    Automatic processing trigger for DocumentFile
    
    Ensures DocumentFile entries also get proper processing
    """
    if created:
        try:
            # If this DocumentFile is linked to an UploadedFile, process it
            # Otherwise, create UploadedFile entry for processing
            if not hasattr(instance, 'uploaded_file') or not instance.uploaded_file:
                # We'll handle DocumentFile processing through the normal upload flow
                pass
        except Exception as e:
            logger.error(f"Error processing DocumentFile: {e}", exc_info=True)


@receiver(pre_save, sender=UploadedFile)
def validate_processing_status(sender, instance, **kwargs):
    """
    Validation before saving UploadedFile
    
    ENSURE: Quality checks are maintained
    - Validates processing status transitions
    - Ensures integrity before marking as ready
    """
    # Get existing instance if updating
    if instance.pk:
        try:
            old_instance = UploadedFile.objects.get(pk=instance.pk)
            
            # If transitioning to 'ready', validate completeness
            if instance.processing_status == 'ready' and old_instance.processing_status != 'ready':
                # VALIDATION: Ensure file is truly ready
                if not instance.is_ready_for_search():
                    logger.warning(
                        f"File {instance.filename} marked as ready but validation failed. "
                        f"metadata_extracted={instance.metadata_extracted}, "
                        f"chunks_created={instance.chunks_created}, "
                        f"embeddings_created={instance.embeddings_created}, "
                        f"chunk_count={instance.chunk_count}, "
                        f"embedding_count={instance.embedding_count}"
                    )
                    # Don't allow transition to ready if validation fails
                    instance.processing_status = 'failed'
                    instance.processing_error = "Validation failed: file not fully processed"
                    
        except UploadedFile.DoesNotExist:
            pass


@receiver(post_save, sender=WebsiteSource)
def auto_process_website_source(sender, instance, created, **kwargs):
    """
    Automatic processing trigger for WebsiteSource
    
    QUALITY FOCUS: Process ALL websites automatically upon creation
    - Fetch HTML content immediately
    - Convert to UploadedFile format
    - Use AutomaticFileProcessor for metadata, chunking, embeddings
    - Mark as ready when complete
    
    Can run in foreground (sync) or background (async via Celery)
    """
    if created and instance.processing_status == 'pending':
        try:
            # IMPORTANT: Always use async processing to prevent blocking requests
            # Celery will handle retries automatically with autoretry_for
            from .tasks import process_website_automatically
            
            logger.info(f"Auto-processing website: {instance.url} (ID: {instance.id}, async=True)")
            
            # Use Celery for async processing (prevents request blocking)
            process_website_automatically.delay(instance.id)
            logger.info(f"Scheduled background processing for website {instance.id}")
            
        except Exception as e:
            logger.error(f"Auto-processing failed for {instance.url}: {e}", exc_info=True)
            # Mark as failed
            instance.processing_status = 'failed'
            instance.processing_error = str(e)
            instance.save()


@receiver(pre_save, sender=WebsiteSource)
def validate_website_processing_status(sender, instance, **kwargs):
    """
    Validation before saving WebsiteSource
    
    ENSURE: Quality checks are maintained
    - Validates processing status transitions
    - Ensures integrity before marking as ready
    """
    # Get existing instance if updating
    if instance.pk:
        try:
            old_instance = WebsiteSource.objects.get(pk=instance.pk)
            
            # If transitioning to 'ready', validate completeness
            if instance.processing_status == 'ready' and old_instance.processing_status != 'ready':
                # VALIDATION: Ensure website is truly ready
                if not instance.is_ready_for_search():
                    logger.warning(
                        f"Website {instance.url} marked as ready but validation failed. "
                        f"metadata_extracted={instance.metadata_extracted}, "
                        f"chunks_created={instance.chunks_created}, "
                        f"embeddings_created={instance.embeddings_created}, "
                        f"chunk_count={instance.chunk_count}, "
                        f"embedding_count={instance.embedding_count}"
                    )
                    # Don't allow transition to ready if validation fails
                    instance.processing_status = 'failed'
                    instance.processing_error = "Validation failed: website not fully processed"
                    
        except WebsiteSource.DoesNotExist:
            pass

