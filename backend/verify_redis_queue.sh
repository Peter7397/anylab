#!/bin/bash
# Verification script for Redis job queue implementation

echo "=========================================="
echo "Redis Job Queue Verification Script"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running in Docker
if [ -f /.dockerenv ]; then
    echo -e "${YELLOW}Running inside Docker container${NC}"
    DOCKER_MODE=true
else
    echo -e "${YELLOW}Running on host${NC}"
    DOCKER_MODE=false
fi

echo ""
echo "1. Checking Redis connection..."
if python manage.py shell -c "
from django.core.cache import cache
try:
    cache.set('test_key', 'test_value', 10)
    result = cache.get('test_key')
    if result == 'test_value':
        print('SUCCESS: Redis connection working')
        exit(0)
    else:
        print('ERROR: Redis cache test failed')
        exit(1)
except Exception as e:
    print(f'ERROR: Redis connection failed: {e}')
    exit(1)
"; then
    echo -e "${GREEN}✓ Redis connection OK${NC}"
else
    echo -e "${RED}✗ Redis connection FAILED${NC}"
    exit 1
fi

echo ""
echo "2. Checking Redis job queue manager..."
if python manage.py shell -c "
from ai_assistant.service_classes.redis_job_queue_manager import redis_job_queue_manager
try:
    if redis_job_queue_manager.is_available():
        print('SUCCESS: Redis job queue manager available')
        exit(0)
    else:
        print('ERROR: Redis job queue manager not available')
        exit(1)
except Exception as e:
    print(f'ERROR: Redis job queue manager error: {e}')
    exit(1)
"; then
    echo -e "${GREEN}✓ Redis job queue manager OK${NC}"
else
    echo -e "${RED}✗ Redis job queue manager FAILED${NC}"
    exit 1
fi

echo ""
echo "3. Running comprehensive tests..."
if python manage.py test_redis_job_queue --full; then
    echo -e "${GREEN}✓ All tests passed${NC}"
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi

echo ""
echo "4. Checking Celery Beat schedule..."
if python manage.py shell -c "
from anylab.celery import app
schedule = app.conf.beat_schedule
if 'persist-redis-jobs-to-database' in schedule:
    print('SUCCESS: Persistence task scheduled')
    print(f\"Schedule: {schedule['persist-redis-jobs-to-database']['schedule']} seconds\")
    exit(0)
else:
    print('ERROR: Persistence task not found in schedule')
    exit(1)
"; then
    echo -e "${GREEN}✓ Celery Beat schedule OK${NC}"
else
    echo -e "${RED}✗ Celery Beat schedule FAILED${NC}"
    exit 1
fi

echo ""
echo "=========================================="
echo -e "${GREEN}All verifications passed!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Restart Django backend: docker-compose restart backend"
echo "2. Restart Celery worker: docker-compose restart celery-worker"
echo "3. Restart Celery Beat: docker-compose restart celery-beat"
echo "4. Monitor logs: docker-compose logs -f celery-worker celery-beat"
echo ""

