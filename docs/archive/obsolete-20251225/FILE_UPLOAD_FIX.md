# File Upload Fix for Mac M4 Docker Setup

## Issues Identified

1. **Missing File Upload Settings**: Django settings didn't have `FILE_UPLOAD_MAX_MEMORY_SIZE` and `DATA_UPLOAD_MAX_MEMORY_SIZE` configured
2. **Media Directory Permissions**: Media directories needed proper permissions for file uploads
3. **Missing Subdirectories**: Required subdirectories (`uploads/`, `temp/`, `pdfs/`) were not created at startup

## Fixes Applied

### 1. Added File Upload Settings to `backend/anylab/settings.py`

```python
# File Upload Configuration - Docker-aware
# Increased limits for Docker environment to support large document uploads
FILE_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB - files larger than this use temp file
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB - max size for request body
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000  # Increased for complex forms
FILE_UPLOAD_TEMP_DIR = os.path.join(MEDIA_ROOT, 'temp')
```

**Why 100MB?**
- Supports large document uploads (manuals, technical documents)
- Files larger than this will be written to temporary files automatically
- Compatible with the 500MB file size limit in the upload validation

### 2. Updated Docker Compose Startup Command

Modified `docker-compose.yml` backend service to create directories and set permissions:

```yaml
command: >
  sh -c "mkdir -p /app/media/uploads /app/media/temp /app/media/pdfs &&
         chmod -R 777 /app/media &&
         python manage.py migrate &&
         python manage.py collectstatic --noinput &&
         gunicorn --config gunicorn_config.py anylab.wsgi:application"
```

### 3. Created Media Subdirectories

- `/app/media/uploads/` - For uploaded files
- `/app/media/temp/` - For temporary file processing
- `/app/media/pdfs/` - For PDF documents

## Verification

To verify the fix is working:

1. **Check settings are applied:**
   ```bash
   docker exec anylab_backend python -c "import django; django.setup(); from django.conf import settings; print('FILE_UPLOAD_MAX_MEMORY_SIZE:', settings.FILE_UPLOAD_MAX_MEMORY_SIZE / (1024*1024), 'MB')"
   ```

2. **Check directory permissions:**
   ```bash
   docker exec anylab_backend ls -la /app/media/
   ```

3. **Test file upload:**
   - Try uploading a file through the frontend
   - Check backend logs: `docker compose logs backend`
   - Verify file appears in `/app/media/uploads/`

## File Upload Limits

| Setting | Value | Purpose |
|---------|-------|---------|
| `FILE_UPLOAD_MAX_MEMORY_SIZE` | 100 MB | Files smaller than this stay in memory |
| `DATA_UPLOAD_MAX_MEMORY_SIZE` | 100 MB | Maximum request body size |
| Application max file size | 500 MB | Validated in upload serializer |
| Nginx `client_max_body_size` | 100 MB | (If using Nginx proxy) |

**Note**: Files larger than 100MB will automatically be written to temporary files on disk, which is more memory-efficient for large uploads.

## Troubleshooting

### If uploads still fail:

1. **Check backend logs:**
   ```bash
   docker compose logs backend --tail 50
   ```

2. **Verify media volume:**
   ```bash
   docker volume inspect anylab103_backend_media
   ```

3. **Test directory write permissions:**
   ```bash
   docker exec anylab_backend touch /app/media/test.txt && docker exec anylab_backend rm /app/media/test.txt
   ```

4. **Check disk space:**
   ```bash
   docker exec anylab_backend df -h /app/media
   ```

### Common Errors:

- **413 Request Entity Too Large**: Increase `DATA_UPLOAD_MAX_MEMORY_SIZE` or check Nginx config
- **Permission Denied**: Ensure media directory has write permissions (777)
- **No space left on device**: Check available disk space in Docker volume

## Next Steps

After applying these fixes:
1. Restart the backend service: `docker compose restart backend`
2. Test file upload through the frontend
3. Monitor logs for any errors
4. Verify files are saved in `/app/media/uploads/`

## Windows Migration Note

These settings will work on Windows as well. The file upload limits are appropriate for both Mac development and Windows production environments.

