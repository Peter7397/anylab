# Hybrid Configuration Investigation Report
**Date:** 2025-11-03  
**Purpose:** Identify configuration inconsistencies causing confusion between Docker and local services

---

## 🎯 Executive Summary

This investigation reveals **critical configuration inconsistencies** that cause repeated confusion about which services run in Docker vs locally. The hybrid setup (Docker services + local Django/Frontend) has **mismatched default values** and **conflicting configuration sources** that lead to connection failures.

---

## 📊 Current State Analysis

### Services Running Status

**Docker Containers (Active):**
```
✅ onlab_postgres  (PostgreSQL with pgvector)
   - Port: 5433:5432
   - DB Name: anylab
   - Container: onlab_postgres
   
✅ onlab_redis     (Redis)
   - Port: 6379:6379
   - Container: onlab_redis
```

**Local Services:**
```
✅ Django Backend  (2 processes - DUPLICATE!)
   - Port: 8000
   - PIDs: 8377, 2656
   
✅ React Frontend
   - Port: 3000
   - Process: Running
   
❌ Celery Worker
   - Status: Not running
```

---

## 🚨 Critical Configuration Issues

### 1. Database Configuration Conflicts

**Issue:** Multiple conflicting default values for database connection

#### `backend/anylab/settings.py` (Line 104-105):
```python
'HOST': os.getenv('DB_HOST', 'db'),      # ❌ WRONG: 'db' is Docker service name
'PORT': os.getenv('DB_PORT', '5432'),    # ❌ WRONG: Should be '5433' for Docker port mapping
```

**Problems:**
- Default `'db'` only works inside Docker network
- Default `'5432'` doesn't match Docker port mapping (`5433`)
- In hybrid setup (local Django + Docker PostgreSQL), this fails

#### `start-hybrid.sh` (Line 29):
```bash
docker run ... -e POSTGRES_DB=onlab ...  # ❌ WRONG: Uses 'onlab'
```

**Problem:**
- Uses DB name `onlab` instead of `anylab` (from docker-compose.yml)
- Creates inconsistency if using docker-compose vs start-hybrid.sh

#### `backend/start-celery-worker.sh` (Line 14-15):
```bash
export DB_PORT=${DB_PORT:-5433}    # ✅ CORRECT for hybrid
export DB_HOST=${DB_HOST:-127.0.0.1}  # ✅ CORRECT for hybrid
```

**Status:** This script has correct defaults, but settings.py overrides them!

#### `docker-compose.yml`:
```yaml
POSTGRES_DB: anylab              # ✅ Consistent
ports: "5433:5432"               # ✅ Port mapping
container_name: onlab_postgres   # ✅ Container name
```

---

### 2. Redis Configuration Conflicts

**Issue:** Mixed Docker service names vs localhost references

#### `backend/anylab/settings.py` (Lines 233-245):
```python
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')      # ❌ WRONG: 'redis' is Docker service name
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')  # ❌ WRONG
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')                      # ❌ WRONG
```

**Problems:**
- Default `'redis'` only works inside Docker network
- In hybrid setup (local Django/Celery + Docker Redis), this fails
- Must use `'localhost'` or `'127.0.0.1'`

#### `backend/start-celery-worker.sh` (Lines 10-11):
```bash
export CELERY_BROKER_URL=${CELERY_BROKER_URL:-redis://localhost:6379/0}     # ✅ CORRECT
export CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND:-redis://localhost:6379/0}  # ✅ CORRECT
```

**Status:** This script has correct defaults, but settings.py overrides them!

---

### 3. Duplicate Process Issue

**Issue:** Two Django runserver processes running simultaneously

```
Process 1: PID 8377 (active since 10:07AM)
Process 2: PID 2656 (active since 5:57PM)
```

**Problems:**
- Causes port conflicts
- Resource waste
- Confusion about which process is active
- Potential race conditions

**Root Cause:** Likely multiple manual starts or script restarts without proper cleanup.

---

### 4. Configuration Source Confusion

**Issue:** Multiple configuration files with different purposes

#### Files Involved:
1. **`backend/anylab/settings.py`**
   - Primary Django settings
   - Defaults assume **FULL Docker** deployment (`db`, `redis`)
   - ❌ **NOT compatible with hybrid setup**

