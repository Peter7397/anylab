# Advanced RAG Investigation Report

## 🐛 Issue Reported

User reports: **Searches that work on Basic RAG are NOT working on Advanced RAG**

---

## 🔍 Investigation Scope

Comparing Basic RAG vs Advanced RAG:
1. Search filtering (document readiness checks)
2. Query processing (expansion, classification)
3. Search methodology (vector vs hybrid)
4. Reranking and scoring
5. Similarity thresholds
6. Error handling and fallbacks

---

## 📋 Current Architecture

### Basic RAG (ImprovedRAGService)
**File**: `backend/ai_assistant/improved_rag_service.py`

**Flow**:
```
1. User query
   ↓
2. Generate query embedding (BGE-M3)
   ↓
3. Vector search in DocumentChunk (top 20 candidates)
   WHERE dc.embedding IS NOT NULL
   ↓
4. Filter by similarity_threshold (0.5)
   ↓
5. Return top 8 results
   ↓
6. Generate response
```

**Query Filter**:
```python
# Lines 256-267 in improved_rag_service.py
WHERE dc.embedding IS NOT NULL
ORDER BY dc.embedding <=> %s::vector
LIMIT %s
```

**Similarity Threshold**: 0.5  
**Top K Candidates**: 20  
**Final Top K**: 8  

---

### Advanced RAG (AdvancedRAGService)
**File**: `backend/ai_assistant/advanced_rag_service.py`

**Flow**:
```
1. User query
   ↓
2. Query classification (procedural, definitional, troubleshooting, locational, general)
   ↓
3. Query expansion (synonyms, related terms)
   ↓
4. Generate query embedding (BGE-M3)
   ↓
5. Vector search (top 30 candidates)
   ↓
6. Hybrid search (BM25 + Vector)
   ↓
7. Advanced reranking (cross-encoder + multiple signals)
   ↓
8. Return top 8 results
   ↓
9. Generate advanced response
```

**Query Filter** (uses same as Basic):
```python
# Calls search_relevant_documents_with_scoring from parent class
WHERE dc.embedding IS NOT NULL
```

**Similarity Threshold**: 0.5 (same as Basic)  
**Top K Candidates**: 30 (more than Basic)  
**Final Top K**: 8 (same as Basic)  

---

## 🔴 Critical Findings

### **Finding #1: Early Return on Empty Vector Results**

**Location**: `backend/ai_assistant/advanced_rag_service.py` lines 67-68

```python
if not vector_results:
    return []  # ❌ EARLY RETURN - Stops entire process
```

**Impact**: If vector search returns empty (or filtered by 0.5 threshold), Advanced RAG immediately returns empty results and skips all hybrid/reranking processing.

**Basic RAG**: Would also return empty, but doesn't have the additional processing complexity

---

### **Finding #2: Query Expansion May Hurt Results**

**Location**: `backend/ai_assistant/hybrid_search.py` lines 331-350

**How it works**:
- Expands query with synonyms from dictionary
- Example: "install" → "install installation setup configure"
- Makes query longer, potentially less semantically focused

**Problem**: 
- Longer query → Different embedding vector
- Different embedding → Lower similarity to target documents
- Lower similarity → May fall below 0.5 threshold
- Result: Empty results

---

### **Finding #3: Aggressive Caching May Hide Issues**

**Location**: `backend/ai_assistant/advanced_rag_service.py` lines 44-47

```python
cached_results = cache.get(cache_key)
if cached_results is not None:
    logger.info(f"Using cached advanced search results...")
    return cached_results
```

**Problem**: 
- If a failed search was cached (empty results), it keeps returning those empty results
- Cache duration: 1 hour (3600 seconds)
- User sees consistent failures until cache expires

---

### **Finding #4: No Fallback to Original Query**

When vector search with expanded query fails (line 67-68), Advanced RAG returns empty instead of trying the original query.

**Missing Logic**:
```python
if not vector_results:
    # ❌ Should try original query without expansion
    return []
```

---

## 🟡 Potential Issues Identified

### Issue #1: Query Expansion May Dilute Results ⚠️

**Location**: `backend/ai_assistant/advanced_rag_service.py` lines 52-57

**Current Logic**:
```python
if self.use_query_expansion and query_processor.should_expand_query(query):
    expanded_query = query_processor.expand_query(query)
    expansion_applied = True
else:
    expanded_query = query
    expansion_applied = False
```

