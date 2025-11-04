#!/bin/bash
# Stop all hybrid system services

set -euo pipefail

echo "🛑 Stopping AnyLab Hybrid System..."
echo "=================================="
echo ""

# Stop frontend
echo "🎨 Stopping React frontend..."
if pgrep -f "react-scripts start" > /dev/null; then
    pkill -f "react-scripts start"
    sleep 2
    echo "✅ Frontend stopped"
else
    echo "ℹ️  Frontend not running"
fi

# Stop backend
echo ""
echo "🔧 Stopping Django backend..."
if pgrep -f "manage.py runserver" > /dev/null; then
    pkill -f "manage.py runserver"
    sleep 2
    echo "✅ Backend stopped"
else
    echo "ℹ️  Backend not running"
fi

# Stop Celery
echo ""
echo "⚙️  Stopping Celery worker..."
if pgrep -f "celery.*worker.*anylab" > /dev/null; then
    pkill -f "celery.*worker.*anylab"
    sleep 2
    echo "✅ Celery worker stopped"
else
    echo "ℹ️  Celery worker not running"
fi

# Clean up PID files
echo ""
echo "🧹 Cleaning up PID files..."
rm -f backend/.backend.pid frontend/.frontend.pid

# Docker services stay running (persistent)
echo ""
echo "ℹ️  Docker services (PostgreSQL, Redis, Neo4j) remain running"
echo "   To stop Docker services: docker-compose down"
echo "   To stop only Neo4j: docker-compose stop neo4j"

echo ""
echo "✅ All local services stopped"



