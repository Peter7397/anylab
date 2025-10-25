@echo off
REM OnLab SysMon Agent - Simple Installation Script
REM This script provides a simple way to install the SysMon agent

setlocal enabledelayedexpansion

echo ========================================
echo OnLab SysMon Agent - Installation
echo ========================================
echo.

REM Check if running as Administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This installer must be run as Administrator
    echo Right-click and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

echo Choose installation method:
echo.
echo 1. VMware Quick Setup (Recommended for VMware Windows 11)
echo 2. PowerShell Deployment (Advanced)
echo 3. Manual Installation (Step by step)
echo 4. Exit
echo.

set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" (
    echo.
    echo Running VMware Quick Setup...
    echo.
    echo IMPORTANT: Make sure to edit config/sysmon.onelab.json first!
    echo.
    pause
    powershell -ExecutionPolicy Bypass -File "vmware-setup.ps1"
) else if "%choice%"=="2" (
    echo.
    echo Running PowerShell Deployment...
    echo.
    echo IMPORTANT: Make sure to edit config/sysmon.onelab.json first!
    echo.
    pause
    powershell -ExecutionPolicy Bypass -File "deploy-windows.ps1"
) else if "%choice%"=="3" (
    echo.
    echo Manual Installation Steps:
    echo.
    echo 1. Edit config/sysmon.onelab.json with your server details
    echo 2. Install Python 3.7+ if not already installed
    echo 3. Run: pip install -r requirements.txt
    echo 4. Test: python sysmon.py
    echo 5. Run: deploy-windows.bat
    echo.
    echo See README.md for detailed instructions.
    echo.
    pause
) else if "%choice%"=="4" (
    echo Exiting...
    exit /b 0
) else (
    echo Invalid choice. Please run the script again.
    pause
    exit /b 1
)

echo.
echo Installation completed!
echo.
echo Next steps:
echo 1. Check service status: sc query SysMonAgent
echo 2. View logs: type "C:\Program Files\OnLab\SysMon\logs\sysmon.log"
echo 3. Check dashboard: http://10.96.17.21:3000
echo.
pause
