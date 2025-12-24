# Quick Zone Fix Guide

## The Problem
Your token can access `ppdog.dpdns.org` but not `anylab.dpdns.org`. This means the `anylab.dpdns.org` zone either:
- Doesn't exist in Cloudflare
- Exists in a different account
- Needs to be added

## Solution: Check Your Cloudflare Dashboard

### Step 1: Check Zones List
1. Go to: https://dash.cloudflare.com
2. Look at the left sidebar - you'll see "Sites" or "Zones"
3. Check if `anylab.dpdns.org` is listed

### Step 2A: If Zone Exists
- Create a NEW token specifically for `anylab.dpdns.org` zone
- Make sure to select `anylab.dpdns.org` (not dpdns.org)
- Use that token in the setup script

### Step 2B: If Zone Doesn't Exist
**Add the zone to Cloudflare:**
1. Click "Add a Site" or "Add Site" button
2. Enter: `anylab.dpdns.org`
3. Select Free plan
4. Follow Cloudflare's instructions
5. Update nameservers if needed
6. Wait for activation
7. Then create a token for that zone

## Quick Test

After adding zone or creating new token, test access:

```bash
curl -s "https://api.cloudflare.com/client/v4/zones" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" | python3 -c \
  "import sys, json; data = json.load(sys.stdin); \
  zones = [z['name'] for z in data.get('result', [])]; \
  print('Zones:', zones); \
  print('anylab.dpdns.org found:', 'anylab.dpdns.org' in zones)"
```

Should show: `anylab.dpdns.org found: True`

## Then Run Setup Again

Once the zone exists and token has access:
```bash
sudo ./nginx/setup-cloudflare-ssl.sh
```
