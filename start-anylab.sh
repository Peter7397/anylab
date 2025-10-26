#!/bin/bash

# AnyLab Startup Script
# This script starts all required services for the AnyLab application

echo "🚀 Starting AnyLab Application..."

# Change to project directory
cd /Volumes/Orico/OnLab0812

# Start Docker services (PostgreSQL and Redis)
echo "📦 Starting Docker services..."
docker-compose -f django-pgvector-pdf/docker-compose.yml up -d

# Wait for Docker services to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Start backend
echo "🔧 Starting Django backend..."
cd backend
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000 &
BACKEND_PID=$!

# Start frontend
echo "🎨 Starting React frontend..."
cd ../frontend
npm start &
FRONTEND_PID=$!

# Save PIDs for later reference
echo $BACKEND_PID > /tmp/anylab_backend.pid
echo $FRONTEND_PID > /tmp/anylab_frontend.pid

echo "✅ AnyLab is starting up!"
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend: http://localhost:8000"
echo "🌍 Public URL: https://anylab.dpdns.org"
echo ""
echo "To stop the services, run: ./stop-anylab.sh"
echo "Or kill the processes: kill $BACKEND_PID $FRONTEND_PID"
