# How to Get Cloudflare API Token

## Quick Steps

### 1. Go to Cloudflare Dashboard
- Visit: https://dash.cloudflare.com/profile/api-tokens
- Or: Dashboard → My Profile → API Tokens

### 2. Create Token

#### Option A: Use Template (Easiest)
1. Scroll down to "API Tokens" section
2. Find **"Edit zone DNS"** template
3. Click **"Use template"**
4. Select **"Zone Resources"** → **"Include"** → **"Specific zone"**
5. Choose **`dpdns.org`** from dropdown
6. Click **"Continue to summary"**
7. Click **"Create Token"**
8. **Copy the token immediately** (you won't see it again!)

#### Option B: Create Custom Token
1. Click **"Create Token"**
2. Click **"Create custom token"**
3. Set permissions:
   - **Zone** → **Zone** → **Read**
   - **Zone** → **DNS** → **Edit**
4. Set Zone Resources:
   - Select **"Include"**
   - Select **"Specific zone"**
   - Choose **`dpdns.org`** (the root domain/zone)
     - Note: Your site is `anylab.dpdns.org` but you select the root zone `dpdns.org`
     - This token will work for all subdomains under `dpdns.org`
5. Click **"Continue to summary"**
6. Click **"Create Token"**
7. **Copy the token immediately**

### 3. Save Token Securely
- The token will look like: `abc123def456...` (long string)
- Save it somewhere safe - you'll need it for the setup script
- You can regenerate it if needed, but old tokens will stop working

## Token Permissions Needed

- ✅ **Zone → Zone → Read** (to read zone information)
- ✅ **Zone → DNS → Edit** (to add TXT records for DNS challenge)

## Security Notes

- 🔒 Keep your token secret
- 🔒 Don't commit it to git
- 🔒 Store it securely
- 🔒 Regenerate if compromised

## Next Step

Once you have the token, run:
```bash
cd /Volumes/Orico/Anylab103
sudo ./nginx/setup-cloudflare-ssl.sh
```

The script will ask for your token and set everything up automatically!

