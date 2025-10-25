#!/bin/bash

echo "🍎 Setting up RAG for ARM64 Mac (Apple Silicon)"
echo "================================================"

# Check if we're on ARM64
if [ "$(uname -m)" != "arm64" ]; then
    echo "❌ This script is designed for ARM64 Mac (Apple Silicon)"
    echo "Current architecture: $(uname -m)"
    exit 1
fi

echo "✅ Detected ARM64 architecture"

# Update docker-compose to use ARM64 configuration
echo "🔧 Updating Docker configuration for ARM64..."
cp docker-compose-arm64.yml docker-compose.yml

# Update environment variable
sed -i.bak 's/OLLAMA_API_BASE_URL=http:\/\/host.docker.internal:11434/OLLAMA_API_BASE_URL=http:\/\/ollama:11434/' .env

echo "🚀 Starting Docker services with ARM64 platform..."
docker compose down

# Remove old volumes to ensure clean start
docker volume rm django-pgvector-pdf_ollama_data 2>/dev/null || true

# Create new volume
docker volume create ollama_data

# Start services
docker compose up -d

echo "⏳ Waiting for services to start..."
sleep 15

echo "📊 Checking service status..."
docker compose ps

echo "🔍 Checking platform compatibility..."
docker compose exec ollama uname -m 2>/dev/null || echo "Ollama container not ready yet"

echo ""
echo "✅ ARM64 setup complete!"
echo "📊 Check status: docker compose ps"
echo "🔍 Monitor resources: docker stats --no-stream"
echo "🌐 Access web interface: http://localhost:8000"
echo ""
echo "💡 Benefits of ARM64 setup:"
echo "   - Native performance on Apple Silicon"
echo "   - Better resource utilization"
echo "   - Faster model inference"
echo "   - Lower memory overhead"
echo ""
echo "💡 To test RAG functionality:"
echo "1. Upload some PDF documents"
echo "2. Go to RAG Query section"
echo "3. Ask questions about your documents"
echo ""
echo "🔧 If you encounter issues:"
echo "   - Check logs: docker compose logs ollama"
echo "   - Monitor resources: docker stats --no-stream"
echo "   - Restart if needed: docker compose restart ollama" 