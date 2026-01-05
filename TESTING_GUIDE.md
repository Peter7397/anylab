# Upload Queue Testing Guide

## Overview
This guide helps you test the simplified upload queue system with:
- 4-state status model (queued, uploading, processing, completed)
- Redis for active jobs only
- PostgreSQL for completed jobs
- Browser-side hash calculation
- Early duplicate detection

## Prerequisites
1. Backend and frontend are running
2. Redis is available and connected
3. PostgreSQL is running
4. You have access to the web UI

## Test 1: Basic File Upload (New File)

### Steps:
1. **Open Upload Queue** in the web UI
2. **Select a file** that you haven't uploaded before
3. **Click "Submit"**
4. **Observe:**
   - Hash calculation progress bar appears
   - Progress shows "Calculating hash... X/1 files"
   - After hash calculation, job is created immediately (< 1 second)
   - Success notification appears: "Job queued successfully! 1 new file(s), 0 duplicate(s) skipped"
   - Job appears in queue with status "Queued"

### Expected Results:
- ✅ Hash calculation completes (progress bar reaches 100%)
- ✅ Job appears in queue immediately (no waiting)
- ✅ Job status is "Queued"
- ✅ You can continue adding more files immediately

### Check Backend Logs:
```bash
docker compose logs backend --tail 50 | grep -i "job\|upload\|redis"
```
Look for:
- "Job {job_id} added to Redis queue"
- "Job queued successfully"

---

## Test 2: Duplicate File Detection

### Steps:
1. **Upload the same file again** (from Test 1)
2. **Click "Submit"**
3. **Observe:**
   - Hash calculation runs
   - Job is created immediately
   - Notification shows: "Job queued successfully! 0 new file(s), 1 duplicate(s) skipped"

