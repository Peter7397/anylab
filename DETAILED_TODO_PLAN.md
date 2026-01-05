# Detailed TODO Plan - Simplified Upload Queue Implementation

## Overview
This document provides a detailed breakdown of all tasks required to implement the simplified upload queue workflow. Each task includes specific implementation details, acceptance criteria, dependencies, and estimated time.

---

## Phase 1: Frontend - Hash Calculation & Early Job Creation

### Task 1.1: Create File Hash Utility
**File**: `frontend/src/utils/fileHash.ts` (NEW)  
**Estimated Time**: 2-3 hours  
**Dependencies**: None  
**Priority**: High

**Implementation Details**:
- Create new utility file for file hash calculation
- Use Web Crypto API (`crypto.subtle.digest`) for SHA-256 hashing
- Implement chunked reading for large files (read in 1MB chunks)
- Support progress callback for UI updates
- Handle errors gracefully (browser compatibility, file read errors)
- Return hash as lowercase hex string

**Acceptance Criteria**:
- [ ] Function calculates SHA-256 hash correctly for files of all sizes
- [ ] Progress callback fires at reasonable intervals (every 10% or 1MB)
- [ ] Works with files up to 500MB without blocking UI
- [ ] Returns consistent hash format (lowercase hex, 64 characters)
- [ ] Handles errors gracefully (shows error message, doesn't crash)
- [ ] TypeScript types are correct
- [ ] Unit tests pass

**Code Structure**:
```typescript
export async function calculateFileHash(
  file: File, 
  onProgress?: (progress: number) => void
): Promise<string>
```

---

### Task 1.2: Add Progress Callback Support
**File**: `frontend/src/utils/fileHash.ts`  
**Estimated Time**: 1 hour  
**Dependencies**: Task 1.1  
**Priority**: Medium

**Implementation Details**:
- Implement progress calculation based on bytes read
- Fire callback at regular intervals (not every chunk to avoid spam)
- Calculate progress as percentage (0-100)
- Handle edge cases (empty files, very small files)

**Acceptance Criteria**:
- [ ] Progress callback fires at reasonable intervals
- [ ] Progress values are accurate (0-100)
- [ ] Doesn't fire too frequently (max once per 5% or 1MB)
- [ ] Works correctly for files of all sizes

---

### Task 1.3: Update File Upload Handler
**File**: `frontend/src/components/AI/UnifiedUploadQueue.tsx`  
**Estimated Time**: 3-4 hours  
**Dependencies**: Tasks 1.1, 1.2  
**Priority**: High

**Implementation Details**:
- Import `calculateFileHash` utility
- Before creating FormData, calculate hash for each selected file
- Show progress indicator: "Calculating hash... X/Y files"
- Collect file metadata: `{name, size, hash, type}` for each file
- Send metadata array to API (JSON, not FormData)
- Remove file content from request (no `formData.append('files', file)`)
- Handle hash calculation errors (show error, allow retry)
- Update API call to use JSON body instead of FormData

**Acceptance Criteria**:
- [ ] Hash calculation happens before API call
- [ ] Progress indicator shows during hash calculation
- [ ] API receives file metadata (name, size, hash, type) as JSON
- [ ] No file content is sent in initial request
- [ ] Job is created immediately after metadata is sent
- [ ] Error handling works (hash calculation fails, API errors)
- [ ] UI remains responsive during hash calculation

**Code Changes**:
- Modify `handleFileUpload` function
- Add state for hash calculation progress
- Add UI component for progress indicator
- Update API call structure

---

### Task 1.4: Update Folder Scan Handler
**File**: `frontend/src/components/AI/UnifiedUploadQueue.tsx`  
**Estimated Time**: 2-3 hours  
**Dependencies**: Tasks 1.1, 1.2, 1.3  
**Priority**: High

**Implementation Details**:
- After folder scan completes, get file list
- For each file in scanned list, calculate hash
- Show progress: "Preparing files... X/Y"
- Collect metadata for all files
- Send file list with hashes to API (same as file upload)
- Handle files that can't be hashed (permissions, etc.)

**Acceptance Criteria**:
- [ ] Hash calculation happens after folder scan
- [ ] Progress indicator shows during hash calculation
- [ ] All scanned files get hashes calculated
- [ ] API receives file list with hashes
- [ ] Error handling works for files that can't be hashed

**Code Changes**:
- Modify `handleConfirmFolderUpload` function
- Add hash calculation step after folder scan
- Update progress indicator

---

### Task 1.5: Update Webpage Scrape Handler
**File**: `frontend/src/components/AI/UnifiedUploadQueue.tsx`  
**Estimated Time**: 2-3 hours  
**Dependencies**: Tasks 1.1, 1.2, 1.3  
**Priority**: Medium

**Implementation Details**:
- After file discovery, check if file size is known
- For files with known size, attempt to calculate hash (if file is accessible)
- For files without size or not accessible, skip hash calculation
- Show progress for files being hashed
- Send file list with hashes (where available) to API
- Note: Some files may not have hashes (will be checked during download)

**Acceptance Criteria**:
- [ ] Hash calculation happens for accessible files
- [ ] Files without size/access are handled gracefully
- [ ] Progress indicator shows during hash calculation
- [ ] API receives file list with hashes (where available)

**Code Changes**:
- Modify webpage file selection handler
- Add hash calculation for accessible files
- Handle files without hashes

---

### Task 1.6: Add Hash Calculation Progress UI
**File**: `frontend/src/components/AI/UnifiedUploadQueue.tsx`  
**Estimated Time**: 1-2 hours  
**Dependencies**: Tasks 1.3, 1.4, 1.5  
**Priority**: Medium

**Implementation Details**:
- Create progress indicator component
- Show "Calculating hash... X/Y files" message
- Display progress bar or percentage
- Show current file being processed
- Handle multiple files being hashed in parallel (if implemented)
- Dismiss progress indicator when complete

**Acceptance Criteria**:
- [ ] Progress indicator is visible during hash calculation
- [ ] Shows accurate progress (X/Y files)
- [ ] Doesn't block UI interaction
- [ ] Dismisses automatically when complete
- [ ] Shows errors if hash calculation fails

**Code Changes**:
- Add state for hash calculation progress
- Create progress indicator component
- Integrate into upload handlers

---

## Phase 2: Backend - Duplicate Detection & Job Creation

### Task 2.1: Update Job Creation API Endpoint
**File**: `backend/ai_assistant/views/upload_queue_views.py`  
**Estimated Time**: 3-4 hours  
**Dependencies**: None  
**Priority**: High

**Implementation Details**:
- Change endpoint to accept JSON body instead of FormData
- Accept file metadata array: `[{name, size, hash, type}, ...]`
- Remove temp file saving logic from this endpoint
- Validate request data (job_type, source, files array)
- Validate each file metadata (name, size, hash format, type)
- Return job_id immediately after Redis job creation

**Acceptance Criteria**:
- [ ] Endpoint accepts JSON body with file metadata
- [ ] Validates all required fields
- [ ] Validates hash format (SHA-256 hex string, 64 chars)
- [ ] No temp files are created in this endpoint
- [ ] Returns job_id immediately (<50ms response time)
- [ ] Error handling works (invalid data, missing fields)

**Code Changes**:
- Modify `create_upload_job` function
- Remove file handling logic (temp file creation)
- Add JSON body parsing
- Add validation logic

---

### Task 2.2: Implement Duplicate Detection
**File**: `backend/ai_assistant/views/upload_queue_views.py`  
**Estimated Time**: 2-3 hours  
**Dependencies**: Task 2.1  
**Priority**: High

**Implementation Details**:
- Before creating job, check each file hash for duplicates
- Use `UploadedFile.find_duplicates(file_hash=hash)` to check
- If duplicate found:
  - Mark file as `completed` immediately
  - Set `status: 'skipped'` in file metadata
  - Set `uploaded_file_id` to existing file ID
  - Set `uploaded_at` timestamp
- If not duplicate:
  - Add file to job normally
- Count duplicates vs new files
- Log duplicate detection results

**Acceptance Criteria**:
- [ ] Duplicate detection happens before job creation
- [ ] Duplicates are marked as `completed` with `skipped` status
- [ ] Existing file ID is correctly assigned to duplicates
- [ ] Non-duplicate files are added to job normally
- [ ] Duplicate count is accurate
- [ ] Logs show duplicate detection results

**Code Changes**:
- Add duplicate checking logic in `create_upload_job`
- Update file metadata for duplicates
- Add logging

---

### Task 2.3: Create Background File Upload Task
**File**: `backend/ai_assistant/tasks/file_upload_tasks.py` (NEW)  
**Estimated Time**: 4-5 hours  
**Dependencies**: Tasks 2.1, 2.2  
**Priority**: High

**Implementation Details**:
- Create new Celery task: `upload_files_to_temp`
- Receive job_id and file metadata from Redis
- For each file in job:
  - If duplicate (status = 'skipped'): Skip temp file creation
  - If not duplicate: Request file upload from frontend or read from source
  - Save file to temp folder
  - Update file status in Redis
- Update job status to `uploading` when files start uploading
- Trigger file processing tasks after upload

**Acceptance Criteria**:
- [ ] Task receives job_id and file metadata
- [ ] Duplicates are skipped (no temp file creation)
- [ ] Non-duplicate files are saved to temp folder
- [ ] File status is updated in Redis
- [ ] Job status is updated to `uploading`
- [ ] Processing tasks are triggered after upload
- [ ] Error handling works (file not found, permission errors)

**Code Changes**:
- Create new file `file_upload_tasks.py`
- Implement `upload_files_to_temp` task
- Add file upload logic
- Add status update logic

**Note**: This task may need to coordinate with frontend to receive file content. Consider:
- Option A: Frontend uploads files after job creation (separate endpoint)
- Option B: Files are read from source (folder path, URL) in background task
- Option C: Hybrid approach (files uploaded via separate endpoint, task processes them)

---

### Task 2.4: Update Job Creation to Return Immediately
**File**: `backend/ai_assistant/views/upload_queue_views.py`  
**Estimated Time**: 1 hour  
**Dependencies**: Tasks 2.1, 2.2  
**Priority**: High

**Implementation Details**:
- After duplicate check and Redis job creation, return immediately
- Don't wait for temp file creation
- Don't wait for file processing
- Return job_id, status, and basic job info
- Trigger background file upload task asynchronously

**Acceptance Criteria**:
- [ ] API returns in <50ms
- [ ] Job_id is returned immediately
- [ ] Background task is triggered
- [ ] No blocking operations in endpoint

**Code Changes**:
- Ensure no blocking I/O in `create_upload_job`
- Trigger background task
- Return immediately

---

### Task 2.5: Add Hash Validation in Backend
**File**: `backend/ai_assistant/views/upload_queue_views.py`  
**Estimated Time**: 1 hour  
**Dependencies**: Task 2.1  
**Priority**: Medium

**Implementation Details**:
- Validate hash format before duplicate checking
- Check: 64 character hex string (lowercase)
- Validate: Only contains 0-9, a-f characters
- Return error if hash format is invalid
- Log validation failures

**Acceptance Criteria**:
- [ ] Hash format is validated before duplicate check
- [ ] Invalid hashes are rejected with clear error message
- [ ] Valid hashes pass validation
- [ ] Error messages are user-friendly

**Code Changes**:
- Add hash validation function
- Call validation before duplicate check
- Add error handling

---

## Phase 3: Backend - Status Model Simplification

### Task 3.1: Update STATUS_CHOICES in Models
**File**: `backend/ai_assistant/models.py`  
**Estimated Time**: 1 hour  
**Dependencies**: None  
**Priority**: High

**Implementation Details**:
- Simplify `STATUS_CHOICES` to 4 states:
  - `queued`: Job created, waiting to start
  - `uploading`: Files being uploaded to storage
  - `processing`: Files being processed (metadata, chunking, embedding)
  - `completed`: All files finished (ready, skipped, or failed)
- Remove: `paused`, `partially_completed`, `failed`, `cancelled`
- Note: `paused` and `cancelled` can be handled with boolean flags
- Note: `failed` can be indicated by `failed_items > 0` with status `completed`

**Acceptance Criteria**:
- [ ] STATUS_CHOICES only contains 4 states
- [ ] Old status values are removed
- [ ] Database migration is created (if needed)
- [ ] All references to old statuses are updated

**Code Changes**:
- Update `STATUS_CHOICES` in `UploadJob` model
- Create database migration if needed

---

### Task 3.2: Simplify File Status Tracking
**File**: `backend/ai_assistant/tasks/task_helpers.py`  
**Estimated Time**: 3-4 hours  
**Dependencies**: Task 3.1  
**Priority**: High

**Implementation Details**:
- Remove separate `upload_status` and `processing_status` fields
- Use single `status` field with 3 states:
  - `pending`: Not started
  - `processing`: Being uploaded/processed
  - `completed`: Done (ready, skipped, or failed)
- Update all file status update functions
- Update file status checking logic

**Acceptance Criteria**:
- [ ] Single `status` field is used for files
- [ ] All file status updates use new field
- [ ] Status checking logic is updated
- [ ] No references to old status fields remain

**Code Changes**:
- Update `update_file_status_in_job` function
- Update all file status update calls
- Update file status checking logic

---

### Task 3.3: Update Status Recalculation Function
**File**: `backend/ai_assistant/tasks/task_helpers.py`  
**Estimated Time**: 2-3 hours  
**Dependencies**: Tasks 3.1, 3.2  
**Priority**: High

**Implementation Details**:
- Simplify `recalculate_job_status` logic:
  - Count `pending` files (status = 'pending')
  - Count `processing` files (status = 'processing')
  - Count `completed` files (status = 'completed')
  - Determine job status:
    - `queued`: All files pending
    - `uploading`: Some files processing, no uploaded_file_id
    - `processing`: Some files processing, has uploaded_file_id
    - `completed`: All files completed

**Acceptance Criteria**:
- [ ] Job status is calculated correctly
- [ ] Status transitions work correctly
- [ ] Edge cases are handled (empty jobs, all duplicates, etc.)

**Code Changes**:
- Update `recalculate_job_status` function
- Simplify status determination logic

---

### Task 3.4: Update All Status Update Calls
**File**: Multiple files  
**Estimated Time**: 2-3 hours  
**Dependencies**: Tasks 3.1, 3.2, 3.3  
**Priority**: High

**Implementation Details**:
- Find all references to `upload_status` and `processing_status`
- Replace with single `status` field
- Update status values to new 3-state model
- Test all status update paths

**Files to Update**:
- `backend/ai_assistant/tasks/file_processing_tasks.py`
- `backend/ai_assistant/tasks/task_helpers.py`
- `backend/ai_assistant/service_classes/upload_queue_manager.py`
- Any other files that update file status

**Acceptance Criteria**:
- [ ] All status update calls use new field
- [ ] All status values are correct
- [ ] No references to old status fields remain
- [ ] All tests pass

---

## Phase 4: Backend - Redis for Active Jobs Only

### Task 4.1: Add remove_job_from_redis Method
**File**: `backend/ai_assistant/service_classes/redis_job_queue_manager.py`  
**Estimated Time**: 1-2 hours  
**Dependencies**: None  
**Priority**: High

**Implementation Details**:
- Add method to remove job from Redis when completed
- Remove from job status hash
- Remove from active jobs set
- Remove from priority queue (if still there)
- Remove from pending persist list
- Return success/failure status

**Acceptance Criteria**:
- [ ] Job is completely removed from Redis
- [ ] All Redis keys related to job are removed
- [ ] Method returns success/failure status
- [ ] Errors are handled gracefully

**Code Changes**:
- Add `remove_job_from_redis` method
- Remove all Redis keys for job

---

### Task 4.2: Add get_active_jobs Method
**File**: `backend/ai_assistant/service_classes/redis_job_queue_manager.py`  
**Estimated Time**: 2-3 hours  
**Dependencies**: Task 4.1  
**Priority**: High

**Implementation Details**:
- Get all active jobs from Redis (status: queued, uploading, processing)
- Filter by user_id if provided
- Serialize job data for API response
- Return list of active jobs

**Acceptance Criteria**:
- [ ] Only active jobs are returned
- [ ] User filtering works correctly
- [ ] Job data is properly serialized
- [ ] Completed jobs are excluded

**Code Changes**:
- Add `get_active_jobs` method
- Filter by status
- Serialize job data

---

### Task 4.3: Update add_job_fast Method
**File**: `backend/ai_assistant/service_classes/redis_job_queue_manager.py`  
**Estimated Time**: 1 hour  
**Dependencies**: None  
**Priority**: Medium

**Implementation Details**:
- Only add job to Redis if status is active (not completed)
- Skip Redis addition if job is already completed (duplicates)
- Log skipped additions

**Acceptance Criteria**:
- [ ] Only active jobs are added to Redis
- [ ] Completed jobs are not added
- [ ] Logging is accurate

**Code Changes**:
- Add status check in `add_job_fast`
- Skip Redis addition for completed jobs

---

### Task 4.4: Update update_job_status Method
**File**: `backend/ai_assistant/service_classes/redis_job_queue_manager.py`  
**Estimated Time**: 1-2 hours  
**Dependencies**: Task 4.1  
**Priority**: High

**Implementation Details**:
- When status changes to `completed`, automatically remove from Redis
- Call `remove_job_from_redis` when status becomes completed
- Ensure job is persisted to PostgreSQL before removal
- Log removal

**Acceptance Criteria**:
- [ ] Completed jobs are automatically removed from Redis
- [ ] Job is persisted to PostgreSQL before removal
- [ ] Logging is accurate

**Code Changes**:
- Update `update_job_status` method
- Add automatic removal for completed jobs

---

### Task 4.5: Update get_queue_status Method
**File**: `backend/ai_assistant/service_classes/upload_queue_manager.py`  
**Estimated Time**: 3-4 hours  
**Dependencies**: Tasks 4.1, 4.2  
**Priority**: High

**Implementation Details**:
- Query active jobs from Redis using `get_active_jobs`
- Query completed jobs from PostgreSQL
- Combine results
- Apply filters (user, status_filter, active_only)
- Calculate statistics from both sources

**Acceptance Criteria**:
- [ ] Active jobs come from Redis
- [ ] Completed jobs come from PostgreSQL
- [ ] Results are properly combined
- [ ] Filters work correctly
- [ ] Statistics are accurate

**Code Changes**:
- Update `get_queue_status` method
- Query Redis for active jobs
- Query PostgreSQL for completed jobs
- Combine and return

---

### Task 4.6: Create mark_job_completed Helper
**File**: `backend/ai_assistant/tasks/task_helpers.py`  
**Estimated Time**: 1-2 hours  
**Dependencies**: Tasks 4.1, 4.5  
**Priority**: High

**Implementation Details**:
- Update PostgreSQL job status to `completed`
- Set `completed_at` timestamp
- Remove job from Redis
- Ensure job is persisted to PostgreSQL
- Log completion

**Acceptance Criteria**:
- [ ] Job status is updated in PostgreSQL
- [ ] Job is removed from Redis
- [ ] Timestamp is set correctly
- [ ] Logging is accurate

**Code Changes**:
- Add `mark_job_completed` function
- Update PostgreSQL
- Remove from Redis

---

## Phase 5: Backend - Job Persistence Updates

### Task 5.1: Update persist_jobs_to_database Task
**File**: `backend/ai_assistant/tasks/job_persistence_tasks.py`  
**Estimated Time**: 2-3 hours  
**Dependencies**: Tasks 4.1, 4.4  
**Priority**: High

**Implementation Details**:
- Skip completed jobs during persistence
- Remove completed jobs from Redis if found
- Only persist active jobs (queued, uploading, processing)
- Ensure completed jobs are already in PostgreSQL

**Acceptance Criteria**:
- [ ] Completed jobs are skipped
- [ ] Completed jobs are removed from Redis
- [ ] Only active jobs are persisted
- [ ] No duplicate persistence

**Code Changes**:
- Update `persist_jobs_to_database` task
- Add completed job check
- Remove completed jobs from Redis

---

### Task 5.2: Update Job Persistence Logic
**File**: `backend/ai_assistant/tasks/job_persistence_tasks.py`  
**Estimated Time**: 1-2 hours  
**Dependencies**: Task 5.1  
**Priority**: Medium

**Implementation Details**:
- Ensure persistence only happens for active jobs
- Add status check before persistence
- Log skipped jobs

**Acceptance Criteria**:
- [ ] Only active jobs are persisted
- [ ] Status check works correctly
- [ ] Logging is accurate

**Code Changes**:
- Add status check
- Update logging

---

## Phase 6: Frontend - Status Display Updates

### Task 6.1: Update Status Badges
**File**: `frontend/src/components/AI/UnifiedUploadQueue.tsx`  
**Estimated Time**: 2-3 hours  
**Dependencies**: Task 3.1  
**Priority**: High

**Implementation Details**:
- Simplify status badges to 4 states:
  - `queued`: Blue badge "Queued"
  - `uploading`: Yellow badge "Uploading"
  - `processing`: Orange badge "Processing"
  - `completed`: Green badge "Completed"
- Remove old status badges
- Update badge styling

**Acceptance Criteria**:
- [ ] Only 4 status badges are shown
- [ ] Badge colors are correct
- [ ] Badge text is correct
- [ ] Old badges are removed

**Code Changes**:
- Update status badge component
- Remove old status handling
- Update styling

---

### Task 6.2: Simplify Active Jobs Filter
**File**: `frontend/src/components/AI/UnifiedUploadQueue.tsx`  
**Estimated Time**: 2-3 hours  
**Dependencies**: Tasks 3.1, 6.1  
**Priority**: High

**Implementation Details**:
- Active jobs = `queued`, `uploading`, `processing`
- Completed jobs = `completed` (hidden from active view by default)
- Remove complex file-level status checking
- Simplify filter logic

**Acceptance Criteria**:
- [ ] Active jobs filter works correctly
- [ ] Completed jobs are hidden by default
- [ ] Filter logic is simple and clear
- [ ] No complex file-level checking

**Code Changes**:
- Update active jobs filter logic
- Remove complex file status checking
- Simplify filter conditions

---

### Task 6.3: Update Progress Display
**File**: `frontend/src/components/AI/UnifiedUploadQueue.tsx`  
**Estimated Time**: 1-2 hours  
**Dependencies**: Tasks 3.2, 6.1  
**Priority**: Medium

**Implementation Details**:
- Show simple "X/Y files completed" instead of complex status breakdown
- Remove detailed file status display
- Show overall job progress

**Acceptance Criteria**:
- [ ] Progress display is simple and clear
- [ ] Shows accurate file counts
- [ ] No complex status breakdown

**Code Changes**:
- Update progress display component
- Simplify progress calculation

---

### Task 6.4: Remove Complex Status Filtering Logic
**File**: `frontend/src/components/AI/UnifiedUploadQueue.tsx`  
**Estimated Time**: 1-2 hours  
**Dependencies**: Tasks 6.2, 6.3  
**Priority**: Medium

**Implementation Details**:
- Remove file-level status checking for active jobs filter
- Remove complex status aggregation logic
- Simplify job filtering

**Acceptance Criteria**:
- [ ] Complex logic is removed
- [ ] Filtering is simple and fast
- [ ] No performance issues

**Code Changes**:
- Remove complex filtering logic
- Simplify job filtering

---

## Phase 7: Retry, Cancel & Refresh Features

### Task 7.1: Hash Calculation Stage Controls
**File**: `frontend/src/components/AI/UnifiedUploadQueue.tsx`  
**Estimated Time**: 3-4 hours  
**Dependencies**: Tasks 1.1, 1.2, 1.3  
**Priority**: High

**Implementation Details**:
- **Retry**: Retry hash calculation for failed files
  - Show retry button for files with hash calculation errors
  - Recalculate hash for specific file
  - Update progress indicator
  - Handle retry errors gracefully
- **Cancel**: Cancel hash calculation in progress
  - Stop hash calculation for all files or specific file
  - Clear progress state
  - Allow user to modify file selection
  - Clean up any ongoing calculations
- **Refresh**: Refresh hash calculation progress
  - Update progress indicator
  - Show current file being processed
  - Display elapsed time
  - Update file status

**Acceptance Criteria**:
- [ ] Retry button appears for failed hash calculations
- [ ] Retry successfully recalculates hash
- [ ] Cancel stops hash calculation immediately
- [ ] Cancel clears progress state
- [ ] Refresh updates progress display
- [ ] All controls work for individual files and all files
- [ ] UI remains responsive during operations

**Code Changes**:
- Add state for hash calculation control (retry, cancel, refresh)
- Add UI buttons for retry/cancel/refresh
- Implement retry logic (recalculate hash for failed files)
- Implement cancel logic (stop calculation, clear state)
- Implement refresh logic (update progress display)

---

### Task 7.2: Job Creation Stage Controls
**File**: `frontend/src/components/AI/UnifiedUploadQueue.tsx`  
**File**: `backend/ai_assistant/views/upload_queue_views.py`  
**Estimated Time**: 3-4 hours  
**Dependencies**: Tasks 2.1, 2.2, 2.4  
**Priority**: High

**Implementation Details**:
- **Retry**: Retry job creation if it fails
  - Show retry button if job creation fails
  - Resend file metadata to API
  - Handle duplicate detection retry
  - Show retry progress
- **Cancel**: Cancel job creation
  - Cancel before job is created
  - Clear job creation state
  - Return to file selection
  - Clean up any partial state
- **Refresh**: Refresh job status after creation
  - Poll job status from API
  - Update job display
  - Show current job state
  - Update file statuses

**Backend Endpoints**:
- `POST /ai/upload/queue/retry/` - Retry job creation
- `POST /ai/upload/queue/cancel/` - Cancel job creation (if not yet created)
- `GET /ai/upload/queue/{job_id}/status/` - Get job status

**Acceptance Criteria**:
- [ ] Retry button appears if job creation fails
- [ ] Retry successfully creates job
- [ ] Cancel stops job creation
- [ ] Cancel clears state
- [ ] Refresh updates job status
- [ ] All controls work correctly
- [ ] Error handling works

**Code Changes**:
- Add retry endpoint in backend
- Add cancel endpoint in backend
- Add refresh endpoint in backend
- Add UI controls for retry/cancel/refresh
- Implement retry/cancel/refresh logic

---

### Task 7.3: File Upload Stage Controls
**File**: `frontend/src/components/AI/UnifiedUploadQueue.tsx`  
**File**: `backend/ai_assistant/tasks/file_upload_tasks.py`  
**File**: `backend/ai_assistant/views/upload_queue_views.py`  
**Estimated Time**: 4-5 hours  
**Dependencies**: Tasks 2.3, 4.1, 4.2  
**Priority**: High

**Implementation Details**:
- **Retry**: Retry failed file uploads
  - Retry specific failed files
  - Retry all failed files in job
  - Show retry progress
  - Handle retry errors
- **Cancel**: Cancel file upload
  - Cancel job upload (stop background task)
  - Cancel specific file upload
  - Clean up temp files
  - Update job status
- **Refresh**: Refresh upload progress
  - Poll upload status
  - Update file upload progress
  - Show current upload state
  - Update file statuses

**Backend Endpoints**:
- `POST /ai/upload/queue/{job_id}/retry-upload/` - Retry file uploads
- `POST /ai/upload/queue/{job_id}/cancel-upload/` - Cancel file upload
- `GET /ai/upload/queue/{job_id}/upload-status/` - Get upload status

**Task Updates**:
- Update file upload task to handle cancellation
- Add retry logic for failed uploads
- Add status polling support

**Acceptance Criteria**:
- [ ] Retry button appears for failed uploads
- [ ] Retry successfully uploads files
- [ ] Cancel stops upload immediately
- [ ] Cancel cleans up temp files
- [ ] Refresh updates upload progress
- [ ] All controls work for individual files and job
- [ ] Background task cancellation works

**Code Changes**:
- Add retry endpoint in backend
- Add cancel endpoint in backend
- Add refresh endpoint in backend
- Update file upload task for cancellation
- Add UI controls for retry/cancel/refresh
- Implement retry/cancel/refresh logic

---

### Task 7.4: Processing Stage Controls
**File**: `frontend/src/components/AI/UnifiedUploadQueue.tsx`  
**File**: `backend/ai_assistant/tasks/file_processing_tasks.py`  
**File**: `backend/ai_assistant/views/upload_queue_views.py`  
**Estimated Time**: 4-5 hours  
**Dependencies**: Tasks 3.1, 3.2, 4.1, 4.2  
**Priority**: High

**Implementation Details**:
- **Retry**: Retry failed file processing
  - Retry specific failed files
  - Retry all failed files in job
  - Show retry progress
  - Handle retry errors
- **Cancel**: Cancel file processing
  - Cancel job processing (stop background task)
  - Cancel specific file processing
  - Clean up processing state
  - Update job status
- **Refresh**: Refresh processing progress
  - Poll processing status
  - Update file processing progress
  - Show current processing state
  - Update file statuses

**Backend Endpoints**:
- `POST /ai/upload/queue/{job_id}/retry-processing/` - Retry file processing
- `POST /ai/upload/queue/{job_id}/cancel-processing/` - Cancel file processing
- `GET /ai/upload/queue/{job_id}/processing-status/` - Get processing status

**Task Updates**:
- Update processing task to handle cancellation
- Add retry logic for failed processing
- Add status polling support

**Acceptance Criteria**:
- [ ] Retry button appears for failed processing
- [ ] Retry successfully processes files
- [ ] Cancel stops processing immediately
- [ ] Cancel cleans up processing state
- [ ] Refresh updates processing progress
- [ ] All controls work for individual files and job
- [ ] Background task cancellation works

**Code Changes**:
- Add retry endpoint in backend
- Add cancel endpoint in backend
- Add refresh endpoint in backend
- Update processing task for cancellation
- Add UI controls for retry/cancel/refresh
- Implement retry/cancel/refresh logic

---

### Task 7.5: Unified Job Controls
**File**: `frontend/src/components/AI/UnifiedUploadQueue.tsx`  
**File**: `backend/ai_assistant/views/upload_queue_views.py`  
**Estimated Time**: 3-4 hours  
**Dependencies**: Tasks 7.2, 7.3, 7.4  
**Priority**: High

**Implementation Details**:
- **Retry Job**: Retry entire job from current stage
  - Detect current stage (queued, uploading, processing)
  - Retry from appropriate stage
  - Show retry progress
  - Handle retry errors
- **Cancel Job**: Cancel entire job
  - Cancel at any stage
  - Clean up all resources
  - Remove from active queue
  - Update job status
- **Refresh Job**: Refresh job status
  - Poll job status
  - Update all job information
  - Refresh file statuses
  - Update progress indicators

**Backend Endpoints**:
- `POST /ai/upload/queue/{job_id}/retry/` - Retry job from current stage
- `POST /ai/upload/queue/{job_id}/cancel/` - Cancel entire job
- `GET /ai/upload/queue/{job_id}/refresh/` - Refresh job status

**Acceptance Criteria**:
- [ ] Retry button appears for failed jobs
- [ ] Retry detects current stage correctly
- [ ] Retry retries from appropriate stage
- [ ] Cancel stops job at any stage
- [ ] Cancel cleans up all resources
- [ ] Refresh updates all job information
- [ ] All controls work correctly
- [ ] Stage detection is accurate

**Code Changes**:
- Add unified retry endpoint in backend
- Add unified cancel endpoint in backend
- Add unified refresh endpoint in backend
- Add UI controls in job card
- Implement stage detection logic
- Implement retry/cancel/refresh logic

---

## Phase 8: Migration & Testing

### Task 8.1: Create Migration Command
**File**: `backend/ai_assistant/management/commands/migrate_job_statuses.py` (NEW)  
**Estimated Time**: 3-4 hours  
**Dependencies**: Tasks 3.1, 4.1  
**Priority**: High

**Implementation Details**:
- Create Django management command
- Migrate existing job statuses to new 4-state model:
  - `paused` → `queued` (with paused flag)
  - `partially_completed` → `processing`
  - `failed` → `completed` (with failed_items > 0)
  - `cancelled` → `completed` (with cancelled flag)
- Move completed jobs from Redis to PostgreSQL
- Clean up Redis of old completed jobs
- Add dry-run mode
- Add rollback capability

**Acceptance Criteria**:
- [ ] All job statuses are migrated correctly
- [ ] Completed jobs are moved to PostgreSQL
- [ ] Redis is cleaned up
- [ ] Dry-run mode works
- [ ] Rollback works (if implemented)

**Code Changes**:
- Create migration command
- Implement status migration logic
- Implement Redis cleanup

---

### Task 8.2: Move Completed Jobs from Redis to PostgreSQL
**File**: `backend/ai_assistant/management/commands/migrate_job_statuses.py`  
**Estimated Time**: 2-3 hours  
**Dependencies**: Task 8.1  
**Priority**: High

**Implementation Details**:
- Find all completed jobs in Redis
- Ensure they exist in PostgreSQL (create if missing)
- Remove from Redis
- Log migration results

**Acceptance Criteria**:
- [ ] All completed jobs are moved
- [ ] Jobs exist in PostgreSQL
- [ ] Jobs are removed from Redis
- [ ] Logging is accurate

**Code Changes**:
- Add Redis to PostgreSQL migration logic
- Add job creation if missing

---

### Task 8.3: Test File Upload with Hash Calculation
**Estimated Time**: 1-2 hours  
**Dependencies**: Tasks 1.1-1.6, 2.1-2.5  
**Priority**: High

**Test Cases**:
- [ ] Small file (<1MB) hash calculation
- [ ] Medium file (1-10MB) hash calculation
- [ ] Large file (10-100MB) hash calculation
- [ ] Very large file (>100MB) hash calculation
- [ ] Multiple files hash calculation
- [ ] Hash calculation progress indicator
- [ ] Hash calculation error handling
- [ ] Job creation after hash calculation
- [ ] Duplicate detection with hash

---

### Task 8.4: Test Duplicate Detection
**Estimated Time**: 1-2 hours  
**Dependencies**: Tasks 2.2, 2.5  
**Priority**: High

**Test Cases**:
- [ ] Duplicate detected before temp file creation
- [ ] Duplicate marked as completed immediately
- [ ] Duplicate has correct uploaded_file_id
- [ ] Non-duplicate files are processed normally
- [ ] Multiple duplicates in one job
- [ ] Mixed duplicates and new files
- [ ] Invalid hash format handling

---

### Task 8.5: Test Redis Active Jobs Only
**Estimated Time**: 1-2 hours  
**Dependencies**: Tasks 4.1-4.6  
**Priority**: High

**Test Cases**:
- [ ] Active jobs are in Redis
- [ ] Completed jobs are removed from Redis
- [ ] Query active jobs from Redis works
- [ ] Query completed jobs from PostgreSQL works
- [ ] Job removal from Redis works
- [ ] No completed jobs in Redis after completion

---

### Task 8.6: Test PostgreSQL History
**Estimated Time**: 1-2 hours  
**Dependencies**: Tasks 4.5, 5.1, 5.2  
**Priority**: High

**Test Cases**:
- [ ] Completed jobs are in PostgreSQL
- [ ] Completed jobs are queryable
- [ ] Completed jobs are not in Redis
- [ ] Job history is preserved
- [ ] Statistics are accurate

---

### Task 8.7: Test Status Transitions
**Estimated Time**: 2-3 hours  
**Dependencies**: Tasks 3.1-3.4, 4.1-4.6  
**Priority**: High

**Test Cases**:
- [ ] queued → uploading transition
- [ ] uploading → processing transition
- [ ] processing → completed transition
- [ ] Status updates are immediate
- [ ] Status updates are accurate
- [ ] Edge cases (all duplicates, all failed, etc.)

---

### Task 8.8: Test Folder Scan Workflow
**Estimated Time**: 1-2 hours  
**Dependencies**: Tasks 1.4, 2.1-2.5  
**Priority**: Medium

**Test Cases**:
- [ ] Folder scan works
- [ ] Hash calculation for scanned files
- [ ] Duplicate detection for scanned files
- [ ] Job creation for folder upload
- [ ] File processing for folder upload

---

### Task 8.9: Test Webpage Scrape Workflow
**Estimated Time**: 1-2 hours  
**Dependencies**: Tasks 1.5, 2.1-2.5  
**Priority**: Medium

**Test Cases**:
- [ ] Webpage discovery works
- [ ] Hash calculation for discovered files (when possible)
- [ ] Duplicate detection for discovered files
- [ ] Job creation for webpage upload
- [ ] File processing for webpage upload

---

### Task 8.10: Test Large File Hash Calculation
**Estimated Time**: 1-2 hours  
**Dependencies**: Tasks 1.1, 1.2, 1.6  
**Priority**: Medium

**Test Cases**:
- [ ] Progress indicator works for large files
- [ ] Hash calculation doesn't block UI
- [ ] Hash calculation completes successfully
- [ ] Error handling for very large files

---

### Task 8.11: Test Retry, Cancel & Refresh Features
**Estimated Time**: 3-4 hours  
**Dependencies**: Tasks 7.1-7.5  
**Priority**: High

**Test Cases**:
- [ ] Retry hash calculation for failed files
- [ ] Cancel hash calculation in progress
- [ ] Refresh hash calculation progress
- [ ] Retry job creation if it fails
- [ ] Cancel job creation
- [ ] Refresh job status after creation
- [ ] Retry failed file uploads
- [ ] Cancel file upload
- [ ] Refresh upload progress
- [ ] Retry failed file processing
- [ ] Cancel file processing
- [ ] Refresh processing progress
- [ ] Unified job retry/cancel/refresh
- [ ] Stage detection for retry
- [ ] Error handling for all controls

---

### Task 8.12: Test Error Handling
**Estimated Time**: 2-3 hours  
**Dependencies**: All previous tasks  
**Priority**: High

**Test Cases**:
- [ ] Hash calculation fails gracefully
- [ ] Duplicate check fails gracefully
- [ ] Redis errors are handled
- [ ] PostgreSQL errors are handled
- [ ] File upload errors are handled
- [ ] Job creation errors are handled
- [ ] Status update errors are handled

---

## Summary

**Total Tasks**: 36  
**Total Estimated Time**: 75-100 hours  
**Phases**: 8  
**Priority Breakdown**:
- High Priority: 25 tasks
- Medium Priority: 11 tasks

**Dependencies**:
- Phase 1 can be done independently
- Phase 2 depends on Phase 1
- Phase 3 depends on Phase 2
- Phase 4 depends on Phase 3
- Phase 5 depends on Phase 4
- Phase 6 depends on Phase 3
- Phase 7 depends on Phases 1-4 (retry/cancel/refresh features)
- Phase 8 depends on all previous phases

**Critical Path**:
1. Phase 1 (Frontend hash calculation)
2. Phase 2 (Backend duplicate detection)
3. Phase 3 (Status simplification)
4. Phase 4 (Redis active jobs only)
5. Phase 5 (Persistence updates)
6. Phase 6 (Frontend display)
7. Phase 7 (Retry, cancel & refresh features)
8. Phase 8 (Migration & testing)

