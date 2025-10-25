#!/bin/bash

# OnLab Hybrid Development Stop Script
# This script stops the backend and frontend services

echo "🛑 Stopping OnLab Hybrid Development Environment..."
echo "=================================================="

# Stop backend
if [ -f "backend/.backend.pid" ]; then
    BACKEND_PID=$(cat backend/.backend.pid)
    echo "🔧 Stopping Django Backend (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null
    rm backend/.backend.pid
    echo "✅ Backend stopped."
else
    echo "⚠️  Backend PID file not found, trying to kill Django processes..."
    pkill -f "python manage.py runserver" 2>/dev/null
fi

# Stop frontend
if [ -f "frontend/.frontend.pid" ]; then
    FRONTEND_PID=$(cat frontend/.frontend.pid)
    echo "🎨 Stopping React Frontend (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID 2>/dev/null
    rm frontend/.frontend.pid
    echo "✅ Frontend stopped."
else
    echo "⚠️  Frontend PID file not found, trying to kill React processes..."
    pkill -f "react-scripts" 2>/dev/null
fi

# Stop Docker services (optional - uncomment if you want to stop them too)
# echo "🐳 Stopping Docker services..."
# docker stop onlab_postgres onlab_redis 2>/dev/null
# echo "✅ Docker services stopped."

echo ""
echo "✅ All OnLab services stopped!"
echo "=================================================="
