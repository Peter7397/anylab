# Hybrid System Reliability Plan
**Date:** 2025-11-03  
**Goal:** Make hybrid system work reliably with hardcoded configuration and ensure Neo4j always runs

---

## 🎯 **Objectives**

1. ✅ **Hardcode hybrid configuration** (no more Docker service name defaults)
2. ✅ **Ensure Neo4j always runs** (auto-start, health checks)
3. ✅ **Remove duplicate processes** (single Django, single Celery worker)
4. ✅ **Prevent future duplicates** (process checks, PID management)
5. ✅ **Make system resilient** (auto-recovery, clear error messages)

---

## 📋 **Phase 1: Configuration Hardcoding (HIGH PRIORITY)**

### **1.1 Fix `backend/anylab/settings.py` Defaults**

**Current (Wrong):**
```python
'HOST': os.getenv('DB_HOST', 'db'),  # ❌ Docker service name
'PORT': os.getenv('DB_PORT', '5432'),  # ❌ Wrong port
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')  # ❌
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')  # ❌
```

**Fixed (Hardcoded for Hybrid):**
```python
# HARDCODED for Hybrid Setup (Docker services + Local Django/Frontend)
'HOST': os.getenv('DB_HOST', '127.0.0.1'),  # ✅ localhost for hybrid
'PORT': os.getenv('DB_PORT', '5433'),  # ✅ Docker port mapping
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')  # ✅
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')  # ✅
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')  # ✅ Already correct
```

**Why:**
- Works out of the box for hybrid setup
- No confusion about Docker vs localhost
- Still allows override via `.env` if needed
- Clear comments explain hybrid setup

**Files to Change:**
- `backend/anylab/settings.py` (lines 104-105, 233-234, 245, 288)

---

### **1.2 Fix `start-hybrid.sh` Database Name**

**Current:**
```bash
docker run ... -e POSTGRES_DB=onlab ...  # ❌ Wrong name
```

**Fixed:**
```bash
docker run ... -e POSTGRES_DB=anylab ...  # ✅ Matches docker-compose.yml
```

**Files to Change:**
- `start-hybrid.sh` (line 29)

---

### **1.3 Add Configuration Comments**

Add clear documentation in `settings.py`:

```python
"""
HYBRID SETUP CONFIGURATION
==========================
This project uses a HYBRID architecture:
- Docker: PostgreSQL (port 5433), Redis (port 6379), Neo4j (ports 7474, 7687)
- Local: Django Backend (port 8000), React Frontend (port 3000), Celery Worker

All service connections use localhost/127.0.0.1 to connect from local processes
to Docker containers via exposed ports.

To change to full Docker deployment:
- Set DB_HOST='db', REDIS_URL='redis://redis:6379/0' via .env
"""
```

**Files to Change:**
- `backend/anylab/settings.py` (add at top of database/redis sections)

---

## 📋 **Phase 2: Neo4j Always Running (CRITICAL)**

### **2.1 Update docker-compose.yml**

**Current:** Neo4j configured but not auto-starting

**Fixed:** Ensure Neo4j starts with other services

**Add to docker-compose.yml:**
```yaml
services:
  postgres:
    # ... existing config
    depends_on:
      - redis
  
  redis:
    # ... existing config
  
  neo4j:
    # ... existing config
    restart: unless-stopped  # ✅ Already set
    depends_on:
      - postgres  # Optional: Start after postgres is ready
    # Ensure health check passes
    healthcheck:
      test: ["CMD-SHELL", "wget --quiet --tries=1 --spider http://localhost:7474 || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 40s
```

**No changes needed** - already configured correctly! Just need to ensure it starts.

**Files to Change:**
- `docker-compose.yml` (verify configuration, no changes if correct)

---

### **2.2 Create Startup Script for All Docker Services**

**Create:** `start-docker-services.sh`

