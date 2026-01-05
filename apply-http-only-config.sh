#!/bin/bash
# Apply HTTP-only nginx config (for Cloudflare Flexible SSL)

set -e

echo "=========================================="
echo "Applying HTTP-only Nginx Configuration"
echo "=========================================="
echo ""
echo "This will use HTTP on the origin server."
echo "Make sure Cloudflare SSL mode is set to 'Flexible'"
echo ""

# Backup current config
BACKUP_FILE="/opt/homebrew/etc/nginx/servers/anylab.conf.backup.$(date +%Y%m%d_%H%M%S)"
if [ -f "/opt/homebrew/etc/nginx/servers/anylab.conf" ]; then
    echo "1. Backing up current config..."
    sudo cp /opt/homebrew/etc/nginx/servers/anylab.conf "$BACKUP_FILE"
    echo "   ✅ Backup saved to: $BACKUP_FILE"
else
    echo "1. No existing config to backup"
fi

# Copy HTTP-only config
echo ""
echo "2. Copying HTTP-only configuration..."
sudo cp /Volumes/Orico/Anylab103/nginx/anylab-http-only.conf /opt/homebrew/etc/nginx/servers/anylab.conf
echo "   ✅ Config copied"

# Test configuration
echo ""
echo "3. Testing nginx configuration..."
if sudo /opt/homebrew/bin/nginx -t; then
    echo "   ✅ Configuration test passed"
else
    echo "   ❌ Configuration test failed"
    exit 1
fi

# Restart nginx
echo ""
echo "4. Restarting nginx..."
sudo /opt/homebrew/bin/nginx -s stop 2>/dev/null || true
sleep 1
sudo /opt/homebrew/bin/nginx
sleep 2

# Verify nginx is running
if ps aux | grep -q "[n]ginx: master process"; then
    echo "   ✅ Nginx is running"
else
    echo "   ❌ Nginx failed to start"
    exit 1
fi

# Test endpoints
echo ""
echo "5. Testing endpoints..."
sleep 2

API_STATUS=$(curl -s -o /dev/null -w '%{http_code}' http://localhost/api/token/ -H "Host: anylab.dpdns.org" 2>&1)
MANIFEST_STATUS=$(curl -s -o /dev/null -w '%{http_code}' http://localhost/manifest.json -H "Host: anylab.dpdns.org" 2>&1)

echo "   API endpoint (local): $API_STATUS"
echo "   Manifest endpoint (local): $MANIFEST_STATUS"

# Check if nginx is listening
if netstat -an | grep -q ":80.*LISTEN"; then
    echo "   ✅ Nginx is listening on port 80"
else
    echo "   ⚠️  Nginx may not be listening on port 80"
fi

echo ""
echo "=========================================="
echo "Done!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Make sure Cloudflare SSL mode is set to 'Flexible'"
echo "2. Test: https://anylab.dpdns.org"
echo ""
echo "To restore HTTPS config later (after setting up SSL):"
echo "  sudo cp $BACKUP_FILE /opt/homebrew/etc/nginx/servers/anylab.conf"
echo "  sudo /opt/homebrew/bin/nginx -s reload"

