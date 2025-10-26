#!/bin/bash

# AnyLab Stop Script
# This script stops all AnyLab services

echo "🛑 Stopping AnyLab Application..."

# Stop frontend and backend if PIDs exist
if [ -f /tmp/anylab_frontend.pid ]; then
    FRONTEND_PID=$(cat /tmp/anylab_frontend.pid)
    echo "🎨 Stopping React frontend (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID 2>/dev/null
    rm /tmp/anylab_frontend.pid
fi

if [ -f /tmp/anylab_backend.pid ]; then
    BACKEND_PID=$(cat /tmp/anylab_backend.pid)
    echo "🔧 Stopping Django backend (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null
    rm /tmp/anylab_backend.pid
fi

# Stop Docker services
echo "📦 Stopping Docker services..."
cd /Volumes/Orico/OnLab0812
docker-compose -f django-pgvector-pdf/docker-compose.yml down

# Stop cloudflared tunnel
echo "🌐 Stopping Cloudflare tunnel..."
pkill cloudflared

echo "✅ AnyLab services stopped!"
