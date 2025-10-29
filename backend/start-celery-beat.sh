#!/usr/bin/env bash
set -euo pipefail

if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs -0 bash -c 'printf "%s\n" "$@"' -- 2>/dev/null || true)
fi

export CELERY_BROKER_URL=${CELERY_BROKER_URL:-redis://localhost:6379/0}
export CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND:-redis://localhost:6379/0}

exec ./venv/bin/celery -A anylab beat -l info


