# 🔍 Advanced Neo4j Exploration Queries

Advanced queries to explore your knowledge graph in differing ways!

## 🎯 Entity Discovery

### Find Most Mentioned Products
```cypher
MATCH (e:Entity {type: 'PRODUCT'})
RETURN e.name, e.normalized_name, e.occurrence_count
ORDER BY e.occurrence_count DESC
LIMIT 20
```

### Find All Version References
```cypher
MATCH (e:Entity {type: 'VERSION'})
RETURN DISTINCT e.name, count(*) AS occurrences
ORDER BY occurrences DESC
```

### Find Error Codes and Their Context
```cypher
MATCH (d:Document)-[r:CONTAINS]->(e:Entity {type: 'ERROR_CODE'})
RETURN d.filename, e.name AS error_code, r.context
LIMIT 20
```

## 🔗 Relationship Analysis

### Documents Sharing Multiple Entities
```cypher
MATCH (d1:Document)-[:CONTAINS]->(e:Entity)<-[:CONTAINS]-(d2:Document)
WHERE d1 <> d2
WITH d1, d2, collect(e.name) AS shared_entities
WHERE size(shared_entities) >= 3
RETURN d1.filename, d2.filename, shared_entities
ORDER BY size(shared_entities) DESC
LIMIT 10
```

### Entity Co-occurrence Matrix
```cypher
MATCH (e1:Entity)-[:RELATED_TO]-(e2:Entity)
WHERE e1.type <> e2.type
RETURN e1.type AS type1, e2.type AS type2, count(*) AS co_occurrences
ORDER BY co_occurrences DESC
```

### Products with Their Versions
```cypher
MATCH (p:Entity {type: 'PRODUCT'})
MATCH (v:Entity {type: 'VERSION'})
MATCH (d:Document)-[:CONTAINS]->(p)
MATCH (d)-[:CONTAINS]->(v)
WITH p, v, collect(DISTINCT d.filename) AS documents
RETURN p.name AS product, v.name AS version, documents
LIMIT 30
```

## 📊 Statistical Analysis

### Document Richness (entities per document)
```cypher
MATCH (d:Document)
OPTIONAL MATCH (d)-[:CONTAINS]->(e:Entity)
RETURN d.filename, 
       count(e) AS total_entities,
       collect(DISTINCT e.type) AS entity_types
ORDER BY total_entities DESC
LIMIT 20
```

### Entity Distribution by Document Type
```cypher
MATCH (d:Document)-[:CONTAINS]->(e:Entity)
WHERE d.filename CONTAINS '.pdf'
RETURN 
  CASE 
    WHEN d.filename CONTAINS 'Guide' THEN 'Guide'
    WHEN d.filename CONTAINS 'Release' THEN 'Release Notes'
    WHEN d.filename CONTAINS 'Requirements' THEN 'Requirements'
    ELSE 'Other'
  END AS doc_type,
  e.type AS entity_type,
  count(*) AS count
ORDER BY doc_type, count DESC
```

### Most Connected Entities
```cypher
MATCH (e:Entity)-[r:RELATED_TO]-(other:Entity)
RETURN e.name, e.type, count(r) AS connection_count
ORDER BY connection_count DESC
LIMIT 20
```

## 🔎 Specific Domain Queries

### OpenLab CDS Ecosystem
```cypher
MATCH (d:Document)-[:CONTAINS]->(e:Entity)
WHERE e.name CONTAINS 'OpenLab CDS' OR e.name CONTAINS 'CDS'
RETURN DISTINCT d.filename, 
       collect(DISTINCT e.name) AS related_entities
LIMIT 20
```

### Version 2.8 Complete Analysis
```cypher
MATCH (v:Entity {type: 'VERSION'})
WHERE v.name CONTAINS '2.8'
MATCH (d:Document)-[:CONTAINS]->(v)
MATCH (d)-[:CONTAINS]->(e:Entity)
RETURN DISTINCT d.filename, 
       v.name AS version,
       collect(DISTINCT e.name) AS entities_in_doc
LIMIT 15
```

### Error Code Analysis
```cypher
MATCH (e:Entity {type: 'ERROR_CODE'})
MATCH (d:Document)-[r:CONTAINS]->(e)
RETURN e.name AS error_code,
       collect(DISTINCT d.filename) AS mentioned_in,
       avg(r.confidence) AS avg_confidence
ORDER BY size(mentioned_in) DESC
```

## 🗺️ Path Finding

### Find Path Between Entities
```cypher
MATCH path = (e1:Entity)-[*..3]-(e2:Entity)
WHERE e1.name CONTAINS 'OpenLab CDS' 
  AND e2.name CONTAINS '2.8'
对的RETURN path
LIMIT 5
```

### Document Clusters by Shared Entities
```cypher
MATCH (d1:Document)-[:CONTAINS]->(e:Entity)<-[:CONTAINS]-(d2:Document)
WHERE d1 <> d2
WITH d1, d2, count(e) AS shared_count
WHERE shared_count >= 5
RETURN d1.filename AS doc1, d2.filename AS doc2, shared_count
ORDER BY shared_count DESC
LIMIT 20
```

## 📈 Trend Analysis

### Entity Frequency by Document Upload Date
```cypher
MATCH (d:Document)-[:CONTAINS]->(e:Entity {type: 'PRODUCT'})
RETURN date(d.uploaded_at) AS upload_date, 
       e.name, 
       count(*) AS mentions
ORDER BY upload_date DESC, mentions DESC
LIMIT 30
```

## 🎨 Visualization Queries

### Graph Overview - Products and Versions
```cypher
MATCH (p:Entity {type: 'PRODUCT'})
MATCH (v:Entity {type: 'VERSION'})
MATCH (d:Document)-[:CONTAINS]->(p)
MATCH (d)-[:CONTAINS]->(v)
RETURN p, v, d
LIMIT 50
```

### Problem-Solution Network
```cypher
MATCH (prob:Entity {type: 'PROBLEM'})
MATCH (sol:Entity {type: 'SOLUTION'})
MATCH (d:Document)-[:CONTAINS]->(prob)
MATCH (d)-[:CONTAINS]->(sol)
RETURN prob, sol, d
LIMIT 30
```

## 🔍 Search and Filter

### Find Documents by Multiple Criteria
```cypher
MATCH (d:Document)-[:CONTAINS]->(e1:Entity {type: 'PRODUCT'})
MATCH (d)-[:CONTAINS]->(e2:Entity {type: 'VERSION'})
WHERE e1.name CONTAINS 'OpenLab'
  AND e2.name CONTAINS '2.8'
RETURN DISTINCT d.filename, 
       collect(DISTINCT e1.name) AS products,
       collect(DISTINCT e2.name) AS versions
```

### High Confidence Entities Only
```cypher
MATCH (d:Document)-[r:CONTAINS]->(e:Entity)
WHERE r.confidence > 0.7
RETURN d.filename, e.name, e.type, r.confidence
ORDER BY r.confidence DESC
LIMIT 30
```

---

**Tip**: Click the graph visualization icon in Neo4j Browser to see these as interactive graphs!

