#!/bin/bash
# Test script to verify upload queue immediate response time

echo "=== Upload Queue Speed Test ==="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Check backend logs for timing
echo -e "${YELLOW}Test 1: Monitoring backend logs for upload requests...${NC}"
echo "Watch for 'create_upload_job' entries and timing"
echo ""
echo "Press Ctrl+C to stop monitoring"
echo ""

docker logs -f anylab_backend 2>&1 | grep --line-buffered -E "create_upload_job|UPLOAD START|Reading file|Saving file|Created upload job|job_id" | while read line; do
    timestamp=$(date '+%H:%M:%S')
    echo "[$timestamp] $line"
done

