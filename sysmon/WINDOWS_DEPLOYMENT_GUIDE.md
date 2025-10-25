# OnLab SysMon Agent - Windows Deployment Guide

## 🚀 Quick Deployment Methods for Windows

### Method 1: PowerShell Script (Recommended)

**Step 1: Create Windows package**
```powershell
# On your OnLab server (if you have PowerShell)
cd sysmon
.\create-windows-package.ps1
```

**Step 2: Transfer to Windows client**
```powershell
# Copy the zip file to your Windows PC
# You can use USB drive, network share, or email
```

**Step 3: Deploy on Windows client**
```powershell
# Extract the package
Expand-Archive -Path "onlab-sysmon-agent-windows-2.0.0.zip" -DestinationPath .

# Navigate to extracted folder
cd onlab-sysmon-agent-windows-2.0.0

# Edit configuration (update server IP and API key)
notepad deploy-windows.ps1

# Run as Administrator
# Right-click PowerShell and select "Run as administrator"
.\deploy-windows.ps1
```

### Method 2: Batch File (Alternative)

**For clients that prefer batch files:**
```cmd
# Extract and navigate to package
cd onlab-sysmon-agent-windows-2.0.0

# Edit configuration
notepad deploy-windows.bat

# Run as Administrator
# Right-click deploy-windows.bat and select "Run as administrator"
deploy-windows.bat
```

### Method 3: Manual Installation

**Step 1: Install Python**
1. Download Python 3.7+ from https://python.org
2. Install with "Add Python to PATH" checked
3. Verify installation: `python --version`

**Step 2: Create directories**
```cmd
mkdir "C:\Program Files\OnLab\SysMon"
mkdir "C:\Program Files\OnLab\SysMon\logs"
mkdir "C:\Program Files\OnLab\SysMon\queue"
mkdir "C:\Program Files\OnLab\SysMon\temp"
mkdir "C:\Program Files\OnLab\SysMon\config"
```

**Step 3: Copy files**
```cmd
xcopy sysmon_project\src\* "C:\Program Files\OnLab\SysMon\" /E /Y
copy sysmon_project\requirements.txt "C:\Program Files\OnLab\SysMon\"
```

**Step 4: Install dependencies**
```cmd
cd "C:\Program Files\OnLab\SysMon"
pip install -r requirements.txt
```

**Step 5: Create configuration**
```cmd
notepad "C:\Program Files\OnLab\SysMon\config\sysmon.onlab.json"
```

**Step 6: Create and start service**
```cmd
# Download NSSM manually or use the script
# Install service using NSSM
C:\nssm\win64\nssm.exe install SysMonAgent "python" "C:\Program Files\OnLab\SysMon\sysmon.py"
C:\nssm\win64\nssm.exe set SysMonAgent AppDirectory "C:\Program Files\OnLab\SysMon"
net start SysMonAgent
```

## ⚙️ Configuration

### Required Settings

Edit the configuration file: `C:\Program Files\OnLab\SysMon\config\sysmon.onlab.json`

```json
{
  "server_url": "http://YOUR_ONELAB_SERVER:8000",
  "api_key": "YOUR_API_KEY_FROM_ONELAB_ADMIN",
  "client_name": "WINDOWS-PC-NAME",
  "monitor_interval_sec": 60,
  "upload_metrics": true
}
```

### Get API Key from OnLab

1. Log into OnLab admin panel: `http://your-server:8000/admin`
2. Go to **Users** → **API Keys** (or create one)
3. Copy the API key to your Windows configuration

## 🔧 Service Management

### PowerShell Commands
```powershell
# Check status
Get-Service SysMonAgent

# Start service
Start-Service SysMonAgent

# Stop service
Stop-Service SysMonAgent

# Restart service
Restart-Service SysMonAgent

# View logs
Get-Content "C:\Program Files\OnLab\SysMon\logs\sysmon.log" -Tail 50
```

### Command Prompt Commands
```cmd
# Check status
sc query SysMonAgent

# Start service
net start SysMonAgent

# Stop service
net stop SysMonAgent

# View logs
type "C:\Program Files\OnLab\SysMon\logs\sysmon.log"
```

