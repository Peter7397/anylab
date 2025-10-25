# 🖥️ VMware Windows 11 Deployment Guide

## 📋 Prerequisites for VMware Windows 11

### VMware Machine Requirements:
- **Windows 11** (any edition)
- **Python 3.7+** installed
- **Administrator access**
- **Network connectivity** to your OnLab server
- **VMware Tools** installed (recommended)

### OnLab Server Requirements:
- **OnLab server running** and accessible
- **API key** generated from admin panel

## 🚀 Step-by-Step Deployment

### Step 1: Transfer Files to VMware Machine

**Option A: Shared Folder (Easiest)**
```powershell
# In VMware, enable shared folders:
# VM → Settings → Options → Shared Folders → Always enabled
# Add a shared folder pointing to your OnLab sysmon directory

# In Windows 11, access via:
# \\vmware-host\Shared Folders\sysmon\
```

**Option B: USB/Network Transfer**
```powershell
# Copy the package to a USB drive or network share
# Then copy to Windows 11 VM
```

**Option C: Direct Download (if network allows)**
```powershell
# Download directly in Windows 11 if your OnLab server is accessible
Invoke-WebRequest -Uri "http://your-onlab-server/sysmon/onlab-sysmon-agent-windows-2.0.0.tar.gz" -OutFile "sysmon-package.tar.gz"
```

### Step 2: Install Python (if not already installed)

```powershell
# Check if Python is installed
python --version

# If not installed, download from:
# https://python.org/downloads/
# Make sure to check "Add Python to PATH" during installation
```

### Step 3: Extract and Deploy

```powershell
# Extract the package
# If you have tar installed:
tar -xzf onlab-sysmon-agent-windows-2.0.0.tar.gz

# Or use 7-Zip/WinRAR to extract the tar.gz file

# Navigate to extracted folder
cd onlab-sysmon-agent-windows-2.0.0

# Edit the deployment script
notepad deploy-windows.ps1
```

### Step 4: Configure the Deployment Script

**Edit `deploy-windows.ps1` and update these lines:**
```powershell
param(
    [string]$OnLabServer = "http://YOUR_ONELAB_SERVER_IP:8000",  # Update this
    [string]$ApiKey = "YOUR_API_KEY_HERE",                       # Update this
    [string]$ClientName = $env:COMPUTERNAME,                     # Auto-detected
    [string]$InstallDir = "C:\Program Files\OnLab\SysMon",      # Default
    [string]$ServiceName = "SysMonAgent"                         # Default
)
```

**Get your OnLab server IP:**
```bash
# On your OnLab server (macOS/Linux)
ifconfig | grep "inet " | grep -v 127.0.0.1
# Or
ip addr show | grep "inet " | grep -v 127.0.0.1
```

**Get API key from OnLab:**
1. Open browser in Windows 11 VM
2. Go to: `http://YOUR_ONELAB_SERVER_IP:8000/admin`
3. Login with admin credentials
4. Go to Users → API Keys → Create new key
5. Copy the API key

### Step 5: Deploy the Agent

```powershell
# Run PowerShell as Administrator
# Right-click PowerShell and select "Run as administrator"

# Navigate to the extracted folder
cd "path\to\onlab-sysmon-agent-windows-2.0.0"

# Run the deployment script
.\deploy-windows.ps1
```

### Step 6: Verify Installation

```powershell
# Check service status
Get-Service SysMonAgent

# Should show: Running

# Check logs
Get-Content "C:\Program Files\OnLab\SysMon\logs\sysmon.log" -Tail 20

# Should show connection messages

# Check OnLab dashboard
# Open browser and go to: http://YOUR_ONELAB_SERVER_IP:3000
# Look for your Windows 11 VM in the monitoring dashboard
```

## 🔧 VMware-Specific Configuration

### Network Configuration
```powershell
# Ensure VM can reach OnLab server
# Test connectivity:
Invoke-WebRequest -Uri "http://YOUR_ONELAB_SERVER_IP:8000/api/" -TimeoutSec 10

# If using NAT, make sure OnLab server is accessible
# If using Bridged, ensure both are on same network
```

