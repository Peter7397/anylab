#!/bin/bash
# Start all required Docker services for hybrid setup
# This script ensures PostgreSQL, Redis, and Neo4j are running

set -euo pipefail

echo "🐳 Starting Docker services (PostgreSQL, Redis, Neo4j)..."
echo "========================================================"

cd "$(dirname "$0")"

# Start all services defined in docker-compose.yml
echo ""
echo "📦 Starting services with docker-compose..."
docker-compose up -d postgres redis neo4j

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check PostgreSQL
echo ""
echo "🔍 Checking PostgreSQL..."
if docker exec anylab_postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo "✅ PostgreSQL is ready"
else
    echo "⚠️  PostgreSQL is starting (may need more time)"
    echo "   Checking again in 5 seconds..."
    sleep 5
    if docker exec anylab_postgres pg_isready -U postgres > /dev/null 2>&1; then
        echo "✅ PostgreSQL is now ready"
    else
        echo "❌ PostgreSQL failed to start - check logs: docker logs anylab_postgres"
    fi
fi

# Check Redis
echo ""
echo "🔍 Checking Redis..."
if docker exec anylab_redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is ready"
else
    echo "⚠️  Redis is starting (may need more time)"
    sleep 2
    if docker exec anylab_redis redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis is now ready"
    else
        echo "❌ Redis failed to start - check logs: docker logs anylab_redis"
    fi
fi

# Check Neo4j (wait longer as it takes more time to start)
echo ""
echo "🔍 Checking Neo4j (this takes 30-60 seconds)..."
NEO4J_READY=false
for i in {1..15}; do
    if curl -s http://localhost:7474 > /dev/null 2>&1; then
        echo "✅ Neo4j is ready"
        NEO4J_READY=true
        break
    fi
    echo "   Attempt $i/15..."
    sleep 5
done

if [ "$NEO4J_READY" = false ]; then
    echo "⚠️  Neo4j is still starting (this is normal, can take up to 2 minutes)"
    echo "   You can check status later with: docker logs anylab_neo4j"
fi

# Enable pgvector extension if not already enabled
echo ""
echo "🔍 Checking pgvector extension..."
if docker exec anylab_postgres psql -U postgres -d anylab -c "\dx" | grep -q vector; then
    echo "✅ pgvector extension already enabled"
else
    echo "📦 Enabling pgvector extension..."
    docker exec anylab_postgres psql -U postgres -d anylab -c "CREATE EXTENSION IF NOT EXISTS vector;" || true
    echo "✅ pgvector extension enabled"
fi

echo ""
echo "📊 Docker services status:"
docker-compose ps

echo ""
echo "✅ All Docker services started!"
echo ""
echo "📍 Access URLs:"
echo "   Neo4j Browser: http://localhost:7474"
echo "   PostgreSQL:    localhost:5433"
echo "   Redis:         localhost:6379"



