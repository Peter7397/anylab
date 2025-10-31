# Graph RAG Migration Plan for AnyLab0812

## Executive Summary

This document outlines options for converting the current vector-based RAG system to a Graph RAG architecture. Graph RAG enhances traditional RAG by storing entities and relationships in a graph database, enabling richer query capabilities, better context understanding, and more accurate responses.

## Current Architecture Analysis

### Existing Components
- **Vector Database**: PostgreSQL with pgvector extension
- **Embeddings**: BGE-M3 (1024 dimensions) via Ollama
- **Entity Extraction**: Basic NER via spaCy (exists but not stored)
- **Metadata**: Rich schemas (ProductCategory, DocumentType, ContentCategory)
- **Relationships**: Implicit (related_documents, dependencies) stored as lists
- **Chunking**: Document chunks stored with embeddings

### Current Limitations
1. **No explicit entity storage**: Entities are extracted but not persisted
2. **Flat relationship model**: Relationships stored as JSON lists, not queryable
3. **Limited contextual reasoning**: Vector search finds similar chunks but doesn't understand entity relationships
4. **No knowledge graph**: No graph structure to navigate concepts

---

## Migration Options

### Option 1: Hybrid Vector + Graph RAG (Recommended)
**Difficulty**: Medium | **Timeline**: 4-6 weeks | **Risk**: Low

#### Architecture
- Keep PostgreSQL + pgvector for vector similarity search
- Add Neo4j or ArangoDB for graph storage
- Implement dual retrieval: Vector search + Graph traversal
- Merge results using reranking

#### Benefits
- ✅ Best of both worlds: Semantic similarity + structured knowledge
- ✅ Minimal disruption to existing system
- ✅ Gradual migration possible
- ✅ Can leverage existing vector infrastructure

#### Implementation Steps
1. **Phase 1: Graph Database Setup** (Week 1)
   - Install Neo4j/ArangoDB
   - Design graph schema (entities, relationships)
   - Create migration scripts

2. **Phase 2: Entity Extraction Enhancement** (Week 2)
   - Enhance existing entity extraction (ai_content_analyzer.py)
   - Extract: Products, Software, Versions, Problems, Solutions, Authors
   - Create entity linking/disambiguation

3. **Phase 3: Graph Construction** (Week 3-4)
   - Build graph from existing documents
   - Create nodes: Document, Entity, Category, User
   - Create relationships: CONTAINS, RELATED_TO, DEPENDS_ON, MENTIONS, SOLVES

4. **Phase 4: Hybrid Retrieval** (Week 5)
   - Implement GraphRAGService combining vector + graph search
   - Query graph for entity relationships
   - Merge results with vector search results

5. **Phase 6: Testing & Optimization** (Week 6)
   - Test query accuracy improvements
   - Optimize graph queries
   - Performance tuning

#### Technology Stack
- **Graph DB**: Neo4j Community Edition (or ArangoDB)
- **Graph Client**: `neo4j` Python driver
- **Entity Linking**: spaCy NER + custom rules
- **Query Engine**: Cypher (Neo4j) or AQL (ArangoDB)

#### Example Graph Schema
```
(Document)-[:CONTAINS]->(Entity)
(Document)-[:RELATED_TO]->(Document)
(Entity)-[:MENTIONS]->(Entity)
(Entity)-[:OCCURS_IN]->(Document)
(Product)-[:VERSION]->(Version)
(Problem)-[:SOLVED_BY]->(Solution)
(Solution)-[:DEPENDS_ON]->(Product)
```

#### Cost
- **Development**: 4-6 weeks
- **Infrastructure**: Neo4j Community (free) or cloud (~$50-200/month)
- **Complexity**: Medium

---

### Option 2: Full Graph RAG with Vector Embeddings as Properties
**Difficulty**: High | **Timeline**: 6-8 weeks | **Risk**: Medium-High

#### Architecture
- Migrate entirely to graph database (Neo4j or ArangoDB)
- Store embeddings as node properties
- Use vector similarity within graph queries
- Replace PostgreSQL vector storage

#### Benefits
- ✅ Single source of truth
- ✅ Native graph traversal capabilities
- ✅ Unified query language
- ✅ Better relationship reasoning

#### Challenges
- ❌ Larger migration effort
- ❌ Requires data migration from PostgreSQL
- ❌ Need to rebuild existing functionality
- ❌ Learning curve for graph query languages

