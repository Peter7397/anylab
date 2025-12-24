#!/bin/bash
# Prerequisites verification script for nginx setup
# This script checks if everything is ready for domain setup

echo "🔍 Verifying Prerequisites for Domain Setup"
echo "=========================================="
echo ""

ERRORS=0
WARNINGS=0

# Check 1: DNS Configuration
echo "1️⃣  Checking DNS Configuration..."
DNS_RESULT=$(nslookup anylab.dpdns.org 2>&1 | grep -i "address" | tail -1)
if [ -z "$DNS_RESULT" ]; then
    echo "   ❌ DNS not configured - anylab.dpdns.org does not resolve"
    echo "      Please configure DNS A record to point to your server's public IP"
    ERRORS=$((ERRORS + 1))
else
    echo "   ✅ DNS resolves: $DNS_RESULT"
fi

# Check 2: Homebrew (for macOS)
echo ""
echo "2️⃣  Checking Homebrew..."
if command -v brew &> /dev/null; then
    echo "   ✅ Homebrew is installed"
else
    echo "   ❌ Homebrew not found"
    echo "      Install from: https://brew.sh"
    ERRORS=$((ERRORS + 1))
fi

# Check 3: Nginx
echo ""
echo "3️⃣  Checking Nginx..."
if command -v nginx &> /dev/null; then
    NGINX_VERSION=$(nginx -v 2>&1)
    echo "   ✅ Nginx is installed: $NGINX_VERSION"
else
    echo "   ⚠️  Nginx not installed (will be installed by setup script)"
    WARNINGS=$((WARNINGS + 1))
fi

# Check 4: Certbot
echo ""
echo "4️⃣  Checking Certbot..."
if command -v certbot &> /dev/null; then
    CERTBOT_VERSION=$(certbot --version 2>&1)
    echo "   ✅ Certbot is installed: $CERTBOT_VERSION"
else
    echo "   ⚠️  Certbot not installed (will be installed by setup script)"
    WARNINGS=$((WARNINGS + 1))
fi

# Check 5: Port availability
echo ""
echo "5️⃣  Checking Port Availability..."
if lsof -i :80 -sTCP:LISTEN >/dev/null 2>&1; then
    PROCESS=$(lsof -i :80 -sTCP:LISTEN | tail -1 | awk '{print $1}')
    echo "   ⚠️  Port 80 is in use by: $PROCESS"
    echo "      You may need to stop this service or configure nginx differently"
    WARNINGS=$((WARNINGS + 1))
else
    echo "   ✅ Port 80 is available"
fi

if lsof -i :443 -sTCP:LISTEN >/dev/null 2>&1; then
    PROCESS=$(lsof -i :443 -sTCP:LISTEN | tail -1 | awk '{print $1}')
    echo "   ⚠️  Port 443 is in use by: $PROCESS"
    echo "      You may need to stop this service or configure nginx differently"
    WARNINGS=$((WARNINGS + 1))
else
    echo "   ✅ Port 443 is available"
fi

# Check 6: Application Services
echo ""
echo "6️⃣  Checking Application Services..."
if lsof -i :8001 -sTCP:LISTEN >/dev/null 2>&1; then
    echo "   ✅ Backend (Django) is running on port 8001"
else
    echo "   ❌ Backend (Django) is not running on port 8001"
    echo "      Please start the backend first"
    ERRORS=$((ERRORS + 1))
fi

if lsof -i :3000 -sTCP:LISTEN >/dev/null 2>&1; then
    echo "   ✅ Frontend (React) is running on port 3000"
else
    echo "   ❌ Frontend (React) is not running on port 3000"
    echo "      Please start the frontend first"
    ERRORS=$((ERRORS + 1))
fi

# Check 7: Docker Services
echo ""
echo "7️⃣  Checking Docker Services..."
if docker ps --filter "name=anylab_postgres" --format "{{.Names}}" | grep -q "anylab_postgres"; then
    echo "   ✅ PostgreSQL container is running"
else
    echo "   ❌ PostgreSQL container is not running"
    echo "      Run: docker compose up -d postgres"
    ERRORS=$((ERRORS + 1))
fi

if docker ps --filter "name=anylab_redis" --format "{{.Names}}" | grep -q "anylab_redis"; then
    echo "   ✅ Redis container is running"
else
    echo "   ❌ Redis container is not running"
    echo "      Run: docker compose up -d redis"
    ERRORS=$((ERRORS + 1))
fi

# Check 8: Configuration Files
echo ""
echo "8️⃣  Checking Configuration Files..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/anylab.conf" ]; then
    echo "   ✅ Nginx configuration file exists"
else
    echo "   ❌ Nginx configuration file not found"
    ERRORS=$((ERRORS + 1))
fi

if [ -f "$SCRIPT_DIR/setup-nginx.sh" ]; then
    echo "   ✅ Setup script exists"
else
    echo "   ❌ Setup script not found"
    ERRORS=$((ERRORS + 1))
fi

# Summary
echo ""
echo "=========================================="
echo "📊 Summary"
echo "=========================================="
if [ $ERRORS -eq 0 ]; then
    echo "✅ All critical checks passed!"
    if [ $WARNINGS -gt 0 ]; then
        echo "⚠️  $WARNINGS warning(s) - see above"
    fi
    echo ""
    echo "🚀 You're ready to run the setup script:"
    echo "   sudo ./nginx/setup-nginx.sh"
    exit 0
else
    echo "❌ $ERRORS error(s) found - please fix these before proceeding"
    if [ $WARNINGS -gt 0 ]; then
        echo "⚠️  $WARNINGS warning(s) - see above"
    fi
    echo ""
    echo "Please address the errors above before running the setup script."
    exit 1
fi

