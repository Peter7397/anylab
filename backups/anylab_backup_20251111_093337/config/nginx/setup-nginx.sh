#!/bin/bash
# Setup script for nginx reverse proxy for AnyLab
# This script installs nginx and configures it for anylab.dpdns.org

set -euo pipefail

echo "🔧 Setting up Nginx reverse proxy for AnyLab..."
echo "=============================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Step 1: Install nginx (without sudo for Homebrew)
echo "📦 Step 1: Installing nginx..."
if command -v nginx &> /dev/null; then
    echo "✅ Nginx is already installed"
else
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS - Homebrew doesn't need sudo
        if command -v brew &> /dev/null; then
            echo "   Installing nginx with Homebrew (no sudo needed)..."
            # Run as current user, not root
            if [ "$EUID" -eq 0 ]; then
                echo "⚠️  Running as root. Switching to current user for Homebrew..."
                sudo -u "$SUDO_USER" brew install nginx || {
                    echo "❌ Failed to install nginx. Please run: brew install nginx"
                    exit 1
                }
            else
                brew install nginx || {
                    echo "❌ Failed to install nginx. Please run: brew install nginx"
                    exit 1
                }
            fi
        else
            echo "❌ Homebrew not found. Please install Homebrew first."
            echo "   Or install nginx manually: brew install nginx"
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux - uses system package manager (requires sudo)
        if command -v apt-get &> /dev/null; then
            apt-get update
            apt-get install -y nginx
        elif command -v yum &> /dev/null; then
            yum install -y nginx
        else
            echo "❌ Package manager not found. Please install nginx manually."
            exit 1
        fi
    else
        echo "❌ Unsupported OS. Please install nginx manually."
        exit 1
    fi
fi

# Step 2: Copy nginx configuration
echo ""
echo "📝 Step 2: Installing nginx configuration..."
NGINX_CONF="$PROJECT_DIR/nginx/anylab.conf"
NGINX_SITES_AVAILABLE="/etc/nginx/sites-available/anylab"
NGINX_SITES_ENABLED="/etc/nginx/sites-enabled/anylab"

# Create sites-available and sites-enabled directories if they don't exist
mkdir -p /etc/nginx/sites-available
mkdir -p /etc/nginx/sites-enabled

# Copy configuration file
cp "$NGINX_CONF" "$NGINX_SITES_AVAILABLE"

# Create symlink if it doesn't exist
if [ ! -L "$NGINX_SITES_ENABLED" ]; then
    ln -s "$NGINX_SITES_AVAILABLE" "$NGINX_SITES_ENABLED"
fi

# Remove default nginx site if it exists
if [ -L /etc/nginx/sites-enabled/default ]; then
    rm /etc/nginx/sites-enabled/default
fi

# Step 3: Test nginx configuration
echo ""
echo "🔍 Step 3: Testing nginx configuration..."
if nginx -t; then
    echo "✅ Nginx configuration is valid"
else
    echo "❌ Nginx configuration test failed"
    exit 1
fi

