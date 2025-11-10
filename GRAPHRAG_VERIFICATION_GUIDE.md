# GraphRAG Verification Guide

This guide helps you verify that the GraphRAG improvements are working correctly.

## Quick Verification

### 1. Check Graph Analysis

```bash
cd backend
python manage.py analyze_graph
```

**What to look for:**
- ✅ Enhanced entity types (CONCEPT, KEY_TERM, IMPORTANT_INFO, KEY_POINT) should be present
- ✅ Enhanced types should be >10% of total entities (ideally >20%)
- ✅ High confidence entities should be present

**Example output:**
```
Entity Type Breakdown:
  ✨ CONCEPT              150 (25.0%) avg_conf: 0.75
  ✨ KEY_TERM             80 (13.3%) avg_conf: 0.82
  📌 PRODUCT              120 (20.0%) avg_conf: 0.80
  📌 ERROR_CODE           90 (15.0%) avg_conf: 0.75
  ...

Improvement Indicators:
  ✅ Enhanced entity types found: 230 (38.3%)
  ✅ Good coverage of enhanced entity types (>20%)
```

### 2. Test a Query

```bash
python manage.py test_graph_rag_query "What are the key points?" --show-entities
```

**What to look for:**
- ✅ Enhanced entity types extracted from query (marked with ✨)
- ✅ Graph-enhanced results in response
- ✅ Important sections (summary, conclusion) in sources

**Example output:**
```
Extracted 3 entities:
  ✨ CONCEPT              "key points" (conf: 0.85)
  ✨ IMPORTANT_INFO       "important information" (conf: 0.78)
  📌 TOPIC                "main topics" (conf: 0.70)

Graph Statistics:
  Total results: 5
  Graph-enhanced: 3 ✨
  ✅ 60.0% of results are graph-enhanced
```

## Detailed Verification Steps

### Step 1: Analyze Entity Types

```bash
python manage.py analyze_graph --entity-types --top-entities 20
```

**Check:**
1. Are enhanced entity types present? (CONCEPT, KEY_TERM, IMPORTANT_INFO, KEY_POINT)
2. What percentage of entities are enhanced types?
3. Are top entities a mix of enhanced and traditional types?

**Good signs:**
- Enhanced types represent 20%+ of total entities
- Top entities include both enhanced and traditional types
- High confidence scores for enhanced types

### Step 2: Test Conceptual Queries

Conceptual queries should benefit most from improvements:

```bash
# Test conceptual queries
python manage.py test_graph_rag_query "What are the key points?" --show-entities
python manage.py test_graph_rag_query "What is the main idea?" --show-entities
python manage.py test_graph_rag_query "How does this work?" --show-entities
```

**Check:**
1. Are enhanced entity types extracted from these queries?
2. Do results include graph-enhanced documents?
3. Are important sections (summary, conclusion) prioritized?

**Good signs:**
- Enhanced entity types extracted from conceptual queries
- Graph-enhanced results appear in top results
- Important sections ranked higher

### Step 3: Compare Before/After

If you have access to before/after data:

**Before improvements:**
- Only traditional entity types (PRODUCT, ERROR_CODE, etc.)
- No concept extraction
- Limited semantic understanding

**After improvements:**
- Enhanced entity types present
- Concepts and key terms extracted
- Better query understanding
- Important sections prioritized

### Step 4: Test Sample Queries

```bash
python manage.py test_graph_rag_query --sample-queries
```

This tests multiple sample queries and shows:
- Entity extraction for each
- Graph-enhanced results
- Improvement indicators

## Verification Checklist

### Graph Analysis
- [ ] Enhanced entity types present in graph
- [ ] Enhanced types >10% of total (ideally >20%)
- [ ] High confidence entities present
- [ ] Top entities include enhanced types

### Query Testing
- [ ] Enhanced entities extracted from conceptual queries
- [ ] Graph-enhanced results appear
- [ ] Important sections prioritized
- [ ] Query understanding improved

### Performance
- [ ] Queries return relevant results
- [ ] Important information appears first
- [ ] Graph-enhanced results have higher scores
- [ ] Response quality improved

## Troubleshooting

### No Enhanced Entity Types Found

**Problem:** `analyze_graph` shows no enhanced types

**Solutions:**
1. Reprocess documents: `python manage.py reprocess_graph_rag`
2. Check LLM is enabled: Ensure Ollama is running
3. Verify entity extraction: Check logs for errors
4. Test with one document: `python manage.py reprocess_graph_rag --document-id 1`

### Low Enhanced Type Coverage

**Problem:** Enhanced types <10% of total

**Solutions:**
1. Reprocess with LLM: `python manage.py reprocess_graph_rag` (without --skip-llm)
2. Check document content: Some documents may not have conceptual content
3. Verify LLM extraction: Check logs for LLM extraction results
4. Increase LLM extraction: Ensure `use_llm_extraction = True`

### No Graph-Enhanced Results

**Problem:** Queries show no graph-enhanced results

**Solutions:**
1. Check graph is built: `python manage.py analyze_graph`
2. Verify entities in graph: Check entity type breakdown
3. Test entity extraction: `python manage.py test_graph_rag_query "test" --show-entities`
4. Reprocess documents: May need to rebuild graph

### Poor Query Results

**Problem:** Results don't seem improved

**Solutions:**
1. Verify reprocessing completed: Check reprocessing logs
2. Test with conceptual queries: These benefit most
3. Check entity extraction: Ensure enhanced types are extracted
4. Review importance scoring: Check if important sections are identified

## Expected Improvements

### Entity Extraction
- **Before:** Only regex-based (products, error codes)
- **After:** LLM-based concepts, key terms, important info

### Query Understanding
- **Before:** Only exact entity matches
- **After:** Semantic understanding, concept extraction

### Result Ranking
- **Before:** Simple similarity scores
- **After:** Importance-boosted, graph-enhanced results

### Information Retrieval
- **Before:** May miss important sections
- **After:** Prioritizes summaries, conclusions, key points

## Success Metrics

### Good Performance Indicators:
- ✅ Enhanced entity types: 20%+ of total
- ✅ Graph-enhanced results: 30%+ of query results
- ✅ Important sections: Identified and prioritized
- ✅ Query understanding: Enhanced types extracted from queries

### Excellent Performance Indicators:
- ✅ Enhanced entity types: 30%+ of total
- ✅ Graph-enhanced results: 50%+ of query results
- ✅ All important sections: Identified
- ✅ All conceptual queries: Enhanced types extracted

## Next Steps

After verification:

1. **If improvements are working:**
   - Continue using GraphRAG
   - Monitor query performance
   - Consider reprocessing more documents

2. **If improvements need work:**
   - Reprocess documents with LLM extraction
   - Check for errors in logs
   - Verify Ollama is working correctly
   - Test with different document types

3. **For ongoing optimization:**
   - Regularly analyze graph statistics
   - Test new queries
   - Monitor improvement indicators
   - Adjust entity extraction if needed