#### Implementation Steps
1. **Phase 1: Graph Schema Design** (Week 1-2)
   - Design comprehensive graph schema
   - Plan data migration strategy
   - Create migration scripts

2. **Phase 2: Data Migration** (Week 3-4)
   - Export data from PostgreSQL
   - Transform to graph structure
   - Import into graph database
   - Verify data integrity

3. **Phase 3: Vector Search in Graph** (Week 5-6)
   - Implement vector similarity in graph queries
   - Use graph + vector hybrid queries
   - Optimize for performance

4. **Phase 4: Service Migration** (Week 7)
   - Rewrite RAG services for graph
   - Update API endpoints
   - Migrate frontend if needed

5. **Phase 5: Testing** (Week 8)
   - Comprehensive testing
   - Performance benchmarking
   - Bug fixes

#### Technology Stack
- **Graph DB**: Neo4j (with vector extension) or ArangoDB
- **Vector Search**: Neo4j GDS or ArangoDB vector search

#### Cost
- **Development**: 6-8 weeks
- **Infrastructure**: Neo4j Enterprise (~$200-500/month) or ArangoDB Cloud
- **Complexity**: High

---

### Option 3: Lightweight Graph Layer (Minimal Change)
**Difficulty**: Low | **Timeline**: 2-3 weeks | **Risk**: Very Low

#### Architecture
- Keep existing PostgreSQL + pgvector
- Add lightweight graph layer using PostgreSQL's JSON/JSONB
- Use recursive CTEs for graph traversal
- Implement basic entity extraction

#### Benefits
- ✅ Minimal infrastructure changes
- ✅ No new database required
- ✅ Quick implementation
- ✅ Low risk

#### Limitations
- ⚠️ Limited graph capabilities (no native graph algorithms)
- ⚠️ Performance may not scale as well
- ⚠️ More complex queries harder to implement

#### Implementation Steps
1. **Phase 1: Entity Model Enhancement** (Week 1)
   - Add Entity model to Django
   - Add Relationship model
   - Store relationships in PostgreSQL

2. **Phase 2: Entity Extraction** (Week 1-2)
   - Enhance entity extraction from documents
   - Extract and store entities
   - Create relationships

3. **Phase 3: Graph Queries** (Week 2-3)
   - Implement graph traversal using SQL recursive CTEs
   - Combine with vector search
   - Test and optimize

#### Technology Stack
- **Database**: PostgreSQL (existing)
- **Graph Storage**: JSONB tables with relationships
- **Query**: SQL recursive CTEs

#### Cost
- **Development**: 2-3 weeks
- **Infrastructure**: No additional cost
- **Complexity**: Low

---

### Option 4: Incremental Migration (Hybrid Approach)
**Difficulty**: Medium | **Timeline**: 8-10 weeks (phased) | **Risk**: Low

#### Architecture
- Start with Option 1 (Hybrid)
- Gradually migrate more functionality to graph
- Keep PostgreSQL for operational data
- Use graph for knowledge graph

#### Benefits
- ✅ Lowest risk approach
- ✅ Allows learning and iteration
- ✅ Can pause at any phase
- ✅ Production continues throughout

#### Implementation Phases
1. **Phase 1**: Add graph DB, extract entities (Weeks 1-2)
2. **Phase 2**: Build basic graph, hybrid search (Weeks 3-4)
3. **Phase 3**: Enhance entity extraction (Weeks 5-6)
4. **Phase 4**: Add advanced graph queries (Weeks 7-8)
5. **Phase 5**: Optimize and scale (Weeks 9-10)

#### Cost
- **Development**: 8-10 weeks (flexible)
- **Infrastructure**: Starts with free tier, scales as needed
- **Complexity**: Medium (spread over time)

---

## Comparison Matrix

| Feature | Option 1: Hybrid | Option 2: Full Graph | Option 3: Lightweight | Option 4: Incremental |
|---------|-----------------|---------------------|----------------------|---------------------|
| **Timeline** | 4-6 weeks | 6-8 weeks | 2-3 weeks | 8-10 weeks |
| **Risk** | Low | Medium-High | Very Low | Low |
| **Performance** | Excellent | Excellent | Good | Excellent |
| **Complexity** | Medium | High | Low | Medium |
| **Scalability** | Excellent | Excellent | Limited | Excellent |
| **Cost** | $$ | $$$ | $ | $$ |
| **Learning Curve** | Medium | High | Low | Medium |
| **Best For** | Production ready | Long-term | Quick win | Large teams |

---

