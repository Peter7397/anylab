#!/bin/bash
# Quick script to update Cloudflare token in credentials file

if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run with sudo"
    exit 1
fi

CREDENTIALS_FILE="/etc/letsencrypt/cloudflare.ini"

echo "🔧 Update Cloudflare API Token"
echo "=============================="
echo ""

# Backup existing file
if [ -f "$CREDENTIALS_FILE" ]; then
    echo "📦 Backing up existing credentials..."
    cp "$CREDENTIALS_FILE" "${CREDENTIALS_FILE}.backup"
    echo "✅ Backup created: ${CREDENTIALS_FILE}.backup"
fi

echo ""
echo "Enter your NEW Cloudflare API token for anylab.dpdns.org:"
read -s NEW_TOKEN
echo ""

if [ -z "$NEW_TOKEN" ]; then
    echo "❌ Token cannot be empty"
    exit 1
fi

# Update credentials file
echo "dns_cloudflare_api_token = $NEW_TOKEN" > "$CREDENTIALS_FILE"
chmod 600 "$CREDENTIALS_FILE"

echo ""
echo "✅ Credentials file updated!"
echo ""
echo "🔍 Verifying token access..."
echo ""

# Test token
RESPONSE=$(curl -s "https://api.cloudflare.com/client/v4/zones" \
  -H "Authorization: Bearer $NEW_TOKEN" \
  -H "Content-Type: application/json")

ZONES=$(echo "$RESPONSE" | python3 -c \
  "import sys, json; \
  data = json.load(sys.stdin); \
  zones = [z['name'] for z in data.get('result', [])]; \
  print(' '.join(zones))" 2>/dev/null)

if echo "$ZONES" | grep -q "anylab.dpdns.org"; then
    echo "✅ Token can access anylab.dpdns.org zone!"
    echo ""
    echo "🚀 Ready to get certificate. Run:"
    echo "   sudo ./nginx/fix-zone-issue.sh"
else
    echo "⚠️  Token still can't access anylab.dpdns.org"
    echo "Available zones: $ZONES"
    echo ""
    echo "Please verify:"
    echo "  1. Token was created for anylab.dpdns.org zone"
    echo "  2. Token has Zone Read + DNS Edit permissions"
    echo "  3. anylab.dpdns.org zone exists in Cloudflare"
fi
