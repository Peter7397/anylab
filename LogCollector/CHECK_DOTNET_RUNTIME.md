# How to Check .NET Runtime on Target PC

This guide shows you how to check if a target PC already has .NET runtime installed.

---

## Method 1: Command Prompt (Easiest)

### Check All Installed .NET Versions

1. **Open Command Prompt** (as Administrator)
   - Press `Win + R`
   - Type `cmd` and press Enter
   - Or search for "Command Prompt" in Start menu

2. **Run this command:**
   ```cmd
   dotnet --list-runtimes
   ```

3. **What to look for:**
   - Look for `Microsoft.WindowsDesktop.App 8.0.x` (for .NET 8.0)
   - Or `Microsoft.WindowsDesktop.App 7.0.x` (for .NET 7.0)
   - Or `Microsoft.WindowsDesktop.App 6.0.x` (for .NET 6.0)

### Example Output (if .NET 8.0 is installed):
```
Microsoft.AspNetCore.App 8.0.0
Microsoft.NETCore.App 8.0.0
Microsoft.WindowsDesktop.App 8.0.0
```

### Example Output (if NOT installed):
```
No runtimes found.
```

---

## Method 2: PowerShell

### Check .NET Runtime

1. **Open PowerShell** (as Administrator)
   - Press `Win + X`
   - Select "Windows PowerShell (Admin)"
   - Or search for "PowerShell" and right-click → "Run as administrator"

2. **Run this command:**
   ```powershell
   dotnet --list-runtimes
   ```

3. **Or check specific version:**
   ```powershell
   Get-ChildItem "HKLM:\SOFTWARE\dotnet\Setup\InstalledVersions\x64\sharedfx\Microsoft.WindowsDesktop.App" | Select-Object Name
   ```

---

## Method 3: Registry Check

### Check Registry for .NET Installation

1. **Open Registry Editor**
   - Press `Win + R`
   - Type `regedit` and press Enter
   - Click "Yes" if prompted

2. **Navigate to:**
   ```
   HKEY_LOCAL_MACHINE\SOFTWARE\dotnet\Setup\InstalledVersions\x64\sharedfx\Microsoft.WindowsDesktop.App
   ```

3. **Look for folders:**
   - `8.0.x` folder = .NET 8.0 Desktop Runtime installed
   - `7.0.x` folder = .NET 7.0 Desktop Runtime installed
   - `6.0.x` folder = .NET 6.0 Desktop Runtime installed

---

## Method 4: Check Installed Programs

### Using Control Panel

1. **Open Control Panel**
   - Press `Win + R`
   - Type `appwiz.cpl` and press Enter

2. **Look for:**
   - "Microsoft .NET Desktop Runtime 8.0.x"
   - "Microsoft .NET Desktop Runtime 7.0.x"
   - "Microsoft .NET Desktop Runtime 6.0.x"

### Using PowerShell (Faster)

```powershell
Get-ItemProperty "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*" | Where-Object { $_.DisplayName -like "*Microsoft .NET Desktop Runtime*" } | Select-Object DisplayName, DisplayVersion
```

---

## Method 5: Quick Check Script

### Create a Simple Check Script

Create a file called `check_dotnet.bat`:

```batch
@echo off
echo Checking for .NET Runtime...
echo.

dotnet --list-runtimes >nul 2>&1
if %errorlevel% == 0 (
    echo .NET is installed. Installed versions:
    dotnet --list-runtimes
) else (
    echo .NET is NOT installed or not in PATH.
)

echo.
echo Checking for .NET 8.0 Desktop Runtime specifically...
dotnet --list-runtimes | findstr "Microsoft.WindowsDesktop.App 8.0"
if %errorlevel% == 0 (
    echo .NET 8.0 Desktop Runtime is installed!
) else (
    echo .NET 8.0 Desktop Runtime is NOT installed.
)

pause
```

**To use:**
1. Copy the script above into Notepad
2. Save as `check_dotnet.bat`
3. Run it on the target PC

---

## What You Need for Remotecollect

### Required Runtime

For **Remotecollect** to run (if using framework-dependent build), you need:
- **Microsoft.WindowsDesktop.App 8.0.x** (Desktop Runtime)

**Note:** 
- If you built with **self-contained** deployment (which you did), you **don't need** .NET installed on target PC
- The self-contained build includes the runtime inside the `.exe` file

---

## Understanding the Results

### Scenario 1: .NET 8.0 Desktop Runtime is Installed
```
Microsoft.WindowsDesktop.App 8.0.0
```
**Result:** ✅ You could use framework-dependent build (smaller file)
**But:** Your self-contained build will still work fine

### Scenario 2: Only .NET Core Runtime (No Desktop)
```
Microsoft.NETCore.App 8.0.0
```
**Result:** ❌ Not enough - need Desktop Runtime
**Solution:** Use self-contained build (which you have)

### Scenario 3: No .NET Installed
```
No runtimes found.
```
**Result:** ❌ No .NET installed
**Solution:** Use self-contained build (which you have) ✅

### Scenario 4: Older Version Only
```
Microsoft.WindowsDesktop.App 6.0.0
```
**Result:** ❌ Wrong version - need 8.0
**Solution:** Use self-contained build (which you have) ✅

---

## Quick Decision Guide

| Target PC Has .NET 8.0 Desktop Runtime? | What to Use |
|------------------------------------------|-------------|
| ✅ Yes | Either self-contained OR framework-dependent |
| ❌ No | **Must use self-contained** (which you have) ✅ |

---

## Recommendation

**Since you already built with self-contained deployment:**
- ✅ Your `.exe` will work on **any** Windows PC
- ✅ No need to check or install .NET on target PCs
- ✅ Just copy and run the `.exe` file

**However, if you want a smaller file size:**
- If target PCs have .NET 8.0 Desktop Runtime installed
- You could rebuild as framework-dependent (smaller file, ~5-10 MB)
- But then you'd need to ensure all target PCs have .NET 8.0 installed

---

## Summary

**To check on target PC:**
1. Open Command Prompt
2. Run: `dotnet --list-runtimes`
3. Look for: `Microsoft.WindowsDesktop.App 8.0.x`

**Your current build:**
- ✅ Self-contained (includes .NET runtime)
- ✅ Works on any Windows PC
- ✅ No need to check or install .NET
- ✅ File size: ~70-100 MB (normal for self-contained)

**You're all set!** Your self-contained build doesn't require .NET to be installed on target PCs.
