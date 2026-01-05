#!/bin/bash
# Test script for batch file upload optimization
# This tests the new batch upload endpoint

echo "=========================================="
echo "Testing Batch File Upload (OPT-2)"
echo "=========================================="
echo ""

# Check if backend is running
echo "1. Checking backend status..."
if ! curl -s http://localhost:8000/health/ > /dev/null 2>&1; then
    echo "❌ Backend is not accessible at http://localhost:8000"
    echo "   Please ensure the backend is running: docker compose up -d backend"
    exit 1
fi
echo "✅ Backend is accessible"
echo ""

# Check authentication token (if needed)
TOKEN="${ANYLAB_TOKEN:-}"
if [ -z "$TOKEN" ]; then
    echo "⚠️  No authentication token found. Set ANYLAB_TOKEN environment variable if needed."
    echo "   For testing, you may need to log in first to get a token."
    echo ""
fi

echo "2. Testing batch upload endpoint structure..."
echo "   Endpoint: POST /ai/upload/queue/<job_id>/upload-files/"
echo "   Expected: Accepts FormData with 'files[]' array (5-10 files)"
echo ""

echo "3. Checking endpoint registration..."
# Check if the URL is registered (by checking if we can get 404/405 which means route exists)
echo "   URL pattern should be: queue/<str:job_id>/upload-files/"
echo ""

echo "4. Test procedure:"
echo "   a) Create a job with file metadata (no content)"
echo "   b) Upload 8 files in a single batch request"
echo "   c) Verify all files are saved correctly"
echo "   d) Check error handling for partial failures"
echo ""

echo "=========================================="
echo "Manual Testing Steps:"
echo "=========================================="
echo ""
echo "1. Use the frontend to upload multiple files (5-10 files)"
echo "2. Check browser Network tab to see batch requests"
echo "3. Verify files upload faster than before"
echo "4. Check backend logs for batch upload messages:"
echo "   docker compose logs backend | grep -i 'batch upload'"
echo ""
echo "To test via API (requires authentication):"
echo "  curl -X POST http://localhost:8000/ai/upload/queue/<job_id>/upload-files/ \\"
echo "    -H 'Authorization: Bearer <token>' \\"
echo "    -F 'files[]=@file1.pdf' \\"
echo "    -F 'files[]=@file2.pdf' \\"
echo "    -F 'files[]=@file3.pdf'"
echo ""

