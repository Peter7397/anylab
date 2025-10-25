#!/bin/bash

# Quick RAG Backup to Orico Drive
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="RAG_Backup_${TIMESTAMP}"

echo "Looking for Orico drive..."
echo "Common locations: /Volumes/ORICO, /Volumes/ORICO_HDD, etc."

# Try to find Orico drive
ORICO_DRIVE=""
for drive in /Volumes/ORICO* /Volumes/ORICO_HDD /Volumes/ORICO_SSD; do
    if [ -d "$drive" ]; then
        ORICO_DRIVE="$drive"
        echo "Found drive: $ORICO_DRIVE"
        break
    fi
done

if [ -z "$ORICO_DRIVE" ]; then
    echo "Please enter the path to your Orico drive:"
    read -r ORICO_DRIVE
fi

if [ ! -d "$ORICO_DRIVE" ]; then
    echo "Error: Drive not found or not accessible"
    exit 1
fi

BACKUP_DIR="${ORICO_DRIVE}/${BACKUP_NAME}"
echo "Creating backup: $BACKUP_DIR"

# Create backup
mkdir -p "$BACKUP_DIR"

# Copy files (excluding large directories)
cp -R . "$BACKUP_DIR/" 2>/dev/null || {
    echo "Using rsync for better compatibility..."
    rsync -av --exclude='node_modules' --exclude='venv' --exclude='.git' --exclude='build' --exclude='media' --exclude='staticfiles' . "$BACKUP_DIR/"
}

# Create backup info
echo "RAG System Backup - $(date)" > "$BACKUP_DIR/BACKUP_INFO.txt"
echo "Backup created: $(date)" >> "$BACKUP_DIR/BACKUP_INFO.txt"
echo "Source: $(pwd)" >> "$BACKUP_DIR/BACKUP_INFO.txt"

echo "Backup completed: $BACKUP_DIR"
