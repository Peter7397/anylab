# 🚀 Quick Start - VMware Windows 11 Deployment

## ⚡ Your OnLab Server Information

**Server IP:** `10.96.17.21`  
**Backend API:** `http://10.96.17.21:8000`  
**Frontend Dashboard:** `http://10.96.17.21:3000`  
**Admin Panel:** `http://10.96.17.21:8000/admin`

## 📋 Prerequisites Checklist

- ✅ Windows 11 VM running in VMware
- ✅ Python 3.7+ installed (https://python.org)
- ✅ Administrator access to Windows 11 VM
- ✅ Network connectivity between VM and OnLab server
- ✅ VMware Tools installed (recommended)

## 🚀 Quick Deployment Steps

### Step 1: Transfer Files to VMware

**Option A: Shared Folder (Recommended)**
```powershell
# In VMware: VM → Settings → Options → Shared Folders
# Add shared folder pointing to your OnLab sysmon directory
# In Windows 11: \\vmware-host\Shared Folders\sysmon\
```

**Option B: Direct Download**
```powershell
# In Windows 11 PowerShell:
Invoke-WebRequest -Uri "http://10.96.17.21:8000/sysmon/onlab-sysmon-agent-windows-2.0.0.tar.gz" -OutFile "sysmon-package.tar.gz"
```

### Step 2: Extract and Setup

```powershell
# Extract the package
# Use 7-Zip or tar if available
tar -xzf onlab-sysmon-agent-windows-2.0.0.tar.gz

# Navigate to extracted folder
cd onlab-sysmon-agent-windows-2.0.0

# Use the VMware-specific setup script
# (This script is pre-configured with your server IP)
.\vmware-setup.ps1
```

### Step 3: Get API Key

```powershell
# Open browser in Windows 11 VM
# Go to: http://10.96.17.21:8000/admin
# Login with: admin / admin123
# Navigate to: Users → API Keys → Create new key
# Copy the API key
```

### Step 4: Update Configuration

```powershell
# Edit the configuration file
notepad "C:\Program Files\OnLab\SysMon\config\sysmon.onlab.json"

# Update the "api_key" field with your actual API key
```

### Step 5: Verify Installation

```powershell
# Check service status
Get-Service SysMonAgent

# Should show: Running

# View logs
Get-Content "C:\Program Files\OnLab\SysMon\logs\sysmon.log" -Tail 20

# Check OnLab dashboard
# Open browser: http://10.96.17.21:3000
# Look for your Windows 11 VM in the monitoring dashboard
```

## 🔧 Quick Commands

```powershell
# Service management
Start-Service SysMonAgent
Stop-Service SysMonAgent
Restart-Service SysMonAgent
Get-Service SysMonAgent

# Logs
Get-Content "C:\Program Files\OnLab\SysMon\logs\sysmon.log" -Tail 50 -Wait

# Manual run (for debugging)
cd "C:\Program Files\OnLab\SysMon"
python sysmon.py
```

## 🧪 Testing Scenarios

### Test High CPU Usage
```powershell
# Run CPU-intensive task
while($true) { $i = 1..1000000 | ForEach-Object { $_ * $_ } }
```

### Test High Memory Usage
```powershell
# Allocate large array
$largeArray = 1..10000000
```

### Test Network Connectivity
```powershell
# Test connection to OnLab server
Invoke-WebRequest -Uri "http://10.96.17.21:8000/api/" -TimeoutSec 10
```

## 🛠️ Troubleshooting

### Service Won't Start
```powershell
# Check Windows Event Logs
Get-WinEvent -LogName Application | Where-Object {$_.Message -like "*SysMon*"} | Select-Object -First 5

# Check service configuration
sc qc SysMonAgent
```

### Can't Connect to Server
```powershell
# Test network connectivity
ping 10.96.17.21

# Check if OnLab server is running
Invoke-WebRequest -Uri "http://10.96.17.21:8000/api/"
```

### Python Not Found
```powershell
# Check Python installation
python --version

# If not found, install from https://python.org
# Make sure to check "Add Python to PATH"
```

## 📊 What Gets Monitored

- ✅ CPU usage (total & per-process)
- ✅ Memory usage (RAM & pagefile)
- ✅ Disk space & I/O (all drives)
- ✅ Network statistics
- ✅ System uptime
- ✅ Process count
- ✅ Windows services status
- ✅ Custom alerts

## 🎯 Success Indicators

- ✅ SysMonAgent service shows "Running"
- ✅ Logs show "Connected to OnLab server"
- ✅ Windows 11 VM appears in OnLab dashboard
- ✅ CPU, memory, and disk metrics are being collected
- ✅ No errors in Windows Event Logs

## 🔄 Next Steps

Once deployed successfully:
1. **Test different scenarios** (high CPU, memory, network issues)
2. **Monitor performance impact** on the VM
3. **Verify data accuracy** in OnLab dashboard
4. **Test service restart** and recovery
5. **Document any issues** for production deployment

## 📞 Quick Help

**If you encounter issues:**
1. Check the logs: `Get-Content "C:\Program Files\OnLab\SysMon\logs\sysmon.log" -Tail 50`
2. Verify network connectivity: `ping 10.96.17.21`
3. Check OnLab server status: `http://10.96.17.21:3000`
4. Review Windows Event Logs for errors
