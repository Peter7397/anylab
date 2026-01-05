#!/bin/bash
# Build script to work around Mac external drive xattr issues
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

# Create temporary build directory
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

echo "📦 Copying backend files to temporary directory..."
rsync -av --exclude='__pycache__' --exclude='*.pyc' --exclude='venv' --exclude='.git' \
    --exclude='._*' --exclude='.DS_Store' \
    "$PROJECT_DIR/backend/" "$TEMP_DIR/"

echo "🔨 Building Docker image..."
cd "$TEMP_DIR"
docker build -t anylab-backend:latest -f Dockerfile .

echo "✅ Build complete!"

