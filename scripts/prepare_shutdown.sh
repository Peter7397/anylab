#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "==> AnyLab Shutdown Preparation"
echo

echo "[1/6] Checking docker compose status..."
docker compose ps
echo

echo "[2/6] Capturing recent logs (last 50 lines)..."
docker compose logs --tail=50 || true
echo

BACKUPS_DIR="$ROOT_DIR/backups"
mkdir -p "$BACKUPS_DIR"
STAMP="$(date +%F_%H%M%S)"

echo "[3/6] Saving docker compose config snapshot to backups/docker-compose-$STAMP.yaml"
docker compose config > "$BACKUPS_DIR/docker-compose-$STAMP.yaml"
echo "Saved $(realpath "$BACKUPS_DIR/docker-compose-$STAMP.yaml")"
echo

echo "[4/6] Showing git status (for your reference)"
git status -sb || true
echo

echo "[5/6] Reminder: back up critical data"
cat <<'EONOTE'
- PostgreSQL volume (pgdata): consider pg_dump or filesystem snapshot
- Uploaded documents / media: backend/media, backend/locale, frontend/src/locales
- Environment files (.env, secrets, certificates)
- Neo4j / external services data (if applicable)
EONOTE
echo

echo "[6/6] Stop containers cleanly"
read -rp "Run 'docker compose stop' now? [y/N] " answer
answer_lower="$(printf '%s' "$answer" | tr '[:upper:]' '[:lower:]')"
if [[ "$answer_lower" == "y" ]]; then
  docker compose stop
  echo "Containers stopped. Ready for host shutdown."
else
  echo "Skipping automatic stop. Remember to stop containers before powering off."
fi

echo
echo "Shutdown checklist complete."

