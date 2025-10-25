#!/bin/bash

# OneLab Local Development Startup Script
# This script starts the backend services for local development

echo "🚀 Starting OneLab Local Development Services..."
echo "==============================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found"
    echo "💡 Please run ./setup-local-dev.sh first"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found"
    echo "💡 Please run ./setup-local-dev.sh first"
    exit 1
fi

# Check if PostgreSQL is running
echo "🔍 Checking PostgreSQL..."
if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "⚠️  PostgreSQL is not running"
    echo "🚀 Starting PostgreSQL container..."
    docker run -d --name onelab_postgres \
        -e POSTGRES_DB=onelab \
        -e POSTGRES_USER=postgres \
        -e POSTGRES_PASSWORD=password \
        -p 5432:5432 \
        pgvector/pgvector:pg16
    
    echo "⏳ Waiting for PostgreSQL to start..."
    sleep 10
else
    echo "✅ PostgreSQL is running"
fi

# Check if Redis is running
echo "🔍 Checking Redis..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo "⚠️  Redis is not running"
    echo "🚀 Starting Redis container..."
    docker run -d --name onelab_redis \
        -p 6379:6379 \
        redis:7-alpine
    
    echo "⏳ Waiting for Redis to start..."
    sleep 5
else
    echo "✅ Redis is running"
fi

# Run migrations
echo "🔄 Running database migrations..."
python manage.py migrate

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

# Start Celery worker in background
echo "🚀 Starting Celery worker..."
celery -A onelab worker --loglevel=info &
CELERY_PID=$!

# Start Celery beat in background
echo "🚀 Starting Celery beat..."
celery -A onelab beat --loglevel=info &
CELERY_BEAT_PID=$!

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $CELERY_PID 2>/dev/null
    kill $CELERY_BEAT_PID 2>/dev/null
    echo "✅ Services stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

echo ""
echo "🎉 All services started!"
echo "📍 Services:"
echo "   • Django: http://localhost:8000"
echo "   • Admin: http://localhost:8000/admin"
echo "   • API: http://localhost:8000/api/"
echo "   • PostgreSQL: localhost:5432"
echo "   • Redis: localhost:6379"
echo ""
echo "💡 Press Ctrl+C to stop all services"
echo ""

# Start Django development server
echo "🚀 Starting Django development server..."
python manage.py runserver 0.0.0.0:8000
