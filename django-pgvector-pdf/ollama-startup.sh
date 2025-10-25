#!/bin/bash

# Start Ollama server in the background
ollama serve &

# Wait for the server to be ready
echo "Waiting for Ollama server to start..."
sleep 15

# Check if models already exist
if ! ollama list | grep -q "qwen2.5:7b"; then
    echo "Downloading qwen2.5:7b model..."
    ollama pull qwen2.5:7b
else
    echo "qwen2.5:7b model already exists"
fi

if ! ollama list | grep -q "qwen2.5:14b"; then
    echo "Downloading qwen2.5:14b model..."
    ollama pull qwen2.5:14b
else
    echo "qwen2.5:14b model already exists"
fi

# List available models
echo "Available models:"
ollama list

# Keep the container running
wait 