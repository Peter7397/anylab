#!/bin/bash
# Verify what zones the token can access

echo "🔍 Verifying Zone Access"
echo "======================="
echo ""

read -p "Enter your Cloudflare API token: " -s TOKEN
echo ""

echo ""
echo "Checking accessible zones..."
echo ""

RESPONSE=$(curl -s "https://api.cloudflare.com/client/v4/zones" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json")

ZONES=$(echo "$RESPONSE" | python3 -c \
  "import sys, json; \
  data = json.load(sys.stdin); \
  zones = [(z['name'], z['id']) for z in data.get('result', [])]; \
  print('\n'.join([f\"{name}: {zone_id}\" for name, zone_id in zones]))" 2>/dev/null)

if [ -z "$ZONES" ]; then
    echo "❌ No zones found or error accessing API"
    echo ""
    echo "Raw response:"
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null | head -20
else
    echo "✅ Zones accessible with this token:"
    echo "$ZONES"
    echo ""
    
    if echo "$ZONES" | grep -q "anylab.dpdns.org"; then
        echo "✅ anylab.dpdns.org zone is accessible!"
    else
        echo "❌ anylab.dpdns.org zone NOT found"
        echo ""
        echo "Possible reasons:"
        echo "  1. Zone doesn't exist in Cloudflare yet"
        echo "  2. Token was created for different zone"
        echo "  3. Zone needs to be added to Cloudflare"
    fi
fi
