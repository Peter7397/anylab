# Guide: Reprocessing Existing Documents for GraphRAG Improvements

This guide explains how to reprocess your existing documents to take advantage of the GraphRAG improvements (LLM-based entity extraction, importance scoring, etc.).

## Quick Start

### Reprocess All Documents

```bash
cd backend
python manage.py reprocess_graph_rag
```

This will:
- Reprocess all documents with status 'ready'
- Use LLM-based extraction for concepts and important information
- Calculate importance scores for chunks
- Rebuild the knowledge graph with enhanced entities

### Reprocess a Specific Document

```bash
python manage.py reprocess_graph_rag --document-id 123
```

### Dry Run (See What Would Be Processed)

```bash
python manage.py reprocess_graph_rag --dry-run
```

## Command Options

### `reprocess_graph_rag` Command

**Basic Options:**
- `--document-id <ID>`: Process only a specific document
- `--batch-size <N>`: Number of documents per batch (default: 5)
- `--status <STATUS>`: Only process documents with this status (default: 'ready')
- `--dry-run`: Show what would be processed without making changes

**Advanced Options:**
- `--clear-graph`: Clear all existing graph data before reprocessing
- `--skip-llm`: Skip LLM-based extraction (faster but less comprehensive)

### `build_graph` Command (Alternative)

The existing `build_graph` command has also been updated with improvements:

```bash
# Build graph for all ready documents
python manage.py build_graph

# Force rebuild (clears existing graph data)
python manage.py build_graph --force --clear-existing

# Process specific document
python manage.py build_graph --document-id 123 --force
```

## Processing Modes

### 1. Full Reprocessing (Recommended)

Uses all improvements including LLM extraction:

```bash
python manage.py reprocess_graph_rag
```

**What it does:**
- Extracts entities using regex patterns (fast)
- Extracts concepts using LLM (comprehensive)
- Extracts key points, summaries, important info (heuristics)
- Calculates importance scores for chunks
- Rebuilds graph with all entity types

**Time:** ~30-60 seconds per document (depends on LLM processing)

### 2. Fast Reprocessing (Skip LLM)

Faster processing without LLM extraction:

```bash
python manage.py reprocess_graph_rag --skip-llm
```

**What it does:**
- Extracts entities using regex patterns
- Extracts key points using heuristics
- Calculates importance scores
- Rebuilds graph

**Time:** ~5-10 seconds per document

**Trade-off:** Less comprehensive entity extraction, but much faster

### 3. Clear and Rebuild

Start fresh by clearing all graph data:

```bash
python manage.py reprocess_graph_rag --clear-graph
```

**Use when:**
- You want a clean slate
- Graph has inconsistencies
- Starting fresh with improved extraction

## Step-by-Step Process

### 1. Check Document Status

First, see what documents are ready:

```bash
python manage.py check_pdf_status
```

Or check in Django admin:
- Go to Admin → Uploaded Files
- Filter by `processing_status = 'ready'`

### 2. Test with One Document

Start with a single document to verify everything works:

```bash
python manage.py reprocess_graph_rag --document-id 1 --dry-run
python manage.py reprocess_graph_rag --document-id 1
```

### 3. Process in Batches

For large document sets, process in smaller batches:

```bash
# Process 5 documents at a time (default)
python manage.py reprocess_graph_rag --batch-size 5

# Process 10 documents at a time (faster but more memory)
python manage.py reprocess_graph_rag --batch-size 10
```

### 4. Monitor Progress

The command shows:
- Progress per document
- Number of entities extracted
- Number of relationships created
- Success/failure status
- Final statistics

## What Gets Improved

### Before Reprocessing
- Only regex-based entity extraction (product names, error codes)
- No importance scoring
- Limited concept understanding
- Basic graph relationships

### After Reprocessing
- ✅ LLM-based concept extraction
- ✅ Importance scores for chunks
- ✅ Enhanced entity types (CONCEPT, KEY_TERM, IMPORTANT_INFO, KEY_POINT)
- ✅ Better semantic understanding
- ✅ Improved query processing

## Performance Considerations

### Processing Time

- **With LLM**: ~30-60 seconds per document
- **Without LLM**: ~5-10 seconds per document
- **Batch size**: Smaller batches (5) recommended for LLM processing

### Resource Usage

- **Memory**: Moderate (depends on document size)
- **CPU**: Moderate (LLM processing)
- **Neo4j**: Graph operations are fast

### Recommendations

1. **Start small**: Test with 1-2 documents first
2. **Use batches**: Process 5-10 documents at a time
3. **Monitor**: Watch for errors and adjust batch size
4. **Skip LLM if needed**: Use `--skip-llm` for faster processing