### Expected Results:
- ✅ Duplicate is detected immediately
- ✅ File is marked as "skipped" in the job
- ✅ Job shows 0 new files, 1 duplicate
- ✅ No file content upload happens (duplicate doesn't need it)

### Check Job Details:
- Open the job in the queue
- Check file status: Should show "skipped" or "completed"
- Check `uploaded_file_id`: Should reference existing file

---

## Test 3: Multiple Files Upload

### Steps:
1. **Select 3-5 files** (mix of new and potentially duplicate)
2. **Click "Submit"**
3. **Observe:**
   - Hash calculation for all files (progress: 1/5, 2/5, etc.)
   - Job created with all files
   - Notification shows correct counts

### Expected Results:
- ✅ All files' hashes calculated
- ✅ Duplicates detected and marked
- ✅ New files queued for upload
- ✅ Job shows correct total files count

---

## Test 4: Job Status Progression

### Steps:
1. **Upload a new file** (from Test 1)
2. **Watch the job status change:**
   - Initial: "Queued"
   - After file upload starts: "Uploading"
   - After processing starts: "Processing"
   - When complete: "Completed"

### Expected Results:
- ✅ Status transitions: Queued → Uploading → Processing → Completed
- ✅ Progress updates in real-time
- ✅ File status shows individual file progress

### Check Redis (Active Jobs):
```bash
docker compose exec redis redis-cli SMEMBERS upload_jobs:active
```
Should show job IDs for active jobs only.

### Check PostgreSQL (Completed Jobs):
```bash
docker compose exec backend python manage.py shell
```
```python
from ai_assistant.models import UploadJob
completed = UploadJob.objects.filter(status='completed').order_by('-created_at')[:5]
for job in completed:
    print(f"{job.job_id}: {job.status}, created: {job.created_at}")
```

---

## Test 5: Active Jobs Filter

### Steps:
1. **Upload a file** and wait for it to complete
2. **Check the queue filter:**
   - Default should be "Active Jobs"
   - Completed job should NOT appear in "Active Jobs"
   - Switch to "All" to see completed jobs

### Expected Results:
- ✅ "Active Jobs" filter is default
- ✅ Completed jobs are hidden in "Active Jobs" view
- ✅ Completed jobs appear in "All" view
- ✅ Jobs with failures still appear in "Active Jobs"

---

## Test 6: Redis Cleanup (Job Completion)

### Steps:
1. **Upload a file** and wait for completion
2. **Check Redis:**
   ```bash
   docker compose exec redis redis-cli SMEMBERS upload_jobs:active
   ```
3. **Check PostgreSQL:**
   ```bash
   docker compose exec backend python manage.py shell
   ```
   ```python
   from ai_assistant.models import UploadJob
   job = UploadJob.objects.filter(status='completed').first()
   print(f"Job {job.job_id} in PostgreSQL: {job.status}")
   ```

### Expected Results:
- ✅ Completed job is NOT in Redis active jobs set
- ✅ Completed job IS in PostgreSQL
- ✅ Job status in PostgreSQL is "completed"

---

## Test 7: Job Persistence (Redis → PostgreSQL)

### Steps:
1. **Upload a file** (creates job in Redis)
2. **Immediately check Redis:**
   ```bash
   docker compose exec redis redis-cli HGETALL upload_job:{job_id}
   ```
3. **Wait 10-15 seconds** (persistence task runs every 10s)
4. **Check PostgreSQL:**
   ```bash
   docker compose exec backend python manage.py shell
   ```
   ```python
   from ai_assistant.models import UploadJob
   job = UploadJob.objects.get(job_id='{job_id}')
   print(f"Job persisted: {job.job_id}, status: {job.status}")
   ```

### Expected Results:
- ✅ Job appears in Redis immediately
- ✅ Job is persisted to PostgreSQL within 10-15 seconds
- ✅ Job data matches between Redis and PostgreSQL

---

## Test 8: Multiple Jobs Concurrently

### Steps:
1. **Upload 3 files quickly** (one after another)
2. **Don't wait** - just keep clicking "Submit"
3. **Observe:**
   - All jobs appear immediately
   - No blocking or waiting
   - Each job processes independently

### Expected Results:
- ✅ All 3 jobs created instantly (< 1 second each)
- ✅ All jobs appear in queue
- ✅ Jobs process in parallel
- ✅ No errors or conflicts

---

## Test 9: Error Handling

### Steps:
1. **Try uploading a corrupted file** (if possible)
2. **Or stop Redis** temporarily:
   ```bash
   docker compose stop redis
   ```
3. **Try uploading a file**
4. **Restart Redis:**
   ```bash
   docker compose start redis
   ```

### Expected Results:
- ✅ System handles errors gracefully
- ✅ Fallback to PostgreSQL if Redis unavailable
- ✅ Error messages are clear
- ✅ System recovers when Redis is back

---

## Test 10: Status Badge Display

### Steps:
1. **Upload files** and observe status badges
2. **Check badge colors and text:**
   - Queued: Blue/Green badge
   - Uploading: Yellow/Orange badge
   - Processing: Yellow/Orange badge
   - Completed: Green badge

### Expected Results:
- ✅ Status badges are clear and distinct
- ✅ Colors match status (queued=blue, processing=yellow, completed=green)
- ✅ Text is readable and accurate

---

## Verification Commands

### Check Redis Status:
```bash
docker compose exec redis redis-cli INFO stats
docker compose exec redis redis-cli SMEMBERS upload_jobs:active
docker compose exec redis redis-cli LLEN upload_jobs:pending_persist
```

### Check PostgreSQL Jobs:
```bash
docker compose exec backend python manage.py shell
```
```python
from ai_assistant.models import UploadJob
from django.utils import timezone
from datetime import timedelta

# Active jobs
active = UploadJob.objects.exclude(status='completed').count()
print(f"Active jobs: {active}")

# Completed jobs (last 24 hours)
recent = UploadJob.objects.filter(
    status='completed',
    created_at__gte=timezone.now() - timedelta(days=1)
).count()
print(f"Completed jobs (24h): {recent}")

# Jobs by status
from django.db.models import Count
status_counts = UploadJob.objects.values('status').annotate(count=Count('id'))
for s in status_counts:
    print(f"{s['status']}: {s['count']}")
```

### Check Backend Logs:
```bash
docker compose logs backend --tail 100 | grep -E "job|redis|status|completed"
```

### Check Frontend Console:
- Open browser DevTools (F12)
- Check Console for errors
- Check Network tab for API calls

---

## Common Issues & Solutions

### Issue: Job not appearing in queue
**Solution:**
- Check Redis connection: `docker compose logs backend | grep -i redis`
- Check job creation logs: `docker compose logs backend | grep -i "job.*added"`
- Refresh the queue page

### Issue: Duplicate not detected
**Solution:**
- Check hash calculation: Look for hash in browser console
- Check backend logs: `docker compose logs backend | grep -i duplicate`
- Verify file hash matches existing file

### Issue: Job stuck in "Queued"
**Solution:**
- Check Celery workers: `docker compose ps celery`
- Check processing logs: `docker compose logs celery --tail 50`
- Check job details for errors

### Issue: Completed job still in Redis
**Solution:**
- Wait a few seconds (cleanup happens on status update)
- Manually check: `docker compose exec redis redis-cli SMEMBERS upload_jobs:active`
- Check backend logs for cleanup: `docker compose logs backend | grep -i "remove.*redis"`

---

## Success Criteria

✅ All tests pass
✅ Jobs create instantly (< 1 second)
✅ Duplicates detected immediately
✅ Status transitions correctly
✅ Completed jobs removed from Redis
✅ Active jobs query from Redis
✅ Completed jobs query from PostgreSQL
✅ No errors in logs
✅ UI is responsive and clear

---

## Next Steps After Testing

If all tests pass:
1. ✅ Phase 3 & 4 implementation is successful
2. Proceed to Phase 6 (Frontend UI updates)
3. Proceed to Phase 7 (Retry/Cancel/Refresh features)

If issues found:
1. Document the issue
2. Check logs for errors
3. Verify Redis and PostgreSQL connections
4. Test individual components

