# File Upload Debugging Guide

## Issue
Files are uploaded but show "chunking" then "failed" status. The error is:
```
Could not locate file for uploads/filename.pdf
```

## Root Cause
The file is not being saved to disk during upload, or the file path resolution is incorrect.

## Debugging Steps

### 1. Check if files are being saved
```bash
# Check uploads directory
docker exec anylab_backend ls -la /app/media/uploads/

# Check latest uploaded file
docker exec anylab_backend python manage.py shell -c "from ai_assistant.models import UploadedFile; f = UploadedFile.objects.order_by('-id').first(); print(f'File: {f.filename}, Status: {f.processing_status}, Error: {f.processing_error}')"
```

### 2. Check backend logs during upload
```bash
docker compose logs backend -f
# Then try uploading a file and watch the logs
```

### 3. Check file write permissions
```bash
docker exec anylab_backend python -c "import os; test_file = '/app/media/uploads/test.txt'; os.makedirs(os.path.dirname(test_file), exist_ok=True); open(test_file, 'w').write('test'); print('Write test:', os.path.exists(test_file)); os.remove(test_file)"
```

### 4. Verify MEDIA_ROOT
```bash
docker exec anylab_backend python manage.py shell -c "from django.conf import settings; print('MEDIA_ROOT:', settings.MEDIA_ROOT)"
```

## Fix Applied

Added error handling and logging to the file save operation in `rag_service.py`:
- Logs when file is saved successfully
- Verifies file exists after writing
- Checks file size is not zero
- Raises clear error messages if save fails

## Next Steps

1. **Try uploading a file again** and check:
   - Backend logs for "File saved successfully" message
   - Uploads directory for the file
   - Processing status in database

2. **If file still not saved:**
   - Check Docker volume mount: `docker volume inspect anylab103_backend_media`
   - Check disk space: `docker exec anylab_backend df -h /app/media`
   - Check file permissions: `docker exec anylab_backend ls -la /app/media/`

3. **If file is saved but not found:**
   - Check the `_get_file_path` function in `automatic_file_processor.py`
   - Verify filename format matches what's stored in database
   - Check if path resolution is using Docker paths, not host paths

## Common Issues

1. **Volume not mounted correctly**: Check `docker-compose.yml` volume configuration
2. **Permission issues**: Files need write access in `/app/media/uploads/`
3. **Path mismatch**: Database stores relative path but code looks for absolute path
4. **File content not read**: `file.read()` might fail silently

