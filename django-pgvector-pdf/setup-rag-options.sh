#!/bin/bash

echo "🚀 RAG Setup Options for Resource-Constrained Systems"
echo "====================================================="
echo ""

# Check system resources
echo "📊 System Resource Check:"
echo "------------------------"

# Check total memory
if command -v sysctl &> /dev/null; then
    TOTAL_MEM=$(sysctl -n hw.memsize | awk '{print $0/1024/1024/1024}')
    echo "Total Memory: ${TOTAL_MEM}GB"
else
    echo "Total Memory: Unable to determine"
fi

# Check available memory
if command -v vm_stat &> /dev/null; then
    AVAILABLE_MEM=$(vm_stat | grep "Pages free" | awk '{print $3}' | sed 's/\.//')
    AVAILABLE_MEM_GB=$(echo "scale=2; $AVAILABLE_MEM * 4096 / 1024 / 1024 / 1024" | bc -l 2>/dev/null || echo "Unknown")
    echo "Available Memory: ${AVAILABLE_MEM_GB}GB"
else
    echo "Available Memory: Unable to determine"
fi

echo ""
echo "🎯 Recommended Options:"
echo "======================"
echo ""

echo "1. 🏠 HOST OLLAMA (Recommended for 8GB RAM)"
echo "   - Run Ollama on your host system"
echo "   - Use qwen2:latest (7.6B model)"
echo "   - Django in Docker connects to host Ollama"
echo "   - Command: ./setup-host-ollama.sh"
echo ""

echo "2. 🐳 DOCKER WITH SMALL MODEL (Recommended for 16GB RAM)"
echo "   - Everything in Docker"
echo "   - Use qwen2.5:0.5b (0.5B model - much smaller)"
echo "   - Resource limits applied"
echo "   - Command: ./setup-small-model.sh"
echo ""

echo "3. 🐳 DOCKER WITH OPTIMIZED SETTINGS (For 16GB+ RAM)"
echo "   - Everything in Docker with resource limits"
echo "   - Use qwen2:latest with memory limits"
echo "   - Command: ./setup-optimized.sh"
echo ""

echo "4. 🔧 MANUAL SETUP"
echo "   - Choose your own configuration"
echo "   - Customize resource limits"
echo ""

echo "📋 Current Status:"
echo "================="
docker compose ps 2>/dev/null | grep -E "(ollama|web|db)" || echo "No containers running"

echo ""
echo "💡 Quick Start Commands:"
echo "======================="
echo ""

echo "# Option 1: Host Ollama (if you have Ollama installed locally)"
echo "cp docker-compose-host-ollama.yml docker-compose.yml"
echo "docker compose up -d"
echo ""

echo "# Option 2: Small Model in Docker"
echo "cp docker-compose-small-model.yml docker-compose.yml"
echo "docker compose up -d"
echo ""

echo "# Option 3: Optimized Settings"
echo "cp docker-compose-optimized.yml docker-compose.yml"
echo "docker compose up -d"
echo ""

echo "🔍 Resource Monitoring:"
echo "======================"
echo "docker stats --no-stream"
echo "docker compose logs ollama"
echo "" 