"""
Debug Views for Testing Upload Functionality

These views help debug file upload issues by providing test endpoints
and diagnostic information.
"""

import logging
import os
import time
from django.conf import settings
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def debug_upload_info(request):
    """
    Debug endpoint to check upload configuration and permissions
    """
    try:
        uploads_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
        
        info = {
            'media_root': settings.MEDIA_ROOT,
            'media_root_exists': os.path.exists(settings.MEDIA_ROOT),
            'media_root_writable': os.access(settings.MEDIA_ROOT, os.W_OK) if os.path.exists(settings.MEDIA_ROOT) else False,
            'uploads_dir': uploads_dir,
            'uploads_dir_exists': os.path.exists(uploads_dir),
            'uploads_dir_writable': os.access(uploads_dir, os.W_OK) if os.path.exists(uploads_dir) else False,
            'file_upload_max_memory_size': getattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', 'Not set'),
            'data_upload_max_memory_size': getattr(settings, 'DATA_UPLOAD_MAX_MEMORY_SIZE', 'Not set'),
            'user': str(request.user),
            'user_authenticated': request.user.is_authenticated,
        }
        
        # Try to list files in uploads directory
        if os.path.exists(uploads_dir):
            try:
                files = os.listdir(uploads_dir)
                info['files_in_uploads'] = len(files)
                info['sample_files'] = files[:5]  # First 5 files
            except Exception as e:
                info['list_files_error'] = str(e)
        
        return JsonResponse({
            'success': True,
            'info': info
        })
    except Exception as e:
        logger.error(f"Debug upload info error: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def debug_test_upload(request):
    """
    Test endpoint to verify file upload functionality
    Accepts a file and saves it to verify the upload path works
    """
    try:
        logger.info(f"[DEBUG TEST] Upload test request received")
        logger.info(f"[DEBUG TEST] Method: {request.method}")
        logger.info(f"[DEBUG TEST] FILES keys: {list(request.FILES.keys())}")
        logger.info(f"[DEBUG TEST] POST keys: {list(request.POST.keys())}")
        
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'No file provided in request.FILES',
                'files_keys': list(request.FILES.keys()) if hasattr(request, 'FILES') else 'No FILES attribute'
            }, status=400)
        
        file = request.FILES['file']
        logger.info(f"[DEBUG TEST] File received: name={file.name}, size={file.size}")
        
        # Try to read file content
        file.seek(0)
        file_content = file.read()
        logger.info(f"[DEBUG TEST] File content read: {len(file_content)} bytes")
        
        # Try to save file
        uploads_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        
        test_filename = f"test_upload_{int(time.time())}_{file.name}"
        test_path = os.path.join(uploads_dir, test_filename)
        
        logger.info(f"[DEBUG TEST] Attempting to save to: {test_path}")
        
        with open(test_path, 'wb') as f:
            bytes_written = f.write(file_content)
            f.flush()
            os.fsync(f.fileno())
        
        logger.info(f"[DEBUG TEST] File saved: {bytes_written} bytes written")
        
        # Verify file exists
        file_exists = os.path.exists(test_path)
        file_size = os.path.getsize(test_path) if file_exists else 0
        
        logger.info(f"[DEBUG TEST] File verification: exists={file_exists}, size={file_size}")
        
        # Clean up test file
        if file_exists:
            try:
                os.remove(test_path)
                logger.info(f"[DEBUG TEST] Test file cleaned up")
            except Exception as e:
                logger.warning(f"[DEBUG TEST] Could not clean up test file: {e}")
        
        return JsonResponse({
            'success': True,
            'message': 'Test upload successful',
            'details': {
                'file_name': file.name,
                'file_size': file.size,
                'content_length': len(file_content),
                'bytes_written': bytes_written,
                'file_saved': file_exists,
                'saved_file_size': file_size,
                'test_path': test_path,
            }
        })
        
    except Exception as e:
        logger.error(f"[DEBUG TEST] Test upload error: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }, status=500)

