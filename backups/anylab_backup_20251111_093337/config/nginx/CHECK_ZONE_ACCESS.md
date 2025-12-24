# Check Zone Access and Fix

## Issue
The token can access `ppdog.dpdns.org` but not `anylab.dpdns.org`. This means either:
1. The `anylab.dpdns.org` zone doesn't exist in Cloudflare yet
2. The token doesn't have access to it
3. The zone needs to be added to Cloudflare

## Solution Options

### Option 1: Add Zone to Cloudflare (If Not Added)

If `anylab.dpdns.org` is not yet a zone in Cloudflare:

1. Go to Cloudflare Dashboard: https://dash.cloudflare.com
2. Click **"Add a Site"** or **"Add Site"**
3. Enter: `anylab.dpdns.org`
4. Select a plan (Free plan is fine)
5. Cloudflare will scan your DNS records
6. Update your nameservers if needed
7. Wait for activation (usually a few minutes)

### Option 2: Check if Zone Exists

1. Go to Cloudflare Dashboard
2. Look at your zones list
3. Check if `anylab.dpdns.org` appears
4. If not, you need to add it (see Option 1)

### Option 3: Use Different Token

If `anylab.dpdns.org` is managed under a different Cloudflare account or needs different permissions:

1. Create a new token
2. Make sure it has access to `anylab.dpdns.org` zone
3. Use that token instead

## Verify Zone Access

Run this command to see what zones your token can access:

```bash
curl -s "https://api.cloudflare.com/client/v4/zones" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" | python3 -m json.tool
```

Look for `anylab.dpdns.org` in the results.

## If Zone Doesn't Exist

You have two options:

### A. Add as Separate Zone (Recommended if it's a subdomain)
1. Add `anylab.dpdns.org` as a new site in Cloudflare
2. Follow Cloudflare's setup instructions
3. Update nameservers if needed

### B. Use Root Domain Zone
If `dpdns.org` is the actual zone and `anylab` is just a subdomain:
1. Create a new token for `dpdns.org` zone
2. The token will work for `anylab.dpdns.org` subdomain
3. Use that token

## Quick Check

**Question:** When you go to Cloudflare Dashboard, do you see `anylab.dpdns.org` listed as one of your sites/zones?

- **Yes** → Token might not have access, create new token for that zone
- **No** → Need to add `anylab.dpdns.org` as a site in Cloudflare first

