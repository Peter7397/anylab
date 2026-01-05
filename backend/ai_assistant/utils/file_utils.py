"""
File utility functions for file path resolution and archive handling.
"""

import logging
import os
import tempfile
import shutil
import zipfile
from pathlib import Path
from django.conf import settings
from django.core.files.storage import default_storage

logger = logging.getLogger(__name__)


def get_file_path(uploaded_file) -> str:
    """
    Get actual file path from uploaded file
    
    Handles multiple possible storage locations:
    1. DocumentFile.file.path (if exists) - files stored via Django FileField
    2. media/uploads/ - direct uploads (current location)
    3. media/documents/ - DocumentFile storage
    4. Old external device locations (for files moved from external device)
    5. Other fallback locations
    
    Note: If file is accessible via URL but not found on disk, it may be on
    the old external device. This method tries common old locations.
    """
    from ..models import DocumentFile
    
    # First, check if there's a DocumentFile with the actual file stored
    document_file = DocumentFile.objects.filter(uploaded_file=uploaded_file).first()
    if document_file and document_file.file:
        file_path = document_file.file.path
        if os.path.exists(file_path):
            logger.debug(f"Found file via DocumentFile: {file_path}")
            return file_path
    
    # Normalize filename (remove 'uploads/' prefix if present)
    filename = uploaded_file.filename
    base_filename = filename.replace('uploads/', '') if filename.startswith('uploads/') else filename
    
    # Build list of possible paths to check
    possible_paths = []
    
    # Check if we're in Docker
    is_docker = os.path.exists('/.dockerenv')
    
    # PRIORITY 1: Use Django storage API (Docker-aware, recommended approach)
    # This is the same API used to save files, so it should find them
    logger.info(f"[FILE PATH] Attempting Django storage API lookup for: {filename}")
    if default_storage.exists(filename):
        try:
            storage_path = default_storage.path(filename)
            if os.path.exists(storage_path):
                logger.info(f"[FILE PATH] Found file via Django storage API: {storage_path}")
                return storage_path
            else:
                logger.warning(f"[FILE PATH] Storage says file exists but path not found: {storage_path}")
        except Exception as e:
            logger.warning(f"[FILE PATH] Storage.path() failed: {e}, trying other methods")
    
    # Also try with just the base filename (without 'uploads/' prefix)
    if filename.startswith('uploads/'):
        base_only = filename.replace('uploads/', '', 1)
        logger.info(f"[FILE PATH] Trying base filename: {base_only}")
        if default_storage.exists(base_only):
            try:
                storage_path = default_storage.path(base_only)
                if os.path.exists(storage_path):
                    logger.info(f"[FILE PATH] Found file via Django storage API (base filename): {storage_path}")
                    return storage_path
            except Exception as e:
                logger.debug(f"[FILE PATH] Storage.path() failed for base filename: {e}")
    
    # PRIORITY 2: Use MEDIA_ROOT (should be /app/media in Docker)
    # Handle both 'uploads/filename.pdf' and 'filename.pdf' formats
    if filename.startswith('uploads/'):
        media_path = os.path.join(settings.MEDIA_ROOT, filename)
        # Also try without the 'uploads/' prefix in case it's duplicated
        base_only_path = os.path.join(settings.MEDIA_ROOT, 'uploads', base_filename)
        if base_only_path != media_path:
            possible_paths.append(base_only_path)
    else:
        media_path = os.path.join(settings.MEDIA_ROOT, 'uploads', filename)
    
    possible_paths.append(media_path)
    logger.info(f"Checking MEDIA_ROOT path: {media_path} (exists: {os.path.exists(media_path)})")
    
    # PRIORITY 3: If in Docker, also explicitly check /app/media (in case MEDIA_ROOT is wrong)
    if is_docker:
        docker_media_root = '/app/media'
        if filename.startswith('uploads/'):
            docker_path = os.path.join(docker_media_root, filename)
            # Also try base filename
            docker_base_path = os.path.join(docker_media_root, 'uploads', base_filename)
            if docker_base_path != docker_path:
                possible_paths.insert(0, docker_base_path)
        else:
            docker_path = os.path.join(docker_media_root, 'uploads', filename)
        if docker_path not in possible_paths:
            possible_paths.insert(0, docker_path)  # Insert at beginning for priority
        logger.info(f"Checking Docker path: {docker_path} (exists: {os.path.exists(docker_path)})")
    
    # Also try as absolute path if filename looks like one
    if os.path.isabs(filename):
        possible_paths.insert(0, filename)
    
    # Try all possible paths
    for path in possible_paths:
        if os.path.exists(path):
            logger.info(f"[FILE PATH] Found file at: {path}")
            return path
    
    # If not found, raise error with helpful message
    error_msg = (
        f"File not found for {uploaded_file.filename} (ID: {uploaded_file.id}). "
        f"Checked paths: {possible_paths[:3]}. "
        f"Please verify the file exists in the media directory."
    )
    logger.error(error_msg)
    raise FileNotFoundError(error_msg)


def is_archive_file(file_ext: str) -> bool:
    """Check if file is an archive"""
    return file_ext.lower() in ['.zip', '.rar', '.7z', '.tar', '.gz', '.tar.gz', '.tar.bz2']


def extract_archive_contents(file_path: str, uploaded_file) -> list:
    """
    Extract archive and return list of extracted file paths
    
    QUALITY FOCUS: Process ALL contents, unlimited chunks for each file
    """
    extracted_files = []
    temp_dir = tempfile.mkdtemp()
    
    try:
        file_ext = Path(file_path).suffix.lower()
        
        # ZIP extraction
        if file_ext == '.zip':
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
                for root, dirs, files in os.walk(temp_dir):
                    for filename in files:
                        extracted_path = os.path.join(root, filename)
                        extracted_files.append({
                            'path': extracted_path,
                            'relative_path': os.path.relpath(extracted_path, temp_dir),
                            'size': os.path.getsize(extracted_path)
                        })
        
        # TAR.GZ extraction
        elif file_ext in ['.tar', '.tar.gz', '.gz']:
            import tarfile
            with tarfile.open(file_path, 'r:*') as tar_ref:
                tar_ref.extractall(temp_dir)
                for root, dirs, files in os.walk(temp_dir):
                    for filename in files:
                        extracted_path = os.path.join(root, filename)
                        extracted_files.append({
                            'path': extracted_path,
                            'relative_path': os.path.relpath(extracted_path, temp_dir),
                            'size': os.path.getsize(extracted_path)
                        })
        
        logger.info(f"Extracted {len(extracted_files)} files from archive: {uploaded_file.filename}")
        
        # Store temp directory for cleanup
        extracted_files.append({'temp_dir': temp_dir})
        
        return extracted_files
        
    except Exception as e:
        logger.error(f"Archive extraction error: {e}")
        # Cleanup temp directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        raise

