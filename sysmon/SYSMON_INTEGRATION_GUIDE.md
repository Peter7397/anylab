# SysMon Agent Integration Guide for OnLab

## Overview

The SysMon Agent is a lightweight system monitoring service that collects comprehensive system metrics and sends them to the OnLab backend for monitoring and alerting. This guide covers deployment, configuration, and integration with the existing OnLab monitoring system.

## Features

### Enhanced System Monitoring
- **CPU Monitoring**: Total usage, per-process monitoring, top processes
- **Memory Monitoring**: RAM usage, available memory, pagefile usage
- **Disk Monitoring**: Usage per partition, I/O statistics, performance metrics
- **Network Monitoring**: Interface statistics, errors, drops, throughput
- **System Information**: Uptime, boot time, process count

### Performance Optimizations
- **Process Caching**: Reduces CPU overhead by caching process information
- **Efficient Collection**: Optimized data collection with minimal system impact
- **Smart Filtering**: Only monitors processes above threshold
- **Memory Management**: Automatic cleanup and resource limits

### Reliability Features
- **Offline Queue**: Stores data when network is unavailable
- **Retry Logic**: Automatic retry with exponential backoff
- **Error Handling**: Comprehensive error handling and logging
- **Queue Management**: Automatic cleanup to prevent disk space issues

## Architecture

```
┌─────────────────┐    HTTP/HTTPS    ┌─────────────────┐
│   SysMon Agent  │ ───────────────► │  OnLab Backend │
│   (Client Host) │                  │                 │
└─────────────────┘                  └─────────────────┘
         │                                    │
         │                                    │
         ▼                                    ▼
┌─────────────────┐                  ┌─────────────────┐
│   Local Queue   │                  │  Django Models  │
│   (Offline)     │                  │                 │
└─────────────────┘                  └─────────────────┘
```

## Deployment

### Prerequisites
- Python 3.7 or higher
- Root/sudo access
- Network connectivity to OnLab backend
- 512MB RAM minimum
- 100MB disk space

### Quick Deployment

1. **Clone and Deploy**:
```bash
# On the client system
sudo ./deploy-sysmon-agent.sh
```

2. **Configure API Key**:
```bash
# Edit the configuration file
sudo nano /opt/sysmon-agent/config/sysmon.onlab.json

# Update the API key
"api_key": "YOUR_ONELAB_API_KEY"
```

3. **Restart Service**:
```bash
sudo systemctl restart sysmon-agent
```

### Manual Deployment

1. **Create Installation Directory**:
```bash
sudo mkdir -p /opt/sysmon-agent
sudo mkdir -p /opt/sysmon-agent/{logs,queue,temp,config}
```

2. **Copy Agent Files**:
```bash
sudo cp -r sysmon_project/src/* /opt/sysmon-agent/
sudo cp sysmon_project/requirements.txt /opt/sysmon-agent/
```

3. **Install Dependencies**:
```bash
cd /opt/sysmon-agent
sudo pip3 install -r requirements.txt
```

4. **Create Configuration**:
```bash
# Copy and customize the configuration
sudo cp sysmon_project/config/sysmon.onlab.json /opt/sysmon-agent/config/
```

5. **Create Systemd Service**:
```bash
sudo nano /etc/systemd/system/sysmon-agent.service
# Use the service definition from deploy script
```

