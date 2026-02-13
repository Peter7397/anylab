# Build Guide - Multi-Method Remote Log Collector

## Prerequisites

### Required Software

1. **.NET 8.0 SDK** (not just Runtime)
   - Download from: https://dotnet.microsoft.com/download/dotnet/8.0
   - Choose the SDK (not Runtime) for your Windows version
   - Verify installation:
     ```bash
     dotnet --version
     ```
     Should show version 8.0.x or higher

2. **Windows Operating System**
   - Windows 10/11 or Windows Server 2016/2019/2022
   - This is a Windows Forms application and cannot be built on macOS/Linux

3. **Visual Studio (Optional but Recommended)**
   - Visual Studio 2022 Community/Professional/Enterprise
   - Or Visual Studio Code with C# extension
   - Or any IDE that supports .NET development

## Building the Project

### Method 1: Using Command Line (Recommended)

1. **Open Command Prompt or PowerShell**
   - Press `Win + R`, type `cmd` or `powershell`, press Enter
   - **Important:** For final deployment, run as Administrator

2. **Navigate to Project Directory**
   ```bash
   cd C:\path\to\Anylab103\Remotecollect
   ```
   Or if you're already in the project root:
   ```bash
   cd Remotecollect
   ```

3. **Restore NuGet Packages**
   ```bash
   dotnet restore
   ```
   This downloads the required packages:
   - System.DirectoryServices
   - System.Management.Automation

4. **Build the Project**
   ```bash
   dotnet build
   ```
   
   For Release build (optimized):
   ```bash
   dotnet build -c Release
   ```

5. **Verify Build Success**
   - You should see: `Build succeeded.`
   - No errors should be displayed

6. **Run the Application**
   ```bash
   dotnet run
   ```
   
   Or run the compiled executable:
   ```bash
   dotnet run --project Remotecollect.csproj
   ```

### Method 2: Using Visual Studio

1. **Open Visual Studio 2022**

2. **Open Solution**
   - File → Open → Project/Solution
   - Navigate to `Remotecollect.sln`
   - Click Open

3. **Restore Packages**
   - Visual Studio will automatically restore NuGet packages
   - Or manually: Right-click solution → Restore NuGet Packages

4. **Build Solution**
   - Press `Ctrl + Shift + B`
   - Or: Build → Build Solution
   - Or: Right-click solution → Build

5. **Run Application**
   - Press `F5` to run with debugging
   - Or `Ctrl + F5` to run without debugging
   - **Important:** Right-click project → Properties → Debug → Check "Run as administrator"

### Method 3: Using Visual Studio Code

1. **Install C# Extension**
   - Open VS Code
   - Extensions → Search "C#" → Install "C# Dev Kit" or "C#"

2. **Open Folder**
   - File → Open Folder
   - Select the `Remotecollect` directory

3. **Restore and Build**
   - Press `Ctrl + Shift + P`
   - Type: `.NET: Restore Packages`
   - Then: `.NET: Build`

4. **Run**
   - Press `F5` to debug
   - Or use terminal: `dotnet run`

## Creating a Standalone Executable

### Publish as Self-Contained Executable (✅ Already Configured!)

**Good News:** The project file is already configured for self-contained deployment! This means:
- ✅ The .NET 8.0 runtime is **bundled** with your application
- ✅ Target PCs **do NOT need** to install .NET 8.0 separately
- ✅ Creates a single executable file (larger size, but standalone)

**To build the self-contained executable:**

```bash
dotnet publish -c Release -r win-x64
```

**Or with explicit flags (same result):**
```bash
dotnet publish -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -p:IncludeNativeLibrariesForSelfExtract=true -p:PublishReadyToRun=true
```

