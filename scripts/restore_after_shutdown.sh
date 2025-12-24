#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "==> AnyLab Post-Shutdown Restore"
echo

echo "[1/7] Verifying docker daemon availability..."
docker info >/dev/null
echo "Docker is available."
echo

echo "[2/7] Starting containers..."
if docker compose ps --services --filter "status=exited" | grep -q .; then
  docker compose start
else
  docker compose up -d
fi
echo "Containers initiated."
echo

echo "[3/7] Waiting 10 seconds for services to initialise..."
sleep 10

echo "[4/7] Current container status:"
docker compose ps
echo

echo "[5/7] Tail end of service logs (ctrl+c to stop)"
docker compose logs --tail=20 || true
echo

echo "[6/7] Running health check:"
curl -fsS http://localhost:8001/api/health/ && echo -e "\nHealth endpoint reachable."
echo

echo "[7/7] Optional migrations (run if code changed during downtime)"
read -rp "Execute 'docker compose exec django python manage.py migrate'? [y/N] " migrate_answer
answer_lower="$(printf '%s' "$migrate_answer" | tr '[:upper:]' '[:lower:]')"
if [[ "$answer_lower" == "y" ]]; then
  docker compose exec django python manage.py migrate
else
  echo "Skipping migrations."
fi

cat <<'EONOTE'
Manual verification checklist:
- Log in to the web UI and confirm dashboard loads.
- Trigger a chat prompt and confirm it appears in your personal history.
- Staff: check /api/ai/dashboard/stats/global/ and /api/ai/analytics/performance/global/
- Review Celery/Qwen logs if those services are in use.
EONOTE

echo
echo "Restore checklist complete."

