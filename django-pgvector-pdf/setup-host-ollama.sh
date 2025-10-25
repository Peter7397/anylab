#!/bin/bash

echo "🏠 Setting up RAG with Host Ollama"
echo "=================================="

# Check if Ollama is installed on host
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed on your host system."
    echo "Please install Ollama first:"
    echo "  curl -fsSL https://ollama.ai/install.sh | sh"
    exit 1
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo "🚀 Starting Ollama on host..."
    ollama serve &
    sleep 5
fi

# Check if qwen2:latest is available
if ! ollama list | grep -q "qwen2:latest"; then
    echo "📥 Downloading qwen2:latest model..."
    ollama pull qwen2:latest
fi

echo "✅ Host Ollama is ready!"

# Update docker-compose to use host Ollama
echo "🔧 Updating Docker configuration..."
cp docker-compose-host-ollama.yml docker-compose.yml

# Update environment variable
sed -i.bak 's/OLLAMA_API_BASE_URL=http:\/\/ollama:11434/OLLAMA_API_BASE_URL=http:\/\/host.docker.internal:11434/' .env

echo "🚀 Starting Docker services..."
docker compose down
docker compose up -d

echo ""
echo "✅ Setup complete!"
echo "📊 Check status: docker compose ps"
echo "🔍 Monitor resources: docker stats --no-stream"
echo "🌐 Access web interface: http://localhost:8000"
echo ""
echo "💡 To test RAG functionality:"
echo "1. Upload some PDF documents"
echo "2. Go to RAG Query section"
echo "3. Ask questions about your documents" 