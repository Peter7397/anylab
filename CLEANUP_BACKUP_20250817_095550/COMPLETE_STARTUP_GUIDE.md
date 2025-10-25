# 🚀 OneLab Complete Startup Guide

## 🎯 Quick Start (Next Time)

### 1. Start Backend (Terminal 1)
```bash
cd /Users/pinggenchen/Desktop/OneLab0803/backend
./start-system.sh
```
**Result**: Backend ready at http://localhost:8000 (22 seconds)

### 2. Start Frontend (Terminal 2)  
```bash
cd /Users/pinggenchen/Desktop/OneLab0803/frontend
npm start
```
**Result**: Frontend ready at http://localhost:3000 (30 seconds)

### 3. Access Your Application
- **Main App**: http://localhost:3000
- **Backend Admin**: http://localhost:8000/admin
- **API**: http://localhost:8000/api/

## 📂 Directory Structure Reference

```
OneLab0803/
├── backend/           ← Django + PostgreSQL + AI
│   ├── start-system.sh   ← Start backend here
│   ├── stop-system.sh    ← Stop backend here  
│   └── ...
├── frontend/          ← React + TypeScript
│   ├── package.json      ← npm start here
│   └── ...
└── this_file.md
```

## ⚠️ Common Mistakes & Solutions

### ❌ Wrong Directory Error
```bash
# ERROR: Running npm start from wrong place
cd /Users/pinggenchen/Desktop/OneLab0803  # ← Wrong!
npm start  # ← Will fail: "package.json not found"
```

### ✅ Correct Way
```bash
# CORRECT: Always go to frontend directory first
cd /Users/pinggenchen/Desktop/OneLab0803/frontend  # ← Right!
npm start  # ← Will work!
```

## 🛑 How to Stop Everything

### Stop Frontend
```bash
# In the frontend terminal, press:
Ctrl+C
```

### Stop Backend
```bash
cd /Users/pinggenchen/Desktop/OneLab0803/backend
./stop-system.sh
```

## 🔧 System Requirements Check

### Before Starting, Ensure:
- ✅ Docker Desktop is running
- ✅ Ollama is running locally (port 11434)
- ✅ Node.js is installed (`node --version`)
- ✅ You're in the correct directories

### Quick Health Check:
```bash
# Check Docker
docker --version

# Check Node.js  
node --version

# Check Ollama
curl -s http://localhost:11434/api/tags
```

## 🎮 Development Workflow

### Morning Routine:
```bash
# Terminal 1: Start Backend
cd /Users/pinggenchen/Desktop/OneLab0803/backend
./start-system.sh

# Terminal 2: Start Frontend  
cd /Users/pinggenchen/Desktop/OneLab0803/frontend
npm start

# Your full-stack app is now running! 🎉
```

### Evening Routine:
```bash
# Stop frontend: Ctrl+C in frontend terminal
# Stop backend: ./stop-system.sh or Ctrl+C
```

## 🌐 Application URLs

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | Main React app |
| **Backend API** | http://localhost:8000 | Django REST API |
| **Admin Panel** | http://localhost:8000/admin | Django admin |
| **Flower Monitor** | http://localhost:5555 | Celery tasks |
| **Ollama API** | http://localhost:11434 | AI models |

## 🚨 Troubleshooting

### "package.json not found"
```bash
pwd  # Check where you are
cd /Users/pinggenchen/Desktop/OneLab0803/frontend  # Go to frontend
npm start
```

### "Port 3000 already in use"
```bash
lsof -ti:3000 | xargs kill -9  # Kill process on port 3000
npm start  # Try again
```

### "Docker not running"
```bash
open -a Docker  # Start Docker Desktop
# Wait for Docker to start, then retry
```

### Backend not responding
```bash
cd /Users/pinggenchen/Desktop/OneLab0803/backend
docker compose ps  # Check service status
docker compose logs web  # Check logs
```

## 📋 Quick Commands Reference

| Task | Command |
|------|---------|
| **Start Backend** | `cd backend && ./start-system.sh` |
| **Start Frontend** | `cd frontend && npm start` |
| **Stop Backend** | `cd backend && ./stop-system.sh` |
| **Stop Frontend** | `Ctrl+C` |
| **Check Backend** | `docker compose ps` |
| **Check Frontend** | `lsof -i :3000` |
| **View Backend Logs** | `docker compose logs -f` |

---

**🎯 Key Point: Always navigate to the correct directory (`frontend/` or `backend/`) before running commands!**