### Windows Services Manager
1. Press `Win + R`, type `services.msc`
2. Find "SysMonAgent" service
3. Right-click for options (Start, Stop, Restart, Properties)

## 📊 Monitoring Features

The SysMon agent collects on Windows:

- **CPU Usage**: Total and per-process monitoring
- **Memory Usage**: RAM usage, available memory, pagefile
- **Disk Usage**: Space usage per drive, I/O statistics
- **Network**: Interface statistics, throughput
- **System Info**: Uptime, process count, boot time
- **Windows-Specific**: Event logs, services status

## 🔍 Troubleshooting

### Common Issues

**1. Service won't start**
```powershell
# Check Windows Event Logs
Get-WinEvent -LogName Application | Where-Object {$_.Message -like "*SysMon*"} | Select-Object -First 10

# Check service configuration
sc qc SysMonAgent
```

**2. Python not found**
```cmd
# Check Python installation
python --version

# If not found, reinstall Python with "Add to PATH" checked
# Or add Python manually to PATH environment variable
```

**3. Permission denied**
```cmd
# Run as Administrator
# Check file permissions
icacls "C:\Program Files\OnLab\SysMon" /grant "NT AUTHORITY\SYSTEM:(OI)(CI)F"
```

**4. Can't connect to OnLab server**
```powershell
# Test connectivity
Invoke-WebRequest -Uri "http://your-onlab-server:8000/api/"

# Check Windows Firewall
Get-NetFirewallRule | Where-Object {$_.DisplayName -like "*Python*"}
```

### Log Locations
- **Windows Event Logs**: Event Viewer → Windows Logs → Application
- **Agent logs**: `C:\Program Files\OnLab\SysMon\logs\`
- **Service logs**: `C:\Program Files\OnLab\SysMon\logs\sysmon.log`

## 🛡️ Security Considerations

1. **API Key Security**: Store API keys securely, don't commit to version control
2. **Network Security**: Use HTTPS for OnLab server communication
3. **Windows Firewall**: Ensure Python can make outbound connections
4. **Permissions**: Run as Local System for system metrics access
5. **Antivirus**: Add exclusions for the SysMon directory if needed

## 📈 Performance Impact

- **CPU**: < 1% average usage
- **Memory**: ~50MB RAM
- **Disk**: < 100MB total
- **Network**: ~1KB per minute

## 🔄 Updates

To update the agent:

```powershell
# Stop service
Stop-Service SysMonAgent

# Backup configuration
Copy-Item "C:\Program Files\OnLab\SysMon\config\sysmon.onlab.json" "$env:TEMP\"

# Update files
# Copy new files to installation directory

# Restore configuration
Copy-Item "$env:TEMP\sysmon.onlab.json" "C:\Program Files\OnLab\SysMon\config\"

# Restart service
Start-Service SysMonAgent
```

## 🏢 Enterprise Deployment

### Group Policy Deployment
1. Create a Group Policy Object
2. Add the deployment script to Computer Configuration → Windows Settings → Scripts
3. Configure startup script to run the deployment

### SCCM Deployment
1. Create an Application in SCCM
2. Package the SysMon agent files
3. Deploy as a required application

### PowerShell Remoting
```powershell
# Deploy to multiple computers
$computers = @("PC1", "PC2", "PC3")
foreach ($computer in $computers) {
    Invoke-Command -ComputerName $computer -ScriptBlock {
        # Deployment commands here
    }
}
```

## 📞 Support

For issues or questions:
1. Check Windows Event Logs
2. Verify configuration syntax
3. Test network connectivity
4. Check OnLab server status
5. Review agent logs in `C:\Program Files\OnLab\SysMon\logs\`

## 🎯 Success Indicators

- ✅ Service shows "Running" in Services Manager
- ✅ Logs show "Connected to OnLab server"
- ✅ Client appears in OnLab dashboard
- ✅ Metrics are being collected
- ✅ No errors in Windows Event Logs
