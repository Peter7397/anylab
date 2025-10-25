@echo off
chcp 65001 >nul
echo 🚀 Starting OneLab Backend with Docker...

REM Check if .env file exists
if not exist .env (
    echo 📝 Creating .env file from template...
    copy env.docker .env
    echo ⚠️  Please edit .env file with your configuration before continuing
    echo    Key variables to update:
    echo    - SECRET_KEY
    echo    - DB_PASSWORD
    echo    - JWT_SECRET_KEY
    pause
)

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker and try again.
    pause
    exit /b 1
)

REM Check if docker-compose is available
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ docker-compose is not installed. Please install it and try again.
    pause
    exit /b 1
)

REM Build and start services
echo 🔨 Building and starting services...
docker-compose up --build -d

REM Wait for services to be ready
echo ⏳ Waiting for services to be ready...
timeout /t 10 /nobreak >nul

REM Check if web service is healthy
echo 🏥 Checking service health...
docker-compose exec -T web python manage.py check >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Services may still be starting up...
) else (
    echo ✅ Services are healthy!
)

echo.
echo 🎉 OneLab Backend is starting up!
echo.
echo 📊 Service URLs:
echo    - API: http://localhost:8000
echo    - Admin: http://localhost:8000/admin
echo    - Health Check: http://localhost:8000/api/health/
echo    - Celery Flower: http://localhost:5555
echo.
echo 📝 Useful commands:
echo    - View logs: docker-compose logs -f
echo    - Stop services: docker-compose down
echo    - Restart services: docker-compose restart
echo    - Create superuser: docker-compose exec web python manage.py createsuperuser
echo.
echo 🔍 Monitoring:
echo    - View all logs: docker-compose logs
echo    - View specific service: docker-compose logs web
echo    - Access container: docker-compose exec web bash
echo.

REM Keep script running to maintain containers
echo 🔄 Services are running. Press Ctrl+C to stop...
docker-compose logs -f 