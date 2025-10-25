#!/bin/bash

# OnLab SysMon Agent - Client Deployment Script
# This script makes it easy to deploy the system monitor to target clients

set -e

# Configuration - UPDATE THESE FOR YOUR ENVIRONMENT
ONELAB_SERVER="http://YOUR_SERVER_IP:8000"  # Change to your OnLab server IP
API_KEY="YOUR_API_KEY_HERE"                 # Get this from OnLab admin panel
CLIENT_NAME="$(hostname)"                   # Auto-detected, or set manually

# Installation paths
INSTALL_DIR="/opt/sysmon-agent"
SERVICE_NAME="sysmon-agent"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}=== OnLab SysMon Agent Deployment ===${NC}"
echo -e "${BLUE}Target Server: $ONELAB_SERVER${NC}"
echo -e "${BLUE}Client Name: $CLIENT_NAME${NC}"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}❌ This script must be run as root (use sudo)${NC}"
   exit 1
fi

# Check Python version
echo -e "${YELLOW}🔍 Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed. Please install Python 3.7+ first.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo -e "${GREEN}✅ Python version: $PYTHON_VERSION${NC}"

# Create installation directory
echo -e "${YELLOW}📁 Creating installation directory...${NC}"
mkdir -p $INSTALL_DIR/{logs,queue,temp,config}

# Copy agent files (assuming script is run from sysmon directory)
echo -e "${YELLOW}📋 Copying agent files...${NC}"
if [ -d "sysmon_project/src" ]; then
    cp -r sysmon_project/src/* $INSTALL_DIR/
    cp sysmon_project/requirements.txt $INSTALL_DIR/
else
    echo -e "${RED}❌ Agent files not found. Please run this script from the sysmon directory.${NC}"
    exit 1
fi

# Install Python dependencies
echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"
cd $INSTALL_DIR
pip3 install -r requirements.txt

# Create configuration file
echo -e "${YELLOW}⚙️  Creating configuration...${NC}"
cat > $INSTALL_DIR/config/sysmon.onlab.json << EOF
{
  "server_url": "$ONELAB_SERVER",
  "api_key": "$API_KEY",
  "client_name": "$CLIENT_NAME",
  "monitor_interval_sec": 60,
  "upload_metrics": true,
  "enable_detailed_logging": false,
  "max_queue_size": 1000,
  "paths": {
    "logs": "logs",
    "queue": "queue",
    "temp": "temp"
  },
  "thresholds": {
    "cpu_total": {
      "warn_pct": 70,
      "crit_pct": 90
    },
    "ram": {
      "warn_pct": 75,
      "crit_pct": 90
    },
    "disk_free": {
      "warn_pct": 20,
      "crit_pct": 10
    }
  }
}
EOF

# Create systemd service file
echo -e "${YELLOW}🔧 Creating system service...${NC}"
cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=OnLab SysMon Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/sysmon.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Set permissions
chmod +x $INSTALL_DIR/sysmon.py
chown -R root:root $INSTALL_DIR

# Enable and start service
echo -e "${YELLOW}🚀 Starting SysMon service...${NC}"
systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl start $SERVICE_NAME

# Check service status
echo -e "${YELLOW}📊 Checking service status...${NC}"
sleep 3
if systemctl is-active --quiet $SERVICE_NAME; then
    echo -e "${GREEN}✅ SysMon Agent is running successfully!${NC}"
else
    echo -e "${RED}❌ Service failed to start. Check logs with: journalctl -u $SERVICE_NAME${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo ""
echo -e "${BLUE}📋 Service Information:${NC}"
echo -e "   Service Name: $SERVICE_NAME"
echo -e "   Install Directory: $INSTALL_DIR"
echo -e "   Configuration: $INSTALL_DIR/config/sysmon.onlab.json"
echo -e "   Logs: $INSTALL_DIR/logs/"
echo ""
echo -e "${BLUE}🔧 Useful Commands:${NC}"
echo -e "   Check Status: sudo systemctl status $SERVICE_NAME"
echo -e "   View Logs: sudo journalctl -u $SERVICE_NAME -f"
echo -e "   Restart: sudo systemctl restart $SERVICE_NAME"
echo -e "   Stop: sudo systemctl stop $SERVICE_NAME"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT: Make sure to update the API key in the configuration file!${NC}"
echo -e "   Edit: sudo nano $INSTALL_DIR/config/sysmon.onlab.json"
