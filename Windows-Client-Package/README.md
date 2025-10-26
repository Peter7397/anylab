# 🖥️ AnyLab SysMon Agent - Windows Client Package

## 📦 Package Contents

This package contains everything you need to deploy the AnyLab System Monitor agent to your Windows target machine.

### 📁 Files Included

```
Windows-Client-Package/
├── 📄 README.md                    # This file - Installation guide
├── 🐍 sysmon.py                    # Main SysMon agent script
├── 📋 requirements.txt             # Python dependencies
├── ⚙️ config/
│   ├── global.default.json         # Default configuration
│   └── sysmon.anylab.json          # AnyLab server configuration
├── 🚀 deploy-windows.ps1           # PowerShell deployment script (Recommended)
├── 🚀 deploy-windows.bat           # Batch deployment script
├── 🖥️ vmware-setup.ps1            # VMware-specific setup script
├── 📖 VMWARE_QUICK_START.md        # Quick start guide for VMware
└── 📖 VMWARE_DEPLOYMENT_GUIDE.md   # Detailed VMware deployment guide
```

## 🚀 Quick Installation (VMware Windows 11)

### Method 1: VMware Quick Setup (Recommended)

**Step 1: Edit Configuration**
```powershell
# Open config/sysmon.anylab.json and update:
{
  "server_url": "http://10.96.17.21:8000",
  "api_key": "YOUR_API_KEY_HERE",
  "client_name": "YOUR-VM-NAME"
}
```

**Step 2: Run VMware Setup**
```powershell
# Right-click vmware-setup.ps1 → "Run as administrator"
# Or run in PowerShell as Administrator:
.\vmware-setup.ps1
```

### Method 2: PowerShell Deployment

**Step 1: Run PowerShell as Administrator**
```powershell
# Navigate to this directory
cd "path\to\Windows-Client-Package"

# Run deployment script
.\deploy-windows.ps1
```

### Method 3: Batch Script Deployment

**Step 1: Run Command Prompt as Administrator**
```cmd
# Navigate to this directory
cd "path\to\Windows-Client-Package"

# Run deployment script
deploy-windows.bat
```

## ⚙️ Configuration

### Required Settings

**Edit `config/sysmon.anylab.json`:**
```json
{
  "server_url": "http://10.96.17.21:8000",
  "api_key": "YOUR_API_KEY_HERE",
  "client_name": "WINDOWS-PC-NAME",
  "monitor_interval_sec": 60,
  "upload_metrics": true,
  "enable_detailed_logging": false
}
```

### Get API Key

1. **Go to AnyLab Admin Panel:** `http://10.96.17.21:8000/admin`
2. **Login:** `admin` / `admin123`
3. **Navigate:** Users → API Keys → Create new key
4. **Copy the API key** and paste it in the configuration

## 🧪 Verification

### Check Service Status
```powershell
# Check if service is running
sc query SysMonAgent

# Check service details
sc qc SysMonAgent
```

### View Logs
```powershell
# View recent logs
Get-Content "C:\Program Files\AnyLab\SysMon\logs\sysmon.log" -Tail 20

# Monitor logs in real-time
Get-Content "C:\Program Files\AnyLab\SysMon\logs\sysmon.log" -Wait
```

### Test Network Connectivity
```powershell
# Test connection to AnyLab server
Invoke-WebRequest -Uri "http://10.96.17.21:8000/api/" -Method GET

# Test API endpoint
Invoke-WebRequest -Uri "http://10.96.17.21:8000/api/monitoring/" -Method GET
```

### Check AnyLab Dashboard
- **Open:** `http://10.96.17.21:3000`
- **Login:** `admin` / `admin123`
- **Navigate:** Monitoring → System Monitoring
- **Look for:** Your Windows machine in the systems list

## 🔧 Service Management

### Start/Stop Service
```powershell
# Start service
net start SysMonAgent

# Stop service
net stop SysMonAgent

# Restart service
net stop SysMonAgent && net start SysMonAgent
```

### Service Configuration
```powershell
# View service configuration
sc qc SysMonAgent

# Change startup type (Auto/Manual/Disabled)
sc config SysMonAgent start= auto

# Change service description
sc description SysMonAgent "AnyLab System Monitoring Agent"
```

## 🐛 Troubleshooting

### Common Issues

