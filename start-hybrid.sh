#!/bin/bash

# OnLab Hybrid Development Startup Script
# This script starts the backend (local) and frontend (local) for development

echo "🚀 Starting OnLab Hybrid Development Environment..."
echo "=================================================="

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "⚠️  Port $1 is already in use"
        return 1
    else
        return 0
    fi
}

# Function to start backend
start_backend() {
    echo "🔧 Starting Django Backend..."
    cd backend
    source venv/bin/activate
    
    # Check if PostgreSQL and Redis are running
    echo "📊 Checking Docker services..."
    if ! docker ps | grep -q "onlab_postgres"; then
        echo "🐘 Starting PostgreSQL..."
        docker run -d --name onlab_postgres -e POSTGRES_DB=onlab -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=password -p 5433:5432 postgres:15
        sleep 5
        # Enable pgvector extension
        docker exec onlab_postgres psql -U postgres -d onlab -c "CREATE EXTENSION IF NOT EXISTS vector;"
    fi
    
    if ! docker ps | grep -q "onlab_redis"; then
        echo "🔴 Starting Redis..."
        docker run -d --name onlab_redis -p 6379:6379 redis:7-alpine
    fi
    
    # Run migrations
    echo "🔄 Running database migrations..."
    python manage.py migrate --noinput
    
    # Start Django server
    echo "🌐 Starting Django server on http://localhost:8000"
    python manage.py runserver 0.0.0.0:8000 &
    BACKEND_PID=$!
    echo $BACKEND_PID > .backend.pid
    cd ..
}

# Function to start frontend
start_frontend() {
    echo "🎨 Starting React Frontend..."
    cd frontend
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        echo "📦 Installing frontend dependencies..."
        npm install
    fi
    
    # Start React development server
    echo "⚛️  Starting React server on http://localhost:3000"
    npm start &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > .frontend.pid
    cd ..
}

# Main execution
main() {
    # Check if ports are available
    if ! check_port 8000; then
        echo "❌ Backend port 8000 is already in use. Please stop the existing service."
        exit 1
    fi
    
    if ! check_port 3000; then
        echo "❌ Frontend port 3000 is already in use. Please stop the existing service."
        exit 1
    fi
    
    # Start services
    start_backend
    sleep 3
    start_frontend
    
    echo ""
    echo "✅ OnLab Hybrid Development Environment Started!"
    echo "=================================================="
    echo "🌐 Backend: http://localhost:8000"
    echo "⚛️  Frontend: http://localhost:3000"
    echo "🔐 Login: http://localhost:8000/login/"
    echo ""
    echo "📋 Demo Credentials:"
    echo "   Username: admin"
    echo "   Password: admin123!@#"
    echo ""
    echo "🛑 To stop services, run: ./stop-hybrid.sh"
    echo ""
    
    # Wait for user input to stop
    echo "Press Ctrl+C to stop all services..."
    wait
}

# Handle cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping OnLab services..."
    
    # Stop backend
    if [ -f "backend/.backend.pid" ]; then
        BACKEND_PID=$(cat backend/.backend.pid)
        kill $BACKEND_PID 2>/dev/null
        rm backend/.backend.pid
    fi
    
    # Stop frontend
    if [ -f "frontend/.frontend.pid" ]; then
        FRONTEND_PID=$(cat frontend/.frontend.pid)
        kill $FRONTEND_PID 2>/dev/null
        rm frontend/.frontend.pid
    fi
    
    echo "✅ Services stopped."
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Run main function
main
