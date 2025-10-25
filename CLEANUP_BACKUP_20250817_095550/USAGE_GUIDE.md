# OneLab Backend - No-Rebuild Usage Guide

## ✅ System is Ready for Daily Use (No Rebuilding Needed)

The system has been optimized to use existing Docker images. **You will NOT need to rebuild** unless you change code or dependencies.

## Daily Startup (Fast - Uses Existing Images)

```bash
./start-system.sh
```

**What it does:**
- ✅ Uses existing `onelab-backend:latest` image (7.58GB with all dependencies)
- ✅ Starts PostgreSQL with pgvector 
- ✅ Starts Redis for caching
- ✅ Starts all Celery services
- ✅ Connects to your local Ollama instance
- ⚡ **Fast startup** - No image building!

## Daily Shutdown

```bash
./stop-system.sh
```

## System Status Check

```bash
docker compose ps
```

## View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs web -f
docker compose logs celery -f
```

## Only Rebuild When Needed

**Rebuild ONLY if you:**
- Change Python code significantly
- Update `requirements.txt` dependencies
- Need to update the base Docker image

```bash
./rebuild-images.sh
```

## System URLs (When Running)

- **Backend API**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin  
- **API Documentation**: http://localhost:8000/api/
- **Flower (Celery Monitor)**: http://localhost:5555
- **Database**: localhost:5432 (postgres/password)
- **Redis**: localhost:6379

## Configuration Files (Already Optimized)

### ✅ `docker-compose.yml`
- Uses `image: onelab-backend:latest` (no build section)
- Hard-coded database credentials (no variable issues)
- All services use `.env` file consistently

### ✅ `onelab/settings.py`
- Removed SQLite fallback that caused localhost connections
- Defaults to `DB_HOST=db` (Docker service name)
- Proper PostgreSQL-only configuration

### ✅ `.env`
- All environment variables properly defined
- Database settings match docker-compose
- Consistent across all services

### ✅ `start-system.sh`
- Checks for existing image (no rebuild attempt)
- Fast startup using existing containers
- Comprehensive health checks

## Troubleshooting

### If services fail to start:
```bash
docker compose logs web
docker compose logs db
```

### If you get "image not found" error:
```bash
./build-images.sh  # One-time build
```

### Reset database (if needed):
```bash
docker compose down
docker volume rm backend_postgres_data
./start-system.sh
```

## Architecture Summary

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend       │    │   Ollama        │
│   (React)       │◄──►│   (Django)       │◄──►│   (Local)       │
│   Port 3000     │    │   Port 8000      │    │   Port 11434    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   PostgreSQL     │
                    │   + pgvector     │
                    │   Port 5432      │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │      Redis       │
                    │   (Cache/Queue)  │
                    │   Port 6379      │
                    └──────────────────┘
```

## Next Steps

1. ✅ **Backend is ready** - No rebuilding needed for daily use
2. 🔄 **Start Frontend** - Navigate to `/frontend` and run `npm start`
3. 🚀 **Access System** - http://localhost:3000 (frontend) → http://localhost:8000 (backend)

---

**Key Point**: The system is now configured for **offline development** with **fast startups**. No more waiting for Docker builds!
