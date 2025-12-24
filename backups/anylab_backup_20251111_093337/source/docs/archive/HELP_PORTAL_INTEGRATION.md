# Help Portal Integration Guide

## Overview

A new system has been created to manage and track help portal documentation for the RAG (Retrieval-Augmented Generation) system. This allows you to:

1. **Track help portal documents** from `/backend/media/documents/help_portal/docs/EN/`
2. **Process documents** and create embeddings for RAG search
3. **Monitor processing status** via a web UI
4. **View statistics** on document processing

## Files Created

### Backend

1. **Model**: `backend/ai_assistant/models.py`
   - Added `HelpPortalDocument` model to track document processing status
   - Tracks status, category, version, chunk count, processing dates

2. **Management Command**: `backend/ai_assistant/management/commands/import_help_portal.py`
   - Batch imports and processes help portal PDFs
   - Creates embeddings using existing RAG infrastructure
   - Classifies documents by product (CDS, ECM, etc.)

3. **API Views**: `backend/ai_assistant/views/help_portal_views.py`
   - `GET /api/ai/help-portal/` - List documents with filters
   - `GET /api/ai/help-portal/statistics/` - Get processing statistics

4. **Serializers**: `backend/ai_assistant/serializers.py`
   - Added `HelpPortalDocumentSerializer` for API responses

5. **URLs**: `backend/ai_assistant/urls/help_portal_urls.py`
   - Added routes for help portal endpoints

### Frontend

1. **Component**: `frontend/src/components/AI/HelpPortal.tsx`
   - UI for viewing help portal documents
   - Shows statistics, status badges, filtering
   - Reuses existing Document Management patterns

2. **Routing**: `frontend/src/App.tsx`
   - Added route: `/ai/knowledge/help-portal`
   - Accessible from sidebar navigation

## How to Use

### 1. Access the UI

Navigate to: **http://localhost:3000/ai/knowledge/help-portal**

The sidebar already has the link under "Knowledge Library" → "Help Portal"

### 2. Import Help Portal Documents

Run the management command to import and process all help portal documents:

```bash
cd backend
source venv/bin/activate
python manage.py import_help_portal
```

**Options:**
- `--force` - Reprocess documents even if already processed

**What it does:**
- Scans `/backend/media/documents/help_portal/docs/EN/` for PDF files
- Calculates file hashes for deduplication
- Classifies documents by product (CDS, ECM, etc.)
- Extracts document type (Installation Guide, Release Notes, etc.)
- Processes PDFs and creates embeddings
- Stores in `UploadedFile` and `DocumentChunk` models

### 3. View Status

After running the import command, refresh the UI to see:
- **Total documents** discovered
- **Processing status** for each document:
  - ✅ Completed (embedded and ready for RAG)
  - ⏱️ Pending (not yet processed)
  - 🔄 Processing (currently being processed)
  - ❌ Failed (processing failed with error message)
  - ⏭️ Skipped (already processed, duplicate)
- **Category breakdown** (OpenLab CDS, ECM XT, etc.)
- **Chunk count** (number of embedded chunks per document)

### 4. Filter Documents

Use the filter dropdowns to:
- Filter by **category** (CDS, ECM, Test Services, etc.)
- Filter by **status** (Completed, Failed, Pending, etc.)
- Click **Refresh** to reload data

## Document Categories

The system automatically classifies documents:

- **OpenLab CDS** (`cds`) - CDS-related documentation
- **OpenLab Server/ECM XT** (`ecm`) - ECM and server docs
- **Test Services** (`services`) - Test Services docs
- **Shared Services** (`shared`) - BalanceBridge, Sample Scheduler
- **Other** (`other`) - Uncategorized docs

## Document Types Detected

The system extracts document types from filenames:

- Installation Guide
- Administration Guide
- User Guide
- Release Notes
- Requirements Document
- Configuration Guide
- Quick Reference
- Quality Declaration
- Documentation (default)

## Integration with RAG

Once documents are processed (status = "completed"), they are automatically available for RAG search:

1. Documents are stored in `UploadedFile` model
2. Text chunks are extracted per page
3. Embeddings are generated and stored in `DocumentChunk` model
4. RAG queries can find and use this content

## Statistics

The UI shows real-time statistics:

- **Total**: All documents discovered
- **Completed**: Successfully processed and embedded
- **Pending**: Awaiting processing
- **Processing**: Currently being processed
- **Failed**: Processing failed (check error messages)
- **Skipped**: Already processed (duplicates)

## Adding New Documents

To add new help portal documents:

1. Place PDF files in `/backend/media/documents/help_portal/docs/EN/`
2. Run `python manage.py import_help_portal`
3. The system will:
   - Detect new files via hash comparison
   - Process only new/updated files
   - Track duplicates and skip them

## Error Handling

Failed documents show error messages in the UI. Common issues:

- **Corrupted PDF**: Fix or remove the file
- **Large file**: May timeout, check server logs
- **Encoding issues**: Check PDF structure

To retry failed documents:
```bash
python manage.py import_help_portal --force
```

## Database Schema

The `HelpPortalDocument` model tracks:

- `filename` - Document name
- `file_path` - Full path to file
- `file_size` - Size in bytes
- `file_hash` - MD5 hash for deduplication
- `category` - Product category
- `document_type` - Type of document
- `version` - Product version (v2.8, v3.6, etc.)
- `status` - Processing status
- `chunk_count` - Number of embedded chunks
- `discovered_at` - When first discovered
- `processed_at` - When processing completed
- `error_message` - Error details if failed
- `uploaded_file` - Link to UploadedFile record
- `metadata` - Additional JSON metadata

## Next Steps

1. Run the import command to process existing documents
2. Monitor the UI to track processing status
3. Use the documents in RAG queries
4. Add new documents as needed by placing them in the folder

## UI Features

- **Responsive design** - Works on all screen sizes
- **Real-time statistics** - See progress at a glance
- **Status badges** - Color-coded status indicators
- **Filters** - Easy filtering by category and status
- **Error messages** - View detailed error information
- **Refresh button** - Reload data anytime

The UI follows the same patterns as SSB Database and Document Manager for consistency.

