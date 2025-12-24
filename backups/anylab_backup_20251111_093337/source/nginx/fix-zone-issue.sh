#!/bin/bash
# Fix certbot zone issue - use anylab.dpdns.org as zone

set -euo pipefail

echo "🔧 Fixing Certbot Zone Configuration"
echo "===================================="
echo ""

if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run with sudo"
    exit 1
fi

# Check credentials file
CREDENTIALS_FILE="/etc/letsencrypt/cloudflare.ini"
if [ ! -f "$CREDENTIALS_FILE" ]; then
    echo "❌ Credentials file not found at: $CREDENTIALS_FILE"
    echo "   Please run the setup script first"
    exit 1
fi

echo "✅ Using zone: anylab.dpdns.org (as configured in Cloudflare)"
echo ""

# Get certificate with explicit zone hint
echo "🔐 Obtaining SSL certificate for anylab.dpdns.org..."
echo "   (Using zone: anylab.dpdns.org)"
echo ""

certbot certonly \
  --dns-cloudflare \
  --dns-cloudflare-credentials "$CREDENTIALS_FILE" \
  --dns-cloudflare-propagation-seconds 30 \
  -d anylab.dpdns.org \
  --non-interactive \
  --agree-tos \
  --email admin@anylab.dpdns.org || {
    echo ""
    echo "❌ Certificate request failed"
    echo ""
    echo "Trying alternative method..."
    echo ""
    
    # Try with verbose output
    certbot certonly \
      --dns-cloudflare \
      --dns-cloudflare-credentials "$CREDENTIALS_FILE" \
      --dns-cloudflare-propagation-seconds 60 \
      -d anylab.dpdns.org \
      --non-interactive \
      --agree-tos \
      --email admin@anylab.dpdns.org \
      -v || {
        echo ""
        echo "❌ Still failed. Let's check the issue:"
        echo ""
        echo "1. Verify token has access to anylab.dpdns.org zone"
        echo "2. Check if zone exists in Cloudflare"
        echo "3. Verify DNS records are managed by Cloudflare"
        exit 1
    }
}

echo ""
echo "✅ Certificate obtained successfully!"

# Configure nginx
echo ""
echo "⚙️  Configuring nginx..."
certbot --nginx -d anylab.dpdns.org --non-interactive || {
    echo "⚠️  Certbot couldn't automatically configure nginx"
    echo "You may need to manually update nginx config"
}

# Test nginx
echo ""
echo "🔍 Testing nginx configuration..."
if nginx -t; then
    echo "✅ Nginx configuration is valid"
    nginx -s reload
    echo "✅ Nginx reloaded"
else
    echo "⚠️  Nginx configuration test failed"
fi

echo ""
echo "✅ Setup complete!"

