#!/bin/bash

# RAG System Backup to Orico Drive
# This script creates a timestamped backup of the OneLab RAG system

# Get current timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="RAG_Backup_${TIMESTAMP}"

# Define source directory (current project)
SOURCE_DIR="$(pwd)"

# Try to detect Orico drive - common mount points on macOS
ORICO_PATHS=(
    "/Volumes/ORICO"
    "/Volumes/ORICO_HDD"
    "/Volumes/ORICO_SSD"
    "/Volumes/ORICO_*"
    "/Volumes/ORICO*"
)

ORICO_DRIVE=""

# Try to find the Orico drive
for path in "${ORICO_PATHS[@]}"; do
    if [ -d "$path" ]; then
        ORICO_DRIVE="$path"
        echo "Found Orico drive at: $ORICO_DRIVE"
        break
    fi
done

# If no Orico drive found, ask user to specify
if [ -z "$ORICO_DRIVE" ]; then
    echo "Orico drive not automatically detected."
    echo "Please enter the path to your Orico drive:"
    read -r ORICO_DRIVE
    
    if [ ! -d "$ORICO_DRIVE" ]; then
        echo "Error: The specified path does not exist or is not accessible."
        echo "Please check the path and try again."
        exit 1
    fi
fi

# Create backup directory on Orico drive
BACKUP_DIR="${ORICO_DRIVE}/${BACKUP_NAME}"
echo "Creating backup directory: $BACKUP_DIR"

# Create the backup directory
mkdir -p "$BACKUP_DIR"

# Check if directory was created successfully
if [ ! -d "$BACKUP_DIR" ]; then
    echo "Error: Failed to create backup directory on Orico drive."
    echo "Please check if the drive has sufficient space and write permissions."
    exit 1
fi

echo "Starting backup process..."
echo "Source: $SOURCE_DIR"
echo "Destination: $BACKUP_DIR"
echo "Timestamp: $TIMESTAMP"

# Create a backup log file
BACKUP_LOG="${BACKUP_DIR}/backup_log.txt"
echo "RAG System Backup Log" > "$BACKUP_LOG"
echo "Timestamp: $TIMESTAMP" >> "$BACKUP_LOG"
echo "Source: $SOURCE_DIR" >> "$BACKUP_LOG"
echo "Destination: $BACKUP_DIR" >> "$BACKUP_LOG"
echo "----------------------------------------" >> "$BACKUP_LOG"

# Function to log backup progress
log_progress() {
    echo "$1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$BACKUP_LOG"
}

# Copy main project files (excluding large directories)
log_progress "Copying project files..."

# Copy all files and directories except large ones
rsync -av --progress \
    --exclude='node_modules' \
    --exclude='venv' \
    --exclude='.git' \
    --exclude='build' \
    --exclude='media' \
    --exclude='staticfiles' \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='.DS_Store' \
    --exclude='*.log' \
    --exclude='celerybeat-schedule' \
    "$SOURCE_DIR/" "$BACKUP_DIR/"

if [ $? -eq 0 ]; then
    log_progress "Project files copied successfully"
else
    log_progress "Error: Failed to copy project files"
    exit 1
fi

# Create a special backup info file
cat > "${BACKUP_DIR}/BACKUP_INFO.txt" << EOF
OneLab RAG System Backup
========================

Backup Created: $(date '+%Y-%m-%d %H:%M:%S')
Source Directory: $SOURCE_DIR
Backup Name: $BACKUP_NAME

System Components:
- Backend: Django REST Framework with RAG services
- Frontend: React with TypeScript
- Database: PostgreSQL with pgvector
- AI: Ollama (Qwen model)
- Cache: Redis

RAG Features:
- Basic RAG Search
- Advanced RAG Search  
- Comprehensive RAG Search
- Document Management
- Knowledge Library
- Chat History Persistence

To restore this backup:
1. Copy the backup to your target system
2. Follow the instructions in RAG_SYSTEM_BACKUP_README.md
3. Set up the required services (PostgreSQL, Redis, Ollama)
4. Install dependencies and configure environment variables

For detailed restoration instructions, see RAG_SYSTEM_BACKUP_README.md
EOF

# Create a quick restore script
cat > "${BACKUP_DIR}/restore_backup.sh" << 'EOF'
#!/bin/bash

echo "OneLab RAG System Restore Script"
echo "================================="
echo ""
echo "This script will help you restore the RAG system from this backup."
echo ""

# Check if we're in the backup directory
if [ ! -f "BACKUP_INFO.txt" ]; then
    echo "Error: Please run this script from the backup directory."
    exit 1
fi

echo "Backup found. Starting restoration process..."
echo ""

# Check for required tools
command -v python3 >/dev/null 2>&1 || { echo "Error: Python 3 is required but not installed."; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "Error: Node.js/npm is required but not installed."; exit 1; }

echo "Prerequisites check passed."
echo ""

echo "Next steps for restoration:"
echo "1. Set up PostgreSQL database with pgvector extension"
echo "2. Install and start Redis server"
echo "3. Install and start Ollama with Qwen model"
echo "4. Copy this backup to your target system"
echo "5. Install Python dependencies: pip install -r backend/requirements.txt"
echo "6. Install Node.js dependencies: npm install (in frontend directory)"
echo "7. Configure environment variables in backend/.env and frontend/.env"
echo "8. Run database migrations: python manage.py migrate"
echo "9. Start the backend server: python manage.py runserver"
echo "10. Start the frontend: npm start"
echo ""
echo "For detailed instructions, see RAG_SYSTEM_BACKUP_README.md"
EOF

chmod +x "${BACKUP_DIR}/restore_backup.sh"

# Calculate backup size
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
log_progress "Backup completed successfully"
log_progress "Backup size: $BACKUP_SIZE"

# Create a summary
cat > "${BACKUP_DIR}/BACKUP_SUMMARY.txt" << EOF
Backup Summary
==============

Backup Name: $BACKUP_NAME
Created: $(date '+%Y-%m-%d %H:%M:%S')
Size: $BACKUP_SIZE
Location: $BACKUP_DIR

Contents:
- Complete RAG system source code
- Configuration files
- Documentation and guides
- Backup and restore scripts
- System architecture documentation

Status: SUCCESS
EOF

echo ""
echo "=========================================="
echo "BACKUP COMPLETED SUCCESSFULLY!"
echo "=========================================="
echo "Backup Name: $BACKUP_NAME"
echo "Location: $BACKUP_DIR"
echo "Size: $BACKUP_SIZE"
echo ""
echo "Files included:"
echo "- Complete RAG system source code"
echo "- All configuration files"
echo "- Documentation and guides"
echo "- Backup and restore scripts"
echo ""
echo "To restore this backup, see:"
echo "- BACKUP_INFO.txt (general information)"
echo "- RAG_SYSTEM_BACKUP_README.md (detailed instructions)"
echo "- restore_backup.sh (quick restore script)"
echo ""
echo "Backup log saved to: $BACKUP_LOG"
