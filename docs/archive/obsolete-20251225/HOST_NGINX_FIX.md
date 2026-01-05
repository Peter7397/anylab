# Host Nginx Fix for PDF Worker MIME Type

## Issue

When accessing via `https://anylab.dpdns.org`, the PDF worker file was still being served with `application/octet-stream` MIME type, even though the Docker container was serving it correctly.

## Root Cause

The host Nginx (running on the Mac) was proxying requests to the Docker frontend container, but wasn't explicitly handling the PDF worker file with the correct MIME type. The proxy_pass was preserving headers, but browser caching or header processing might have been interfering.

## Fix Applied

Added an explicit location block in `/Volumes/Orico/Anylab103/nginx/anylab.conf` for the PDF worker file:

```nginx
# PDF worker file - ensure correct MIME type (must come before catch-all)
location = /pdf.worker.min.mjs {
    proxy_pass http://127.0.0.1:3000;
    proxy_redirect off;
    # Force correct MIME type
    add_header Content-Type "application/javascript" always;
    add_header Cache-Control "public, max-age=31536000, immutable" always;
    # Preserve original headers from backend
    proxy_pass_header Content-Type;
}
```

**Why this works:**
- Exact match (`location =`) takes highest priority
- `add_header ... always` ensures the header is set even if the backend sets it
- Placed before the catch-all `location /` block
- Preserves backend headers while forcing the correct MIME type

## Apply the Fix

1. **Test the configuration:**
   ```bash
   sudo nginx -t
   ```

2. **Reload Nginx:**
   ```bash
   sudo nginx -s reload
   ```

3. **Verify:**
   ```bash
   curl -I https://anylab.dpdns.org/pdf.worker.min.mjs | grep -i content-type
   ```
   Should show: `Content-Type: application/javascript`

4. **Clear browser cache:**
   - Hard refresh: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)
   - Or clear cache for the site in browser settings

## Troubleshooting

### If MIME type is still wrong:

1. **Check if Nginx reloaded:**
   ```bash
   sudo nginx -s reload
   ```

2. **Check Nginx error logs:**
   ```bash
   sudo tail -f /var/log/nginx/anylab_error.log
   ```

3. **Verify the location block is active:**
   ```bash
   sudo nginx -T | grep -A 5 "pdf.worker"
   ```

4. **Test direct access:**
   ```bash
   curl -v https://anylab.dpdns.org/pdf.worker.min.mjs 2>&1 | grep -i "content-type"
   ```

5. **Clear browser cache completely:**
   - The browser might be caching the old MIME type
   - Try incognito/private mode to bypass cache

### If still not working:

1. **Check if Docker frontend is serving correctly:**
   ```bash
   curl -I http://localhost:3000/pdf.worker.min.mjs | grep -i content-type
   ```

2. **Verify the host Nginx config file location:**
   ```bash
   ls -la /etc/nginx/sites-available/anylab
   ls -la /etc/nginx/sites-enabled/anylab
   ```

3. **Check for other Nginx configs that might interfere:**
   ```bash
   sudo nginx -T | grep -i "pdf.worker"
   ```

## Notes

- The fix ensures the MIME type is correct at the host Nginx level
- Browser caching might require a hard refresh to see the fix
- The `always` flag ensures the header is set even if the backend doesn't set it
- This works in conjunction with the Docker container's nginx.conf fix

