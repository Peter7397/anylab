# OnLab Windows Deployment Guide

## 🎯 **Overview**

This guide covers deploying OnLab from Mac development to Windows production, addressing platform-specific challenges and providing solutions.

---

## 🔍 **Mac → Windows Challenges & Solutions**

### **1. File Path Differences**

**Challenge**: Mac uses `/` paths, Windows uses `\` paths

**Solution**: ✅ **Already Handled**
- Using `pathlib` in `cross_platform.py`
- Relative paths in configuration
- Environment variables for paths

### **2. Line Ending Differences**

**Challenge**: Mac uses `\n`, Windows uses `\r\n`

**Solution**: ✅ **Git Configuration**
```bash
# Configure Git to handle line endings
git config --global core.autocrlf true  # On Windows
git config --global core.autocrlf input # On Mac
```

### **3. Environment Variable Syntax**

**Challenge**: Different syntax for environment variables

**Solution**: ✅ **Cross-platform scripts created**
- `setup-local-dev.bat` for Windows
- `setup-local-dev.sh` for Mac/Linux

### **4. Service Management**

**Challenge**: Different service management systems

**Solution**: ✅ **Docker Compose for consistency**

---

## 🚀 **Windows Deployment Options**

### **Option 1: Docker Desktop (Recommended)**

#### **Prerequisites:**
1. **Docker Desktop for Windows**
   - Download from: https://www.docker.com/products/docker-desktop
   - Enable WSL 2 backend (recommended)
   - Allocate sufficient resources (4GB RAM, 2 CPUs minimum)

2. **Windows Subsystem for Linux (WSL 2)**
   ```powershell
   # Enable WSL 2
   dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
   dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
   
   # Restart computer, then install WSL 2
   wsl --install
   ```

#### **Deployment Steps:**
```powershell
# 1. Clone repository
git clone <your-repo-url>
cd OnLab0812

# 2. Setup production environment
cd backend
copy env.docker .env
# Edit .env with production settings

# 3. Deploy with Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# 4. Verify deployment
docker-compose -f docker-compose.prod.yml ps
```

### **Option 2: Native Windows Installation**

#### **Prerequisites:**
1. **Python 3.11+**
   - Download from: https://www.python.org/downloads/
   - Add to PATH during installation

2. **PostgreSQL 16**
   - Download from: https://www.postgresql.org/download/windows/
   - Install with pgvector extension

3. **Redis for Windows**
   - Use Redis via WSL 2 or Docker
   - Or use Memurai (Redis-compatible for Windows)

#### **Deployment Steps:**
```powershell
# 1. Setup Python environment
cd backend
python -m venv venv
venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup database
# Configure PostgreSQL connection in .env

# 4. Run migrations
python manage.py migrate

# 5. Start services
python manage.py runserver
```

---

## 🔧 **Windows-Specific Configuration**

### **1. Environment Variables**

Create `backend/.env` for Windows:
```env
# Django Settings
DEBUG=False
SECRET_KEY=your-production-secret-key
ALLOWED_HOSTS=your-windows-server-ip,localhost,127.0.0.1

# Database Settings
DB_NAME=onlab
DB_USER=postgres
DB_PASSWORD=your-secure-password
DB_HOST=localhost
DB_PORT=5432

# Redis Settings
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# CORS Settings
CORS_ALLOWED_ORIGINS=http://your-frontend-domain,http://localhost:3000

# AI Settings
EMBEDDING_MODE=lightweight
OLLAMA_API_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:latest
EMBEDDING_MODEL=bge-m3

# Windows-specific settings
FILE_UPLOAD_MAX_MEMORY_SIZE=2621440
DATA_UPLOAD_MAX_MEMORY_SIZE=2621440
```

### **2. Windows Service Configuration**

Create `backend/windows-service-setup.bat`:
```batch
@echo off
REM Windows Service Setup for OnLab

echo Setting up OnLab as Windows Service...

REM Install NSSM (Non-Sucking Service Manager)
REM Download from: https://nssm.cc/download

REM Setup Django service
nssm install OnLabDjango "C:\path\to\python.exe" "C:\path\to\onlab\manage.py runserver 0.0.0.0:8000"
nssm set OnLabDjango AppDirectory "C:\path\to\onlab"
nssm set OnLabDjango Description "OnLab Django Web Server"
nssm set OnLabDjango Start SERVICE_AUTO_START

REM Setup Celery worker service
nssm install OnLabCelery "C:\path\to\python.exe" "-m celery -A onlab worker --loglevel=info"
nssm set OnLabCelery AppDirectory "C:\path\to\onlab"
nssm set OnLabCelery Description "OnLab Celery Worker"
nssm set OnLabCelery Start SERVICE_AUTO_START

REM Setup Celery beat service
nssm install OnLabCeleryBeat "C:\path\to\python.exe" "-m celery -A onlab beat --loglevel=info"
nssm set OnLabCeleryBeat AppDirectory "C:\path\to\onlab"
nssm set OnLabCeleryBeat Description "OnLab Celery Beat Scheduler"
nssm set OnLabCeleryBeat Start SERVICE_AUTO_START

echo Services installed. Start with: net start OnLabDjango
```

### **3. Windows Firewall Configuration**

```powershell
# Allow Django application
New-NetFirewallRule -DisplayName "OnLab Django" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow

# Allow PostgreSQL
New-NetFirewallRule -DisplayName "OnLab PostgreSQL" -Direction Inbound -Protocol TCP -LocalPort 5432 -Action Allow