```bash
#!/bin/bash
# Start all required Docker services for hybrid setup

echo "🐳 Starting Docker services (PostgreSQL, Redis, Neo4j)..."

cd "$(dirname "$0")"

# Start all services defined in docker-compose.yml
docker-compose up -d postgres redis neo4j

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check PostgreSQL
if docker exec onlab_postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo "✅ PostgreSQL is ready"
else
    echo "⚠️  PostgreSQL is starting (may need more time)"
fi

# Check Redis
if docker exec onlab_redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is ready"
else
    echo "⚠️  Redis is starting (may need more time)"
fi

# Check Neo4j (wait longer as it takes more time to start)
echo "⏳ Waiting for Neo4j (this takes 30-60 seconds)..."
for i in {1..12}; do
    if curl -s http://localhost:7474 > /dev/null 2>&1; then
        echo "✅ Neo4j is ready"
        break
    fi
    echo "   Attempt $i/12..."
    sleep 5
done

echo ""
echo "📊 Docker services status:"
docker-compose ps

echo ""
echo "✅ All Docker services started!"
```

**Files to Create:**
- `start-docker-services.sh` (new file)

---

### **2.3 Update start-hybrid.sh to Use docker-compose**

**Current:** Uses direct `docker run` commands

**Fixed:** Use `docker-compose` for consistency

```bash
# Replace direct docker run with docker-compose
if ! docker ps | grep -q "onlab_postgres"; then
    echo "🐘 Starting PostgreSQL..."
    docker-compose up -d postgres redis neo4j  # Start all at once
    sleep 5
    # Enable pgvector extension
    docker exec onlab_postgres psql -U postgres -d anylab -c "CREATE EXTENSION IF NOT EXISTS vector;" || true
fi
```

**Files to Change:**
- `start-hybrid.sh` (lines 27-38)

---

### **2.4 Add Neo4j Health Check to Django Startup**

**Create:** `backend/anylab/startup_checks.py`

```python
"""
Startup checks for required services
"""
import logging
import time
from django.conf import settings

logger = logging.getLogger(__name__)

def check_neo4j_connection(max_retries=12, delay=5):
    """Check if Neo4j is accessible"""
    try:
        from ai_assistant.services.neo4j_service import get_neo4j_service
        neo4j = get_neo4j_service()
        
        for i in range(max_retries):
            if neo4j.test_connection():
                logger.info("✅ Neo4j connection successful")
                stats = neo4j.get_graph_stats()
                logger.info(f"📊 Graph: {stats.get('nodes', 0)} nodes, {stats.get('relationships', 0)} relationships")
                return True
            
            logger.warning(f"⏳ Neo4j not ready yet (attempt {i+1}/{max_retries})...")
            time.sleep(delay)
        
        logger.error("❌ Neo4j connection failed after retries")
        return False
    except Exception as e:
        logger.error(f"❌ Neo4j check failed: {e}")
        return False
```

**Add to:** `backend/anylab/__init__.py` or `backend/anylab/wsgi.py`

**Files to Create:**
- `backend/anylab/startup_checks.py` (new file)

**Files to Change:**
- `backend/anylab/wsgi.py` or `backend/anylab/__init__.py` (add startup check call)

---

## 📋 **Phase 3: Remove Duplicates & Process Management**

### **3.1 Kill Duplicate Processes (Manual Step - After Confirmation)**

**Create:** `cleanup-duplicates.sh`

