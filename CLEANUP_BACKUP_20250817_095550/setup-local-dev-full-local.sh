#!/bin/bash

# OneLab Full Local Development Setup Script
# This script sets up everything locally (no Docker at all)

echo "🚀 Setting up OneLab Full Local Development Environment..."
echo "=========================================================="

# Check if Python 3.11+ is installed
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
if [ -z "$python_version" ]; then
    echo "❌ Python 3.11+ is required but not found"
    echo "💡 Please install Python 3.11+ and try again"
    exit 1
fi

echo "✅ Python $python_version found"

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="mac"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
else
    echo "❌ Unsupported OS: $OSTYPE"
    echo "💡 This script supports macOS and Linux"
    exit 1
fi

echo "🔍 Detected OS: $OS"

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

# Install PostgreSQL based on OS
echo "🗄️  Setting up PostgreSQL..."
if [ "$OS" = "mac" ]; then
    # macOS setup
    if ! command -v brew &> /dev/null; then
        echo "❌ Homebrew is required for macOS"
        echo "💡 Install Homebrew: https://brew.sh"
        exit 1
    fi
    
    # Install PostgreSQL
    if ! brew list postgresql@16 &> /dev/null; then
        echo "📦 Installing PostgreSQL 16..."
        brew install postgresql@16
    else
        echo "✅ PostgreSQL 16 already installed"
    fi
    
    # Start PostgreSQL service
    echo "🚀 Starting PostgreSQL service..."
    brew services start postgresql@16
    
    # Wait for PostgreSQL to start
    echo "⏳ Waiting for PostgreSQL to start..."
    sleep 5
    
    # Create database and user
    echo "🗄️  Creating database and user..."
    createdb onelab 2>/dev/null || echo "Database 'onelab' already exists"
    psql -d onelab -c "CREATE USER postgres WITH PASSWORD 'password';" 2>/dev/null || echo "User 'postgres' already exists"
    psql -d onelab -c "GRANT ALL PRIVILEGES ON DATABASE onelab TO postgres;" 2>/dev/null || echo "Privileges already granted"
    
    # Install pgvector (this is the complex part)
    echo "🔧 Installing pgvector extension..."
    if ! psql -d onelab -c "SELECT * FROM pg_extension WHERE extname = 'vector';" | grep -q vector; then
        echo "⚠️  pgvector extension not found"
        echo "💡 Installing pgvector manually..."
        echo "   This requires manual compilation. Please run:"
        echo "   git clone https://github.com/pgvector/pgvector.git"
        echo "   cd pgvector"
        echo "   make"
        echo "   make install"
        echo "   psql -d onelab -c 'CREATE EXTENSION vector;'"
        echo ""
        echo "   Or use Docker for easier setup:"
        echo "   docker run -d --name onelab_postgres -e POSTGRES_DB=onelab -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=password -p 5432:5432 pgvector/pgvector:pg16"
    else
        echo "✅ pgvector extension found"
    fi
    
elif [ "$OS" = "linux" ]; then
    # Linux setup
    echo "📦 Installing PostgreSQL and pgvector..."
    sudo apt-get update
    sudo apt-get install -y postgresql-16 postgresql-16-pgvector
    
    # Start PostgreSQL service
    echo "🚀 Starting PostgreSQL service..."
    sudo systemctl start postgresql
    
    # Create database and user
    echo "🗄️  Creating database and user..."
    sudo -u postgres createdb onelab 2>/dev/null || echo "Database 'onelab' already exists"
    sudo -u postgres psql -c "CREATE USER postgres WITH PASSWORD 'password';" 2>/dev/null || echo "User 'postgres' already exists"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE onelab TO postgres;" 2>/dev/null || echo "Privileges already granted"
    sudo -u postgres psql -d onelab -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null || echo "Vector extension already exists"
fi

# Install Redis based on OS
echo "🔴 Setting up Redis..."
if [ "$OS" = "mac" ]; then
    # macOS Redis setup
    if ! brew list redis &> /dev/null; then
        echo "📦 Installing Redis..."
        brew install redis
    else
        echo "✅ Redis already installed"
    fi
    
    # Start Redis service
    echo "🚀 Starting Redis service..."
    brew services start redis
    
elif [ "$OS" = "linux" ]; then
    # Linux Redis setup
    if ! command -v redis-server &> /dev/null; then
        echo "📦 Installing Redis..."
        sudo apt-get install -y redis-server
    else
        echo "✅ Redis already installed"
    fi
    
    # Start Redis service
    echo "🚀 Starting Redis service..."
    sudo systemctl start redis-server
fi

# Wait for Redis to start
echo "⏳ Waiting for Redis to start..."
sleep 3

# Test Redis connection
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is running"
else
    echo "❌ Redis connection failed"
    echo "💡 Please check Redis installation"
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# Django Settings
DEBUG=True
SECRET_KEY=dev-secret-key-change-this-in-production
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Settings (Local PostgreSQL)
DB_NAME=onelab
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432

# Redis Settings (Local Redis)
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

echo ""
echo "🎉 Full Local Development Setup Complete!"
echo ""
echo "📝 Next Steps:"
echo "1. Run migrations: python manage.py migrate"
echo "2. Create superuser: python manage.py createsuperuser"
echo "3. Start Django: python manage.py runserver"
echo "4. Start Celery: celery -A onelab worker --loglevel=info"
echo "5. Start Celery Beat: celery -A onelab beat --loglevel=info"
echo ""
echo "💡 Services Status:"
echo "   • PostgreSQL: $(brew services list | grep postgresql | awk '{print $2}' 2>/dev/null || echo 'Unknown')"
echo "   • Redis: $(brew services list | grep redis | awk '{print $2}' 2>/dev/null || echo 'Unknown')"
echo ""
echo "⚠️  Note: If pgvector installation failed, consider using Docker for easier setup"
