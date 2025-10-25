#!/bin/bash

# SysMon Agent Deployment Script for OnLab v2.0
# This script deploys the enhanced sysmon agent to a client system

set -e

# Configuration
AGENT_NAME="sysmon-agent"
ONELAB_SERVER="http://localhost:8000"
API_KEY="CHANGE_ME_TO_ONELAB_API_KEY"
INSTALL_DIR="/opt/sysmon-agent"
SERVICE_NAME="sysmon-agent"
AGENT_VERSION="2.0.0"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== SysMon Agent Deployment Script v${AGENT_VERSION} ===${NC}"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root${NC}"
   exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
if [[ $(echo "$PYTHON_VERSION >= 3.7" | bc -l) -eq 0 ]]; then
    echo -e "${RED}Python 3.7 or higher is required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi

echo -e "${BLUE}Python version: $PYTHON_VERSION${NC}"

# Create installation directory
echo -e "${YELLOW}Creating installation directory...${NC}"
mkdir -p $INSTALL_DIR
mkdir -p $INSTALL_DIR/logs
mkdir -p $INSTALL_DIR/queue
mkdir -p $INSTALL_DIR/temp
mkdir -p $INSTALL_DIR/config

# Copy agent files
echo -e "${YELLOW}Copying agent files...${NC}"
cp -r sysmon_project/src/* $INSTALL_DIR/
cp sysmon_project/requirements.txt $INSTALL_DIR/

# Create OnLab configuration
echo -e "${YELLOW}Creating OnLab configuration...${NC}"
cat > $INSTALL_DIR/config/sysmon.onlab.json << EOF
{
  "monitor_interval_sec": 60,
  "hostname_alias": "",
  "dedup_suppress_sec": 1800,
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
      "warn_window_sec": 300,
      "crit_pct": 90,
      "crit_window_sec": 60
    },
    "cpu_per_process": {
      "warn_pct": 30,
      "warn_window_sec": 300,
      "crit_pct": 50,
      "crit_window_sec": 120,
      "top_n": 10
    },
    "ram": {
      "warn_pct": 75,
      "crit_pct": 90,
      "avail_warn_mb": 1024,
      "avail_crit_mb": 500,
      "pagefile_warn_pct": 70,
      "pagefile_crit_pct": 85
    },
    "disk_free": [
      {
        "drive": "C:",
        "warn_pct": 20,
        "crit_pct": 10,
        "crit_min_gb": 5
      },
      {
        "drive": "*",
        "warn_pct": 20,
        "crit_pct": 10
      }
    ]
  },
  "alert_server": {
    "base_url": "$ONELAB_SERVER/api/monitoring/sysmon",
    "api_key": "$API_KEY",
    "connect_timeout_sec": 5,
    "read_timeout_sec": 20,
    "retry_attempts": 3,
    "retry_delay_sec": 5,
    "tls": {
      "verify": false,
      "ca_bundle_path": null
    }
  },
  "performance": {
    "process_cache_ttl_sec": 5,
    "max_processes_to_monitor": 100,
    "min_cpu_threshold_pct": 0.1,
    "enable_process_filtering": true
  },
  "logging": {
    "level": "INFO",
    "max_file_size_mb": 10,
    "backup_count": 5,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  }
}
EOF

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
cd $INSTALL_DIR

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo -e "${YELLOW}Installing pip3...${NC}"
    if command -v apt-get &> /dev/null; then
        apt-get update && apt-get install -y python3-pip
    elif command -v yum &> /dev/null; then
        yum install -y python3-pip
    elif command -v dnf &> /dev/null; then
        dnf install -y python3-pip
    else
        echo -e "${RED}Could not install pip3. Please install it manually.${NC}"
        exit 1
    fi
fi

# Install requirements
pip3 install --upgrade pip
pip3 install -r requirements.txt

# Create systemd service
echo -e "${YELLOW}Creating systemd service...${NC}"
cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=SysMon Agent for OnLab v${AGENT_VERSION}
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/sysmon.py --global config/global.default.json --local config/sysmon.onlab.json --upload-metrics
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$INSTALL_DIR

# Resource limits
LimitNOFILE=65536
MemoryMax=512M

[Install]
WantedBy=multi-user.target
EOF

# Set permissions
echo -e "${YELLOW}Setting permissions...${NC}"
chown -R root:root $INSTALL_DIR
chmod +x $INSTALL_DIR/sysmon.py
chmod 755 $INSTALL_DIR
chmod 755 $INSTALL_DIR/logs
chmod 755 $INSTALL_DIR/queue
chmod 755 $INSTALL_DIR/temp
chmod 644 $INSTALL_DIR/config/*.json

# Create logrotate configuration
echo -e "${YELLOW}Creating logrotate configuration...${NC}"
cat > /etc/logrotate.d/$SERVICE_NAME << EOF
$INSTALL_DIR/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        systemctl reload $SERVICE_NAME > /dev/null 2>&1 || true
    endscript
}
EOF

# Enable and start service
echo -e "${YELLOW}Enabling and starting service...${NC}"
systemctl daemon-reload
systemctl enable $SERVICE_NAME

# Check if service already exists and stop it
if systemctl is-active --quiet $SERVICE_NAME; then
    echo -e "${YELLOW}Stopping existing service...${NC}"
    systemctl stop $SERVICE_NAME
fi

systemctl start $SERVICE_NAME

# Check service status
echo -e "${YELLOW}Checking service status...${NC}"
sleep 3  # Give service time to start

if systemctl is-active --quiet $SERVICE_NAME; then
    echo -e "${GREEN}✓ SysMon Agent service is running${NC}"
    
    # Show service info
    echo -e "${BLUE}Service Information:${NC}"
    echo -e "  Status: $(systemctl is-active $SERVICE_NAME)"
    echo -e "  PID: $(systemctl show -p MainPID --value $SERVICE_NAME)"
    echo -e "  Memory: $(systemctl show -p MemoryCurrent --value $SERVICE_NAME) bytes"
    
else
    echo -e "${RED}✗ SysMon Agent service failed to start${NC}"
    echo -e "${YELLOW}Checking service logs:${NC}"
    journalctl -u $SERVICE_NAME --no-pager -n 20
    exit 1
fi

# Test the agent
echo -e "${YELLOW}Testing agent functionality...${NC}"
cd $INSTALL_DIR
if python3 sysmon.py --once --upload-metrics; then
    echo -e "${GREEN}✓ Agent test successful${NC}"
else
    echo -e "${YELLOW}⚠ Agent test had issues (check logs)${NC}"
fi

echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Update the API key in: $INSTALL_DIR/config/sysmon.onlab.json"
echo -e "2. Restart the service: systemctl restart $SERVICE_NAME"
echo -e "3. Check logs: journalctl -u $SERVICE_NAME -f"
echo -e "4. View agent status in OnLab monitoring dashboard"

# Show service commands
echo -e "${YELLOW}Service commands:${NC}"
echo -e "  Start:   systemctl start $SERVICE_NAME"
echo -e "  Stop:    systemctl stop $SERVICE_NAME"
echo -e "  Restart: systemctl restart $SERVICE_NAME"
echo -e "  Status:  systemctl status $SERVICE_NAME"
echo -e "  Logs:    journalctl -u $SERVICE_NAME -f"
echo -e "  Config:  $INSTALL_DIR/config/sysmon.onlab.json"

# Show monitoring commands
echo -e "${YELLOW}Monitoring commands:${NC}"
echo -e "  Test once:     cd $INSTALL_DIR && python3 sysmon.py --once"
echo -e "  Test metrics:  cd $INSTALL_DIR && python3 sysmon.py --once --upload-metrics"
echo -e "  Check queue:   ls -la $INSTALL_DIR/queue/"
echo -e "  Check logs:    tail -f $INSTALL_DIR/logs/sysmon.log"

echo -e "${GREEN}Deployment completed successfully!${NC}"
