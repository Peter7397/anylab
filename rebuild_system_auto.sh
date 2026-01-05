#!/bin/bash
# Complete System Rebuild Script (Non-Interactive)
# Rebuilds all services from scratch for testing

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  COMPLETE SYSTEM REBUILD (AUTO)${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Stop all services
echo -e "${YELLOW}[1/10] Stopping all services...${NC}"
echo ""

# Stop Docker containers
if docker info > /dev/null 2>&1; then
    echo "   Stopping Docker containers..."
    docker compose down 2>/dev/null || true
    echo -e "   ${GREEN}✅ Docker containers stopped${NC}"
else
    echo -e "   ${YELLOW}⚠️  Docker not running, skipping${NC}"
fi

# Stop backend processes
echo "   Stopping backend processes..."
pkill -f "manage.py runserver" 2>/dev/null || true
pkill -f "gunicorn" 2>/dev/null || true
pkill -f "celery.*worker" 2>/dev/null || true
pkill -f "celery.*beat" 2>/dev/null || true
sleep 2
echo -e "   ${GREEN}✅ Backend processes stopped${NC}"
echo ""

# Step 2: Keep volumes (preserve data for testing)
echo -e "${YELLOW}[2/10] Preserving data volumes...${NC}"
echo -e "   ${GREEN}✅ Keeping volumes (data preserved)${NC}"
echo ""

# Step 3: Start Docker services
echo -e "${YELLOW}[3/10] Starting Docker services...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "   ${RED}❌ Docker is not running!${NC}"
    echo "   Please start Docker Desktop first."
    exit 1
fi

echo "   Starting PostgreSQL, Redis, Neo4j, Ollama..."
docker compose up -d postgres redis neo4j ollama
echo -e "   ${GREEN}✅ Docker services starting${NC}"
echo ""

# Step 4: Wait for services to be ready
echo -e "${YELLOW}[4/10] Waiting for services to be ready...${NC}"
echo "   Waiting 20 seconds for services to initialize..."
sleep 20

# Check service health
echo "   Checking service health..."
if docker compose ps | grep -q "unhealthy"; then
    echo -e "   ${YELLOW}⚠️  Some services may still be starting...${NC}"
else
    echo -e "   ${GREEN}✅ Services appear healthy${NC}"
fi
echo ""

# Step 5: Setup backend environment
echo -e "${YELLOW}[5/10] Setting up backend environment...${NC}"
cd backend

# Activate virtual environment
if [ ! -d "venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
echo -e "   ${GREEN}✅ Virtual environment activated${NC}"

# Install/update dependencies
echo "   Installing/updating Python dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo -e "   ${GREEN}✅ Dependencies installed${NC}"
echo ""

# Step 6: Run database migrations
echo -e "${YELLOW}[6/10] Running database migrations...${NC}"
echo "   Waiting for PostgreSQL to be ready..."

# Check PostgreSQL connection
for i in {1..30}; do
    if docker compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
        echo -e "   ${GREEN}✅ PostgreSQL is ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "   ${RED}❌ PostgreSQL not ready after 30 attempts${NC}"
        exit 1
    fi
    sleep 1
done

# Run migrations
echo "   Running migrations..."
python manage.py migrate --noinput
echo -e "   ${GREEN}✅ Migrations completed${NC}"
echo ""

# Step 7: Collect static files
echo -e "${YELLOW}[7/10] Collecting static files...${NC}"
python manage.py collectstatic --noinput --clear 2>/dev/null || true
echo -e "   ${GREEN}✅ Static files collected${NC}"
echo ""

# Step 8: Verify CLIP installation
echo -e "${YELLOW}[8/10] Verifying CLIP installation...${NC}"
if python -c "import clip; import torch; print('OK')" 2>/dev/null; then
    echo -e "   ${GREEN}✅ CLIP verified${NC}"
else
    echo -e "   ${YELLOW}⚠️  CLIP not found - installing...${NC}"
    pip install ftfy regex -q
    pip install git+https://github.com/openai/CLIP.git -q
    echo -e "   ${GREEN}✅ CLIP installed${NC}"
fi
echo ""

# Step 9: Start backend services
echo -e "${YELLOW}[9/10] Starting backend services...${NC}"

# Start Celery worker
echo "   Starting Celery worker..."
if [ -f "start-celery-worker.sh" ]; then
    bash start-celery-worker.sh > /dev/null 2>&1 &
else
    celery -A anylab worker --loglevel=info --logfile=logs/celery_worker.log > /dev/null 2>&1 &
fi
sleep 3
echo -e "   ${GREEN}✅ Celery worker started${NC}"

# Start Celery beat
echo "   Starting Celery beat..."
if [ -f "start-celery-beat.sh" ]; then
    bash start-celery-beat.sh > /dev/null 2>&1 &
else
    celery -A anylab beat --loglevel=info --logfile=logs/celery_beat.log > /dev/null 2>&1 &
fi
sleep 2
echo -e "   ${GREEN}✅ Celery beat started${NC}"

# Start Django server
echo "   Starting Django server..."
python manage.py runserver 0.0.0.0:8001 > ../logs/django.log 2>&1 &
BACKEND_PID=$!
sleep 5
echo -e "   ${GREEN}✅ Django server started (PID: $BACKEND_PID)${NC}"
echo ""

cd ..

# Step 10: Verify services
echo -e "${YELLOW}[10/10] Verifying services...${NC}"
echo "   Waiting 5 seconds for services to initialize..."
sleep 5

# Check backend health
echo "   Checking backend health..."
for i in {1..10}; do
    if curl -s http://localhost:8001/api/health/ > /dev/null 2>&1; then
        echo -e "   ${GREEN}✅ Backend is healthy${NC}"
        break
    fi
    if [ $i -eq 10 ]; then
        echo -e "   ${YELLOW}⚠️  Backend health check failed (may still be starting)${NC}"
    else
        sleep 2
    fi
done

# Check Docker services
echo "   Checking Docker services..."
docker compose ps --format "table {{.Name}}\t{{.Status}}"
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  REBUILD COMPLETE${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}✅ System rebuild completed!${NC}"
echo ""
echo "Service URLs:"
echo "  - Backend API: http://localhost:8001"
echo "  - Admin Panel: http://localhost:8001/admin"
echo "  - Frontend: http://localhost:3000 (start separately)"
echo ""
echo "Next steps:"
echo "  1. Test visual embeddings: cd backend && source venv/bin/activate && python test_complete_workflow.py"
echo "  2. Start frontend: cd frontend && npm start"
echo "  3. Check logs: tail -f backend/logs/django.log"
echo ""
echo "To stop services:"
echo "  docker compose down"
echo "  pkill -f 'manage.py runserver'"
echo "  pkill -f 'celery'"
echo ""

