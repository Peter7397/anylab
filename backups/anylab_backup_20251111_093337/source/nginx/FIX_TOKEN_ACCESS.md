# Fix Token Access Issue

## Problem
- ✅ `anylab.dpdns.org` zone exists in Cloudflare Dashboard
- ❌ Token cannot access `anylab.dpdns.org` zone via API
- ✅ Token can access `ppdog.dpdns.org` zone

## Solution: Create New Token for anylab.dpdns.org

Since the zone exists but the token doesn't have access, create a new token specifically for `anylab.dpdns.org`.

### Step 1: Create New Token
1. Go to: https://dash.cloudflare.com/profile/api-tokens
2. Click **"Create Token"**
3. Use **"Edit zone DNS"** template
4. In **Zone Resources**, select:
   - **Include** → **Specific zone** → **`anylab.dpdns.org`**
5. Click **"Continue to summary"**
6. Click **"Create Token"**
7. **COPY THE TOKEN** (you won't see it again!)

### Step 2: Verify Token Access
Test the new token:

```bash
curl -s "https://api.cloudflare.com/client/v4/zones" \
  -H "Authorization: Bearer YOUR_NEW_TOKEN" \
  -H "Content-Type: application/json" | python3 -c \
  "import sys, json; data = json.load(sys.stdin); \
  zones = [z['name'] for z in data.get('result', [])]; \
  print('Zones:', zones); \
  print('anylab.dpdns.org found:', 'anylab.dpdns.org' in zones)"
```

Should show: `anylab.dpdns.org found: True`

### Step 3: Update Credentials File
Replace the old token with the new one:

```bash
sudo nano /etc/letsencrypt/cloudflare.ini
```

Replace the token line with:
```
dns_cloudflare_api_token = YOUR_NEW_TOKEN_HERE
```

Save and exit (Ctrl+X, then Y, then Enter)

### Step 4: Run Setup Again
```bash
cd /Volumes/Orico/Anylab103
sudo ./nginx/setup-cloudflare-ssl.sh
```

Or if credentials file is already updated:
```bash
sudo ./nginx/fix-zone-issue.sh
```

## Why This Happens

Sometimes tokens are created but:
- The zone selection doesn't work correctly
- Permissions aren't properly applied
- The token needs to be recreated for the specific zone

## Quick Fix Command

After creating new token, update credentials:

```bash
# Backup old file
sudo cp /etc/letsencrypt/cloudflare.ini /etc/letsencrypt/cloudflare.ini.backup

# Update with new token
echo "dns_cloudflare_api_token = YOUR_NEW_TOKEN" | sudo tee /etc/letsencrypt/cloudflare.ini
sudo chmod 600 /etc/letsencrypt/cloudflare.ini
```

Then run setup again!