# Step 4: Setup SSL certificate with Let's Encrypt
echo ""
echo "🔐 Step 4: Setting up SSL certificate..."
echo "⚠️  Note: SSL certificate setup requires:"
echo "   1. Domain anylab.dpdns.org must point to this server's public IP"
echo "   2. Ports 80 and 443 must be open in firewall"
echo "   3. Certbot must be installed"
echo ""
read -p "Do you want to set up SSL certificate now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Install certbot if not installed
    if ! command -v certbot &> /dev/null; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # Homebrew doesn't need sudo
            if [ "$EUID" -eq 0 ]; then
                sudo -u "$SUDO_USER" brew install certbot || {
                    echo "⚠️  Failed to install certbot. Please run: brew install certbot"
                }
            else
                brew install certbot || {
                    echo "⚠️  Failed to install certbot. Please run: brew install certbot"
                }
            fi
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            if command -v apt-get &> /dev/null; then
                apt-get install -y certbot python3-certbot-nginx
            elif command -v yum &> /dev/null; then
                yum install -y certbot python3-certbot-nginx
            fi
        fi
    fi
    
    # Temporarily modify nginx config for certbot (remove SSL directives)
    echo "📝 Creating temporary nginx config for certificate validation..."
    TEMP_CONF="/tmp/anylab_temp.conf"
    sed 's/ssl_certificate/#ssl_certificate/g; s/ssl_certificate_key/#ssl_certificate_key/g; s/ssl_protocols/#ssl_protocols/g; s/ssl_ciphers/#ssl_ciphers/g; s/ssl_prefer_server_ciphers/#ssl_prefer_server_ciphers/g; s/ssl_session_cache/#ssl_session_cache/g; s/ssl_session_timeout/#ssl_session_timeout/g' "$NGINX_SITES_AVAILABLE" > "$TEMP_CONF"
    mv "$TEMP_CONF" "$NGINX_SITES_AVAILABLE"
    
    # Reload nginx (only if it's running)
    if [ -f "/opt/homebrew/var/run/nginx.pid" ] && kill -0 "$(cat /opt/homebrew/var/run/nginx.pid 2>/dev/null)" 2>/dev/null; then
        nginx -s reload 2>/dev/null || echo "⚠️  Nginx not running yet, will start after certbot"
    elif systemctl is-active --quiet nginx 2>/dev/null; then
        systemctl reload nginx 2>/dev/null || echo "⚠️  Could not reload nginx"
    else
        echo "⚠️  Nginx not running yet, will start after certbot"
    fi
    
    # Fix certbot nginx path for Homebrew
    if [[ "$OSTYPE" == "darwin"* ]]; then
        HOMEBREW_NGINX_CONF="/opt/homebrew/etc/nginx/nginx.conf"
        LOCAL_NGINX_CONF="/usr/local/etc/nginx/nginx.conf"
        
        if [ -f "$HOMEBREW_NGINX_CONF" ] && [ ! -f "$LOCAL_NGINX_CONF" ]; then
            echo "   Fixing certbot nginx path for Homebrew..."
            mkdir -p /usr/local/etc/nginx
            ln -sf "$HOMEBREW_NGINX_CONF" "$LOCAL_NGINX_CONF"
            echo "   ✅ Created symlink for certbot compatibility"
        fi
    fi
    
    # Run certbot
    echo "🔐 Running certbot..."
    if [[ "$OSTYPE" == "darwin"* ]] && [ -f "/opt/homebrew/etc/nginx/nginx.conf" ]; then
        # Use explicit path for Homebrew
        certbot --nginx --nginx-server-root /opt/homebrew/etc/nginx -d anylab.dpdns.org --non-interactive --agree-tos --email admin@anylab.dpdns.org || {
            echo "⚠️  Certbot failed. You may need to:"
            echo "   1. Ensure domain points to this server"
            echo "   2. Open ports 80 and 443 in firewall"
            echo "   3. Run manually: sudo certbot --nginx --nginx-server-root /opt/homebrew/etc/nginx -d anylab.dpdns.org"
        }
    else
        certbot --nginx -d anylab.dpdns.org --non-interactive --agree-tos --email admin@anylab.dpdns.org || {
            echo "⚠️  Certbot failed. You may need to:"
            echo "   1. Ensure domain points to this server"
            echo "   2. Open ports 80 and 443 in firewall"
            echo "   3. Run manually: sudo certbot --nginx -d anylab.dpdns.org"
        }
    fi
    
    # Restore full config
    cp "$PROJECT_DIR/nginx/anylab.conf" "$NGINX_SITES_AVAILABLE"
    nginx -t && nginx -s reload
fi

# Step 5: Start/restart nginx
echo ""
echo "🚀 Step 5: Starting nginx..."

# Determine nginx path and PID file location
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS with Homebrew
    NGINX_PID_FILE="/opt/homebrew/var/run/nginx.pid"
    NGINX_BIN=$(which nginx)
else
    # Linux
    NGINX_PID_FILE="/var/run/nginx.pid"
    NGINX_BIN=$(which nginx)
