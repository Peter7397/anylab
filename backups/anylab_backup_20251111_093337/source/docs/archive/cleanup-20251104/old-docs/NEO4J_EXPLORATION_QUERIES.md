# 🔍 Neo4j Graph Exploration Queries

Use these queries in Neo4j Browser (http://localhost:7474) to explore your knowledge graph!

## 📊 Basic Queries

### View All Documents
```cypher
MATCH (d:Document) 
RETURN d 
ORDER BY d.uploaded_at DESC 
LIMIT 20
```

### View All Entities
```cypher
MATCH (e:Entity) 
RETURN e 
LIMIT 20
```

### Count Statistics
```cypher
// Total counts
MATCH (n) 
RETURN count(n) AS total_nodes;

MATCH ()-[r]->() 
RETURN count(r) AS total_relationships;
```

## 🏷️ Entity Type Analysis

### Count Entities by Type
```cypher
MATCH (e:Entity)
RETURN e.type AS entity_type, count(e) AS count
ORDER BY count DESC
```

### Find Specific Entity Types
```cypher
// All Products
MATCH (e:Entity {type: 'PRODUCT'})
RETURN e
LIMIT 20

// All Versions
MATCH (e:Entity {type: 'VERSION'})
RETURN e.name, e.occurrence_count
ORDER BY e.occurrence_count DESC

// All Error Codes
MATCH (e:Entity {type: 'ERROR_CODE'})
RETURN e
```

## 🔗 Relationship Queries

### Document-Entity Connections
```cypher
// See which documents contain which entities
MATCH (d:Document)-[r:CONTAINS]->(e:Entity)
RETURN d.filename, e.name, e.type, r.confidence
LIMIT 50
```

### Find Documents by Entity
```cypher
// Find documents mentioning "OpenLab CDS"
MATCH (d:Document)-[:CONTAINS]->(e:Entity)
WHERE e.name CONTAINS 'OpenLab CDS' OR e.normalized_name CONTAINS 'openlab cds拍'
RETURN DISTINCT d, e
```

### Entity Co-occurrence
```cypher
// Find entities that appear together
MATCH (e1:Entity)-[:RELATED_TO]-(e2:Entity)
RETURN e1.name, e2.name, e1.type, e2.type
LIMIT 30
```

## 🔍 Search Queries

### Find Specific Product Mentions
```cypher
MATCH (d:Document)-[:CONTAINS]->(e:Entity {type: 'PRODUCT'})
WHERE e.name CONTAINS 'OpenLab'
RETURN d.filename, e.name, e.normalized_name
ORDER BY d.filename
```

### Find Version References
```cypher
// Find all documents mentioning version 2.8
MATCH (d:Document)-[:CONTAINS]->(e:Entity {type: 'VERSION'})
WHERE e.name CONTAINS '2.8'
RETURN DISTINCT d.filename, e.name
```

### Find Error Codes
```cypher
MATCH (d:Document)-[:CONTAINS]->(e:Entity {type: 'ERROR_CODE'})
RETURN d.filename, e.name
ORDER BY d.filename
```

## 📈 Advanced Queries

### Most Connected Documents
```cypher
// Documents with most entities
MATCH (d:Document)-[:CONTAINS]->(e:Entity)
RETURN d.filename, count(e) AS entity_count
ORDER BY entity_count DESC
LIMIT 10
```

### Most Common Entities
```cypher
// Entities that appear in most documents
MATCH (d:Document)-[:CONTAINS]->(e:Entity)
RETURN e.name, e.type, count(DISTINCT d) AS document_count
ORDER BY document_count DESC
LIMIT 20
```

### Entity Relationships Graph
```cypher
// Visualize entity relationships
MATCH (e1:Entity)-[:RELATED_TO]->(e2:Entity)
RETURN e1, e2
LIMIT 50
```

### Find Related Documents
```cypher
// Documents that share entities (potential related docs)
MATCH (d1:Document)-[:CONTAINS]->(e:Entity)<-[:CONTAINS]-(d2:Document)
WHERE d1 <> d2
RETURN d1.filename, d2.filename, count(e) AS shared_entities
ORDER BY shared_entities DESC
LIMIT 20
```

## 🎨 Visualization Queries

### Graph Overview
```cypher
// See the whole graph structure (be careful - might be large!)
MATCH (d:Document)-[:CONTAINS]->(e:Entity)
RETURN d, e
LIMIT 100
```

### Product-Version Relationships
```cypher
// Find products and their versions
MATCH (p:Entity {type: 'PRODUCT'})
MATCH (v:Entity {type: 'VERSION'})
MATCH (d:Document)-[:CONTAINS]->(p)
MATCH (d)-[:CONTAINS]->(v)
RETURN p.name, v.name, d.filename
LIMIT 30
```

### Problem-Solution Pairs
```cypher
// Find problems and their solutions
MATCH (prob:Entity {type: 'PROBLEM'})
MATCH (sol:Entity {type: 'SOLUTION'})
MATCH (d:Document)-[:CONTAINS]->(prob)
MATCH (d)-[:CONTAINS]->(sol)
RETURN prob.name, sol.name, d.filename
LIMIT 20
```

## 🔎 Specific Searches

### Find OpenLab CDS Documents
```cypher
MATCH (d:Document)-[:CONTAINS]->(e:Entity)
WHERE e.type = 'PRODUCT' AND (e.name CONTAINS 'OpenLab CDS' OR e.normalized_name CONTAINS 'openlab cds')
RETURN DISTINCT d.filename, d.id
```

### Find v2.8 Related Content
```cypher
MATCH (d:Document)-[:CONTAINS]->(e:Entity)
WHERE e.type = 'VERSION' AND e.name CONTAINS '2.8'
RETURN DISTINCT d.filename, e.name
ORDER BY d.filename
```

### Find Documents by Entity Count
```cypher
MATCH (d:Document)
OPTIONAL MATCH (d)-[:CONTAINS]->(e:Entity)
RETURN d.filename, count(e) AS entity_count
ORDER BY entity_count DESC
```

## 💡 Tips

1. **Use LIMIT** - Large queries can be slow, always use LIMIT
2. **Visualize** - Click the graph visualization icon to see connections
3. **Filter** - Use WHERE clauses to narrow results
4. **Count First** - Run count queries before returning full results

## 🚀 Next Steps

Now that you can explore the graph, you're ready for:
- **Week 5**: Implement hybrid search (vector + graph)
- Create GraphRAG service
- Enhanced query responses using graph context

---

Enjoy exploring your knowledge graph! 🎉

