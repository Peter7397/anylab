#!/bin/bash

# Graph Building Helper Script
# Builds Neo4j knowledge graph from existing documents

echo "🚀 Building Neo4j Knowledge Graph from Documents"
echo "=================================================="
echo ""

# Check if Neo4j is running
if ! docker ps | grep -q anylab_neo4j; then
    echo "❌ Error: Neo4j is not running!"
    echo "   Please start Neo4j first: docker compose up -d neo4j"
    exit 1
fi

echo "✅ Neo4j is running"
echo ""

# Navigate to backend
cd backend

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found at backend/venv"
    echo "   Creating virtual environment..."
    python3 -m venv venv
    echo "   Installing dependencies..."
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo "✅ Virtual environment found"
    source venv/bin/activate
fi

echo ""
echo "📊 Checking available documents..."
echo ""

# Check documents
python manage.py shell -c "
from ai_assistant.models import UploadedFile
ready = UploadedFile.objects.filter(processing_status='ready', chunks_created=True)
total = UploadedFile.objects.count()
print(f'Total documents: {total}')
print(f'Ready documents: {ready.count()}')
if ready.count() > 0:
    print('\\nFirst 5 ready documents:')
    for f in ready[:5]:
        print(f'  ID: {f.id}, File: {f.filename[:60]}')
"

echo ""
echo "🔨 Building graph..."
echo ""

# Build graph
python manage.py build_graph

echo ""
echo "✅ Graph building complete!"
echo ""
echo "📊 View your graph at: http://localhost:7474"
echo "   Username: neo4j"
echo "   Password: anylab_neo4j_password"
echo ""
echo "💡 Try these queries in Neo4j Browser:"
echo "   MATCH (d:Document) RETURN d LIMIT 10"
echo "   MATCH (e:Entity) RETURN e LIMIT 10"
echo "   MATCH (d:Document)-[:CONTAINS]->(e:Entity) RETURN d, e LIMIT 20"

