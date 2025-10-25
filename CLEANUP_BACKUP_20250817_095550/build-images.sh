#!/bin/bash

# OneLab Image Build Script
# Build the backend image with pgvector pre-installed

echo "🔨 Building OneLab Backend Image with pgvector..."

# Build the image
docker build -f Dockerfile.pgvector -t onelab-backend:latest .

echo "✅ Image built successfully!"
echo ""
echo "📦 Image: onelab-backend:latest"
echo "🔍 To verify: docker images | grep onelab-backend"
echo "🚀 To start system: ./start-system.sh"
