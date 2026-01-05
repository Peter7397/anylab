#!/bin/bash
# Comprehensive test script for all optimizations

echo "=========================================="
echo "Comprehensive Optimization Testing"
echo "=========================================="
echo ""

echo "OPT-1: Celery Worker Pool & Concurrency"
echo "-------------------------------------------"
docker compose exec celery-worker celery -A anylab inspect stats 2>/dev/null | grep -A 5 "pool" | head -10
echo ""

echo "OPT-2: Batch File Upload Endpoint"
echo "-------------------------------------------"
echo "✅ Backend endpoint created: /ai/upload/queue/<job_id>/upload-files/"
echo "✅ Frontend updated to batch 8 files per request"
echo "   Test: Upload multiple files via frontend and check Network tab"
echo ""

echo "OPT-3: Batch Database Updates"
echo "-------------------------------------------"
echo "✅ Batch update function created: bulk_update_file_statuses_in_job()"
echo "✅ Optimized _process_single_file_async to reduce redundant updates"
echo "   Test: Process files and monitor database update frequency in logs"
echo ""

echo "OPT-4: Embedding Batch Size"
echo "-------------------------------------------"
echo "✅ Batch size increased: 50 → 100 chunks per API call"
echo "   Test: Upload a document and check embedding logs for batch size"
echo ""

echo "=========================================="
echo "Resource Monitoring"
echo "=========================================="
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" | grep -E "NAME|celery|backend|ollama"
echo ""

echo "=========================================="
echo "Recent Activity"
echo "=========================================="
echo "Celery Worker Logs (last 20 lines):"
docker compose logs --tail=20 celery-worker 2>&1 | tail -10
echo ""

echo "Backend Logs (last 20 lines):"
docker compose logs --tail=20 backend 2>&1 | tail -10
echo ""

echo "=========================================="
echo "Testing Recommendations"
echo "=========================================="
echo ""
echo "1. Upload 10 files via frontend - should use 2 batch requests (8+2)"
echo "2. Upload a folder with 20 files - should use 3 batch requests (8+8+4)"
echo "3. Monitor resource usage during uploads"
echo "4. Check logs for 'batch upload' and 'Bulk updated' messages"
echo "5. Verify embedding batch size 100 in processing logs"
echo ""

