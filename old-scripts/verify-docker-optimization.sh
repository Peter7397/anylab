#!/bin/bash
# Docker Optimization Verification Script
# This script checks if the optimization was successful

set -euo pipefail

echo "🔍 Docker Optimization Verification"
echo "===================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0

# Function to check and print result
check() {
    local test_name="$1"
    local condition="$2"
    
    if eval "$condition"; then
        echo -e "${GREEN}✅ PASS${NC}: $test_name"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC}: $test_name"
        ((FAILED++))
    fi
}

echo "1️⃣  Checking Docker Desktop Settings..."
echo "----------------------------------------"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running!${NC}"
    exit 1
fi

# Get Docker memory allocation
DOCKER_MEMORY=$(docker info 2>/dev/null | grep "Total Memory" | awk '{print $3}')
echo "   Docker Desktop Memory: $DOCKER_MEMORY"

# Check if memory is reduced (should be around 4 GB)
if [ -n "$DOCKER_MEMORY" ]; then
    MEMORY_VALUE=$(echo "$DOCKER_MEMORY" | sed 's/GiB//')
    if (( $(echo "$MEMORY_VALUE < 6" | bc -l) )); then
        echo -e "${GREEN}✅ Docker memory optimized${NC} (< 6 GB)"
        ((PASSED++))
    else
        echo -e "${YELLOW}⚠️  Docker memory not optimized${NC} ($DOCKER_MEMORY - should be ~4 GB)"
        echo "   Please reduce in Docker Desktop → Settings → Resources"
        ((FAILED++))
    fi
fi

echo ""
echo "2️⃣  Checking Container Status..."
echo "----------------------------------------"

# Check if containers are running
check "PostgreSQL container running" "docker ps | grep -q anylab_postgres"
check "Redis container running" "docker ps | grep -q anylab_redis"
check "Neo4j container running" "docker ps | grep -q anylab_neo4j"

echo ""
echo "3️⃣  Checking Container Health..."
echo "----------------------------------------"

# Check container health status
POSTGRES_HEALTH=$(docker inspect --format='{{.State.Health.Status}}' anylab_postgres 2>/dev/null || echo "no-health")
REDIS_HEALTH=$(docker inspect --format='{{.State.Health.Status}}' anylab_redis 2>/dev/null || echo "no-health")
NEO4J_HEALTH=$(docker inspect --format='{{.State.Health.Status}}' anylab_neo4j 2>/dev/null || echo "no-health")

check "PostgreSQL healthy" "[[ '$POSTGRES_HEALTH' == 'healthy' ]]"
check "Redis healthy" "[[ '$REDIS_HEALTH' == 'healthy' ]]"
check "Neo4j healthy" "[[ '$NEO4J_HEALTH' == 'healthy' ]]"

echo ""
echo "4️⃣  Checking Memory Limits..."
echo "----------------------------------------"

# Check if memory limits are set
POSTGRES_LIMIT=$(docker inspect --format='{{.HostConfig.Memory}}' anylab_postgres 2>/dev/null)
REDIS_LIMIT=$(docker inspect --format='{{.HostConfig.Memory}}' anylab_redis 2>/dev/null)
NEO4J_LIMIT=$(docker inspect --format='{{.HostConfig.Memory}}' anylab_neo4j 2>/dev/null)

if [ "$POSTGRES_LIMIT" -gt 0 ] 2>/dev/null; then
    POSTGRES_MB=$((POSTGRES_LIMIT / 1024 / 1024))
    echo -e "${GREEN}✅ PostgreSQL limit set:${NC} ${POSTGRES_MB} MB"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️  PostgreSQL limit not set${NC}"
    ((FAILED++))
fi

if [ "$REDIS_LIMIT" -gt 0 ] 2>/dev/null; then
    REDIS_MB=$((REDIS_LIMIT / 1024 / 1024))
    echo -e "${GREEN}✅ Redis limit set:${NC} ${REDIS_MB} MB"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️  Redis limit not set${NC}"
    ((FAILED++))
fi

if [ "$NEO4J_LIMIT" -gt 0 ] 2>/dev/null; then
    NEO4J_GB=$((NEO4J_LIMIT / 1024 / 1024 / 1024))
    echo -e "${GREEN}✅ Neo4j limit set:${NC} ${NEO4J_GB} GB"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️  Neo4j limit not set${NC}"
    ((FAILED++))
