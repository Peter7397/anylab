# 🚀 OnLab Quick Start Guide

## Prerequisites
- Docker Desktop running
- Node.js 18+ installed
- Git (for cloning)

## 🎯 One-Command Startup (Recommended)

From the project root directory:
```bash
./start-hybrid.sh
```

This script will:
1. ✅ Check Docker is running
2. ✅ Verify backend image exists (build if needed)
3. ✅ Start backend services (PostgreSQL, Redis, Django, Celery)
4. ✅ Wait for backend to be ready
5. ✅ Install frontend dependencies if needed
6. ✅ Start React development server

## 🔧 Manual Startup (Alternative)

### Backend Only
```bash
cd backend
docker compose up -d
```

### Frontend Only
```bash
cd frontend
./start-frontend.sh
```

## 📍 Access Points

Once started, access the system at:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **Celery Monitor**: http://localhost:5555
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## 🛠️ Useful Commands

### View Logs
```bash
# Backend logs
cd backend && docker compose logs -f django

# Frontend logs (in another terminal)
cd frontend && npm start
```

### Stop System
```bash
# Stop backend
cd backend && docker compose down

# Stop frontend
# Press Ctrl+C in the frontend terminal
```

### Restart System
```bash
# Restart backend
cd backend && docker compose restart

# Restart frontend
# Press Ctrl+C and run npm start again
```

## 🔍 Troubleshooting

### Backend Issues
1. **Docker not running**: Start Docker Desktop
2. **Port conflicts**: Check if ports 8000, 5432, 6379 are free
3. **Image missing**: Run `cd backend && ./build-images.sh`
4. **Database issues**: Run `cd backend && docker compose down -v && ./start-system.sh`

### Frontend Issues
1. **Node modules missing**: Run `cd frontend && npm install`
2. **Port 3000 busy**: Frontend will automatically use another port
3. **API connection**: Ensure backend is running at http://localhost:8000

### Performance Issues
1. **Slow startup**: First run builds Docker images (one-time)
2. **Memory issues**: Check Docker Desktop resource limits
3. **Large files**: Use the optimized viewers we implemented

## 📋 Configuration Files Status

✅ **All configuration files are properly set up:**

- **Backend**: `docker-compose.yml`, `requirements.txt`, `start-system.sh`
- **Frontend**: `package.json`, `start-frontend.sh`, API configuration
- **Environment**: `env.docker` for Docker environment variables
- **Dependencies**: All required packages installed

## 🎉 What's Ready

✅ **Enhanced Knowledge Library Viewer** with:
- PDF, Word, Excel, PowerPoint, Text file support
- Fixed PDF highlight positioning during zoom
- Search functionality for all file types
- Download capabilities
- Performance optimizations for large files
- Sticky header and navigation
- Virtual scrolling for large datasets

✅ **Complete Backend System** with:
- Django REST API
- PostgreSQL with pgvector
- Redis for caching
- Celery for background tasks
- AI/ML capabilities
- Document processing

✅ **Modern Frontend** with:
- React with TypeScript
- Tailwind CSS styling
- Responsive design
- Authentication system
- Real-time updates

## 🚀 Next Time You Start

Simply run:
```bash
./start-onlab.sh
```

And enjoy your enhanced OnLab system! 🎉
