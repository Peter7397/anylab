# OnLab SysMon Agent - Windows Executable Builder (PowerShell)
# This script builds the SysMon agent as a Windows .exe file

param(
    [switch]$Clean,
    [switch]$Test,
    [switch]$InstallOnly
)

# Colors for output
$Green = "Green"
$Yellow = "Yellow"
$Red = "Red"
$Blue = "Blue"

Write-Host "🚀 OnLab SysMon Agent - Windows Executable Builder" -ForegroundColor $Green
Write-Host "=" * 50 -ForegroundColor $Blue

# Function to check if Python is available
function Test-Python {
    try {
        $pythonVersion = python --version 2>&1
        Write-Host "✅ Python found: $pythonVersion" -ForegroundColor $Green
        return $true
    } catch {
        Write-Host "❌ Python not found or not in PATH" -ForegroundColor $Red
        Write-Host "Please install Python 3.7+ from https://python.org" -ForegroundColor $Yellow
        return $false
    }
}

# Function to install PyInstaller
function Install-PyInstaller {
    Write-Host "📦 Installing PyInstaller..." -ForegroundColor $Yellow
    try {
        python -m pip install pyinstaller
        Write-Host "✅ PyInstaller installed successfully" -ForegroundColor $Green
        return $true
    } catch {
        Write-Host "❌ Failed to install PyInstaller" -ForegroundColor $Red
        return $false
    }
}

# Function to clean build files
function Clear-BuildFiles {
    Write-Host "🧹 Cleaning build files..." -ForegroundColor $Yellow
    
    $dirsToRemove = @("dist", "build", "__pycache__")
    $filesToRemove = @("*.spec")
    
    foreach ($dir in $dirsToRemove) {
        if (Test-Path $dir) {
            Remove-Item $dir -Recurse -Force
            Write-Host "  Removed: $dir" -ForegroundColor $Blue
        }
    }
    
    foreach ($pattern in $filesToRemove) {
        Get-ChildItem -Path . -Filter $pattern | ForEach-Object {
            Remove-Item $_.FullName -Force
            Write-Host "  Removed: $($_.Name)" -ForegroundColor $Blue
        }
    }
    
    Write-Host "✅ Build files cleaned" -ForegroundColor $Green
}

# Function to create configuration template
function New-ConfigTemplate {
    Write-Host "⚙️  Creating configuration template..." -ForegroundColor $Yellow
    
    $config = @{
        server_url = "http://10.96.17.21:8000"
        api_key = "YOUR_API_KEY_HERE"
        client_name = $env:COMPUTERNAME
        monitor_interval_sec = 60
        upload_metrics = $true
        enable_detailed_logging = $false
        max_queue_size = 1000
        paths = @{
            logs = "logs"
            queue = "queue"
            temp = "temp"
        }
        thresholds = @{
            cpu_total = @{
                warn_pct = 70
                crit_pct = 90
            }
            ram = @{
                warn_pct = 75
                crit_pct = 90
            }
            disk_free = @{
                warn_pct = 20
                crit_pct = 10
            }
        }
    }
    
    if (!(Test-Path "config")) {
        New-Item -ItemType Directory -Path "config" | Out-Null
    }
    
    $config | ConvertTo-Json -Depth 10 | Out-File "config/sysmon.onlab.json" -Encoding UTF8
    Write-Host "✅ Configuration template created" -ForegroundColor $Green
}

# Function to build executable
function Build-Executable {
    Write-Host "🔨 Building SysMon Agent executable..." -ForegroundColor $Yellow
    
    $pyinstallerArgs = @(
        "--onefile",
        "--console",
        "--name=SysMonAgent",
        "--add-data=config;config",
        "--hidden-import=psutil",
        "--hidden-import=requests",
        "--hidden-import=jsonschema",
        "--hidden-import=typing_extensions",
        "sysmon.py"
    )
    
    try {
        python -m PyInstaller @pyinstallerArgs
        Write-Host "✅ Executable built successfully!" -ForegroundColor $Green
        return $true
    } catch {
        Write-Host "❌ Failed to build executable" -ForegroundColor $Red
        return $false
    }
}

