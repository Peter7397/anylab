#!/bin/bash
# Build script for frontend to work around Mac external drive xattr issues
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

# Create temporary build directory
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

echo "📦 Copying frontend files to temporary directory..."
rsync -av --exclude='node_modules' --exclude='build' --exclude='.git' \
    --exclude='._*' --exclude='.DS_Store' \
    "$PROJECT_DIR/frontend/" "$TEMP_DIR/"

echo "🔨 Building Docker image..."
cd "$TEMP_DIR"
docker build -t anylab103-frontend:latest -f Dockerfile .

echo "✅ Build complete!"

