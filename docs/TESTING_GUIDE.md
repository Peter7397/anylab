# Testing Guide - Workflow Improvements

**Quick reference for testing the implemented improvements.**

---

## Quick Test

### 1. Test Recent File
```bash
docker exec anylab_backend python manage.py test_improvements --check-recent
```

This will check the most recently uploaded file and verify:
- No duplicate chunks
- Chunk count matches
- Embedding count matches
- Processing status

### 2. Test Specific File
```bash
docker exec anylab_backend python manage.py test_improvements --file-id <FILE_ID>
```

### 3. Monitor New File Upload

**Step 1:** Upload a new file through the UI

**Step 2:** Get the file ID from the response or database

**Step 3:** Monitor processing:
```bash
# Watch logs in real-time
docker logs -f anylab_celery_worker | grep -E "Processing|Embedding|GraphRAG|bulk"

# Or use the test command
docker exec anylab_backend python manage.py test_improvements --file-id <ID>
```

---

## What to Look For

### ✅ Success Indicators

1. **No Duplicates**
   - Test output shows: `✓ No duplicate chunks`
   - Database: Each `chunk_index` appears only once

2. **Fast Database Writes**
   - Logs show: `Bulk inserted X chunks`
   - Creation time: < 1 second for 159 chunks

3. **Progress Updates**
   - Logs show: `Embedding progress: X/Y (Z%)`
   - Database: `embedding_count` updates every 50 chunks

4. **Cache Hits** (for repetitive content)
   - Logs show: `Embedding cache hits: X/Y chunks (Z%)`
   - Higher percentage = more time saved

5. **GraphRAG Async**
   - File becomes "ready" immediately after embeddings
   - Logs show: `Scheduling GraphRAG build for ... (async, non-blocking)`
   - Separate Celery task runs: `build_graph_for_file`

### ⚠️ Warning Signs

1. **Duplicates Detected**
   - If test shows duplicates on NEW file → bug still exists
   - If test shows duplicates on OLD file → expected (processed before fix)

2. **Slow Database Writes**
   - Creation time > 2 seconds → bulk insert might not be working
   - Check logs for "Bulk inserted" messages

3. **No Progress Updates**
   - `embedding_count` doesn't update during processing
   - Check if progress callback is being called

---

## Manual Verification

### Check for Duplicates
```python
from ai_assistant.models import UploadedFile, DocumentChunk
from collections import Counter

file = UploadedFile.objects.get(id=<FILE_ID>)
chunks = DocumentChunk.objects.filter(uploaded_file=file)
indices = [c.chunk_index for c in chunks]
duplicates = {idx: count for idx, count in Counter(indices).items() if count > 1}

if duplicates:
    print(f"❌ Found {len(duplicates)} duplicate chunk_indices")
else:
    print("✅ No duplicates - improvement working!")
```

### Monitor Processing Progress
```python
from ai_assistant.models import UploadedFile
import time

file = UploadedFile.objects.get(id=<FILE_ID>)

while file.processing_status != 'ready':
    file.refresh_from_db()
    print(f"Status: {file.processing_status}, Embeddings: {file.embedding_count}/{file.chunk_count}")
    time.sleep(2)
    
print("✅ File ready!")
```

### Check Cache Performance
```bash
# Look for cache hit messages
docker logs anylab_celery_worker | grep "cache hits"

# Example output:
# INFO Embedding cache hits: 45/159 chunks (28.3%)
```

---

## Expected Performance

### Small File (50-100 chunks)
- **Processing time:** 2-3 minutes
- **Database writes:** < 0.5 seconds
- **Cache hits:** 0% (first upload)

### Medium File (150-200 chunks)
- **Processing time:** 4-5 minutes
- **Database writes:** < 1 second
- **Cache hits:** 0-20% (depending on content)

### Large File (500+ chunks)
- **Processing time:** 10-15 minutes
- **Database writes:** 2-3 seconds
- **Cache hits:** 20-40% (if repetitive content)

### Re-upload Same File
- **Processing time:** 2-3 minutes (cache hits!)
- **Cache hits:** 80-100% (most chunks cached)

---

## Troubleshooting

### Issue: Duplicates Still Appearing
**Check:**
1. Is this a NEW file (uploaded after fixes)?
2. Check signal code: `signals.py` line 83 should use `instance.uploaded_file.id`
3. Check logs for "Skipping duplicate trigger" message

### Issue: Slow Database Writes
**Check:**
1. Logs should show "Bulk inserted" messages
2. Verify `bulk_create()` is being called
3. Check database connection/performance

### Issue: No Progress Updates
**Check:**
1. Verify `progress_callback` is being passed to `generate_embeddings()`
2. Check logs for "Embedding progress" messages
3. Verify `embedding_count` field is updating in database

### Issue: GraphRAG Not Building
**Check:**
1. Verify Celery worker is running
2. Check logs for `build_graph_for_file` task
3. Verify task is registered in `tasks/__init__.py`

---

## Performance Benchmarks

### Before Improvements
- File 321: 8m 39s, 318 chunks (duplicates), no progress updates

### After Improvements (Expected)
- New file: 4-5 minutes, correct chunk count, real-time progress

---

## Next Steps After Testing

1. **If all tests pass:** ✅ Ready for production
2. **If issues found:** Check troubleshooting section above
3. **Monitor production:** Use test command periodically to verify

---

**Ready to test! Upload a new file and run the test command.**

