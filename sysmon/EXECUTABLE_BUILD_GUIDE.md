# 🚀 Windows Executable Build Guide

## Overview

This guide shows you how to compile the SysMon agent into a Windows executable (.exe) file using PyInstaller. This makes deployment much easier as you don't need Python installed on target machines.

## 📋 Prerequisites

### Development Environment (Windows)
- **Python 3.7+** installed
- **VS Code** (recommended) or any text editor
- **Git** (optional, for version control)
- **Internet connection** (for downloading PyInstaller)

### Target Systems
- **Windows 10/11** or **Windows Server 2016+**
- **Administrator privileges** (for service installation)
- **Network connectivity** to OnLab server

## 🛠️ Build Methods

### Method 1: VS Code Tasks (Recommended)

**Step 1: Open VS Code**
```bash
# Open VS Code in the sysmon directory
code .
```

**Step 2: Install PyInstaller**
```bash
# Press Ctrl+Shift+P → "Tasks: Run Task" → "Install PyInstaller"
# Or run manually:
pip install pyinstaller
```

**Step 3: Build Executable**
```bash
# Press Ctrl+Shift+P → "Tasks: Run Task" → "Build SysMon Windows Executable"
# Or press Ctrl+Shift+B (default build task)
```

### Method 2: PowerShell Script

**Step 1: Run PowerShell as Administrator**
```powershell
# Navigate to sysmon directory
cd "path\to\sysmon"

# Run the build script
.\build-windows-exe.ps1
```

**Step 2: Alternative PowerShell Commands**
```powershell
# Clean build files only
.\build-windows-exe.ps1 -Clean

# Test the agent only
.\build-windows-exe.ps1 -Test

# Install PyInstaller only
.\build-windows-exe.ps1 -InstallOnly
```

### Method 3: Python Script

**Step 1: Run Python Build Script**
```bash
# Navigate to sysmon directory
cd path\to\sysmon

# Run the build script
python build-windows-exe.py
```

### Method 4: Manual PyInstaller

**Step 1: Install PyInstaller**
```bash
pip install pyinstaller
```

**Step 2: Build Executable**
```bash
pyinstaller --onefile --console --name=SysMonAgent --add-data=config;config --hidden-import=psutil --hidden-import=requests --hidden-import=jsonschema --hidden-import=typing_extensions sysmon.py
```

## 📦 Build Output

After successful build, you'll get:

```
SysMonAgent-Windows/
├── SysMonAgent.exe          # The executable file
├── install-sysmon.bat       # Installation script
├── sysmon.onlab.json        # Configuration template
└── README.txt              # Installation instructions
```

## 🔧 Build Configuration

### PyInstaller Options Used

```bash
--onefile              # Create single executable file
--console              # Show console window (for debugging)
--name=SysMonAgent     # Name of the executable
--add-data=config;config  # Include configuration files
--hidden-import=psutil     # Include required modules
--hidden-import=requests
--hidden-import=jsonschema
--hidden-import=typing_extensions
```

### Customizing the Build

**Edit `build-windows-exe.py` or `build-windows-exe.ps1` to modify:**

1. **Executable Name:**
   ```python
   "--name=YourCustomName"
   ```

2. **Add Icons:**
   ```python
   "--icon=path/to/icon.ico"
   ```

3. **Hide Console:**
   ```python
   "--windowed"  # Instead of --console
   ```

4. **Add More Dependencies:**
   ```python
   "--hidden-import=your_module"
   ```

## 🧪 Testing the Build

### Test the Executable Locally
```bash
# Run the executable directly
.\dist\SysMonAgent.exe

# Or test the Python script
python sysmon.py
```

### Test Installation Package
```bash
# Copy to test machine
# Run install-sysmon.bat as Administrator
# Check service status
sc query SysMonAgent
```

## 📊 Build Optimization

### Reduce Executable Size

**Option 1: Exclude Unused Modules**
```bash
pyinstaller --onefile --console --exclude-module=matplotlib --exclude-module=numpy sysmon.py
```

