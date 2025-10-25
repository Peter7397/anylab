# OnLab SysMon Agent - Windows PowerShell Deployment Script
# This script deploys the system monitor to Windows PCs

param(
    [string]$OnLabServer = "http://YOUR_SERVER_IP:8000",
    [string]$ApiKey = "YOUR_API_KEY_HERE",
    [string]$ClientName = $env:COMPUTERNAME,
    [string]$InstallDir = "C:\Program Files\OnLab\SysMon",
    [string]$ServiceName = "SysMonAgent"
)

# Colors for output
$Green = "Green"
$Yellow = "Yellow"
$Red = "Red"
$Blue = "Blue"

Write-Host "=== OnLab SysMon Agent - Windows Deployment ===" -ForegroundColor $Green
Write-Host "Target Server: $OnLabServer" -ForegroundColor $Blue
Write-Host "Client Name: $ClientName" -ForegroundColor $Blue
Write-Host "Install Directory: $InstallDir" -ForegroundColor $Blue
Write-Host ""

# Check if running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "ERROR: This script must be run as Administrator" -ForegroundColor $Red
    Write-Host "Right-click PowerShell and select 'Run as administrator'" -ForegroundColor $Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if Python is installed
Write-Host "Checking Python installation..." -ForegroundColor $Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python version: $pythonVersion" -ForegroundColor $Green
} catch {
    Write-Host "❌ ERROR: Python is not installed or not in PATH" -ForegroundColor $Red
    Write-Host "Please install Python 3.7+ from https://python.org" -ForegroundColor $Red
    Write-Host "Make sure to check 'Add Python to PATH' during installation" -ForegroundColor $Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Create installation directory
Write-Host "Creating installation directory..." -ForegroundColor $Yellow
$dirs = @(
    $InstallDir,
    "$InstallDir\logs",
    "$InstallDir\queue", 
    "$InstallDir\temp",
    "$InstallDir\config"
)

foreach ($dir in $dirs) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# Copy agent files (assuming script is run from sysmon directory)
Write-Host "Copying agent files..." -ForegroundColor $Yellow
if (Test-Path "sysmon_project\src") {
    Copy-Item "sysmon_project\src\*" $InstallDir -Recurse -Force
    Copy-Item "sysmon_project\requirements.txt" $InstallDir -Force
} else {
    Write-Host "❌ ERROR: Agent files not found" -ForegroundColor $Red
    Write-Host "Please run this script from the sysmon directory" -ForegroundColor $Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Install Python dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor $Yellow
Set-Location $InstallDir
try {
    python -m pip install -r requirements.txt
    Write-Host "✅ Dependencies installed successfully" -ForegroundColor $Green
} catch {
    Write-Host "❌ ERROR: Failed to install Python dependencies" -ForegroundColor $Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Create configuration file
Write-Host "Creating configuration..." -ForegroundColor $Yellow
$config = @{
    server_url = $OnLabServer
    api_key = $ApiKey
    client_name = $ClientName
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

$config | ConvertTo-Json -Depth 10 | Out-File "$InstallDir\config\sysmon.onlab.json" -Encoding UTF8

# Create Windows Service using NSSM
Write-Host "Creating Windows service..." -ForegroundColor $Yellow

# Download NSSM if not present
$nssmPath = "C:\nssm\nssm.exe"
if (!(Test-Path $nssmPath)) {
    Write-Host "Downloading NSSM..." -ForegroundColor $Yellow
    $nssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
    $nssmZip = "$env:TEMP\nssm.zip"
    
    try {
        Invoke-WebRequest -Uri $nssmUrl -OutFile $nssmZip
        Expand-Archive -Path $nssmZip -DestinationPath "C:\" -Force
        Remove-Item $nssmZip
        Write-Host "✅ NSSM downloaded successfully" -ForegroundColor $Green
    } catch {
        Write-Host "❌ ERROR: Failed to download NSSM" -ForegroundColor $Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Install service using NSSM
try {
    & "C:\nssm\win64\nssm.exe" install $ServiceName "python" "$InstallDir\sysmon.py"
    & "C:\nssm\win64\nssm.exe" set $ServiceName AppDirectory $InstallDir
    & "C:\nssm\win64\nssm.exe" set $ServiceName Description "OnLab System Monitoring Agent"
    & "C:\nssm\win64\nssm.exe" set $ServiceName Start SERVICE_AUTO_START
    Write-Host "✅ Service created successfully" -ForegroundColor $Green
} catch {
    Write-Host "❌ ERROR: Failed to create service" -ForegroundColor $Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Start the service
Write-Host "Starting SysMon service..." -ForegroundColor $Yellow
try {
    Start-Service $ServiceName
    Write-Host "✅ Service started successfully" -ForegroundColor $Green
} catch {
    Write-Host "⚠️  WARNING: Service failed to start automatically" -ForegroundColor $Yellow
    Write-Host "You may need to start it manually or check the configuration" -ForegroundColor $Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor $Green
Write-Host "Deployment completed!" -ForegroundColor $Green
Write-Host "========================================" -ForegroundColor $Green
Write-Host ""
Write-Host "Service Information:" -ForegroundColor $Blue
Write-Host "  Service Name: $ServiceName"
Write-Host "  Install Directory: $InstallDir"
Write-Host "  Configuration: $InstallDir\config\sysmon.onlab.json"
Write-Host "  Logs: $InstallDir\logs\"
Write-Host ""
Write-Host "Useful Commands:" -ForegroundColor $Blue
Write-Host "  Check Status: Get-Service $ServiceName"
Write-Host "  Start Service: Start-Service $ServiceName"
Write-Host "  Stop Service: Stop-Service $ServiceName"
Write-Host "  View Logs: Get-Content '$InstallDir\logs\sysmon.log' -Tail 50"
Write-Host ""
Write-Host "IMPORTANT: Make sure to update the API key in the configuration file!" -ForegroundColor $Yellow
Write-Host "  Edit: notepad '$InstallDir\config\sysmon.onlab.json'"
Write-Host ""
Read-Host "Press Enter to exit"
