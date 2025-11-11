#!/bin/bash

# AnyLab Permanent Startup Script
# Ensures backend is running before starting frontend
# Handles all edge cases and provides health checks

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

BACKEND_PORT=8001
FRONTEND_PORT=3000
BACKEND_URL="http://localhost:${BACKEND_PORT}"
HEALTH_CHECK_URL="${BACKEND_URL}/api/health/"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🚀 Starting AnyLab..."
echo "=================================================="

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to check if backend is responding
check_backend_health() {
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$HEALTH_CHECK_URL" >/dev/null 2>&1; then
            return 0  # Backend is healthy
        fi
        echo -e "${YELLOW}⏳ Waiting for backend to be ready... (attempt $attempt/$max_attempts)${NC}"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    return 1  # Backend is not responding
}

# Function to start backend
start_backend() {
    echo "🔧 Starting Django Backend..."
    cd backend
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo -e "${RED}❌ Virtual environment not found. Please run: python3 -m venv venv${NC}"
        exit 1
    fi
    
    source venv/bin/activate
    
    # Check if PostgreSQL and Redis are running
    echo "📊 Checking Docker services..."
    if ! docker ps | grep -q "anylab_postgres"; then
        echo "🐘 Starting PostgreSQL..."
        if docker ps -a | grep -q "anylab_postgres"; then
            docker start anylab_postgres
        else
            docker run -d --name anylab_postgres \
                -e POSTGRES_DB=anylab \
                -e POSTGRES_USER=postgres \
                -e POSTGRES_PASSWORD=password \
                -p 5433:5432 \
                -v anylab_postgres_data:/var/lib/postgresql/data \
                postgres:15
        fi
        sleep 3
        # Enable pgvector extension
        docker exec anylab_postgres psql -U postgres -d anylab -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null || true
    fi
    
    if ! docker ps | grep -q "anylab_redis"; then
        echo "🔴 Starting Redis..."
        if docker ps -a | grep -q "anylab_redis"; then
            docker start anylab_redis
        else
            docker run -d --name anylab_redis \
                -p 6379:6379 \
                -v anylab_redis_data:/data \
                redis:7-alpine
        fi
    fi
    
    # Run migrations
    echo "🔄 Running database migrations..."
    python manage.py migrate --noinput >/dev/null 2>&1 || echo "⚠️  Migration warnings (non-fatal)"
    
    # Check if backend is already running
    if check_port $BACKEND_PORT; then
        echo -e "${YELLOW}⚠️  Backend port $BACKEND_PORT is already in use${NC}"
        if check_backend_health; then
            echo -e "${GREEN}✅ Backend is already running and healthy${NC}"
            cd ..
            return 0
        else
            echo -e "${RED}❌ Port $BACKEND_PORT is in use but backend is not responding${NC}"
            echo "   Killing process on port $BACKEND_PORT..."
            lsof -ti:$BACKEND_PORT | xargs kill -9 2>/dev/null || true
            sleep 2
        fi
    fi
    
    # Start Django server
    echo "🌐 Starting Django server on $BACKEND_URL"
    nohup python manage.py runserver 0.0.0.0:$BACKEND_PORT > /tmp/anylab_backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > /tmp/anylab_backend.pid
    
    cd ..
    
    # Wait for backend to be ready
    if check_backend_health; then
        echo -e "${GREEN}✅ Backend is running and healthy${NC}"
        return 0
    else
        echo -e "${RED}❌ Backend failed to start or is not responding${NC}"
        echo "   Check logs: tail -f /tmp/anylab_backend.log"
        exit 1
    fi
}

# Function to start frontend
start_frontend() {
    echo "🎨 Starting React Frontend..."
    cd frontend
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo "📦 Installing frontend dependencies..."
        npm install
    fi
    
    # Check if frontend is already running
    if check_port $FRONTEND_PORT; then
        echo -e "${YELLOW}⚠️  Frontend port $FRONTEND_PORT is already in use${NC}"
        echo "   Killing process on port $FRONTEND_PORT..."
        lsof -ti:$FRONTEND_PORT | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
    
    # Start React development server
    echo "⚛️  Starting React server on http://localhost:$FRONTEND_PORT"
    nohup npm start > /tmp/anylab_frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > /tmp/anylab_frontend.pid
    
    cd ..
    
    sleep 3
    if check_port $FRONTEND_PORT; then
        echo -e "${GREEN}✅ Frontend is running${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  Frontend may still be starting...${NC}"
        return 0
    fi
}

# Function to stop services
stop_services() {
    echo ""
    echo "🛑 Stopping AnyLab services..."
    
    # Stop backend
    if [ -f "/tmp/anylab_backend.pid" ]; then
        BACKEND_PID=$(cat /tmp/anylab_backend.pid)
        kill $BACKEND_PID 2>/dev/null || true
        rm /tmp/anylab_backend.pid
    fi
    # Also kill by port if PID file is missing
    lsof -ti:$BACKEND_PORT | xargs kill -9 2>/dev/null || true
    
    # Stop frontend
    if [ -f "/tmp/anylab_frontend.pid" ]; then
        FRONTEND_PID=$(cat /tmp/anylab_frontend.pid)
        kill $FRONTEND_PID 2>/dev/null || true
        rm /tmp/anylab_frontend.pid
    fi
    # Also kill by port if PID file is missing
    lsof -ti:$FRONTEND_PORT | xargs kill -9 2>/dev/null || true
    
    echo "✅ Services stopped."
}

# Set up signal handlers
trap stop_services SIGINT SIGTERM EXIT

# Main execution
main() {
    # Start backend first
    start_backend
    
    # Wait a moment for backend to fully initialize
    sleep 2
    
    # Start frontend
    start_frontend
    
    echo ""
    echo -e "${GREEN}✅ AnyLab is now running!${NC}"
    echo "=================================================="
    echo ""
    echo "📍 Access URLs:"
    echo "   Frontend: http://localhost:$FRONTEND_PORT"
    echo "   Backend:  $BACKEND_URL"
    echo ""
    echo "📋 Log Files:"
    echo "   Backend:  tail -f /tmp/anylab_backend.log"
    echo "   Frontend: tail -f /tmp/anylab_frontend.log"
    echo ""
    echo "🔐 Login Credentials:"
    echo "   Username: admin"
    echo "   Password: admin123"
    echo ""
    echo "🛑 Press Ctrl+C to stop all services"
    echo ""
    
    # Keep script running
    wait
}

# Run main function
main

