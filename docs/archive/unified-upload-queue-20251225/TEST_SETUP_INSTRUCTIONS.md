# Test Setup Instructions

## Current Status

✅ **Code is ready** - All Phases 1-4 implementation complete
✅ **Test scripts created** - Automated test suite ready
❌ **Docker not running** - PostgreSQL container needs to be started
❌ **Migration pending** - Database table needs to be created

## Steps to Run Tests

### Step 1: Start Docker Desktop

1. Open Docker Desktop application on your Mac
2. Wait for Docker to fully start (whale icon in menu bar should be steady)
3. Verify Docker is running:
   ```bash
   docker ps
   ```

### Step 2: Start PostgreSQL Container

Once Docker is running, start the PostgreSQL container:

```bash
cd /Volumes/Orico/Anylab103
docker-compose up -d postgres
```

Or if using newer Docker Compose:
```bash
docker compose up -d postgres
```

Verify PostgreSQL is running:
```bash
docker ps | grep postgres
```

You should see `anylab_postgres` container running.

### Step 3: Verify Database Connection

Test the connection:
```bash
cd /Volumes/Orico/Anylab103/backend
source venv/bin/activate
python manage.py dbshell
```

If connection works, type `\q` to exit.

### Step 4: Create Database Migration

Create the migration for UploadJob model:
```bash
cd /Volumes/Orico/Anylab103/backend
source venv/bin/activate
python manage.py makemigrations ai_assistant --name add_upload_job
```

### Step 5: Run Migration

Apply the migration to create the table:
```bash
python manage.py migrate
```

### Step 6: Run Tests

Now run the automated test suite:
```bash
python test_upload_queue_phases_1_4.py
```

## Expected Results

Once Docker and migrations are set up, you should see:

```
============================================================
Upload Queue System - Comprehensive Test Suite
Phases 1-4: Core, Multi-file, Pause/Resume, Workload Balancing
============================================================

============================================================
PHASE 1: Model Creation Tests
============================================================
✓ PASSED: Create UploadJob with all fields
✓ PASSED: Model methods (get_progress_percentage, is_active)
✓ PASSED: Status field updates

... (more tests)

Total: 11/11 test suites passed

🎉 All test suites passed! The upload queue system is working correctly.
```

## Troubleshooting

### Docker won't start
- Check Docker Desktop is installed
- Restart Docker Desktop
- Check system resources (Docker needs memory)

### PostgreSQL connection refused
- Verify container is running: `docker ps | grep postgres`
- Check port 5433 is not in use: `lsof -i :5433`
- Check container logs: `docker logs anylab_postgres`

### Migration errors
- Ensure database is accessible
- Check Django settings for correct database config
- Verify all dependencies installed: `pip install -r requirements.txt`

### Test failures
- Check database connection
- Verify migration was applied: `python manage.py showmigrations ai_assistant`
- Check test output for specific error messages

## Quick Start Script

Once Docker is running, you can use this one-liner:

```bash
cd /Volumes/Orico/Anylab103 && \
docker-compose up -d postgres && \
sleep 5 && \
cd backend && \
source venv/bin/activate && \
python manage.py makemigrations ai_assistant --name add_upload_job && \
python manage.py migrate && \
python test_upload_queue_phases_1_4.py
```

## Next Steps After Tests Pass

1. ✅ Verify all tests pass
2. → Test API endpoints manually
3. → Test with actual file uploads
4. → Proceed to Phase 5 (Webpage download)

