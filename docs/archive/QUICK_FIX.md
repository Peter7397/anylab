# Quick Fix for Help Portal 404 Error

## Issue
The Help Portal page is showing 404 errors even though the routes exist.

## Solution

### Option 1: Restart Backend Server (Recommended)
The backend needs to be restarted to load the new routes:

```bash
# Find and kill the current server process
ps aux | grep "python.*manage.py runserver" | grep -v grep
# Kill it (replace PID with actual process ID)
kill <PID>

# Restart the server
cd /Volumes/Orico/OnLab0812/backend
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

### Option 2: Hard Refresh Frontend
1. Open browser DevTools (F12)
2. Right-click the refresh button
3. Select "Empty Cache and Hard Reload"

### Option 3: Clear Frontend Cache
```bash
cd /Volumes/Orico/OnLab0812/frontend
rm -rf node_modules/.cache
npm start
```

## Verification
After restarting, test the endpoint:
```bash
curl "http://localhost:8000/api/ai/help-portal/" -H "Authorization: Bearer YOUR_TOKEN"
```

Should return authentication error (not 404), which means the route exists.

## Alternative: Temporarily Remove Authentication
If you want to test without authentication, temporarily modify the views to remove `@permission_classes([IsAuthenticated])` decorator.

