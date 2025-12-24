# Quick Start: SSL Certificate Setup

## 🚀 Fastest Way (3 Steps)

### Step 1: Install Plugin
```bash
pip3 install certbot-dns-cloudflare --break-system-packages
```

Or if that doesn't work:
```bash
sudo pip3 install certbot-dns-cloudflare --break-system-packages
```

### Step 2: Get Cloudflare API Token
1. Go to: https://dash.cloudflare.com/profile/api-tokens
2. Click "Create Token" → "Edit zone DNS" template
3. Select zone: `dpdns.org`
4. Copy the token

### Step 3: Run Setup
```bash
cd /Volumes/Orico/Anylab103
sudo ./nginx/setup-cloudflare-ssl.sh
```

The script will:
- ✅ Ask for your Cloudflare token
- ✅ Create credentials file
- ✅ Get SSL certificate
- ✅ Configure nginx

## Or Do It Manually

See `nginx/MANUAL_SSL_SETUP.md` for step-by-step manual instructions.

## After Setup

1. **Set Cloudflare SSL mode:**
   - Dashboard → SSL/TLS → "Full (strict)"

2. **Test:**
   ```bash
   curl -I https://anylab.dpdns.org
   ```

3. **Verify certificate:**
   ```bash
   sudo certbot certificates
   ```

## That's It! 🎉

Your site will be fully encrypted end-to-end!
