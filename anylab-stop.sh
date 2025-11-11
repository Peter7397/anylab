#!/bin/bash
# AnyLab Complete Shutdown Script
# Stops backend and Docker services

set -euo pipefail

echo "🛑 Stopping AnyLab System"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Step 1: Stop backend
echo "🔧 Step 1: Stopping backend..."
if launchctl list | grep -q "com.anylab.backend"; then
    launchctl unload ~/Library/LaunchAgents/com.anylab.backend.plist 2>/dev/null || true
    echo -e "${GREEN}✅ Backend stopped${NC}"
else
    echo -e "${YELLOW}   Backend was not running${NC}"
fi
echo ""

# Step 2: Stop Docker services
echo "📦 Step 2: Stopping Docker services..."
if docker info > /dev/null 2>&1; then
    docker compose down
    echo -e "${GREEN}✅ Docker services stopped${NC}"
else
    echo -e "${YELLOW}   Docker is not running${NC}"
fi
echo ""

echo "======================================"
echo -e "${GREEN}✅ AnyLab Stopped${NC}"
echo "======================================"
echo ""