```bash
#!/bin/bash
# Cleanup duplicate processes

echo "🧹 Cleaning up duplicate processes..."

# Kill duplicate Django processes (keep PID 8377, kill PID 2656)
DUPLICATE_DJANGO=$(ps aux | grep "manage.py runserver" | grep -v grep | awk '{print $2}' | tail -n +2)
if [ ! -z "$DUPLICATE_DJANGO" ]; then
    echo "⚠️  Found duplicate Django processes. Killing duplicates..."
    echo "$DUPLICATE_DJANGO" | xargs kill 2>/dev/null || true
    echo "✅ Duplicate Django processes killed"
else
    echo "✅ No duplicate Django processes found"
fi

# Kill all Celery workers (will restart with single instance)
echo "🧹 Cleaning up Celery workers..."
pkill -f "celery.*worker.*anylab" 2>/dev/null || true
sleep 2
echo "✅ Celery workers stopped"

# Remove old Docker containers
echo "🧹 Removing old Docker containers..."
docker rm -f anylab_db anylab_redis 2>/dev/null || true
echo "✅ Old containers removed"

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📊 Current processes:"
ps aux | grep -E "(manage.py runserver|celery.*worker)" | grep -v grep | wc -l | xargs echo "Active processes:"
```

**Files to Create:**
- `cleanup-duplicates.sh` (new file)

---

### **3.2 Add Process Checks to Startup Scripts**

**Update:** `start-hybrid.sh`

Add process checks before starting:

```bash
# Check if Django is already running
if pgrep -f "manage.py runserver" > /dev/null; then
    echo "⚠️  Django is already running"
    read -p "Kill existing Django process? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pkill -f "manage.py runserver"
        sleep 2
    else
        echo "❌ Cannot start: Django already running"
        exit 1
    fi
fi

# Check if Celery is already running
if pgrep -f "celery.*worker.*anylab" > /dev/null; then
    echo "⚠️  Celery worker is already running"
    read -p "Kill existing Celery worker? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pkill -f "celery.*worker.*anylab"
        sleep 2
    fi
fi
```

**Files to Change:**
- `start-hybrid.sh` (add process checks at start)

---

### **3.3 Add PID File Management**

**Update:** `start-hybrid.sh`

```bash
# Store PIDs for cleanup
BACKEND_DIR="backend"
FRONTEND_DIR="frontend"

# Create PID files
echo $$ > "$BACKEND_DIR/.backend.pid"
echo $$ > "$FRONTEND_DIR/.frontend.pid"

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    
    # Kill by PID if file exists
    if [ -f "$BACKEND_DIR/.backend.pid" ]; then
        BACKEND_PID=$(cat "$BACKEND_DIR/.backend.pid")
        kill $BACKEND_PID 2>/dev/null || true
        rm "$BACKEND_DIR/.backend.pid"
    fi
    
    if [ -f "$FRONTEND_DIR/.frontend.pid" ]; then
        FRONTEND_PID=$(cat "$FRONTEND_DIR/.frontend.pid")
        kill $FRONTEND_PID 2>/dev/null || true
        rm "$FRONTEND_DIR/.frontend.pid"
    fi
    
    # Also kill by process name (safety)
    pkill -f "manage.py runserver" 2>/dev/null || true
    pkill -f "react-scripts start" 2>/dev/null || true
    
    echo "✅ Services stopped"
}
trap cleanup EXIT INT TERM
```

**Files to Change:**
- `start-hybrid.sh` (improve PID management)

---

### **3.4 Fix Celery Worker Startup**

**Update:** `backend/start-celery-worker.sh`

Add check for existing workers:

```bash
#!/usr/bin/env bash
set -euo pipefail

# Check if Celery worker is already running
if pgrep -f "celery.*worker.*anylab" > /dev/null; then
    echo "⚠️  Celery worker is already running!"
    echo "   PIDs: $(pgrep -f 'celery.*worker.*anylab' | tr '\n' ' ')"
    read -p "Kill existing workers and restart? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pkill -f "celery.*worker.*anylab"
        sleep 2
        echo "✅ Old workers stopped"
    else
        echo "❌ Exiting - worker already running"
        exit 1
    fi
fi

# Load environment if present
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs -0 bash -c 'printf "%s\n" "$@"' -- 2>/dev/null || true)
fi

# Hardcoded for hybrid setup (Docker services on localhost)
export CELERY_BROKER_URL=${CELERY_BROKER_URL:-redis://localhost:6379/0}
export CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND:-redis://localhost:6379/0}
export DB_PORT=${DB_PORT:-5433}
export DB_HOST=${DB_HOST:-127.0.0.1}

export ENABLE_ASYNC_FILE_PROCESSING=${ENABLE_ASYNC_FILE_PROCESSING:-true}

# Start single worker instance
exec ./venv/bin/celery -A anylab worker -l info -Q ai_queue,default --concurrency=4
```

