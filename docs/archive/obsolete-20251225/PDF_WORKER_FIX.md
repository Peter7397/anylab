# PDF Worker Fix for Document Viewer

## Issue

When viewing documents in RAG results, the PDF.js worker failed to load with error:
```
Setting up fake worker failed: "Failed to fetch dynamically imported module: https://anylab.dpdns.org/pdf.worker.min.mjs"
```

## Root Causes

1. **Hardcoded Worker Path**: The PDF worker path was hardcoded to `/pdf.worker.min.mjs`, which doesn't work correctly when accessed via different domains (localhost vs anylab.dpdns.org)

2. **Nginx Permission Issues**: The worker file had incorrect permissions (`-rwx------`) that prevented Nginx from serving it

3. **Missing MIME Type**: Nginx wasn't configured to serve `.mjs` files with the correct MIME type

## Fixes Applied

### 1. Dynamic Worker Path (`frontend/src/components/AI/DocumentViewer.tsx`)

Changed from hardcoded path to dynamic path based on current origin:

```typescript
// Before:
GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs';

// After:
if (typeof window !== 'undefined') {
  const workerPath = `${window.location.origin}/pdf.worker.min.mjs`;
  GlobalWorkerOptions.workerSrc = workerPath;
}
```

**Why**: This ensures the worker loads from the correct origin whether accessing via:
- `http://localhost:3000` (development)
- `https://anylab.dpdns.org` (production)

### 2. Nginx Configuration (`frontend/nginx.conf`)

Added explicit handling for the PDF worker file:

```nginx
# Serve PDF worker file with correct MIME type
location = /pdf.worker.min.mjs {
    add_header Content-Type "application/javascript";
    add_header Cache-Control "public, max-age=31536000, immutable";
    try_files $uri =404;
}

# Updated static assets to include .mjs files
location ~* \.(js|mjs|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

**Why**: 
- Ensures correct MIME type for `.mjs` files
- Proper caching headers
- Explicit location block takes precedence

### 3. Dockerfile Permissions (`frontend/Dockerfile`)

Added permission fix in the Dockerfile:

```dockerfile
# Set proper permissions for Nginx to serve files
RUN chmod -R 755 /usr/share/nginx/html && \
    chown -R nginx:nginx /usr/share/nginx/html
```

**Why**: Nginx runs as a non-root user and needs read access to all files in the web root.

## Verification

To verify the fix:

1. **Check file permissions:**
   ```bash
   docker exec anylab_frontend ls -la /usr/share/nginx/html/pdf.worker.min.mjs
   ```
   Should show: `-rw-r--r--` (644) or `-rwxr-xr-x` (755)

2. **Test worker loading:**
   - Open browser DevTools → Network tab
   - Navigate to a document in RAG results
   - Check if `pdf.worker.min.mjs` loads successfully (status 200)
   - No CORS errors should appear

3. **Check Nginx logs:**
   ```bash
   docker compose logs frontend | grep pdf.worker
   ```
   Should show successful requests, not permission denied errors

## Testing

1. **Local Development:**
   - Access via `http://localhost:3000`
   - Worker should load from `http://localhost:3000/pdf.worker.min.mjs`

2. **Production:**
   - Access via `https://anylab.dpdns.org`
   - Worker should load from `https://anylab.dpdns.org/pdf.worker.min.mjs`

## Rebuild Required

After these changes, rebuild the frontend container:

```bash
# Rebuild frontend
docker compose -f docker-compose.yml -f docker-compose.mac.yml build frontend

# Restart frontend
docker compose -f docker-compose.yml -f docker-compose.mac.yml up -d frontend
```

Or use the build script:
```bash
./scripts/build-frontend-docker.sh
docker compose -f docker-compose.yml -f docker-compose.mac.yml up -d frontend
```

## Troubleshooting

### If worker still fails to load:

1. **Check file exists:**
   ```bash
   docker exec anylab_frontend ls -la /usr/share/nginx/html/pdf.worker.min.mjs
   ```

2. **Check Nginx can read it:**
   ```bash
   docker exec anylab_frontend cat /usr/share/nginx/html/pdf.worker.min.mjs | head -5
   ```

3. **Test direct access:**
   - Open `https://anylab.dpdns.org/pdf.worker.min.mjs` in browser
   - Should see JavaScript code, not 404 or 403

4. **Check browser console:**
   - Look for CORS errors
   - Check Network tab for failed requests
   - Verify the worker URL matches current origin

5. **Check Nginx error logs:**
   ```bash
   docker exec anylab_frontend cat /var/log/nginx/error.log | tail -20
   ```

## MIME Type Fix

The critical issue was that Nginx was serving `.mjs` files with `application/octet-stream` instead of `application/javascript`. This was fixed by:

1. **Adding types override in nginx.conf:**
   ```nginx
   include /etc/nginx/mime.types;
   
   types_hash_max_size 4096;
   types {
       application/javascript mjs js;
   }
   ```

2. **The types block must come after the include** to properly override the default MIME types.

3. **Rebuild required:** The frontend container must be rebuilt for the nginx.conf changes to take effect.

## Additional Notes

- The worker file is copied from `frontend/public/pdf.worker.min.mjs` during build
- The file is served as a static asset by Nginx with correct MIME type
- Caching is enabled for performance (1 year cache)
- The fix works for both development and production environments
- The MIME type fix ensures browsers accept the worker as a JavaScript module