**Option 2: Use UPX Compression**
```bash
# Install UPX first
pyinstaller --onefile --console --upx-dir=path/to/upx sysmon.py
```

**Option 3: Strip Debug Information**
```bash
pyinstaller --onefile --console --strip sysmon.py
```

### Improve Startup Time

**Option 1: Use --onedir Instead of --onefile**
```bash
pyinstaller --onedir --console sysmon.py
```

**Option 2: Optimize Imports**
```python
# In sysmon.py, use lazy imports
def get_psutil():
    import psutil
    return psutil
```

## 🔍 Troubleshooting Build Issues

### Common Build Problems

**1. Module Not Found**
```bash
# Add missing module to hidden-imports
--hidden-import=missing_module
```

**2. File Not Found**
```bash
# Check file paths in --add-data
--add-data=correct/path;destination
```

**3. Large Executable Size**
```bash
# Use --exclude-module for unused modules
--exclude-module=large_module
```

**4. Antivirus False Positive**
```bash
# Add antivirus exclusions
# Or use --codesign-identity for code signing
```

### Debug Build Issues

**Enable Verbose Output:**
```bash
pyinstaller --onefile --console --debug=all sysmon.py
```

**Check PyInstaller Logs:**
```bash
# Look for build logs in build/ directory
# Check for missing dependencies
```

## 🚀 Deployment

### Single Machine Deployment
```bash
# Copy SysMonAgent-Windows folder to target machine
# Edit sysmon.onlab.json with server details
# Run install-sysmon.bat as Administrator
```

### Enterprise Deployment

**Option 1: Group Policy**
```bash
# Package the executable
# Deploy via GPO startup scripts
```

**Option 2: SCCM**
```bash
# Create SCCM application
# Deploy to target machines
```

**Option 3: PowerShell Remoting**
```powershell
# Deploy to multiple machines
$computers = @("PC1", "PC2", "PC3")
foreach ($computer in $computers) {
    Copy-Item "SysMonAgent-Windows" "\\\\$computer\\C$\\temp\\" -Recurse
    Invoke-Command -ComputerName $computer -ScriptBlock {
        # Installation commands
    }
}
```

## 📈 Performance Considerations

### Executable Size
- **Typical size:** 15-25 MB
- **With UPX compression:** 8-15 MB
- **Minimal build:** 5-10 MB

### Memory Usage
- **Runtime memory:** ~50 MB
- **Startup time:** 2-5 seconds
- **CPU impact:** < 1%

### Network Impact
- **Data transfer:** ~1KB per minute
- **Connection overhead:** Minimal

## 🔄 Continuous Integration

### Automated Build Script
```powershell
# build-ci.ps1
param([string]$Version = "2.0.0")

# Build executable
.\build-windows-exe.ps1

# Create versioned package
$packageName = "SysMonAgent-Windows-v$Version"
Rename-Item "SysMonAgent-Windows" $packageName

# Create zip archive
Compress-Archive -Path $packageName -DestinationPath "$packageName.zip"

Write-Host "Build completed: $packageName.zip"
```

### GitHub Actions Example
```yaml
name: Build Windows Executable

on:
  push:
    branches: [ main ]
  release:
    types: [ published ]

jobs:
  build:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install pyinstaller
        pip install -r requirements.txt
    
    - name: Build executable
      run: python build-windows-exe.py
    
    - name: Upload artifacts
      uses: actions/upload-artifact@v2
      with:
        name: SysMonAgent-Windows
        path: SysMonAgent-Windows/
```

## 📞 Support

### Build Issues
1. Check PyInstaller documentation
2. Review build logs
3. Test with minimal configuration
4. Update PyInstaller to latest version

### Runtime Issues
1. Check Windows Event Logs
2. Verify configuration file
3. Test network connectivity
4. Review agent logs

### Performance Issues
1. Monitor resource usage
2. Optimize configuration
3. Update to latest version
4. Consider hardware requirements

