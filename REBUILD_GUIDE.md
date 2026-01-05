# Complete System Rebuild Guide

This guide will help you rebuild the entire system from scratch for testing.

## Quick Rebuild (Automated)

```bash
# Run the automated rebuild script
./rebuild_system.sh
```

This script will:
1. ✅ Stop all services
2. ✅ Clean up (optional)
3. ✅ Start Docker services (PostgreSQL, Redis, Neo4j, Ollama)
4. ✅ Setup backend environment
5. ✅ Install/update dependencies
6. ✅ Run database migrations
7. ✅ Collect static files
8. ✅ Verify CLIP installation
9. ✅ Start backend services (Django, Celery)
10. ✅ Verify all services

## Manual Rebuild Steps

If you prefer to rebuild manually:

### Step 1: Stop All Services

```bash
# Stop Docker containers
docker compose down

# Stop backend processes
pkill -f "manage.py runserver"
pkill -f "gunicorn"
pkill -f "celery"
```

### Step 2: Clean Up (Optional)

```bash
# Remove Docker volumes (WARNING: Deletes all data)
docker compose down -v

# Or keep volumes and just rebuild containers
docker compose build --no-cache
```

### Step 3: Start Docker Services

```bash
# Start all Docker services
docker compose up -d

# Or start specific services
docker compose up -d postgres redis neo4j ollama

# Wait for services to be ready
sleep 15
```

### Step 4: Setup Backend

```bash
cd backend

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Verify CLIP is installed
python -c "import clip; print('CLIP OK')"
```

### Step 5: Run Migrations

```bash
# Wait for PostgreSQL
sleep 5

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput
```

### Step 6: Start Backend Services

```bash
# Start Celery worker (in background)
celery -A anylab worker --loglevel=info --logfile=logs/celery_worker.log &

# Start Celery beat (in background)
celery -A anylab beat --loglevel=info --logfile=logs/celery_beat.log &

# Start Django server
python manage.py runserver 0.0.0.0:8001
```

### Step 7: Start Frontend (Separate Terminal)

```bash
cd frontend
npm install  # If needed
npm start
```

## Verification

### Check Docker Services

```bash
docker compose ps
```

All services should show "Up" or "healthy".

### Check Backend Health

```bash
curl http://localhost:8001/api/health/
```

Should return: `{"status": "healthy"}`

### Check CLIP Installation

```bash
cd backend
source venv/bin/activate
python -c "from ai_assistant.utils.visual_embedding import get_visual_embedding_service; s = get_visual_embedding_service(); print('CLIP available:', s.clip_model is not None)"
```

### Run Complete Workflow Test

```bash
cd backend
source venv/bin/activate
python test_complete_workflow.py
```

Should show: **4/4 tests passed**

## Service URLs

After rebuild:
- **Backend API**: http://localhost:8001
- **Admin Panel**: http://localhost:8001/admin
- **Frontend**: http://localhost:3000
- **PostgreSQL**: localhost:5433
- **Redis**: localhost:6379
- **Neo4j**: http://localhost:7474
- **Ollama**: http://localhost:11434

## Troubleshooting

### Docker Services Not Starting

```bash
# Check Docker status
docker info

# Check service logs
docker compose logs postgres
docker compose logs redis
docker compose logs neo4j
```

### Backend Not Starting

```bash
# Check Django logs
tail -f backend/logs/django.log

# Check for port conflicts
lsof -i :8001

# Try different port
python manage.py runserver 0.0.0.0:8002
```

### Migration Errors

```bash
# Reset migrations (WARNING: Deletes data)
docker compose down -v
docker compose up -d postgres
cd backend
source venv/bin/activate
python manage.py migrate
```

### CLIP Not Working

```bash
cd backend
source venv/bin/activate
./install_clip.sh
```

## Quick Commands Reference

```bash
# Rebuild everything
./rebuild_system.sh

# Stop everything
docker compose down
pkill -f "manage.py runserver"
pkill -f "celery"

# Start everything
docker compose up -d
cd backend && source venv/bin/activate
python manage.py runserver 0.0.0.0:8001 &
celery -A anylab worker --loglevel=info &
celery -A anylab beat --loglevel=info &

# Check status
docker compose ps
curl http://localhost:8001/api/health/

# View logs
docker compose logs -f
tail -f backend/logs/django.log
```

## Post-Rebuild Testing

1. **Test Visual Embeddings**:
   ```bash
   cd backend
   source venv/bin/activate
   python test_complete_workflow.py
   ```

2. **Test RAG Search**:
   - Open frontend: http://localhost:3000
   - Navigate to AI Assistant
   - Try a search query

3. **Test Image Upload**:
   - Upload an image through the UI
   - Check logs for "CLIP library available"
   - Verify visual embedding is generated

4. **Check Database**:
   ```bash
   docker compose exec postgres psql -U postgres anylab -c "SELECT COUNT(*) FROM ai_assistant_documentchunk WHERE visual_embedding IS NOT NULL;"
   ```

---

**Status**: Ready for testing! 🚀

