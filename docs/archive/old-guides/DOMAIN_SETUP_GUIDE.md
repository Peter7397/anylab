# Domain Setup Guide - anylab.dpdns.org

This guide explains how to set up internet access for AnyLab using the domain name `anylab.dpdns.org`.

## Overview

AnyLab uses **Cloudflare Tunnel** for secure remote access. This provides:
- ✅ **Secure HTTPS** without exposing ports
- ✅ **No firewall configuration** needed
- ✅ **Automatic SSL/TLS** certificates
- ✅ **DDoS protection** and security features

**Note**: Nginx is NOT required for remote access. Cloudflare Tunnel handles all routing.

For detailed Cloudflare Tunnel setup, see: [CLOUDFLARE_TUNNEL_SETUP.md](CLOUDFLARE_TUNNEL_SETUP.md)

## Prerequisites

1. **Cloudflare Tunnel** - Installed and configured (see [CLOUDFLARE_TUNNEL_SETUP.md](CLOUDFLARE_TUNNEL_SETUP.md))
2. **Application Running**
   - Frontend: Running on port 3000
   - Backend: Running on port 8001
   - Docker services: PostgreSQL, Redis, Neo4j

**Note**: No firewall configuration or port forwarding needed - Cloudflare Tunnel handles everything!

## Setup Steps

### Step 1: Configure Cloudflare Tunnel
See [CLOUDFLARE_TUNNEL_SETUP.md](CLOUDFLARE_TUNNEL_SETUP.md) for detailed instructions.

The tunnel configuration file is at: `~/.cloudflared/config.yml`

### Step 1 (Legacy): Install and Configure Nginx (Optional - Not Required)
**Note**: Nginx is not needed when using Cloudflare Tunnel. This section is for reference only.

```bash
cd /Volumes/Orico/Anylab103
sudo ./nginx/setup-nginx.sh
```

This script will:
- Install nginx (if not already installed)
- Copy nginx configuration
- Set up SSL certificate (optional, can be done later)
- Start nginx service

### Step 2: Manual Nginx Setup (Alternative)

If you prefer to set up manually:

```bash
# Copy nginx configuration
sudo cp nginx/anylab.conf /etc/nginx/sites-available/anylab
sudo ln -s /etc/nginx/sites-available/anylab /etc/nginx/sites-enabled/anylab

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Start/reload nginx
sudo systemctl restart nginx  # Linux
# or
sudo nginx -s reload  # macOS
```

### Step 3: Set Up SSL Certificate

For HTTPS access, you need an SSL certificate:

```bash
# Install certbot (if not installed)
# macOS:
brew install certbot

# Linux (Ubuntu/Debian):
sudo apt-get install certbot python3-certbot-nginx

# Linux (CentOS/RHEL):
sudo yum install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d anylab.dpdns.org

# Follow the prompts and enter your email address
```

**Note:** Certbot requires:
- Domain must point to your server's public IP
- Ports 80 and 443 must be accessible from the internet
- You may need to configure firewall/router port forwarding

### Step 4: Configure Firewall/Router

You need to open ports 80 and 443:

**On the server (if firewall is enabled):**
```bash
# macOS (pfctl)
# Edit /etc/pf.conf or use pfctl commands

# Linux (ufw)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw reload

# Linux (iptables)
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
```

**On your router:**
- Forward port 80 (HTTP) to your server's local IP
- Forward port 443 (HTTPS) to your server's local IP

### Step 5: Restart Services

After configuration, restart the services:

```bash
# Restart nginx
sudo systemctl restart nginx  # Linux
# or
sudo nginx -s reload  # macOS

# Restart backend (if needed)
cd /Volumes/Orico/Anylab103/backend
./venv/bin/python manage.py runserver 0.0.0.0:8001

# Restart frontend (if needed)
cd /Volumes/Orico/Anylab103/frontend
npm start
```

## Configuration Details

### Nginx Configuration

The nginx configuration (`nginx/anylab.conf`) does the following:

- **HTTP (port 80)**: Redirects all traffic to HTTPS
- **HTTPS (port 443)**: 
  - `/api/*` → Proxies to Django backend (port 8001)
  - `/admin/*` → Proxies to Django admin (port 8001)
  - `/media/*` → Proxies to Django media files (port 8001)
  - `/static/*` → Proxies to Django static files (port 8001)
  - `/*` → Proxies to React frontend (port 3000)

### Application Configuration

**Backend (Django):**
- ✅ `anylab.dpdns.org` added to `ALLOWED_HOSTS`
- ✅ `https://anylab.dpdns.org` and `http://anylab.dpdns.org` added to `CORS_ALLOWED_ORIGINS`

