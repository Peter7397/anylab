#!/bin/bash
# Manual nginx installation script for macOS
# Run this WITHOUT sudo first, then run setup-nginx.sh with sudo

echo "🔧 Manual Nginx Installation for macOS"
echo "======================================"
echo ""

if [ "$EUID" -eq 0 ]; then
    echo "❌ Please run this script WITHOUT sudo"
    echo "   This script installs nginx using Homebrew"
    exit 1
fi

if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew not found. Please install Homebrew first:"
    echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

echo "📦 Installing nginx..."
brew install nginx

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Nginx installed successfully!"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Run the setup script with sudo:"
    echo "      sudo ./nginx/setup-nginx.sh"
    echo ""
    echo "   2. Then set up SSL:"
    echo "      sudo certbot --nginx -d anylab.dpdns.org"
else
    echo ""
    echo "❌ Failed to install nginx"
    exit 1
fi
