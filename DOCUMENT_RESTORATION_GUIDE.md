# Document Restoration Guide

## Current Situation

### What Happened
After the system rebuild, **all documents were lost from the database**. This happened because:

1. **Database was reset**: When we ran `python manage.py migrate`, the database was recreated with fresh tables
2. **Media files**: The Docker volume `anylab103_backend_media` exists but is empty
3. **Local files**: Your original uploaded files still exist in `backend/media/uploads/` on your local machine

### Current Status
- ✅ **Database**: 0 documents, 0 chunks
- ✅ **Docker media volume**: Empty
- ✅ **Local files**: Still exist in `backend/media/uploads/` (but not linked to database)

## Options to Restore Documents

### Option 1: Restore from Database Backup (Recommended if available)

If you have a database backup from before the rebuild:

```bash
# Check for backups
ls -la backups/
ls -la migration-package/

# Restore PostgreSQL backup
docker compose exec -T postgres psql -U postgres anylab < migration-package/postgres_backup_*.sql
```

### Option 2: Re-upload Documents

If no backup is available, you'll need to re-upload your documents:

1. **Via Frontend UI**:
   - Go to http://localhost:3000
   - Navigate to Document Manager or Upload Queue
   - Upload your documents again

2. **Via API** (if you have many files):
   ```bash
   # Upload a single file
   curl -X POST http://localhost:8000/api/ai/upload/ \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -F "file=@/path/to/document.pdf"
   ```

### Option 3: Bulk Import from Local Files (Advanced)

If you want to import files from `backend/media/uploads/`:

```bash
cd backend
source venv/bin/activate
python manage.py shell
```

Then in Python shell:
```python
import os
from django.core.files import File
from ai_assistant.models import UploadedFile
from django.contrib.auth import get_user_model

User = get_user_model()
admin = User.objects.get(username='admin')

# Get all files from local uploads directory
uploads_dir = '/Volumes/Orico/Anylab103/backend/media/uploads'
for filename in os.listdir(uploads_dir):
    if filename.startswith('._'):  # Skip macOS metadata files
        continue
    
    file_path = os.path.join(uploads_dir, filename)
    if os.path.isfile(file_path):
        # Create UploadedFile record
        with open(file_path, 'rb') as f:
            uploaded_file = UploadedFile.objects.create(
                filename=filename,
                file_hash='',  # Will be calculated during processing
                uploaded_by=admin,
                processing_status='pending'
            )
            # Copy file to Docker volume
            # Note: This requires additional setup
            print(f"Created record for: {filename}")
```

## Why This Happened

During the rebuild:
1. We preserved Docker volumes (didn't use `-v` flag)
2. But when migrations ran, the database was reset
3. The media volume was recreated empty
4. Local files weren't automatically imported

## Prevention for Future

To prevent data loss in future rebuilds:

1. **Always backup before rebuild**:
   ```bash
   # Backup database
   docker compose exec postgres pg_dump -U postgres anylab > backup_$(date +%Y%m%d).sql
   
   # Backup media files
   docker compose exec backend tar -czf /tmp/media_backup.tar.gz /app/media
   docker compose cp backend:/tmp/media_backup.tar.gz ./media_backup.tar.gz
   ```

2. **Use data migration scripts** instead of fresh migrations

3. **Keep regular backups** of both database and media files

## Quick Check Commands

```bash
# Check database documents
docker compose exec backend python manage.py shell -c "from ai_assistant.models import UploadedFile; print(f'Documents: {UploadedFile.objects.count()}')"

# Check media files in Docker
docker compose exec backend ls -la /app/media/uploads/ | wc -l

# Check local files
ls -la backend/media/uploads/ | wc -l
```

## Recommendation

**If you have a backup**: Restore it now before uploading new documents.

**If no backup**: You'll need to re-upload your documents. The system will:
- Process them automatically
- Generate embeddings
- Make them searchable in RAG

The good news is that all the improvements we made (visual embeddings, OCR, etc.) will work on newly uploaded documents!

