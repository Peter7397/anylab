# Testing Guide - Upload Queue System Phases 1-4

## Prerequisites

1. **Database Migration**: Create and run migration first
   ```bash
   cd /Volumes/Orico/Anylab103/backend
   python manage.py makemigrations ai_assistant --name add_upload_job
   python manage.py migrate
   ```

2. **Dependencies**: Ensure all packages are installed
   ```bash
   pip install -r requirements.txt
   ```

3. **Services Running**:
   - Django server: `python manage.py runserver`
   - Celery worker: `celery -A anylab worker -l info`
   - Celery beat (optional): `celery -A anylab beat -l info`

---

## Test Suite 1: Automated Python Tests

### Run Comprehensive Test Suite

```bash
cd /Volumes/Orico/Anylab103/backend
python test_upload_queue_phases_1_4.py
```

### What It Tests

**Phase 1: Core Queue System**
- ✅ UploadJob model creation
- ✅ Model methods (get_progress_percentage, is_active)
- ✅ Queue manager (add_job, get_job, get_queue_status)
- ✅ Progress tracking

**Phase 2: Multi-File Support**
- ✅ Multi-file job creation
- ✅ Progress tracking for multiple files
- ✅ Checkpoint system
- ✅ Folder integration

**Phase 3: Pause/Resume**
- ✅ Pause functionality
- ✅ Resume functionality
- ✅ Cancel functionality
- ✅ Checkpoint preservation

**Phase 4: Workload Balancing**
- ✅ Priority-based scheduling
- ✅ Concurrent job limits
- ✅ Resource monitoring
- ✅ Fair scheduling

**Additional**
- ✅ Error handling per file

---

## Test Suite 2: API Endpoint Tests

### Step 1: Get Authentication Token

```bash
# Login to get token
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'
```

Copy the `access` token from the response.

### Step 2: Update Test Script

Edit `test_api_endpoints.sh` and replace `YOUR_TOKEN_HERE` with your actual token.

### Step 3: Run API Tests

```bash
cd /Volumes/Orico/Anylab103/backend
./test_api_endpoints.sh
```

### Manual API Tests

#### 1. Create Upload Job
```bash
curl -X POST http://localhost:8000/api/ai/upload/queue/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "job_type": "file",
    "source": "test_upload",
    "files": [{"name": "test.pdf", "size": 1024}],
    "priority": 5
  }'
```

**Expected**: Returns job_id, status, total_items

#### 2. Get Queue Status
```bash
curl -X GET http://localhost:8000/api/ai/upload/queue/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: Returns stats and job list

#### 3. Get Job Detail
```bash
curl -X GET http://localhost:8000/api/ai/upload/queue/{job_id}/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: Returns detailed job information

#### 4. Pause Job
```bash
curl -X POST http://localhost:8000/api/ai/upload/queue/{job_id}/pause/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: Job status changes to 'paused'

#### 5. Resume Job
```bash
curl -X POST http://localhost:8000/api/ai/upload/queue/{job_id}/resume/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: Job status changes back to 'queued' or 'uploading'

#### 6. Get Queue Statistics
```bash
curl -X GET http://localhost:8000/api/ai/upload/queue/stats/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: Returns statistics including system resources

---

## Test Suite 3: Django Admin Tests

1. **Access Admin**: http://localhost:8000/admin/
2. **Navigate**: AI Assistant → Upload Jobs
3. **Test Actions**:
   - Create new job manually
   - View job details
   - Use "Pause selected jobs" action
   - Use "Resume selected jobs" action
   - Use "Retry selected jobs" action

---

## Test Suite 4: Integration Tests

### Test Multi-File Upload

```bash
# Create job with multiple files
curl -X POST http://localhost:8000/api/ai/upload/queue/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "job_type=file" \
  -F "source=batch_test" \
  -F "files=@file1.pdf" \
  -F "files=@file2.pdf" \
  -F "files=@file3.pdf" \
  -F "priority=5"
```

**Check**:
- Job created with total_items=3
- Progress updates as files process
- Checkpoint updates correctly

### Test Folder Scanning

```bash
curl -X POST http://localhost:8000/api/ai/process/scan-folder/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "folder_path": "/path/to/folder",
    "auto_upload": true,
    "priority": 5
  }'
```

**Check**:
- Folder scanned, files discovered
- UploadJob created automatically
- job_id returned
- Files process in queue

### Test Priority Scheduling

1. Create 3 jobs with priorities: 3, 5, 8
2. Check queue status
3. Verify high-priority (8) processes first
4. Verify FIFO for same priority

### Test Resource Monitoring

1. Monitor system resources via stats endpoint
2. If CPU/Memory high, verify low-priority jobs pause
3. When resources normalize, verify jobs resume

---

## Verification Checklist

### Phase 1 ✅
- [ ] UploadJob model can be created
- [ ] Queue manager methods work
- [ ] API endpoints respond correctly
- [ ] Jobs appear in Django admin

### Phase 2 ✅
- [ ] Multiple files create single job
- [ ] Progress updates correctly
- [ ] Checkpoint system works
- [ ] Folder scanning creates jobs

### Phase 3 ✅
- [ ] Jobs can be paused
- [ ] Jobs can be resumed
- [ ] Checkpoint preserved on resume
- [ ] Jobs can be cancelled

### Phase 4 ✅
- [ ] High-priority jobs process first
- [ ] Concurrent job limits enforced
- [ ] Resource monitoring works
- [ ] Fair scheduling distributes job types

---

## Troubleshooting

### Issue: Migration fails
**Solution**: Check Django version, ensure all dependencies installed

### Issue: API returns 401
**Solution**: Get fresh auth token, check token expiration

### Issue: Jobs not processing
**Solution**: 
- Check Celery worker is running
- Check Celery logs for errors
- Verify Redis/broker is accessible

### Issue: Resource monitoring not working
**Solution**: 
- Verify psutil is installed: `pip install psutil`
- Check system permissions for resource access

---

## Next Steps After Testing

Once all tests pass:
1. ✅ Phase 1-4 verified
2. → Proceed to Phase 5 (Webpage download integration)
3. → Frontend integration
4. → Production deployment