## Recommended Approach: Option 1 (Hybrid Vector + Graph RAG)

### Why Option 1?
1. **Balanced**: Good performance without over-engineering
2. **Proven**: Hybrid approaches are industry standard
3. **Flexible**: Can migrate to Option 2 later if needed
4. **Risk**: Low disruption to existing system
5. **Timeline**: Reasonable for production use

### Detailed Implementation Plan for Option 1

#### Step 1: Graph Database Setup (Week 1)

**Tasks:**
- [ ] Choose graph database (recommend Neo4j Community)
- [ ] Install Neo4j locally/Docker
- [ ] Design graph schema
- [ ] Create Django models for graph synchronization
- [ ] Set up connection pooling

**Graph Schema Design:**
```cypher
// Nodes
Document {id, title, filename, type, url}
Entity {id, name, type, description}
Product {id, name, category, version}
Software {id, name, platform, version}
Problem {id, description, severity, error_code}
Solution {id, description, type, difficulty}
Category {id, name, type}
User {id, username, role}

// Relationships
(Document)-[:CONTAINS {confidence}]->(Entity)
(Document)-[:MENTIONS {frequency}]->(Product)
(Document)-[:RELATED_TO {strength}]->(Document)
(Document)-[:DESCRIBES]->(Problem)
(Document)-[:SOLVES]->(Problem)
(Problem)-[:SOLVED_BY {success_rate}]->(Solution)
(Product)-[:VERSION]->(Version)
(Entity)-[:OCCURS_WITH {co_occurrence}]->(Entity)
(Category)-[:HAS_SUBCATEGORY]->(Category)
```

#### Step 2: Enhanced Entity Extraction (Week 2)

**Tasks:**
- [ ] Enhance `ai_content_analyzer.py` entity extraction
- [ ] Add entity linking/disambiguation
- [ ] Extract domain-specific entities:
  - Products: OpenLab CDS, 7890B GC, etc.
  - Software versions: v2.8, v3.6
  - Error codes: M84xx, KPR numbers
  - Problems: Database connection, performance issues
- [ ] Create entity normalization service
- [ ] Store entities in both PostgreSQL and Neo4j

**Entity Types to Extract:**
```python
ENTITY_TYPES = [
    'PRODUCT',           # Product names
    'SOFTWARE',          # Software platforms
    'VERSION',           # Version numbers
    'PROBLEM',           # Issues/problems
    'SOLUTION',          # Solutions/fixes
    'ERROR_CODE',        # Error codes
    'KPR_NUMBER',        # KPR identifiers
    'CATEGORY',          # Content categories
    'INSTRUMENT',        # Instruments
    'PROTOCOL',          # Protocols/procedures
    'ORGANIZATION',      # Companies/organizations
    'PERSON',            # Authors/contributors
]
```

#### Step 3: Graph Construction Pipeline (Week 3-4)

**Tasks:**
- [ ] Create `graph_builder.py` service
- [ ] Batch process existing documents
- [ ] Extract entities and relationships
- [ ] Build graph incrementally
- [ ] Create relationships between entities
- [ ] Index graph for performance

**Graph Construction Logic:**
```python
def build_graph_from_document(document):
    # Extract entities
    entities = extract_entities(document.content)
    
    # Create document node
    doc_node = create_document_node(document)
    
    # Create entity nodes and relationships
    for entity in entities:
        entity_node = get_or_create_entity(entity)
        create_relationship(doc_node, 'CONTAINS', entity_node)
        
        # Create co-occurrence relationships
        for other_entity in entities:
            if entity != other_entity:
                increment_co_occurrence(entity, other_entity)
    
    # Extract document relationships
    for related_doc_id in document.related_documents:
        related_doc = get_document(related_doc_id)
        create_relationship(doc_node, 'RELATED_TO', related_doc)
```

#### Step 4: Hybrid Retrieval Service (Week 5)

**Tasks:**
- [ ] Create `graph_rag_service.py`
- [ ] Implement graph query methods
- [ ] Combine vector and graph results
- [ ] Implement reranking logic
- [ ] Add graph context to RAG prompts

**Hybrid Retrieval Algorithm:**
```python
def hybrid_search(query):
    # Step 1: Vector search (existing)
    vector_results = vector_search(query, top_k=20)
    
    # Step 2: Extract entities from query
    query_entities = extract_entities(query)
    
    # Step 3: Graph traversal
    graph_results = []
    for entity in query_entities:
        # Find related documents via graph
        related_docs = graph_traverse(entity, depth=2)
        graph_results.extend(related_docs)
    
    # Step 4: Merge and rerank
    combined_results = merge_results(vector_results, graph_results)
    reranked = rerank(combined_results, query)
    
    return reranked[:10]
```