**Files to Change:**
- `backend/start-celery-worker.sh` (add process check, ensure single instance)

---

## 📋 **Phase 4: System Reliability Improvements**

### **4.1 Create Master Startup Script**

**Create:** `start-all.sh`

```bash
#!/bin/bash
# Master startup script for hybrid system

echo "🚀 Starting OnLab Hybrid System..."
echo "=================================="
echo ""

# Step 1: Start Docker services
echo "📦 Step 1: Starting Docker services..."
./start-docker-services.sh

# Step 2: Wait for services to be ready
echo ""
echo "⏳ Step 2: Waiting for all services to be ready..."
sleep 10

# Step 3: Start backend
echo ""
echo "🔧 Step 3: Starting Django backend..."
cd backend
source venv/bin/activate
python manage.py migrate --noinput
python manage.py runserver 0.0.0.0:8000 &
BACKEND_PID=$!
cd ..
echo "   Backend PID: $BACKEND_PID"

# Step 4: Start Celery worker
echo ""
echo "⚙️  Step 4: Starting Celery worker..."
cd backend
source venv/bin/activate
DB_PORT=5433 ./start-celery-worker.sh &
CELERY_PID=$!
cd ..
echo "   Celery PID: $CELERY_PID"

# Step 5: Start frontend
echo ""
echo "🎨 Step 5: Starting React frontend..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..
echo "   Frontend PID: $FRONTEND_PID"

echo ""
echo "✅ All services started!"
echo ""
echo "📍 Access:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo "   Neo4j:    http://localhost:7474"
echo ""
echo "🛑 To stop: ./stop-all.sh"
```

**Files to Create:**
- `start-all.sh` (new file)

---

### **4.2 Create Stop Script**

**Create:** `stop-all.sh`

```bash
#!/bin/bash
# Stop all hybrid system services

echo "🛑 Stopping OnLab Hybrid System..."

# Stop frontend
pkill -f "react-scripts start" 2>/dev/null || true

# Stop backend
pkill -f "manage.py runserver" 2>/dev/null || true

# Stop Celery
pkill -f "celery.*worker.*anylab" 2>/dev/null || true

# Docker services stay running (persistent)
echo "ℹ️  Docker services (PostgreSQL, Redis, Neo4j) remain running"
echo "   To stop: docker-compose down"

echo "✅ All local services stopped"
```

**Files to Create:**
- `stop-all.sh` (new file)

---

### **4.3 Add Health Check Endpoint**

**Update:** Create or enhance health check in Django

**File:** `backend/ai_assistant/views/system_settings_views.py`

Add comprehensive health check:

```python
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def health_check(request):
    """Comprehensive health check for all services"""
    health = {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'services': {}
    }
    
    # Check PostgreSQL
    try:
        from django.db import connection
        connection.ensure_connection()
        health['services']['postgresql'] = {'status': 'healthy'}
    except Exception as e:
        health['status'] = 'degraded'
        health['services']['postgresql'] = {'status': 'unhealthy', 'error': str(e)}
    
    # Check Redis
    try:
        from django.core.cache import cache
        cache.set('health_check', 'ok', 10)
        health['services']['redis'] = {'status': 'healthy'}
    except Exception as e:
        health['status'] = 'degraded'
        health['services']['redis'] = {'status': 'unhealthy', 'error': str(e)}
    
    # Check Neo4j
    try:
        from ai_assistant.services.neo4j_service import get_neo4j_service
        neo4j = get_neo4j_service()
        if neo4j.test_connection():
            stats = neo4j.get_graph_stats()
            health['services']['neo4j'] = {
                'status': 'healthy',
                'nodes': stats.get('nodes', 0),
                'relationships': stats.get('relationships', 0)
            }
        else:
            health['status'] = 'degraded'
            health['services']['neo4j'] = {'status': 'unhealthy'}
    except Exception as e:
        health['status'] = 'degraded'
        health['services']['neo4j'] = {'status': 'unhealthy', 'error': str(e)}
    
    status_code = 200 if health['status'] == 'healthy' else 503
    return Response(health, status=status_code)
```

