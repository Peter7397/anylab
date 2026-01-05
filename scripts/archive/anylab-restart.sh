#!/bin/bash
# AnyLab Restart Script
# Restarts all services

set -euo pipefail

echo "🔄 Restarting AnyLab System"
echo "======================================"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Stop everything
echo "Stopping services..."
./anylab-stop.sh

echo ""
echo "Waiting 3 seconds..."
sleep 3
echo ""

# Start everything
echo "Starting services..."
./anylab-start.sh

