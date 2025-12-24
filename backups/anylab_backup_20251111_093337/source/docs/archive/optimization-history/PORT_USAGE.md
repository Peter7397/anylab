# AnyLab Project - Port Usage

This document lists all ports used by the AnyLab project to help you avoid conflicts with other projects.

## Application Ports

### Frontend (React)
- **Port 3000**: React development server
  - Default CRA port
  - Accessible at: `http://localhost:3000`
  - Configurable via `PORT` environment variable in `package.json`

### Backend (Django)
- **Port 8000**: Django development server
  - Default Django runserver port
  - Accessible at: `http://localhost:8000`
  - API endpoints: `http://localhost:8000/api/`

## Docker Services Ports

### PostgreSQL
- **Port 5433**: PostgreSQL (mapped from container port 5432)
  - Used by Django backend to connect to database
  - **IMPORTANT**: This is mapped to avoid conflicts with local PostgreSQL (default 5432)
  - Connection: `localhost:5433`

### Redis
- **Port 6379**: Redis cache and message broker
  - Used by Celery for task queue
  - Used by Django for caching
  - **WARNING**: This is the default Redis port - may conflict with other Redis instances

### Neo4j
- **Port 7474**: Neo4j HTTP (browser interface)
  - Accessible at: `http://localhost:7474`
  
- **Port 7687**: Neo4j Bolt protocol (database connections)
  - Used by Python driver to connect to Neo4j
  - **WARNING**: This is the default Neo4j Bolt port

## Summary Table

| Service | Port | Type | Conflict Risk |
|---------|------|------|---------------|
| React Frontend | 3000 | Application | High (default CRA port) |
| Django Backend | 8000 | Application | High (common web dev port) |
| PostgreSQL | 5433 | Database | Low (non-standard port) |
| Redis | 6379 | Cache/Queue | Medium (default Redis port) |
| Neo4j HTTP | 7474 | Database UI | Low (specific to Neo4j) |
| Neo4j Bolt | 7687 | Database | Low (specific to Neo4j) |

## Port Conflict Prevention

If you need to change ports to avoid conflicts:

### Change Frontend Port
Edit `frontend/package.json`:
```json
"scripts": {
  "start": "PORT=3001 react-scripts start"
}
```

### Change Backend Port
When starting Django:
```bash
python manage.py runserver 0.0.0.0:8001
```
Also update `frontend/src/services/api.ts` to point to the new port.

### Change PostgreSQL Port
Edit `docker-compose.yml`:
```yaml
ports:
  - "5434:5432"  # Change from 5433 to 5434
```
Also update `backend/anylab/settings.py`:
```python
'PORT': '5434',  # Update this
```

### Change Redis Port
Edit `docker-compose.yml`:
```yaml
ports:
  - "6380:6379"  # Change from 6379 to 6380
```
Also update `backend/anylab/settings.py`:
```python
CELERY_BROKER_URL = 'redis://localhost:6380/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6380/0'
```

### Change Neo4j Ports
Edit `docker-compose.yml`:
```yaml
ports:
  - "7475:7474"   # HTTP
  - "7688:7687"   # Bolt
```
Also update `backend/anylab/settings.py`:
```python
NEO4J_URI = 'bolt://localhost:7688'
```

## Current Configuration

All ports are hardcoded in the following files:
- `docker-compose.yml` - Docker service ports
- `backend/anylab/settings.py` - Database, Redis, Neo4j ports
- `frontend/src/services/api.ts` - Backend API URL (defaults to port 8000)
- `frontend/package.json` - Frontend port (defaults to 3000)

## Notes

- Port 5433 is intentionally non-standard to avoid conflicts with local PostgreSQL
- Ports 3000 and 8000 are commonly used in web development - high conflict risk
- Redis and Neo4j use default ports - medium to low conflict risk
- All port configurations are currently hardcoded (no environment variables)

