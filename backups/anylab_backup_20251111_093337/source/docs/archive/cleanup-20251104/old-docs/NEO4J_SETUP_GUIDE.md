# Neo4j Setup Guide - Quick Start

## 🚀 Quick Installation

### Step 1: Install Neo4j Python Driver

```bash
cd backend
pip install neo4j==5.20.0
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

### Step 2: Start Neo4j Container

From the project root directory:

```bash
# Start Neo4j
docker-compose up -d neo4j

# Check if it's running
docker ps | grep neo4j

# View logs
docker-compose logs -f neo4j
```

### Step 3: Access Neo4j Browser

1. Open your browser and go to: **http://localhost:7474**
2. Login with:
   - **Username**: `neo4j`
   - **Password**: `anylab_neo4j_password` (default)
3. You'll be prompted to change the password on first login

### Step 4: Verify Connection from Django

```bash
cd backend

# Start Django shell
python manage.py shell
```

In the shell:
```python
from ai_assistant.services.neo4j_service import get_neo4j_service

neo4j = get_neo4j_service()

# Test connection
if neo4j.test_connection():
    print("✅ Neo4j connection successful!")
else:
    print("❌ Neo4j connection failed")

# Create constraints/indexes
neo4j.create_constraints()

# Get graph stats (should be empty initially)
stats = neo4j.get_graph_stats()
print(f"Graph stats: {stats}")
```

### Step 5: Test with a Simple Query

In Django shell:
```python
from ai_assistant.services.neo4j_service import get_neo4j_service

neo4j = get_neo4j_service()

# Create a test node
query = """
CREATE (d:Document {
    id: 'test-001',
    title: 'Test Document',
    type: 'test'
})
RETURN d
"""
result = neo4j.execute_query(query)
print(f"Created node: {result}")

# Query all documents
query = "MATCH (d:Document) RETURN d LIMIT 10"
result = neo4j.execute_query(query)
print(f"Found {len(result)} documents")
```

## 📝 Configuration

### Environment Variables

You can customize Neo4j connection in your `.env` file (or environment):

```bash
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password_here
NEO4J_DATABASE=neo4j
```

### Change Default Password

**Important**: Change the default password after first setup!

1. Access Neo4j Browser: http://localhost:7474
2. Login with default credentials
3. Set a new password
4. Update `docker-compose.yml` or `.env` file with the new password

## 🛠️ Common Commands

### Start Neo4j
```bash
docker-compose up -d neo4j
```

### Stop Neo4j
```bash
docker-compose stop neo4j
```

### Restart Neo4j
```bash
docker-compose restart neo4j
```

### View Logs
```bash
docker-compose logs -f neo4j
```

### Remove Neo4j (keeps data)
```bash
docker-compose stop neo4j
docker-compose rm neo4j
```

### Remove Neo4j and ALL Data
```bash
docker-compose down -v neo4j
```

## 🔍 Verify Installation

### Check Container Status
```bash
docker ps | grep neo4j
```

Should show:
```
anylab_neo4j   neo4j:5.15-community   Up   7474/tcp, 0.0.0.0:7474->7474/tcp, 0.0.0.0:7687->7687/tcp
```

### Check Health
```bash
docker inspect anylab_neo4j | grep Health -A 10
```

### Test Connection from Command Line
```bash
# Using cypher-shell in container
docker exec -it anylab_neo4j cypher-shell -u neo4j -p anylab_neo4j_password

# Then run:
MATCH (n) RETURN count(n) AS node_count;
```

## 📊 Access Neo4j Browser

- **URL**: http://localhost:7474
- **Default Username**: `neo4j`
- **Default Password**: `anylab_neo4j_password`

### First Time Setup

1. Open http://localhost:7474
2. Login with default credentials
3. **Important**: Change password immediately
4. You'll see a welcome screen with sample queries

### Example Queries in Browser

```cypher
// Count all nodes
MATCH (n) RETURN count(n)

// Show all node labels
CALL db.labels()

// Show all relationship types
CALL db.relationshipTypes()

// Show all documents
MATCH (d:Document) RETURN d LIMIT 10
```

## 🔐 Security Notes

### Production Setup

1. **Change Default Password** (required!)
2. **Use Environment Variables** for credentials
3. **Restrict Network Access**:
   - Remove port mappings for production
   - Use internal Docker network only
   - Access via VPN/internal network

### Update Password in Docker Compose

1. Change password in Neo4j Browser
2. Update `docker-compose.yml`:
   ```yaml
   - NEO4J_AUTH=neo4j/your_new_password
   ```
3. Update `.env` file:
   ```bash
   NEO4J_PASSWORD=your_new_password
   ```
4. Restart container:
   ```bash
   docker-compose restart neo4j
   ```

## 🐛 Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs neo4j

# Check if port is already in use
lsof -i :7474
lsof -i :7687

# Remove and recreate
docker-compose down neo4j
docker-compose up -d neo4j
```

### Connection Refused

1. Check if container is running: `docker ps | grep neo4j`
2. Check logs: `docker-compose logs neo4j`
3. Verify URI in settings: Should be `bolt://localhost:7687`
4. Try restarting: `docker-compose restart neo4j`

### Authentication Failed

1. Verify password in `docker-compose.yml`
2. Check `.env` file if using environment variables
3. Reset password:
   ```bash
   docker exec -it anylab_neo4j neo4j-admin dbms set-initial-password new_password
   ```

### Out of Memory

Increase memory limits in `docker-compose.yml`:
```yaml
- NEO4J_dbms_memory_heap_max__size=4G
- NEO4J_dbms_memory_pagecache_size=2G
```

## 📚 Next Steps

1. ✅ Neo4j is running
2. ✅ Connection verified
3. ⏭️ Next: Build graph from existing documents
4. ⏭️ Next: Implement entity extraction
5. ⏭️ anschließend: Create hybrid search service

See `GRAPH_RAG_MIGRATION_PLAN.md` for the full implementation plan.

## 🆘 Need Help?

- **Neo4j Documentation**: https://neo4j.com/docs/
- **Cypher Query Language**: https://neo4j.com/docs/cypher-manual/
- **Python Driver**: https://neo4j.com/docs/python-manual/current/
- **Neo4j Browser Guide**: https://neo4j.com/docs/browser-manual/

---

**You're all set!** 🎉 Neo4j is now running and ready for Graph RAG implementation.

