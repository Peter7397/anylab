# 🚀 Quick Guide: Build Graph from Documents

## ✅ Prerequisites (Already Done!)

- ✅ Neo4j is running (`docker ps | grep neo4j` shows it's up)
- ✅ Services created (entity extractor, graph builder)
- ✅ Management command ready

## 📋 Simple Steps

### Step 1: Activate Environment

```bash
cd backend
source venv/bin/activate
```

### Step 2: Install Neo4j Package (if needed)

```bash
pip install neo4j==5.20.0
```

### Step 3: Test Neo4j Connection

```bash
python manage.py shell
```

Then:
```python
from ai_assistant.services.neo4j_service import get_neo4j_service

neo4j = get_neo4j_service()
if neo4j.test_connection():
    print("✅ Connected!")
    neo4j.create_constraints()  # Create indexes
```

### Step 4: Build Graph

```bash
# Exit shell first (Ctrl+D or exit())
python manage.py build_graph
```

## 🎯 What You'll See

The command will:
1. Find all ready documents
2. Extract entities from each document
3. Create nodes in Neo4j
4. Create relationships
5. Show progress and statistics

Example output:
```
Starting graph construction...
Found 10 document(s) to process
Processing: document1.pdf (ID: 1)...
  ✅ Success: 15 entities, 23 relationships
Processing: document2.pdf (ID: 2)...
  ✅ Success: 12 entities, 18 relationships
...
Graph Construction Summary:
  Total documents: 10
  Processed: 10
  Successful: 10
  Failed: 0

Graph Statistics:
  Total nodes: 125
  Total relationships: 156

✅ Graph construction complete!
```

## 🔍 Verify Results

Open Neo4j Browser: http://localhost:7474

Try these queries:

```cypher
// View all documents
MATCH (d:Document) RETURN d LIMIT 10

// View all entities
MATCH (e:Entity) RETURN e LIMIT 10

// See document-entity relationships
MATCH (d:Document)-[:CONTAINS]->(e:Entity)
RETURN d, e LIMIT 20

// Count entities by type
MATCH (e:Entity)
RETURN e.type, count(e) AS count
ORDER BY count DESC
```

## 🆘 Troubleshooting

**"No module named 'neo4j'"**
```bash
pip install neo4j==5.20.0
```

**"Connection failed"**
- Check Neo4j: `docker ps | grep neo4j`
- Start if needed: `docker compose up -d neo4j`

**"No documents found"**
- Check documents have `processing_status='ready'` and `chunks_created=True`
- You may need to process documents first

**Need more help?** See `BUILD_GRAPH_GUIDE.md` for detailed instructions.

---

**Ready to build?** Just run:
```bash
cd backend && source venv/bin/activate && python manage.py build_graph
```

