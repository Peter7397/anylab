#!/bin/bash
# AnyLab Logs Viewer
# View logs from different services

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📋 AnyLab Logs Viewer"
echo "======================================"
echo ""
echo "Select which logs to view:"
echo ""
echo "  1) Backend (Gunicorn) - Error Log"
echo "  2) Backend (Gunicorn) - Access Log"
echo "  3) Docker Compose Logs (All)"
echo "  4) PostgreSQL Logs"
echo "  5) Neo4j Logs"
echo "  6) Redis Logs"
echo "  7) All Backend Logs (follow mode)"
echo "  8) All Docker Logs (follow mode)"
echo ""
read -p "Enter choice [1-8]: " choice

case $choice in
    1)
        echo -e "${BLUE}Viewing Backend Error Log (Ctrl+C to exit)${NC}"
        echo ""
        tail -f logs/gunicorn-error.log
        ;;
    2)
        echo -e "${BLUE}Viewing Backend Access Log (Ctrl+C to exit)${NC}"
        echo ""
        tail -f logs/gunicorn-access.log
        ;;
    3)
        echo -e "${BLUE}Viewing All Docker Logs (last 50 lines)${NC}"
        echo ""
        docker compose logs --tail=50
        ;;
    4)
        echo -e "${BLUE}Viewing PostgreSQL Logs (last 50 lines)${NC}"
        echo ""
        docker compose logs --tail=50 postgres
        ;;
    5)
        echo -e "${BLUE}Viewing Neo4j Logs (last 50 lines)${NC}"
        echo ""
        docker compose logs --tail=50 neo4j
        ;;
    6)
        echo -e "${BLUE}Viewing Redis Logs (last 50 lines)${NC}"
        echo ""
        docker compose logs --tail=50 redis
        ;;
    7)
        echo -e "${BLUE}Following All Backend Logs (Ctrl+C to exit)${NC}"
        echo ""
        tail -f logs/gunicorn-error.log logs/gunicorn-access.log
        ;;
    8)
        echo -e "${BLUE}Following All Docker Logs (Ctrl+C to exit)${NC}"
        echo ""
        docker compose logs -f
        ;;
    *)
        echo -e "${YELLOW}Invalid choice${NC}"
        exit 1
        ;;
esac