**Frontend (React):**
- ✅ Auto-detects domain name and uses it for API calls
- ✅ When accessed via `anylab.dpdns.org`, API calls go to `https://anylab.dpdns.org/api`

## Testing

### 1. Test DNS Resolution

```bash
nslookup anylab.dpdns.org
# Should return your server's public IP
```

### 2. Test HTTP Access (should redirect to HTTPS)

```bash
curl -I http://anylab.dpdns.org
# Should return 301 redirect to HTTPS
```

### 3. Test HTTPS Access

```bash
curl -I https://anylab.dpdns.org
# Should return 200 OK
```

### 4. Test API Endpoint

```bash
curl https://anylab.dpdns.org/api/health/
# Should return JSON: {"status": "healthy", "service": "anylab-backend"}
```

### 5. Test from Browser

1. Open browser and go to: `https://anylab.dpdns.org`
2. Should see the React frontend
3. Check browser console for any API errors
4. Try logging in to verify API connectivity

## Troubleshooting

### Issue: "Connection Refused"

**Symptoms:** Cannot access `anylab.dpdns.org` from internet

**Solutions:**
1. Check DNS: `nslookup anylab.dpdns.org` - should point to your public IP
2. Check firewall: Ensure ports 80 and 443 are open
3. Check router: Ensure port forwarding is configured
4. Check nginx: `sudo systemctl status nginx` or `ps aux | grep nginx`
5. Check nginx logs: `sudo tail -f /var/log/nginx/anylab_error.log`

### Issue: "SSL Certificate Error"

**Symptoms:** Browser shows "Not Secure" or certificate error

**Solutions:**
1. Check certificate: `sudo certbot certificates`
2. Renew certificate: `sudo certbot renew`
3. Check nginx config: `sudo nginx -t`
4. Reload nginx: `sudo systemctl reload nginx`

### Issue: "502 Bad Gateway"

**Symptoms:** Nginx returns 502 error

**Solutions:**
1. Check backend is running: `ps aux | grep "manage.py runserver"`
2. Check backend logs: `tail -f logs/django.log`
3. Check frontend is running: `ps aux | grep "react-scripts"`
4. Verify ports: `lsof -i :8001` and `lsof -i :3000`
5. Check nginx error logs: `sudo tail -f /var/log/nginx/anylab_error.log`

### Issue: "CORS Error"

**Symptoms:** Browser console shows CORS errors

**Solutions:**
1. Verify domain is in `CORS_ALLOWED_ORIGINS` in `backend/anylab/settings.py`
2. Restart backend after configuration changes
3. Check browser console for exact error message
4. Verify protocol (http vs https) matches

### Issue: "API Not Found (404)"

**Symptoms:** API calls return 404

**Solutions:**
1. Check nginx configuration: `sudo nginx -t`
2. Verify `/api/` location block in nginx config
3. Test backend directly: `curl http://localhost:8001/api/health/`
4. Check Django URLs: `curl http://localhost:8001/api/ai/`

## Maintenance

### Renew SSL Certificate

SSL certificates expire every 90 days. Certbot can auto-renew:

```bash
# Test renewal
sudo certbot renew --dry-run

# Manual renewal
sudo certbot renew
sudo systemctl reload nginx
```

### Update Nginx Configuration

After modifying `nginx/anylab.conf`:

```bash
# Copy to nginx
sudo cp nginx/anylab.conf /etc/nginx/sites-available/anylab

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### Monitor Logs

```bash
# Nginx access logs
sudo tail -f /var/log/nginx/anylab_access.log

# Nginx error logs
sudo tail -f /var/log/nginx/anylab_error.log

# Django logs
tail -f logs/django.log

# Frontend logs
tail -f logs/frontend.log
```

## Security Considerations

1. **HTTPS Only**: HTTP automatically redirects to HTTPS
2. **Security Headers**: Nginx adds security headers (HSTS, X-Frame-Options, etc.)
3. **Firewall**: Only ports 80 and 443 should be open from internet
4. **Rate Limiting**: Consider adding rate limiting in nginx for API endpoints
5. **SSL Configuration**: Uses modern TLS protocols (1.2, 1.3)

## Access URLs

Once set up, you can access:

- **Frontend**: https://anylab.dpdns.org
- **Backend API**: https://anylab.dpdns.org/api/
- **Admin Panel**: https://anylab.dpdns.org/admin/
- **Health Check**: https://anylab.dpdns.org/api/health/

## Support

If you encounter issues:

1. Check nginx logs: `/var/log/nginx/anylab_error.log`
2. Check application logs: `logs/django.log` and `logs/frontend.log`
3. Verify all services are running
4. Test DNS resolution and port connectivity
5. Review firewall and router configurations