#### Step 5: Graph-Enhanced RAG Prompts (Week 5)

**Tasks:**
- [ ] Enhance RAG prompts with graph context
- [ ] Include entity relationships in context
- [ ] Add graph path information
- [ ] Improve answer quality with structured knowledge

**Example Enhanced Prompt:**
```
Context from Documents:
[Document content...]

Knowledge Graph Context:
- Related Products: OpenLab CDS v2.8, OpenLab ECM
- Related Problems: Database connection issues (KPR-1476890N)
- Related Solutions: Configure connection pool settings
- Document Relationships: This document is related to "Installation Guide" and "Troubleshooting FAQ"

User Question: {query}

Answer using both document content and knowledge graph relationships.
```

#### Step 6: Testing & Optimization (Week 6)

**Tasks:**
- [ ] Test query accuracy improvements
- [ ] Benchmark performance (latency, throughput)
- [ ] Optimize graph queries
- [ ] Tune entity extraction accuracy
- [ ] A/B test with existing system

---

## Technical Implementation Details

### Graph Database Choice: Neo4j vs ArangoDB

#### Neo4j (Recommended)
**Pros:**
- ✅ Most mature graph database
- ✅ Excellent Python driver
- ✅ Cypher query language (intuitive)
- ✅ Great documentation and community
- ✅ Vector search available (GDS library)

**Cons:**
- ⚠️ Enterprise features require license
- ⚠️ Memory intensive

#### ArangoDB
**Pros:**
- ✅ Multi-model (graph + document + key-value)
- ✅ Built-in vector search
- ✅ Good performance
- ✅ Flexible schema

**Cons:**
- ⚠️ Smaller community
- ⚠️ AQL learning curve

**Recommendation**: Start with Neo4j Community Edition

### Entity Extraction Enhancement

**Current State:**
- Basic spaCy NER exists
- Entities extracted but not stored

**Enhancement Needed:**
```python
# Enhanced entity extractor
class EnhancedEntityExtractor:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.domain_patterns = self._load_domain_patterns()
    
    def extract_entities(self, text, document_id):
        # SpaCy NER
        doc = self.nlp(text)
        entities = []
        
        for ent in doc.ents:
            entity = {
                'text': ent.text,
                'type': self._map_to_domain_type(ent.label_),
                'start': ent.start_char,
                'end': ent.end_char,
                'confidence': 0.8,
                'context': text[max(0, ent.start_char-50):ent.end_char+50]
            }
            entities.append(entity)
        
        # Domain-specific extraction
        domain_entities = self._extract_domain_entities(text)
        entities.extend(domain_entities)
        
        # Entity linking (disambiguation)
        linked_entities = self._link_entities(entities, document_id)
        
        return linked_entities
    
    def _extract_domain_entities(self, text):
        # Extract product names, versions, error codes
        # Use regex + knowledge base
        entities = []
        
        # Product patterns
        products Firms = [
            r'OpenLab\s+(?:CDS|ECM|ELN|Server)',
            r'7890B\s+GC',
            r'MassHunter\s+\w+',
        ]
        
        # Version patterns
        version_pattern = r'(?:v|version|ver\.?)\s*(\d+(?:\.\d+)*)'
        
        # Error code patterns
        error_pattern = r'(?:KPR|M)\d+[A-Z]?\d+[A-Z]?'
        
        return entities
```

### Graph Query Examples

**Find documents mentioning a product:**
```cypher
MATCH (d:Document)-[:CONTAINS]->(e:Entity {type: 'PRODUCT', name: 'OpenLab CDS'})
RETURN d ORDER BY d.created_at DESC LIMIT 10
```

**Find related problems and solutions:**
```cypher
MATCH (p:Problem {error_code: 'M84xx'})-[:SOLVED_BY]->(s:Solution)
MATCH (s)<-[:DESCRIBES]-(d:Document)
RETURN p, s, d
```

**Graph-augmented search:**
```cypher
// Find documents similar to query AND related entities
MATCH (d:Document)
WHERE d.embedding <-> $query_embedding < 0.3
MATCH (d)-[:CONTAINS]->(e:Entity)
MATCH (e)<-[:CONTAINS]-(related:Document)
WHERE related <> d
RETURN DISTINCT related, 
       COUNT(DISTINCT e) as shared_entities
ORDER BY shared_entities DESC, related.relevance_score DESC
LIMIT 10
```

