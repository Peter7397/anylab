# 🚀 OneLab Backend - Quick Start & Testing Guide

## 📋 Prerequisites

Before starting, ensure you have:
- ✅ Docker Desktop installed and running
- ✅ Docker Compose available
- ✅ At least 4GB RAM available
- ✅ Ports 8000, 5432, 6379, 5555 available

## 🎯 Quick Start (3 Steps)

### Step 1: Setup Environment
```bash
# Navigate to backend directory
cd OneLab0803/backend

# Create environment file from template
cp env.docker .env

# Edit .env file with your settings (see configuration section below)
```

### Step 2: Start Services
```bash
# Build and start all services
docker-compose up --build -d

# Or use the startup script (Windows)
start.bat

# Or use the startup script (Linux/macOS)
chmod +x start.sh
./start.sh
```

### Step 3: Verify Installation
```bash
# Check if all services are running
docker-compose ps

# Check service health
curl http://localhost:8000/api/health/
```

## ⚙️ Configuration

### Essential Environment Variables (.env file)
```bash
# Django Settings
DEBUG=True  # Set to False for production
SECRET_KEY=your-super-secret-key-change-this-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database Settings
DB_NAME=onelab_db
DB_USER=postgres
DB_PASSWORD=your-secure-password
DB_HOST=db
DB_PORT=5432

# Redis Settings
REDIS_URL=redis://redis:6379/0

# Celery Settings
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# CORS Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# JWT Settings
JWT_SECRET_KEY=your-jwt-secret-key-change-this
JWT_ACCESS_TOKEN_LIFETIME=5
JWT_REFRESH_TOKEN_LIFETIME=1
```

## 🧪 Testing the Backend

### 1. Health Check Test
```bash
# Test the health endpoint
curl http://localhost:8000/api/health/

# Expected response:
# {"status": "healthy", "service": "onelab-backend"}
```

### 2. Database Connection Test
```bash
# Check if database is accessible
docker-compose exec web python manage.py check

# Expected output: "System check identified no issues"
```

### 3. Admin Interface Test
```bash
# Create a superuser
docker-compose exec web python manage.py createsuperuser

# Then visit: http://localhost:8000/admin
```

### 4. API Endpoints Test
```bash
# Test JWT authentication
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'

# Test user endpoints
curl http://localhost:8000/api/users/

# Test monitoring endpoints
curl http://localhost:8000/api/monitoring/

# Test maintenance endpoints
curl http://localhost:8000/api/maintenance/

# Test AI assistant endpoints
curl http://localhost:8000/api/ai/
```

### 5. Celery Monitoring Test
```bash
# Visit Celery Flower monitoring interface
# URL: http://localhost:5555

# Check Celery worker status
docker-compose exec web celery -A onelab inspect active
```

### 6. Background Tasks Test
```bash
# Test system health check task
docker-compose exec web python manage.py shell
```
```python
# In Django shell:
from monitoring.tasks import system_health_check
result = system_health_check.delay()
print(result.get())
```

## 🔍 Monitoring & Debugging

### View Logs
```bash
# All services logs
docker-compose logs

# Specific service logs
docker-compose logs web
docker-compose logs celery
docker-compose logs db
docker-compose logs redis

# Follow logs in real-time
docker-compose logs -f web
```

### Service Status
```bash
# Check all services
docker-compose ps

# Check service health
docker-compose exec web python manage.py check

# Check database connection
docker-compose exec db psql -U postgres -d onelab_db -c "SELECT version();"
```

### Debug Commands
```bash
# Access Django shell
docker-compose exec web python manage.py shell

# Access container shell
docker-compose exec web bash

# Check Django settings
docker-compose exec web python manage.py check --deploy
```

## 🐛 Troubleshooting

### Common Issues & Solutions

#### 1. Port Already in Use
```bash
# Check what's using the ports
netstat -tulpn | grep :8000
netstat -tulpn | grep :5432

# Stop conflicting services or change ports in docker-compose.yml
```

