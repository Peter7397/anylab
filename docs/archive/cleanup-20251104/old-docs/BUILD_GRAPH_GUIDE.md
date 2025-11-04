# 🔨 Building Graph from Existing Documents - Step by Step Guide

## Prerequisites Check

✅ **Neo4j is running** (we verified this)
✅ **Documents exist** (we'll check this)
✅ **Django environment** (we'll set this up)

## Step-by-Step Instructions

### Step 1: Check Neo4j Connection

```bash
# Verify Neo4j is running
docker ps | grep neo4j

# Should show:
# anylab_neo4j   neo4j:5.15-community   ...   Up ... (healthy)
```

### Step 2: Activate Django Environment

```bash
cd backend

# Activate virtual environment
source venv/bin/activate

# If venv doesn't exist, create it:
# python3 -m venv venv
# source venv/bin/activate
# pip install -r requirements.txt

# Verify Django works
python manage.py --version
```

### Step 3: Check Available Documents

```bash
# In Django shell
python manage.py shell
```

Then run:
```python
from ai_assistant.models import UploadedFile, DocumentChunk

# Count total documents
total = UploadedFile.objects.count()
print(f"Total documents: {total}")

# Count ready documents (with chunks)
ready = UploadedFile.objects.filter(
    processing_status='ready',
    chunks_created=True
)
print(f"Ready documents: {ready.count()}")

# Show first few
for f in ready[:5]:
    chunks = DocumentChunk.objects.filter(uploaded_file=f)
    print(f"ID: {f.id}, File: {f.filename}, Chunks: {chunks.count()}")
```

### Step 4: Test Neo4j Connection

Still in Django shell:
```python
from ai_assistant.services.neo4j_service import get_neo4j_service

neo4j = get_neo4j_service()

# Test connection
if neo4j.test_connection():
    print("✅ Neo4j connected!")
    
    # Create constraints/indexes (important!)
    neo4j.create_constraints()
    print("✅ Constraints created!")
    
    # Get current stats
    stats = neo4j.get_graph_stats()
    print(f"Current graph: {stats['total_nodes']} nodes, {stats['total_relationships']} relationships")
else:
    print("❌ Connection failed - check Neo4j is running")
```

### Step 5: Build Graph

#### Option A: Build from ALL Ready Documents
```bash
python manage.py build_graph
```

#### Option B: Build from Specific Document
```bash
python manage.py build_graph --document-id 1
```

#### Option C: Build in Batches
```bash
python manage.py build_graph --batch-size 20
```

#### Option D: Build with Status Filter
```bash
python manage.py build_graph --status ready
```

### Step 6: Monitor Progress

The command will show:
```
Starting graph construction...
Found X document(s) to process
Processing: filename.pdf (ID: 1)...
  ✅ Success: 15 entities, 23 relationships
Processing: filename2.pdf (ID: 2)...
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

### Step 7: Verify in Neo4j Browser

1. Open http://localhost:7474
2. Login: `neo4j` / `anylab_neo4j_password`

3. Try these queries:

```cypher
// Count all nodes
MATCH (n) RETURN count(n) AS total_nodes

// View all documents
MATCH (d:Document) RETURN d LIMIT 10

// View all entities
MATCH (e:Entity) RETURN e LIMIT 10

// View document-entity relationships
MATCH (d:Document)-[:CONTAINS]->(e:Entity)
RETURN d, e LIMIT 20

// Find specific entity type
MATCH (e:Entity {type: 'PRODUCT'}) RETURN e

// Count entities by type
MATCH (e:Entity)
RETURN e.type, count(e) AS count
ORDER BY count DESC

// View graph visualization
MATCH (d:Document)-[:CONTAINS]->(e:Entity)
RETURN d, e LIMIT 50
```

## Quick Command Reference

```bash
# Full process in one go (using helper script)
./build-graph.sh

# Or manually:
cd backend
source venv/bin/activate
python manage.py build_graph
```

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'django'"
**Solution:** Activate virtual environment
```bash
cd backend
source venv/bin/activate
```

### Issue: "Neo4j connection failed"
**Solution:** Check Neo4j is running
```bash
docker ps | grep neo4j
docker compose up -d neo4j
```

### Issue: "No documents found to process"
**Solution:** Check document status
```bash
python manage.py shell
>>> from ai_assistant.models import UploadedFile
>>> UploadedFile.objects.filter(processing_status='ready', chunks_created=True).count()
```

### Issue: "No chunks found for document"
**Solution:** Document needs to be processed first
- Documents need `chunks_created=True` and `processing_status='ready'`
- If chunks are missing, the document needs to be reprocessed

## Expected Results

After successful build, you should see:
- **Document nodes** in Neo4j (one per uploaded file)
- **Entity nodes** (products, versions, error codes, etc.)
- **CONTAINS relationships** (documents → entities)
- **RELATED_TO relationships** (entities → entities)

## Next Steps After Building

1. ✅ Graph built
2. ⏭️ View in Neo4j Browser
3. ⏭️ Week 5: Implement hybrid search combining vector + graph
4. ⏭️ Test queries with entity relationships

---

**Need Help?** Check `GRAPH_RAG_WEEK2_COMPLETE.md` for more details.

