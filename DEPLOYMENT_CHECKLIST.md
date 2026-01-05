# Deployment Checklist

## Mac M4 Development Setup ✅

### Prerequisites
- [x] Docker Desktop installed
- [x] Git repository cloned
- [x] Environment files configured (`.env.mac`)

### Services Status
- [x] PostgreSQL: Healthy (port 5433)
- [x] Redis: Healthy (port 6379)
- [x] Neo4j: Healthy (ports 7474, 7687)
- [x] Backend: Healthy (port 8000)
- [x] Celery Worker: Running
- [x] Celery Beat: Running
- [x] Ollama: Running (port 11435, model: qwen2.5:1.5b)
- [x] Frontend: Running (port 3000)

### Verification
- [x] Backend API: http://localhost:8000/api/health/
- [x] Frontend: http://localhost:3000
- [x] Ollama model downloaded and accessible
- [x] Database migrations completed
- [x] All merge conflicts resolved

---

## Windows A1000 Production Setup

### Prerequisites (Before Migration)
- [ ] Docker Desktop for Windows installed
- [ ] WSL2 installed and configured
- [ ] NVIDIA drivers installed (verify with `nvidia-smi`)
- [ ] NVIDIA Container Toolkit installed
- [ ] Git installed
- [ ] At least 50GB free disk space

### Pre-Migration (On Mac)
- [ ] Run migration script: `./scripts/migrate-to-windows.sh`
- [ ] Verify migration package created in `migration-package/` directory
- [ ] Copy migration package to Windows PC
- [ ] Commit and push all code changes to Git

### Windows Setup Steps
1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd Anylab103
   ```

2. **Configure Environment**
   - [ ] Copy `.env.windows` to `.env`
   - [ ] Review and update environment variables if needed
   - [ ] Verify GPU settings for Ollama

3. **Start Base Services**
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.windows.yml --env-file .env.windows up -d postgres redis neo4j
   ```
   - [ ] Wait 10-15 seconds for services to initialize
   - [ ] Verify services are healthy: `docker compose ps`

4. **Restore Databases**
   ```bash
   # PostgreSQL
   docker exec -i anylab_postgres psql -U postgres anylab < migration-package/postgres_backup_*.sql
   
   # Neo4j (if backup exists)
   docker exec anylab_neo4j neo4j-admin database load --database=neo4j --from-path=/data/backups/neo4j_backup_*.dump --overwrite-destination=true
   ```
   - [ ] Verify PostgreSQL restore completed
   - [ ] Verify Neo4j restore completed (if applicable)

5. **Start All Services**
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.windows.yml --env-file .env.windows up -d
   ```
   - [ ] Wait for all services to start
   - [ ] Check service status: `docker compose ps`

6. **Verify Deployment**
   - [ ] Backend health check: http://localhost:8000/api/health/
   - [ ] Frontend accessible: http://localhost:3000
   - [ ] Ollama GPU access: `docker exec anylab_ollama nvidia-smi`
   - [ ] Ollama model downloaded: `docker exec anylab_ollama ollama list`
   - [ ] Test RAG query through frontend

7. **Post-Deployment**
   - [ ] Re-upload media files through application interface
   - [ ] Configure user accounts and permissions
   - [ ] Test all RAG search modes
   - [ ] Verify GPU acceleration is working
   - [ ] Set up automated backups
   - [ ] Configure monitoring (optional)

### Troubleshooting Checklist
- [ ] If GPU not accessible: Check NVIDIA drivers and container toolkit
- [ ] If services fail: Check logs with `docker compose logs <service>`
- [ ] If ports in use: Change port mappings in compose files
- [ ] If database errors: Verify connection strings in `.env.windows`
- [ ] If Ollama unhealthy: Check model download and GPU access

### Performance Verification
- [ ] GPU utilization: `nvidia-smi -l 1` shows activity during AI queries
- [ ] Response times acceptable for RAG queries
- [ ] Memory usage within limits
- [ ] No excessive CPU usage

---

## Quick Reference Commands

### Mac Development
```bash
# Start all services
docker compose -f docker-compose.yml -f docker-compose.mac.yml --env-file .env.mac up -d

# Stop all services
docker compose -f docker-compose.yml -f docker-compose.mac.yml down

# View logs
docker compose -f docker-compose.yml -f docker-compose.mac.yml logs -f

# Rebuild services
docker compose -f docker-compose.yml -f docker-compose.mac.yml up -d --build
```

### Windows Production
```bash
# Start all services
docker compose -f docker-compose.yml -f docker-compose.windows.yml --env-file .env.windows up -d

# Stop all services
docker compose -f docker-compose.yml -f docker-compose.windows.yml down

# View logs
docker compose -f docker-compose.yml -f docker-compose.windows.yml logs -f

# Check GPU access
docker exec anylab_ollama nvidia-smi
```

### Database Operations
```bash
# Backup PostgreSQL
docker exec anylab_postgres pg_dump -U postgres anylab > backup_$(date +%Y%m%d).sql

# Backup Neo4j
docker exec anylab_neo4j neo4j-admin database dump --database=neo4j --to-path=/data/backups/

# Restore PostgreSQL
docker exec -i anylab_postgres psql -U postgres anylab < backup_file.sql
```

---

## Notes
- Media files are NOT migrated - re-upload on Windows
- Ollama model will be downloaded automatically on first use
- GPU acceleration requires NVIDIA Container Toolkit
- Health check "unhealthy" for Celery is normal (no health check defined)

