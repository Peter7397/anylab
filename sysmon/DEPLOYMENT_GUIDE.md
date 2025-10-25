# OnLab SysMon Agent - Deployment Guide

## 🚀 Quick Deployment Methods

### Method 1: Automated Script (Easiest)

**Step 1: Prepare the deployment package**
```bash
# On your OnLab server, create a deployment package
cd sysmon
tar -czf sysmon-agent.tar.gz sysmon_project/ deploy-client.sh
```

**Step 2: Transfer to client**
```bash
# Copy to your target client
scp sysmon-agent.tar.gz user@client-ip:/tmp/
```

**Step 3: Deploy on client**
```bash
# SSH to your client and run:
ssh user@client-ip

# Extract and deploy
cd /tmp
tar -xzf sysmon-agent.tar.gz
cd sysmon
sudo ./deploy-client.sh
```

### Method 2: Docker Container (Recommended for Production)

**Step 1: Create Dockerfile**
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY sysmon_project/ .

RUN pip install -r requirements.txt

CMD ["python", "src/sysmon.py"]
```

**Step 2: Build and deploy**
```bash
docker build -t onlab-sysmon .
docker run -d --name sysmon-agent \
  -v /proc:/host/proc:ro \
  -v /sys:/host/sys:ro \
  -e ONELAB_SERVER=http://your-server:8000 \
  -e API_KEY=your-api-key \
  onlab-sysmon
```

### Method 3: Manual Installation

**Step 1: Install dependencies**
```bash
sudo apt update
sudo apt install python3 python3-pip
```

**Step 2: Copy files**
```bash
sudo mkdir -p /opt/sysmon-agent
sudo cp -r sysmon_project/src/* /opt/sysmon-agent/
sudo cp sysmon_project/requirements.txt /opt/sysmon-agent/
```

**Step 3: Install Python packages**
```bash
cd /opt/sysmon-agent
sudo pip3 install -r requirements.txt
```

**Step 4: Configure and run**
```bash
# Create configuration
sudo nano /opt/sysmon-agent/config/sysmon.onlab.json

# Run manually
sudo python3 /opt/sysmon-agent/sysmon.py
```

## ⚙️ Configuration

### Required Settings

Edit `/opt/sysmon-agent/config/sysmon.onlab.json`:

```json
{
  "server_url": "http://YOUR_ONELAB_SERVER:8000",
  "api_key": "YOUR_API_KEY_FROM_ONELAB_ADMIN",
  "client_name": "client-hostname",
  "monitor_interval_sec": 60,
  "upload_metrics": true
}
```

### Get API Key from OnLab

1. Log into OnLab admin panel: `http://your-server:8000/admin`
2. Go to **Users** → **API Keys** (or create one)
3. Copy the API key to your client configuration

## 🔧 Service Management

### Systemd Commands
```bash
# Check status
sudo systemctl status sysmon-agent

# Start service
sudo systemctl start sysmon-agent

# Stop service
sudo systemctl stop sysmon-agent

# Restart service
sudo systemctl restart sysmon-agent

# Enable auto-start
sudo systemctl enable sysmon-agent

# View logs
sudo journalctl -u sysmon-agent -f
```

### Manual Control
```bash
# Run in foreground
sudo python3 /opt/sysmon-agent/sysmon.py

# Run in background
sudo nohup python3 /opt/sysmon-agent/sysmon.py > /var/log/sysmon.log 2>&1 &
```

## 📊 Monitoring Features

The SysMon agent collects:

- **CPU Usage**: Total and per-process
- **Memory Usage**: RAM and swap
- **Disk Usage**: Space and I/O
- **Network**: Interface statistics
- **System Info**: Uptime, processes
- **Custom Metrics**: Configurable thresholds

## 🔍 Troubleshooting

### Common Issues

**1. Service won't start**
```bash
# Check logs
sudo journalctl -u sysmon-agent -n 50

# Check configuration
sudo python3 /opt/sysmon-agent/sysmon.py --test-config
```

**2. Can't connect to OnLab server**
```bash
# Test connectivity
curl -v http://your-onlab-server:8000/api/

# Check firewall
sudo ufw status
```

**3. Permission denied**
```bash
# Fix permissions
sudo chown -R root:root /opt/sysmon-agent
sudo chmod +x /opt/sysmon-agent/sysmon.py
```

### Log Locations
- **System logs**: `journalctl -u sysmon-agent`
- **Agent logs**: `/opt/sysmon-agent/logs/`
- **Queue files**: `/opt/sysmon-agent/queue/`

## 🛡️ Security Considerations

1. **API Key Security**: Store API keys securely, don't commit to version control
2. **Network Security**: Use HTTPS for OnLab server communication
3. **Firewall**: Ensure client can reach OnLab server on port 8000
4. **Permissions**: Run as root for system metrics access

## 📈 Performance Impact

- **CPU**: < 1% average usage
- **Memory**: ~50MB RAM
- **Disk**: < 100MB total
- **Network**: ~1KB per minute

## 🔄 Updates

To update the agent:

```bash
# Stop service
sudo systemctl stop sysmon-agent

# Backup configuration
sudo cp /opt/sysmon-agent/config/sysmon.onlab.json /tmp/

# Update files
sudo cp -r new-sysmon-files/* /opt/sysmon-agent/

# Restore configuration
sudo cp /tmp/sysmon.onlab.json /opt/sysmon-agent/config/

# Restart service
sudo systemctl start sysmon-agent
```

## 📞 Support

For issues or questions:
1. Check the logs: `sudo journalctl -u sysmon-agent -f`
2. Verify configuration syntax
3. Test network connectivity
4. Check OnLab server status
