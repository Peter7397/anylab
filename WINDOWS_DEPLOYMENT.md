# Windows Deployment Guide - Anylab with NVIDIA A1000 GPU

This guide provides step-by-step instructions for deploying Anylab on Windows with Docker and GPU acceleration.

## Prerequisites

### 1. System Requirements
- **OS**: Windows 10/11 (64-bit)
- **GPU**: NVIDIA A1000 (or compatible NVIDIA GPU)
- **RAM**: Minimum 16GB (32GB recommended)
- **Storage**: At least 50GB free space
- **Docker**: Docker Desktop for Windows

### 2. Software Installation

#### A. Install Docker Desktop for Windows
1. Download from: https://www.docker.com/products/docker-desktop
2. Install and ensure WSL2 backend is enabled
3. Verify installation: `docker --version`

#### B. Install WSL2 (if not already installed)
```powershell
wsl --install
```
Restart your computer after installation.

#### C. Install NVIDIA Container Toolkit
1. Download NVIDIA Container Toolkit for WSL2:
   - Visit: https://github.com/NVIDIA/nvidia-docker
   - Or use: `wsl -d docker-desktop` then follow Linux installation steps

2. Verify GPU access:
   ```bash
   docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
   ```

#### D. Install Git (if not already installed)
Download from: https://git-scm.com/download/win

## Deployment Steps

### Step 1: Clone Repository
```bash
git clone <repository-url>
cd Anylab103
```

### Step 2: Configure Environment
1. Copy `.env.windows` and review settings:
   ```bash
   cp .env.windows .env
   ```

2. Update `.env.windows` if needed:
   - Database passwords
   - API keys
   - Domain names

### Step 3: Start Base Services
```bash
docker compose -f docker-compose.yml -f docker-compose.windows.yml --env-file .env.windows up -d postgres redis neo4j
```

Wait 10-15 seconds for services to initialize.

### Step 4: Restore Database (if migrating from Mac)
```bash
# Restore PostgreSQL
docker exec -i anylab_postgres psql -U postgres anylab < migration-package/postgres_backup_*.sql

# Restore Neo4j (if backup exists)
docker exec anylab_neo4j neo4j-admin database load --database=neo4j --from-path=/data/backups/neo4j_backup_*.dump --overwrite-destination=true
```

### Step 5: Start All Services
```bash
docker compose -f docker-compose.yml -f docker-compose.windows.yml --env-file .env.windows up -d
```

### Step 6: Verify Deployment
1. **Check service status:**
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.windows.yml ps
   ```

2. **Test endpoints:**
   - Health Check: http://localhost:8000/api/health/
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/api/

3. **Check GPU usage:**
   ```bash
   docker exec anylab_ollama nvidia-smi
   ```

## Service Configuration

### Ollama GPU Configuration
The `docker-compose.windows.yml` file configures Ollama for GPU acceleration:
- **Model**: `qwen2.5:7b` (optimized for A1000)
- **GPU**: NVIDIA A1000 (automatically detected)
- **Memory**: GPU memory allocated dynamically

### Port Mappings
- **Frontend**: 3000 → Container 80
- **Backend**: 8000 → Container 8000
- **PostgreSQL**: 5433 → Container 5432
- **Redis**: 6379 → Container 6379
- **Neo4j**: 7474 (HTTP), 7687 (Bolt)
- **Ollama**: 11434 → Container 11434

## Troubleshooting

### Issue: Docker cannot access GPU
**Solution:**
1. Verify NVIDIA drivers are installed: `nvidia-smi` in PowerShell
2. Check WSL2 NVIDIA support: `wsl -d docker-desktop nvidia-smi`
3. Restart Docker Desktop
4. Verify container toolkit: `docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi`

### Issue: Services fail to start
**Solution:**
1. Check logs: `docker compose -f docker-compose.yml -f docker-compose.windows.yml logs <service-name>`
2. Verify ports are not in use: `netstat -ano | findstr :8000`
3. Check Docker resources: Docker Desktop → Settings → Resources

### Issue: Ollama shows "unhealthy"
**Solution:**
1. Check Ollama logs: `docker compose logs ollama`
2. Verify model is downloaded: `docker exec anylab_ollama ollama list`
3. Test API: `curl http://localhost:11434/api/tags`

### Issue: Database connection errors
**Solution:**
1. Verify PostgreSQL is running: `docker ps | grep postgres`
2. Check connection: `docker exec -it anylab_postgres psql -U postgres -d anylab`
3. Review `.env.windows` database settings

### Issue: Frontend cannot connect to backend
**Solution:**
1. Check backend is running: `docker ps | grep backend`
2. Verify CORS settings in `backend/anylab/settings.py`
3. Check browser console for errors
4. Verify API URL in frontend configuration

## Performance Optimization

### GPU Memory Management
- Monitor GPU usage: `nvidia-smi -l 1`
- Adjust model size if needed (edit `OLLAMA_MODEL` in `.env.windows`)
- Consider using smaller model for development: `qwen2.5:1.5b`

### Docker Resource Limits
Edit `docker-compose.windows.yml` to adjust:
- CPU limits
- Memory limits
- GPU memory allocation

### Database Optimization
- PostgreSQL: Already optimized for container limits
- Neo4j: Adjust heap size in Neo4j configuration if needed
- Redis: Configured with maxmemory policy

## Maintenance

### Backup Databases
```bash
# PostgreSQL
docker exec anylab_postgres pg_dump -U postgres anylab > backup_$(date +%Y%m%d).sql

# Neo4j
docker exec anylab_neo4j neo4j-admin database dump --database=neo4j --to-path=/data/backups/
```

### Update Services
```bash
# Pull latest images
docker compose -f docker-compose.yml -f docker-compose.windows.yml pull

# Rebuild and restart
docker compose -f docker-compose.yml -f docker-compose.windows.yml up -d --build
```

### View Logs
```bash
# All services
docker compose -f docker-compose.yml -f docker-compose.windows.yml logs -f

# Specific service
docker compose -f docker-compose.yml -f docker-compose.windows.yml logs -f backend
```

## Security Considerations

1. **Change default passwords** in `.env.windows`
2. **Use HTTPS** in production (configure reverse proxy)
3. **Restrict port access** using Windows Firewall
4. **Regular updates** for Docker images and system
5. **Backup strategy** for databases and configurations

## Support

For issues specific to:
- **Docker**: Check Docker Desktop logs
- **GPU**: Verify NVIDIA drivers and container toolkit
- **Application**: Check service logs and GitHub issues

## Next Steps

After successful deployment:
1. Re-upload media files through the application interface
2. Configure user accounts and permissions
3. Set up automated backups
4. Configure monitoring and logging
5. Plan for production deployment (HTTPS, domain, etc.)

