# Testing Upload Queue Immediate Response

## Quick Test Steps

### 1. **Monitor Backend Logs (Terminal 1)**
```bash
# Watch for upload requests and timing
docker logs -f anylab_backend 2>&1 | grep -E "create_upload_job|Created upload job|job_id"
```

### 2. **Monitor Celery Worker (Terminal 2)**
```bash
# Watch for job processing
docker logs -f anylab_celery_worker 2>&1 | grep -E "Processing upload job|_process_file_upload|Successfully uploaded"
```

### 3. **Test via UI**

#### Option A: Via Unified Upload Queue Page
1. Open browser: `http://localhost:3000/ai/knowledge/upload` (or your frontend URL)
2. Click "File" tab
3. Select a file (try a small file first, like a PDF < 5MB)
4. Click "Upload Files"
5. **Expected**: Job should appear in queue **immediately** (< 1 second)
6. **Check**: Look at browser Network tab - the POST request should complete in < 200ms

#### Option B: Via Document Manager
1. Navigate to Document Manager
2. Click "Upload" button
3. Select file(s)
4. Click "Queue Files" (if using unified queue option)
5. **Expected**: Immediate response, job appears in queue

### 4. **Verify Immediate Response**

#### Check Response Time in Browser:
1. Open Browser DevTools (F12)
2. Go to Network tab
3. Filter by "queue"
4. Upload a file
5. **Expected**: POST to `/ai/upload/queue/` should complete in **< 200ms**

#### Check Queue Status:
```bash
# Get queue status via API
curl -X GET http://localhost:8000/api/ai/upload/queue/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  | jq '.jobs[0] | {job_id, status, created_at, total_items}'
```

### 5. **Performance Benchmarks**

**Expected Performance:**
- **Small file (< 5MB)**: < 200ms response time
- **Medium file (5-20MB)**: < 500ms response time  
- **Large file (> 20MB)**: < 1s response time (temp file write)

**What to Look For:**
- ✅ Job appears in queue immediately after upload
- ✅ Browser shows fast response (< 200ms for small files)
- ✅ Backend logs show "Created upload job" quickly
- ✅ Celery starts processing shortly after (1-2 seconds)

### 6. **Troubleshooting**

#### If still slow:
```bash
# Check if temp directory exists and is writable
docker compose exec backend ls -la /app/media/temp

# Check file system performance
docker compose exec backend time dd if=/dev/zero of=/app/media/temp/test.bin bs=1M count=10

# Check Docker volume mount performance
docker compose exec backend df -h /app/media
```

#### Check for blocking operations:
```bash
# Monitor backend during upload
docker stats anylab_backend --no-stream

# Check for errors
docker logs anylab_backend --since 5m | grep -i error
```

### 7. **Test Different File Sizes**

```bash
# Create test files
docker compose exec backend bash -c "
  # Small file (1MB)
  dd if=/dev/zero of=/app/media/temp/test_small.pdf bs=1M count=1
  
  # Medium file (10MB)
  dd if=/dev/zero of=/app/media/temp/test_medium.pdf bs=1M count=10
  
  # Large file (50MB)
  dd if=/dev/zero of=/app/media/temp/test_large.pdf bs=1M count=50
"
```

Then test uploading each via UI and measure response times.

### 8. **API Test (Direct)**

```bash
# Test with curl (replace with your auth token)
TOKEN="your_auth_token_here"
FILE="test.pdf"

time curl -X POST http://localhost:8000/api/ai/upload/queue/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "job_type=file" \
  -F "source=file_upload" \
  -F "priority=5" \
  -F "file=@$FILE" \
  -w "\nTime: %{time_total}s\n"
```

**Expected**: `Time: 0.1-0.3s` for small files

## Success Criteria

✅ **Job created immediately** (< 200ms for small files)  
✅ **No blocking** - UI remains responsive  
✅ **Job appears in queue** right after upload  
✅ **Celery processes** in background (1-2 seconds later)  
✅ **No errors** in logs  

## Current Status

After the optimization:
- ✅ All files use temp file approach (no blocking storage.save)
- ✅ Job created immediately after temp file write
- ✅ Celery handles all file processing
- ✅ Temp files cleaned up after processing

