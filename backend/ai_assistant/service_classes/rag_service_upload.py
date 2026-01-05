"""
Simplified Docker-First Upload Service

This is a redesigned, simplified upload workflow that:
1. Uses Django's storage API directly
2. Saves files immediately without excessive verification
3. Has clear, visible logging
4. Is optimized for Docker volume sharing
"""

import logging
import hashlib
import os
import sys
from typing import Dict, Any
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from .base_service import BaseService
from ..models import UploadedFile

logger = logging.getLogger(__name__)

# Force logging to stdout for Docker visibility
def log_to_stdout(message, level='INFO'):
    """Log to both logger and stdout for Docker visibility"""
    # Force output to stdout with immediate flush
    msg = f"[UPLOAD] {message}"
    print(msg, file=sys.stdout)
    sys.stdout.flush()
    # Also log via logger
    if level == 'ERROR':
        logger.error(message)
    elif level == 'WARNING':
        logger.warning(message)
    else:
        logger.info(message)


class SimpleUploadService(BaseService):
    """Simplified upload service for Docker environment"""
    
    def upload_document_enhanced(self, file, user, **kwargs) -> Dict[str, Any]:
        """
        Simplified upload workflow:
        1. Read file content
        2. Calculate hash
        3. Check duplicates
        4. Save file using Django storage
        5. Create DB record
        6. Return success
        """
        try:
            log_to_stdout(f"=== UPLOAD START: {file.name} ({file.size} bytes) ===")
            
            # Step 1: Read file content
            log_to_stdout(f"Reading file content...")
            if hasattr(file, 'seek'):
                file.seek(0)
            
            file_content = file.read()
            if not file_content or len(file_content) == 0:
                error_msg = "File content is empty"
                log_to_stdout(f"ERROR: {error_msg}", 'ERROR')
                raise ValueError(error_msg)
            
            log_to_stdout(f"File read: {len(file_content)} bytes")
            
            # Step 2: Calculate hash
            log_to_stdout(f"Calculating hash...")
            file_hash = hashlib.md5(file_content).hexdigest()
            log_to_stdout(f"Hash: {file_hash[:8]}...")
            
            # Step 3: Check for duplicates
            existing_file = UploadedFile.objects.filter(file_hash=file_hash).first()
            if existing_file:
                log_to_stdout(f"Duplicate found: ID={existing_file.id}")
                # Verify file exists on disk
                if default_storage.exists(existing_file.filename):
                    log_to_stdout(f"Duplicate file exists on disk, returning existing record")
                    return self.success_response("File already exists", {
                        'uploaded_file_id': existing_file.id,
                        'filename': existing_file.filename,
                        'message': 'This file has already been uploaded'
                    })
                else:
                    log_to_stdout(f"Duplicate record exists but file missing, will restore")
            
            # Step 4: Save file using Django storage
            log_to_stdout(f"Saving file to storage...")
            log_to_stdout(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")
            
            # Generate safe filename
            original_filename = file.name
            safe_filename = default_storage.get_valid_name(original_filename)
            relative_path = f'uploads/{safe_filename}'
            
            # Handle filename conflicts
            counter = 1
            base_name, ext = os.path.splitext(safe_filename)
            while default_storage.exists(relative_path):
                safe_filename = f"{base_name}_{counter}{ext}"
                relative_path = f'uploads/{safe_filename}'
                counter += 1
                log_to_stdout(f"Filename conflict, trying: {relative_path}")
            
            log_to_stdout(f"Saving to: {relative_path}")
            
            # Store original file size for validation
            original_file_size = len(file_content)
            log_to_stdout(f"Original file size: {original_file_size:,} bytes")
            
            # Save file - this is the critical step
            saved_path = default_storage.save(relative_path, ContentFile(file_content))
            log_to_stdout(f"File saved: {saved_path}")
            
            # Quick verification
            if not default_storage.exists(saved_path):
                error_msg = f"File save failed: {saved_path}"
                log_to_stdout(f"ERROR: {error_msg}", 'ERROR')
                raise Exception(error_msg)
            
            file_size = default_storage.size(saved_path)
            log_to_stdout(f"Saved file size: {file_size:,} bytes")
            
            # CRITICAL: Verify file size matches original (file integrity check)
            if file_size != original_file_size:
                error_msg = (
                    f"File size mismatch detected! "
                    f"Original: {original_file_size:,} bytes, "
                    f"Saved: {file_size:,} bytes, "
                    f"Difference: {abs(file_size - original_file_size):,} bytes. "
                    f"File may have been corrupted during upload. Upload aborted."
                )
                log_to_stdout(f"ERROR: {error_msg}", 'ERROR')
                # Clean up the corrupted file
                try:
                    default_storage.delete(saved_path)
                    log_to_stdout(f"Deleted corrupted file: {saved_path}")
                except Exception as cleanup_error:
                    log_to_stdout(f"Warning: Failed to delete corrupted file: {cleanup_error}", 'WARNING')
                raise Exception(error_msg)
            
            log_to_stdout(f"✓ File size verified: {file_size:,} bytes (matches original)")
            
            # Step 5: Create DB record
            log_to_stdout(f"Creating database record...")
            uploaded_file = UploadedFile.objects.create(
                filename=saved_path,  # Store relative path
                file_hash=file_hash,
                file_size=file_size,
                uploaded_by=user,
                processing_status='pending'
            )
            log_to_stdout(f"Database record created: ID={uploaded_file.id}")
            
            # Step 6: Final verification
            if not default_storage.exists(saved_path):
                error_msg = f"File disappeared after DB creation: {saved_path}"
                log_to_stdout(f"ERROR: {error_msg}", 'ERROR')
                uploaded_file.processing_status = 'failed'
                uploaded_file.processing_error = error_msg
                uploaded_file.save()
                raise Exception(error_msg)
            
            log_to_stdout(f"=== UPLOAD SUCCESS: ID={uploaded_file.id} ===")
            
            result = {
                'uploaded_file_id': uploaded_file.id,
                'filename': uploaded_file.filename,
                'file_size': uploaded_file.file_size,
                'status': 'pending',
                'message': 'File uploaded successfully. Processing will begin automatically.'
            }
            
            return self.success_response("Document uploaded successfully", result)
            
        except Exception as e:
            error_msg = f"Upload failed: {str(e)}"
            log_to_stdout(f"ERROR: {error_msg}", 'ERROR')
            import traceback
            log_to_stdout(f"Traceback:\n{traceback.format_exc()}", 'ERROR')
            logger.error(error_msg, exc_info=True)
            self.log_error('upload_document_enhanced', e)
            return self.error_response(f'Failed to upload document: {str(e)}')

