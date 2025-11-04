#!/bin/bash
# Cleanup duplicate processes
# Run this AFTER confirming new configuration works

set -euo pipefail

echo "🧹 Cleaning up duplicate processes..."
echo "===================================="
echo ""
echo "⚠️  WARNING: This will stop duplicate Django and Celery processes"
echo "   Make sure you've tested the new configuration first!"
echo ""
read -p "Continue with cleanup? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cleanup cancelled"
    exit 0
fi

# Kill duplicate Django processes (keep first one)
echo ""
echo "🔍 Checking Django processes..."
DJANGO_PIDS=$(ps aux | grep "manage.py runserver" | grep -v grep | awk '{print $2}')
DJANGO_COUNT=$(echo "$DJANGO_PIDS" | wc -l | tr -d ' ')

if [ "$DJANGO_COUNT" -gt 1 ]; then
    echo "⚠️  Found $DJANGO_COUNT Django processes"
    echo "$DJANGO_PIDS" | tail -n +2 | while read pid; do
        echo "   Killing duplicate Django process (PID: $pid)..."
        kill $pid 2>/dev/null || true
    done
    sleep 2
    echo "✅ Duplicate Django processes killed"
elif [ "$DJANGO_COUNT" -eq 1 ]; then
    echo "✅ Only one Django process running (good)"
else
    echo "ℹ️  No Django processes running"
fi

# Kill all Celery workers (will restart with single instance)
echo ""
echo "🔍 Checking Celery workers..."
CELERY_COUNT=$(ps aux | grep -c "celery.*worker.*anylab" | grep -v grep || echo "0")

if [ "$CELERY_COUNT" -gt 0 ]; then
    echo "⚠️  Found Celery worker processes"
    echo "   Stopping all Celery workers..."
    pkill -f "celery.*worker.*anylab" 2>/dev/null || true
    sleep 3
    echo "✅ Celery workers stopped"
else
    echo "ℹ️  No Celery workers running"
fi

# Remove old Docker containers
echo ""
echo "🔍 Checking for old Docker containers..."
OLD_CONTAINERS=$(docker ps -a --filter "name=anylab_db" --filter "name=anylab_redis" --format "{{.Names}}" 2>/dev/null || true)

if [ ! -z "$OLD_CONTAINERS" ]; then
    echo "⚠️  Found old containers:"
    echo "$OLD_CONTAINERS" | while read container; do
        echo "   Removing: $container"
        docker rm -f "$container" 2>/dev/null || true
    done
    echo "✅ Old containers removed"
else
    echo "✅ No old containers found"
fi

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📊 Current processes:"
DJANGO_COUNT=$(ps aux | grep -c "manage.py runserver" | grep -v grep || echo "0")
CELERY_COUNT=$(ps aux | grep -c "celery.*worker.*anylab" | grep -v grep || echo "0")
echo "   Django processes: $DJANGO_COUNT (expected: 0 or 1)"
echo "   Celery workers: $CELERY_COUNT (expected: 0 or 1 main + children)"
echo ""
echo "💡 To restart services:"
echo "   ./start-all.sh"