**1. Service Won't Start**
```powershell
# Check Windows Event Logs
Get-WinEvent -LogName Application | Where-Object {$_.Message -like "*SysMon*"}

# Check service dependencies
sc qc SysMonAgent

# Test Python script manually
python sysmon.py
```

**2. Network Connection Issues**
```powershell
# Test basic connectivity
ping 10.96.17.21

# Test HTTP connectivity
Invoke-WebRequest -Uri "http://10.96.17.21:8000/" -Method GET

# Check firewall settings
Get-NetFirewallRule | Where-Object {$_.DisplayName -like "*Python*"}
```

**3. Permission Issues**
```powershell
# Check if running as Administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo "Run as Administrator"
)

# Check file permissions
Get-Acl "C:\Program Files\AnyLab\SysMon\"
```

**4. Python Issues**
```powershell
# Check Python installation
python --version

# Install required packages
pip install -r requirements.txt

# Test imports
python -c "import psutil, requests, jsonschema; print('All modules OK')"
```

### Debug Mode

**Enable Detailed Logging:**
```json
{
  "enable_detailed_logging": true,
  "log_level": "DEBUG"
}
```

**Run Manually for Debugging:**
```powershell
# Run agent manually to see output
python sysmon.py

# Run with verbose output
python -u sysmon.py
```

## 📊 Performance Monitoring

### Resource Usage
- **CPU:** < 1% (typically 0.1-0.5%)
- **Memory:** ~50 MB
- **Disk:** Minimal (logs only)
- **Network:** ~1KB per minute

### Monitoring Intervals
- **Default:** 60 seconds
- **Configurable:** 30-300 seconds
- **Real-time:** Available via AnyLab dashboard

## 🔄 Updates

### Update Agent
```powershell
# Stop service
net stop SysMonAgent

# Backup current installation
Copy-Item "C:\Program Files\AnyLab\SysMon" "C:\Program Files\AnyLab\SysMon.backup" -Recurse

# Copy new files
Copy-Item "sysmon.py" "C:\Program Files\AnyLab\SysMon\"

# Start service
net start SysMonAgent
```

### Update Configuration
```powershell
# Edit configuration
notepad "C:\Program Files\AnyLab\SysMon\config\sysmon.anylab.json"

# Restart service to apply changes
net stop SysMonAgent && net start SysMonAgent
```

## 🛡️ Security

### Firewall Configuration
```powershell
# Allow outbound connections to AnyLab server
New-NetFirewallRule -DisplayName "AnyLab SysMon Agent" -Direction Outbound -Protocol TCP -RemoteAddress 10.96.17.21 -RemotePort 8000 -Action Allow
```

### Antivirus Exclusions
```powershell
# Add exclusions for SysMon agent
# Common paths to exclude:
# - C:\Program Files\AnyLab\SysMon\
# - C:\Program Files\AnyLab\SysMon\logs\
# - C:\Program Files\AnyLab\SysMon\queue\
```

## 📞 Support

### Log Locations
- **Service Logs:** `C:\Program Files\AnyLab\SysMon\logs\sysmon.log`
- **Windows Event Logs:** Application → SysMonAgent
- **Python Errors:** Console output when running manually

### Useful Commands
```powershell
# Quick status check
sc query SysMonAgent

# View recent logs
Get-Content "C:\Program Files\AnyLab\SysMon\logs\sysmon.log" -Tail 10

# Test connectivity
Invoke-WebRequest -Uri "http://10.96.17.21:8000/api/" -Method GET

# Check configuration
Get-Content "C:\Program Files\AnyLab\SysMon\config\sysmon.anylab.json"
```

### AnyLab Dashboard
- **URL:** `http://10.96.17.21:3000`
- **Login:** `admin` / `admin123`
- **Monitoring:** System Monitoring → Your Windows Machine

## 🎯 Success Checklist

- ✅ Service installed and running (`sc query SysMonAgent`)
- ✅ Configuration updated with correct server URL and API key
- ✅ Network connectivity to AnyLab server (10.96.17.21:8000)
- ✅ Logs showing successful data upload
- ✅ Machine appears in AnyLab dashboard
- ✅ Metrics being collected (CPU, Memory, Disk, Network)
- ✅ No errors in Windows Event Logs

## 🔄 Next Steps

1. **Test on your VMware Windows 11 machine**
2. **Verify all metrics are collected**
3. **Test different scenarios** (high CPU, memory, network issues)
4. **Deploy to production machines**
5. **Set up monitoring alerts** in AnyLab dashboard
