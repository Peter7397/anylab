# Services Started - Quick Reference

## Current Status

### Docker Services
All services are running in Docker containers:
- ✅ PostgreSQL (port 5433)
- ✅ Redis (port 6379)
- ✅ Neo4j (ports 7474, 7687)
- ✅ Ollama (port 11435)
- ✅ Backend (Django/Gunicorn)
- ✅ Celery Worker
- ✅ Celery Beat

### Local Services
- ✅ Frontend (React) - Starting on port 3000

## Service URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001 (or 8000)
- **Admin Panel**: http://localhost:8001/admin
- **Health Check**: http://localhost:8001/api/health/

## Check Service Status

```bash
# Docker services
docker compose ps

# Backend health
curl http://localhost:8001/api/health/

# Frontend
curl http://localhost:3000
```

## View Logs

```bash
# Backend logs
docker compose logs -f backend

# Frontend logs (if running locally)
# Check terminal where npm start was run

# All services
docker compose logs -f
```

## Stop Services

```bash
# Stop Docker services
docker compose down

# Stop frontend (if running locally)
pkill -f "npm start"
```

