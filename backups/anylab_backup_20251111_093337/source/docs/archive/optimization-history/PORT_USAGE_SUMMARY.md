# AnyLab Project - Complete Port Usage Summary

This document provides a comprehensive overview of all ports used by the AnyLab project to help you identify and avoid conflicts with other projects.

## 🎯 Quick Summary

| Service | Port | Type | Conflict Risk | Notes |
|---------|------|------|---------------|-------|
| **React Frontend** | **3000** | Application | ⚠️ **HIGH** | Default CRA port - commonly used |
| **Django Backend** | **8001** | Application | ⚠️ **MEDIUM** | Changed from 8000 to avoid 7English conflict |
| **PostgreSQL** | **5433** | Database | ✅ **LOW** | Non-standard port (standard is 5432) |
| **Redis** | **6379** | Cache/Queue | ⚠️ **MEDIUM** | Default Redis port |
| **Neo4j HTTP** | **7474** | Database UI | ✅ **LOW** | Neo4j-specific |
| **Neo4j Bolt** | **7687** | Database | ✅ **LOW** | Neo4j-specific |
| **Nginx HTTP** | **80** | Web Server | ⚠️ **HIGH** | Standard HTTP port |
| **Nginx HTTPS** | **443** | Web Server | ⚠️ **HIGH** | Standard HTTPS port |

---

## 📋 Detailed Port Information

### 1. Frontend (React Development Server)
- **Port**: `3000`
- **Service**: React development server (Create React App)
- **Access**: `http://localhost:3000`
- **Configuration**: 
  - Default CRA port
  - Can be changed via `PORT` environment variable in `package.json`
- **Conflict Risk**: ⚠️ **HIGH** - Very commonly used port
- **Files**:
  - `frontend/package.json` - Scripts configuration
  - `frontend/src/services/api.ts` - API base URL references

### 2. Backend (Django Development Server)
- **Port**: `8001` ⚠️ **CHANGED FROM 8000**
- **Service**: Django REST API backend
- **Access**: `http://localhost:8001`
- **API Endpoints**: `http://localhost:8001/api/`
- **Admin Panel**: `http://localhost:8001/admin/`
- **Configuration**: 
  - Changed from 8000 to avoid conflict with 7English project
  - Started with: `python manage.py runserver 0.0.0.0:8001`
- **Conflict Risk**: ⚠️ **MEDIUM** - Common web development port
- **Files**:
  - `frontend/src/services/api.ts` - API base URL (line 11)
  - `start-hybrid.sh` - Startup script (line 46)
  - `start-all.sh` - Startup script (line 57)
  - `nginx/anylab.conf` - Nginx proxy configuration (line 84)

### 3. PostgreSQL Database
- **Port**: `5433` (mapped from container port 5432)
- **Service**: PostgreSQL database with pgvector extension
- **Access**: `localhost:5433`
- **Configuration**: 
  - Intentionally uses non-standard port to avoid conflicts
  - Standard PostgreSQL port is 5432
  - Container internal port: 5432
  - Host mapped port: 5433
- **Conflict Risk**: ✅ **LOW** - Non-standard port
- **Files**:
  - `docker-compose.yml` - Port mapping (line 11)
  - `backend/anylab/settings.py` - Database connection settings

### 4. Redis Cache & Message Broker
- **Port**: `6379`
- **Service**: Redis for caching and Celery message broker
- **Access**: `localhost:6379`
- **Configuration**: 
  - Default Redis port
  - Used by Celery for task queue
  - Used by Django for caching
- **Conflict Risk**: ⚠️ **MEDIUM** - Default Redis port
- **Files**:
  - `docker-compose.yml` - Port mapping (line 29)
  - `backend/anylab/settings.py` - Redis connection settings

### 5. Neo4j Graph Database
- **HTTP Port**: `7474` (Browser interface)
- **Bolt Port**: `7687` (Database connections)
- **Service**: Neo4j graph database
- **Access**: 
  - Browser: `http://localhost:7474`
  - Python driver: `bolt://localhost:7687`
- **Configuration**: 
  - Default Neo4j ports
  - HTTP for web interface
  - Bolt for Python driver connections
- **Conflict Risk**: ✅ **LOW** - Neo4j-specific ports
- **Files**:
  - `docker-compose.yml` - Port mappings (lines 47-48)
  - `backend/anylab/settings.py` - Neo4j connection settings

### 6. Nginx Web Server (Production)
- **HTTP Port**: `80`
- **HTTPS Port**: `443`
- **Service**: Nginx reverse proxy
- **Access**: 
  - HTTP: `http://anylab.dpdns.org` (redirects to HTTPS)
  - HTTPS: `https://anylab.dpdns.org`
