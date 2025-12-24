#!/bin/bash

# Neo4j Quick Start Script for AnyLab0812

echo "🚀 Starting Neo4j for Graph RAG..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found in current directory"
    exit 1
fi

# Start Neo4j
echo "📦 Starting Neo4j container..."
docker-compose up -d neo4j

# Wait for Neo4j to be ready
echo "⏳ Waiting for Neo4j to start (this may take 30-60 seconds)..."
sleep 10

# Check if Neo4j is running
if docker ps | grep -q anylab_neo4j; then
    echo "✅ Neo4j container is running!"
    echo ""
    echo "📊 Access Neo4j Browser:"
    echo "   URL: http://localhost:7474"
    echo "   Username: neo4j"
    echo "   Password: anylab_neo4j_password"
    echo ""
    echo "🔌 Connection Details:"
    echo "   Bolt URI: bolt://localhost:7687"
    echo "   HTTP URI: http://localhost:7474"
    echo ""
    echo "📝 Next Steps:"
    echo "   1. Open http://localhost:7474 in your browser"
    echo "   2. Login and change the password"
    echo "   3. Update docker-compose.yml with new password"
    echo "   4. Test connection from Django:"
    echo "      python manage.py shell"
    echo "      >>> from ai_assistant.services.neo4j_service import get_neo4j_service"
    echo "      >>> neo4j = get_neo4j_service()"
    echo "      >>> neo4j.test_connection()"
    echo ""
    echo "📚 View logs: docker-compose logs -f neo4j"
    echo "🛑 Stop Neo4j: docker-compose stop neo4j"
else
    echo "❌ Error: Neo4j container failed to start"
    echo "Check logs with: docker-compose logs neo4j"
    exit 1
fi

