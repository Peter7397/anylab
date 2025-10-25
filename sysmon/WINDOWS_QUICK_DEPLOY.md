# 🚀 Quick Deploy - SysMon Agent for Windows

## ⚡ Easiest Method (3 Steps)

### Step 1: Get API Key from OnLab
```powershell
# Log into OnLab admin panel
http://your-onlab-server:8000/admin

# Go to Users → API Keys → Create new key
# Copy the API key
```

### Step 2: Deploy to Windows PC
```powershell
# Extract the Windows package
Expand-Archive -Path "onlab-sysmon-agent-windows-2.0.0.zip" -DestinationPath .

# Navigate to extracted folder
cd onlab-sysmon-agent-windows-2.0.0

# Edit configuration (update server IP and API key)
notepad deploy-windows.ps1

# Run as Administrator
# Right-click PowerShell and select "Run as administrator"
.\deploy-windows.ps1
```

### Step 3: Verify Installation
```powershell
# Check service status
Get-Service SysMonAgent

# View logs
Get-Content "C:\Program Files\OnLab\SysMon\logs\sysmon.log" -Tail 20

# Check OnLab dashboard
http://your-onlab-server:3000
```

## 🔧 Configuration

**Required changes in `deploy-windows.ps1`:**
```powershell
$OnLabServer = "http://YOUR_SERVER_IP:8000"  # Your OnLab server
$ApiKey = "YOUR_API_KEY_HERE"                # From admin panel
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

## 🛠️ Troubleshooting

**Service not starting:**
```powershell
# Check Windows Event Logs
Get-WinEvent -LogName Application | Where-Object {$_.Message -like "*SysMon*"} | Select-Object -First 5

# Check service configuration
sc qc SysMonAgent
```

**Python not found:**
```cmd
python --version
# If not found, install Python 3.7+ from python.org with "Add to PATH" checked
```

**Can't connect to server:**
```powershell
Invoke-WebRequest -Uri "http://your-onlab-server:8000/api/"
```

**Permission issues:**
```cmd
# Run as Administrator
# Check file permissions
icacls "C:\Program Files\OnLab\SysMon" /grant "NT AUTHORITY\SYSTEM:(OI)(CI)F"
```

## 📞 Quick Commands

```powershell
# Service management
Start-Service SysMonAgent
Stop-Service SysMonAgent
Restart-Service SysMonAgent
Get-Service SysMonAgent

# Logs
Get-Content "C:\Program Files\OnLab\SysMon\logs\sysmon.log" -Tail 50

# Manual run
python "C:\Program Files\OnLab\SysMon\sysmon.py"
```

## 🎯 Success Indicators

- ✅ Service shows "Running" in Services Manager
- ✅ Logs show "Connected to OnLab server"
- ✅ Client appears in OnLab dashboard
- ✅ Metrics are being collected
- ✅ No errors in Windows Event Logs

## 🔄 Alternative Methods

**Batch File Deployment:**
```cmd
# Right-click deploy-windows.bat and "Run as administrator"
deploy-windows.bat
```

**Manual Installation:**
```cmd
# Install Python first, then follow manual steps in WINDOWS_DEPLOYMENT_GUIDE.md
```

## 🏢 Enterprise Options

- **Group Policy**: Deploy via GPO startup scripts
- **SCCM**: Package and deploy via System Center
- **PowerShell Remoting**: Deploy to multiple PCs remotely