2. **`backend/anylab/cross_platform.py`**
   - Cross-platform helpers
   - Defaults use `localhost` ✅
   - ⚠️ **NOT USED** by settings.py - dead code?

3. **`backend/start-celery-worker.sh`**
   - Celery startup script
   - Defaults use `localhost:6379` and `127.0.0.1:5433` ✅
   - ✅ **Correct for hybrid**, but conflicts with settings.py defaults

4. **`start-hybrid.sh`**
   - Main startup script
   - Uses hardcoded Docker commands
   - ⚠️ Uses different DB name (`onlab` vs `anylab`)

5. **`.env` file** (in backend/)
   - Environment variables
   - ⚠️ Can't be read (filtered by .cursorignore)
   - Should override settings.py defaults

6. **`docker-compose.yml`**
   - Docker service definitions
   - ✅ Correct for Docker deployment
   - ⚠️ Not used by hybrid setup

---

## 🔍 Root Cause Analysis

### Why This Keeps Happening:

1. **Ambiguous Defaults:**
   - `settings.py` assumes full Docker deployment
   - Hybrid setup requires localhost references
   - No clear "hybrid mode" detection

2. **Missing Environment Detection:**
   - No automatic detection of Docker vs local services
   - No fallback logic when service names fail
   - Manual environment variable setting required

3. **Inconsistent Documentation:**
   - No clear guide on what runs where
   - Multiple scripts with different assumptions
   - No single source of truth

4. **Dead Code:**
   - `cross_platform.py` has correct defaults but isn't used
   - Alternative config files that are ignored

---

## 📋 Detailed Configuration Matrix

### Current Configuration State

| Service | Location | Port | Connection String | Default in settings.py | Actual Required |
|---------|----------|------|-------------------|------------------------|-----------------|
| PostgreSQL | Docker | 5433 | `127.0.0.1:5433` | `db:5432` ❌ | `127.0.0.1:5433` ✅ |
| Redis | Docker | 6379 | `localhost:6379` | `redis:6379` ❌ | `localhost:6379` ✅ |
| Neo4j | Docker (optional) | 7687 | `localhost:7687` | `localhost:7687` ✅ | `localhost:7687` ✅ |
| Django | Local | 8000 | N/A | N/A | N/A |
| React | Local | 3000 | N/A | N/A | N/A |
| Celery | Local | N/A | N/A | `redis:6379` ❌ | `localhost:6379` ✅ |

---

## 🔧 Identified Duplications

### 1. Duplicate Django Processes
- **Location:** 2 `manage.py runserver` processes
- **Action Needed:** Kill duplicate, implement process check before start

### 2. Duplicate Configuration Logic
- **`settings.py`** vs **`cross_platform.py`**
  - Both define database/Redis configs
  - Only `settings.py` is used
  - `cross_platform.py` is dead code

### 3. Duplicate Startup Mechanisms
- **`start-hybrid.sh`** uses direct `docker run` commands
- **`docker-compose.yml`** defines same services
- Both create containers with different names/configs

### 4. Conflicting DB Names
- `docker-compose.yml`: `anylab`
- `start-hybrid.sh`: `onlab`
- Settings default: `anylab`
- **Inconsistency creates confusion**

---

## 📝 Recommendations

### Priority 1: Fix Configuration Defaults (CRITICAL)

1. **Update `settings.py` defaults for hybrid setup:**
   ```python
   # Change from Docker service names to localhost
   'HOST': os.getenv('DB_HOST', '127.0.0.1'),      # Was: 'db'
   'PORT': os.getenv('DB_PORT', '5433'),          # Was: '5432'
   CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')  # Was: 'redis://redis:6379/0'
   REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')                  # Was: 'redis://redis:6379/0'
   ```

2. **Add environment detection:**
   ```python
   # Detect if running in Docker or hybrid mode
   import socket
   def is_docker_network():
       try:
           socket.gethostbyname('db')  # Try Docker service name
           return True
       except:
           return False
   
   DB_HOST = 'db' if is_docker_network() else '127.0.0.1'
   ```

### Priority 2: Standardize Configuration (HIGH)

1. **Remove duplicate config files:**
   - Delete or document `cross_platform.py` usage
   - Consolidate to single source of truth

