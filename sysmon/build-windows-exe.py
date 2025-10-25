#!/usr/bin/env python3
"""
OnLab SysMon Agent - Windows Executable Builder
This script builds the SysMon agent as a Windows .exe file using PyInstaller
"""

import os
import sys
import shutil
import subprocess
import json
from pathlib import Path

def check_pyinstaller():
    """Check if PyInstaller is installed"""
    try:
        import PyInstaller
        print("✅ PyInstaller is installed")
        return True
    except ImportError:
        print("❌ PyInstaller not found. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("✅ PyInstaller installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install PyInstaller")
            return False

def create_spec_file():
    """Create PyInstaller spec file for SysMon agent"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['sysmon.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config', 'config'),
        ('requirements.txt', '.'),
    ],
    hiddenimports=[
        'psutil',
        'requests',
        'jsonschema',
        'typing_extensions',
        'json',
        'time',
        'threading',
        'logging',
        'os',
        'sys',
        'platform',
        'subprocess',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SysMonAgent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
    version_file=None,
)
'''
    
    with open('SysMonAgent.spec', 'w') as f:
        f.write(spec_content)
    print("✅ Created PyInstaller spec file")

def create_installer_script():
    """Create a simple installer script"""
    installer_content = '''@echo off
REM OnLab SysMon Agent - Windows Installer
REM This script installs the SysMon agent as a Windows service

setlocal enabledelayedexpansion

echo ========================================
echo OnLab SysMon Agent - Windows Installer
echo ========================================

REM Check if running as Administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This installer must be run as Administrator
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

REM Configuration
set INSTALL_DIR=C:\\Program Files\\OnLab\\SysMon
set SERVICE_NAME=SysMonAgent
set EXE_NAME=SysMonAgent.exe

echo Installing SysMon Agent...

REM Create installation directory
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%INSTALL_DIR%\\logs" mkdir "%INSTALL_DIR%\\logs"
if not exist "%INSTALL_DIR%\\queue" mkdir "%INSTALL_DIR%\\queue"
if not exist "%INSTALL_DIR%\\temp" mkdir "%INSTALL_DIR%\\temp"
if not exist "%INSTALL_DIR%\\config" mkdir "%INSTALL_DIR%\\config"

REM Copy executable
copy "%EXE_NAME%" "%INSTALL_DIR%\\"
copy "config\\sysmon.onlab.json" "%INSTALL_DIR%\\config\\"

REM Create Windows Service using NSSM
echo Creating Windows service...

REM Download NSSM if not present
if not exist "C:\\nssm\\nssm.exe" (
    echo Downloading NSSM...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://nssm.cc/release/nssm-2.24.zip' -OutFile 'nssm.zip'}"
    powershell -Command "& {Expand-Archive -Path 'nssm.zip' -DestinationPath 'C:\\' -Force}"
    del nssm.zip
)

REM Install service using NSSM
C:\\nssm\\win64\\nssm.exe install %SERVICE_NAME% "%INSTALL_DIR%\\%EXE_NAME%"
C:\\nssm\\win64\\nssm.exe set %SERVICE_NAME% AppDirectory "%INSTALL_DIR%"
C:\\nssm\\win64\\nssm.exe set %SERVICE_NAME% Description "OnLab System Monitoring Agent"
C:\\nssm\\win64\\nssm.exe set %SERVICE_NAME% Start SERVICE_AUTO_START

REM Start the service
echo Starting SysMon service...
net start %SERVICE_NAME%

echo.
echo ========================================
echo Installation completed!
echo ========================================
echo.
echo Service Information:
echo   Service Name: %SERVICE_NAME%
echo   Install Directory: %INSTALL_DIR%
echo   Configuration: %INSTALL_DIR%\\config\\sysmon.onlab.json
echo   Logs: %INSTALL_DIR%\\logs\\
echo.
echo Useful Commands:
echo   Check Status: sc query %SERVICE_NAME%
echo   Start Service: net start %SERVICE_NAME%
echo   Stop Service: net stop %SERVICE_NAME%
echo   View Logs: type "%INSTALL_DIR%\\logs\\sysmon.log"
echo.
echo IMPORTANT: Make sure to update the API key in the configuration file!
echo   Edit: notepad "%INSTALL_DIR%\\config\\sysmon.onlab.json"
echo.
pause
'''
    
    with open('install-sysmon.bat', 'w') as f:
        f.write(installer_content)
    print("✅ Created installer script")

def create_config_template():
    """Create a configuration template"""
    config_template = {
        "server_url": "http://YOUR_ONELAB_SERVER:8000",
        "api_key": "YOUR_API_KEY_HERE",
        "client_name": "WINDOWS-PC-NAME",
        "monitor_interval_sec": 60,
        "upload_metrics": True,
        "enable_detailed_logging": False,
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
    
    os.makedirs('config', exist_ok=True)
    with open('config/sysmon.onlab.json', 'w') as f:
        json.dump(config_template, f, indent=2)
    print("✅ Created configuration template")

def build_executable():
    """Build the executable using PyInstaller"""
    print("🔨 Building SysMon Agent executable...")
    
    try:
        # Run PyInstaller
        subprocess.check_call([
            sys.executable, "-m", "PyInstaller",
            "--onefile",
            "--console",
            "--name=SysMonAgent",
            "--add-data=config;config",
            "--hidden-import=psutil",
            "--hidden-import=requests",
            "--hidden-import=jsonschema",
            "--hidden-import=typing_extensions",
            "sysmon.py"
        ])
        
        print("✅ Executable built successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to build executable: {e}")
        return False

def create_package():
    """Create the final package"""
    print("📦 Creating deployment package...")
    
    # Create package directory
    package_dir = "SysMonAgent-Windows"
    if os.path.exists(package_dir):
        shutil.rmtree(package_dir)
    os.makedirs(package_dir)
    
    # Copy files
    if os.path.exists("dist/SysMonAgent.exe"):
        shutil.copy("dist/SysMonAgent.exe", package_dir)
    
    shutil.copy("install-sysmon.bat", package_dir)
    shutil.copy("config/sysmon.onlab.json", package_dir)
    
    # Create README
    readme_content = '''# OnLab SysMon Agent - Windows Executable

## Quick Installation

1. **Edit Configuration:**
   - Open `sysmon.onlab.json`
   - Update `server_url` with your OnLab server IP
   - Update `api_key` with your API key from OnLab admin panel

2. **Install:**
   - Right-click `install-sysmon.bat`
   - Select "Run as administrator"

3. **Verify:**
   - Check service status: `sc query SysMonAgent`
   - View logs: `type "C:\\Program Files\\OnLab\\SysMon\\logs\\sysmon.log"`
   - Check OnLab dashboard

## Files Included
- `SysMonAgent.exe` - The monitoring agent executable
- `install-sysmon.bat` - Installation script
- `sysmon.onlab.json` - Configuration template

## Requirements
- Windows 10/11 or Windows Server 2016+
- Administrator privileges
- Network connectivity to OnLab server

## Support
For issues, check the logs in `C:\\Program Files\\OnLab\\SysMon\\logs\\`
'''
    
    with open(f"{package_dir}/README.txt", 'w') as f:
        f.write(readme_content)
    
    print(f"✅ Package created: {package_dir}/")
    return package_dir

def main():
    """Main build process"""
    print("🚀 OnLab SysMon Agent - Windows Executable Builder")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("sysmon.py"):
        print("❌ Error: sysmon.py not found")
        print("Please run this script from the sysmon directory")
        return False
    
    # Check PyInstaller
    if not check_pyinstaller():
        return False
    
    # Create necessary files
    create_spec_file()
    create_installer_script()
    create_config_template()
    
    # Build executable
    if not build_executable():
        return False
    
    # Create package
    package_dir = create_package()
    
    print("\n🎉 Build completed successfully!")
    print(f"📦 Package location: {package_dir}/")
    print("\n📋 Next steps:")
    print("1. Copy the package to your Windows system")
    print("2. Edit sysmon.onlab.json with your server details")
    print("3. Run install-sysmon.bat as Administrator")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
