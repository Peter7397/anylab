# AnyLab0812 - Testing Guide

## Date: October 26, 2025

### Overview
This guide provides instructions for testing the AnyLab0812 RAG system to verify all functionality works correctly.

---

## ✅ Completed Implementation Tasks

### 1. Adaptive Query Expansion ✅
**Status**: Implemented
**Files Modified**:
- `backend/ai_assistant/hybrid_search.py` - Added `should_expand_query()` logic
- `backend/ai_assistant/advanced_rag_service.py` - Integrated adaptive expansion
- `backend/ai_assistant/comprehensive_rag_service.py` - Integrated adaptive expansion

**Features**:
- Intelligently skips expansion for:
  - Exact phrases (quoted strings)
  - Very specific queries (>8 significant words)
  - Technical terms (version, ip, url, api, id, uuid, hash)
  - Specific patterns ("what is X", "where is X", "when did X")
  
- Expands queries when beneficial:
  - Short queries (<3 words) for better context
  - General queries that need more synonyms
  - Better recall for broad searches

---

## 🧪 Recommended Testing Procedures

### Test 1: Document Upload and Processing

**Steps:**
1. Access frontend at `https://anylab.dpdns.org` or `http://localhost:3000`
2. Navigate to Document Manager
3. Click "Upload Document"
4. Upload a test PDF or text file (sample files in `test_documents/`)
5. Wait for processing to complete

**Expected Results:**
- ✅ Document appears in list
- ✅ Processing completes without errors
- ✅ Chunks are created in database
- ✅ Embeddings are generated
- ✅ File accessible for download

**Verification:**
```bash
# Check database
cd backend
source venv/bin/activate
python manage.py shell -c "from ai_assistant.models import UploadedFile, DocumentChunk; print(f'Files: {UploadedFile.objects.count()}, Chunks: {DocumentChunk.objects.count()}')"

# Verify new document appears
python manage.py shell -c "from ai_assistant.models import UploadedFile; for f in UploadedFile.objects.all()[:5]: print(f.id, f.filename)"
```

---

### Test 2: Basic RAG Search

**Steps:**
1. Navigate to RAG Search interface
2. Select "Basic" or "Enhanced" mode
3. Enter query: "what is a spectrophotometer?"
4. Click search
5. Review results

**Expected Results:**
- ✅ Search completes in 200-500ms
- ✅ Returns relevant documents
- ✅ Shows performance metrics
- ✅ Displays sources with similarity scores

**Verification:**
```bash
# Check backend logs for performance data
tail -f backend/logs/anylab.log | grep "RAG Search Performance"
```

---

### Test 3: Advanced RAG Search (Hybrid + Reranking)

**Steps:**
1. Navigate to RAG Search interface
2. Select "Advanced" mode
3. Enter query: "how to calibrate laboratory equipment"
4. Click search
5. Review results

**Expected Results:**
- ✅ Search completes in 800-1500ms
- ✅ Uses hybrid search (BM25 + Vector)
- ✅ Applies reranking
- ✅ Shows multiple result sources

**Verification:**
- Check response for `"search_method": "hybrid"`
- Verify performance metrics in response
- Confirm reranking applied

---

### Test 4: Comprehensive RAG Search

**Steps:**
1. Navigate to RAG Search interface
2. Select "Comprehensive" mode
3. Enter query: "laboratory safety procedures"
4. Click search
5. Review results

**Expected Results:**
- ✅ Search completes in 1500-3000ms
- ✅ Returns 15 results (maximum detail)
- ✅ Comprehensive context (12k tokens)
- ✅ Multiple perspectives on topic

**Verification:**
- Verify 15 results returned
- Check context length in response
- Confirm comprehensive mode metadata

---

### Test 5: Adaptive Query Expansion

**Test Cases:**

#### Case 1: Query That Should NOT Expand
**Query:** `"what is version 2.5 of the software"`
**Expected:** Query NOT expanded (contains "version", technical term)

#### Case 2: Query That SHOULD Expand
**Query:** `install software`
**Expected:** Query expanded to "install software installation setup configure deploy"

#### Case 3: Short Query That Should Expand
**Query:** `error code`
**Expected:** Query expanded (short query, <3 significant words)

#### Case 4: Specific Query That Should NOT Expand
**Query:** `where is "main control panel" located?`
**Expected:** Query NOT expanded (contains exact phrase in quotes)

**Verification:**
```bash
# Check backend logs
tail -f backend/logs/anylab.log | grep "Query expansion"
tail -f backend/logs/anylab.log | grep "expansion applied"
```

---

### Test 6: Vector Similarity Search

**Steps:**
1. Navigate to RAG Search interface
2. Select "Vector" mode
3. Enter query: "analytical instruments"
4. Click search

**Expected Results:**
- ✅ Returns 5 vector similarity results
- ✅ Shows similarity scores
- ✅ Performance metrics included

