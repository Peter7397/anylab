#!/bin/bash
# Master startup script for hybrid system
# Starts all Docker services, Django backend, Celery worker, and React frontend

set -euo pipefail

echo "🚀 Starting AnyLab Hybrid System..."
echo "=================================="
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Step 1: Start Docker services
echo "📦 Step 1: Starting Docker services (PostgreSQL, Redis, Neo4j)..."
if [ -f "start-docker-services.sh" ]; then
    bash start-docker-services.sh
else
    echo "⚠️  start-docker-services.sh not found, using docker-compose..."
    docker-compose up -d postgres redis neo4j
    sleep 10
fi

# Step 2: Wait for services to be ready
echo ""
echo "⏳ Step 2: Waiting for all services to be ready..."
sleep 5

# Step 3: Start backend
echo ""
echo "🔧 Step 3: Starting Django backend..."

# Check if already running
if pgrep -f "manage.py runserver" > /dev/null; then
    echo "⚠️  Django is already running"
    read -p "Stop and restart? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pkill -f "manage.py runserver"
        sleep 2
    else
        echo "❌ Skipping Django startup"
    fi
fi

if ! pgrep -f "manage.py runserver" > /dev/null; then
    cd backend
    source venv/bin/activate
    
    # Run migrations
    echo "   Running database migrations..."
    DB_PORT=5433 python manage.py migrate --noinput
    
    # Start Django
    echo "   Starting Django server on http://localhost:8001 (port changed to avoid conflict with 7English on 8000)"
    DB_PORT=5433 python manage.py runserver 0.0.0.0:8001 > ../logs/django.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > .backend.pid
    cd ..
    echo "   ✅ Backend started (PID: $BACKEND_PID)"
else
    echo "   ✅ Backend already running"
fi

# Step 4: Start Celery worker
echo ""
echo "⚙️  Step 4: Starting Celery worker..."

# Check if already running
if pgrep -f "celery.*worker.*anylab" > /dev/null; then
    echo "⚠️  Celery worker is already running"
    read -p "Stop and restart? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pkill -f "celery.*worker.*anylab"
        sleep 2
    else
        echo "❌ Skipping Celery startup"
    fi
fi

if ! pgrep -f "celery.*worker.*anylab" > /dev/null; then
    cd backend
    source venv/bin/activate
    
    # Create logs directory if needed
    mkdir -p ../logs
    
    echo "   Starting Celery worker..."
    DB_PORT=5433 nohup ./start-celery-worker.sh > ../logs/celery.log 2>&1 &
    CELERY_PID=$!
    cd ..
    echo "   ✅ Celery worker started (PID: $CELERY_PID)"
else
    echo "   ✅ Celery worker already running"
fi

# Step 5: Start frontend
echo ""
echo "🎨 Step 5: Starting React frontend..."

# Check if already running
if pgrep -f "react-scripts start" > /dev/null; then
    echo "⚠️  Frontend is already running"
    read -p "Stop and restart? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pkill -f "react-scripts start"
        sleep 2
    else
        echo "❌ Skipping frontend startup"
    fi
fi

if ! pgrep -f "react-scripts start" > /dev/null; then
    cd frontend
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        echo "   Installing frontend dependencies..."
        npm install
    fi
    
    echo "   Starting React server on http://localhost:3000"
    npm start > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > .frontend.pid
    cd ..
    echo "   ✅ Frontend started (PID: $FRONTEND_PID)"
else
    echo "   ✅ Frontend already running"
fi

# Create logs directory
mkdir -p logs

echo ""
echo "✅ All services started!"
echo ""
echo "📍 Access URLs:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8001 (changed from 8000 to avoid conflict with 7English)"
echo "   Neo4j:    http://localhost:7474"
echo ""
echo "📊 Logs:"
echo "   Django:  logs/django.log"
echo "   Celery:  logs/celery.log"
echo "   Frontend: logs/frontend.log"
echo ""
echo "🛑 To stop: ./stop-all.sh"
echo ""