#### 2. Database Connection Issues
```bash
# Check if database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Reset database (WARNING: This will delete all data)
docker-compose down -v
docker-compose up -d
```

#### 3. Memory Issues
```bash
# Check Docker memory usage
docker stats

# Increase Docker memory limit in Docker Desktop settings
```

#### 4. Build Issues
```bash
# Clean build
docker-compose down
docker system prune -f
docker-compose up --build
```

#### 5. Permission Issues
```bash
# Fix file permissions
sudo chown -R $USER:$USER OneLab0803/backend/
chmod +x start.sh
```

## 📊 Service URLs & Ports

| Service | URL | Port | Description |
|---------|-----|------|-------------|
| Django API | http://localhost:8000 | 8000 | Main API server |
| Django Admin | http://localhost:8000/admin | 8000 | Admin interface |
| Health Check | http://localhost:8000/api/health/ | 8000 | Health endpoint |
| Celery Flower | http://localhost:5555 | 5555 | Task monitoring |
| PostgreSQL | localhost | 5432 | Database |
| Redis | localhost | 6379 | Cache & message broker |

## 🧪 Automated Testing

### Run Django Tests
```bash
# Run all tests
docker-compose exec web python manage.py test

# Run specific app tests
docker-compose exec web python manage.py test users
docker-compose exec web python manage.py test monitoring
docker-compose exec web python manage.py test maintenance
docker-compose exec web python manage.py test ai_assistant
```

### API Testing with curl
```bash
# Test health endpoint
curl -X GET http://localhost:8000/api/health/

# Test authentication
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# Test with authentication token
TOKEN="your_jwt_token_here"
curl -X GET http://localhost:8000/api/users/ \
  -H "Authorization: Bearer $TOKEN"
```

## 🔄 Development Workflow

### 1. Development Mode
```bash
# Use development compose file
docker-compose -f docker-compose.dev.yml up --build
```

### 2. Code Changes
```bash
# Changes are automatically reflected in development mode
# For production, rebuild the container:
docker-compose up --build
```

### 3. Database Migrations
```bash
# Create migrations
docker-compose exec web python manage.py makemigrations

# Apply migrations
docker-compose exec web python manage.py migrate
```

### 4. Static Files
```bash
# Collect static files
docker-compose exec web python manage.py collectstatic
```

## 🛑 Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: This will delete all data)
docker-compose down -v

# Stop and remove images
docker-compose down --rmi all
```

## 📈 Performance Testing

### Load Testing
```bash
# Install Apache Bench (if available)
ab -n 1000 -c 10 http://localhost:8000/api/health/

# Or use curl for simple load testing
for i in {1..100}; do curl http://localhost:8000/api/health/; done
```

### Memory Usage
```bash
# Check container resource usage
docker stats

# Check specific service
docker stats onelab_web onelab_celery onelab_db onelab_redis
```

## ✅ Success Checklist

- [ ] All containers are running (`docker-compose ps`)
- [ ] Health check returns success (`curl http://localhost:8000/api/health/`)
- [ ] Database is accessible (`docker-compose exec web python manage.py check`)
- [ ] Admin interface is accessible (http://localhost:8000/admin)
- [ ] Celery Flower is accessible (http://localhost:5555)
- [ ] Background tasks are working (test via Django shell)
- [ ] Logs show no errors (`docker-compose logs`)

## 🆘 Getting Help

### Useful Commands
```bash
# View all logs
docker-compose logs

# Restart specific service
docker-compose restart web

# Rebuild specific service
docker-compose up --build web

# Check service status
docker-compose ps

# Access container shell
docker-compose exec web bash
```

### Documentation
- [Docker Setup Summary](DOCKER_SETUP_SUMMARY.md)
- [Docker Deployment Guide](README_Docker.md)
- [Django Documentation](https://docs.djangoproject.com/)
- [Celery Documentation](https://docs.celeryproject.org/)

---

**🎉 Congratulations!** Your OneLab backend is now running and ready for development! 