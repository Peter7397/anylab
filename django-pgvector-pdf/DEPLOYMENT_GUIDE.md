# 🚀 Deployment Guide - Offline Docker Application

## ✅ Current Status: Everything is Offline!

Your application is now **completely self-contained** and runs offline:

### 🐳 **Docker Containers Running:**
- ✅ **Django Web App** - Containerized web application
- ✅ **PostgreSQL Database** - Containerized with pgvector extension
- ✅ **Ollama + Qwen Model** - Containerized AI model (qwen2:latest)
- ✅ **all-MiniLM-L6-v2 Model** - Local embedding model
- ✅ **Nginx** - Containerized reverse proxy

### 🔒 **Offline Features:**
- No external API calls required
- All AI models are local
- Database is self-contained
- Works without internet connection
- All dependencies are in Docker images

## 🚀 Deployment Methods

### **Method 1: Quick Deployment Script**

```bash
# Create deployment package
./deploy.sh my-deployment-folder

# Copy to target system
scp -r my-deployment-folder user@target-server:/path/to/deploy/

# On target system
cd /path/to/deploy/my-deployment-folder
docker volume create ollama_data
docker compose up -d
```

### **Method 2: Manual Deployment**

#### **Step 1: Prepare Deployment Package**
```bash
# Create deployment directory
mkdir my-app-deployment
cd my-app-deployment

# Copy essential files
cp -r ../docker-compose.yml .
cp -r ../Dockerfile .
cp -r ../requirements.txt .
cp -r ../.env .
cp -r ../all-MiniLM-L6-v2_local_copy .
cp -r ../pdfimport .
cp -r ../myproject .
cp -r ../manage.py .
cp -r ../nginx .
cp -r ../init-db.sh .
cp -r ../docker-entrypoint.sh .
cp -r ../test_ollama.py .
```

#### **Step 2: Transfer to Target System**
```bash
# Option A: SCP (Linux/Mac)
scp -r my-app-deployment user@target-server:/home/user/

# Option B: USB Drive
# Copy the folder to USB drive and transfer

# Option C: Git Repository
git init
git add .
git commit -m "Initial deployment"
git remote add origin your-repo-url
git push -u origin main
```

#### **Step 3: Deploy on Target System**
```bash
# On target system
cd my-app-deployment

# Create Docker volume
docker volume create ollama_data

# Start services
docker compose up -d

# Test deployment
python3 test_ollama.py
```

## 📋 System Requirements

### **Minimum Requirements:**
- **RAM**: 8GB (16GB recommended)
- **Storage**: 20GB free space
- **CPU**: 4 cores minimum
- **OS**: Linux, macOS, or Windows with Docker

### **Recommended Requirements:**
- **RAM**: 16GB or more
- **Storage**: 50GB free space
- **CPU**: 8 cores or more
- **GPU**: Optional (for faster AI inference)

## 🔧 Pre-deployment Checklist

### **Target System Preparation:**
```bash
# 1. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 2. Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 3. Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

## 🚀 Quick Deployment Commands

### **One-Command Deployment:**
```bash
# Create and deploy
./deploy.sh && cd django-pgvector-pdf-deployed && docker volume create ollama_data && docker compose up -d
```

### **Test Deployment:**
```bash
# Test Ollama
python3 test_ollama.py

# Test web interface
curl http://localhost:8000

# Check all services
docker compose ps
```

## 🌐 Production Deployment

### **For Production Servers:**

1. **Update Environment Variables:**
```bash
# Edit .env file
nano .env

# Change these for production:
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-domain.com,your-ip
POSTGRES_PASSWORD=your-secure-password
```

2. **Configure Nginx:**
```bash
# Edit nginx configuration
nano nginx/conf.d/default.conf

# Add your domain
server_name your-domain.com;
```

3. **Set Up SSL (Optional):**
```bash
# Add SSL certificates to nginx/ssl/
# Update nginx configuration for HTTPS
```

## 🔍 Monitoring & Maintenance

### **Health Checks:**
```bash
# Check service status
docker compose ps

# View logs
docker compose logs -f

# Monitor resource usage
docker stats
```

### **Backup & Restore:**
```bash
# Backup database
docker compose exec db pg_dump -U postgres mydb > backup.sql

# Restore database
docker compose exec -T db psql -U postgres mydb < backup.sql

# Backup Ollama models
docker run --rm -v ollama_data:/data -v $(pwd):/backup alpine tar czf /backup/ollama-backup.tar.gz -C /data .
```

## 🛠️ Troubleshooting

### **Common Issues:**

1. **Port Conflicts:**
```bash
# Check what's using the ports
lsof -i :8000
lsof -i :11435
lsof -i :5432

# Change ports in .env if needed
```

2. **Memory Issues:**
```bash
# Check available memory
free -h

# Reduce Ollama model size or increase Docker memory limit
```

3. **Permission Issues:**
```bash
# Fix file permissions
chmod +x docker-entrypoint.sh
chmod +x init-db.sh
```

## 📊 Performance Optimization

### **For Better Performance:**
```bash
# Increase Docker memory limit
# Edit Docker Desktop settings or docker daemon config

# Use GPU acceleration (if available)
# Add GPU support to docker-compose.yml
```

## 🎯 Success Indicators

Your deployment is successful when:

✅ `docker compose ps` shows all services as "Up"  
✅ `python3 test_ollama.py` returns success  
✅ `curl http://localhost:8000` returns HTTP 302 (redirect)  
✅ Web interface is accessible at http://localhost:8000  

## 🔄 Updates & Maintenance

### **Updating the Application:**
```bash
# Pull latest changes
git pull origin main

# Rebuild containers
docker compose down
docker compose up --build -d
```

### **Updating Models:**
```bash
# Update Ollama models
docker compose exec ollama ollama pull qwen2.5:7b

# Update embedding model
# Replace all-MiniLM-L6-v2_local_copy with new version
```

## 🎉 Deployment Complete!

Your offline Docker application is now ready for deployment to any system with Docker support. The application is completely self-contained and will work without internet connectivity once deployed. 