# Simplified Upload Queue Implementation Plan

## Overview
Simplify the upload queue workflow with:
- **4 Status Model**: `queued` → `uploading` → `processing` → `completed`
- **Redis for Active Jobs Only**: Fast queue, remove completed jobs from Redis
- **PostgreSQL for History**: Store all completed jobs in PostgreSQL
- **Early Duplicate Detection**: Check duplicates before temp file creation
- **Hash Calculation in Browser**: Calculate file hash before queueing

---

## Phase 1: Frontend - Hash Calculation & Early Job Creation

### 1.1 Create File Hash Utility
**File**: `frontend/src/utils/fileHash.ts` (NEW)

**Features**:
- Calculate SHA-256 hash of file using Web Crypto API
- Support chunked reading for large files
- Show progress for hash calculation
- Return hash as hex string

**Implementation**:
```typescript
export async function calculateFileHash(file: File, onProgress?: (progress: number) => void): Promise<string>
```

### 1.2 Update File Upload Handler
**File**: `frontend/src/components/AI/UnifiedUploadQueue.tsx`

**Changes**:
- Before creating FormData, calculate hash for each file
- Show progress indicator: "Calculating hash... X/Y files"
- Send file metadata (name, size, hash, type) to API
- **DO NOT** send file content in initial request
- API returns job_id immediately
- Background: Upload files to temp folder after job creation
- **Add retry/cancel/refresh features**:
  - Retry: Retry hash calculation for failed files
  - Cancel: Cancel hash calculation in progress
  - Refresh: Refresh hash calculation progress

**New Flow**:
1. User selects files
2. Calculate hashes (show progress) - **Can retry/cancel/refresh**
3. Call API: `POST /ai/upload/queue/` with metadata only - **Can retry/cancel**
4. API checks duplicates, creates job in Redis, returns job_id - **Can refresh status**
5. Background task: Upload files to temp folder - **Can retry/cancel/refresh**
6. Background task: Process files - **Can retry/cancel/refresh**

### 1.3 Update Folder Scan Handler
**File**: `frontend/src/components/AI/UnifiedUploadQueue.tsx`

**Changes**:
- After folder scan, calculate hashes for all files
- Show progress: "Preparing files... X/Y"
- Send file list with hashes to API
- Same flow as file upload

### 1.4 Update Webpage Scrape Handler
**File**: `frontend/src/components/AI/UnifiedUploadQueue.tsx`

**Changes**:
- After file discovery, if file size is known, calculate hash
- For files without size, skip hash calculation (will check during download)
- Send file list with hashes to API
- Same flow as file upload

---

## Phase 2: Backend - Duplicate Detection & Job Creation

### 2.1 Update Job Creation API
**File**: `backend/ai_assistant/views/upload_queue_views.py`

**Changes**:
- Accept file metadata (name, size, hash, type) instead of file content
- Check duplicates using hash BEFORE creating job
- If duplicate found:
  - Mark file as `completed` immediately
  - Set `upload_status: 'skipped'`
  - Set `processing_status: 'skipped'`
  - Set `uploaded_file_id` to existing file ID
- If not duplicate:
  - Create job in Redis with status `queued`
  - Return job_id immediately
- **DO NOT** save temp files in this endpoint

**New Endpoint Structure**:
```python
POST /ai/upload/queue/
{
  "job_type": "file|folder|webpage",
  "source": "path_or_url",
  "files": [
    {
      "name": "file.pdf",
      "size": 1024000,
      "hash": "sha256_hex_string",
      "type": "application/pdf"
    }
  ]
}
```

### 2.2 Create Background File Upload Task
**File**: `backend/ai_assistant/tasks/file_upload_tasks.py` (NEW)

**Features**:
- Receive job_id and file metadata from Redis
- Upload files to temp folder
- Update job status to `uploading`
- Process files (same as current `_process_single_file_async`)

**Task Flow**:
1. Get job from Redis
2. For each file in job:
   - If duplicate (already marked): Skip
   - If not duplicate: Upload to temp folder
   - Update file status in Redis
3. Update job status to `uploading`
4. Trigger file processing tasks

---

## Phase 3: Backend - Status Model Simplification

