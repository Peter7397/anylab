# Port Conflict Resolution - AnyLab vs 7English

## Port Conflicts Identified

### ✅ Resolved: Port 8000 → 8001
- **7English**: Uses port 8000 (Backend API)
- **AnyLab**: Changed from port 8000 → **8001** (Django Backend)
- **Status**: ✅ RESOLVED

### ✅ No Conflict: Port 5432
- **7English**: Uses port 5432 (PostgreSQL)
- **AnyLab**: Uses port **5433** (PostgreSQL via Docker)
- **Status**: ✅ NO CONFLICT

### ✅ Shared Service: Port 11434 (Ollama)
- **7English**: Uses port 11434 (Ollama)
- **AnyLab**: Uses port 11434 (Ollama)
- **Status**: ✅ SHARED - Both projects use the same Ollama instance
- **Note**: Ollama can handle multiple clients simultaneously, so sharing is safe

## Changes Made

### 1. Backend Port Changed: 8000 → 8001

**File**: `frontend/src/services/api.ts`
- Changed default port from `8000` to `8001`
- Frontend will now connect to `http://localhost:8001/api`

**To start backend on new port:**
```bash
cd backend
source venv/bin/activate
python manage.py runserver 0.0.0.0:8001
```

**Or use the startup script:**
```bash
./start-hybrid.sh
```
(Update the script to use port 8001)

### 2. Startup Scripts Need Update

The following scripts may need to be updated to use port 8001:
- `start-hybrid.sh`
- `start-all.sh`
- Any other scripts that start the Django server

## Updated Port Summary

| Service | AnyLab Port | 7English Port | Status |
|---------|-------------|---------------|--------|
| Backend API | **8001** | 8000 | ✅ No conflict |
| PostgreSQL | 5433 | 5432 | ✅ No conflict |
| Ollama | 11434 | 11434 | ✅ Shared (OK) |
| Frontend | 3000 | ? | Check if 7English uses 3000 |
| Redis | 6379 | ? | Check if 7English uses 6379 |
| Neo4j HTTP | 7474 | ? | Check if 7English uses 7474 |
| Neo4j Bolt | 7687 | ? | Check if 7English uses 7687 |

## Ollama Sharing Details

Both projects can safely use the same Ollama instance because:
1. Ollama is designed to handle multiple concurrent requests
2. Each project uses different models:
   - AnyLab: `llama3:8b`, `bge-m3:latest`
   - 7English: (check their models)
3. Ollama manages model loading/unloading automatically
4. Requests are queued and processed independently

**Potential considerations:**
- If both projects make heavy requests simultaneously, there may be resource contention
- Monitor Ollama performance if you notice slowdowns
- Consider using different Ollama instances if resource contention becomes an issue

## Testing

After making changes, test:
1. Start AnyLab backend on port 8001
2. Start AnyLab frontend on port 3000
3. Verify frontend can connect to backend at `http://localhost:8001/api`
4. Verify 7English still works on port 8000
5. Test both projects using Ollama simultaneously

## Next Steps

1. ✅ Update frontend API URL to use port 8001
2. ⏳ Update startup scripts to use port 8001
3. ⏳ Test both projects running simultaneously
4. ⏳ Document any other port conflicts discovered

