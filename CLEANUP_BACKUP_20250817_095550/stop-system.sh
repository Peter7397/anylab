#!/bin/bash

# OneLab System Stop Script

echo "🛑 Stopping OneLab Backend System..."

# Stop all services
docker compose down

echo "✅ All services stopped"
echo ""
echo "💡 To restart: ./start-system.sh"