## Troubleshooting

### No Documents Found

**Problem:** Command says "No documents found to process"

**Solutions:**
- Check document status: `python manage.py check_pdf_status`
- Ensure documents have `processing_status = 'ready'`
- Ensure documents have chunks: `chunks_created = True`
- Use `--document-id` to process specific document

### LLM Extraction Fails

**Problem:** LLM extraction errors or timeouts

**Solutions:**
- Check Ollama is running: `curl http://localhost:11434/api/tags`
- Use `--skip-llm` to continue without LLM extraction
- Check logs for specific errors
- Verify Ollama model is available

### Graph Connection Errors

**Problem:** Neo4j connection errors

**Solutions:**
- Check Neo4j is running: `docker ps | grep neo4j`
- Verify Neo4j connection in settings
- Check Neo4j logs: `docker logs <neo4j-container>`
- Test connection: `python manage.py build_graph --document-id 1 --dry-run`

### Memory Issues

**Problem:** Out of memory errors

**Solutions:**
- Reduce batch size: `--batch-size 3`
- Process documents one at a time: `--batch-size 1`
- Use `--skip-llm` to reduce memory usage
- Process during off-peak hours

## Verification

### Analyze Graph Statistics

After reprocessing, analyze the graph to see improvements:

```bash
# Basic analysis
python manage.py analyze_graph

# Detailed entity type breakdown
python manage.py analyze_graph --entity-types

# Show top entities
python manage.py analyze_graph --top-entities 20

# Full analysis
python manage.py analyze_graph --entity-types --documents --relationships
```

This shows:
- Entity type breakdown (enhanced vs traditional types)
- Top entities by occurrence
- Document statistics
- Relationship statistics
- Improvement indicators

### Test GraphRAG Queries

Test queries to verify improvements are working:

```bash
# Test a specific query
python manage.py test_graph_rag_query "What are the key points?"

# Test with entity extraction shown
python manage.py test_graph_rag_query "What is the main idea?" --show-entities

# Test sample queries
python manage.py test_graph_rag_query --sample-queries

# Show detailed source information
python manage.py test_graph_rag_query "How does this work?" --show-sources
```

This shows:
- Extracted entities from query (with enhanced types marked)
- Graph-enhanced results
- Source documents with importance indicators
- Improvement indicators

### Check Graph Statistics (Alternative)

```bash
python manage.py build_graph --dry-run
```

Or in Django admin:
- Go to Admin → System Settings
- Check Neo4j health status
- View graph statistics

### Test Queries

Test with queries that should benefit from improvements:

1. **Conceptual queries:**
   - "What are the key points?"
   - "What is the main idea?"
   - "How does this work?"

2. **Important information:**
   - "What should I know about X?"
   - "What are the important notes?"
   - "What are the warnings?"

3. **Compare results:**
   - Check if important sections appear higher
   - Verify concepts are being extracted
   - Confirm better relevance

## Best Practices

1. **Backup first**: Consider backing up Neo4j data before clearing
2. **Test incrementally**: Start with one document, then small batches
3. **Monitor logs**: Watch for errors and warnings
4. **Use dry-run**: Always test with `--dry-run` first
5. **Schedule off-peak**: Process large batches during low usage
6. **Keep LLM enabled**: Use `--skip-llm` only if necessary

## Example Workflows

### Workflow 1: Full Reprocessing (Recommended)

```bash
# 1. Check what will be processed
python manage.py reprocess_graph_rag --dry-run

# 2. Process all documents
python manage.py reprocess_graph_rag --batch-size 5

# 3. Verify results
python manage.py build_graph --dry-run
```

### Workflow 2: Fast Reprocessing

```bash
# Skip LLM for faster processing
python manage.py reprocess_graph_rag --skip-llm --batch-size 10
```

### Workflow 3: Selective Reprocessing

```bash
# Process only specific documents
python manage.py reprocess_graph_rag --document-id 1
python manage.py reprocess_graph_rag --document-id 2
python manage.py reprocess_graph_rag --document-id 3
```

### Workflow 4: Clean Slate

```bash
# Clear everything and rebuild
python manage.py reprocess_graph_rag --clear-graph --batch-size 5
```

## Next Steps

After reprocessing:

1. **Test queries** to see improvements
2. **Monitor performance** of GraphRAG queries
3. **Check graph visualization** in admin interface
4. **Review entity extraction** in logs
5. **Adjust if needed** based on results

## Support

If you encounter issues:

1. Check logs: `backend/logs/anylab.log`
2. Review error messages in command output
3. Verify services are running (Ollama, Neo4j)
4. Test with `--dry-run` first
5. Start with single document processing

