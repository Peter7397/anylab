# Backup Guide - AnyLab Project

**Last Updated:** 2025-01-XX  
**Purpose:** Comprehensive backup strategy and procedures for the AnyLab project

## Overview

This document outlines the backup procedures for the AnyLab project, including:
- Full project backup
- Database backup
- Configuration backup
- Media files backup
- Git repository backup

## Backup Types

### 1. Full Project Backup

A complete backup of the entire project directory, including:
- Source code
- Configuration files
- Documentation
- Scripts
- Docker configurations

### 2. Database Backup

PostgreSQL database backup including:
- All tables and data
- Vector embeddings (pgvector)
- User data
- Document metadata
- Chat history

### 3. Media Files Backup

Backup of uploaded content:
- PDF documents
- Uploaded files
- User avatars
- Generated reports

### 4. Configuration Backup

Backup of critical configuration:
- Environment files
- Docker compose files
- Nginx configurations
- SSL certificates

## Backup Scripts

### Full Backup Script

Create `backup-full.sh`:

```bash
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

# 2. Backup database
echo "Backing up database..."
docker exec anylab-postgres-1 pg_dump -U postgres anylab > "${BACKUP_DIR}/${BACKUP_NAME}/database_${TIMESTAMP}.sql"

# 3. Backup media files
echo "Backing up media files..."
if [ -d "${PROJECT_DIR}/backend/media" ]; then
    tar -czf "${BACKUP_DIR}/${BACKUP_NAME}/media_${TIMESTAMP}.tar.gz" -C "${PROJECT_DIR}/backend" media/
fi

# 4. Backup configuration files
echo "Backing up configuration..."
mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}/config"
cp "${PROJECT_DIR}/docker-compose.yml" "${BACKUP_DIR}/${BACKUP_NAME}/config/"
cp "${PROJECT_DIR}/docker-compose.optimized.yml" "${BACKUP_DIR}/${BACKUP_NAME}/config/" 2>/dev/null || true
cp -r "${PROJECT_DIR}/nginx" "${BACKUP_DIR}/${BACKUP_NAME}/config/" 2>/dev/null || true

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
- Database dump: database_${TIMESTAMP}.sql
- Media files: media_${TIMESTAMP}.tar.gz
- Configuration files

Backup Location: ${BACKUP_DIR}/${BACKUP_NAME}

To restore:
1. Extract source code to project directory
2. Restore database: docker exec -i anylab-postgres-1 psql -U postgres anylab < database_${TIMESTAMP}.sql
3. Extract media: tar -xzf media_${TIMESTAMP}.tar.gz -C backend/
4. Restore configuration files
EOF

# 6. Create compressed archive
echo "Creating compressed archive..."
cd "${BACKUP_DIR}"
tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}/"
echo "Compressed backup created: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"

# 7. Calculate backup size
BACKUP_SIZE=$(du -sh "${BACKUP_DIR}/${BACKUP_NAME}" | cut -f1)
ARCHIVE_SIZE=$(du -sh "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" | cut -f1)

echo ""
echo "Backup completed successfully!"
echo "Backup directory: ${BACKUP_DIR}/${BACKUP_NAME}"
echo "Backup size: ${BACKUP_SIZE}"
echo "Compressed size: ${ARCHIVE_SIZE}"
echo "Archive: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
```

### Quick Backup Script

Create `backup-quick.sh` for quick incremental backups:

```bash
#!/bin/bash

# Quick Backup Script (Source code only)
set -e

BACKUP_DIR="/Volumes/Orico/Anylab103/backups"
PROJECT_DIR="/Volumes/Orico/Anylab103"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="anylab_quick_${TIMESTAMP}"

mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}"

echo "Starting quick backup..."

# Backup source code only
rsync -av --exclude='node_modules' \
          --exclude='venv' \
          --exclude='__pycache__' \
          --exclude='.git' \
          --exclude='build' \
          --exclude='staticfiles' \
          --exclude='media' \
          --exclude='logs' \
          "${PROJECT_DIR}/" "${BACKUP_DIR}/${BACKUP_NAME}/"

# Create archive
cd "${BACKUP_DIR}"
tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}/"

echo "Quick backup completed: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
```

### Database-Only Backup Script

Create `backup-database.sh`:

```bash
#!/bin/bash

# Database Backup Script
set -e

BACKUP_DIR="/Volumes/Orico/Anylab103/backups/database"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/anylab_db_${TIMESTAMP}.sql"

mkdir -p "${BACKUP_DIR}"

echo "Backing up database..."

# Backup database
docker exec anylab-postgres-1 pg_dump -U postgres anylab > "${BACKUP_FILE}"

# Compress
gzip "${BACKUP_FILE}"

echo "Database backup completed: ${BACKUP_FILE}.gz"
```

## Manual Backup Procedures

### 1. Git Repository Backup

```bash
# Create a bundle of the entire repository
cd /Volumes/Orico/Anylab103
git bundle create anylab_backup_$(date +%Y%m%d).bundle --all

# Or push to a remote backup repository
git remote add backup https://github.com/yourusername/anylab-backup.git
git push backup --all
```

### 2. Docker Images Backup

