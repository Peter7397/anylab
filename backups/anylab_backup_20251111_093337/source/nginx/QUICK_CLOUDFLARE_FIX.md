# Quick Cloudflare SSL Fix

## Problem
Certbot HTTP-01 challenge fails because Cloudflare proxies requests and nginx isn't serving the challenge path correctly.

## Solution Options

### Option 1: DNS Challenge (Best for Cloudflare) ⭐

Works with Cloudflare proxy enabled. No need to disable anything.

```bash
# 1. Get Cloudflare API token from dashboard
# Cloudflare Dashboard → My Profile → API Tokens → Create Token
# Permissions: Zone → Zone → Read, DNS → DNS → Edit

# 2. Install plugin
brew install certbot-dns-cloudflare

# 3. Create credentials
sudo mkdir -p /etc/letsencrypt
echo "dns_cloudflare_api_token = YOUR_TOKEN_HERE" | sudo tee /etc/letsencrypt/cloudflare.ini
sudo chmod 600 /etc/letsencrypt/cloudflare.ini

# 4. Get certificate
sudo certbot certonly \
  --dns-cloudflare \
  --dns-cloudflare-credentials /etc/letsencrypt/cloudflare.ini \
  -d anylab.dpdns.org

# 5. Configure nginx
sudo certbot --nginx -d anylab.dpdns.org
```

### Option 2: Disable Cloudflare Proxy Temporarily

1. Go to Cloudflare Dashboard → DNS
2. Find `anylab` A record
3. Click orange cloud → make it gray (DNS only)
4. Wait 2-5 minutes
5. Run: `sudo certbot --nginx -d anylab.dpdns.org`
6. After certificate is issued, re-enable proxy (gray → orange)

### Option 3: Fix Nginx Config (Already Done)

The nginx config has been updated to serve ACME challenges. You still need to:

1. Create challenge directory:
   ```bash
   sudo mkdir -p /opt/homebrew/var/www/html/.well-known/acme-challenge
   sudo chmod -R 755 /opt/homebrew/var/www/html
   ```

2. Reload nginx:
   ```bash
   sudo nginx -t
   sudo nginx -s reload
   ```

3. Disable Cloudflare proxy temporarily (gray cloud)
4. Run certbot:
   ```bash
   sudo certbot --nginx -d anylab.dpdns.org
   ```
5. Re-enable proxy after certificate is issued

## Recommendation

**Use DNS Challenge (Option 1)** - It's the most reliable with Cloudflare and doesn't require disabling the proxy.
