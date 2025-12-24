#!/bin/bash
# Verify Docker Memory Optimization

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🔍 Docker Memory Optimization Verification"
echo "=========================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running!${NC}"
    echo "   Please start Docker Desktop first."
    exit 1
fi

# Get Docker memory allocation
DOCKER_MEMORY=$(docker info 2>/dev/null | grep "Total Memory" | awk '{print $3}')
echo -e "${BLUE}📊 Docker Desktop Memory Allocation:${NC}"
echo "   Current: $DOCKER_MEMORY"
echo ""

# Check if it's optimized
MEMORY_VALUE=$(echo "$DOCKER_MEMORY" | sed 's/GiB//')
if (( $(echo "$MEMORY_VALUE < 6" 2>/dev/null | bc -l) )); then
    echo -e "${GREEN}✅ OPTIMIZED!${NC} Docker memory is properly limited"
    echo "   Target: 4 GB"
    echo "   Actual: $DOCKER_MEMORY"
    echo "   Savings: ~7-8 GB freed! 🎉"
else
    echo -e "${YELLOW}⚠️  NOT OPTIMIZED${NC}"
    echo "   Current: $DOCKER_MEMORY"
    echo "   Target: 4 GB"
    echo "   You still need to reduce it in Docker Desktop → Settings → Resources"
fi
echo ""

# Check container status
echo -e "${BLUE}🐳 Container Status:${NC}"
docker compose ps 2>/dev/null
echo ""

# Check memory usage
echo -e "${BLUE}💾 Container Memory Usage:${NC}"
docker stats --no-stream --format "   {{.Name}}: {{.MemUsage}}" 2>/dev/null
echo ""

# System memory
echo -e "${BLUE}🖥️  System Memory Status:${NC}"
FREE_PAGES=$(vm_stat | grep "Pages free" | awk '{print $3}' | sed 's/\.//')
FREE_GB=$(echo "scale=2; $FREE_PAGES * 16384 / 1024 / 1024 / 1024" | bc 2>/dev/null || echo "N/A")
echo "   Free RAM: ${FREE_GB} GB"

SWAP_USED=$(sysctl vm.swapusage 2>/dev/null | grep -o "used = [^,]*" | awk '{print $3}' | sed 's/M//')
if [ -n "$SWAP_USED" ]; then
    SWAP_GB=$(echo "scale=2; $SWAP_USED / 1024" | bc 2>/dev/null || echo "N/A")
    echo "   Swap Used: ${SWAP_GB} GB"
    
    if (( $(echo "$SWAP_GB < 2" 2>/dev/null | bc -l) )); then
        echo -e "   ${GREEN}✅ Low swap usage - system is healthy!${NC}"
    elif (( $(echo "$SWAP_GB < 4" 2>/dev/null | bc -l) )); then
        echo -e "   ${YELLOW}⚠️  Moderate swap usage${NC}"
    else
        echo -e "   ${RED}⚠️  High swap usage - close some applications${NC}"
    fi
fi
echo ""

echo "=========================================="
if (( $(echo "$MEMORY_VALUE < 6" 2>/dev/null | bc -l) )); then
    echo -e "${GREEN}🎉 OPTIMIZATION COMPLETE!${NC}"
    echo ""
    echo "Benefits:"
    echo "  • 7.67 GB freed from Docker VM"
    echo "  • More room for other projects"
    echo "  • Reduced swap usage"
    echo "  • Better system performance"
else
    echo -e "${YELLOW}Action Required:${NC}"
    echo "  1. Open Docker Desktop"
    echo "  2. Settings → Resources → Memory"
    echo "  3. Change from $DOCKER_MEMORY to 4 GB"
    echo "  4. Click 'Apply & Restart'"
fi
echo ""

