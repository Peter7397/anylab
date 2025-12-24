# GraphRAG Improvements - Complete Guide

This is your complete guide to the GraphRAG improvements, including how to reprocess existing documents and verify the improvements are working.

## Quick Start

### 1. Reprocess Existing Documents

```bash
cd backend

# Reprocess all documents (recommended)
python manage.py reprocess_graph_rag

# Or reprocess a specific document first (to test)
python manage.py reprocess_graph_rag --document-id 1
```

### 2. Verify Improvements

```bash
# Analyze the graph
python manage.py analyze_graph --entity-types

# Test a query
python manage.py test_graph_rag_query "What are the key points?" --show-entities
```

## What Was Improved

### 1. Enhanced Entity Extraction
- **LLM-based extraction** for concepts, key terms, and important information
- **Heuristic extraction** for summaries, conclusions, and key points
- **New entity types**: CONCEPT, KEY_TERM, IMPORTANT_INFO, KEY_POINT, TOPIC, PROCEDURE

### 2. Importance Scoring
- **Chunk importance scores** based on entity presence and position
- **Priority boosting** for introduction and conclusion sections
- **Key section identification** (summaries, important notes)

### 3. Enhanced Query Processing
- **Concept extraction** from queries (not just named entities)
- **Semantic similarity fallback** when no entities found
- **Boosted scoring** for conceptual matches

### 4. Result Boosting
- **Importance-based boosting** for important chunks
- **Graph-enhanced results** prioritized
- **Better relevance ranking**

## Commands Reference

### Reprocessing Commands

#### `reprocess_graph_rag`
Reprocess documents with improved extraction:

```bash
# Basic usage
python manage.py reprocess_graph_rag

# Options
--document-id <ID>      # Process specific document
--batch-size <N>        # Documents per batch (default: 5)
--clear-graph          # Clear all graph data first
--skip-llm             # Skip LLM extraction (faster)
--dry-run              # Preview without changes
```

#### `build_graph`
Alternative graph building command (also improved):

```bash
python manage.py build_graph --force --clear-existing
```

### Analysis Commands

#### `analyze_graph`
Analyze the knowledge graph:

```bash
# Basic analysis
python manage.py analyze_graph

# Detailed breakdown
python manage.py analyze_graph --entity-types --documents --relationships

# Top entities
python manage.py analyze_graph --top-entities 20

# Specific document
python manage.py analyze_graph --document-id 1
```

**Shows:**
- Entity type breakdown (enhanced vs traditional)
- Top entities by occurrence
- Document statistics
- Relationship statistics
- Improvement indicators

#### `test_graph_rag_query`
Test GraphRAG queries:

```bash
# Test specific query
python manage.py test_graph_rag_query "What are the key points?"

# With entity extraction
python manage.py test_graph_rag_query "query" --show-entities

# With source details
python manage.py test_graph_rag_query "query" --show-sources

# Test sample queries
python manage.py test_graph_rag_query --sample-queries
```

**Shows:**
- Extracted entities (with enhanced types marked ✨)
- Graph-enhanced results
- Source documents with importance indicators
- Improvement indicators

## Step-by-Step Workflow

### Initial Setup

1. **Check current state:**
   ```bash
   python manage.py analyze_graph
   ```

2. **Test a query (before):**
   ```bash
   python manage.py test_graph_rag_query "What are the key points?"
   ```

3. **Reprocess documents:**
   ```bash
   # Start with one document to test
   python manage.py reprocess_graph_rag --document-id 1
   
   # If successful, process all
   python manage.py reprocess_graph_rag --batch-size 5
   ```

4. **Verify improvements:**
   ```bash
   # Check graph analysis
   python manage.py analyze_graph --entity-types
   
   # Test same query (after)
   python manage.py test_graph_rag_query "What are the key points?" --show-entities
   ```

### Ongoing Maintenance

1. **Regular analysis:**
   ```bash
   python manage.py analyze_graph --entity-types
   ```

2. **Test new queries:**
   ```bash
   python manage.py test_graph_rag_query "your query" --show-entities
   ```

