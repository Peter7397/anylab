#!/usr/bin/env bash
set -euo pipefail

# Load environment if present
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs -0 bash -c 'printf "%s\n" "$@"' -- 2>/dev/null || true)
fi

# Default broker/backends if not provided
export CELERY_BROKER_URL=${CELERY_BROKER_URL:-redis://localhost:6379/0}
export CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND:-redis://localhost:6379/0}

# Prefer async processing in production
export ENABLE_ASYNC_FILE_PROCESSING=${ENABLE_ASYNC_FILE_PROCESSING:-true}

# Constrain queues to ai_queue and default
exec ./venv/bin/celery -A anylab worker -l info -Q ai_queue,default


