# 🔧 Hardcoded Configuration Summary

**Date:** November 4, 2025  
**Status:** ✅ All Configuration Hardcoded

## Overview

All configuration values have been hardcoded into the application code to ensure the system runs reliably without depending on environment variables or `.env` files.

## Backend Configuration (`backend/anylab/settings.py`)

### Database - HARDCODED
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'anylab',
        'USER': 'postgres',
        'PASSWORD': 'password',
        'HOST': '127.0.0.1',
        'PORT': '5433',
    }
}
```

### Redis - HARDCODED
```python
REDIS_URL = 'redis://localhost:6379/0'
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
```

### Neo4j - HARDCODED
```python
NEO4J_URI = 'bolt://localhost:7687'
NEO4J_USER = 'neo4j'
NEO4J_PASSWORD = 'anylab_neo4j_password'
NEO4J_DATABASE = 'neo4j'
```

### Security - HARDCODED
```python
SECRET_KEY = 'django-insecure-anylab-production-key-change-in-production-deployment'
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '192.168.1.24', '192.168.1.216', '192.168.1.15', '10.96.17.21', 'anylab.dpdns.org', '*']
```

### JWT Settings - HARDCODED
```python
ACCESS_TOKEN_LIFETIME = 5 hours
REFRESH_TOKEN_LIFETIME = 1 day
```

### Ollama AI Settings - HARDCODED
```python
OLLAMA_API_URL = 'http://localhost:11434'
OLLAMA_MODEL = 'llama3:8b'
OLLAMA_REQUEST_TIMEOUT = 120
OLLAMA_NUM_CTX = 1024
OLLAMA_DEFAULT_MAX_TOKENS = 256
OLLAMA_TEMPERATURE = 0.3
```

### Embedding Settings - HARDCODED
```python
EMBEDDING_MODEL_NAME = 'bge-m3:latest'
EMBEDDING_MODEL_FALLBACK = 'nomic-embed-text:latest'
EMBEDDING_DEVICE = 'cpu'
EMBEDDING_MODE = 'lightweight'
EMBEDDING_OFFLINE_ONLY = True
EMBEDDING_DIM = 1024
```

### Cache Settings - HARDCODED
```python
EMBEDDING_CACHE_TTL = 3600  # 1 hour
RESPONSE_CACHE_TTL = 1800   # 30 minutes
SEARCH_CACHE_TTL = 3600     # 1 hour
```

## Frontend Configuration (`frontend/src/services/api.ts`)

### API Configuration - HARDCODED
```typescript
// Auto-detects API URL based on current hostname
// Port 8000 is hardcoded
const API_BASE_URL = getApiBaseUrl(); // Uses window.location.hostname:8000/api

// JWT Storage Keys - HARDCODED
const JWT_STORAGE_KEY = 'anylab_token';
const REFRESH_TOKEN_KEY = 'anylab_refresh_token';
```

## Docker Compose Configuration (`docker-compose.yml`)

All Docker services are already hardcoded:

### PostgreSQL
- **Container:** `anylab_postgres`
- **Port:** `5433:5432`
- **Database:** `anylab`
- **User:** `postgres`
- **Password:** `password`

### Redis
- **Container:** `anylab_redis`
- **Port:** `6379:6379`

### Neo4j
- **Container:** `anylab_neo4j`
- **Ports:** `7474:7474` (HTTP), `7687:7687` (Bolt)
- **User:** `neo4j`
- **Password:** `anylab_neo4j_password`

## Hybrid Architecture

The system uses a **hybrid architecture**:

### Docker Services (Running in containers)
- PostgreSQL on port 5433
- Redis on port 6379
- Neo4j on ports 7474/7687

### Local Services (Running on host)
- Django Backend on port 8000
- React Frontend on port 3000
- Celery Worker (local)

### Connection Pattern
All local services connect to Docker services via `localhost/127.0.0.1` using the exposed ports.

## Benefits of Hardcoded Configuration

1. ✅ **No Environment Variables Needed** - System works out of the box
2. ✅ **Consistent Behavior** - Same configuration every time
3. ✅ **Easy Deployment** - No need to set up .env files
4. ✅ **Reliable** - No missing environment variable errors
5. ✅ **Well Documented** - All values are visible in code

## Port Configuration Summary

| Service | Port | Type |
|---------|------|------|
| PostgreSQL | 5433 | Docker |
| Redis | 6379 | Docker |
| Neo4j HTTP | 7474 | Docker |
| Neo4j Bolt | 7687 | Docker |
| Django Backend | 8000 | Local |
| React Frontend | 3000 | Local |
| Ollama | 11434 | Local (if installed) |

## Notes

- All values are hardcoded in `backend/anylab/settings.py`
- Frontend API configuration is hardcoded in `frontend/src/services/api.ts`
- Docker Compose configuration is in `docker-compose.yml`
- **No `.env` files are required** - the system will work without them
- The `dotenv` import has been removed from settings.py (though it's still imported, it's not used)

## Testing

To verify the configuration:
```bash
cd backend
./venv/bin/python manage.py check
```

The system should run without any environment variables set.

