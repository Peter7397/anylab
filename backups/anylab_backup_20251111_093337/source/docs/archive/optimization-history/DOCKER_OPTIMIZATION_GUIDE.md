# Docker Memory Optimization Guide

**Date:** November 11, 2025  
**Status:** Ready for Implementation  
**Expected Savings:** 7-8 GB RAM

---

## 📊 BEFORE vs AFTER Comparison

### Docker Desktop Allocation

| Setting | Before | After | Savings |
|---------|--------|-------|---------|
| **Docker VM Memory** | 11.67 GB | 4 GB | **-7.67 GB** ✅ |
| **Docker VM CPUs** | 10 cores | 4-6 cores | Save CPU for other projects |

### Container Memory Limits

| Container | Before | After | Current Usage | Headroom |
|-----------|--------|-------|---------------|----------|
| **PostgreSQL** | Unlimited (11.67 GB) | 256 MB | 97 MB | 2.6x ✅ |
| **Redis** | Unlimited (11.67 GB) | 128 MB | 13 MB | 10x ✅ |
| **Neo4j** | Unlimited (11.67 GB) | 2 GB | 1.466 GB | 36% ✅ |
| **Total** | ~35 GB potential | 2.384 GB | 1.576 GB | 51% ✅ |

### Neo4j Memory Configuration

| Setting | Before | After | Savings |
|---------|--------|-------|---------|
| **Heap Initial** | 512 MB | 256 MB | -256 MB |
| **Heap Max** | 2 GB | 1 GB | -1 GB |
| **Pagecache** | 1 GB | 512 MB | -512 MB |
| **Total** | ~3 GB | ~1.5 GB | **-1.5 GB** ✅ |

---

## 🎯 Total System Impact

### Memory Availability

```
BEFORE Optimization:
┌─────────────────────────────────────────┐
│ 16 GB Total RAM                         │
├─────────────────────────────────────────┤
│ Docker Desktop:       11.67 GB  🔴      │
│ Docker Containers:    ~1.6 GB           │
│ macOS + Apps:         ~3.5 GB           │
│ Swap Usage:           7.6 GB    🔴      │
│ Available:            <0.5 GB   🔴      │
└─────────────────────────────────────────┘
Status: CRITICAL 🚨

AFTER Optimization:
┌─────────────────────────────────────────┐
│ 16 GB Total RAM                         │
├─────────────────────────────────────────┤
│ Docker Desktop:       4 GB      ✅      │
│ Docker Containers:    ~1.8 GB           │
│ AnyLab Backend:       ~1.8 GB           │
│ 7English Project:     ~1.5 GB           │
│ Other Project:        ~3 GB             │
│ macOS + Apps:         ~2 GB             │
│ Available Buffer:     ~4 GB     ✅      │
└─────────────────────────────────────────┘
Status: HEALTHY 🟢
Swap Usage: <1 GB
```

**Total Freed Memory: ~7-8 GB** 🎉

---

## 📝 Implementation Steps

### Step 1: Stop Current Containers (2 minutes)

```bash
cd /Volumes/Orico/Anylab103

# Stop all containers
docker-compose down

# Verify all stopped
docker ps -a | grep anylab
```

### Step 2: Reduce Docker Desktop Memory (5 minutes)

**Manual Steps:**
1. Open **Docker Desktop** application
2. Click the **Settings** ⚙️ icon (top right)
3. Navigate to **Resources** → **Memory**
4. Change slider from **11.67 GB** to **4 GB**
5. **Optional:** Also reduce CPUs from 10 to 4-6
6. Click **Apply & Restart**
7. Wait for Docker to restart (green icon in menu bar)

**This is the BIGGEST savings: 7.67 GB freed!** ✅

### Step 3: Apply Optimized Docker Compose (2 minutes)

```bash
cd /Volumes/Orico/Anylab103

# Verify backup exists
ls -lh docker-compose.yml.backup-*

# Replace with optimized version
cp docker-compose.optimized.yml docker-compose.yml

# Verify the new file
cat docker-compose.yml | grep -E "(memory:|cpus:)" 
```

### Step 4: Start Optimized Containers (3 minutes)

```bash
# Start containers with new limits
docker-compose up -d

# Wait for containers to be healthy (check every 10 seconds)
watch -n 10 'docker-compose ps'

# Or check manually:
docker-compose ps
```

Expected output:
```
NAME              STATUS                    PORTS
anylab_neo4j      Up (healthy)             0.0.0.0:7474->7474/tcp, 7687->7687/tcp
anylab_postgres   Up (healthy)             0.0.0.0:5433->5432/tcp
anylab_redis      Up (healthy)             0.0.0.0:6379->6379/tcp
```

### Step 5: Verify Memory Limits (1 minute)

```bash
# Check container memory usage with limits
docker stats --no-stream

# Should see memory limits like:
# anylab_neo4j:    1.4GB / 2GB
# anylab_postgres: 97MB / 256MB
# anylab_redis:    13MB / 128MB
```

### Step 6: Test Application (2 minutes)