**Verification:**
- Verify response includes `similarity` scores
- Check `results_count` matches actual results
- Confirm vector search mode in performance metrics

---

### Test 7: Performance Monitoring

**Steps:**
1. Perform any RAG search
2. Check API response for `performance` object
3. Review performance metrics in logs

**Expected Results:**
- ✅ Response includes `performance` object
- ✅ Contains `search_time_ms` and `total_time_ms`
- ✅ Shows `search_mode` and `top_k`
- ✅ Logs include performance data

**Example Response:**
```json
{
  "data": {
    "response": "...",
    "sources": [...],
    "performance": {
      "search_time_ms": 1234.56,
      "total_time_ms": 1456.78,
      "search_mode": "enhanced",
      "top_k": 8
    }
  }
}
```

---

### Test 8: Cache Performance

**Steps:**
1. Perform same search twice in succession
2. Compare response times
3. Check cache hit rates

**Expected Results:**
- ✅ Second search is faster (cached)
- ✅ Response time reduced by 90%+ for cached queries
- ✅ Logs show cache hit messages

**Verification:**
```bash
# Check cache in Redis (if available)
redis-cli keys "embedding_*" | head -5
redis-cli keys "*_search_*" | head -5
```

---

## 📊 Performance Benchmarks

### Expected Performance Times

| Search Mode | Expected Time | Results | Notes |
|-------------|---------------|---------|-------|
| Basic | 200-500ms | 8 | Fastest, simple vector search |
| Enhanced | 400-800ms | 8 | Good balance |
| Advanced | 800-1500ms | 8 | Hybrid + reranking |
| Comprehensive | 1500-3000ms | 15 | Maximum detail |
| Vector | 300-600ms | 5 | Direct similarity |

### Cache Performance

| Cache Type | TTL | Hit Rate Expected |
|------------|-----|-------------------|
| Embedding | 24h | 70-90% |
| Search | 1h | 40-60% |
| Response | 30m | 20-40% |

---

## 🔍 Debugging Guide

### View Backend Logs
```bash
tail -f backend/logs/anylab.log
```

### Check Database Status
```bash
cd backend
source venv/bin/activate
python manage.py shell
```

```python
from ai_assistant.models import UploadedFile, DocumentChunk, QueryHistory

# Check documents
print(f"Files: {UploadedFile.objects.count()}")
print(f"Chunks: {DocumentChunk.objects.count()}")

# Check latest queries
for q in QueryHistory.objects.all()[:5]:
    print(q.query, q.created_at)

# Check document chunks
for chunk in DocumentChunk.objects.select_related('document')[:5]:
    print(chunk.document.filename, chunk.chunk_index)
```

### Test Ollama Models
```bash
# Test LLM model
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5:latest",
  "prompt": "test",
  "stream": false
}'

# Test embedding model
curl http://localhost:11434/api/embeddings -d '{
  "model": "bge-m3:latest",
  "prompt": "test embedding"
}'
```

### Check API Health
```bash
curl http://localhost:8000/api/health/
```

---

## ✅ Testing Checklist

### Functionality Tests
- [ ] Document upload works
- [ ] Document processing completes
- [ ] Chunks are created correctly
- [ ] Embeddings are generated
- [ ] Basic RAG search returns results
- [ ] Advanced RAG search uses hybrid search
- [ ] Comprehensive RAG returns 15 results
- [ ] Vector search shows similarity scores
- [ ] Performance metrics are captured

### Performance Tests
- [ ] Basic search <500ms
- [ ] Enhanced search <800ms
- [ ] Advanced search <1500ms
- [ ] Comprehensive search <3000ms
- [ ] Cache hit rates >40%
- [ ] Response times decrease on second query

### Adaptive Expansion Tests
- [ ] Technical terms not expanded
- [ ] Short queries expanded
- [ ] Exact phrases not expanded
- [ ] Specific patterns not expanded
- [ ] General queries expanded
- [ ] Logs show expansion decisions

### Integration Tests
- [ ] Frontend connects to backend
- [ ] API authentication works
- [ ] CORS configured correctly
- [ ] Documents load in frontend
- [ ] Search results display correctly
- [ ] Error handling works

---

## 🎯 Next Steps After Testing

Once testing is complete:

1. **Analyze Performance Metrics**
   - Review actual search times
   - Compare to expected benchmarks
   - Identify bottlenecks

2. **Optimize Based on Results**
   - Adjust similarity thresholds if needed
   - Fine-tune cache durations
   - Modify query expansion rules

3. **Document Findings**
   - Create performance report
   - Update configuration based on results
   - Share metrics with team

4. **Production Deployment**
   - Configure environment variables
   - Set up monitoring
   - Deploy to production server

---

## 📝 Notes

- All tests should be performed in a test environment first
- Keep test data separate from production data
- Document any issues found during testing
- Create issues for bugs that need fixing
- Update this guide with actual performance numbers

**Good luck with testing! 🚀**

