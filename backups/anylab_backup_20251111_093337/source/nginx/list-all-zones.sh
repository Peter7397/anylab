#!/bin/bash
# List all zones accessible with current token

echo "🔍 Checking All Zones in Cloudflare Account"
echo "==========================================="
echo ""

read -p "Enter your Cloudflare API token: " -s TOKEN
echo ""

echo ""
echo "Fetching zones..."
echo ""

RESPONSE=$(curl -s "https://api.cloudflare.com/client/v4/zones" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json")

echo "All zones in your account:"
echo "------------------------"
echo "$RESPONSE" | python3 -c \
  "import sys, json; \
  data = json.load(sys.stdin); \
  if data.get('success'): \
    zones = data.get('result', []); \
    if zones: \
      print('\n'.join([f\"  {i+1}. {z['name']} (ID: {z['id']})\" for i, z in enumerate(zones)])); \
    else: \
      print('  No zones found'); \
  else: \
    errors = data.get('errors', []); \
    print('Error:', errors[0].get('message', 'Unknown error') if errors else 'Unknown error')" 2>/dev/null

echo ""
echo "Looking for anylab.dpdns.org..."
if echo "$RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); zones = [z['name'] for z in data.get('result', [])]; print('Found!' if 'anylab.dpdns.org' in zones else 'Not found')" 2>/dev/null | grep -q "Found"; then
    echo "✅ anylab.dpdns.org is in your account"
else
    echo "❌ anylab.dpdns.org is NOT accessible with this token"
    echo ""
    echo "This means either:"
    echo "  1. The token was created for a different zone (ppdog.dpdns.org)"
    echo "  2. anylab.dpdns.org needs a separate token"
    echo ""
    echo "Solution: Create a NEW token specifically for anylab.dpdns.org"
fi
