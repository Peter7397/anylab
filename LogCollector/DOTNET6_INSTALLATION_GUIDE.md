# .NET 6.0 Runtime Installation Guide

## Important: .NET 6.0 is NOT Pre-Installed

**.NET 6.0 Desktop Runtime is NOT included by default in any Windows version.** It must be installed separately on target PCs.

---

## Windows Versions and .NET 6.0

### Which Windows Versions Support .NET 6.0?

**.NET 6.0 can be installed on:**
- ✅ Windows 10 version 1607 or later
- ✅ Windows 11 (all versions)
- ✅ Windows Server 2016 or later
- ✅ Windows Server 2019
- ✅ Windows Server 2022

**Note:** Even though these Windows versions *support* .NET 6.0, it is **NOT pre-installed**. You must install it separately.

---

## Installation Options

### Option 1: Self-Contained Build (Recommended - No Installation Needed)

**Current Setup:** Your application is configured for **self-contained deployment**.

**Benefits:**
- ✅ No .NET installation required on target PCs
- ✅ Works on any Windows 10/11 PC
- ✅ One executable includes everything
- ⚠️ Larger file size (~60-100 MB)

**This is what you have now!** No need to install .NET on target PCs.

---

### Option 2: Framework-Dependent Build (Requires .NET Installation)

If you switch to framework-dependent build, target PCs need .NET 6.0 Desktop Runtime installed.

**Benefits:**
- ✅ Smaller file size (~5-10 MB)
- ✅ Uses existing runtime
- ⚠️ Requires .NET 6.0 Desktop Runtime on target PCs

---

## How to Install .NET 6.0 Desktop Runtime

If you need to install .NET 6.0 Desktop Runtime on target PCs:

### Method 1: Download and Install Manually

1. **Download .NET 6.0 Desktop Runtime**
   - Visit: https://dotnet.microsoft.com/download/dotnet/6.0
   - Click on **"Desktop Runtime 6.0.x"** (not SDK)
   - Choose **Windows x64** version
   - Download the installer

2. **Install**
   - Run the downloaded installer
   - Follow the installation wizard
   - Restart the application if it was running

### Method 2: Silent Installation (For IT Deployment)

**Using Command Line:**
```cmd
dotnet-desktopruntime-6.0.x-win-x64.exe /quiet /norestart
```

**Using PowerShell:**
```powershell
Start-Process -FilePath "dotnet-desktopruntime-6.0.x-win-x64.exe" -ArgumentList "/quiet", "/norestart" -Wait
```

### Method 3: Using Windows Package Manager (winget)

```cmd
winget install Microsoft.DotNet.DesktopRuntime.6
```

---

## Runtime Detection in Application

I've added runtime detection code to `Program.cs` (currently commented out). 

**To enable it** (if you switch to framework-dependent build):

1. Open `Program.cs`
2. Find the commented section around line 60-90
3. Uncomment the `.NET Runtime check` section
4. Rebuild the application

**What it does:**
- Checks if .NET 6.0, 7.0, or 8.0 Desktop Runtime is installed
- If not found, prompts user to download and install
- Opens the download page automatically

---

## Checking if .NET 6.0 is Installed

### Method 1: Command Prompt
```cmd
dotnet --list-runtimes
```

Look for:
```
Microsoft.WindowsDesktop.App 6.0.x
```

### Method 2: PowerShell
```powershell
dotnet --list-runtimes | Select-String "Microsoft.WindowsDesktop.App 6.0"
```

### Method 3: Registry
Navigate to:
```
HKEY_LOCAL_MACHINE\SOFTWARE\dotnet\Setup\InstalledVersions\x64\sharedfx\Microsoft.WindowsDesktop.App
```

Look for a folder named `6.0.x`

---

## Recommendation for Your Situation

Since your target PCs **already have .NET 6.0.3 installed** (as you showed earlier):

### Current Setup (Self-Contained .NET 8.0)
- ✅ Works everywhere (even without .NET)
- ✅ No installation needed
- ⚠️ Larger file (~70-100 MB)

### Alternative: Framework-Dependent .NET 6.0
- ✅ Smallest file (~5-10 MB)
- ✅ Uses existing .NET 6.0 runtime
- ⚠️ Only works on PCs with .NET 6.0+ installed

### Best Choice

**If all your target PCs have .NET 6.0:**
- Switch to framework-dependent .NET 6.0 for smallest file size

**If unsure or some PCs don't have .NET:**
- Keep current self-contained build (works everywhere)

---

## Summary

| Question | Answer |
|----------|--------|
| Is .NET 6.0 pre-installed in Windows? | ❌ No - must be installed separately |
| Which Windows versions support .NET 6.0? | Windows 10 (1607+), Windows 11, Windows Server 2016+ |
| Do I need to install .NET 6.0? | Only if using framework-dependent build |
| Current setup requires installation? | ❌ No - self-contained includes everything |

---

## Quick Reference

**Download .NET 6.0 Desktop Runtime:**
- URL: https://dotnet.microsoft.com/download/dotnet/6.0
- Choose: Desktop Runtime (not SDK)
- Version: 6.0.x (latest)
- Platform: Windows x64

**Check Installation:**
```cmd
dotnet --list-runtimes
```

**Your Current Build:**
- ✅ Self-contained (no .NET installation needed)
- ✅ Works on any Windows PC
- ✅ Just copy and run!