**Files to Change:**
- `backend/ai_assistant/views/system_settings_views.py` (add or enhance health check)

---

## 📋 **Implementation Order**

### **Step 1: Configuration Hardcoding (Do First)**
1. Fix `settings.py` defaults
2. Fix `start-hybrid.sh` DB name
3. Add configuration comments

### **Step 2: Neo4j Always Running**
1. Create `start-docker-services.sh`
2. Update `start-hybrid.sh` to use docker-compose
3. Add Neo4j health check to Django startup

### **Step 3: Process Management**
1. Create `cleanup-duplicates.sh`
2. Add process checks to startup scripts
3. Fix Celery worker startup

### **Step 4: System Reliability**
1. Create `start-all.sh` master script
2. Create `stop-all.sh` stop script
3. Add health check endpoint

### **Step 5: Cleanup (After Confirmation)**
1. Run `cleanup-duplicates.sh`
2. Remove old Docker containers
3. Verify everything works

---

## ✅ **Verification Checklist**

After implementation, verify:

- [ ] PostgreSQL accessible on port 5433
- [ ] Redis accessible on port 6379
- [ ] Neo4j accessible on ports 7474 and 7687
- [ ] Django connects to all services without errors
- [ ] Celery connects to Redis
- [ ] Only 1 Django process running
- [ ] Only 1 Celery worker (with child processes)
- [ ] No duplicate processes
- [ ] GraphRAG functionality works
- [ ] All services start automatically
- [ ] Health check endpoint reports all services healthy

---

## 📝 **Files Summary**

### **Files to Create:**
1. `start-docker-services.sh` - Start all Docker services
2. `cleanup-duplicates.sh` - Clean up duplicate processes
3. `start-all.sh` - Master startup script
4. `stop-all.sh` - Stop all services
5. `backend/anylab/startup_checks.py` - Startup health checks

### **Files to Modify:**
1. `backend/anylab/settings.py` - Hardcode hybrid defaults
2. `start-hybrid.sh` - Use docker-compose, add process checks
3. `backend/start-celery-worker.sh` - Add process check, ensure single instance
4. `backend/ai_assistant/views/system_settings_views.py` - Add health check endpoint

### **Files to Verify:**
1. `docker-compose.yml` - Neo4j configuration (should be correct)

---

## 🎯 **Expected Outcome**

After implementation:

✅ **Configuration:**
- Hardcoded localhost defaults (no confusion)
- Clear comments explaining hybrid setup
- Works out of the box

✅ **Neo4j:**
- Always starts with Docker services
- Health checks verify it's running
- Automatic recovery if it stops

✅ **Processes:**
- Single Django instance
- Single Celery worker instance
- No duplicates
- Process checks prevent future duplicates

✅ **Reliability:**
- Master startup script
- Health check endpoint
- Clear error messages
- Automatic service verification

---

## ⚠️ **Important Notes**

1. **Backup `.env` file** before making changes (though we're hardcoding defaults, .env still works for overrides)

2. **Test each phase** before moving to next

3. **Cleanup duplicates** only after confirming new configuration works

4. **Document any manual steps** required after implementation

---

**Ready to implement when you approve!** 🚀



