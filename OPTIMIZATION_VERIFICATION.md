# Optimization Verification Guide

## Date: 2026-01-05

## All Optimizations Implemented ✅

### OPT-1: Celery Worker Pool & Concurrency ✅ VERIFIED
- **Status**: ✅ Tested and verified
- **Configuration**: 
  - Main worker: `prefork` pool, `concurrency=4` ✅
  - OCR worker: `prefork` pool, `concurrency=2` ✅
- **Verification**: Confirmed in logs and worker stats

### OPT-2: Batch File Uploads ✅ IMPLEMENTED
- **Status**: ✅ Ready for testing
- **Backend**: 
  - Endpoint: `POST /ai/upload/queue/<job_id>/upload-files/` ✅
  - Accepts 5-10 files per request ✅
  - Error handling for partial failures ✅
- **Frontend**:
  - Files batched into groups of 8 ✅
  - Fallback to individual uploads if batch fails ✅
- **Test**: Upload multiple files via frontend UI

### OPT-3: Batch Database Updates ✅ IMPLEMENTED
- **Status**: ✅ Ready for testing
- **Backend**:
  - Function: `bulk_update_file_statuses_in_job()` ✅
  - Optimized `_process_single_file_async` to reduce redundant updates ✅
  - Reduced from 3-4 calls to 1-2 calls per file ✅
- **Test**: Monitor database update frequency during file processing

### OPT-4: Embedding Batch Size ✅ IMPLEMENTED
- **Status**: ✅ Ready for testing
- **Configuration**:
  - Batch size: 50 → 100 chunks per API call ✅
  - Max batch size: 200 (safety limit) ✅
- **Test**: Upload document and check embedding logs

---

## Testing Instructions

### Test 1: Batch File Upload (OPT-2)
1. Open frontend upload queue
2. Select 10 files to upload
3. Open browser DevTools → Network tab
4. Upload files
5. **Expected**: Should see 2 requests to `/upload-files/` endpoint (8 files + 2 files)
6. **Verify**: Files upload faster than before

### Test 2: Database Batch Updates (OPT-3)
1. Upload multiple files
2. Monitor backend logs:
   ```bash
   docker compose logs -f backend | grep -i "update.*status"
   ```
3. **Expected**: Fewer individual update calls, more efficient batching
4. **Verify**: Files process without errors

### Test 3: Embedding Batch Size (OPT-4)
1. Upload a document with many chunks (>100)
2. Monitor Celery worker logs:
   ```bash
   docker compose logs -f celery-worker | grep -i "batch\|embedding"
   ```
3. **Expected**: See "Processing batch X/Y (100 chunks)" instead of 50
4. **Verify**: Embedding completes faster

### Test 4: Overall Performance
1. Upload 20 files simultaneously
2. Monitor resource usage:
   ```bash
   docker stats
   ```
3. **Expected**: 
   - Faster upload completion
   - Better CPU utilization
   - Lower database load
4. **Verify**: All files process successfully

---

## Verification Commands

### Check Celery Configuration
```bash
docker compose exec celery-worker celery -A anylab inspect stats | grep -A 5 "pool"
```

### Monitor Batch Uploads
```bash
docker compose logs -f backend | grep -i "batch upload"
```

### Monitor Database Updates
```bash
docker compose logs -f celery-worker | grep -i "Bulk updated\|update.*status"
```

### Check Embedding Batch Size
```bash
docker compose logs -f celery-worker | grep -i "batch.*100\|BATCH_SIZE"
```

### Monitor Resources
```bash
docker stats --no-stream | grep -E "celery|backend|ollama"
```

---

## Expected Performance Improvements

| Optimization | Expected Improvement | Status |
|--------------|---------------------|--------|
| OPT-1: Celery Workers | 2-3x faster processing | ✅ Verified |
| OPT-2: Batch Uploads | 2-3x faster uploads | ⏳ Ready to test |
| OPT-3: Batch DB Updates | 3-4x faster updates | ⏳ Ready to test |
| OPT-4: Embedding Batch | 2x faster embedding | ⏳ Ready to test |
| **Overall** | **4-6x faster** | ⏳ Ready to test |

---

## Success Criteria

✅ **OPT-1**: Workers using prefork pool with correct concurrency (VERIFIED)
⏳ **OPT-2**: Batch upload endpoint accepts multiple files (READY)
⏳ **OPT-3**: Fewer database update calls (READY)
⏳ **OPT-4**: Embedding uses batch size 100 (READY)

---

## Next Steps

1. Test with actual file uploads via frontend
2. Monitor logs for optimization indicators
3. Measure performance improvements
4. Adjust batch sizes if needed based on results

