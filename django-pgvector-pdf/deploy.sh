#!/bin/bash

# Quick Deployment Script for Django PDF Vector Search
# Usage: ./deploy.sh [target-directory]

set -e

echo "Starting deployment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Set target directory
TARGET_DIR=${1:-"./django-pgvector-pdf-deployed"}

echo "Creating deployment directory: $TARGET_DIR"
mkdir -p "$TARGET_DIR"

# Copy necessary files
echo "Copying project files..."
cp -r docker-compose.yml "$TARGET_DIR/"
cp -r Dockerfile "$TARGET_DIR/"
cp -r requirements.txt "$TARGET_DIR/"
cp -r .env "$TARGET_DIR/"
cp -r all-MiniLM-L6-v2_local_copy "$TARGET_DIR/"
cp -r pdfimport "$TARGET_DIR/"
cp -r myproject "$TARGET_DIR/"
cp -r manage.py "$TARGET_DIR/"
cp -r nginx "$TARGET_DIR/"
cp -r init-db.sh "$TARGET_DIR/"
cp -r docker-entrypoint.sh "$TARGET_DIR/"
cp -r test_ollama.py "$TARGET_DIR/"
cp -r DOCKER_SETUP.md "$TARGET_DIR/"
cp -r SETUP_COMPLETE.md "$TARGET_DIR/"

# Create deployment instructions
cat > "$TARGET_DIR/DEPLOYMENT_INSTRUCTIONS.md" << 'EOF'
# Deployment Instructions

## Quick Start:
1. Ensure Docker and Docker Compose are installed
2. Run: docker volume create ollama_data
3. Run: docker compose up -d
4. Test: python3 test_ollama.py
5. Access: http://localhost:8000

## System Requirements:
- RAM: 8GB minimum (16GB recommended)
- Storage: 20GB free space
- CPU: 4 cores minimum

## Troubleshooting:
- Check logs: docker compose logs -f
- Restart: docker compose restart
- Rebuild: docker compose up --build
EOF

echo "Deployment package created in: $TARGET_DIR"
echo ""
echo "Next steps:"
echo "1. Copy the '$TARGET_DIR' folder to your target system"
echo "2. On target system, run: cd $TARGET_DIR"
echo "3. Run: docker volume create ollama_data"
echo "4. Run: docker compose up -d"
echo "5. Test with: python3 test_ollama.py"
echo ""
echo "Deployment package is ready!" 