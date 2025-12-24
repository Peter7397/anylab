# Fix Certbot Nginx Path Issue

## Problem
Certbot is looking for nginx at `/usr/local/etc/nginx/nginx.conf` but Homebrew installs it at `/opt/homebrew/etc/nginx/nginx.conf`.

## Solution

### Option 1: Create Symlink (Recommended)

```bash
# Create directory if it doesn't exist
sudo mkdir -p /usr/local/etc/nginx

# Create symlink
sudo ln -sf /opt/homebrew/etc/nginx/nginx.conf /usr/local/etc/nginx/nginx.conf

# Verify
ls -la /usr/local/etc/nginx/nginx.conf
```

Then run certbot:
```bash
sudo certbot --nginx -d anylab.dpdns.org
```

### Option 2: Use Certbot with Explicit Config

```bash
sudo certbot --nginx --nginx-server-root /opt/homebrew/etc/nginx -d anylab.dpdns.org
```

### Option 3: Set Environment Variable

```bash
export NGINX_CONFIG_PATH="/opt/homebrew/etc/nginx/nginx.conf"
sudo -E certbot --nginx -d anylab.dpdns.org
```

## Verify Fix

After creating symlink:
```bash
# Test nginx config
sudo nginx -t

# Run certbot
sudo certbot --nginx -d anylab.dpdns.org
```