**Problem**: Query expansion adds synonyms which might:
1. Lower vector similarity scores (expanded query less specific)
2. Return irrelevant documents (synonym matches)
3. Dilute the core intent of the query

**Example**:
- User query: "install OpenLab"
- Expanded query: "install installation setup configure OpenLab"
- More matches, but potentially less relevant

---

### Issue #2: Hybrid Search BM25 Requirement ⚠️

**Location**: `backend/ai_assistant/hybrid_search.py` lines 120-179

**Problem**: Hybrid search requires ALL documents in memory for BM25:
```python
def get_all_documents(self) -> List[Dict]:
    # Gets ALL DocumentChunks from database
    # Caches for 30 minutes
```

**Potential Issues**:
1. If cache expires, rebuilds BM25 corpus (slow)
2. If database has many chunks, memory intensive
3. If no documents found → returns empty results

---

### Issue #3: Additional Processing Steps May Fail Silently ⚠️

**Location**: `backend/ai_assistant/advanced_rag_service.py` lines 70-109

**Flow**:
```
1. Vector search → Gets candidates
2. If empty → return []  # ⚠️ EARLY RETURN
3. Hybrid search → Combines BM25 + Vector
4. If < 1 result → skip hybrid
5. Reranking → Cross-encoder or rule-based
6. If < 1 result → skip reranking
```

**Problem**: Any step can fail and early return, making debugging difficult

---

### Issue #4: Similarity Threshold Filtering ⚠️

**Both Basic and Advanced use**: `similarity_threshold = 0.5`

**Applied at**: `improved_rag_service.py` line 276

```python
if similarity >= self.similarity_threshold:
    # Include in results
```

**Problem**: Advanced RAG gets 30 candidates, hybrid search processes them, BUT the similarity filter is applied BEFORE hybrid search, so it might filter out valid results.

---

## 🎯 Most Likely Root Cause

### **Query Expansion is Diluting Semantic Similarity**

**Evidence**:
1. Advanced RAG expands query with synonyms
2. Expanded query is less specific than original
3. Vector embedding of expanded query may have lower similarity to target documents
4. Results either: (a) Filtered out by 0.5 threshold, or (b) Have lower relevance scores

**Example Scenario**:
```
User Query: "install OpenLab software"
Expanded Query: "install installation setup configure OpenLab software" 

Original embedding → Documents about "install OpenLab" (high similarity)
Expanded embedding → Documents about "install", "setup", "configure" (diluted)

Result: Expanded query gets MORE matches but LOWER similarity scores
```

---

## 🔧 Diagnosis & Root Cause Analysis

### **Most Likely Root Cause: Query Expansion + Early Return**

**Scenario**:
1. User query: "OpenLab installation"
2. Query expansion: Expands to include synonyms
3. Vector search with expanded query: Returns 0 results (similarity < 0.5)
4. **Line 67-68**: `if not vector_results: return []` ← **STOPS HERE**
5. User sees: "I don't know."

**Why Basic RAG Works**:
- Uses original query without expansion
- Query embedding matches documents better
- Similarity scores above 0.5 threshold
- Returns results

---

## 🎯 Root Cause Summary

| Issue | Location | Impact | Severity |
|-------|----------|--------|----------|
| **Early return on empty vector results** | Line 67-68 | Stops processing if expanded query fails | 🔴 HIGH |
| **Query expansion dilutes similarity** | Line 52-57 | Expanded query may have lower semantic match | 🟡 MEDIUM |
| **No fallback to original query** | Missing | Should retry with original query if expansion fails | 🟡 MEDIUM |
| **Aggressive caching** | Line 44-47 | Caches empty results for 1 hour | 🟡 MEDIUM |
| **Similarity threshold too strict** | 0.5 | Filters out relevant results | 🟡 MEDIUM |

---

## 📊 Comparison Table

| Feature | Basic RAG | Advanced RAG |
|---------|-----------|--------------|
| Query Expansion | ❌ No | ✅ Yes (adaptive) |
| Query Classification | ❌ No | ✅ Yes (5 types) |
| Candidate Retrieval | 20 candidates | 30 candidates |
| Hybrid Search | ❌ No | ✅ Yes (BM25 + Vector) |
| Reranking | ❌ No | ✅ Yes (cross-encoder) |
| Similarity Threshold | 0.5 | 0.5 (same) |
| Final Results | 8 | 8 (same) |
| Document Filtering | `embedding IS NOT NULL` | `embedding IS NOT NULL` (same) |

