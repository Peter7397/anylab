# 🚀 Quick Start - Windows Executable Build

## ⚡ Fastest Build Method

### Step 1: Setup VS Code
```bash
# Open VS Code in sysmon directory
code .

# Install PyInstaller (if not already installed)
# Press Ctrl+Shift+P → "Tasks: Run Task" → "Install PyInstaller"
```

### Step 2: Build Executable
```bash
# Press Ctrl+Shift+B (default build task)
# Or Ctrl+Shift+P → "Tasks: Run Task" → "Build SysMon Windows Executable"
```

### Step 3: Get Your Package
```bash
# After successful build, you'll get:
SysMonAgent-Windows/
├── SysMonAgent.exe          # The executable
├── install-sysmon.bat       # Installer script
├── sysmon.onlab.json        # Configuration
└── README.txt              # Instructions
```

## 🔧 Alternative Build Methods

### PowerShell Script
```powershell
# Run as Administrator
.\build-windows-exe.ps1

# Clean build files only
.\build-windows-exe.ps1 -Clean

# Test the agent
.\build-windows-exe.ps1 -Test
```

### Python Script
```bash
python build-windows-exe.py
```

### Manual PyInstaller
```bash
pip install pyinstaller
pyinstaller --onefile --console --name=SysMonAgent --add-data=config;config --hidden-import=psutil --hidden-import=requests --hidden-import=jsonschema --hidden-import=typing_extensions sysmon.py
```

## 📦 What You Get

### Executable Features
- ✅ **Single file** - No Python required on target machines
- ✅ **Windows service** - Runs automatically on startup
- ✅ **Self-contained** - All dependencies included
- ✅ **Easy deployment** - Just copy and run installer

### Package Contents
- **SysMonAgent.exe** - Main executable (15-25 MB)
- **install-sysmon.bat** - One-click installer
- **sysmon.onlab.json** - Configuration template
- **README.txt** - Installation instructions

## 🚀 Deployment

### Single Machine
```bash
# 1. Copy SysMonAgent-Windows folder to target machine
# 2. Edit sysmon.onlab.json with your server details
# 3. Right-click install-sysmon.bat → "Run as administrator"
```

### Enterprise Deployment
```powershell
# Deploy to multiple machines
$computers = @("PC1", "PC2", "PC3")
foreach ($computer in $computers) {
    Copy-Item "SysMonAgent-Windows" "\\\\$computer\\C$\\temp\\" -Recurse
    Invoke-Command -ComputerName $computer -ScriptBlock {
        cd "C:\temp\SysMonAgent-Windows"
        .\install-sysmon.bat
    }
}
```

## ⚙️ Configuration

### Required Settings
```json
{
  "server_url": "http://10.96.17.21:8000",
  "api_key": "YOUR_API_KEY_HERE",
  "client_name": "WINDOWS-PC-NAME"
}
```

### Get API Key
```bash
# 1. Go to: http://10.96.17.21:8000/admin
# 2. Login: admin / admin123
# 3. Navigate: Users → API Keys → Create new key
# 4. Copy the API key
```

## 🧪 Testing

### Test Executable Locally
```bash
# Run directly
.\dist\SysMonAgent.exe

# Test Python script
python sysmon.py
```

### Test Installation
```bash
# Check service status
sc query SysMonAgent

# View logs
type "C:\Program Files\OnLab\SysMon\logs\sysmon.log"

# Check dashboard
# Open: http://10.96.17.21:3000
```

## 🔍 Troubleshooting

### Build Issues
```bash
# Module not found
--hidden-import=missing_module

# File not found
--add-data=correct/path;destination

# Large executable
--exclude-module=unused_module
```

### Runtime Issues
```bash
# Check Windows Event Logs
Get-WinEvent -LogName Application | Where-Object {$_.Message -like "*SysMon*"}

# Check service configuration
sc qc SysMonAgent

# Test network connectivity
Invoke-WebRequest -Uri "http://10.96.17.21:8000/api/"
```

## 📊 Performance

### Resource Usage
- **Executable size:** 15-25 MB
- **Runtime memory:** ~50 MB
- **CPU impact:** < 1%
- **Startup time:** 2-5 seconds

### Optimization
```bash
# Reduce size with UPX
pyinstaller --onefile --console --upx-dir=path/to/upx sysmon.py

# Hide console window
pyinstaller --onefile --windowed sysmon.py

# Add custom icon
pyinstaller --onefile --console --icon=icon.ico sysmon.py
```

## 🎯 Success Checklist

- ✅ Executable builds without errors
- ✅ Package contains all required files
- ✅ Installer runs successfully
- ✅ Service starts automatically
- ✅ Agent connects to OnLab server
- ✅ Metrics appear in dashboard
- ✅ No antivirus false positives

## 📞 Quick Commands

```bash
# VS Code Tasks
Ctrl+Shift+B                    # Build executable
Ctrl+Shift+P → "Clean Build"    # Clean build files
Ctrl+Shift+P → "Test Agent"     # Test locally

# PowerShell
.\build-windows-exe.ps1         # Full build
.\build-windows-exe.ps1 -Clean  # Clean only
.\build-windows-exe.ps1 -Test   # Test only

# Service Management
sc query SysMonAgent            # Check status
net start SysMonAgent           # Start service
net stop SysMonAgent            # Stop service
```

## 🔄 Next Steps

1. **Test on your VMware Windows 11 machine**
2. **Verify all metrics are collected**
3. **Test different scenarios** (high CPU, memory, network issues)
4. **Deploy to production machines**
5. **Set up automated builds** (GitHub Actions, CI/CD)

