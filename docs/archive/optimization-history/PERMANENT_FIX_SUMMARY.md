# Permanent Fix for AnyLab Connection Issues

## Problem
The frontend was experiencing infinite flashing and connection errors because:
1. Backend wasn't starting automatically
2. Frontend kept polling aggressively even when backend was down
3. No health check mechanism
4. No exponential backoff for retries

## Permanent Solution Implemented

### 1. Backend Health Check Service (`frontend/src/services/backendHealth.ts`)
- **Purpose**: Centralized health checking to prevent unnecessary API calls
- **Features**:
  - Checks backend health before making requests
  - Caches health status to avoid excessive requests
  - Automatic background health checks every 30 seconds
  - Tracks consecutive failures (marks as unhealthy after 2 failures)
  - 3-second timeout for health checks

### 2. Improved AuthContext (`frontend/src/context/AuthContext.tsx`)
- **Before**: Polled every 1 second regardless of backend status
- **After**:
  - Checks backend health before attempting API calls
  - **Stops polling completely** when backend is unhealthy
  - Uses exponential backoff (1s → 2s → 4s → ... → 30s max) when errors occur
  - Only checks every 30 seconds when backend is down (to detect recovery)
  - Automatically resumes normal polling when backend comes back

### 3. Smart Startup Script (`start-anylab.sh`)
- **Purpose**: Ensures backend is running before starting frontend
- **Features**:
  - Checks if backend is already running
  - Starts Docker services (PostgreSQL, Redis) if needed
  - Waits for backend to be healthy before starting frontend
  - Handles port conflicts automatically
  - Provides clear error messages
  - Logs to `/tmp/anylab_backend.log` and `/tmp/anylab_frontend.log`

### 4. API Client Integration
- Automatically marks backend as unhealthy on connection errors
- Prevents cascade of failed requests

## How It Works

### Normal Operation (Backend Healthy)
1. Frontend polls every 1 second for token changes
2. Health check passes immediately (cached)
3. API calls proceed normally

### Backend Down Scenario
1. First connection attempt fails
2. Backend marked as unhealthy after 2 failures
3. **Polling stops completely** (no more flashing)
4. Health check runs every 30 seconds in background
5. When backend comes back, health check detects it
6. Polling resumes automatically

### Error Recovery
- Uses exponential backoff: 1s → 2s → 4s → 8s → 16s → 30s (max)
- Automatically reduces to 1s when connection succeeds
- Prevents overwhelming a recovering backend

## Usage

### Start AnyLab (Recommended)
```bash
./start-anylab.sh
```

This script:
- ✅ Checks if backend is running
- ✅ Starts Docker services if needed
- ✅ Waits for backend to be healthy
- ✅ Starts frontend only after backend is ready
- ✅ Handles all edge cases

### Manual Start (Alternative)
```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
python manage.py runserver 0.0.0.0:8001

# Terminal 2: Frontend (after backend is ready)
cd frontend
npm start
```

## Benefits

1. **No More Flashing**: Frontend stops polling when backend is down
2. **Automatic Recovery**: Detects when backend comes back online
3. **Better UX**: Clear error messages instead of infinite retries
4. **Resource Efficient**: Reduces unnecessary network requests
5. **Reliable Startup**: Ensures backend is ready before frontend starts

## Monitoring

### Check Backend Status
```bash
curl http://localhost:8001/api/health/
```

### View Logs
```bash
# Backend logs
tail -f /tmp/anylab_backend.log

# Frontend logs
tail -f /tmp/anylab_frontend.log
```

### Check Running Services
```bash
# Check backend port
lsof -i :8001

# Check frontend port
lsof -i :3000
```

## Troubleshooting

### Frontend still flashing?
1. Check if backend is running: `curl http://localhost:8001/api/health/`
2. Check browser console for errors
3. Clear browser cache and reload

### Backend not starting?
1. Check logs: `tail -f /tmp/anylab_backend.log`
2. Check Docker services: `docker ps | grep anylab`
3. Check port conflicts: `lsof -i :8001`

### Health check failing?
1. Verify backend is accessible: `curl http://localhost:8001/api/health/`
2. Check CORS settings in backend
3. Verify network connectivity

## Technical Details

### Health Check Logic
- **Endpoint**: `/api/health/`
- **Timeout**: 3 seconds
- **Cache**: 5 seconds (for healthy status)
- **Failure Threshold**: 2 consecutive failures
- **Background Check**: Every 30 seconds

### Polling Behavior
- **Normal**: 1 second interval
- **Backend Down**: 30 second interval (to detect recovery)
- **Exponential Backoff**: 1s → 2s → 4s → 8s → 16s → 30s (max)

This permanent fix ensures the system is robust, user-friendly, and resource-efficient.

