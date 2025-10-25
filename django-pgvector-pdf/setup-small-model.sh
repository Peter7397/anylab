#!/bin/bash

echo "🐳 Setting up RAG with Small Qwen Model in Docker"
echo "=================================================="

# Update docker-compose to use small model
echo "🔧 Updating Docker configuration..."
cp docker-compose-small-model.yml docker-compose.yml

# Update environment variable
sed -i.bak 's/OLLAMA_API_BASE_URL=http:\/\/host.docker.internal:11434/OLLAMA_API_BASE_URL=http:\/\/ollama:11434/' .env

echo "🚀 Starting Docker services with resource limits..."
docker compose down
docker compose up -d

echo "⏳ Waiting for services to start..."
sleep 10

echo "📊 Checking service status..."
docker compose ps

echo ""
echo "✅ Setup complete!"
echo "📊 Check status: docker compose ps"
echo "🔍 Monitor resources: docker stats --no-stream"
echo "🌐 Access web interface: http://localhost:8000"
echo ""
echo "💡 This setup uses qwen2.5:0.5b (0.5B parameters) instead of qwen2:latest (7.6B)"
echo "   Much lower memory usage while still providing good RAG functionality"
echo ""
echo "💡 To test RAG functionality:"
echo "1. Upload some PDF documents"
echo "2. Go to RAG Query section"
echo "3. Ask questions about your documents" 