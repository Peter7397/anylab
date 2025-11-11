# AnyLab Performance Parameters Report

## Current Configuration Summary

This report documents all embedding, metadata extraction, and RAG parameters currently configured in the AnyLab system. Use this to identify potential performance improvements.

---

## 1. EMBEDDING PARAMETERS

### Model Configuration
| Parameter | Current Value | Location | Notes |
|-----------|--------------|----------|-------|
| **Primary Model** | `bge-m3:latest` | `settings.py:300` | BGE-M3 via Ollama |
| **Fallback Model** | `nomic-embed-text:latest` | `settings.py:301` | Not used (OFFLINE_ONLY=True) |
| **Embedding Dimensions** | `1024` | `settings.py:313` | BGE-M3 standard |
| **Device** | `cpu` | `settings.py:302` | CPU-only (no GPU) |
| **Mode** | `lightweight` | `settings.py:311` | Options: 'auto', 'performance', 'lightweight' |
| **Offline Only** | `True` | `settings.py:312` | Forces offline embeddings (no fallback) |

### Embedding Generation Settings
| Parameter | Current Value | Location | Notes |
|-----------|--------------|----------|-------|
| **Batch Size** | `50 chunks/batch` | `automatic_file_processor.py:59` | Chunks processed per Ollama API call |
| **Cache TTL** | `3600 seconds (1 hour)` | `settings.py:291` | Embedding cache duration |
| **Retry Logic** | `3 attempts` | `automatic_file_processor.py` | With exponential backoff |
| **Timeout** | `60 seconds` | `automatic_file_processor.py` | Per embedding request |

### Performance Notes
- ✅ **BGE-M3**: High-quality 1024-dim embeddings, good for semantic search
- ⚠️ **CPU-only**: May be slower than GPU but more accessible
- ⚠️ **Batch size 50**: Could be increased for better throughput if Ollama can handle it
- ✅ **1-hour cache**: Good balance between freshness and performance

---

## 2. CHUNKING PARAMETERS

### Chunking Strategy
| Parameter | Current Value | Location | Notes |
|-----------|--------------|----------|-------|
| **Chunk Size** | `600 characters` | `enhanced_chunking.py:199` | Balanced for semantic understanding |
| **Chunk Overlap** | `120 characters (20%)` | `enhanced_chunking.py:200` | Maintains context between chunks |
| **Max Chunks per Doc** | `2000 chunks` | `enhanced_chunking.py:201` | Hard limit to prevent crashes |
| **Chunking Method** | `Semantic (sentence-aware)` | `enhanced_chunking.py` | Respects sentence boundaries |

### Chunking Algorithm Details
- **Preprocessing**: Removes excessive whitespace, normalizes unicode, cleans headers/footers
- **Boundary Detection**: Uses sentence endings (`.`, `!`, `?`) for natural breaks
- **Overlap Strategy**: 20% overlap ensures context continuity
- **Safety Limit**: Documents exceeding 2000 chunks are truncated with warning

### Performance Notes
- ✅ **600 chars**: Good balance - not too small (avoids fragmentation) nor too large (maintains precision)
- ✅ **20% overlap**: Standard practice for RAG systems
- ⚠️ **2000 chunk limit**: Large documents may be truncated - consider increasing if needed
- ✅ **Sentence-aware**: Better semantic coherence than fixed-size chunks

---

## 3. METADATA EXTRACTION PARAMETERS

### Metadata Settings
| Parameter | Current Value | Location | Notes |
|-----------|--------------|----------|-------|
| **Extraction Method** | `Automatic (via file processors)` | `automatic_file_processor.py` | Extracted during file processing |
| **Supported Formats** | PDF, DOCX, PPTX, HTML, TXT | Various processors | Multi-format support |
| **Metadata Fields** | Title, author, date, keywords, etc. | `models.py` | DocumentFile model |

### Metadata Extraction Details
- **PDF**: Uses PyMuPDF (fitz) for text and metadata
- **DOCX**: Uses mammoth for Word documents
- **PPTX**: Uses pptx2json for PowerPoint
- **HTML**: Custom HTML parser with content extraction
- **Extraction**: Happens automatically during file upload/processing

