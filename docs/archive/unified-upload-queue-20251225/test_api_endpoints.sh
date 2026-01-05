#!/bin/bash
# API Endpoint Testing Script for Upload Queue System
# 
# Prerequisites:
# 1. Server running on http://localhost:8000
# 2. Get auth token first (replace YOUR_TOKEN below)
# 3. Run: chmod +x test_api_endpoints.sh && ./test_api_endpoints.sh

BASE_URL="http://localhost:8000/api/ai/upload"
TOKEN="YOUR_TOKEN_HERE"  # Replace with actual token

echo "=========================================="
echo "Upload Queue API Endpoint Tests"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Create Upload Job (POST)
echo -e "${YELLOW}Test 1: Create Upload Job${NC}"
echo "POST $BASE_URL/queue/"
response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/queue/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "job_type": "file",
    "source": "/test/path",
    "files": [{"name": "test.pdf", "size": 1024}],
    "priority": 5,
    "metadata": {"test": "data"}
  }')

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" -eq 200 ] || [ "$http_code" -eq 201 ]; then
    echo -e "${GREEN}✓ PASSED${NC} - HTTP $http_code"
    JOB_ID=$(echo "$body" | grep -o '"job_id":"[^"]*' | cut -d'"' -f4)
    echo "  Job ID: $JOB_ID"
else
    echo -e "${RED}✗ FAILED${NC} - HTTP $http_code"
    echo "  Response: $body"
fi
echo ""

# Test 2: Get Queue Status (GET)
echo -e "${YELLOW}Test 2: Get Queue Status${NC}"
echo "GET $BASE_URL/queue/"
response=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/queue/" \
  -H "Authorization: Bearer $TOKEN")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" -eq 200 ]; then
    echo -e "${GREEN}✓ PASSED${NC} - HTTP $http_code"
    echo "  Response received"
else
    echo -e "${RED}✗ FAILED${NC} - HTTP $http_code"
    echo "  Response: $body"
fi
echo ""

# Test 3: Get Job Detail (if job_id available)
if [ ! -z "$JOB_ID" ]; then
    echo -e "${YELLOW}Test 3: Get Job Detail${NC}"
    echo "GET $BASE_URL/queue/$JOB_ID/"
    response=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/queue/$JOB_ID/" \
      -H "Authorization: Bearer $TOKEN")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -eq 200 ]; then
        echo -e "${GREEN}✓ PASSED${NC} - HTTP $http_code"
        echo "  Job details retrieved"
    else
        echo -e "${RED}✗ FAILED${NC} - HTTP $http_code"
        echo "  Response: $body"
    fi
    echo ""
    
    # Test 4: Pause Job
    echo -e "${YELLOW}Test 4: Pause Job${NC}"
    echo "POST $BASE_URL/queue/$JOB_ID/pause/"
    response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/queue/$JOB_ID/pause/" \
      -H "Authorization: Bearer $TOKEN")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -eq 200 ]; then
        echo -e "${GREEN}✓ PASSED${NC} - HTTP $http_code"
        echo "  Job paused"
    else
        echo -e "${RED}✗ FAILED${NC} - HTTP $http_code"
        echo "  Response: $body"
    fi
    echo ""
    
    # Test 5: Resume Job
    echo -e "${YELLOW}Test 5: Resume Job${NC}"
    echo "POST $BASE_URL/queue/$JOB_ID/resume/"
    response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/queue/$JOB_ID/resume/" \
      -H "Authorization: Bearer $TOKEN")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -eq 200 ]; then
        echo -e "${GREEN}✓ PASSED${NC} - HTTP $http_code"
        echo "  Job resumed"
    else
        echo -e "${RED}✗ FAILED${NC} - HTTP $http_code"
        echo "  Response: $body"
    fi
    echo ""
fi

# Test 6: Get Queue Statistics
echo -e "${YELLOW}Test 6: Get Queue Statistics${NC}"
echo "GET $BASE_URL/queue/stats/"
response=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/queue/stats/" \
  -H "Authorization: Bearer $TOKEN")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" -eq 200 ]; then
    echo -e "${GREEN}✓ PASSED${NC} - HTTP $http_code"
    echo "  Statistics retrieved"
    # Try to parse and show some stats
    echo "$body" | grep -o '"total":[0-9]*' | head -1
else
    echo -e "${RED}✗ FAILED${NC} - HTTP $http_code"
    echo "  Response: $body"
fi
echo ""

echo "=========================================="
echo "API Tests Complete"
echo "=========================================="
echo ""
echo "Note: To test with actual file uploads, use:"
echo "curl -X POST $BASE_URL/queue/ \\"
echo "  -H \"Authorization: Bearer \$TOKEN\" \\"
echo "  -F \"job_type=file\" \\"
echo "  -F \"source=test_upload\" \\"
echo "  -F \"file=@/path/to/file.pdf\""

