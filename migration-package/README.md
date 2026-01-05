# Windows Migration Package

This package contains database backups and migration instructions for deploying Anylab on Windows with NVIDIA A1000 GPU.

## Contents

- `postgres_backup_*.sql` - PostgreSQL database backup
- `neo4j_backup_*.dump` - Neo4j database backup (if available)
- `WINDOWS_DEPLOYMENT.md` - Detailed Windows deployment instructions

## Quick Start

1. **Install Prerequisites on Windows:**
   - Docker Desktop for Windows
   - WSL2 (Windows Subsystem for Linux 2)
   - NVIDIA Container Toolkit
   - Git

2. **Clone Repository:**
   ```bash
   git clone <repository-url>
   cd Anylab103
   ```

3. **Restore Databases:**
   ```bash
   # Start services first
   docker compose -f docker-compose.yml -f docker-compose.windows.yml --env-file .env.windows up -d postgres neo4j
   
   # Wait for services to be ready
   sleep 10
   
   # Restore PostgreSQL
   docker exec -i anylab_postgres psql -U postgres anylab < postgres_backup_*.sql
   
   # Restore Neo4j (if backup exists)
   docker exec anylab_neo4j neo4j-admin database load --database=neo4j --from-path=/data/backups/neo4j_backup_*.dump --overwrite-destination=true
   ```

4. **Start All Services:**
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.windows.yml --env-file .env.windows up -d
   ```

5. **Verify Deployment:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Health Check: http://localhost:8000/api/health/

## Media Files

Media files are NOT included in this migration package. You will need to re-upload them on the Windows system through the application interface.

## Troubleshooting

See `WINDOWS_DEPLOYMENT.md` for detailed troubleshooting steps.
