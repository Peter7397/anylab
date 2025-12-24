# SSB Import with MHTML Support - Implementation Summary

## Overview
Enhanced the SSB import functionality to support MHTML (MIME HTML) files in addition to regular HTML and text files.

## Changes Made

### 1. Frontend - File Upload Support
**File:** `frontend/src/components/AI/SSBDatabase.tsx`
- Added `.mhtml` to accepted file types
- Added `Upload` icon from lucide-react
- Created hidden file input with accept attribute: `.html,.txt,.text,.mhtml`
- Implemented `handleImportClick()` to trigger file picker
- Implemented `handleFileImport()` to process uploaded files and call backend API

### 2. Frontend - API Client Integration
**File:** `frontend/src/services/api.ts`
- Added `importSSBFile(file: File)` method
- Uses FormData for file upload
- Calls `/api/ai/ssb/import/` endpoint
- Returns promise with import results

### 3. Backend - Import Endpoint
**File:** `backend/ai_assistant/views/ssb_views.py`
- Added `import_ssb_file()` view function
- Supports authentication via `@permission_classes([IsAuthenticated])`
- Handles file upload with `request.FILES['file']`
- Multiple encoding support:
  - UTF-8 (primary)
  - Latin-1 (fallback for special characters)
- Extensive logging for debugging:
  - File name and size logging
  - Keyword sections found
  - Total KPRs extracted
  - Import/update/skip counts
- Error handling with detailed messages
- Returns structured response with imported/updated/skipped counts

### 4. Backend - KPR Parser Enhancement
**File:** `backend/ai_assistant/kpr_index_parser.py`
- Enhanced `parse_index_content()` to detect and handle MHTML format
- Added `_extract_html_from_mhtml()` method:
  - Detects MHTML by checking for 'From:' header or 'boundary=' pattern
  - Extracts HTML content from MHTML boundaries
  - Falls back to raw text parsing if HTML extraction fails
- Maintains compatibility with regular HTML and text files

### 5. Backend - URL Routing
**File:** `backend/ai_assistant/urls/ssb_urls.py`
- Added `path('import/', import_ssb_file, name='ssb_import')`
- Route is accessible at `/api/ai/ssb/import/`

## How to Use

### Import Process:
1. Navigate to `http://localhost:3000/ai/knowledge/ssb`
2. Click **"Import SSB File"** button (upload icon)
3. Select a file (HTML, TXT, or MHTML format)
4. Wait for import to complete
5. Success message shows imported/updated counts
6. Data automatically refreshes to show new entries

### File Format Requirements:
The parser looks for these patterns in the file:
- **Keyword sections:** Lines starting with `Keyword:`
- **KPR entries:** Lines starting with `KPR#:` followed by number and title
Example:
```
Keyword: 68xx Driver
KPR#:147 6890N with 7693 barcode scanning...
KPR#:148 Customer can't install column...
```

### Supported File Formats:
- ✅ `.html` - Standard HTML files
- ✅ `.txt` - Plain text files
- ✅ `.mhtml` - MIME HTML (single-file websites)
- ✅ `.text` - Alternative text extension

### MHTML Detection:
The system automatically detects MHTML files by checking for:
1. `From:` header at the start
2. `boundary=` pattern in headers

## Error Handling

### Import Errors:
- **"No file provided"** - User didn't select a file
- **"No KPR entries found"** - File doesn't contain KPR# patterns
- **"Unable to decode file"** - Encoding issues
- **"Authentication failed"** - User not logged in

### Debugging:
Check backend logs (`backend/logs/anylab.log`) for:
- File processing details
- Number of KPRs extracted
- Import success/failure per entry
- Encoding information

## Testing
To test the import:
1. Save the Agilent KPR index page as HTML or MHTML
2. Use File → Save As → "Web Page, Complete" (MHTML) or "Web Page, HTML Only"
3. Navigate to SSB Database page
4. Click "Import SSB File"
5. Select the saved file
6. Verify entries appear in the database

## Next Steps
- Test with actual MHTML file from user
- Monitor logs for any parsing issues
- Consider adding preview before import
- Add support for drag-and-drop file upload

