# AnyLab Shutdown & Restart Playbook

This checklist helps you pause the entire AnyLab stack for a planned outage (e.g., a two-day shutdown) and brings it back exactly as it is today.

> **TL;DR:** snapshot current state, stop the containers cleanly, capture any secrets/backups you need, and after the outage bring the stack back up with the documented `docker compose` commands. Verify the services with the provided health checks.

---

## 1. Before Shutting Down

1. **Confirm current state**
   - `docker compose ps`
   - `docker compose logs --tail=50`
2. **Stop workloads cleanly**  
   Choose ONE of these options:
   - Preserve container state: `docker compose stop`
   - Fresh restart next time: `docker compose down`
3. **Back up critical data (optional but recommended)**
   - PostgreSQL volume: `pgdata` (see Automation Script section)
   - User uploads/config: e.g., `backend/media`, `backend/locale`, `frontend/src/locales`, `.env` files, any custom certificates
   - If you rely on Neo4j or other external services, back up their data per vendor guidance.
4. **Record the current configuration**
   - `docker compose config > backups/docker-compose-$(date +%F).yaml`
   - `git status -sb` (note any uncommitted files)
5. **Shutdown host**
   - Once containers are stopped and backups captured, shut down the machine normally.

---

## 2. Coming Back Online

1. **Power on and verify Docker**
   - Ensure Docker Desktop / docker daemon is running.
   - `docker info` (sanity check)
2. **Start the stack**
   - If you previously ran `docker compose down`:  
     `docker compose up -d`
   - If you previously ran `docker compose stop`:  
     `docker compose start`
   - Optional: `docker compose pull` (only if you expect newer images and want to refresh them)
3. **Run migrations (only if code changed during downtime)**
   - `docker compose exec django python manage.py migrate`
4. **Verify health**
   - `docker compose ps`
   - `docker compose logs -f django react redis` (Ctrl+C when satisfied)
   - `curl http://localhost:8001/api/health/`
   - Log in to the UI and load dashboard/chat to confirm per-user history behaves as expected.
   - Check Celery and Qwen containers if used: `docker compose logs -f celery qwen`
5. **Optional validations**
   - Run a sample chat prompt and verify it shows up in your personal chat history.
   - Visit admin-only analytics endpoints if you are staff:
     - `/api/ai/dashboard/stats/global/`
     - `/api/ai/analytics/performance/global/`

---

## 3. Automation Helpers

Use the scripts in `scripts/` (added in this change) to streamline common tasks:

| Script | Purpose |
| ------ | ------- |
| `scripts/prepare_shutdown.sh` | Runs through the pre-shutdown checks and reminders. |
| `scripts/restore_after_shutdown.sh` | Brings the stack back up and runs basic verification after downtime. |

> Execute scripts with `bash scripts/<script>.sh`. They echo the commands so you can see exactly what will run. Feel free to customise for your environment.

---

## 4. What to Double-Check

- `.env` files, secret keys, OAuth credentials, and any API tokens are stored safely (not just in the container environment).
- Neo4j, Redis snapshots, or other auxiliary services are covered if they run outside Docker.
- Backups are stored on external media if you require worst-case disaster recovery.
- Monitoring/alerting is silenced or updated for the planned outage window.

With this playbook, your two-day shutdown should be uneventful and you’ll be able to resume operations exactly where you left off. Update this doc as your infrastructure evolves.