# Function to create installer script
function New-InstallerScript {
    Write-Host "📝 Creating installer script..." -ForegroundColor $Yellow
    
    $installerContent = @'
@echo off
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
set INSTALL_DIR=C:\Program Files\OnLab\SysMon
set SERVICE_NAME=SysMonAgent
set EXE_NAME=SysMonAgent.exe

echo Installing SysMon Agent...

REM Create installation directory
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%INSTALL_DIR%\logs" mkdir "%INSTALL_DIR%\logs"
if not exist "%INSTALL_DIR%\queue" mkdir "%INSTALL_DIR%\queue"
if not exist "%INSTALL_DIR%\temp" mkdir "%INSTALL_DIR%\temp"
if not exist "%INSTALL_DIR%\config" mkdir "%INSTALL_DIR%\config"

REM Copy executable
copy "%EXE_NAME%" "%INSTALL_DIR%\"
copy "config\sysmon.onlab.json" "%INSTALL_DIR%\config\"

REM Create Windows Service using NSSM
echo Creating Windows service...

REM Download NSSM if not present
if not exist "C:\nssm\nssm.exe" (
    echo Downloading NSSM...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://nssm.cc/release/nssm-2.24.zip' -OutFile 'nssm.zip'}"
    powershell -Command "& {Expand-Archive -Path 'nssm.zip' -DestinationPath 'C:\' -Force}"
    del nssm.zip
)

REM Install service using NSSM
C:\nssm\win64\nssm.exe install %SERVICE_NAME% "%INSTALL_DIR%\%EXE_NAME%"
C:\nssm\win64\nssm.exe set %SERVICE_NAME% AppDirectory "%INSTALL_DIR%"
C:\nssm\win64\nssm.exe set %SERVICE_NAME% Description "OnLab System Monitoring Agent"
C:\nssm\win64\nssm.exe set %SERVICE_NAME% Start SERVICE_AUTO_START

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
'@
    
    $installerContent | Out-File "install-sysmon.bat" -Encoding ASCII
    Write-Host "✅ Installer script created" -ForegroundColor $Green
}

# Function to create package
function New-Package {
    Write-Host "📦 Creating deployment package..." -ForegroundColor $Yellow
    
    $packageDir = "SysMonAgent-Windows"
    if (Test-Path $packageDir) {
        Remove-Item $packageDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $packageDir | Out-Null
    
    # Copy files
    if (Test-Path "dist/SysMonAgent.exe") {
        Copy-Item "dist/SysMonAgent.exe" $packageDir
    }
    
    Copy-Item "install-sysmon.bat" $packageDir
    Copy-Item "config/sysmon.onlab.json" $packageDir
    
    # Create README
    $readmeContent = @"
# OnLab SysMon Agent - Windows Executable

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
   - View logs: `type "C:\Program Files\OnLab\SysMon\logs\sysmon.log"`
   - Check OnLab dashboard: http://10.96.17.21:3000

## Files Included
- `SysMonAgent.exe` - The monitoring agent executable
- `install-sysmon.bat` - Installation script
- `sysmon.onlab.json` - Configuration template

## Requirements
- Windows 10/11 or Windows Server 2016+
- Administrator privileges
- Network connectivity to OnLab server

## Support
For issues, check the logs in `C:\Program Files\OnLab\SysMon\logs\`
"@
    
    $readmeContent | Out-File "$packageDir/README.txt" -Encoding UTF8
    
    Write-Host "✅ Package created: $packageDir/" -ForegroundColor $Green
    return $packageDir
}

# Function to test the agent
function Test-SysMonAgent {
    Write-Host "🧪 Testing SysMon Agent..." -ForegroundColor $Yellow
    
    if (!(Test-Path "sysmon.py")) {
        Write-Host "❌ sysmon.py not found" -ForegroundColor $Red
        return $false
    }
    
    try {
        Write-Host "Running SysMon agent (press Ctrl+C to stop)..." -ForegroundColor $Blue
        python sysmon.py
    } catch {
        Write-Host "❌ Test failed" -ForegroundColor $Red
        return $false
    }
}

# Main execution
if ($Clean) {
    Clear-BuildFiles
    exit 0
}

if ($Test) {
    Test-SysMonAgent
    exit 0
}

if ($InstallOnly) {
    Install-PyInstaller
    exit 0
}

# Check Python
if (!(Test-Python)) {
    exit 1
}

# Install PyInstaller if needed
try {
    python -c "import PyInstaller" 2>$null
    Write-Host "✅ PyInstaller is already installed" -ForegroundColor $Green
} catch {
    if (!(Install-PyInstaller)) {
        exit 1
    }
}

# Clean previous builds
Clear-BuildFiles

# Create configuration template
New-ConfigTemplate

# Build executable
if (!(Build-Executable)) {
    exit 1
}

# Create installer script
New-InstallerScript

# Create package
$packageDir = New-Package

Write-Host ""
Write-Host "🎉 Build completed successfully!" -ForegroundColor $Green
Write-Host "📦 Package location: $packageDir/" -ForegroundColor $Blue
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor $Yellow
Write-Host "1. Copy the package to your target Windows system" -ForegroundColor $Blue
Write-Host "2. Edit sysmon.onlab.json with your server details" -ForegroundColor $Blue
Write-Host "3. Run install-sysmon.bat as Administrator" -ForegroundColor $Blue
Write-Host ""
Write-Host "🔧 VS Code Tasks:" -ForegroundColor $Yellow
Write-Host "- Ctrl+Shift+P → 'Tasks: Run Task' → 'Build SysMon Windows Executable'" -ForegroundColor $Blue
Write-Host "- Ctrl+Shift+P → 'Tasks: Run Task' → 'Clean Build Files'" -ForegroundColor $Blue

