@echo off
REM OnLab SysMon Agent - Windows Deployment Script
REM This script deploys the system monitor to Windows PCs

setlocal enabledelayedexpansion

REM Configuration - UPDATE THESE FOR YOUR ENVIRONMENT
set ONELAB_SERVER=http://YOUR_SERVER_IP:8000
set API_KEY=YOUR_API_KEY_HERE
set CLIENT_NAME=%COMPUTERNAME%
set INSTALL_DIR=C:\Program Files\OnLab\SysMon
set SERVICE_NAME=SysMonAgent

echo ========================================
echo OnLab SysMon Agent - Windows Deployment
echo ========================================
echo Target Server: %ONELAB_SERVER%
echo Client Name: %CLIENT_NAME%
echo Install Directory: %INSTALL_DIR%
echo.

REM Check if running as Administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

REM Check if Python is installed
echo Checking Python installation...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

python --version
echo.

REM Create installation directory
echo Creating installation directory...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%INSTALL_DIR%\logs" mkdir "%INSTALL_DIR%\logs"
if not exist "%INSTALL_DIR%\queue" mkdir "%INSTALL_DIR%\queue"
if not exist "%INSTALL_DIR%\temp" mkdir "%INSTALL_DIR%\temp"
if not exist "%INSTALL_DIR%\config" mkdir "%INSTALL_DIR%\config"

REM Copy agent files (assuming script is run from sysmon directory)
echo Copying agent files...
if exist "sysmon_project\src" (
    xcopy "sysmon_project\src\*" "%INSTALL_DIR%\" /E /Y
    copy "sysmon_project\requirements.txt" "%INSTALL_DIR%\"
) else (
    echo ERROR: Agent files not found
    echo Please run this script from the sysmon directory
    pause
    exit /b 1
)

REM Install Python dependencies
echo Installing Python dependencies...
cd /d "%INSTALL_DIR%"
pip install -r requirements.txt
if %errorLevel% neq 0 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)

REM Create configuration file
echo Creating configuration...
(
echo {
echo   "server_url": "%ONELAB_SERVER%",
echo   "api_key": "%API_KEY%",
echo   "client_name": "%CLIENT_NAME%",
echo   "monitor_interval_sec": 60,
echo   "upload_metrics": true,
echo   "enable_detailed_logging": false,
echo   "max_queue_size": 1000,
echo   "paths": {
echo     "logs": "logs",
echo     "queue": "queue",
echo     "temp": "temp"
echo   },
echo   "thresholds": {
echo     "cpu_total": {
echo       "warn_pct": 70,
echo       "crit_pct": 90
echo     },
echo     "ram": {
echo       "warn_pct": 75,
echo       "crit_pct": 90
echo     },
echo     "disk_free": {
echo       "warn_pct": 20,
echo       "crit_pct": 10
echo     }
echo   }
echo }
) > "%INSTALL_DIR%\config\sysmon.onlab.json"

REM Create Windows Service using NSSM
echo Creating Windows service...
if not exist "C:\nssm\nssm.exe" (
    echo Downloading NSSM...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://nssm.cc/release/nssm-2.24.zip' -OutFile 'nssm.zip'}"
    powershell -Command "& {Expand-Archive -Path 'nssm.zip' -DestinationPath 'C:\' -Force}"
    del nssm.zip
)

REM Install service using NSSM
C:\nssm\win64\nssm.exe install %SERVICE_NAME% "python" "%INSTALL_DIR%\sysmon.py"
C:\nssm\win64\nssm.exe set %SERVICE_NAME% AppDirectory "%INSTALL_DIR%"
C:\nssm\win64\nssm.exe set %SERVICE_NAME% Description "OnLab System Monitoring Agent"
C:\nssm\win64\nssm.exe set %SERVICE_NAME% Start SERVICE_AUTO_START

REM Start the service
echo Starting SysMon service...
net start %SERVICE_NAME%
if %errorLevel% neq 0 (
    echo WARNING: Service failed to start automatically
    echo You may need to start it manually or check the configuration
)

echo.
echo ========================================
echo Deployment completed!
echo ========================================
echo.
echo Service Information:
echo   Service Name: %SERVICE_NAME%
echo   Install Directory: %INSTALL_DIR%
echo   Configuration: %INSTALL_DIR%\config\sysmon.onlab.json
echo   Logs: %INSTALL_DIR%\logs\
echo.
echo Useful Commands:
echo   Check Status: sc query %SERVICE_NAME%
echo   Start Service: net start %SERVICE_NAME%
echo   Stop Service: net stop %SERVICE_NAME%
echo   View Logs: type "%INSTALL_DIR%\logs\sysmon.log"
echo.
echo IMPORTANT: Make sure to update the API key in the configuration file!
echo   Edit: notepad "%INSTALL_DIR%\config\sysmon.onlab.json"
echo.
pause