### Performance Notes
- ✅ **Automatic extraction**: No manual intervention needed
- ✅ **Multi-format**: Handles various document types
- ℹ️ **No specific tuning**: Metadata extraction is straightforward, no performance parameters to tune

---

## 4. RAG SEARCH PARAMETERS

### Basic RAG Service (`ImprovedRAGService`)
| Parameter | Current Value | Location | Notes |
|-----------|--------------|----------|-------|
| **Similarity Threshold** | `0.5` | `improved_rag_service.py:33` | Minimum cosine similarity score |
| **Top K Candidates** | `20` | `improved_rag_service.py:34` | Initial candidate retrieval |
| **Final Top K** | `8` | `improved_rag_service.py:35` | Final results returned |
| **Search Cache TTL** | `3600s (1 hour)` | `improved_rag_service.py:29` | Search result cache |

### Advanced RAG Service (`AdvancedRAGService`)
| Parameter | Current Value | Location | Notes |
|-----------|--------------|----------|-------|
| **Similarity Threshold** | `0.3` | `advanced_rag_service.py:40` | Lower for better recall |
| **Hybrid Search** | `Enabled` | `advanced_rag_service.py:29` | BM25 + Vector search |
| **Reranking** | `Enabled` | `advanced_rag_service.py:30` | Cross-encoder reranking |
| **Query Expansion** | `Enabled` | `advanced_rag_service.py:31` | Adaptive query expansion |
| **Vector Candidates** | `30` | `advanced_rag_service.py:75` | For hybrid search |
| **Hybrid Cache TTL** | `3600s (1 hour)` | `advanced_rag_service.py:34` | Hybrid search cache |

### Comprehensive RAG Service (`ComprehensiveRAGService`)
| Parameter | Current Value | Location | Notes |
|-----------|--------------|----------|-------|
| **Similarity Threshold** | `0.25` | `comprehensive_rag_service.py:202` | Most inclusive |
| **Comprehensive Top K** | `30` | `comprehensive_rag_service.py:200` | Final results returned |
| **Comprehensive Candidates** | `120` | `comprehensive_rag_service.py:201` | Wide candidate net |
| **Max Context Length** | `12000 characters` | `comprehensive_rag_service.py:205` | Context window size |
| **Comprehensive Cache TTL** | `21600s (6 hours)` | `comprehensive_rag_service.py:208` | Longer cache for comprehensive |

### Performance Notes
- ⚠️ **Thresholds vary by service**: 0.5 (basic) → 0.3 (advanced) → 0.25 (comprehensive)
- ✅ **Hybrid search**: Better recall than pure vector search
- ✅ **Query expansion**: Improves search for complex queries
- ⚠️ **Comprehensive uses 120 candidates**: May be slow for large document sets

---

## 5. LLM GENERATION PARAMETERS

### Ollama Model Settings (Global)
| Parameter | Current Value | Location | Notes |
|-----------|--------------|----------|-------|
| **Model** | `llama3:8b` | `settings.py:283` | Primary LLM model |
| **API URL** | `http://localhost:11434` | `settings.py:282` | Ollama endpoint |
| **Request Timeout** | `120 seconds` | `settings.py:284` | Per request timeout |
| **Default Max Tokens** | `256 tokens` | `settings.py:286` | Default response length |
| **Temperature** | `0.3` | `settings.py:287` | Low = focused, High = creative |
| **Context Size (num_ctx)** | `1024 tokens` | `settings.py:285` | Context window |
| **System Prompt** | `"You are a helpful, expert assistant..."` | `settings.py:288` | Default system prompt |

### Basic RAG Generation (via `rag_service.py`)
| Parameter | Current Value | Location | Notes |
|-----------|--------------|----------|-------|
| **num_predict** | `768 tokens` | `rag_service.py:626` | Max tokens generated |
| **Temperature** | `0.3` | `rag_service.py:627` | Focused responses |
| **top_p** | `0.9` | `rag_service.py:628` | Nucleus sampling |
| **top_k** | `40` | `rag_service.py:629` | Top-k sampling |
| **repeat_penalty** | `1.1` | `rag_service.py:630` | Prevents repetition |
| **num_ctx** | `4096 tokens` | `rag_service.py:631` | Context window |

