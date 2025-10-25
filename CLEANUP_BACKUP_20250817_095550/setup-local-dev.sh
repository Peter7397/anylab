#!/bin/bash

# OneLab Local Development Setup Script
# This script sets up the backend for local development (easier than Docker)

echo "🚀 Setting up OneLab Local Development Environment..."
echo "=================================================="

# Check if Python 3.11+ is installed
python_version=$(python3 --version 2>&1 | grep -o '\d\+\.\d\+' | head -1)
if [ -z "$python_version" ]; then
    echo "❌ Python 3.11+ is required but not found"
    echo "💡 Please install Python 3.11+ and try again"
    exit 1
fi

echo "✅ Python $python_version found"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# Django Settings
DEBUG=True
SECRET_KEY=dev-secret-key-change-this-in-production
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Settings (for local PostgreSQL)
DB_NAME=onelab
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432

# Redis Settings (for local Redis)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# CORS Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# AI Settings
EMBEDDING_MODE=lightweight
OLLAMA_API_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:latest
EMBEDDING_MODEL=bge-m3

# Media and Static
MEDIA_ROOT=media
STATIC_ROOT=staticfiles
EOF
    echo "✅ .env file created"
else
    echo "✅ .env file already exists"
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p media logs staticfiles

# Check if PostgreSQL is running (Docker or local)
echo "🔍 Checking PostgreSQL connection..."
if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "✅ PostgreSQL is running"
else
    echo "⚠️  PostgreSQL is not running"
    echo "💡 You can start it with: docker run -d --name onelab_postgres -e POSTGRES_DB=onelab -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=password -p 5432:5432 pgvector/pgvector:pg16"
fi

# Check if Redis is running
echo "🔍 Checking Redis connection..."
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is running"
else
    echo "⚠️  Redis is not running"
    echo "💡 You can start it with: docker run -d --name onelab_redis -p 6379:6379 redis:7-alpine"
fi

echo ""
echo "🎉 Local Development Setup Complete!"
echo ""
echo "📝 Next Steps:"
echo "1. Start PostgreSQL: docker run -d --name onelab_postgres -e POSTGRES_DB=onelab -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=password -p 5432:5432 pgvector/pgvector:pg16"
echo "2. Start Redis: docker run -d --name onelab_redis -p 6379:6379 redis:7-alpine"
echo "3. Run migrations: python manage.py migrate"
echo "4. Create superuser: python manage.py createsuperuser"
echo "5. Start Django: python manage.py runserver"
echo "6. Start Celery: celery -A onelab worker --loglevel=info"
echo "7. Start Celery Beat: celery -A onelab beat --loglevel=info"
echo ""
echo "💡 For Windows, use: setup-local-dev.bat"