fi

echo ""
echo "5️⃣  Checking Actual Memory Usage..."
echo "----------------------------------------"

# Get current memory usage
docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}" | grep anylab

echo ""
echo "6️⃣  Testing Database Connections..."
echo "----------------------------------------"

# Test PostgreSQL
if docker exec anylab_postgres psql -U postgres -d anylab -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PostgreSQL accepting connections${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ PostgreSQL connection failed${NC}"
    ((FAILED++))
fi

# Test Redis
if docker exec anylab_redis redis-cli ping | grep -q PONG; then
    echo -e "${GREEN}✅ Redis responding to PING${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ Redis connection failed${NC}"
    ((FAILED++))
fi

# Test Neo4j
if curl -s -o /dev/null -w "%{http_code}" http://localhost:7474 | grep -q "200"; then
    echo -e "${GREEN}✅ Neo4j browser accessible${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️  Neo4j browser not accessible${NC}"
    echo "   (This is OK if Neo4j is still starting up)"
    ((FAILED++))
fi

echo ""
echo "7️⃣  Checking System Memory..."
echo "----------------------------------------"

# macOS memory check
if command -v vm_stat &> /dev/null; then
    FREE_PAGES=$(vm_stat | grep "Pages free" | awk '{print $3}' | sed 's/\.//')
    FREE_GB=$(echo "scale=2; $FREE_PAGES * 16384 / 1024 / 1024 / 1024" | bc)
    echo "   Free RAM: ${FREE_GB} GB"
    
    if (( $(echo "$FREE_GB > 2" | bc -l) )); then
        echo -e "${GREEN}✅ Sufficient free RAM${NC} (> 2 GB)"
        ((PASSED++))
    else
        echo -e "${YELLOW}⚠️  Low free RAM${NC} (< 2 GB)"
        ((FAILED++))
    fi
fi

# Check swap usage
SWAP_USAGE=$(sysctl vm.swapusage | grep -oE "used = [0-9.]+[MG]" | awk '{print $3}')
echo "   Swap Usage: ${SWAP_USAGE}"

if [[ "$SWAP_USAGE" == *"M"* ]] || (( $(echo "${SWAP_USAGE//G/} < 2" 2>/dev/null | bc -l) )); then
    echo -e "${GREEN}✅ Low swap usage${NC} (< 2 GB)"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️  High swap usage${NC} (> 2 GB)"
    echo "   Consider closing other applications"
    ((FAILED++))
fi

echo ""
echo "8️⃣  Checking Configuration Files..."
echo "----------------------------------------"

# Check if optimized config is in place
if grep -q "memory:" docker-compose.yml 2>/dev/null; then
    echo -e "${GREEN}✅ Memory limits configured in docker-compose.yml${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️  Memory limits not found in docker-compose.yml${NC}"
    echo "   You may need to apply the optimized configuration"
    ((FAILED++))
fi

# Check if backup exists
if ls docker-compose.yml.backup-* > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backup file exists${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️  No backup file found${NC}"
    ((FAILED++))
fi

echo ""
echo "========================================"
echo "📊 SUMMARY"
echo "========================================"
echo -e "Passed: ${GREEN}${PASSED}${NC}"
echo -e "Failed: ${RED}${FAILED}${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL CHECKS PASSED!${NC}"
    echo "Docker optimization is working correctly."
    echo ""
    echo "Next steps:"
    echo "  1. Monitor memory usage: docker stats"
    echo "  2. Check system performance over next 24 hours"
    echo "  3. Verify backend application works correctly"
    exit 0
elif [ $FAILED -lt 3 ]; then
    echo -e "${YELLOW}⚠️  OPTIMIZATION PARTIALLY COMPLETE${NC}"
    echo "Some checks failed but system is mostly operational."
    echo ""
    echo "Review the failed checks above and address if needed."
    exit 1
else
    echo -e "${RED}❌ OPTIMIZATION NOT COMPLETE${NC}"
    echo "Multiple checks failed. Please review the output above."
    echo ""
    echo "Consider:"
    echo "  1. Check Docker Desktop is running"
    echo "  2. Verify docker-compose.yml configuration"
    echo "  3. Check container logs: docker-compose logs"
    echo "  4. Review DOCKER_OPTIMIZATION_GUIDE.md"
    exit 2
fi

