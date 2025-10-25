#!/bin/bash

# OneLab Image Rebuild Script
# Use this script only when you need to rebuild images after code changes

echo "🔄 Rebuilding OneLab Backend Images..."

# Stop existing services
echo "🛑 Stopping existing services..."
docker compose down

# Remove existing images
echo "🗑️  Removing old images..."
docker rmi onelab-backend:latest 2>/dev/null || true

# Build new images
echo "📦 Building new images with pgvector..."
docker build -f Dockerfile.pgvector -t onelab-backend:latest .

echo "✅ Images rebuilt successfully!"
echo ""
echo "🚀 To start the system: ./start-system.sh"
