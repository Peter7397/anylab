# 📄 Managing Unprocessed Documents

## Quick Summary

You have **26 unprocessed documents** that are in 'pending' status.

## Options

### Option 1: Delete Unprocessed Documents (Recommended if you want to re-upload)

This will **permanently delete** all unprocessed documents so you can upload them again fresh.

```bash
cd backend
./venv/bin/python manage_unprocessed_documents.py delete
```

**What it does:**
- Deletes all unprocessed documents (pending, failed, in-progress)
- Deletes related DocumentFile records
- Deletes related DocumentChunk records
- **Files in media/uploads/ are NOT deleted** (you can manually delete them if needed)

**After deletion:** You can upload the documents again and they will be processed fresh.

### Option 2: Reprocess All Pending Documents

This will **reprocess all pending documents** in the background.

```bash
cd backend
./venv/bin/python manage_unprocessed_documents.py reprocess
```

**What it does:**
- Queues all pending documents for background processing via Celery
- Documents will be processed automatically
- Processing happens in background (non-blocking)

**Note:** Make sure Celery worker is running:
```bash
cd backend
./start-celery-worker.sh
```

### Option 3: Reset for Reprocessing

This resets unprocessed documents to 'pending' status and clears existing chunks/embeddings.

```bash
cd backend
./venv/bin/python manage_unprocessed_documents.py reset
```

**What it does:**
- Resets processing status to 'pending'
- Clears existing chunks and embeddings
- Documents will be automatically processed when you upload new files (or trigger manually)

### Option 4: View Unprocessed Documents

List all unprocessed documents without making changes:

```bash
cd backend
./venv/bin/python manage_unprocessed_documents.py list
```

### Option 5: Dry Run (See What Would Happen)

Preview what would be deleted/reset without making changes:

```bash
cd backend
./venv/bin/python manage_unprocessed_documents.py dry-run
```

## Current Status

- **Total Unprocessed:** 26 documents
- **Pending:** 26 documents
- **Failed:** 0 documents
- **In Progress:** 0 documents

## Recommendation

**Option 1 (Delete)** is recommended if:
- You want a clean slate
- Files are still available to re-upload
- You want to ensure fresh processing

**Option 2 (Reprocess)** is recommended if:
- Files are already uploaded and you just want them processed
- Celery worker is running
- You want to keep existing upload records

## Examples

### Delete all unprocessed documents:
```bash
cd /Volumes/Orico/Anylab103/backend
./venv/bin/python manage_unprocessed_documents.py delete
# Type 'yes' when prompted
```

### Reprocess all pending documents:
```bash
cd /Volumes/Orico/Anylab103/backend
./venv/bin/python manage_unprocessed_documents.py reprocess
# Type 'yes' when prompted
# Make sure Celery worker is running!
```