```bash
# Test PostgreSQL
docker exec anylab_postgres psql -U postgres -d anylab -c "SELECT version();"

# Test Redis
docker exec anylab_redis redis-cli ping

# Test Neo4j (in browser)
# Open: http://localhost:7474
# Login: neo4j / anylab_neo4j_password
```

**Total Implementation Time: ~15 minutes**

---

## ✅ Verification Checklist

After implementation, verify:

- [ ] Docker Desktop shows 4 GB memory allocation
- [ ] All 3 containers are running and healthy
- [ ] `docker stats` shows memory limits in effect
- [ ] PostgreSQL accepts connections
- [ ] Redis responds to PING
- [ ] Neo4j browser is accessible
- [ ] Backend can connect to all databases
- [ ] System RAM usage is significantly lower
- [ ] Swap usage is minimal (<1 GB)

---

## 🔄 Rollback Procedure (If Needed)

If anything goes wrong, you can quickly rollback:

```bash
cd /Volumes/Orico/Anylab103

# Stop containers
docker-compose down

# Restore original configuration
cp docker-compose.yml.backup-YYYYMMDD-HHMMSS docker-compose.yml
# (use the actual backup filename with timestamp)

# Restart with original config
docker-compose up -d

# Restore Docker Desktop memory to 11.67 GB in Settings
```

---

## 🎯 Key Optimizations Explained

### PostgreSQL (256 MB limit)
- **shared_buffers: 64MB** - Memory for caching data (25% of container)
- **effective_cache_size: 128MB** - Estimated OS cache (50% of container)
- **work_mem: 4MB** - Memory per query operation
- **max_connections: 50** - Reduced from 100 to save memory

**Impact:** Minimal - PostgreSQL works well with small buffers for your workload

### Redis (128 MB limit)
- **maxmemory: 100MB** - Hard limit on data storage
- **maxmemory-policy: allkeys-lru** - Evict least recently used keys when full
- **Persistence optimized** - Less frequent saves to reduce memory overhead

**Impact:** None - Redis is very memory-efficient for your cache usage

### Neo4j (2 GB limit)
- **Heap reduced to 1 GB** - JVM heap for object storage (was 2 GB)
- **Pagecache reduced to 512 MB** - File system cache (was 1 GB)
- **Transaction limits added** - Prevent runaway queries from consuming all memory

**Impact:** Minimal - Your current usage of 1.466 GB fits comfortably with 36% headroom

---

## 📈 Monitoring After Optimization

### First 24 Hours - Watch Closely

```bash
# Monitor memory usage every hour
watch -n 3600 'docker stats --no-stream'

# Check for OOM (Out of Memory) kills
docker-compose logs --tail=100 | grep -i "memory\|oom\|killed"

# Monitor system memory
vm_stat | awk 'NR==1 {print; next} /Pages free|Pages active|Pages inactive/ {printf "%-20s %10.2f GB\n", $1 " " $2, $3 * 16384 / 1024 / 1024 / 1024}'
```

### If Neo4j Hits Memory Limit

**Symptoms:**
- Queries become slow
- Container restarts unexpectedly
- Logs show "OutOfMemoryError"

**Solutions:**
1. Check query patterns - optimize expensive queries
2. Reduce concurrent connections
3. If needed, increase heap_max to 1.5 GB (still better than 2 GB)
4. Add more system RAM (upgrade to 24 GB)

### If PostgreSQL Hits Memory Limit

**Symptoms:**
- Connection errors
- Slow queries
- Container restarts

**Solutions:**
1. Increase shared_buffers to 96 MB
2. Increase container limit to 384 MB
3. Optimize queries to use indexes

---

## 💡 Additional Recommendations

### 1. Regular Memory Monitoring
Add to crontab:
```bash
# Check memory usage daily
0 9 * * * docker stats --no-stream > /Volumes/Orico/Anylab103/logs/docker-stats-$(date +\%Y\%m\%d).log
```

### 2. Log Rotation
Prevent logs from consuming disk space:
```bash
# Add to docker-compose.yml for each service:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 3. Periodic Container Restart
Restart containers weekly to clear any memory fragmentation:
```bash
# Add to crontab - restart at 3 AM Sunday
0 3 * * 0 cd /Volumes/Orico/Anylab103 && docker-compose restart
```

---

## 🆘 Troubleshooting

### Container Won't Start After Optimization

**Check logs:**
```bash
docker-compose logs neo4j
docker-compose logs postgres
docker-compose logs redis
```

**Common issues:**
- Neo4j heap too small: Increase to 768 MB or 1 GB
- PostgreSQL shared_buffers invalid: Must be multiple of 8KB
- Redis maxmemory reached: Increase to 150 MB

### System Still Using Too Much Swap

**Check what else is consuming memory:**
```bash
# Top memory consumers
ps aux | sort -nrk 4 | head -20

# Check if other Docker projects are running
docker ps -a
```

**Solutions:**
- Stop 7English project when not needed
- Close Chrome/browsers with many tabs
- Quit Cursor/Xcode when not coding

---

## 📞 Support

If you encounter issues:
1. Check the rollback procedure above
2. Review container logs: `docker-compose logs`
3. Check system memory: `vm_stat`
4. Verify Docker Desktop settings

---

**Remember: You can always rollback to the original configuration if needed!**