6. **Start Service**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable sysmon-agent
sudo systemctl start sysmon-agent
```

## Configuration

### Main Configuration File
Location: `/opt/sysmon-agent/config/sysmon.onlab.json`

```json
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
    "ram": {
      "warn_pct": 75,
      "crit_pct": 90,
      "avail_warn_mb": 1024,
      "avail_crit_mb": 500
    }
  },
  "alert_server": {
    "base_url": "http://your-onlab-server:8000/api/monitoring/sysmon",
    "api_key": "YOUR_API_KEY",
    "connect_timeout_sec": 5,
    "read_timeout_sec": 20,
    "retry_attempts": 3,
    "retry_delay_sec": 5
  }
}
```

### Key Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `monitor_interval_sec` | Collection interval in seconds | 60 |
| `upload_metrics` | Enable metrics upload to backend | true |
| `dedup_suppress_sec` | Alert deduplication window | 1800 |
| `max_queue_size` | Maximum queue files before cleanup | 1000 |

### Threshold Configuration

Configure alert thresholds for different metrics:

```json
"thresholds": {
  "cpu_total": {
    "warn_pct": 70,
    "crit_pct": 90
  },
  "ram": {
    "warn_pct": 75,
    "crit_pct": 90,
    "avail_warn_mb": 1024,
    "avail_crit_mb": 500
  },
  "disk_free": [
    {
      "drive": "C:",
      "warn_pct": 20,
      "crit_pct": 10
    }
  ]
}
```

## Backend Integration

### API Endpoints

The SysMon agent communicates with these OnLab backend endpoints:

- **Metrics**: `POST /api/monitoring/sysmon/metrics/`
- **Alerts**: `POST /api/monitoring/sysmon/alerts/`
- **Uploads**: `POST /api/monitoring/sysmon/uploads/`

### Data Models

The backend stores SysMon data in these Django models:

- **System**: Basic system information
- **SystemMetrics**: Performance metrics
- **Alert**: System alerts and notifications
- **LogEntry**: System and application logs

### Metrics Data Structure

```json
{
  "host": "client-hostname",
  "service": "SysMonSvc",
  "timestamp_utc": "2024-01-01T12:00:00Z",
  "metrics": {
    "cpu": {
      "cpu_total_pct": 25.5,
      "top_procs": [...],
      "process_count": 150,
      "high_cpu_count": 5
    },
    "mem": {
      "ram_total_mb": 16384,
      "ram_used_pct": 65.2,
      "ram_available_mb": 5700
    },
    "disk": {
      "disks": [...],
      "io": {...},
      "total_disks": 3
    },
    "net": {
      "nics": ["eth0", "lo"],
      "stats": {...},
      "active_nics": 1
    },
    "system": {
      "uptime_seconds": 86400,
      "uptime_hours": 24.0
    }
  }
}
```

## Monitoring and Troubleshooting

### Service Management

```bash
# Check service status
sudo systemctl status sysmon-agent

# View logs
sudo journalctl -u sysmon-agent -f

# Restart service
sudo systemctl restart sysmon-agent

# Test agent manually
cd /opt/sysmon-agent
sudo python3 sysmon.py --once --upload-metrics
```

### Log Files

- **Systemd logs**: `journalctl -u sysmon-agent`
- **Agent logs**: `/opt/sysmon-agent/logs/sysmon.log`
- **Queue files**: `/opt/sysmon-agent/queue/`

### Common Issues

1. **Service won't start**:
   - Check Python version (requires 3.7+)
   - Verify dependencies are installed
   - Check configuration file syntax

2. **Metrics not uploading**:
   - Verify API key is correct
   - Check network connectivity
   - Review backend logs for errors

3. **High CPU usage**:
   - Adjust `monitor_interval_sec`
   - Enable process filtering
   - Reduce `max_processes_to_monitor`

4. **Queue growing large**:
   - Check backend availability
   - Verify API endpoints
   - Review network connectivity

### Performance Tuning

1. **Reduce Collection Frequency**:
```json
"monitor_interval_sec": 120
```

2. **Limit Process Monitoring**:
```json
"performance": {
  "max_processes_to_monitor": 50,
  "min_cpu_threshold_pct": 1.0
}
```

3. **Enable Process Filtering**:
```json
"performance": {
  "enable_process_filtering": true
}
```

## Security Considerations

### Network Security
- Use HTTPS for backend communication
- Implement proper API key management
- Consider network segmentation

### System Security
- Run service with minimal privileges
- Enable systemd security features
- Regular security updates

### Data Privacy
- Review collected metrics for sensitive data
- Implement data retention policies
- Consider data encryption

## Integration with OnLab Frontend

### Dashboard Integration
The SysMon data appears in the OnLab monitoring dashboard:

1. **System Overview**: Shows all monitored systems
2. **Metrics History**: Displays historical performance data
3. **Alert Management**: Manages system alerts
4. **Agent Status**: Shows agent health and connectivity

### API Access
Frontend components can access SysMon data via:

```javascript
// Get system list
GET /api/monitoring/sysmon/agents/

// Get system metrics
GET /api/monitoring/sysmon/agents/{hostname}/metrics/

// Get system details
GET /api/monitoring/sysmon/agents/{hostname}/
```

## Scaling Considerations

### Multiple Agents
- Each agent runs independently
- Backend handles multiple concurrent connections
- Consider load balancing for large deployments

### Performance Impact
- Agent uses ~50MB RAM
- Minimal CPU impact (<1% typically)
- Network usage: ~1KB per minute per agent

### Database Considerations
- Monitor database growth
- Implement data retention policies
- Consider partitioning for large deployments

## Support and Maintenance

### Regular Maintenance
- Monitor log file sizes
- Review queue directory
- Update agent versions
- Check system resources

### Backup and Recovery
- Backup configuration files
- Document custom thresholds
- Test recovery procedures

### Updates
- Test new versions in staging
- Plan maintenance windows
- Coordinate with backend updates

## Conclusion

The SysMon Agent provides comprehensive system monitoring with minimal resource impact and maximum reliability. Proper deployment and configuration ensure seamless integration with the OnLab monitoring system.

For additional support, refer to the OnLab documentation or contact the development team.