3. **Reprocess new documents:**
   - New documents are automatically processed with improvements
   - For existing documents, use `reprocess_graph_rag`

## Expected Results

### Before Improvements
- Only regex-based entity extraction
- No concept understanding
- Limited semantic relationships
- Important sections may be missed

### After Improvements
- ✅ LLM-based concept extraction
- ✅ Enhanced entity types (CONCEPT, KEY_TERM, etc.)
- ✅ Importance scoring for chunks
- ✅ Better query understanding
- ✅ Important sections prioritized

### Verification Indicators

**Good signs:**
- Enhanced entity types: 20%+ of total entities
- Graph-enhanced results: 30%+ of query results
- Important sections identified and prioritized
- Conceptual queries extract enhanced types

**Excellent signs:**
- Enhanced entity types: 30%+ of total entities
- Graph-enhanced results: 50%+ of query results
- All important sections identified
- All conceptual queries work well

## Troubleshooting

### No Enhanced Entity Types

**Check:**
1. Are documents reprocessed? `python manage.py analyze_graph`
2. Is LLM extraction enabled? Check logs for LLM errors
3. Is Ollama running? `curl http://localhost:11434/api/tags`

**Fix:**
```bash
# Reprocess with LLM
python manage.py reprocess_graph_rag --document-id 1
```

### Low Enhanced Type Coverage

**Check:**
1. Entity type breakdown: `python manage.py analyze_graph --entity-types`
2. Document content (some may not have conceptual content)
3. LLM extraction logs

**Fix:**
```bash
# Reprocess without skipping LLM
python manage.py reprocess_graph_rag  # (no --skip-llm)
```

### No Graph-Enhanced Results

**Check:**
1. Graph is built: `python manage.py analyze_graph`
2. Entities in graph: Check entity type breakdown
3. Query entity extraction: `--show-entities` flag

**Fix:**
```bash
# Rebuild graph
python manage.py reprocess_graph_rag --clear-graph
```

## Documentation Files

- **GRAPH_RAG_IMPROVEMENTS.md** - Technical details of improvements
- **REPROCESS_GRAPHRAG_GUIDE.md** - Detailed reprocessing guide
- **GRAPHRAG_VERIFICATION_GUIDE.md** - Verification and testing guide
- **GRAPHRAG_COMPLETE_GUIDE.md** - This file (complete overview)

## Performance Considerations

### Processing Time
- **With LLM**: ~30-60 seconds per document
- **Without LLM**: ~5-10 seconds per document
- **Batch size**: 5 documents recommended for LLM processing

### Resource Usage
- **Memory**: Moderate (depends on document size)
- **CPU**: Moderate (LLM processing)
- **Neo4j**: Fast graph operations

### Recommendations
1. Start with 1-2 documents to test
2. Use batches of 5-10 documents
3. Monitor for errors
4. Use `--skip-llm` only if necessary

## Best Practices

1. **Test first**: Always test with `--dry-run` or single document
2. **Monitor progress**: Watch command output for errors
3. **Verify results**: Use analysis commands to check improvements
4. **Keep LLM enabled**: Only skip if absolutely necessary
5. **Regular analysis**: Periodically check graph statistics
6. **Test queries**: Verify improvements with real queries

## Support

If you encounter issues:

1. **Check logs**: `backend/logs/anylab.log`
2. **Review errors**: Command output shows detailed errors
3. **Verify services**: Ollama and Neo4j must be running
4. **Test incrementally**: Start with single document
5. **Use dry-run**: Test with `--dry-run` first

## Next Steps

1. **Reprocess documents**: Start with one, then batch process
2. **Verify improvements**: Use analysis and test commands
3. **Monitor performance**: Check query results and graph statistics
4. **Optimize if needed**: Adjust based on results

---

**Ready to start?** Run:
```bash
cd backend
python manage.py reprocess_graph_rag --document-id 1
python manage.py analyze_graph --entity-types
python manage.py test_graph_rag_query "What are the key points?" --show-entities
```