### VMware Tools Integration
```powershell
# Install VMware Tools for better performance
# VM → Guest → Install/Upgrade VMware Tools

# This provides better network and disk performance
```

### Resource Allocation
```powershell
# Recommended VM settings for SysMon:
# - CPU: 2 cores minimum
# - RAM: 4GB minimum
# - Disk: 20GB minimum
# - Network: NAT or Bridged
```

## 🧪 Testing and Development

### Test Different Scenarios
```powershell
# Test high CPU usage
# Run CPU-intensive tasks and check monitoring

# Test high memory usage
# Allocate large amounts of memory

# Test network connectivity
# Disconnect/reconnect network and check reconnection

# Test service restart
Restart-Service SysMonAgent
```

### Development Testing
```powershell
# For development, you can run manually:
cd "C:\Program Files\OnLab\SysMon"
python sysmon.py

# This runs in foreground for debugging
```

### Log Analysis
```powershell
# View real-time logs
Get-Content "C:\Program Files\OnLab\SysMon\logs\sysmon.log" -Wait

# Check Windows Event Logs
Get-WinEvent -LogName Application | Where-Object {$_.Message -like "*SysMon*"}
```

## 🛠️ Troubleshooting VMware Issues

### Common VMware Issues

**1. Network Connectivity**
```powershell
# Check VM network settings
# VM → Settings → Network Adapter
# Try different network modes: NAT, Bridged, Host-only

# Test connectivity
ping YOUR_ONELAB_SERVER_IP
```

**2. Shared Folder Access**
```powershell
# If shared folders not working:
# VM → Settings → Options → Shared Folders
# Enable and add folder

# Alternative: Use USB or network transfer
```

**3. Performance Issues**
```powershell
# Install VMware Tools
# Allocate more resources to VM
# Check if antivirus is interfering
```

**4. Service Won't Start**
```powershell
# Check Windows Event Logs
Get-WinEvent -LogName Application | Where-Object {$_.Message -like "*SysMon*"}

# Check service configuration
sc qc SysMonAgent

# Try manual installation
cd "C:\Program Files\OnLab\SysMon"
python sysmon.py
```

## 📊 Monitoring Verification

### Check OnLab Dashboard
1. Open browser in Windows 11 VM
2. Go to: `http://YOUR_ONELAB_SERVER_IP:3000`
3. Login to OnLab
4. Navigate to Monitoring → System Monitoring
5. Look for your Windows 11 VM in the list
6. Check that metrics are being collected

### Verify Metrics Collection
```powershell
# Check what's being monitored
Get-Process | Sort-Object CPU -Descending | Select-Object -First 5

# Check disk usage
Get-WmiObject -Class Win32_LogicalDisk | Select-Object DeviceID, @{Name="FreeGB";Expression={[math]::Round($_.FreeSpace/1GB,2)}}, @{Name="TotalGB";Expression={[math]::Round($_.Size/1GB,2)}}

# Check memory usage
Get-WmiObject -Class Win32_OperatingSystem | Select-Object @{Name="FreeGB";Expression={[math]::Round($_.FreePhysicalMemory/1MB,2)}}, @{Name="TotalGB";Expression={[math]::Round($_.TotalVisibleMemorySize/1MB,2)}}
```

## 🎯 Success Checklist

- ✅ Python 3.7+ installed and in PATH
- ✅ SysMonAgent service is running
- ✅ Logs show "Connected to OnLab server"
- ✅ Windows 11 VM appears in OnLab dashboard
- ✅ CPU, memory, and disk metrics are being collected
- ✅ No errors in Windows Event Logs
- ✅ Network connectivity to OnLab server is stable

## 🔄 Next Steps

Once deployed successfully:
1. **Test different scenarios** (high CPU, memory, network issues)
2. **Monitor performance impact** on the VM
3. **Verify data accuracy** in OnLab dashboard
4. **Test service restart** and recovery
5. **Document any issues** for production deployment
