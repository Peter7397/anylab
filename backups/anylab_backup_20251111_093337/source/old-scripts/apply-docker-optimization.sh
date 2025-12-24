#!/bin/bash
# Docker Optimization Implementation Script
# This script helps apply the optimized Docker configuration

set -euo pipefail

echo "🚀 Docker Optimization Implementation"
echo "====================================="
echo ""
echo "This script will:"
echo "  1. Stop current Docker containers"
echo "  2. Apply optimized docker-compose.yml"
echo "  3. Restart containers with new limits"
echo "  4. Verify the optimization"
echo ""
echo "⚠️  IMPORTANT: You still need to manually reduce Docker Desktop memory!"
echo "   Go to: Docker Desktop → Settings → Resources → Memory"
echo "   Change from 11.67 GB to 4 GB"
echo ""

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found!"
    echo "   Please run this script from /Volumes/Orico/Anylab103"
    exit 1
fi

# Check if optimized file exists
if [ ! -f "docker-compose.optimized.yml" ]; then
    echo "❌ Error: docker-compose.optimized.yml not found!"
    echo "   Please ensure the optimized configuration was generated."
    exit 1
fi

# Ask for confirmation
read -p "⚠️  Do you want to proceed? (yes/no): " -r
echo
if [[ ! $REPLY =~ ^[Yy](es)?$ ]]; then
    echo "❌ Optimization cancelled."
    exit 0
fi

echo ""
echo "📝 Step 1: Creating backup..."
echo "----------------------------------------"

# Create timestamped backup
BACKUP_FILE="docker-compose.yml.backup-$(date +%Y%m%d-%H%M%S)"
cp docker-compose.yml "$BACKUP_FILE"
echo "✅ Backup created: $BACKUP_FILE"

echo ""
echo "🛑 Step 2: Stopping current containers..."
echo "----------------------------------------"

docker-compose down
echo "✅ Containers stopped"

echo ""
echo "📋 Step 3: Applying optimized configuration..."
echo "----------------------------------------"

# Show differences
echo "Changes being applied:"
echo ""
diff -u docker-compose.yml docker-compose.optimized.yml | head -50 || true
echo ""
echo "(showing first 50 lines of changes)"
echo ""

# Apply optimized config
cp docker-compose.optimized.yml docker-compose.yml
echo "✅ Optimized configuration applied"

echo ""
echo "🚀 Step 4: Starting containers with new limits..."
echo "----------------------------------------"

docker-compose up -d

echo "✅ Containers started"
echo ""
echo "⏳ Waiting 30 seconds for containers to initialize..."
sleep 30

echo ""
echo "🔍 Step 5: Checking container status..."
echo "----------------------------------------"

docker-compose ps
echo ""

echo "📊 Step 6: Checking memory usage..."
echo "----------------------------------------"

docker stats --no-stream

echo ""
echo "========================================"
echo "✅ OPTIMIZATION APPLIED!"
echo "========================================"
echo ""
echo "📝 NEXT STEPS:"
echo ""
echo "1. ⚠️  MANUALLY reduce Docker Desktop memory:"
echo "   • Open Docker Desktop"
echo "   • Go to Settings → Resources → Memory"
echo "   • Change from 11.67 GB to 4 GB"
echo "   • Click 'Apply & Restart'"
echo "   • Wait for Docker to restart"
echo ""
echo "2. Run verification script:"
echo "   ./verify-docker-optimization.sh"
echo ""
echo "3. Test your backend application:"
echo "   • Start the backend server"
echo "   • Try logging in"
echo "   • Verify all features work"
echo ""
echo "4. Monitor memory usage for 24 hours:"
echo "   docker stats"
echo ""
echo "📄 See DOCKER_OPTIMIZATION_GUIDE.md for detailed information"
echo ""
echo "🔄 To rollback if needed:"
echo "   docker-compose down"
echo "   cp $BACKUP_FILE docker-compose.yml"
echo "   docker-compose up -d"
echo ""