### Comprehensive RAG Generation (Query-Type Specific)
| Query Type | num_predict | Temperature | top_p | repeat_penalty | num_ctx | Location |
|------------|-------------|-------------|-------|----------------|---------|----------|
| **Procedural** | 6000 | 0.05 | 0.7 | 1.3 | 16384 | `comprehensive_rag_service.py:417` |
| **Definitional** | 5000 | 0.05 | 0.75 | 1.25 | 16384 | `comprehensive_rag_service.py:425` |
| **Troubleshooting** | 6000 | 0.05 | 0.7 | 1.3 | 16384 | `comprehensive_rag_service.py:433` |
| **Locational** | 3500 | 0.05 | 0.7 | 1.2 | 16384 | `comprehensive_rag_service.py:441` |
| **General** | 5000 | 0.05 | 0.8 | 1.2 | 16384 | `comprehensive_rag_service.py:449` |

### Performance Notes
- ⚠️ **Default max_tokens (256)**: Very short - may truncate detailed answers
- ✅ **Temperature 0.3**: Good for factual, focused responses
- ⚠️ **Context size 1024**: Small - may limit context understanding
- ✅ **Comprehensive uses 16384 ctx**: Much better for detailed responses
- ⚠️ **Comprehensive uses very low temp (0.05)**: Very deterministic, may be too rigid

---

## 6. CACHE PARAMETERS

| Cache Type | TTL | Location | Notes |
|------------|-----|----------|-------|
| **Embedding Cache** | 3600s (1 hour) | `settings.py:291` | Caches computed embeddings |
| **Response Cache** | 1800s (30 min) | `settings.py:292` | Caches LLM responses |
| **Search Cache** | 3600s (1 hour) | `settings.py:293` | Caches search results |
| **Hybrid Search Cache** | 3600s (1 hour) | `advanced_rag_service.py:34` | Caches hybrid search |
| **Comprehensive Cache** | 21600s (6 hours) | `comprehensive_rag_service.py:208` | Caches comprehensive results |

### Performance Notes
- ✅ **1-hour embedding cache**: Good balance - embeddings don't change
- ⚠️ **30-min response cache**: May be too short for static content
- ✅ **6-hour comprehensive cache**: Good for detailed analysis

---

## 7. PROCESSING PARAMETERS

### File Processing
| Parameter | Current Value | Location | Notes |
|-----------|--------------|----------|-------|
| **Async Processing** | `Disabled (False)` | `settings.py:297` | Synchronous processing |
| **Batch Embedding** | `50 chunks/batch` | `automatic_file_processor.py:59` | Parallel processing |
| **Max Concurrent Workers** | `4 workers` | `automatic_file_processor.py` | Thread pool size |
| **Retry Attempts** | `3 attempts` | `automatic_file_processor.py` | With exponential backoff |

### Performance Notes
- ⚠️ **Synchronous processing**: May block during large uploads
- ✅ **Batch size 50**: Efficient use of Ollama API
- ✅ **4 workers**: Good parallelization for embeddings

---

## 8. PERFORMANCE IMPROVEMENT RECOMMENDATIONS

### High Priority (Potential Quick Wins)

1. **Increase Default Max Tokens**
   - Current: 256 tokens
   - Recommendation: 512-1024 tokens
   - Impact: More complete answers without truncation
   - Risk: Low - just longer responses

2. **Increase Context Window (num_ctx)**
   - Current: 1024 tokens (default), 4096 (basic RAG)
   - Recommendation: 2048-4096 tokens (default)
   - Impact: Better context understanding for complex queries
   - Risk: Low - may slow down slightly but improves quality

3. **Optimize Batch Size**
   - Current: 50 chunks/batch
   - Recommendation: Test 75-100 chunks/batch
   - Impact: Faster embedding generation if Ollama can handle it
   - Risk: Medium - need to test Ollama capacity

