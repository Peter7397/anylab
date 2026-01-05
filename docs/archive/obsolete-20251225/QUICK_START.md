# Quick Start Guide

## Mac M4 Development

### First Time Setup
```bash
# 1. Clone repository
git clone <repository-url>
cd Anylab103

# 2. Start all services
docker compose -f docker-compose.yml -f docker-compose.mac.yml --env-file .env.mac up -d

# 3. Wait for services to start (30-60 seconds)
docker compose -f docker-compose.yml -f docker-compose.mac.yml ps

# 4. Access application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# Health Check: http://localhost:8000/api/health/
```

### Daily Development
```bash
# Start services
docker compose -f docker-compose.yml -f docker-compose.mac.yml --env-file .env.mac up -d

# Stop services
docker compose -f docker-compose.yml -f docker-compose.mac.yml down

# View logs
docker compose -f docker-compose.yml -f docker-compose.mac.yml logs -f <service-name>
```

---

## Windows A1000 Production

### First Time Setup
```bash
# 1. Install prerequisites (see WINDOWS_DEPLOYMENT.md)
# - Docker Desktop for Windows
# - WSL2
# - NVIDIA Container Toolkit
# - Git

# 2. Clone repository
git clone <repository-url>
cd Anylab103

# 3. Start base services
docker compose -f docker-compose.yml -f docker-compose.windows.yml --env-file .env.windows up -d postgres redis neo4j

# 4. Restore databases (if migrating from Mac)
docker exec -i anylab_postgres psql -U postgres anylab < migration-package/postgres_backup_*.sql

# 5. Start all services
docker compose -f docker-compose.yml -f docker-compose.windows.yml --env-file .env.windows up -d

# 6. Verify GPU access
docker exec anylab_ollama nvidia-smi

# 7. Access application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
```

### Daily Operations
```bash
# Start services
docker compose -f docker-compose.yml -f docker-compose.windows.yml --env-file .env.windows up -d

# Stop services
docker compose -f docker-compose.yml -f docker-compose.windows.yml down

# Check GPU usage
docker exec anylab_ollama nvidia-smi

# View logs
docker compose -f docker-compose.yml -f docker-compose.windows.yml logs -f <service-name>
```

---

## Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | React application |
| Backend API | http://localhost:8000 | Django REST API |
| Health Check | http://localhost:8000/api/health/ | Service health status |
| Neo4j Browser | http://localhost:7474 | Graph database browser |
| Ollama API | http://localhost:11434 (Mac) / http://localhost:11435 (Windows) | AI model API |

---

## Common Issues

### Services won't start
```bash
# Check logs
docker compose logs <service-name>

# Check port conflicts
netstat -ano | findstr :8000  # Windows
lsof -i :8000                  # Mac

# Rebuild services
docker compose up -d --build
```

### GPU not accessible (Windows)
```bash
# Verify NVIDIA drivers
nvidia-smi

# Check WSL2 GPU support
wsl -d docker-desktop nvidia-smi

# Verify container toolkit
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### Database connection errors
```bash
# Check if database is running
docker ps | grep postgres

# Test connection
docker exec -it anylab_postgres psql -U postgres -d anylab

# Check environment variables
docker compose config | grep DATABASE
```

---

## File Structure

```
Anylab103/
├── backend/              # Django backend
│   ├── Dockerfile
│   └── ...
├── frontend/             # React frontend
│   ├── Dockerfile
│   └── ...
├── scripts/              # Utility scripts
│   ├── migrate-to-windows.sh
│   ├── backup-database.sh
│   └── ...
├── docker-compose.yml    # Base configuration
├── docker-compose.mac.yml    # Mac overrides
├── docker-compose.windows.yml # Windows overrides
├── .env.mac              # Mac environment variables
├── .env.windows          # Windows environment variables
├── WINDOWS_DEPLOYMENT.md # Detailed Windows guide
├── DEPLOYMENT_CHECKLIST.md # Deployment checklist
└── QUICK_START.md        # This file
```

---

## Support

- **Detailed Windows Guide**: See `WINDOWS_DEPLOYMENT.md`
- **Deployment Checklist**: See `DEPLOYMENT_CHECKLIST.md`
- **Troubleshooting**: Check service logs and documentation

