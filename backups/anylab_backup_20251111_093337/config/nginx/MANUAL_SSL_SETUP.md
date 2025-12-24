# Manual SSL Certificate Setup (Step-by-Step)

If you prefer to do it manually instead of using the automated script:

## Step 1: Install Certbot Cloudflare Plugin

```bash
pip3 install certbot-dns-cloudflare
```

Or with sudo if needed:
```bash
sudo pip3 install certbot-dns-cloudflare
```

## Step 2: Get Cloudflare API Token

1. Go to: https://dash.cloudflare.com/profile/api-tokens
2. Click "Create Token"
3. Use "Edit zone DNS" template
4. Select zone: `dpdns.org`
5. Copy the token

## Step 3: Create Credentials File

```bash
sudo mkdir -p /etc/letsencrypt
sudo nano /etc/letsencrypt/cloudflare.ini
```

Add this line (replace YOUR_TOKEN with your actual token):
```
dns_cloudflare_api_token = YOUR_TOKEN_HERE
```

Save and set permissions:
```bash
sudo chmod 600 /etc/letsencrypt/cloudflare.ini
```

## Step 4: Get Certificate

```bash
sudo certbot certonly \
  --dns-cloudflare \
  --dns-cloudflare-credentials /etc/letsencrypt/cloudflare.ini \
  -d anylab.dpdns.org \
  --agree-tos \
  --email admin@anylab.dpdns.org
```

## Step 5: Configure Nginx

```bash
sudo certbot --nginx -d anylab.dpdns.org
```

Or manually update nginx config with certificate paths:
```
ssl_certificate /etc/letsencrypt/live/anylab.dpdns.org/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/anylab.dpdns.org/privkey.pem;
```

## Step 6: Test and Reload

```bash
sudo nginx -t
sudo nginx -s reload
```

## Step 7: Set Cloudflare Mode

1. Go to Cloudflare Dashboard
2. SSL/TLS → Overview
3. Set to "Full (strict)"
4. Save

## Verify

```bash
# Test HTTPS
curl -I https://anylab.dpdns.org

# Check certificate
sudo certbot certificates
```
