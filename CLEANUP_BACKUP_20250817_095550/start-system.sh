#!/bin/bash

# OneLab System Startup Script
# This script starts the backend services without rebuilding existing images

echo "🚀 Starting OneLab Backend System..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

# Check if the onelab-backend image exists
if ! docker images --format "table {{.Repository}}:{{.Tag}}" | grep -q "^onelab-backend:latest$"; then
    echo "❌ onelab-backend:latest image not found"
    echo "🔨 Please run ./build-images.sh first to build the image"
    echo "💡 This is a one-time setup - after building, you won't need to rebuild"
    exit 1
else
    echo "✅ onelab-backend:latest image found - using existing image"
fi

# Start services
echo "🐳 Starting Docker services..."
docker compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo "📊 Service Status:"
docker compose ps

# Check if web service is healthy
echo "🔍 Checking web service health..."
for i in {1..30}; do
    if curl -s http://localhost:8000/api/health/ > /dev/null 2>&1; then
        echo "✅ Backend is ready at http://localhost:8000"
        break
    elif [ $i -eq 30 ]; then
        echo "⚠️  Backend health check timeout. Check logs with: docker compose logs web"
    else
        echo "⏳ Waiting for backend to be ready... ($i/30)"
        sleep 2
    fi
done

echo ""
echo "🎉 OneLab Backend System Started!"
echo "📍 Services:"
echo "   • Backend API: http://localhost:8000"
echo "   • Admin Panel: http://localhost:8000/admin"
echo "   • Flower (Celery Monitor): http://localhost:5555"
echo "   • PostgreSQL: localhost:5432"
echo "   • Redis: localhost:6379"
echo ""
echo "📝 Useful commands:"
echo "   • View logs: docker compose logs -f"
echo "   • Stop system: docker compose down"
echo "   • Restart system: docker compose restart"
echo ""