---

## Migration Checklist

### Pre-Migration
- [ ] Backup existing database
- [ ] Document current RAG performance metrics
- [ ] Set up development environment
- [ ] Review and approve graph schema

### Phase 1: Infrastructure
- [ ] Install Neo4j
- [ ] Configure Neo4j connection
- [ ] Create graph schema
- [ ] Set up monitoring

### Phase 2: Entity Extraction
- [ ] Enhance entity extraction
- [ ] Test extraction accuracy
- [ ] Set up entity storage pipeline
- [ ] Validate entity quality

### Phase 3: Graph Building
- [ ] Build graph from existing documents
- [ ] Create entity nodes
- [ ] Create relationships
- [ ] Verify graph integrity

### Phase 4: Hybrid Retrieval
- [ ] Implement graph search
- [ ] Combine with vector search
- [ ] Test query accuracy
- [ ] Optimize performance

### Phase 5: Integration
- [ ] Update API endpoints
- [ ] Update frontend if needed
- [ ] Add monitoring/logging
- [ ] Documentation

### Phase 6: Testing
- [ ] Unit tests
- [ ] Integration tests
- [ ] Performance tests
- [ ] A/B testing with users

### Post-Migration
- [ ] Monitor performance
- [ ] Gather user feedback
- [ ] Optimize based on usage
- [ ] Plan next improvements

---

## Success Metrics

### Quantitative Metrics
- **Query Accuracy**: Improve by 15-25%
- **Response Relevance**: Improve by 20-30%
- **Entity Coverage**: Track entity extraction accuracy
- **Query Latency**: Keep under 500ms (p95)
- **Graph Query Performance**: <100ms for standard queries

### Qualitative Metrics
- **Answer Quality**: More comprehensive, better citations
- **Contextual Understanding**: Better handling of relationships
- **User Satisfaction**: Survey scores

---

## Risks & Mitigations

### Risk 1: Entity Extraction Quality
**Mitigation**: 
- Start with rule-based extraction
- Gradually add ML models
- Human review for critical entities

### Risk 2: Graph Database Performance
**Mitigation**:
- Index frequently queried properties
- Use graph algorithms efficiently
- Monitor query performance
- Scale horizontally if needed

### Risk 3: Data Consistency
**Mitigation**:
- Implement dual-write pattern initially
- Add eventual consistency checks
- Set up monitoring for sync issues

### Risk 4: Migration Complexity
**Mitigation**:
- Use incremental migration (Option 4)
- Test thoroughly in staging
- Have rollback plan

---

## Cost Estimation

### Option 1: Hybrid Approach
- **Development**: 4-6 weeks (1 developer) = $8,000-$12,000
- **Infrastructure**: Neo4j Community (free) or Cloud ($50-200/month)
- **Total First Year**: ~$10,000-$15,000

### Option 2: Full Graph Migration
- **Development**: 6-8 weeks = $12,000-$16,000
- **Infrastructure**: Neo4j Enterprise ($200-500/month) = $2,400-$6,000/year
- **Total First Year**: ~$15,000-$22,000

### Option 3: Lightweight
- **Development**: 2-3 weeks = $4,000-$6,000
- **Infrastructure**: No additional cost
- **Total First Year**: ~$5,000-$7,000

---

## Next Steps

1. **Review Options**: Choose preferred migration approach
2. **POC**: Build small proof-of-concept (1-2 weeks)
3. **Approval**: Get stakeholder approval
4. **Implementation**: Follow chosen option's plan
5. **Iterate**: Continuous improvement based on feedback

---

## Questions to Consider

1. **Timeline**: When do you need this implemented?
2. **Budget**: What's the budget for development and infrastructure?
3. **Risk Tolerance**: How much risk can you accept?
4. **Team Skills**: Does the team have graph database experience?
5. **Scale**: How many documents/entities do you expect?
6. **Priority**: What features are most important?

---

## References

- [Neo4j Documentation](https://neo4j.com/docs/)
- [Graph RAG Research](https://arxiv.org/abs/2309.15320)
- [LangChain Graph RAG](https://python.langchain.com/docs/use_cases/graph/)
- [Neo4j Vector Search](https://neo4j.com/docs/graph-data-science/current/machine-learning/node-embeddings/)

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Author**: AI Assistant  
**Status**: Draft for Review