2. **Standardize DB name:**
   - Use `anylab` everywhere
   - Update `start-hybrid.sh` to match `docker-compose.yml`

3. **Create `.env.example`:**
   - Document required environment variables
   - Show examples for Docker vs hybrid

### Priority 3: Clean Up Duplicates (MEDIUM)

1. **Kill duplicate Django processes:**
   - Implement process check before start
   - Add cleanup on script exit

2. **Unify startup scripts:**
   - Use `docker-compose` instead of direct `docker run`
   - Single source of truth for service creation

3. **Add health checks:**
   - Verify services before starting dependent services
   - Clear error messages on connection failures

---

## 🎯 Proposed Solution Structure

### Option A: Hardcode Hybrid Configuration (RECOMMENDED)

**Approach:** Since this is a **hybrid setup, hardcode the hybrid values** as defaults.

**Pros:**
- ✅ No ambiguity
- ✅ Works out of the box
- ✅ Clear what runs where
- ✅ Easy to override via .env if needed

**Cons:**
- ⚠️ Less flexible for pure Docker deployment
- ⚠️ Requires .env for different setups

**Implementation:**
- Update `settings.py` defaults to `localhost`/`127.0.0.1`
- Document in comments that these are hybrid defaults
- Provide `.env.example` for Docker deployment

### Option B: Auto-Detection (COMPLEX)

**Approach:** Automatically detect environment and choose defaults.

**Pros:**
- ✅ Works in both Docker and hybrid
- ✅ Automatic adaptation

**Cons:**
- ❌ Complex implementation
- ❌ Can fail silently
- ❌ Harder to debug

### Option C: Explicit Environment Variable (SAFEST)

**Approach:** Require explicit `DEPLOYMENT_MODE` environment variable.

**Pros:**
- ✅ No ambiguity
- ✅ Explicit configuration
- ✅ Prevents misconfiguration

**Cons:**
- ⚠️ Requires manual setup
- ⚠️ Extra step for developers

---

## 📊 Impact Assessment

### Current Issues Impact:
- 🔴 **High:** Celery worker connection failures
- 🔴 **High:** Django database connection confusion
- 🟡 **Medium:** Duplicate processes wasting resources
- 🟡 **Medium:** Developer confusion and repeated fixes
- 🟢 **Low:** Dead code (`cross_platform.py`)

### Fix Priority:
1. **IMMEDIATE:** Fix settings.py defaults (30 min)
2. **URGENT:** Kill duplicate Django processes (5 min)
3. **HIGH:** Standardize DB name in start-hybrid.sh (10 min)
4. **MEDIUM:** Add health checks and error messages (1 hour)
5. **LOW:** Clean up dead code (30 min)

---

## 🔍 Files Requiring Changes

### Critical (Must Fix):
1. `backend/anylab/settings.py`
   - Lines 104-105: DB_HOST, DB_PORT defaults
   - Lines 233-234: CELERY_BROKER_URL, CELERY_RESULT_BACKEND defaults
   - Line 245: REDIS_URL default

### High Priority:
2. `start-hybrid.sh`
   - Line 29: DB name consistency
   - Add process cleanup

3. `.env` or `.env.example`
   - Document required variables
   - Provide examples

### Medium Priority:
4. `backend/anylab/cross_platform.py`
   - Remove or document usage
   - Determine if needed

5. Process management
   - Add PID file checks
   - Prevent duplicate starts

---

## 📝 Next Steps

1. ✅ **Investigation Complete** (This document)
2. ⏳ **Get User Approval** for proposed fixes
3. ⏳ **Implement Priority 1 fixes**
4. ⏳ **Clean up duplicates**
5. ⏳ **Test hybrid setup**
6. ⏳ **Document configuration**

---

## 📌 Summary

The hybrid configuration has **fundamental inconsistencies** between:
- Docker service names (`db`, `redis`) vs localhost (`127.0.0.1`, `localhost`)
- Default ports (`5432` vs `5433`)
- Database names (`anylab` vs `onlab`)
- Multiple configuration sources with conflicting defaults

**Root Cause:** `settings.py` defaults assume full Docker deployment, but the project uses a hybrid setup (Docker services + local Django/Frontend).

**Solution:** Update `settings.py` defaults to match hybrid setup (localhost/127.0.0.1), with option to override via environment variables for pure Docker deployment.