fi

# Check if nginx is already running
if [ -f "$NGINX_PID_FILE" ] && kill -0 "$(cat "$NGINX_PID_FILE" 2>/dev/null)" 2>/dev/null; then
    echo "   Nginx is already running, reloading..."
    if nginx -s reload 2>/dev/null; then
        echo "✅ Nginx reloaded"
    else
        echo "⚠️  Failed to reload nginx, trying restart..."
        # Kill existing process
        kill "$(cat "$NGINX_PID_FILE" 2>/dev/null)" 2>/dev/null
        sleep 1
        # Start fresh
        if [ -f "$NGINX_BIN" ]; then
            $NGINX_BIN
            sleep 2
            if [ -f "$NGINX_PID_FILE" ] && kill -0 "$(cat "$NGINX_PID_FILE" 2>/dev/null)" 2>/dev/null; then
                echo "✅ Nginx restarted"
            else
                echo "❌ Failed to start nginx"
                echo "   Try manually: sudo nginx"
                exit 1
            fi
        else
            echo "❌ Nginx binary not found"
            exit 1
        fi
    fi
elif pgrep -x nginx > /dev/null 2>&1; then
    # Nginx is running but PID file is missing/corrupt
    echo "   Nginx process found but PID file is invalid, restarting..."
    pkill nginx 2>/dev/null
    sleep 2
    # Remove invalid PID file
    rm -f "$NGINX_PID_FILE"
    # Start nginx
    if [ -f "$NGINX_BIN" ]; then
        $NGINX_BIN
        sleep 2
        if [ -f "$NGINX_PID_FILE" ] && kill -0 "$(cat "$NGINX_PID_FILE" 2>/dev/null)" 2>/dev/null; then
            echo "✅ Nginx started"
        else
            echo "❌ Failed to start nginx"
            echo "   Try manually: sudo nginx"
            exit 1
        fi
    else
        echo "❌ Nginx binary not found"
        exit 1
    fi
else
    # Nginx is not running, start it
    echo "   Starting nginx..."
    # Remove any stale PID file
    rm -f "$NGINX_PID_FILE"
    
    if systemctl start nginx 2>/dev/null; then
        # Linux with systemd
        sleep 2
        if systemctl is-active --quiet nginx 2>/dev/null; then
            echo "✅ Nginx started"
        else
            echo "❌ Failed to start nginx with systemctl"
            exit 1
        fi
    elif [ -f "$NGINX_BIN" ]; then
        # macOS or Linux without systemd
        $NGINX_BIN
        sleep 2
        if [ -f "$NGINX_PID_FILE" ] && kill -0 "$(cat "$NGINX_PID_FILE" 2>/dev/null)" 2>/dev/null; then
            echo "✅ Nginx started"
        else
            echo "❌ Failed to start nginx"
            echo "   Try manually: sudo nginx"
            echo "   Check logs: tail -f /opt/homebrew/var/log/nginx/error.log"
            exit 1
        fi
    else
        echo "❌ Nginx binary not found at: $NGINX_BIN"
        exit 1
    fi
fi

# Step 6: Enable nginx on boot
echo ""
echo "⚙️  Step 6: Enabling nginx on boot..."
if systemctl enable nginx 2>/dev/null; then
    echo "✅ Nginx enabled on boot"
else
    echo "⚠️  Could not enable nginx on boot (may not be needed on macOS)"
fi

echo ""
echo "✅ Nginx setup complete!"
echo ""
echo "📍 Access your application at:"
echo "   - HTTP:  http://anylab.dpdns.org (redirects to HTTPS)"
echo "   - HTTPS: https://anylab.dpdns.org"
echo ""
echo "📋 Next steps:"
echo "   1. Ensure domain anylab.dpdns.org points to this server's public IP"
echo "   2. Open ports 80 and 443 in your firewall/router"
echo "   3. If SSL not set up, run: certbot --nginx -d anylab.dpdns.org"
echo "   4. Check nginx logs: tail -f /var/log/nginx/anylab_error.log"
echo ""

