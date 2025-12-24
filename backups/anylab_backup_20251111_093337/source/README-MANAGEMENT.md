# AnyLab Management Scripts

**Updated:** November 11, 2025  
**Status:** Production Ready

---

## 🎯 Quick Reference

### **Main Management Commands:**

```bash
./anylab-start.sh    # Start all services (Docker + Backend)
./anylab-stop.sh     # Stop all services
./anylab-restart.sh  # Restart everything
./anylab-status.sh   # Check status of all services
./anylab-logs.sh     # View logs (interactive)
```

---

## 📋 Detailed Usage

### **1. anylab-start.sh**
Starts the complete AnyLab system:
- ✅ Starts Docker containers (PostgreSQL, Redis, Neo4j)
- ✅ Starts production backend via launchd (Gunicorn)
- ✅ Waits for services to be healthy
- ✅ Performs health checks

**Usage:**
```bash
./anylab-start.sh
```

**What it does:**
1. Checks Docker is running
2. Starts Docker Compose services
3. Waits 10 seconds for initialization
4. Loads/restarts backend via launchd
5. Verifies backend is listening on port 8001
6. Performs health check
7. Shows status summary

---

### **2. anylab-stop.sh**
Stops all AnyLab services:
- ✅ Stops production backend (unloads from launchd)
- ✅ Stops Docker containers

**Usage:**
```bash
./anylab-stop.sh
```

**What it does:**
1. Unloads backend from launchd
2. Stops all Docker Compose services
3. Confirms shutdown

---

### **3. anylab-restart.sh**
Convenience script for full restart:
- ✅ Calls stop script
- ✅ Waits 3 seconds
- ✅ Calls start script

**Usage:**
```bash
./anylab-restart.sh
```

---

### **4. anylab-status.sh**
Comprehensive status check:
- ✅ Docker service status
- ✅ Container health
- ✅ Memory usage per container
- ✅ Backend status (port, PID, memory, health)
- ✅ Cloudflare Tunnel status
- ✅ System resources (RAM, swap)
- ✅ Access URLs

**Usage:**
```bash
./anylab-status.sh
```

**Example Output:**
```
📊 AnyLab System Status
======================================

🐳 Docker Services:
   anylab_postgres: Up (healthy) - 18.7MiB / 256MiB
   anylab_redis:    Up (healthy) - 10.88MiB / 128MiB
   anylab_neo4j:    Up (healthy) - 510MiB / 2GiB

🔧 Backend (Gunicorn):
   ✅ Running on port 8001
   PID: 47034
   Memory: 0.0%
   Health: Healthy

💾 System Resources:
   Free RAM: 0.05 GB
   Swap: used = 7113.94M
```

---

### **5. anylab-logs.sh**
Interactive log viewer with multiple options:
1. Backend Error Log (follow mode)
2. Backend Access Log (follow mode)
3. All Docker logs (last 50 lines)
4. PostgreSQL logs
5. Neo4j logs
6. Redis logs
7. All backend logs (follow mode)
8. All Docker logs (follow mode)

**Usage:**
```bash
./anylab-logs.sh
# Then select option 1-8
```

---

## 🔄 Typical Workflows

### **Daily Startup:**
```bash
./anylab-start.sh
```

### **Daily Shutdown:**
```bash
./anylab-stop.sh
```

### **After System Reboot:**
Backend will auto-start via launchd. Just start Docker:
```bash
docker compose up -d
```
Or use:
```bash
./anylab-start.sh
```

### **Something Not Working:**
```bash
# Check status
./anylab-status.sh

# Check logs
./anylab-logs.sh

# Try restart
./anylab-restart.sh
```

### **Backend Only Restart:**
```bash
launchctl kickstart -k gui/$(id -u)/com.anylab.backend
```

### **Docker Only Restart:**
```bash
docker compose restart
```

---

## 📂 File Locations

### **Scripts:**
- `/Volumes/Orico/Anylab103/anylab-*.sh` - Management scripts

### **Configuration:**
- `/Volumes/Orico/Anylab103/docker-compose.yml` - Docker services
- `/Volumes/Orico/Anylab103/backend/gunicorn_config.py` - Gunicorn config
- `~/Library/LaunchAgents/com.anylab.backend.plist` - Auto-start config

### **Logs:**
- `/Volumes/Orico/Anylab103/logs/gunicorn-error.log` - Backend errors
- `/Volumes/Orico/Anylab103/logs/gunicorn-access.log` - HTTP requests
- `docker compose logs` - Docker container logs

### **Old Scripts (Archived):**
- `/Volumes/Orico/Anylab103/old-scripts/` - Previous start/stop scripts

---

## 🔧 Manual Management

### **Backend (launchd):**
```bash
# Load (enable auto-start)
launchctl load ~/Library/LaunchAgents/com.anylab.backend.plist

# Unload (disable)
launchctl unload ~/Library/LaunchAgents/com.anylab.backend.plist

# Restart
launchctl kickstart -k gui/$(id -u)/com.anylab.backend

# Check status
launchctl list | grep anylab

# View service details
launchctl list com.anylab.backend
```

### **Docker:**
```bash
# Start
docker compose up -d

# Stop
docker compose down

# Restart
docker compose restart

# Logs
docker compose logs -f

# Status
docker compose ps
```

### **Check Ports:**
```bash
# Backend port
lsof -i :8001

# PostgreSQL
lsof -i :5433

# Redis
lsof -i :6379

# Neo4j
lsof -i :7474
lsof -i :7687
```

---

## 🆘 Troubleshooting

### **Backend won't start:**
1. Check if already running: `lsof -i :8001`
2. Check logs: `tail -f logs/gunicorn-error.log`
3. Check launchd status: `launchctl list com.anylab.backend`
4. Try manual start: `cd backend && ./venv/bin/gunicorn anylab.wsgi:application --bind 0.0.0.0:8001`

### **Docker services unhealthy:**
1. Check container logs: `docker compose logs <service>`
2. Check container stats: `docker stats`
3. Restart specific service: `docker compose restart <service>`

### **Port already in use:**
1. Find what's using it: `lsof -i :<port>`
2. Kill the process or use different port

### **Memory issues:**
1. Check status: `./anylab-status.sh`
2. Reduce Docker Desktop memory to 4 GB
3. Restart services: `./anylab-restart.sh`

---

## 💡 Best Practices

1. **Always use management scripts** instead of manual commands
2. **Check status** before troubleshooting: `./anylab-status.sh`
3. **Review logs** when issues occur: `./anylab-logs.sh`
4. **Don't run multiple instances** - check first with status script
5. **Keep Docker Desktop** at 4 GB memory allocation
6. **Monitor system resources** regularly

---

## 🎉 Benefits of New System

✅ **Production-grade:** Gunicorn WSGI server  
✅ **Auto-restart:** launchd monitors and restarts on crash  
✅ **Memory optimized:** Docker containers have limits  
✅ **Easy management:** Simple, clear commands  
✅ **Comprehensive monitoring:** Status and log viewing  
✅ **Reliable:** No more runserver crashes  

---

**For issues or questions, check logs first with `./anylab-logs.sh`**

