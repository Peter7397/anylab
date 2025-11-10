# Fix for Homebrew Nginx Installation Issue

## Problem
Homebrew cannot be run as root (with sudo). The error you saw:
```
Error: Running Homebrew as root is extremely dangerous and no longer supported.
```

## Solution

Install nginx **first without sudo**, then run the setup script with sudo.

### Step 1: Install Nginx (without sudo)

```bash
cd /Volumes/Orico/Anylab103
./nginx/install-nginx-manual.sh
```

Or manually:
```bash
brew install nginx
```

### Step 2: Run Setup Script (with sudo)

After nginx is installed, run the setup script:
```bash
sudo ./nginx/setup-nginx.sh
```

The setup script will now:
- ✅ Skip nginx installation (already done)
- ✅ Configure nginx (requires sudo)
- ✅ Set up SSL certificate (optional)

### Step 3: Set Up SSL Certificate

```bash
sudo certbot --nginx -d anylab.dpdns.org
```

## Why This Happens

Homebrew is designed to run as a regular user and manages its own permissions. Running it as root can cause security issues and permission problems.

## Alternative: Install Certbot Too

If you want to install certbot manually as well:

```bash
# Install certbot (without sudo)
brew install certbot

# Then run setup script
sudo ./nginx/setup-nginx.sh
```

## Quick Reference

```bash
# 1. Install nginx (no sudo)
brew install nginx

# 2. Run setup (with sudo)
cd /Volumes/Orico/Anylab103
sudo ./nginx/setup-nginx.sh

# 3. Set up SSL (with sudo)
sudo certbot --nginx -d anylab.dpdns.org
```

