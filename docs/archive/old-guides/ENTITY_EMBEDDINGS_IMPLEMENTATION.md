# Entity Embeddings Implementation for GraphRAG

## Overview

This document describes the implementation of entity embeddings for semantic similarity search in GraphRAG. This enhancement enables fuzzy/semantic matching of entities, not just exact ID/name matching, significantly improving query capabilities.

## What Changed

### 1. Graph Builder (`graph_builder.py`)
- **Added**: Embedding generation for entities when creating entity nodes
- **Method**: Uses BGE-M3 model via Ollama to generate 1024-dimensional embeddings
- **Storage**: Embeddings stored as array property in Neo4j entity nodes
- **Context**: Includes entity context (first 200 chars) for better semantic understanding

### 2. Graph Query Service (`graph_query_service.py`)
- **Added**: `_find_similar_entities_by_embedding()` method for semantic entity search
- **Enhanced**: `find_documents_by_entities()` now uses both exact and semantic entity matching
- **Similarity**: Uses cosine similarity with configurable threshold (default: 0.6)
- **Scoring**: Semantic matches weighted at 80% of exact matches to maintain precision

### 3. Backfill Command (`backfill_entity_embeddings.py`)
- **Purpose**: Generate embeddings for existing entities that don't have them
- **Features**:
  - Batch processing (default: 10 entities per batch)
  - Progress tracking
  - Error handling
  - Statistics reporting

## Benefits

1. **Fuzzy Entity Matching**: Queries can now find entities even if they don't match exactly
2. **Better Query Understanding**: Semantic similarity helps find relevant entities for natural language queries
3. **Improved Recall**: Finds more relevant documents by matching semantically similar entities
4. **Backward Compatible**: Existing exact matching still works, semantic matching is additive

## Usage

### For New Entities
Embeddings are automatically generated when new entities are created during document processing.

### For Existing Entities
Run the backfill command to add embeddings to existing entities:

```bash
# Backfill all entities (recommended)
python manage.py backfill_entity_embeddings

# Backfill with custom batch size
python manage.py backfill_entity_embeddings --batch-size 20

# Backfill limited number (for testing)
python manage.py backfill_entity_embeddings --limit 100
```

### Query Behavior
When a query is processed:
1. **Exact Entity Extraction**: Extracts entities from query using LLM/NER
2. **Semantic Entity Search**: Finds semantically similar entities using embeddings
3. **Combined Results**: Merges exact and semantic matches
4. **Document Retrieval**: Finds documents containing matched entities
5. **Scoring**: Exact matches get full weight, semantic matches get 80% weight

## Configuration

### Similarity Threshold
Default: `0.6` (cosine similarity, range: 0-1)
- Higher = more precise but fewer matches
- Lower = more matches but less precise

Can be adjusted in `graph_query_service.py`:
```python
similar_entities = self._find_similar_entities_by_embedding(
    query, 
    max_similar=10, 
    similarity_threshold=0.6  # Adjust here
)
```

### Semantic Match Weight
Default: `0.8` (80% of exact match weight)
- Can be adjusted in `find_documents_by_entities()` method

## Performance Considerations

1. **Embedding Generation**: 
   - ~1-2 seconds per entity (via Ollama)
   - Cached for 24 hours
   - Batch processing recommended for backfill

2. **Similarity Calculation**:
   - Cosine similarity computed in Python (numpy)
   - Currently limited to 1000 entities per query (for performance)
   - Can be optimized with vector indexes if Neo4j version supports it

3. **Storage**:
   - Each embedding: 1024 floats = ~4KB per entity
   - For 3020 entities: ~12MB total storage

## Statistics

After backfilling all entities:
- **Total Entities**: 3,020
- **With Embeddings**: 3,020 (100%)
- **Storage**: ~12MB
- **Query Performance**: ~100-200ms for semantic search (depending on entity count)

## Testing

Test the implementation:

```bash
# Test query with semantic matching
python manage.py test_graph_rag_query "installation guide" --show-entities

# Check embedding coverage
python manage.py shell -c "
from ai_assistant.services.neo4j_service import get_neo4j_service
neo4j = get_neo4j_service()
result = neo4j.execute_query('MATCH (e:Entity) RETURN count(e) AS total, count(e.embedding) AS with_emb')
print(f\"Coverage: {result[0]['with_emb']}/{result[0]['total']}\")
"
```

## Future Enhancements

1. **Vector Indexes**: Use Neo4j vector indexes (5.11+) for faster similarity search
2. **Batch Similarity**: Optimize similarity calculation for large entity sets
3. **Adaptive Thresholds**: Adjust similarity threshold based on query type
4. **Embedding Updates**: Re-generate embeddings when entity context changes significantly

## Troubleshooting

### Embeddings Not Generated
- Check Ollama is running: `curl http://localhost:11434/api/tags`
- Check BGE-M3 model is available: `ollama list | grep bge-m3`
- Check logs for errors: `tail -f logs/anylab.log | grep embedding`

### Low Similarity Scores
- Lower the similarity threshold (try 0.5 instead of 0.6)
- Check if entity names are too different from query terms
- Verify embeddings are stored correctly in Neo4j

### Performance Issues
- Reduce `max_similar` parameter (default: 10)
- Reduce entity limit in similarity search (currently 1000)
- Consider using vector indexes if available

