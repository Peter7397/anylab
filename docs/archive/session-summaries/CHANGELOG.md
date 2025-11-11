# Changelog

All notable changes to AnyLab will be documented in this file.

## [1.2.0] - 2025-11-10

### Added - GraphRAG Entity Embeddings & Semantic Search

#### Entity Embeddings
- **Entity Embeddings System**: All 3,020 entities now have semantic embeddings (100% coverage)
- **Semantic Similarity Search**: Find entities by meaning using cosine similarity (threshold: 0.6)
- **BGE-M3 Embeddings**: 1024-dimensional vectors stored in Neo4j
- **Backfill Command**: New `backfill_entity_embeddings` management command
- **LLM-based Extraction**: Enhanced entity extraction using Ollama

#### Dashboard Integration
- **GraphRAG Statistics Section**: Real-time entity embedding and graph metrics on dashboard
- **Visual Progress Bars**: Animated progress indicators for embedding coverage
- **Color-Coded Metrics**: Purple (embeddings), Blue (entities), Green (nodes), Indigo (queries)
- **Recent Queries Display**: Shows last 5 GraphRAG queries with timestamps
- **Entity Embedding Coverage**: Visual tracking of semantic search readiness

#### Backend Enhancements
- Enhanced `graph_builder.py` with automatic embedding generation
- Updated `graph_query_service.py` with semantic entity search
- Improved `graph_rag_service.py` to return semantic match information
- Extended `dashboard_views.py` with GraphRAG statistics
- New `backfill_entity_embeddings.py` management command

#### Frontend Enhancements
- Updated `Dashboard.tsx` with new GraphRAG section
- Enhanced `GraphRagSearch.tsx` with semantic entity interfaces
- Prepared UI for displaying exact vs semantic entity matches
- Added responsive design with gradient backgrounds

#### Documentation
- Complete GraphRAG session summary
- Entity embeddings implementation guide
- Dashboard integration documentation
- Frontend update guide
- Master documentation index (45 files organized)
- Housekeeping and cleanup reports

### Improved

#### GraphRAG Performance
- Semantic matching complements exact entity matching
- Better recall: finds more relevant documents
- Weighted scoring: semantic matches at 80% of exact matches
- Query performance: ~100-200ms for semantic search

#### System Organization
- Cleaned up ~55 Mac metadata files
- Created master documentation index
- Organized 45 documentation files by topic
- Added quick start guides for different user types

### Technical Details

#### Knowledge Graph Statistics
- Total Nodes: 3,119
- Total Relationships: 5,107
- Documents Indexed: 99
- Entity Types: 16

#### Performance Metrics
- Embedding Generation: ~1-2 seconds per entity
- Semantic Search: ~100-200ms per query
- Cache Hit Rate: High (24-hour TTL)
- System Health: ✅ No issues

### Configuration

#### New Settings
- `similarity_threshold`: 0.6 (cosine similarity for semantic search)
- `max_similar_entities`: 10 (limit for semantic matches per query)
- `semantic_match_weight`: 0.8 (80% of exact match weight)

---

## [1.1.0] - 2025-11-09

### Added
- Initial GraphRAG improvements
- Enhanced entity extraction (CONCEPT, KEY_TERM, PROCEDURE, etc.)
- Importance scoring for document chunks
- Graph-enhanced hybrid search

### Improved
- Entity extraction with LLM support
- Document processing with graph building
- Query expansion and reranking

---

## [1.0.0] - 2025-11-08

### Initial Release
- Core RAG system with vector search
- Document upload and processing
- Neo4j knowledge graph integration
- Basic entity extraction
- User authentication and permissions
- Forum and help portal features

---

## Version Format

`MAJOR.MINOR.PATCH (build BUILD_NUMBER)`

- **MAJOR**: Breaking changes or major feature releases
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, minor improvements
- **BUILD**: Incremental build number

## Links

- Dashboard: https://anylab.dpdns.org/dashboard
- GraphRAG Search: https://anylab.dpdns.org/ai/graph-rag
- Documentation: See DOCUMENTATION_INDEX.md