```bash
# Save Docker images
docker save anylab-django:latest -o anylab-django-$(date +%Y%m%d).tar
docker save anylab-react:latest -o anylab-react-$(date +%Y%m%d).tar
```

### 3. Configuration Files Backup

```bash
# Backup critical configuration
mkdir -p backups/config_$(date +%Y%m%d)
cp docker-compose.yml backups/config_$(date +%Y%m%d)/
cp -r nginx backups/config_$(date +%Y%m%d)/
cp backend/anylab/settings.py backups/config_$(date +%Y%m%d)/
```

## Restore Procedures

### Restore Full Backup

```bash
# 1. Extract backup
cd /Volumes/Orico/Anylab103/backups
tar -xzf anylab_backup_YYYYMMDD_HHMMSS.tar.gz

# 2. Restore source code
rsync -av backup_name/source/ /Volumes/Orico/Anylab103/

# 3. Restore database
docker exec -i anylab-postgres-1 psql -U postgres anylab < backup_name/database_YYYYMMDD_HHMMSS.sql

# 4. Restore media files
tar -xzf backup_name/media_YYYYMMDD_HHMMSS.tar.gz -C /Volumes/Orico/Anylab103/backend/

# 5. Restore configuration
cp -r backup_name/config/* /Volumes/Orico/Anylab103/
```

### Restore Database Only

```bash
# Stop services (optional, recommended)
docker-compose down

# Restore database
gunzip -c backups/database/anylab_db_YYYYMMDD_HHMMSS.sql.gz | \
  docker exec -i anylab-postgres-1 psql -U postgres anylab

# Restart services
docker-compose up -d
```

## Backup Schedule Recommendations

### Daily Backups
- Database backup (automated)
- Configuration backup (if changed)

### Weekly Backups
- Full project backup
- Media files backup

### Monthly Backups
- Complete system backup
- Archive old backups

### Before Major Changes
- Always create a full backup before:
  - Major code updates
  - Database migrations
  - Configuration changes
  - System upgrades

## Backup Storage

### Local Storage
- Primary: `/Volumes/Orico/Anylab103/backups/`
- Keep last 7 daily backups
- Keep last 4 weekly backups
- Keep last 12 monthly backups

### Remote Storage (Recommended)
- Cloud storage (Dropbox, Google Drive, etc.)
- Remote server
- Git repository (for code only)

## Backup Verification

### Verify Backup Integrity

```bash
# Check backup archive
tar -tzf backup_name.tar.gz > /dev/null && echo "Archive OK" || echo "Archive corrupted"

# Verify database backup
head -n 20 database_backup.sql | grep -q "PostgreSQL database dump" && echo "DB backup OK" || echo "DB backup corrupted"
```

### Test Restore

Periodically test restore procedures to ensure backups are working:
1. Create a test environment
2. Restore from backup
3. Verify all components work
4. Document any issues

## Automation

### Cron Job for Daily Backups

Add to crontab (`crontab -e`):

```bash
# Daily database backup at 2 AM
0 2 * * * /Volumes/Orico/Anylab103/backup-database.sh

# Weekly full backup on Sundays at 3 AM
0 3 * * 0 /Volumes/Orico/Anylab103/backup-full.sh
```

## Backup Checklist

Before creating a backup:
- [ ] Check available disk space
- [ ] Verify database is accessible
- [ ] Stop unnecessary services (optional)
- [ ] Document current system state
- [ ] Note any recent changes

After creating a backup:
- [ ] Verify backup file exists
- [ ] Check backup size (not zero)
- [ ] Test backup integrity
- [ ] Document backup location
- [ ] Update backup log

## Emergency Recovery

### Quick Recovery Steps

1. **Stop all services**
   ```bash
   docker-compose down
   ```

2. **Restore from latest backup**
   ```bash
   ./restore-backup.sh latest
   ```

3. **Verify services**
   ```bash
   docker-compose up -d
   docker-compose ps
   ```

4. **Test application**
   - Access frontend
   - Test login
   - Verify database connectivity

## Backup Log

Maintain a backup log file:

```bash
# Create backup log entry
echo "$(date): Full backup created - ${BACKUP_NAME}" >> backups/backup.log
```

## Best Practices

1. **3-2-1 Rule**
   - 3 copies of data
   - 2 different media types
   - 1 off-site backup

2. **Regular Testing**
   - Test restore procedures monthly
   - Verify backup integrity
   - Document restore times

3. **Documentation**
   - Keep backup procedures documented
   - Update when procedures change
   - Train team members

4. **Security**
   - Encrypt sensitive backups
   - Secure backup storage
   - Limit backup access

## Troubleshooting

### Backup Fails

1. Check disk space: `df -h`
2. Check permissions: `ls -la backups/`
3. Check Docker status: `docker ps`
4. Review error messages

### Restore Fails

1. Verify backup file integrity
2. Check database connection
3. Verify file permissions
4. Check Docker container status
5. Review application logs

## Support

For backup-related issues:
- Review this guide
- Check backup logs
- Verify system resources
- Test in a safe environment first

---

**Last Updated:** 2025-01-XX  
**Version:** 1.0.0