**Output Location:**
- Executable will be in: `bin\Release\net8.0-windows\win-x64\publish\`
- Look for `Remotecollect.exe`
- **Note:** The `.exe` will be large (~70-100 MB) because it includes the .NET runtime. This is normal for self-contained builds.

### Including PSExec with Your Application

To bundle PSExec with your application:

1. **Download PSTools**
   - Download from: https://docs.microsoft.com/en-us/sysinternals/downloads/psexec
   - Extract the ZIP file (contains multiple tools including PSExec)

2. **Choose PSExec Version**
   - **PSExec64.exe** (Recommended for 64-bit Windows) - Native 64-bit, faster performance
   - **PSExec.exe** (32-bit, more compatible) - Works on both 32-bit and 64-bit Windows
   - **Recommendation:** Use `PSExec64.exe` if building for 64-bit Windows (most common scenario)

3. **Copy PSExec to Output Directory**
   - After publishing, copy **only** `PSExec64.exe` (or `PSExec.exe`) to the same folder as `Remotecollect.exe`
   - **You only need ONE file** - either PSExec64.exe OR PSExec.exe, not both
   - The application will automatically find and use either version (prefers PSExec64.exe on 64-bit systems)
   - **Important:** PSExec only needs to be on the collector machine (where Remotecollect.exe runs), NOT on target PCs
   - This allows users to use Method 3 (PSExec) without installing anything on target machines

3. **Distribution Package Structure**
   ```
   Remotecollect_Release\
     ├── Remotecollect.exe
     ├── PSExec64.exe              (or PSExec.exe - you only need one)
     └── [other runtime files if not single-file]
   ```
   
   **Note:** You only need ONE PSExec file:
   - `PSExec64.exe` - Recommended for 64-bit Windows (faster)
   - `PSExec.exe` - Use if you need 32-bit compatibility

### Build for Different Architectures

**x64 (64-bit) - Recommended:**
```bash
dotnet publish -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true
```

**x86 (32-bit):**
```bash
dotnet publish -c Release -r win-x86 --self-contained true -p:PublishSingleFile=true
```

**ARM64:**
```bash
dotnet publish -c Release -r win-arm64 --self-contained true -p:PublishSingleFile=true
```

## Troubleshooting Build Issues

### Issue: "dotnet command not found"

**Solution:**
- Install .NET 8.0 SDK
- Add to PATH if not automatically added
- Restart command prompt/PowerShell

### Issue: "Package restore failed"

**Solution:**
```bash
# Clear NuGet cache
dotnet nuget locals all --clear

# Restore again
dotnet restore
```

### Issue: "Cannot find System.DirectoryServices"

**Solution:**
- Ensure you're using .NET 8.0 SDK
- This package is included in .NET 8.0
- Try: `dotnet add package System.DirectoryServices`

### Issue: "System.Management.Automation not found"

**Solution:**
```bash
# Add the package explicitly
dotnet add package System.Management.Automation --version 7.4.0
```

### Issue: "Windows Forms not available"

**Solution:**
- Ensure `TargetFramework` is `net8.0-windows` (not just `net8.0`)
- Check `UseWindowsForms` is set to `true` in .csproj

### Issue: Build succeeds but app won't run

**Solution:**
- Ensure running as Administrator
- Check Windows Event Viewer for errors
- For self-contained builds, .NET Runtime is included (no installation needed on target machine)

## Build Output Locations

### Development Build
- Location: `bin\Debug\net8.0-windows\`
- Contains: `Remotecollect.exe`, DLLs, config files

### Release Build
- Location: `bin\Release\net8.0-windows\`
- Contains: Optimized executable and dependencies

### Published Build
- Location: `bin\Release\net8.0-windows\win-x64\publish\`
- Contains: All files needed to run (self-contained)

## Deployment Checklist

Before deploying to other machines:

- [ ] Build in Release configuration with self-contained option
- [ ] Copy PSExec.exe to the same folder as Remotecollect.exe
- [ ] Test on a non-development machine
- [ ] Verify administrator privileges work
- [ ] Test domain scanning functionality
- [ ] Test log collection with at least one PC
- [ ] Verify all three connection methods (if possible)
- [ ] Include user guides (USER_GUIDE_EN.md, USER_GUIDE_CN.md)
- [ ] Verify PSExec works from application directory
- [ ] Document any custom configuration needed

## Quick Build Commands Reference

```bash
# Restore packages
dotnet restore

# Build Debug
dotnet build

# Build Release
dotnet build -c Release

# Run
dotnet run

# Publish self-contained single file
dotnet publish -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true

# Clean build artifacts
dotnet clean
```

## Next Steps After Building

1. **Test the Application**
   - Run as Administrator
   - Test domain scanning
   - Test log collection on a test PC

2. **Distribute the Application**
   - Copy the `publish` folder contents
   - Or distribute the single executable
   - Include user guides

3. **Configure Target Environment**
   - Ensure target PCs have WinRM enabled (for Method 2)
   - Install PSExec if using Method 3
   - Verify network connectivity

---

**Note:** This application must be built and run on Windows. It cannot be built on macOS or Linux due to Windows Forms dependency.