### 3.1 Update Status Choices
**File**: `backend/ai_assistant/models.py`

**Changes**:
- Simplify `STATUS_CHOICES` to 4 states:
  ```python
  STATUS_CHOICES = [
      ('queued', 'Queued'),
      ('uploading', 'Uploading'),
      ('processing', 'Processing'),
      ('completed', 'Completed'),
  ]
  ```

### 3.2 Update File Status Tracking
**File**: `backend/ai_assistant/tasks/task_helpers.py`

**Changes**:
- Simplify file status to 3 states:
  - `pending`: Not started
  - `processing`: Being uploaded/processed
  - `completed`: Done (ready, skipped, or failed)

**Remove**:
- Separate `upload_status` and `processing_status`
- Use single `status` field

### 3.3 Update Status Recalculation
**File**: `backend/ai_assistant/tasks/task_helpers.py`

**Changes**:
- Simplify `recalculate_job_status`:
  - Count `pending` files
  - Count `processing` files
  - Count `completed` files (ready + skipped + failed)
  - Job status:
    - `queued`: All files pending
    - `uploading`: Some files uploading (status = processing, no uploaded_file_id)
    - `processing`: Some files processing (status = processing, has uploaded_file_id)
    - `completed`: All files completed

---

## Phase 4: Backend - Redis for Active Jobs Only

### 4.1 Update Redis Job Queue Manager
**File**: `backend/ai_assistant/service_classes/redis_job_queue_manager.py`

**Changes**:
- Add method: `remove_job_from_redis(job_id)` - Remove job from Redis when completed
- Add method: `get_active_jobs()` - Get only active jobs (queued, uploading, processing)
- Update `add_job_fast`: Only add to Redis if status is active
- Update `update_job_status`: Remove from Redis if status is `completed`

**New Methods**:
```python
def remove_job_from_redis(self, job_id: str) -> bool:
    """Remove job from Redis when completed"""
    
def get_active_jobs(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get only active jobs from Redis"""
```

### 4.2 Update Queue Status Query
**File**: `backend/ai_assistant/service_classes/upload_queue_manager.py`

**Changes**:
- `get_queue_status()`:
  - Query active jobs from Redis (queued, uploading, processing)
  - Query completed jobs from PostgreSQL
  - Combine results
  - Remove completed jobs from Redis automatically

**New Logic**:
```python
def get_queue_status(self, user=None, status_filter=None, active_only: bool = False):
    # Get active jobs from Redis
    active_jobs = redis_job_queue_manager.get_active_jobs(user_id=user.id if user else None)
    
    # Get completed jobs from PostgreSQL
    completed_jobs = UploadJob.objects.filter(status='completed')
    if user:
        completed_jobs = completed_jobs.filter(created_by=user)
    
    # Combine and return
    return {
        'jobs': active_jobs + serialized_completed_jobs,
        'stats': {...}
    }
```

### 4.3 Update Job Completion Handler
**File**: `backend/ai_assistant/tasks/task_helpers.py`

**Changes**:
- When job status changes to `completed`:
  - Remove job from Redis
  - Ensure job is persisted in PostgreSQL
  - Log completion

**New Method**:
```python
def mark_job_completed(job_id: str):
    """Mark job as completed and remove from Redis"""
    # Update PostgreSQL
    job = UploadJob.objects.get(job_id=job_id)
    job.status = 'completed'
    job.completed_at = timezone.now()
    job.save()
    
    # Remove from Redis
    redis_job_queue_manager.remove_job_from_redis(job_id)
```

---

## Phase 5: Backend - Job Persistence Updates

### 5.1 Update Persistence Task
**File**: `backend/ai_assistant/tasks/job_persistence_tasks.py`

