#!/bin/bash
# AnyLab Complete Startup Script
# Starts Docker services and production backend with Gunicorn

set -euo pipefail

echo "🚀 Starting AnyLab Production System"
echo "======================================"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Start Docker services
echo "📦 Step 1: Starting Docker services..."
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running!${NC}"
    echo "   Please start Docker Desktop first."
    exit 1
fi

docker compose up -d
echo -e "${GREEN}✅ Docker services started${NC}"
echo ""

# Step 2: Wait for services to be ready
echo "⏳ Step 2: Waiting for services to be ready..."
sleep 10

# Check if services are healthy
if docker compose ps | grep -q "unhealthy"; then
    echo -e "${YELLOW}⚠️  Warning: Some services are not healthy yet${NC}"
    echo "   They may still be starting up..."
else
    echo -e "${GREEN}✅ All services healthy${NC}"
fi
echo ""

# Step 3: Start/Restart backend via launchd
echo "🔧 Step 3: Starting backend (Gunicorn)..."

# Check if backend is already running
if launchctl list | grep -q "com.anylab.backend"; then
    echo "   Backend service already loaded, restarting..."
    launchctl kickstart -k gui/$(id -u)/com.anylab.backend
else
    echo "   Loading backend service..."
    launchctl load ~/Library/LaunchAgents/com.anylab.backend.plist
fi

sleep 3

# Verify backend is running
if lsof -i :8001 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend started on port 8001${NC}"
else
    echo -e "${RED}❌ Backend failed to start!${NC}"
    echo "   Check logs: tail -f logs/gunicorn-error.log"
    exit 1
fi
echo ""

# Step 4: Check health
echo "🏥 Step 4: Health check..."
sleep 2

if curl -s http://localhost:8001/api/health/ | grep -q "healthy"; then
    echo -e "${GREEN}✅ Backend is healthy${NC}"
else
    echo -e "${YELLOW}⚠️  Backend health check failed${NC}"
    echo "   Backend may still be initializing..."
fi
echo ""

echo "======================================"
echo -e "${GREEN}✅ AnyLab Started Successfully!${NC}"
echo "======================================"
echo ""
echo "📊 Status:"
echo "   • Docker Containers: $(docker compose ps | grep -c 'Up')/3 running"
echo "   • Backend: http://localhost:8001"
echo "   • Frontend: https://anylab.dpdns.org"
echo ""
echo "📝 Management:"
echo "   • Stop:    ./anylab-stop.sh"
echo "   • Status:  ./anylab-status.sh"
echo "   • Restart: ./anylab-restart.sh"
echo "   • Logs:    ./anylab-logs.sh"
echo ""

