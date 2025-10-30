# 🚀 OnLab Frontend - Startup Guide

## Quick Start (Daily Use)

### 1. Navigate to Frontend Directory
```bash
cd frontend
```

### 2. Start Frontend Development Server
```bash
npm start
```

**That's it!** The frontend will start on http://localhost:3000

## ⚠️ Common Mistakes to Avoid

### ❌ Don't run `npm start` from the wrong directory:
```bash
# WRONG - This will fail (no package.json here)
cd ..
npm start

# WRONG - This will fail (this is backend directory)
cd backend
npm start
```

### ✅ Always run from the frontend directory:
```bash
# CORRECT
cd frontend
npm start
```

## 📋 Complete Startup Sequence

### Start Backend First:
```bash
# Terminal 1: Backend
cd backend
docker compose up -d
```

### Then Start Frontend:
```bash
# Terminal 2: Frontend  
cd frontend
npm start
```

## 🔧 Alternative Methods

### Method 1: From Project Root
```bash
cd frontend && npm start
```

### Method 2: Direct Path
```bash
cd frontend && npm start
```

### Method 3: VS Code Integrated Terminal
```bash
# In VS Code, open terminal in frontend folder
npm start
```

## 🌐 What to Expect

When you run `npm start`:
```
Compiled successfully!

You can now view onlab-frontend in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.x.x:3000

Note that the development build is not optimized.
To create a production build, use npm run build.

webpack compiled with warnings
```

## 🛠️ Troubleshooting

### If you get "package.json not found" error:
```bash
# Check your current directory
pwd

# Ensure it ends with /frontend; if not, navigate to frontend directory:
cd frontend
```

### If port 3000 is busy:
```bash
# Kill any process using port 3000
lsof -ti:3000 | xargs kill -9

# Then start again
npm start
```

### If you get dependency errors:
```bash
# Reinstall dependencies (rarely needed)
npm install
npm start
```

## 🎯 Quick Reference

| Action | Command |
|--------|---------|
| **Start Frontend** | `cd frontend && npm start` |
| **Stop Frontend** | `Ctrl+C` in terminal |
| **Check if Running** | Open http://localhost:3000 |
| **Check Port Usage** | `lsof -i :3000` |

## 🔄 Daily Workflow

```bash
# Morning startup
cd backend
docker compose up -d

# In another terminal
cd frontend  
npm start

# Work on your project...

# Evening shutdown
# Ctrl+C in frontend terminal
# docker compose down in backend if needed
```

---

**💡 Remember: Always be in the `/frontend` directory when running `npm start`!**
