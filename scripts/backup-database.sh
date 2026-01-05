#!/bin/bash
# Database Backup Script for Mac to Windows Migration
# Creates PostgreSQL and Neo4j backups (media files excluded - will re-upload on Windows)

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

# Create backup directory with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="backups/migration_to_windows_${TIMESTAMP}"
mkdir -p "$BACKUP_DIR"

echo -e "${GREEN}📦 Creating Database Backup for Windows Migration${NC}"
echo "======================================"
echo ""

# Check if Docker containers are running
if ! docker ps | grep -q anylab_postgres; then
    echo -e "${RED}❌ PostgreSQL container is not running!${NC}"
    echo "   Please start Docker services first: docker compose up -d"
    exit 1
fi

# Backup PostgreSQL
echo -e "${YELLOW}📊 Step 1: Backing up PostgreSQL database...${NC}"
docker exec anylab_postgres pg_dump -U postgres -F c -f /tmp/anylab_backup.dump anylab
docker cp anylab_postgres:/tmp/anylab_backup.dump "$BACKUP_DIR/postgres_backup.dump"
docker exec anylab_postgres rm /tmp/anylab_backup.dump
echo -e "${GREEN}✅ PostgreSQL backup created: $BACKUP_DIR/postgres_backup.dump${NC}"
echo ""

# Backup Neo4j (if running)
if docker ps | grep -q anylab_neo4j; then
    echo -e "${YELLOW}📊 Step 2: Backing up Neo4j database...${NC}"
    docker exec anylab_neo4j neo4j-admin database dump neo4j --to-path=/tmp/
    docker cp anylab_neo4j:/tmp/neo4j.dump "$BACKUP_DIR/neo4j_backup.dump" 2>/dev/null || echo "Neo4j dump may not exist yet"
    echo -e "${GREEN}✅ Neo4j backup created: $BACKUP_DIR/neo4j_backup.dump${NC}"
    echo ""
else
    echo -e "${YELLOW}⚠️  Neo4j container not running, skipping Neo4j backup${NC}"
    echo ""
fi

# Create backup manifest
cat > "$BACKUP_DIR/BACKUP_MANIFEST.txt" << EOF
AnyLab Database Backup for Windows Migration
=============================================
Created: $(date)
Source: Mac M4 (ARM64)
Target: Windows x86_64 with NVIDIA A1000

Contents:
---------
1. postgres_backup.dump - PostgreSQL database dump
2. neo4j_backup.dump - Neo4j graph database dump (if available)

Note: Media files are NOT included in this backup.
      You will need to re-upload documents on Windows system.

Restore Instructions:
---------------------
1. Start Docker services on Windows
2. Restore PostgreSQL:
   docker exec -i anylab_postgres pg_restore -U postgres -d anylab -c < postgres_backup.dump
   
3. Restore Neo4j (if applicable):
   docker exec -i anylab_neo4j neo4j-admin database load neo4j < neo4j_backup.dump

4. Download models on Windows:
   docker exec anylab_ollama ollama pull qwen2.5:7b
   docker exec anylab_ollama ollama pull bge-m3:latest
EOF

echo -e "${GREEN}✅ Backup complete!${NC}"
echo ""
echo "📁 Backup location: $BACKUP_DIR"
echo "📄 Manifest: $BACKUP_DIR/BACKUP_MANIFEST.txt"
echo ""
echo -e "${YELLOW}⚠️  Remember: Media files are NOT backed up. Re-upload documents on Windows.${NC}"

