# 🚀 Quick Start - Domain Setup (Fixed)

## The Issue
Homebrew cannot run with sudo. The setup script has been fixed to handle this.

## ✅ Solution: Install Nginx First (No Sudo)

### Step 1: Install Nginx (run WITHOUT sudo)
```bash
brew install nginx
```

Or use the helper script:
```bash
cd /Volumes/Orico/Anylab103
./nginx/install-nginx-manual.sh
```

### Step 2: Run Setup Script (with sudo)
```bash
cd /Volumes/Orico/Anylab103
sudo ./nginx/setup-nginx.sh
```

The script will now:
- ✅ Detect nginx is already installed
- ✅ Configure nginx (requires sudo)
- ✅ Set up SSL certificate (optional)

### Step 3: Set Up SSL Certificate (with sudo)
```bash
sudo certbot --nginx -d anylab.dpdns.org
```

## All-in-One Commands

Copy and paste these commands one at a time:

```bash
# 1. Install nginx (no sudo)
brew install nginx

# 2. Configure nginx (sudo needed)
cd /Volumes/Orico/Anylab103
sudo ./nginx/setup-nginx.sh

# 3. Set up SSL (sudo needed)
sudo certbot --nginx -d anylab.dpdns.org
```

## What Changed?

The setup script now:
- ✅ Detects if nginx is already installed (skips installation)
- ✅ Handles Homebrew correctly (doesn't run it as root)
- ✅ Only uses sudo for system-level operations

## Verify Installation

After setup, test:
```bash
# Check nginx is running
nginx -v

# Test configuration
sudo nginx -t

# Test domain access
curl -I https://anylab.dpdns.org
```

## Need Help?

- See detailed fix: `nginx/INSTALL_NGINX_FIX.md
- Full guide: `DOMAIN_SETUP_GUIDE.md`
- Troubleshooting: `nginx/STEP_BY_STEP_SETUP.md`

