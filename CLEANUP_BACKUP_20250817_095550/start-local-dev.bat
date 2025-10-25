@echo off
REM OneLab Local Development Startup Script for Windows
REM This script starts the backend services for local development

echo 🚀 Starting OneLab Local Development Services...
echo ===============================================

REM Check if virtual environment exists
if not exist "venv" (
    echo ❌ Virtual environment not found
    echo 💡 Please run setup-local-dev.bat first
    pause
    exit /b 1
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if .env file exists
if not exist ".env" (
    echo ❌ .env file not found
    echo 💡 Please run setup-local-dev.bat first
    pause
    exit /b 1
)

REM Check if PostgreSQL is running
echo 🔍 Checking PostgreSQL...
docker exec onelab_postgres pg_isready -U postgres >nul 2>&1
if errorlevel 1 (
    echo ⚠️  PostgreSQL is not running
    echo 🚀 Starting PostgreSQL container...
    docker run -d --name onelab_postgres -e POSTGRES_DB=onelab -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=password -p 5432:5432 pgvector/pgvector:pg16
    
    echo ⏳ Waiting for PostgreSQL to start...
    timeout /t 10 /nobreak >nul
) else (
    echo ✅ PostgreSQL is running
)

REM Check if Redis is running
echo 🔍 Checking Redis...
docker exec onelab_redis redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Redis is not running
    echo 🚀 Starting Redis container...
    docker run -d --name onelab_redis -p 6379:6379 redis:7-alpine
    
    echo ⏳ Waiting for Redis to start...
    timeout /t 5 /nobreak >nul
) else (
    echo ✅ Redis is running
)

REM Run migrations
echo 🔄 Running database migrations...
python manage.py migrate

REM Collect static files
echo 📦 Collecting static files...
python manage.py collectstatic --noinput

echo.
echo 🎉 All services started!
echo 📍 Services:
echo    • Django: http://localhost:8000
echo    • Admin: http://localhost:8000/admin
echo    • API: http://localhost:8000/api/
echo    • PostgreSQL: localhost:5432
echo    • Redis: localhost:6379
echo.
echo 💡 To start Celery worker, open a new terminal and run:
echo    celery -A onelab worker --loglevel=info
echo.
echo 💡 To start Celery beat, open another terminal and run:
echo    celery -A onelab beat --loglevel=info
echo.

REM Start Django development server
echo 🚀 Starting Django development server...
python manage.py runserver 0.0.0.0:8000
