# Cloudflare SSL Certificate Setup Guide

## Issue
When using Cloudflare to manage your domain, the HTTP-01 challenge can fail because:
1. Cloudflare proxies requests (orange cloud)
2. The challenge path gets routed to your app instead of being served directly

## Solutions

### Solution 1: Use DNS-01 Challenge (Recommended for Cloudflare)

DNS-01 challenge works better with Cloudflare because it doesn't require HTTP access.

#### Step 1: Install Cloudflare API Token
1. Go to Cloudflare Dashboard → My Profile → API Tokens
2. Create a token with:
   - Permissions: Zone → Zone → Read, DNS → DNS → Edit
   - Zone Resources: Include → Specific zone → `dpdns.org`

#### Step 2: Set Environment Variable
```bash
export CLOUDFLARE_API_TOKEN="your-api-token-here"
```

#### Step 3: Install Certbot Cloudflare Plugin
```bash
brew install certbot-dns-cloudflare
```

#### Step 4: Create Cloudflare Credentials File
```bash
sudo mkdir -p /etc/letsencrypt
sudo nano /etc/letsencrypt/cloudflare.ini
```

Add your token:
```
dns_cloudflare_api_token = your-api-token-here
```

Set permissions:
```bash
sudo chmod 600 /etc/letsencrypt/cloudflare.ini
```

#### Step 5: Get Certificate with DNS Challenge
```bash
sudo certbot certonly \
  --dns-cloudflare \
  --dns-cloudflare-credentials /etc/letsencrypt/cloudflare.ini \
  -d anylab.dpdns.org
```

#### Step 6: Configure Nginx to Use Certificate
After getting the certificate, update nginx config or let certbot do it:
```bash
sudo certbot --nginx -d anylab.dpdns.org --cert-path /etc/letsencrypt/live/anylab.dpdns.org
```

### Solution 2: Temporarily Disable Cloudflare Proxy

1. Go to Cloudflare Dashboard → DNS settings for `dpdns.org`
2. Find the A record for `anylab`
3. Click the orange cloud icon to make it gray (DNS only, no proxy)
4. Wait 2-5 minutes for DNS to propagate
5. Run certbot:
   ```bash
   sudo certbot --nginx -d anylab.dpdns.org
   ```
6. After certificate is issued, re-enable proxy (click gray cloud to make it orange)

### Solution 3: Fix Nginx to Serve ACME Challenges Properly

The nginx configuration has been updated to serve ACME challenges. After updating:

1. Test nginx configuration:
   ```bash
   sudo nginx -t
   ```

2. Reload nginx:
   ```bash
   sudo nginx -s reload
   ```

3. Ensure Cloudflare proxy is disabled (gray cloud) during challenge

4. Run certbot:
   ```bash
   sudo certbot --nginx -d anylab.dpdns.org
   ```

## Current Nginx Configuration

The nginx config now includes:
```nginx
location /.well-known/acme-challenge/ {
    root /opt/homebrew/var/www/html;
    try_files $uri =404;
    allow all;
}
```

This ensures ACME challenges are served directly, not proxied to your app.

## Quick Start (Recommended: DNS Challenge)

```bash
# 1. Set Cloudflare API token
export CLOUDFLARE_API_TOKEN="your-token"

# 2. Create credentials file
sudo mkdir -p /etc/letsencrypt
echo "dns_cloudflare_api_token = $CLOUDFLARE_API_TOKEN" | sudo tee /etc/letsencrypt/cloudflare.ini
sudo chmod 600 /etc/letsencrypt/cloudflare.ini

# 3. Install cloudflare plugin (if not installed)
brew install certbot-dns-cloudflare

# 4. Get certificate
sudo certbot certonly \
  --dns-cloudflare \
  --dns-cloudflare-credentials /etc/letsencrypt/cloudflare.ini \
  -d anylab.dpdns.org

# 5. Configure nginx (certbot will update config automatically)
sudo certbot --nginx -d anylab.dpdns.org
```

## Verify Certificate

```bash
# Check certificate
sudo certbot certificates

# Test HTTPS
curl -I https://anylab.dpdns.org

# Check certificate details
openssl s_client -connect anylab.dpdns.org:443 -servername anylab.dpdns.org
```

## Renewal

DNS challenge certificates renew the same way:
```bash
sudo certbot renew --dns-cloudflare --dns-cloudflare-credentials /etc/letsencrypt/cloudflare.ini
```

Or set up automatic renewal in crontab:
```bash
sudo crontab -e
# Add:
0 3 * * * certbot renew --dns-cloudflare --dns-cloudflare-credentials /etc/letsencrypt/cloudflare.ini --quiet
```

## Troubleshooting

### Issue: "Invalid response from http://anylab.dpdns.org/.well-known/acme-challenge/..."

**Solution:**
- Ensure Cloudflare proxy is disabled (gray cloud) during challenge
- Check nginx is serving the challenge path correctly
- Verify domain DNS points to your server's IP

### Issue: "DNS timeout" or "Could not resolve domain"

**Solution:**
- Check DNS propagation: `nslookup anylab.dpdns.org`
- Ensure DNS A record points to your server's public IP
- Wait a few minutes for DNS changes to propagate

### Issue: "Connection refused"

**Solution:**
- Ensure ports 80 and 443 are open
- Check firewall/router port forwarding
- Verify nginx is running: `ps aux | grep nginx`

## Benefits of DNS Challenge

- ✅ Works with Cloudflare proxy enabled
- ✅ No need to disable proxy
- ✅ More reliable
- ✅ Can get wildcard certificates (*.dpdns.org)

## Next Steps

After getting the certificate:
1. Enable Cloudflare proxy (orange cloud) if using DNS challenge
2. Configure Cloudflare SSL/TLS mode to "Full" or "Full (strict)"
3. Test HTTPS access
4. Set up automatic renewal