- **Configuration**: 
  - Routes `/api/*` → Backend (port 8001)
  - Routes `/admin/*` → Backend (port 8001)
  - Routes `/*` → Frontend (port 3000)
- **Conflict Risk**: ⚠️ **HIGH** - Standard web ports
- **Files**:
  - `nginx/anylab.conf` - Nginx configuration

---

## 🔍 Port Conflict Analysis

### Known Conflicts Resolved

#### ✅ Resolved: Port 8000 → 8001
- **Conflict**: 7English project uses port 8000
- **Solution**: AnyLab changed to port 8001
- **Status**: ✅ **RESOLVED**
- **Files Updated**:
  - `frontend/src/services/api.ts` - Changed API base URL
  - `start-hybrid.sh` - Updated startup script
  - `start-all.sh` - Updated startup script
  - `nginx/anylab.conf` - Updated proxy configuration

#### ✅ No Conflict: PostgreSQL
- **7English**: Uses port 5432 (standard)
- **AnyLab**: Uses port 5433 (non-standard)
- **Status**: ✅ **NO CONFLICT**

#### ✅ Shared Service: Ollama (Port 11434)
- **Both Projects**: Use port 11434 for Ollama
- **Status**: ✅ **SHARED** - Safe to share (Ollama handles multiple clients)

### Potential Conflicts to Watch

1. **Port 3000 (Frontend)**
   - High conflict risk
   - Many React projects use this port
   - **Solution**: Can be changed via `PORT` environment variable

2. **Port 6379 (Redis)**
   - Medium conflict risk
   - Default Redis port
   - **Solution**: Can be changed in `docker-compose.yml`

3. **Ports 80/443 (Nginx)**
   - High conflict risk
   - Standard web ports
   - **Note**: Only used in production with domain setup

---

## 🔧 How to Change Ports

### Change Frontend Port (3000 → 3001)
Edit `frontend/package.json`:
```json
"scripts": {
  "start": "PORT=3001 react-scripts start"
}
```

### Change Backend Port (8001 → 8002)
1. Update `frontend/src/services/api.ts` (line 11):
   ```typescript
   const port = '8002';
   ```

2. Update startup scripts:
   - `start-hybrid.sh` (line 46)
   - `start-all.sh` (line 57)

3. Update nginx config (if using):
   - `nginx/anylab.conf` (line 84)

### Change PostgreSQL Port (5433 → 5434)
1. Update `docker-compose.yml` (line 11):
   ```yaml
   ports:
     - "5434:5432"
   ```

2. Update `backend/anylab/settings.py`:
   ```python
   'PORT': '5434',
   ```

### Change Redis Port (6379 → 6380)
1. Update `docker-compose.yml` (line 29):
   ```yaml
   ports:
     - "6380:6379"
   ```

2. Update `backend/anylab/settings.py`:
   ```python
   CELERY_BROKER_URL = 'redis://localhost:6380/0'
   CELERY_RESULT_BACKEND = 'redis://localhost:6380/0'
   ```

---

## 📁 Configuration Files Reference

| File | Purpose | Ports Configured |
|------|---------|------------------|
| `docker-compose.yml` | Docker services | 5433, 6379, 7474, 7687 |
| `frontend/src/services/api.ts` | API client | 8001 (backend) |
| `frontend/package.json` | Frontend scripts | 3000 (frontend) |
| `backend/anylab/settings.py` | Django settings | 5433, 6379, 7687 |
| `start-hybrid.sh` | Startup script | 8001, 3000 |
| `start-all.sh` | Startup script | 8001, 3000 |
| `nginx/anylab.conf` | Nginx config | 80, 443, 8001, 3000 |

---

## ✅ Current Status

- ✅ Backend port changed from 8000 → 8001 (conflict resolved)
- ✅ PostgreSQL uses non-standard port 5433 (no conflict)
- ✅ All ports documented and configured
- ⚠️ Frontend port 3000 may conflict with other React projects
- ⚠️ Redis port 6379 may conflict with other Redis instances

---

## 🧪 Testing Port Availability

To check if a port is in use:
```bash
# Check specific port
lsof -i :8001

# Check all AnyLab ports
lsof -i :3000 -i :8001 -i :5433 -i :6379 -i :7474 -i :7687
```

---

## 📝 Notes

1. **Port 8001**: Intentionally changed from 8000 to avoid conflict with 7English project
2. **Port 5433**: Intentionally non-standard to avoid conflict with local PostgreSQL
3. **Ports 80/443**: Only used when nginx is configured for domain access
4. **All ports are hardcoded**: No environment variables used (for reliability)
5. **Ollama sharing**: Both AnyLab and 7English can safely share Ollama on port 11434

---

**Last Updated**: Based on current codebase analysis
**Project**: AnyLab (Anylab103)