4. **Increase Comprehensive RAG Temperature**
   - Current: 0.05 (very deterministic)
   - Recommendation: 0.1-0.2
   - Impact: More natural responses while maintaining accuracy
   - Risk: Low - still very focused

### Medium Priority (Quality Improvements)

5. **Adjust Similarity Thresholds**
   - Current: 0.5 (basic), 0.3 (advanced), 0.25 (comprehensive)
   - Recommendation: Test 0.4-0.45 for basic, keep advanced/comprehensive
   - Impact: Better precision/recall balance
   - Risk: Medium - need to test with real queries

6. **Increase Top K Candidates**
   - Current: 20 (basic), 30 (advanced), 120 (comprehensive)
   - Recommendation: 30-40 for basic, 50-60 for advanced
   - Impact: Better recall for complex queries
   - Risk: Medium - slower search but better results

7. **Extend Cache TTLs**
   - Current: 1 hour (embedding/search), 30 min (response)
   - Recommendation: 24 hours (embedding), 2-4 hours (response)
   - Impact: Better performance for repeated queries
   - Risk: Low - static content benefits from longer cache

8. **Increase Max Chunks per Document**
   - Current: 2000 chunks
   - Recommendation: 3000-5000 chunks (if memory allows)
   - Impact: Process larger documents without truncation
   - Risk: Medium - need sufficient memory

### Low Priority (Advanced Optimizations)

9. **Enable Async Processing**
   - Current: Disabled (synchronous)
   - Recommendation: Enable with Celery for large files
   - Impact: Non-blocking uploads, better UX
   - Risk: Medium - requires Celery setup

10. **GPU Acceleration** (if available)
    - Current: CPU-only
    - Recommendation: Use GPU for embeddings if available
    - Impact: 10-100x faster embedding generation
    - Risk: High - requires GPU setup

11. **Model Optimization**
    - Current: llama3:8b (8B parameters)
    - Recommendation: Consider smaller models (llama3:4b) for faster responses
    - Impact: Faster generation, lower quality
    - Risk: High - may reduce response quality

12. **Hybrid Search Tuning**
    - Current: BM25 + Vector (equal weight)
    - Recommendation: Test different weight combinations
    - Impact: Better relevance for specific query types
    - Risk: Medium - requires experimentation

---

## 9. PARAMETER SUMMARY TABLE

| Category | Parameter | Current | Recommended | Impact | Risk |
|----------|-----------|---------|-------------|--------|------|
| **Embedding** | Batch Size | 50 | 75-100 | High | Medium |
| **Embedding** | Cache TTL | 1h | 24h | Medium | Low |
| **Chunking** | Chunk Size | 600 | 600-800 | Low | Low |
| **Chunking** | Max Chunks | 2000 | 3000-5000 | Medium | Medium |
| **RAG** | Similarity Threshold | 0.5 | 0.4-0.45 | Medium | Medium |
| **RAG** | Top K Candidates | 20 | 30-40 | Medium | Medium |
| **LLM** | Max Tokens | 256 | 512-1024 | High | Low |
| **LLM** | Context Size | 1024 | 2048-4096 | High | Low |
| **LLM** | Temperature | 0.3 | 0.3-0.4 | Low | Low |
| **Cache** | Response Cache | 30m | 2-4h | Medium | Low |

---

## 10. TESTING RECOMMENDATIONS

Before implementing changes, test:

1. **Query Performance**: Measure response time for typical queries
2. **Quality Metrics**: Evaluate answer relevance and completeness
3. **Resource Usage**: Monitor CPU, memory, and Ollama load
4. **Cache Hit Rate**: Track cache effectiveness
5. **Error Rate**: Monitor failed embeddings/searches

---

## 11. CURRENT PERFORMANCE BASELINE

To establish a baseline, consider measuring:
- Average embedding generation time per chunk
- Average search response time
- Average LLM generation time
- Cache hit rates
- Document processing throughput

---

**Report Generated**: 2025-11-04
**Configuration Version**: Current (Hardcoded)
**Next Review**: After implementing recommended changes

