"""
Docker-First Upload Logic for RAG Service

This module provides a simplified, Docker-aware file upload implementation
that uses Django's storage system and Docker volume paths exclusively.
"""

import logging
import hashlib
import os
from typing import Dict, Any
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from .base_service import BaseService
from ..models import UploadedFile

logger = logging.getLogger(__name__)


class DockerUploadService(BaseService):
    """
    Docker-first file upload service
    
    Key principles:
    1. Always use Django's default_storage (configured for Docker)
    2. Use Docker paths exclusively (/app/media/)
    3. Store relative paths in database
    4. Simple, straightforward file saving
    """
    
    def upload_document_enhanced(self, file, user, **kwargs) -> Dict[str, Any]:
        """
        Upload document using Docker-first approach
        
        Steps:
        1. Read file content
        2. Calculate hash for deduplication
        3. Check for duplicates
        4. Save file using Django storage (Docker-aware)
        5. Create DB record with relative path
        6. Return success
        """
        try:
            logger.info(f"[DOCKER UPLOAD] Starting upload: {file.name}, size={file.size}")
            
            # Step 1: Read file content
            if hasattr(file, 'seek'):
                file.seek(0)
            
            file_content = file.read()
            if not file_content or len(file_content) == 0:
                raise ValueError("File content is empty or could not be read")
            
            file_hash = hashlib.md5(file_content).hexdigest()
            logger.info(f"[DOCKER UPLOAD] File read: {len(file_content)} bytes, hash={file_hash[:8]}...")
            
            # Step 2: Check for duplicates
            existing_file = UploadedFile.objects.filter(file_hash=file_hash).first()
            if existing_file:
                # Verify file exists on disk
                existing_path = self._get_docker_path(existing_file.filename)
                if os.path.exists(existing_path):
                    logger.info(f"[DOCKER UPLOAD] Duplicate file found: {existing_file.filename}")
                    return self.success_response("File already exists", {
                        'uploaded_file_id': existing_file.id,
                        'filename': existing_file.filename,
                        'message': 'This file has already been uploaded'
                    })
                else:
                    # File record exists but file is missing - restore it
                    logger.warning(f"[DOCKER UPLOAD] Duplicate hash but file missing, restoring...")
                    self._save_file_to_docker(file_content, existing_file.filename, file.name)
                    existing_file.processing_status = 'pending'
                    existing_file.processing_error = ''
                    existing_file.save()
                    return self.success_response("File restored and scheduled for processing", {
                        'uploaded_file_id': existing_file.id,
                        'filename': existing_file.filename,
                        'message': 'File was missing and has been restored'
                    })
            
            # Step 3: Generate safe filename
            original_filename = file.name
            safe_filename = default_storage.get_valid_name(original_filename)
            
            # Handle filename conflicts
            relative_path = f'uploads/{safe_filename}'
            counter = 1
            while default_storage.exists(relative_path):
                base_name, ext = os.path.splitext(safe_filename)
                safe_filename = f"{base_name}_{counter}{ext}"
                relative_path = f'uploads/{safe_filename}'
                counter += 1
            
            logger.info(f"[DOCKER UPLOAD] Saving file to: {relative_path}")
            
            # Step 4: Save file using Django storage (Docker-aware)
            # This automatically handles Docker volume paths
            saved_path = default_storage.save(relative_path, ContentFile(file_content))
            
            # Verify file was saved
            if not default_storage.exists(saved_path):
                raise Exception(f"File was not saved to {saved_path}")
            
            # Get actual file size
            file_size = default_storage.size(saved_path)
            if file_size != len(file_content):
                logger.warning(f"[DOCKER UPLOAD] Size mismatch: expected {len(file_content)}, got {file_size}")
            
            logger.info(f"[DOCKER UPLOAD] File saved: {saved_path} ({file_size} bytes)")
            
            # Step 5: Create DB record
            uploaded_file = UploadedFile.objects.create(
                filename=saved_path,  # Store relative path: 'uploads/filename.ext'
                file_hash=file_hash,
                file_size=file_size,
                uploaded_by=user,
                processing_status='pending'
            )
            
            logger.info(f"[DOCKER UPLOAD] DB record created: ID={uploaded_file.id}, filename={uploaded_file.filename}")
            
            # Step 6: Final verification - file should be accessible
            docker_path = self._get_docker_path(saved_path)
            if not os.path.exists(docker_path):
                # This should never happen with Django storage, but check anyway
                logger.error(f"[DOCKER UPLOAD ERROR] File not found at Docker path: {docker_path}")
                uploaded_file.processing_status = 'failed'
                uploaded_file.processing_error = f"File not found after save: {docker_path}"
                uploaded_file.save()
                raise Exception(f"File not found after save: {docker_path}")
            
            logger.info(f"[DOCKER UPLOAD SUCCESS] Upload complete: {saved_path}")
            
            return self.success_response("Document uploaded successfully", {
                'uploaded_file_id': uploaded_file.id,
                'filename': uploaded_file.filename,
                'file_size': uploaded_file.file_size,
                'status': 'pending',
                'message': 'File uploaded successfully. Processing will begin automatically.'
            })
            
        except Exception as e:
            logger.error(f"[DOCKER UPLOAD ERROR] Upload failed: {e}", exc_info=True)
            return self.error_response(f'Failed to upload document: {str(e)}')
    
    def _get_docker_path(self, relative_path: str) -> str:
        """
        Convert relative path to Docker absolute path
        
        Args:
            relative_path: Path relative to MEDIA_ROOT (e.g., 'uploads/file.pdf')
            
        Returns:
            Absolute Docker path (e.g., '/app/media/uploads/file.pdf')
        """
        # Ensure path is relative (remove leading slash if present)
        if relative_path.startswith('/'):
            relative_path = relative_path[1:]
        
        # Remove 'media/' prefix if present (MEDIA_ROOT already includes it)
        if relative_path.startswith('media/'):
            relative_path = relative_path[6:]
        
        # Join with MEDIA_ROOT (which is /app/media in Docker)
        return os.path.join(settings.MEDIA_ROOT, relative_path)
    
    def _save_file_to_docker(self, file_content: bytes, relative_path: str, original_name: str):
        """
        Save file content to Docker volume using Django storage
        
        Args:
            file_content: File content as bytes
            relative_path: Target relative path
            original_name: Original filename for logging
        """
        logger.info(f"[DOCKER UPLOAD] Saving file to Docker: {relative_path}")
        
        # Use Django storage to save file
        saved_path = default_storage.save(relative_path, ContentFile(file_content))
        
        # Verify
        if not default_storage.exists(saved_path):
            raise Exception(f"File was not saved to {saved_path}")
        
        logger.info(f"[DOCKER UPLOAD] File saved successfully: {saved_path}")
        return saved_path

