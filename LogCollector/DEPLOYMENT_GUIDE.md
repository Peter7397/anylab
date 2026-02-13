# Deployment Guide - What to Copy to Target PC

## Framework-Dependent Build Deployment

Since the application is built as **framework-dependent** (not self-contained), here's what you need:

---

## Files to Copy

### 1. Main Application Files

After building in **Release** mode, copy the entire output folder:

**Location:** `bin\Release\net6.0-windows\`

**Files to copy:**
```
Remotecollect.exe          (Main executable)
Remotecollect.dll          (Application library)
Remotecollect.deps.json    (Dependency manifest)
Remotecollect.runtimeconfig.json  (Runtime configuration)
```

**Plus all .dll dependencies:**
- `System.DirectoryServices.dll`
- `System.Management.Automation.dll`
- Other dependency DLLs (NuGet packages)

### 2. PSExec (Required)

Copy `PSExec64.exe` (or `PSExec.exe`) to the same folder as `Remotecollect.exe`

**Download:** https://docs.microsoft.com/en-us/sysinternals/downloads/psexec

---

## Quick Copy Method (Recommended)

### Option 1: Copy Entire Output Folder

1. **Build the project in Release mode**
   ```bash
   dotnet build -c Release
   ```

2. **Navigate to output folder:**
   ```
   bin\Release\net6.0-windows\
   ```

3. **Copy the entire folder contents** to target PC:
   - All `.exe` files
   - All `.dll` files
   - All `.json` files
   - `PSExec64.exe` (add this file)

### Option 2: Publish and Copy

1. **Publish the application:**
   ```bash
   dotnet publish -c Release
   ```

2. **Copy from:**
   ```
   bin\Release\net6.0-windows\publish\
   ```

3. **This folder contains all required files** - copy everything to target PC

---

## Target PC Requirements

### 1. .NET 6.0 Desktop Runtime (Required)

**Must be installed on target PC before running the application.**

**If not installed:**
- The application will detect it on startup
- Will prompt you to download and install
- Download from: https://dotnet.microsoft.com/download/dotnet/6.0/runtime
- Choose: **Desktop Runtime 6.0.x** for Windows x64

**To check if installed:**
```cmd
dotnet --list-runtimes
```

Look for: `Microsoft.WindowsDesktop.App 6.0.x`

### 2. Windows Version

- Windows 10 (version 1607 or later)
- Windows 11
- Windows Server 2016/2019/2022

### 3. Administrator Privileges

- Must run as **Domain Administrator**
- Right-click → "Run as administrator"

---

## Deployment Steps

### Step 1: Build the Application

```bash
dotnet publish -c Release
```

### Step 2: Locate Output Files

Go to: `bin\Release\net6.0-windows\publish\`

### Step 3: Add PSExec

Copy `PSExec64.exe` to the publish folder

### Step 4: Copy to Target PC

**Option A: Copy entire folder**
- Copy the entire `publish` folder to target PC
- Keep all files together in one folder

**Option B: Create deployment package**
- Zip the entire `publish` folder
- Extract on target PC
- Keep all files in the same folder

### Step 5: Verify Target PC Has .NET 6.0

On target PC, run:
```cmd
dotnet --list-runtimes
```

If `.NET 6.0 Desktop Runtime` is not found:
- Install it from: https://dotnet.microsoft.com/download/dotnet/6.0/runtime
- Or let the application prompt you (it will on first run)

### Step 6: Run the Application

1. Navigate to the folder on target PC
2. Right-click `Remotecollect.exe`
3. Select "Run as administrator"
4. Click "Yes" when prompted

---

## Folder Structure on Target PC

```
C:\Remotecollect\
  ├── Remotecollect.exe
  ├── Remotecollect.dll
  ├── Remotecollect.deps.json
  ├── Remotecollect.runtimeconfig.json
  ├── System.DirectoryServices.dll
  ├── System.Management.Automation.dll
  ├── [other dependency DLLs]
  └── PSExec64.exe
```

**Important:** All files must be in the same folder!

---

## Minimum Files Required

**Absolute minimum** (if you want to copy selectively):

1. `Remotecollect.exe` - Main executable
2. `Remotecollect.dll` - Application code
3. `Remotecollect.deps.json` - Dependency information
4. `Remotecollect.runtimeconfig.json` - Runtime configuration
5. All `.dll` files in the output folder (dependencies)
6. `PSExec64.exe` - For Method 3 fallback

**Recommendation:** Copy everything from the `publish` folder to avoid missing dependencies.

---

## Quick Checklist

Before deploying to target PC:

- [ ] Built application in Release mode
- [ ] Located output folder: `bin\Release\net6.0-windows\publish\`
- [ ] Added `PSExec64.exe` to the folder
- [ ] Copied all files to target PC
- [ ] Verified target PC has .NET 6.0 Desktop Runtime installed
- [ ] Tested running as administrator

---

## Troubleshooting

### "Application won't start"

1. **Check .NET 6.0 is installed:**
   ```cmd
   dotnet --list-runtimes
   ```

2. **Verify all files are in the same folder**

3. **Check you're running as administrator**

4. **Look for missing DLL errors** - if you see errors about missing DLLs, copy all files from the publish folder

### "Missing dependency" errors

- Copy **all files** from the `publish` folder, not just the .exe
- Framework-dependent builds require all DLL dependencies

### "PSExec not found"

- Ensure `PSExec64.exe` is in the same folder as `Remotecollect.exe`
- The application will look for it in the same directory

---

## Distribution Package

**Recommended structure for distribution:**

```
Remotecollect_v1.0.0.zip
  └── Remotecollect\
      ├── Remotecollect.exe
      ├── Remotecollect.dll
      ├── [all other DLLs and JSON files]
      ├── PSExec64.exe
      └── README.txt (optional - installation instructions)
```

**README.txt content:**
```
Remotecollect - Remote Log Collector

REQUIREMENTS:
- .NET 6.0 Desktop Runtime must be installed
- Domain Administrator privileges

INSTALLATION:
1. Extract all files to a folder (e.g., C:\Remotecollect)
2. Ensure .NET 6.0 Desktop Runtime is installed
3. Right-click Remotecollect.exe → Run as administrator

If .NET 6.0 is not installed, the application will prompt you to download it.
```

---

## Summary

**What to copy:**
- ✅ Entire contents of `bin\Release\net6.0-windows\publish\` folder
- ✅ `PSExec64.exe` (add to the same folder)

**What's needed on target PC:**
- ✅ .NET 6.0 Desktop Runtime (installed separately)
- ✅ Windows 10/11 or Windows Server 2016+
- ✅ Domain Administrator privileges

**File size:** ~5-10 MB (much smaller than self-contained!)
