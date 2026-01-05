#!/bin/bash
# Migration script to prepare data for Windows deployment
# Run this on Mac before migrating to Windows

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

MIGRATION_DIR="$PROJECT_DIR/migration-package"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "📦 Creating migration package for Windows deployment..."
echo "Timestamp: $TIMESTAMP"
echo ""

# Create migration directory
mkdir -p "$MIGRATION_DIR"

# 1. Backup PostgreSQL database
echo "🗄️  Backing up PostgreSQL database..."
docker exec anylab_postgres pg_dump -U postgres anylab > "$MIGRATION_DIR/postgres_backup_$TIMESTAMP.sql"
echo "✅ PostgreSQL backup created: postgres_backup_$TIMESTAMP.sql"

# 2. Backup Neo4j database
echo "🕸️  Backing up Neo4j database..."
docker exec anylab_neo4j neo4j-admin database dump --database=neo4j --to-path=/data/backups/ 2>&1 || echo "⚠️  Neo4j backup may require manual steps"
# Copy from container
docker cp anylab_neo4j:/data/backups/neo4j.dump "$MIGRATION_DIR/neo4j_backup_$TIMESTAMP.dump" 2>&1 || echo "⚠️  Neo4j dump not found, may need manual backup"
echo "✅ Neo4j backup attempted"

# 3. Create migration instructions
cat > "$MIGRATION_DIR/README.md" << 'EOF'
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
EOF

echo "✅ Migration package created in: $MIGRATION_DIR"
echo ""
echo "📋 Next steps:"
echo "1. Copy the migration-package directory to your Windows PC"
echo "2. Follow instructions in migration-package/README.md"
echo "3. See WINDOWS_DEPLOYMENT.md for detailed setup instructions"
echo ""
echo "⚠️  Note: Media files are NOT included. Re-upload them on Windows."

