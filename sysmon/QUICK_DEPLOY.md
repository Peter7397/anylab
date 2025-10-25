# 🚀 Quick Deploy - SysMon Agent

## ⚡ Easiest Method (3 Steps)

### Step 1: Get API Key from OnLab
```bash
# Log into OnLab admin panel
http://your-onlab-server:8000/admin

# Go to Users → API Keys → Create new key
# Copy the API key
```

### Step 2: Deploy to Client
```bash
# On your OnLab server
cd sysmon
./create-package.sh

# Copy package to client
scp onlab-sysmon-agent-2.0.0.tar.gz user@client-ip:/tmp/

# SSH to client
ssh user@client-ip

# Extract and deploy
cd /tmp
tar -xzf onlab-sysmon-agent-2.0.0.tar.gz
cd onlab-sysmon-agent-2.0.0

# Edit configuration
nano deploy-client.sh
# Update: ONELAB_SERVER and API_KEY

# Deploy
sudo ./deploy-client.sh
```

### Step 3: Verify Installation
```bash
# Check service status
sudo systemctl status sysmon-agent

# View logs
sudo journalctl -u sysmon-agent -f

# Check OnLab dashboard
http://your-onlab-server:3000
```

## 🔧 Configuration

**Required changes in `deploy-client.sh`:**
```bash
ONELAB_SERVER="http://YOUR_SERVER_IP:8000"  # Your OnLab server
API_KEY="YOUR_API_KEY_HERE"                 # From admin panel
```

## 📊 What Gets Monitored

- ✅ CPU usage (total & per-process)
- ✅ Memory usage (RAM & swap)
- ✅ Disk space & I/O
- ✅ Network statistics
- ✅ System uptime
- ✅ Process count
- ✅ Custom alerts

## 🛠️ Troubleshooting

**Service not starting:**
```bash
sudo journalctl -u sysmon-agent -n 50
```

**Can't connect to server:**
```bash
curl -v http://your-onlab-server:8000/api/
```

**Permission issues:**
```bash
sudo chown -R root:root /opt/sysmon-agent
sudo chmod +x /opt/sysmon-agent/sysmon.py
```

## 📞 Quick Commands

```bash
# Service management
sudo systemctl start sysmon-agent
sudo systemctl stop sysmon-agent
sudo systemctl restart sysmon-agent
sudo systemctl status sysmon-agent

# Logs
sudo journalctl -u sysmon-agent -f

# Manual run
sudo python3 /opt/sysmon-agent/sysmon.py
```

## 🎯 Success Indicators

- ✅ Service shows "active (running)"
- ✅ Logs show "Connected to OnLab server"
- ✅ Client appears in OnLab dashboard
- ✅ Metrics are being collected
