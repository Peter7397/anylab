#!/bin/bash
# Test script for optimization monitoring
# Usage: ./test_optimizations.sh

echo "=========================================="
echo "Optimization Testing & Monitoring"
echo "=========================================="
echo ""

echo "1. Checking Celery Worker Configuration..."
echo "-------------------------------------------"
docker compose logs --tail=30 celery-worker 2>&1 | grep -i "concurrency\|prefork\|pool" | head -5
echo ""

echo "2. Current Resource Usage..."
echo "-------------------------------------------"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" | grep -E "NAME|celery|backend|ollama|postgres|redis"
echo ""

echo "3. Celery Worker Status..."
echo "-------------------------------------------"
docker compose exec celery-worker celery -A anylab inspect active 2>/dev/null | head -20
echo ""

echo "4. Recent Errors/Warnings..."
echo "-------------------------------------------"
docker compose logs --tail=100 celery-worker 2>&1 | grep -i "error\|warning" | tail -5
docker compose logs --tail=100 celery-worker-ocr 2>&1 | grep -i "error\|warning" | tail -5
echo ""

echo "5. Service Health Status..."
echo "-------------------------------------------"
docker compose ps --format "table {{.Name}}\t{{.Status}}" | grep -E "NAME|celery|backend|ollama"
echo ""

echo "=========================================="
echo "Testing Complete"
echo "=========================================="
echo ""
echo "To monitor in real-time, run:"
echo "  docker stats"
echo ""
echo "To watch Celery logs:"
echo "  docker compose logs -f celery-worker"
echo ""