# Allow Redis
New-NetFirewallRule -DisplayName "OnLab Redis" -Direction Inbound -Protocol TCP -LocalPort 6379 -Action Allow
```

---

## 📋 **Deployment Checklist**

### **Pre-Deployment (Mac)**
- [ ] Test all features on Mac
- [ ] Run full test suite
- [ ] Update requirements.txt
- [ ] Commit all changes
- [ ] Create production .env template
- [ ] Document any Mac-specific configurations

### **Windows Server Setup**
- [ ] Install Docker Desktop (if using Docker)
- [ ] Install Python 3.11+ (if using native)
- [ ] Install PostgreSQL 16 with pgvector
- [ ] Configure Windows Firewall
- [ ] Set up Windows Services (if using native)
- [ ] Configure environment variables

### **Deployment**
- [ ] Clone repository
- [ ] Configure .env file
- [ ] Run database migrations
- [ ] Create superuser
- [ ] Test all endpoints
- [ ] Configure SSL/TLS (production)
- [ ] Set up monitoring
- [ ] Configure backups

### **Post-Deployment**
- [ ] Verify all services running
- [ ] Test frontend integration
- [ ] Monitor logs for errors
- [ ] Set up automated backups
- [ ] Configure monitoring alerts
- [ ] Document deployment

---

## 🔄 **Migration Strategy**

### **Phase 1: Development on Mac (Current)**
```bash
# Mac development setup
cd backend
./setup-local-dev.sh
./start-local-dev.sh
```

### **Phase 2: Windows Testing**
```powershell
# Windows testing setup
cd backend
setup-local-dev.bat
start-local-dev.bat
```

### **Phase 3: Windows Production**
```powershell
# Windows production deployment
cd backend
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🛠️ **Troubleshooting Windows Issues**

### **Common Issues & Solutions**

#### **1. Docker Desktop Issues**
**Problem**: Docker Desktop not starting
**Solution**: 
- Enable WSL 2 backend
- Increase memory allocation
- Check Windows updates

#### **2. Port Conflicts**
**Problem**: Ports already in use
**Solution**:
```powershell
# Check what's using ports
netstat -ano | findstr :8000
netstat -ano | findstr :5432

# Kill process if needed
taskkill /PID <process_id> /F
```

#### **3. File Permission Issues**
**Problem**: Cannot write to directories
**Solution**:
```powershell
# Grant full control to application user
icacls "C:\path\to\onlab" /grant "Users":(OI)(CI)F
```

#### **4. Database Connection Issues**
**Problem**: Cannot connect to PostgreSQL
**Solution**:
- Check PostgreSQL service is running
- Verify connection settings in .env
- Check Windows Firewall rules

#### **5. Celery Issues on Windows**
**Problem**: Celery workers not starting
**Solution**:
- Use `eventlet` pool for Windows
- Reduce worker concurrency
- Check Redis connection

---

## 📊 **Performance Optimization for Windows**

### **1. Docker Desktop Settings**
- **Memory**: 4GB minimum, 8GB recommended
- **CPUs**: 2 minimum, 4 recommended
- **Disk**: 60GB minimum
- **WSL 2**: Enable for better performance

### **2. Windows System Settings**
- **Power Plan**: High Performance
- **Virtual Memory**: 1.5x RAM
- **Antivirus**: Exclude project directories
- **Windows Defender**: Add exclusions

### **3. Application Settings**
```python
# Windows-specific optimizations in settings.py
if is_windows():
    # Reduce worker concurrency
    CELERY_WORKER_CONCURRENCY = 2
    
    # Smaller file upload limits
    FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440
    
    # Use Windows-compatible cache
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }
```

---

## 🔐 **Security Considerations for Windows**

### **1. Windows Security**
- Enable Windows Defender
- Configure firewall rules
- Use Windows Authentication for database
- Regular security updates

### **2. Application Security**
- Use strong passwords
- Enable HTTPS in production
- Configure CORS properly
- Regular dependency updates

### **3. Data Protection**
- Encrypt sensitive data
- Regular backups
- Access control
- Audit logging

---

## 📈 **Monitoring & Maintenance**

### **1. Windows Event Logs**
```powershell
# Monitor application events
Get-EventLog -LogName Application -Source "OnLab*" -Newest 50
```

### **2. Performance Monitoring**
```powershell
# Monitor system resources
Get-Counter "\Processor(_Total)\% Processor Time"
Get-Counter "\Memory\Available MBytes"
```

### **3. Application Monitoring**
- Django admin interface
- Celery Flower monitoring
- Custom health checks
- Log file monitoring

---

## 🎯 **Final Recommendations**

### **For Your Use Case:**

1. **Start with Docker Desktop** - Easier deployment and consistency
2. **Use WSL 2 backend** - Better performance on Windows
3. **Test thoroughly** - Mac and Windows environments can differ
4. **Document everything** - Windows-specific configurations
5. **Plan for scaling** - Consider load balancing for production

### **Deployment Timeline:**
- **Week 1**: Setup Windows development environment
- **Week 2**: Test all features on Windows
- **Week 3**: Deploy to Windows production
- **Week 4**: Monitor and optimize

This approach ensures smooth transition from Mac development to Windows production while maintaining all functionality and performance.

---

**Status**: ✅ Ready for implementation
**Estimated Time**: 1-2 weeks for complete Windows deployment
**Risk Level**: Low (well-documented approach)
