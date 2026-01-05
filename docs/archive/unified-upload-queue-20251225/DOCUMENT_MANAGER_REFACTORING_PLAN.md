# DocumentManager UI Refactoring Plan

## Goals
1. Remove redundant bulk upload features (now handled by UnifiedUploadQueue)
2. Simplify upload to use unified queue by default
3. Add navigation to UnifiedUploadQueue for advanced features
4. Remove unnecessary state management
5. Keep document listing, search, and management features

## Changes to Make

### 1. Remove State Variables
- `showBulkUploadModal` - Remove bulk upload modal
- `bulkFiles` - Server-side folder files
- `bulkFileMetadata` - Browser folder metadata
- `bulkProcessing` - Bulk processing state
- `bulkResults` - Bulk import results
- `selectedFolder` - Server folder path
- `uploadSource` - Browser vs server toggle
- `bulkApplyProductKey` - Bulk apply dropdown keys
- `bulkApplyContentTypeKey` - Bulk apply dropdown keys
- `enabledFileTypes` - File type filtering (keep if useful)
- `filteredOutFiles` - Filtered files
- `importStatus` - Import status tracking
- `progressInterval` - Progress polling
- `jobMonitoring` - Job monitoring state
- `autoRefreshEnabled` - Auto refresh toggle (keep if useful)

### 2. Remove Functions
- `handleBulkImport` - Server-side bulk import
- `handleBulkImportFromBrowser` - Browser folder import
- `handleScanFolder` - Server folder scanning
- `handleFolderSelect` - Browser folder selection
- `startJobMonitoring` - Job status polling

### 3. Simplify Upload
- Remove `useUploadQueue` checkbox - always use queue
- Simplify `handleUpload` to always use unified queue
- Remove `uploadFilesInBatches` complexity - queue handles it
- Simplify upload progress tracking

### 4. Add Navigation
- Add `useNavigate` import
- Add button/link to navigate to `/ai/knowledge/upload` for advanced features
- Update header buttons

### 5. Remove UI Components
- Remove entire bulk upload modal (lines ~2027-2550)
- Remove bulk import button from header
- Simplify upload modal

## Files to Modify
- `frontend/src/components/AI/DocumentManager.tsx`

