#!/bin/bash

# OneLab Complete System Startup Script
# This script starts both backend and frontend services

echo "🚀 Starting OneLab Complete System..."
echo "======================================"

# Check if we're in the right directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: Please run this script from the OneLab root directory"
    echo "💡 Current directory: $(pwd)"
    echo "📁 Expected structure:"
    echo "   OneLab0803/"
    echo "   ├── backend/"
    echo "   └── frontend/"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

# Check if the onelab-backend image exists
if ! docker images --format "table {{.Repository}}:{{.Tag}}" | grep -q "^onelab-backend:latest$"; then
    echo "❌ onelab-backend:latest image not found"
    echo "🔨 Building backend image first..."
    cd backend
    ./build-images.sh
    cd ..
fi

echo "✅ Backend image found - using existing image"

# Start backend services
echo ""
echo "🐳 Starting Backend Services..."
cd backend
./start-system.sh
cd ..

# Wait for backend to be ready
echo ""
echo "⏳ Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/api/health/ > /dev/null 2>&1; then
        echo "✅ Backend is ready at http://localhost:8000"
        break
    elif [ $i -eq 30 ]; then
        echo "⚠️  Backend health check timeout. Check logs with: cd backend && docker compose logs web"
    else
        echo "⏳ Waiting for backend... ($i/30)"
        sleep 2
    fi
done

# Start frontend
echo ""
echo "🎯 Starting Frontend..."
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

echo "🚀 Starting React development server..."
echo "📍 Frontend will be available at: http://localhost:3000"
echo "🔧 Backend is running at: http://localhost:8000"
echo ""
echo "💡 To stop: Press Ctrl+C"
echo ""

npm start
