# OnLab SysMon Agent - Windows Package Creation Script
# This script creates a deployment package for Windows PCs

param(
    [string]$Version = "2.0.0"
)

$PackageName = "onlab-sysmon-agent-windows"
$PackageDir = "${PackageName}-${Version}"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

Write-Host "📦 Creating OnLab SysMon Agent Windows Package v$Version" -ForegroundColor Green

# Create package directory
if (Test-Path $PackageDir) {
    Remove-Item $PackageDir -Recurse -Force
}
New-Item -ItemType Directory -Path $PackageDir | Out-Null

# Copy required files
Write-Host "📋 Copying files..." -ForegroundColor Yellow
Copy-Item -Path "sysmon_project" -Destination $PackageDir -Recurse -Force
Copy-Item -Path "deploy-windows.ps1" -Destination $PackageDir -Force
Copy-Item -Path "deploy-windows.bat" -Destination $PackageDir -Force

# Create README for the package
$readmeContent = @"
# OnLab SysMon Agent Windows v$Version

## Quick Start

1. **Extract the package:**
   ```powershell
   Expand-Archive -Path $PackageName-$Version.zip -DestinationPath .
   cd $PackageName-$Version
   ```

2. **Edit configuration:**
   ```powershell
   # Edit deploy-windows.ps1 and update:
   # - OnLabServer (your OnLab server IP)
   # - ApiKey (get from OnLab admin panel)
   notepad deploy-windows.ps1
   ```

3. **Deploy (PowerShell - Recommended):**
   ```powershell
   # Right-click PowerShell and "Run as administrator"
   .\deploy-windows.ps1
   ```

   **OR Deploy (Batch file):**
   ```cmd
   # Right-click deploy-windows.bat and "Run as administrator"
   deploy-windows.bat
   ```

## Requirements
- Windows 10/11 or Windows Server 2016+
- Python 3.7+ (https://python.org)
- Administrator privileges
- Network connectivity to OnLab server

## Prerequisites
1. Install Python 3.7+ from https://python.org
2. Make sure to check "Add Python to PATH" during installation
3. Run PowerShell as Administrator

## Support
See DEPLOYMENT_GUIDE.md for detailed instructions.
"@

$readmeContent | Out-File "$PackageDir\README.md" -Encoding UTF8

# Create the zip package
Write-Host "🗜️ Creating package..." -ForegroundColor Yellow
$zipPath = "${PackageName}-${Version}.zip"
if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

Compress-Archive -Path $PackageDir\* -DestinationPath $zipPath

# Clean up
Remove-Item $PackageDir -Recurse -Force

Write-Host "✅ Package created: $zipPath" -ForegroundColor Green
Write-Host ""
Write-Host "📤 To deploy to a Windows client:" -ForegroundColor Blue
Write-Host "   1. Copy $zipPath to the Windows PC"
Write-Host "   2. Extract the zip file"
Write-Host "   3. Edit deploy-windows.ps1 (update server IP and API key)"
Write-Host "   4. Right-click PowerShell and 'Run as administrator'"
Write-Host "   5. Run: .\deploy-windows.ps1"
Write-Host ""
Write-Host "🔧 Alternative deployment methods:" -ForegroundColor Blue
Write-Host "   - Use deploy-windows.bat (right-click 'Run as administrator')"
Write-Host "   - Use Group Policy for enterprise deployment"
Write-Host "   - Use SCCM for large-scale deployment"
