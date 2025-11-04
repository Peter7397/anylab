#!/bin/bash

# Manual Neo4j Installation Script
# This script provides multiple ways to install Neo4j

echo "🚀 Neo4j Installation Helper"
echo "=============================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker first."
    exit 1
fi

echo "Attempting to pull Neo4j image..."
echo ""

# Method 1: Try standard pull
echo "📦 Method 1: Standard pull..."
if docker pull neo4j:5.15-community 2>&1 | grep -q "Downloaded\|already exists"; then
    echo "✅ Image pulled successfully!"
    METHOD="standard"
else
    echo "⚠️  Standard pull failed, trying alternatives..."
    
    # Method 2: Try with platform specification
    echo "📦 Method 2: Platform-specific pull (linux/amd64)..."
    if docker pull --platform linux/amd64 neo4j:5.15-community 2>&1 | grep -q "Downloaded\|already exists"; then
        echo "✅ Image pulled successfully!"
        METHOD="platform"
    else
        echo "⚠️  Platform-specific pull failed..."
        
        # Method 3: Try different version
        echo "📦 Method 3: Trying Neo4j 5.14..."
        if docker pull neo4j:5.14-community 2>&1 | grep -q "Downloaded\|already exists"; then
            echo "✅ Image pulled successfully! (Using version 5.14)"
            METHOD="version"
            # Update docker-compose.yml to use 5.14
            sed -i.bak 's/neo4j:5.15-community/neo4j:5.14-community/' docker-compose.yml
        else
            echo "❌ All pull methods failed."
            echo ""
            echo "💡 Troubleshooting:"
            echo "   1. Check your internet connection"
            echo "   2. Check if you're behind a firewall/proxy"
            echo "   3. Try: docker pull neo4j:5.14-community"
            echo "   4. See NEO4J_MANUAL_INSTALL.md for more options"
            exit 1
        fi
    fi
fi

echo ""
echo "🔧 Starting Neo4j container..."

if docker compose up -d neo4j 2>&1 | grep -q "Started\|Created\|up-to-date"; then
    echo "✅ Neo4j container started!"
    echo ""
    echo "⏳ Waiting for Neo4j to be ready (30 seconds)..."
    sleep 30
    
    if docker ps | grep -q anylab_neo4j; then
        echo "✅ Neo4j is running!"
        echo ""
        echo "📊 Access Neo4j Browser:"
        echo "   URL: http://localhost:7474"
        echo "   Username: neo4j"
        echo "   Password: anylab_neo4j_password"
        echo ""
        echo "🔌 Connection Details:"
        echo "   Bolt URI: bolt://localhost:7687"
        echo ""
        echo "📝 Next: Change password in Neo4j Browser"
    else
        echo "⚠️  Container started but may still be initializing..."
        echo "Check logs: docker compose logs neo4j"
    fi
else
    echo "❌ Failed to start container"
    echo "Check logs: docker compose logs neo4j"
    exit 1
fi

