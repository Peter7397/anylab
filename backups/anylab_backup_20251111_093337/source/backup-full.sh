#!/bin/bash

# Full Backup Script for AnyLab
# Usage: ./backup-full.sh

set -e

# Configuration
BACKUP_DIR="/Volumes/Orico/Anylab103/backups"
PROJECT_DIR="/Volumes/Orico/Anylab103"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="anylab_backup_${TIMESTAMP}"

# Create backup directory
mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}"

echo "Starting full backup: ${BACKUP_NAME}"

# 1. Backup source code (excluding large directories)
echo "Backing up source code..."
rsync -av --exclude='node_modules' \
          --exclude='venv' \
          --exclude='venv.old-*' \
          --exclude='__pycache__' \
          --exclude='*.pyc' \
          --exclude='.git' \
          --exclude='build' \
          --exclude='staticfiles' \
          --exclude='media' \
          --exclude='logs' \
          --exclude='*.log' \
          --exclude='celerybeat-schedule*' \
          "${PROJECT_DIR}/" "${BACKUP_DIR}/${BACKUP_NAME}/source/"

# 2. Backup database (if Docker container is running)
echo "Backing up database..."
if docker ps | grep -q anylab-postgres; then
    CONTAINER_NAME=$(docker ps | grep anylab-postgres | awk '{print $NF}' | head -1)
    docker exec "${CONTAINER_NAME}" pg_dump -U postgres anylab > "${BACKUP_DIR}/${BACKUP_NAME}/database_${TIMESTAMP}.sql" 2>/dev/null || \
    docker exec "${CONTAINER_NAME}" pg_dump -U postgres anylab > "${BACKUP_DIR}/${BACKUP_NAME}/database_${TIMESTAMP}.sql" || \
    echo "Warning: Could not backup database. Container may not be running."
else
    echo "Warning: PostgreSQL container not running. Skipping database backup."
fi

# 3. Backup media files
echo "Backing up media files..."
if [ -d "${PROJECT_DIR}/backend/media" ]; then
    tar -czf "${BACKUP_DIR}/${BACKUP_NAME}/media_${TIMESTAMP}.tar.gz" -C "${PROJECT_DIR}/backend" media/ 2>/dev/null || \
    echo "Warning: Could not backup media files."
fi

# 4. Backup configuration files
echo "Backing up configuration..."
mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}/config"
cp "${PROJECT_DIR}/docker-compose.yml" "${BACKUP_DIR}/${BACKUP_NAME}/config/" 2>/dev/null || true
cp "${PROJECT_DIR}/docker-compose.optimized.yml" "${BACKUP_DIR}/${BACKUP_NAME}/config/" 2>/dev/null || true
[ -d "${PROJECT_DIR}/nginx" ] && cp -r "${PROJECT_DIR}/nginx" "${BACKUP_DIR}/${BACKUP_NAME}/config/" 2>/dev/null || true

# 5. Create backup manifest
echo "Creating backup manifest..."
cat > "${BACKUP_DIR}/${BACKUP_NAME}/BACKUP_MANIFEST.txt" << EOF
AnyLab Full Backup
==================
Date: $(date)
Timestamp: ${TIMESTAMP}
Backup Name: ${BACKUP_NAME}

Contents:
- Source code (excluding node_modules, venv, build artifacts)
- Database dump: database_${TIMESTAMP}.sql (if available)
- Media files: media_${TIMESTAMP}.tar.gz (if available)
- Configuration files

Backup Location: ${BACKUP_DIR}/${BACKUP_NAME}

To restore:
1. Extract source code to project directory
2. Restore database: docker exec -i CONTAINER_NAME psql -U postgres anylab < database_${TIMESTAMP}.sql
3. Extract media: tar -xzf media_${TIMESTAMP}.tar.gz -C backend/
4. Restore configuration files
EOF

# 6. Create compressed archive
echo "Creating compressed archive..."
cd "${BACKUP_DIR}"
tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}/"
echo "Compressed backup created: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"

# 7. Calculate backup size
BACKUP_SIZE=$(du -sh "${BACKUP_DIR}/${BACKUP_NAME}" 2>/dev/null | cut -f1 || echo "N/A")
ARCHIVE_SIZE=$(du -sh "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" 2>/dev/null | cut -f1 || echo "N/A")

echo ""
echo "Backup completed successfully!"
echo "Backup directory: ${BACKUP_DIR}/${BACKUP_NAME}"
echo "Backup size: ${BACKUP_SIZE}"
echo "Compressed size: ${ARCHIVE_SIZE}"
echo "Archive: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"

# 8. Log backup
echo "$(date): Full backup created - ${BACKUP_NAME} (${ARCHIVE_SIZE})" >> "${BACKUP_DIR}/backup.log" 2>/dev/null || true

