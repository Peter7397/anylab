#!/bin/bash
# Script to copy updated nginx config and reload nginx

set -e

NGINX_CONF_DIR="/opt/homebrew/etc/nginx"
SERVERS_DIR="$NGINX_CONF_DIR/servers"
LOG_DIR="/opt/homebrew/var/log/nginx"
SOURCE_CONF="/Volumes/Orico/Anylab103/nginx/anylab.conf"
TARGET_CONF="$SERVERS_DIR/anylab.conf"

echo "=========================================="
echo "Reloading Nginx Configuration"
echo "=========================================="
echo ""

# Create servers directory if it doesn't exist
if [ ! -d "$SERVERS_DIR" ]; then
    echo "Creating servers directory: $SERVERS_DIR"
    sudo mkdir -p "$SERVERS_DIR"
fi

# Create log directory if it doesn't exist
if [ ! -d "$LOG_DIR" ]; then
    echo "Creating log directory: $LOG_DIR"
    sudo mkdir -p "$LOG_DIR"
    sudo chmod 755 "$LOG_DIR"
fi

# Copy updated config
echo "Copying updated config..."
sudo cp "$SOURCE_CONF" "$TARGET_CONF"
echo "✅ Config copied to $TARGET_CONF"
echo ""

# Test nginx configuration
echo "Testing nginx configuration..."
sudo /opt/homebrew/bin/nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Configuration test passed"
    echo ""
    
    # Reload nginx
    echo "Reloading nginx..."
    sudo /opt/homebrew/bin/nginx -s reload
    
    if [ $? -eq 0 ]; then
        echo "✅ Nginx reloaded successfully"
    else
        echo "⚠️  Reload failed, trying restart..."
        sudo brew services restart nginx || sudo /opt/homebrew/bin/nginx
    fi
else
    echo "❌ Configuration test failed!"
    echo "Please check the nginx configuration"
    exit 1
fi

echo ""
echo "=========================================="
echo "Testing endpoints..."
echo "=========================================="

# Test backend
BACKEND_STATUS=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/api/token/ 2>&1)
echo "Backend (port 8000): $BACKEND_STATUS"

# Test frontend manifest
MANIFEST_STATUS=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:3000/manifest.json 2>&1)
echo "Frontend manifest.json: $MANIFEST_STATUS"

# Test through nginx
echo ""
echo "Testing through nginx (may take a moment)..."
sleep 2
NGINX_API_STATUS=$(curl -s -o /dev/null -w '%{http_code}' https://anylab.dpdns.org/api/token/ 2>&1 || echo "000")
echo "Nginx → API: $NGINX_API_STATUS"

NGINX_MANIFEST_STATUS=$(curl -s -o /dev/null -w '%{http_code}' https://anylab.dpdns.org/manifest.json 2>&1 || echo "000")
echo "Nginx → manifest.json: $NGINX_MANIFEST_STATUS"

echo ""
echo "=========================================="
echo "Done! Try logging in at: https://anylab.dpdns.org"
echo "=========================================="

