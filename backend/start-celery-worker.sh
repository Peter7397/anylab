#!/usr/bin/env bash
set -euo pipefail

# Check if Celery worker is already running
if pgrep -f "celery.*worker.*anylab" > /dev/null; then
    echo "⚠️  Celery worker is already running!"
    CELERY_PIDS=$(pgrep -f "celery.*worker.*anylab" | tr '\n' ' ')
    echo "   Existing PIDs: $CELERY_PIDS"
    read -p "Kill existing workers and restart? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pkill -f "celery.*worker.*anylab"
        sleep 2
        echo "✅ Old workers stopped"
    else
        echo "❌ Exiting - worker already running"
        exit 1
    fi
fi

# Load environment if present
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs -0 bash -c 'printf "%s\n" "$@"' -- 2>/dev/null || true)
fi

# Local Development Configuration
# =========================================================
# These defaults work for local development when connecting to Docker services:
# - Docker Redis accessible via localhost:6379
# - Docker PostgreSQL accessible via localhost:5433
# For production Docker deployment, these are set via environment variables
# =========================================================
export CELERY_BROKER_URL=${CELERY_BROKER_URL:-redis://localhost:6379/0}
export CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND:-redis://localhost:6379/0}
export DB_PORT=${DB_PORT:-5433}
export DB_HOST=${DB_HOST:-127.0.0.1}

# Prefer async processing in production
export ENABLE_ASYNC_FILE_PROCESSING=${ENABLE_ASYNC_FILE_PROCESSING:-true}

# Start single worker instance with controlled concurrency
# This ensures only one worker process (with child workers)
# Use the venv python to avoid stale shebang in celery entrypoint
exec ./venv/bin/python -m celery -A anylab worker -l info -Q ai_queue,default --concurrency=4


