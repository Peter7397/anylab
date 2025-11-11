#!/bin/bash
# AnyLab Status Script
# Shows current status of all services

set -euo pipefail

echo "📊 AnyLab System Status"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Docker Status
echo "🐳 Docker Services:"
if docker info > /dev/null 2>&1; then
    docker compose ps 2>/dev/null || echo "   No compose services found"
    echo ""
    echo "   Memory Usage:"
    docker stats --no-stream --format "   {{.Name}}: {{.MemUsage}}" 2>/dev/null || echo "   Unable to get stats"
else
    echo -e "   ${RED}Docker is not running${NC}"
fi
echo ""

# Backend Status
echo "🔧 Backend (Gunicorn):"
if launchctl list | grep -q "com.anylab.backend"; then
    if lsof -i :8001 > /dev/null 2>&1; then
        echo -e "   ${GREEN}✅ Running on port 8001${NC}"
        
        # Get process info
        BACKEND_PID=$(lsof -ti :8001 | head -1)
        if [ -n "$BACKEND_PID" ]; then
            BACKEND_MEM=$(ps aux | awk -v pid="$BACKEND_PID" '$2==pid {print $4}')
            echo "   PID: $BACKEND_PID"
            echo "   Memory: ${BACKEND_MEM}%"
        fi
        
        # Health check
        if curl -s http://localhost:8001/api/health/ 2>/dev/null | grep -q "healthy"; then
            echo -e "   Health: ${GREEN}Healthy${NC}"
        else
            echo -e "   Health: ${YELLOW}Unknown${NC}"
        fi
    else
        echo -e "   ${YELLOW}⚠️  Loaded but not listening${NC}"
    fi
else
    echo -e "   ${RED}❌ Not running${NC}"
fi
echo ""

# Cloudflare Tunnel
echo "☁️  Cloudflare Tunnel:"
if pgrep -f "cloudflared.*anylab" > /dev/null 2>&1; then
    echo -e "   ${GREEN}✅ Running${NC}"
else
    echo -e "   ${RED}❌ Not running${NC}"
fi
echo ""

# URLs
echo "🌐 Access URLs:"
echo "   • Local Backend:  http://localhost:8001"
echo "   • Local Frontend: http://localhost:3000"
echo "   • Public:         https://anylab.dpdns.org"
echo "   • Neo4j Browser:  http://localhost:7474"
echo ""

# System Resources
echo "💾 System Resources:"
FREE_RAM=$(vm_stat | grep "Pages free" | awk '{print $3}' | sed 's/\.//')
FREE_GB=$(echo "scale=2; $FREE_RAM * 16384 / 1024 / 1024 / 1024" | bc 2>/dev/null || echo "N/A")
echo "   Free RAM: ${FREE_GB} GB"

SWAP_INFO=$(sysctl vm.swapusage 2>/dev/null | grep -o "used = [^,]*" || echo "N/A")
echo "   Swap: ${SWAP_INFO}"
echo ""

echo "======================================"
echo "💡 Management Commands:"
echo "   ./anylab-start.sh   - Start all services"
echo "   ./anylab-stop.sh    - Stop all services"
echo "   ./anylab-restart.sh - Restart all services"
echo "   ./anylab-logs.sh    - View logs"
echo ""

