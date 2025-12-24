#!/bin/bash
# Fix nginx startup issues on macOS

echo "🔧 Fixing Nginx Startup Issues"
echo "=============================="
echo ""

# Remove stale PID file
PID_FILE="/opt/homebrew/var/run/nginx.pid"
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE" 2>/dev/null)
    if [ -z "$PID" ] || ! kill -0 "$PID" 2>/dev/null; then
        echo "Removing stale PID file..."
        sudo rm -f "$PID_FILE"
    fi
fi

# Kill any existing nginx processes
echo "Checking for existing nginx processes..."
if pgrep -x nginx > /dev/null; then
    echo "Stopping existing nginx processes..."
    sudo pkill nginx
    sleep 2
fi

# Test nginx configuration
echo ""
echo "Testing nginx configuration..."
if sudo nginx -t; then
    echo "✅ Configuration is valid"
    
    # Start nginx
    echo ""
    echo "Starting nginx..."
    sudo nginx
    
    sleep 2
    
    # Verify nginx is running
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE" 2>/dev/null)" 2>/dev/null; then
        echo "✅ Nginx is running (PID: $(cat "$PID_FILE"))"
    elif pgrep -x nginx > /dev/null; then
        echo "✅ Nginx is running"
    else
        echo "❌ Nginx failed to start"
        echo "Check logs: tail -f /opt/homebrew/var/log/nginx/error.log"
        exit 1
    fi
else
    echo "❌ Configuration test failed"
    exit 1
fi

echo ""
echo "✅ Nginx is ready!"
