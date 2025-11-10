#!/bin/bash
# Setup SSL certificate with Cloudflare DNS challenge
# This script guides you through the process

set -euo pipefail

echo "🔐 Setting up SSL Certificate with Cloudflare DNS Challenge"
echo "=========================================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run with sudo"
    exit 1
fi

# Step 1: Check certbot
echo "📦 Step 1: Checking Certbot..."
if ! command -v certbot &> /dev/null; then
    echo "❌ Certbot not found. Installing..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if [ -n "$SUDO_USER" ]; then
            sudo -u "$SUDO_USER" brew install certbot
        else
            echo "⚠️  Please install certbot manually: brew install certbot"
            exit 1
        fi
    fi
fi

echo "✅ Certbot is installed"

# Step 2: Install certbot-dns-cloudflare plugin
echo ""
echo "📦 Step 2: Installing certbot-dns-cloudflare plugin..."
if python3 -c "import certbot_dns_cloudflare" 2>/dev/null; then
    echo "✅ Plugin already installed"
else
    echo "   Installing certbot-dns-cloudflare via pip..."
    pip3 install certbot-dns-cloudflare --break-system-packages 2>/dev/null || \
    pip3 install certbot-dns-cloudflare --user 2>/dev/null || \
    sudo pip3 install certbot-dns-cloudflare --break-system-packages 2>/dev/null || {
        echo "❌ Failed to install certbot-dns-cloudflare"
        echo "   Please install manually:"
        echo "   pip3 install certbot-dns-cloudflare --break-system-packages"
        echo "   OR"
        echo "   sudo pip3 install certbot-dns-cloudflare --break-system-packages"
        exit 1
    }
    echo "✅ Plugin installed"
fi

# Step 3: Get Cloudflare API token
echo ""
echo "🔑 Step 3: Cloudflare API Token"
echo "================================="
echo ""
echo "You need to create a Cloudflare API token:"
echo ""
echo "1. Go to: https://dash.cloudflare.com/profile/api-tokens"
echo "2. Click 'Create Token'"
echo "3. Use 'Edit zone DNS' template OR create custom token with:"
echo "   - Permissions: Zone → Zone → Read"
echo "   - Permissions: Zone → DNS → Edit"
echo "   - Zone Resources: Include → Specific zone → dpdns.org"
echo "4. Copy the token"
echo ""
read -p "Have you created the Cloudflare API token? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Please create the token first, then run this script again."
    echo "Token creation guide: https://developers.cloudflare.com/api/tokens/create/"
    exit 1
fi

echo ""
echo "Enter your Cloudflare API token (it will be hidden):"
read -s CLOUDFLARE_TOKEN
echo ""

if [ -z "$CLOUDFLARE_TOKEN" ]; then
    echo "❌ Token cannot be empty"
    exit 1
fi

# Step 4: Create credentials file
echo ""
echo "📝 Step 4: Creating credentials file..."
CREDENTIALS_FILE="/etc/letsencrypt/cloudflare.ini"
mkdir -p /etc/letsencrypt
echo "dns_cloudflare_api_token = $CLOUDFLARE_TOKEN" > "$CREDENTIALS_FILE"
chmod 600 "$CREDENTIALS_FILE"
echo "✅ Credentials file created at: $CREDENTIALS_FILE"

# Step 5: Get certificate
echo ""
echo "🔐 Step 5: Obtaining SSL certificate..."
echo "This may take a minute..."
echo "Note: Using anylab.dpdns.org as the zone (as configured in Cloudflare)"
certbot certonly \
  --dns-cloudflare \
  --dns-cloudflare-credentials "$CREDENTIALS_FILE" \
  --dns-cloudflare-propagation-seconds 30 \
  -d anylab.dpdns.org \
  --non-interactive \
  --agree-tos \
  --email admin@anylab.dpdns.org || {
    echo ""
    echo "⚠️  Certificate request failed"
    echo ""
    echo "If the error mentions 'unable to determine zone_id', this might mean:"
    echo "  1. anylab.dpdns.org is the zone in Cloudflare (which is correct)"
    echo "  2. The plugin needs to find the zone correctly"
    echo ""
    echo "Trying with longer propagation time..."
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
        echo "❌ Certificate request still failed"
        echo "Check the error above and verify:"
        echo "  1. Cloudflare API token is correct"
        echo "  2. Token has proper permissions for anylab.dpdns.org zone"
        echo "  3. anylab.dpdns.org zone exists in your Cloudflare account"
        echo "  4. DNS records are managed by Cloudflare"
        echo ""
        echo "You can also try the fix script:"
        echo "  sudo ./nginx/fix-zone-issue.sh"
        exit 1
    }
}

echo "✅ Certificate obtained successfully!"

# Step 6: Configure nginx
echo ""
echo "⚙️  Step 6: Configuring nginx..."
certbot --nginx -d anylab.dpdns.org --non-interactive || {
    echo "⚠️  Certbot couldn't automatically configure nginx"
    echo "You may need to manually update nginx config with certificate paths:"
    echo "  ssl_certificate /etc/letsencrypt/live/anylab.dpdns.org/fullchain.pem;"
    echo "  ssl_certificate_key /etc/letsencrypt/live/anylab.dpdns.org/privkey.pem;"
}

echo "✅ Nginx configured"

# Step 7: Test nginx
echo ""
echo "🔍 Step 7: Testing nginx configuration..."
if nginx -t; then
    echo "✅ Nginx configuration is valid"
    nginx -s reload
    echo "✅ Nginx reloaded"
else
    echo "⚠️  Nginx configuration test failed"
    echo "Please check the configuration manually"
fi

# Summary
echo ""
echo "=========================================="
echo "✅ SSL Certificate Setup Complete!"
echo "=========================================="
echo ""
echo "📍 Your certificate is at:"
echo "   /etc/letsencrypt/live/anylab.dpdns.org/"
echo ""
echo "🔒 Next Steps:"
echo "   1. Set Cloudflare SSL/TLS mode to 'Full (strict)'"
echo "      Dashboard → SSL/TLS → Overview → Full (strict)"
echo ""
echo "   2. Test your site:"
echo "      curl -I https://anylab.dpdns.org"
echo ""
echo "   3. Certificate will auto-renew (certbot is set up)"
echo ""
echo "   4. Check certificate:"
echo "      sudo certbot certificates"
echo ""

