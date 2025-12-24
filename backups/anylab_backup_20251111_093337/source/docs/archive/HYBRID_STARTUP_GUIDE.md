# OnLab Hybrid Development Startup Guide

## 🎉 Your Yesterday's UI is Restored!

The UI has been successfully restored to the previous version that you liked. Here's how to use it:

## 🚀 Quick Start

### Option 1: Use the Startup Script (Recommended)
```bash
./start-hybrid.sh
```

### Option 2: Manual Start
```bash
# Terminal 1: Start Backend
cd backend
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000

# Terminal 2: Start Frontend
cd frontend
npm start
```

## 🛑 Stop Services
```bash
./stop-hybrid.sh
```

## 🌐 Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Login Page**: http://localhost:8000/login/
- **Health Check**: http://localhost:8000/api/health/

## 🔐 Demo Credentials
- **Username**: `admin`
- **Password**: `admin123!@#`

## 📋 What Was Restored

### ✅ Layout Structure
- **Previous (Yesterday)**: Simple Layout with `children` prop
- **Current**: ✅ Restored to the previous structure

### ✅ Navigation
- Clean sidebar navigation
- Breadcrumb navigation
- Top bar with AI mode switching

### ✅ Components
- Dashboard
- AI Assistant (Knowledge Library & Chat)
- Administration (Users & Roles)
- Troubleshooting & Monitoring
- Maintenance
- Toolkit
- Settings

## 🔧 Technical Details

### Backend (Local Development)
- Django server running locally
- PostgreSQL in Docker (port 5433)
- Redis in Docker (port 6379)
- Authentication middleware working

### Frontend (Local Development)
- React development server
- TypeScript support
- Tailwind CSS styling
- React Router navigation

## 🐳 Docker Services
- **PostgreSQL**: `onlab_postgres` (port 5433)
- **Redis**: `onlab_redis` (port 6379)

## 🔍 Troubleshooting

### Port Already in Use
If you get "port already in use" errors:
```bash
# Stop existing services
./stop-hybrid.sh

# Or manually kill processes
pkill -f "python manage.py runserver"
pkill -f "react-scripts"
```

### Database Issues
```bash
# Restart PostgreSQL
docker restart onlab_postgres

# Run migrations
cd backend
source venv/bin/activate
python manage.py migrate
```

### Frontend Issues
```bash
# Clear node modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## 📝 Notes

- The UI is now using the simpler Layout structure from yesterday
- Authentication is working with the backend login page
- All routes are properly configured
- The startup script handles all the setup automatically

## 🎯 Next Steps

1. **Test the UI**: Open http://localhost:3000 to see your restored interface
2. **Test Authentication**: Try logging in at http://localhost:8000/login/
3. **Explore Features**: Navigate through the different sections
4. **Customize**: Make any additional changes you want to the UI

Your yesterday's beautiful UI is back! 🎉
