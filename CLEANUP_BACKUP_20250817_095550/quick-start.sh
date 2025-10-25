#!/bin/bash

# OneLab Quick Start - No Rebuild Version
# Run this script for daily development startup

echo "🚀 OneLab Quick Start (No Rebuild)"
echo ""

# Check Docker
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker not running. Starting Docker Desktop..."
    open -a Docker
    echo "⏳ Waiting for Docker to start..."
    sleep 15
fi

# Check if image exists
if ! docker images --format "table {{.Repository}}:{{.Tag}}" | grep -q "^onelab-backend:latest$"; then
    echo "❌ Backend image not found. Building it now..."
    ./build-images.sh
    echo "✅ Image built! Future startups will be faster."
fi

# Start system
echo "🐳 Starting OneLab system..."
./start-system.sh

echo ""
echo "🎉 OneLab is starting up!"
echo "📍 Frontend: http://localhost:3000 (start separately)"
echo "📍 Backend:  http://localhost:8000"
echo "📍 Admin:    http://localhost:8000/admin"
echo ""
echo "💡 Next time just run: ./start-system.sh (much faster!)"