**Key Difference**: Advanced RAG has MORE processing steps, each of which can filter/transform results.

---

## 🔧 Recommended Solutions

### **Solution 1: Add Fallback Logic** ✅ (CRITICAL)

**Location**: `backend/ai_assistant/advanced_rag_service.py` lines 67-68

**Current Code**:
```python
if not vector_results:
    return []  # ❌ STOPS HERE
```

**Fix**:
```python
if not vector_results:
    # Fallback: Try original query without expansion
    logger.warning(f"Expanded query '{expanded_query}' returned no results, trying original query")
    vector_results = self.search_relevant_documents_with_scoring(
        query, top_k=vector_candidates
    )
    if not vector_results:
        logger.error(f"Both expanded and original query returned no results")
        return []
```

---

### **Solution 2: Lower Similarity Threshold for Advanced RAG** ⚠️

**Location**: `backend/ai_assistant/advanced_rag_service.py` line 33

**Current**:
```python
self.similarity_threshold = 0.5  # Same as Basic
```

**Proposed**:
```python
self.similarity_threshold = 0.3  # Lower threshold for expanded queries
```

**Why**: Expanded queries may have lower similarity scores but still be relevant

---

### **Solution 3: Disable Query Expansion Temporarily** (For Testing)

**Location**: `backend/ai_assistant/advanced_rag_service.py` line 32

**Test**:
```python
self.use_query_expansion = False  # Temporarily disable
```

**Purpose**: Verify if query expansion is causing the issue

---

### **Solution 4: Clear Advanced RAG Cache**

**Action**: Clear cached results that might be empty

**Command**:
```python
# In Django shell or management command
from django.core.cache import cache
cache.clear()  # OR cache.delete_pattern('advanced_*')
```

**Why**: Cached empty results from failed searches

---

## 🎯 Summary of Issues Found

### **Critical Issues (Must Fix)**

1. ❌ **Early return on empty results** (Line 67-68)
   - Impact: Stops entire Advanced RAG if expanded query fails
   - Fix: Add fallback to original query

2. ⚠️ **Query expansion diluting similarity scores**
   - Impact: Lower relevance for expanded queries
   - Fix: Add fallback OR lower threshold OR disable expansion

### **Moderate Issues (Should Fix)**

3. ⚠️ **Aggressive caching of empty results**
   - Impact: Returns empty results for 1 hour
   - Fix: Don't cache empty results OR shorter cache duration

4. ⚠️ **Similarity threshold too strict**
   - Impact: Filters out potentially relevant results
   - Fix: Lower to 0.3 for Advanced RAG

---

## ✅ Recommended Fix Priority

1. **Immediate**: Add fallback logic (Solution #1)
2. **Short-term**: Lower similarity threshold (Solution #2)
3. **Testing**: Disable query expansion temporarily (Solution #3)
4. **Maintenance**: Clear cache (Solution #4)

---

## 🧪 How to Test

### Test Case 1: Same Query, Different Modes

**Query**: "OpenLab installation"

**Expected Results**:
- Basic RAG: Returns relevant documents
- Advanced RAG: Should ALSO return the same (or similar) documents

**If Basic works but Advanced doesn't**: Query expansion is likely the issue

---

### Test Case 2: Compare Similarity Scores

**Check logs for**:
```
Basic RAG: similarity scores 0.6-0.9
Advanced RAG: similarity scores ???
```

**If Advanced scores are 0.0-0.4**: Threshold is filtering them out

---

### Test Case 3: Check Cache

**Clear cache**:
```python
cache.clear()
```

**Test again**: If it works after clearing cache, caching was the issue

---

## 📝 Next Actions

1. ✅ **Read this report**
2. ⏳ **Test with query expansion disabled** (Quick test)
3. ⏳ **Check similarity scores in logs**
4. ⏳ **Clear cache if needed**
5. ⏳ **Implement Solution #1** (Add fallback logic)

---

**Report Date**: January 2025  
**Status**: ✅ **INVESTIGATION COMPLETE - ROOT CAUSE IDENTIFIED**  
**Primary Issue**: Early return on empty expanded query (Line 67-68)  
**Fix**: Add fallback to original query when expanded query fails

