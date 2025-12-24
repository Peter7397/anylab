#!/bin/bash
# Fix certbot to use correct nginx path for Homebrew

echo "🔧 Fixing Certbot Nginx Path"
echo "============================"
echo ""

# Find nginx config path
NGINX_CONF=$(nginx -t 2>&1 | grep "configuration file" | awk '{print $NF}' | tr -d '.')

if [ -z "$NGINX_CONF" ]; then
    # Try common locations
    if [ -f "/opt/homebrew/etc/nginx/nginx.conf" ]; then
        NGINX_CONF="/opt/homebrew/etc/nginx/nginx.conf"
    elif [ -f "/usr/local/etc/nginx/nginx.conf" ]; then
        NGINX_CONF="/usr/local/etc/nginx/nginx.conf"
    else
        echo "❌ Could not find nginx.conf"
        echo "Please find it manually: find /opt/homebrew /usr/local -name nginx.conf 2>/dev/null"
        exit 1
    fi
fi

echo "Found nginx.conf at: $NGINX_CONF"
echo ""

# Create symlink if needed
if [ ! -f "/usr/local/etc/nginx/nginx.conf" ] && [ "$NGINX_CONF" != "/usr/local/etc/nginx/nginx.conf" ]; then
    echo "Creating symlink for certbot compatibility..."
    sudo mkdir -p /usr/local/etc/nginx
    sudo ln -sf "$NGINX_CONF" /usr/local/etc/nginx/nginx.conf
    echo "✅ Symlink created"
fi

# Also check if nginx binary path needs fixing
NGINX_BIN=$(which nginx)
echo "Nginx binary: $NGINX_BIN"
echo ""

# Test nginx
echo "Testing nginx configuration..."
sudo nginx -t

echo ""
echo "✅ Fixed! Now try:"
echo "   sudo certbot --nginx -d anylab.dpdns.org"
