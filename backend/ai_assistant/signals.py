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
    
    IMPROVED: Added fallback mechanism - if Celery task fails to queue,
    the periodic task (process_pending_files) will pick it up within 60 seconds.
    """
    if created and instance.processing_status == 'pending':
        try:
            # IMPORTANT: Always use async processing to prevent blocking uploads
            # Celery will handle retries automatically with autoretry_for
            from .tasks import process_file_automatically
            
            logger.info(f"Auto-processing file: {instance.filename} (ID: {instance.id}, async=True)")
            
            # Use Celery for async processing (prevents request blocking)
            try:
                task_result = process_file_automatically.delay(instance.id)
                logger.info(f"Scheduled background processing for file {instance.id} (task_id: {task_result.id})")
            except Exception as celery_error:
                # If Celery task fails to queue (e.g., Celery not running), log but don't fail
                # The periodic task process_pending_files will pick it up within 60 seconds
                logger.warning(
                    f"Failed to queue Celery task for file {instance.id}: {celery_error}. "
                    f"File will be picked up by periodic task within 60 seconds."
                )
                # Keep status as 'pending' so periodic task can process it
                # Don't mark as failed - let periodic task handle it
            
        except Exception as e:
            logger.error(f"Auto-processing signal error for {instance.filename}: {e}", exc_info=True)
            # Don't mark as failed immediately - let periodic task try first
            # Only mark as failed if it's a critical error (not Celery-related)
            if 'celery' not in str(e).lower() and 'task' not in str(e).lower():
                instance.processing_status = 'failed'
                instance.processing_error = f"Signal error: {str(e)}"
                instance.save()


@receiver(post_save, sender=DocumentFile)
def auto_process_document_file(sender, instance, created, **kwargs):
    """
    Automatic processing trigger for DocumentFile
    
    Ensures DocumentFile entries also get proper processing
    FIXED: Now checks if UploadedFile is already being processed to prevent duplicate triggers
    """
    if created:
        try:
            # FIX: Check if UploadedFile is already being processed
            # This prevents duplicate processing when DocumentFile is auto-created during processing
            if instance.uploaded_file:
                if instance.uploaded_file.processing_status in ['processing', 'metadata_extracting', 'chunking', 'embedding']:
                    logger.info(
                        f"DocumentFile {instance.id} linked to UploadedFile {instance.uploaded_file.id} "
                        f"already being processed (status: {instance.uploaded_file.processing_status}). "
                        f"Skipping duplicate trigger."
                    )
                    return
            
            # Check if file needs processing (status is pending)
            status = instance.get_processing_status()
            if status.get('status') == 'pending' and not status.get('is_ready'):
                # FIX: Use UploadedFile ID, not DocumentFile ID
                if instance.uploaded_file:
                    from .tasks import process_file_automatically
                    logger.info(
                        f"Auto-processing DocumentFile: {instance.filename} "
                        f"(UploadedFile ID: {instance.uploaded_file.id}, async=True)"
                    )
                    process_file_automatically.delay(instance.uploaded_file.id)  # ✅ FIXED: Use uploaded_file.id
                    logger.info(f"Scheduled background processing for UploadedFile {instance.uploaded_file.id}")
                else:
                    logger.warning(f"DocumentFile {instance.id} has no linked UploadedFile, cannot trigger processing")
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

