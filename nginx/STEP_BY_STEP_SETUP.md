# Step-by-Step Domain Setup Guide

This guide will walk you through setting up internet access for AnyLab via `anylab.dpdns.org`.

## Prerequisites Checklist

Before starting, ensure:
- [ ] Domain `anylab.dpdns.org` DNS A record points to your server's public IP
- [ ] Ports 80 and 443 are open in your firewall/router
- [ ] Backend and frontend are running
- [ ] Docker services (PostgreSQL, Redis, Neo4j) are running

## Step 1: Verify Prerequisites

Run the verification script:
```bash
cd /Volumes/Orico/Anylab103
chmod +x nginx/verify-prerequisites.sh
./nginx/verify-prerequisites.sh
```

This will check:
- DNS configuration
- Required software (Homebrew, nginx, certbot)
- Port availability
- Application services status
- Docker services status

Fix any errors before proceeding.

## Step 2: Install and Configure Nginx

Run the setup script with sudo:
```bash
cd /Volumes/Orico/Anylab103
sudo ./nginx/setup-nginx.sh
```

This script will:
1. Install nginx (if not already installed)
2. Copy nginx configuration to `/etc/nginx/sites-available/anylab`
3. Create symlink in `/etc/nginx/sites-enabled/`
4. Test nginx configuration
5. Optionally set up SSL certificate

**Note:** You'll need to enter your password for sudo.

## Step 3: Set Up SSL Certificate

After nginx is installed, set up SSL with Let's Encrypt:

```bash
sudo certbot --nginx -d anylab.dpdns.org
```

Follow the prompts:
1. Enter your email address (for renewal notifications)
2. Agree to terms of service
3. Choose whether to redirect HTTP to HTTPS (recommended: Yes)

**Important:** Certbot requires:
- Domain must point to your server's public IP
- Ports 80 and 443 must be accessible from the internet
- You may need to configure port forwarding on your router

## Step 4: Verify Firewall Configuration

### macOS Firewall
1. Open System Preferences → Security & Privacy → Firewall
2. Click "Firewall Options"
3. Ensure nginx is allowed (or add it if needed)
4. Ensure ports 80 and 443 are not blocked

### Router Port Forwarding
Configure your router to forward:
- Port 80 (HTTP) → Your server's local IP:80
- Port 443 (HTTPS) → Your server's local IP:443

## Step 5: Test the Setup

### Test DNS Resolution
```bash
nslookup anylab.dpdns.org
# Should return your server's public IP
```

### Test HTTP Access (should redirect to HTTPS)
```bash
curl -I http://anylab.dpdns.org
# Should return: HTTP/1.1 301 Moved Permanently
```

### Test HTTPS Access
```bash
curl -I https://anylab.dpdns.org
# Should return: HTTP/1.1 200 OK
```

### Test from Browser
1. Open browser and go to: `https://anylab.dpdns.org`
2. Should see the React frontend
3. Check browser console for any errors
4. Try logging in to verify API connectivity

## Step 6: Monitor Logs

Keep an eye on the logs:
```bash
# Nginx access logs
sudo tail -f /var/log/nginx/anylab_access.log

# Nginx error logs
sudo tail -f /var/log/nginx/anylab_error.log

# Django logs
tail -f /Volumes/Orico/Anylab103/logs/django.log

# Frontend logs
tail -f /Volumes/Orico/Anylab103/logs/frontend.log
```

## Troubleshooting

### Issue: "Connection Refused" from Internet

**Check:**
1. DNS: `nslookup anylab.dpdns.org` - should return your public IP
2. Firewall: Ensure ports 80 and 443 are open
3. Router: Check port forwarding configuration
4. Nginx: `sudo systemctl status nginx` or `ps aux | grep nginx`

### Issue: "SSL Certificate Error"

**Solutions:**
1. Check certificate: `sudo certbot certificates`
2. Renew certificate: `sudo certbot renew`
3. Verify nginx config: `sudo nginx -t`
4. Reload nginx: `sudo systemctl reload nginx`

### Issue: "502 Bad Gateway"

**Solutions:**
1. Check backend: `ps aux | grep "manage.py runserver"`
2. Check frontend: `ps aux | grep "react-scripts\|craco"`
3. Verify ports: `lsof -i :8001` and `lsof -i :3000`
4. Check nginx error logs: `sudo tail -f /var/log/nginx/anylab_error.log`

### Issue: "CORS Error"

**Solutions:**
1. Verify domain in `backend/anylab/settings.py`:
   - `CORS_ALLOWED_ORIGINS` should include `https://anylab.dpdns.org`
2. Restart backend after configuration changes
3. Check browser console for exact error

## Manual Nginx Setup (Alternative)

If the automated script doesn't work, you can set up manually:

```bash
# 1. Install nginx
brew install nginx  # macOS
# or
sudo apt-get install nginx  # Linux

# 2. Copy configuration
sudo cp /Volumes/Orico/Anylab103/nginx/anylab.conf /etc/nginx/sites-available/anylab

# 3. Create symlink
sudo ln -s /etc/nginx/sites-available/anylab /etc/nginx/sites-enabled/anylab

# 4. Remove default site
sudo rm /etc/nginx/sites-enabled/default

# 5. Test configuration
sudo nginx -t

# 6. Start nginx
sudo nginx  # or sudo systemctl start nginx
```

## Next Steps

After successful setup:

1. **Set up auto-renewal for SSL:**
   ```bash
   # Certbot auto-renewal is usually set up automatically
   # Test renewal: sudo certbot renew --dry-run
   ```

2. **Monitor performance:**
   - Check nginx access logs regularly
   - Monitor application logs for errors
   - Set up log rotation if needed

3. **Security hardening:**
   - Review nginx security headers
   - Consider rate limiting for API endpoints
   - Keep nginx and certbot updated

## Access URLs

Once set up, you can access:

- **Frontend**: https://anylab.dpdns.org
- **Backend API**: https://anylab.dpdns.org/api/
- **Admin Panel**: https://anylab.dpdns.org/admin/
- **Health Check**: https://anylab.dpdns.org/api/health/

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review logs (nginx, django, frontend)
3. Verify all prerequisites are met
4. Check DNS and firewall/router configurations