**Changes**:
- Only persist active jobs (queued, uploading, processing)
- Skip completed jobs (they're already in PostgreSQL)
- Remove completed jobs from Redis during persistence

**New Logic**:
```python
def persist_jobs_to_database(self, batch_size: int = 50):
    # Get pending jobs from Redis
    pending_jobs = redis_job_queue_manager.get_pending_persist_jobs(count=batch_size)
    
    for job_info in pending_jobs:
        job_data = redis_job_queue_manager.get_job_from_redis(job_id)
        
        # Skip if job is completed (shouldn't happen, but safety check)
        if job_data.get('status') == 'completed':
            # Remove from Redis, ensure in PostgreSQL
            redis_job_queue_manager.remove_job_from_redis(job_id)
            continue
        
        # Persist active job to PostgreSQL
        ...
```

---

## Phase 6: Frontend - Status Display Updates

### 6.1 Update Status Display
**File**: `frontend/src/components/AI/UnifiedUploadQueue.tsx`

**Changes**:
- Simplify status badges to 4 states:
  - `queued`: Blue badge "Queued"
  - `uploading`: Yellow badge "Uploading"
  - `processing`: Orange badge "Processing"
  - `completed`: Green badge "Completed"
- Remove complex status filtering logic
- Show progress: "X/Y files completed"

### 6.2 Update Active Jobs Filter
**File**: `frontend/src/components/AI/UnifiedUploadQueue.tsx`

**Changes**:
- Active jobs = `queued`, `uploading`, `processing`
- Completed jobs = `completed` (hidden from active view by default)
- Simplify filter logic

---

## Phase 7: Migration & Testing

### 7.1 Data Migration
**File**: `backend/ai_assistant/management/commands/migrate_job_statuses.py` (NEW)

**Tasks**:
- Migrate existing job statuses to new 4-state model:
  - `paused` → `queued` (with paused flag)
  - `partially_completed` → `processing`
  - `failed` → `completed` (with failed_items > 0)
  - `cancelled` → `completed` (with cancelled flag)
- Move completed jobs from Redis to PostgreSQL only
- Clean up Redis of old completed jobs

### 7.2 Testing Checklist
- [ ] File upload with hash calculation
- [ ] Duplicate detection before temp file creation
- [ ] Job creation in Redis (active jobs only)
- [ ] Job removal from Redis when completed
- [ ] Query active jobs from Redis
- [ ] Query completed jobs from PostgreSQL
- [ ] Status transitions: queued → uploading → processing → completed
- [ ] Folder scan workflow
- [ ] Webpage scrape workflow
- [ ] Large file hash calculation (progress indicator)
- [ ] Error handling (hash calculation fails, duplicate check fails)

---

## Implementation Order

1. **Phase 1**: Frontend hash calculation (can be done independently)
2. **Phase 2**: Backend duplicate detection & job creation
3. **Phase 3**: Status model simplification
4. **Phase 4**: Redis for active jobs only
5. **Phase 5**: Job persistence updates
6. **Phase 6**: Frontend status display
7. **Phase 7**: Retry, cancel & refresh features
8. **Phase 8**: Migration & testing

---

## Benefits

1. **Faster Queue**: Job created before temp file I/O (<5ms vs 100-500ms)
2. **Simpler Status**: 4 clear states vs 8+ states
3. **Early Duplicate Detection**: Saves time and resources
4. **Clear Separation**: Redis for queue, PostgreSQL for history
5. **Better UX**: Immediate feedback, progress indicators
6. **Easier Debugging**: Single status update path

---

## Potential Issues & Solutions

### Issue 1: Hash Calculation Time for Large Files
**Solution**: 
- Show progress indicator
- Calculate hash in chunks
- For very large files (>100MB), calculate hash during upload

### Issue 2: File Availability When Processing Starts
**Solution**:
- Background task saves temp files first
- Processing task waits for temp file availability
- Add retry logic if temp file not found

### Issue 3: Duplicate Check Accuracy
**Solution**:
- Use SHA-256 (same as backend)
- Validate hash format before sending
- Backend validates hash before checking duplicates

### Issue 4: Browser Compatibility
**Solution**:
- Use Web Crypto API (supported in modern browsers)
- Fallback: Calculate hash on server if browser doesn't support

---

## Estimated Time

- Phase 1: 4-6 hours
- Phase 2: 3-4 hours
- Phase 3: 2-3 hours
- Phase 4: 2-3 hours
- Phase 5: 1-2 hours
- Phase 6: 2-3 hours
- Phase 7: 6-8 hours (Retry, cancel & refresh features)
- Phase 8: 2-3 hours

**Total**: 21-31 hours

