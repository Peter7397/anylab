# Cloudflare Tunnel Setup for AnyLab

## Overview

AnyLab uses **Cloudflare Tunnel** (formerly Argo Tunnel) for secure remote access. This provides:
- ✅ Secure HTTPS access without exposing ports
- ✅ No need for port forwarding or firewall configuration
- ✅ Automatic SSL/TLS certificates
- ✅ DDoS protection and security features

## Current Configuration

**Tunnel Name**: `anylab`  
**Config File**: `~/.cloudflared/config.yml`

### Routing Rules

The tunnel routes traffic as follows:

1. **`/api/*`** → Backend (port 8001)
2. **`/admin/*`** → Backend (port 8001)
3. **`/media/*`** → Backend (port 8001)
4. **`/static/*`** → Backend (port 8001)
5. **Everything else** → Frontend (port 3000)

### Configuration File

```yaml
tunnel: anylab
credentials-file: /Users/pinggenchen/.cloudflared/4d24c081-d409-4a06-9bd2-8c433772c64d.json

ingress:
  # Route /api/* to backend (port 8001)
  - hostname: anylab.dpdns.org
    path: /api/*
    service: http://localhost:8001
  # Route /admin/* to backend
  - hostname: anylab.dpdns.org
    path: /admin/*
    service: http://localhost:8001
  # Route /media/* to backend
  - hostname: anylab.dpdns.org
    path: /media/*
    service: http://localhost:8001
  # Route /static/* to backend
  - hostname: anylab.dpdns.org
    path: /static/*
    service: http://localhost:8001
  # Route everything else to frontend (port 3000)
  - hostname: anylab.dpdns.org
    service: http://localhost:3000
  # Separate API subdomain (if needed)
  - hostname: api.anylab.dpdns.org
    service: http://localhost:8001
  # Catch-all
  - service: http_status:404
```

## Starting the Tunnel

The tunnel should start automatically. To start manually:

```bash
cloudflared tunnel run anylab
```

To run in background:

```bash
cloudflared tunnel run anylab > /tmp/cloudflared.log 2>&1 &
```

## Checking Tunnel Status

```bash
# Check if tunnel is running
ps aux | grep cloudflared

# View tunnel logs
tail -f /tmp/cloudflared.log
```

## DNS Configuration

The domain `anylab.dpdns.org` is configured as a CNAME pointing to the Cloudflare Tunnel:

```
anylab.dpdns.org.  CNAME  4d24c081-d409-4a06-9bd2-8c433772c64d.cfargotunnel.com.
```

This is managed automatically by Cloudflare when you set up the tunnel.

## Access URLs

- **Frontend**: https://anylab.dpdns.org
- **Backend API**: https://anylab.dpdns.org/api/
- **Admin Panel**: https://anylab.dpdns.org/admin/

## Notes

- **Nginx is NOT required** for remote access - Cloudflare Tunnel handles routing
- All traffic is encrypted end-to-end
- No need to expose ports 80/443 on your firewall
- Tunnel automatically handles SSL/TLS certificates

## Troubleshooting

If the tunnel stops working:

1. **Check if tunnel is running**:
   ```bash
   ps aux | grep cloudflared
   ```

2. **Restart the tunnel**:
   ```bash
   killall cloudflared
   cloudflared tunnel run anylab
   ```

3. **Verify backend and frontend are running**:
   ```bash
   lsof -i :8001  # Backend
   lsof -i :3000  # Frontend
   ```

4. **Check tunnel logs**:
   ```bash
   tail -f /tmp/cloudflared.log
   ```

