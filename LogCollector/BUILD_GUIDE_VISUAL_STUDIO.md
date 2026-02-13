# Build Guide - Visual Studio

This guide covers building the Remotecollect application using Visual Studio 2022.

## Prerequisites

- **Visual Studio 2022** (Community, Professional, or Enterprise)
- **.NET 8.0 SDK** (included with Visual Studio 2022 or download separately)
- **PSExec.exe** (for bundling with the application)

## Step 1: Open the Solution

1. Launch **Visual Studio 2022**
2. Click **File** → **Open** → **Project/Solution**
3. Navigate to the project folder and select `Remotecollect.sln`
4. Click **Open**

## Step 2: Configure Build Settings

### ✅ Self-Contained Build (Already Configured!)

**Good News:** The project file is already configured for self-contained deployment! This means:
- ✅ The .NET 8.0 runtime is **bundled** with your application
- ✅ Target PCs **do NOT need** to install .NET 8.0 separately
- ✅ Creates a single executable file (larger size, but standalone)

### About .NET Versions

**Current:** .NET 8.0 (Recommended)
- Latest stable version
- Better performance
- Long-term support (LTS) until November 2026
- Self-contained build size: ~70-100 MB

**Alternative:** .NET 6.0 or 7.0
- If you prefer an older version, change `<TargetFramework>net8.0-windows</TargetFramework>` to:
  - `net7.0-windows` (support until May 2024)
  - `net6.0-windows` (LTS until November 2024)
- Self-contained build size: ~60-90 MB
- **Recommendation:** Stick with .NET 8.0 for best support

### Build Methods

#### Method 1: Using Visual Studio Publish (Recommended)

1. **Right-click** on the `Remotecollect` project in Solution Explorer
2. Select **Publish**
3. Click **New** to create a new publish profile
4. Choose **Folder** as the publish target
5. Click **Next**
6. Choose **Folder** again and specify output path (e.g., `bin\Release\Publish`)
7. Click **Next**
8. Verify settings (should already be configured):
   - **Deployment mode:** Self-contained ✅
   - **Target runtime:** win-x64 ✅
   - **File publish options:**
     - ✅ **Produce single file** (already enabled)
     - ✅ **Enable ReadyToRun compilation** (already enabled)
9. Click **Finish**, then click **Publish**

#### Method 2: Using Command Line (Alternative)

Open **Developer Command Prompt for VS 2022** and run:

```bash
cd C:\path\to\Remotecollect
dotnet publish -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -p:IncludeNativeLibrariesForSelfExtract=true -p:PublishReadyToRun=true
```

**Note:** The project file already has these settings, so you can also just run:
```bash
dotnet publish -c Release -r win-x64
```

## Step 3: Build Output Location

After publishing, your self-contained executable will be located at:

```
bin\Release\net8.0-windows\win-x64\publish\Remotecollect.exe
```

**Important Notes:**
- The `.exe` file will be **large** (~70-100 MB) because it includes the .NET runtime
- This is **normal** for self-contained builds
- The target PC can run this `.exe` **without installing .NET 8.0**
- You can copy just the `.exe` file to the target PC (it's self-contained)

## Step 5: Include PSExec

1. **Download PSTools**
   - Download from: https://docs.microsoft.com/en-us/sysinternals/downloads/psexec
   - Extract the ZIP file (contains multiple tools)

2. **Choose PSExec Version**
   - **PSExec64.exe** (Recommended for 64-bit Windows) - Faster, native 64-bit
   - **PSExec.exe** (32-bit, more compatible) - Works on both 32-bit and 64-bit Windows
   - **Recommendation:** Use `PSExec64.exe` if you're building for 64-bit Windows (most common)

3. **Copy PSExec to Output Folder**
   - Navigate to your publish output folder:
     - If using Publish: `bin\Release\Publish\` (or your custom path)
     - If using Build: `bin\Release\net8.0-windows\win-x64\publish\`
   - Copy **only** `PSExec64.exe` (or `PSExec.exe`) to this folder
   - **You only need ONE file** - either PSExec64.exe OR PSExec.exe, not both
   - Ensure the PSExec file is in the same folder as `Remotecollect.exe`
   - **Note:** The application will automatically find and use either version

## Step 6: Verify Build Output

Your distribution folder should contain:

```
Publish\
  ├── Remotecollect.exe          (self-contained executable)
  ├── PSExec64.exe               (bundled tool - 64-bit version, recommended)
  └── [other runtime files if not single-file]
```

**Note:** 
- If you used single-file publish, you should only see `Remotecollect.exe` and `PSExec64.exe` (or `PSExec.exe`)
- You only need ONE PSExec file - either `PSExec64.exe` (recommended) or `PSExec.exe` (for compatibility)

## Step 7: Test the Build

1. **Navigate** to the publish folder
2. **Right-click** `Remotecollect.exe`
3. Select **Run as administrator**
4. Verify the application starts correctly
5. Test domain scanning and log collection

## Build Configurations

### Release Build (Production)

- **Configuration:** Release
- **Optimizations:** Enabled
- **Debug symbols:** Optional
- **Use for:** Distribution to end users

### Debug Build (Development)

- **Configuration:** Debug
- **Optimizations:** Disabled
- **Debug symbols:** Included
- **Use for:** Development and testing

## Troubleshooting

### Issue: "Publish" option not available

**Solution:**
- Ensure you have the .NET desktop development workload installed
- Install via: **Tools** → **Get Tools and Features** → **.NET desktop development**

### Issue: Build fails with missing packages

**Solution:**
- Right-click solution → **Restore NuGet Packages**
- Or: **Tools** → **NuGet Package Manager** → **Package Manager Console**
- Run: `dotnet restore`

### Issue: Single file is very large

**Solution:**
- This is normal for self-contained builds (includes .NET Runtime)
- Typical size: 60-100 MB for x64
- Consider trimming unused code (enable in publish settings)

### Issue: Application won't run on another PC

**Solution:**
- Ensure you built with `--self-contained true`
- Verify all files are in the same folder
- Check Windows Defender/antivirus isn't blocking it
- Ensure target PC is Windows 10/11 or Windows Server 2016+

## Quick Reference: Publish Settings

| Setting | Value | Description |
|---------|-------|-------------|
| Deployment mode | Self-contained | Includes .NET Runtime |
| Target runtime | win-x64 | 64-bit Windows (or win-x86, win-arm64) |
| Produce single file | ✅ | Creates one executable |
| Enable ReadyToRun | ✅ (optional) | Faster startup |
| Trim unused code | ✅ (optional) | Smaller file size |

## Distribution Checklist

Before distributing:

- [ ] Built in Release configuration
- [ ] Used self-contained deployment
- [ ] Created single-file executable
- [ ] Copied PSExec.exe to output folder
- [ ] Tested on a clean Windows machine
- [ ] Verified administrator privileges work
- [ ] Tested domain scanning
- [ ] Tested log collection
- [ ] Included user guides (optional)

## Next Steps

1. **Package for Distribution**
   - Zip the entire publish folder
   - Include user guides (USER_GUIDE_EN.md, USER_GUIDE_CN.md)
   - Name it: `Remotecollect_v1.0.0.zip`

2. **Distribute**
   - Share the zip file with end users
   - Users only need to extract and run `Remotecollect.exe` as administrator
   - No additional installation required

---

**Last Updated:** December 2024
