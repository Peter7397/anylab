# Create New Token for anylab.dpdns.org

## Current Situation
- ✅ Token is valid
- ✅ Token can access: `ppdog.dpdns.org`
- ❌ Token cannot access: `anylab.dpdns.org`
- ✅ `anylab.dpdns.org` exists in Cloudflare Dashboard

## Problem
The token was likely created for `ppdog.dpdns.org` instead of `anylab.dpdns.org`, or there's a permission issue.

## Solution: Create New Token

### Step 1: Go to API Tokens
1. Visit: https://dash.cloudflare.com/profile/api-tokens
2. Click **"Create Token"**

### Step 2: Use Template
1. Find **"Edit zone DNS"** template
2. Click **"Use template"**

### Step 3: Configure Token
**IMPORTANT:** Make sure you select the correct zone!

1. **Token name:** (optional, e.g., "AnyLab SSL Token")
2. **Permissions:** (already set by template)
   - Zone → Zone → Read ✅
   - Zone → DNS → Edit ✅
3. **Zone Resources:** ⚠️ **CRITICAL STEP**
   - Click dropdown
   - Look for **`anylab.dpdns.org`** in the list
   - **If you see it:** Select it
   - **If you DON'T see it:** This means `anylab.dpdns.org` might not be a separate zone

### Step 4: If anylab.dpdns.org is NOT in the dropdown

This could mean:
- `anylab.dpdns.org` is a subdomain under `dpdns.org` (not a separate zone)
- You need to check if `dpdns.org` is the actual zone

**Check in Cloudflare Dashboard:**
1. Go to your zones list
2. Look at `anylab.dpdns.org`
3. Check if it shows as a separate zone or as a subdomain

**If it's a subdomain:**
- The zone is likely `dpdns.org` (the root domain)
- Create token for `dpdns.org` zone
- The token will work for all subdomains including `anylab.dpdns.org`

### Step 5: Create Token
1. Click **"Continue to summary"**
2. Review the configuration
3. Click **"Create Token"**
4. **COPY THE TOKEN IMMEDIATELY!**

### Step 6: Verify Token
Test the new token:

```bash
cd /Volumes/Orico/Anylab103
./nginx/verify-zone-access.sh
```

Paste your new token when prompted. It should show `anylab.dpdns.org` in the accessible zones.

### Step 7: Update Credentials
```bash
sudo ./nginx/update-token.sh
```

Paste your new token when prompted.

### Step 8: Get Certificate
```bash
sudo ./nginx/fix-zone-issue.sh
```

## Alternative: Check if dpdns.org is the Zone

If `anylab.dpdns.org` is not showing as a zone option, try:

1. Create token for `dpdns.org` (the root domain)
2. The token should work for `anylab.dpdns.org` subdomain
3. Certbot should be able to find the zone automatically

## Quick Check

**In Cloudflare Dashboard:**
1. Go to your zones list
2. Is `anylab.dpdns.org` listed as a **separate zone**?
   - **Yes** → Create token for `anylab.dpdns.org`
   - **No** → It's a subdomain, create token for `dpdns.org`

