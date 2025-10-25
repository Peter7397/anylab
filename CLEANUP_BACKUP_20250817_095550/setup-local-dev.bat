@echo off
REM OneLab Local Development Setup Script for Windows
REM This script sets up the backend for local development (easier than Docker)

echo 🚀 Setting up OneLab Local Development Environment...
echo ==================================================

REM Check if Python 3.11+ is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 3.11+ is required but not found
    echo 💡 Please install Python 3.11+ and try again
    pause
    exit /b 1
)

echo ✅ Python found

REM Create virtual environment
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
) else (
    echo ✅ Virtual environment already exists
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo ⬆️  Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo 📦 Installing Python dependencies...
pip install -r requirements.txt

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo 📝 Creating .env file...
    (
        echo # Django Settings
        echo DEBUG=True
        echo SECRET_KEY=dev-secret-key-change-this-in-production
        echo ALLOWED_HOSTS=localhost,127.0.0.1
        echo.
        echo # Database Settings ^(for local PostgreSQL^)
        echo DB_NAME=onelab
        echo DB_USER=postgres
        echo DB_PASSWORD=password
        echo DB_HOST=localhost
        echo DB_PORT=5432
        echo.
        echo # Redis Settings ^(for local Redis^)
        echo REDIS_URL=redis://localhost:6379/0
        echo CELERY_BROKER_URL=redis://localhost:6379/0
        echo CELERY_RESULT_BACKEND=redis://localhost:6379/0
        echo.
        echo # CORS Settings
        echo CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
        echo.
        echo # AI Settings
        echo EMBEDDING_MODE=lightweight
        echo OLLAMA_API_URL=http://localhost:11434
        echo OLLAMA_MODEL=qwen2.5:latest
        echo EMBEDDING_MODEL=bge-m3
        echo.
        echo # Media and Static
        echo MEDIA_ROOT=media
        echo STATIC_ROOT=staticfiles
    ) > .env
    echo ✅ .env file created
) else (
    echo ✅ .env file already exists
)

REM Create necessary directories
echo 📁 Creating necessary directories...
if not exist "media" mkdir media
if not exist "logs" mkdir logs
if not exist "staticfiles" mkdir staticfiles

echo.
echo 🎉 Local Development Setup Complete!
echo.
echo 📝 Next Steps:
echo 1. Start PostgreSQL: docker run -d --name onelab_postgres -e POSTGRES_DB=onelab -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=password -p 5432:5432 pgvector/pgvector:pg16
echo 2. Start Redis: docker run -d --name onelab_redis -p 6379:6379 redis:7-alpine
echo 3. Run migrations: python manage.py migrate
echo 4. Create superuser: python manage.py createsuperuser
echo 5. Start Django: python manage.py runserver
echo 6. Start Celery: celery -A onelab worker --loglevel=info
echo 7. Start Celery Beat: celery -A onelab beat --loglevel=info
echo.
pause
