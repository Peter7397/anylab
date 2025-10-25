#!/bin/bash
set -eo pipefail

# Configuration
MAX_TRIES=100
WAIT_SECONDS=1

# Function to check if PostgreSQL is ready
check_db() {
    pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER"
}

# Function to check if Ollama is ready
check_ollama() {
    curl -s -f "http://ollama:11434/health" > /dev/null
}

# Function to check if Qwen model is available
check_qwen_model() {
    curl -s -f "http://ollama:11434/api/tags" | grep -q "qwen"
}

echo "Waiting for database..."
for i in $(seq 1 $MAX_TRIES); do
    if check_db; then
        echo "Database is ready!"
        break
    fi
    
    if [ $i -eq $MAX_TRIES ]; then
        echo "Database connection timed out"
        exit 1
    fi
    
    echo "Waiting for database... $i/$MAX_TRIES"
    sleep $WAIT_SECONDS
done

echo "Waiting for Ollama service..."
for i in $(seq 1 $MAX_TRIES); do
    if check_ollama; then
        echo "Ollama service is ready!"
        break
    fi
    
    if [ $i -eq $MAX_TRIES ]; then
        echo "Ollama service connection timed out"
        exit 1
    fi
    
    echo "Waiting for Ollama... $i/$MAX_TRIES"
    sleep $WAIT_SECONDS
done

# Check and pull Qwen model if not available
if ! check_qwen_model; then
    echo "Pulling Qwen model..."
    curl -X POST http://ollama:11434/api/pull -d '{"name": "qwen:7b"}' || {
        echo "Failed to pull Qwen model"
        exit 1
    }
fi

# Apply database migrations
echo "Applying database migrations..."
if ! python manage.py migrate; then
    echo "Failed to apply database migrations"
    exit 1
fi

# Collect static files
echo "Collecting static files..."
if ! python manage.py collectstatic --noinput; then
    echo "Failed to collect static files"
    exit 1
fi

# Create media directory if it doesn't exist
mkdir -p /code/media

# Start server
echo "Starting server..."
exec "$@"