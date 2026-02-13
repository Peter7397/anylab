# Quick Build Guide - Visual Studio

## Building Self-Contained Executable with Visual Studio

Since the project is already configured for self-contained deployment, building is simple!

---

## Method 1: Using Publish (Recommended - Easiest)

### Step-by-Step:

1. **Open Visual Studio 2022**
   - Launch Visual Studio
   - Open the solution: `File` → `Open` → `Project/Solution`
   - Navigate to and select `Remotecollect.sln`

2. **Right-click on the `Remotecollect` project** in Solution Explorer
   - Select **Publish**

3. **Create a New Publish Profile** (if you don't have one)
   - Click **New** or **+ New**
   - Choose **Folder** as publish target
   - Click **Next**

4. **Configure Publish Location**
   - Choose **Folder** again
   - Set output path (default is fine): `bin\Release\net8.0-windows\win-x64\publish`
   - Click **Next**

5. **Review Settings** (should already be configured)
   - ✅ **Deployment mode:** Self-contained
   - ✅ **Target runtime:** win-x64
   - ✅ **File publish options:**
     - ✅ Produce single file
     - ✅ Enable ReadyToRun compilation
   - Click **Finish**

6. **Publish**
   - Click **Publish** button
   - Wait for build to complete
   - You'll see: "Publish succeeded"

7. **Find Your Executable**
   - Navigate to: `bin\Release\net8.0-windows\win-x64\publish\`
   - You'll find: `Remotecollect.exe` (~70-100 MB - this is normal!)

---

## Method 2: Using Build Menu (Alternative)

### Step-by-Step:

1. **Open Visual Studio 2022**
   - Open `Remotecollect.sln`

2. **Set Build Configuration**
   - Go to: `Build` → `Configuration Manager`
   - Set **Active solution configuration:** `Release`
   - Set **Active solution platform:** `x64` (or `Any CPU`)
   - Click **Close**

3. **Publish via Command**
   - Right-click on `Remotecollect` project
   - Select **Publish**
   - If you already have a profile, just click **Publish**
   - If not, follow Method 1 steps 3-6 above

---

## Method 3: Using Command Line from Visual Studio

1. **Open Developer Command Prompt**
   - In Visual Studio: `Tools` → `Command Line` → `Developer Command Prompt`
   - Or: Start Menu → `Developer Command Prompt for VS 2022`

2. **Navigate to Project**
   ```bash
   cd C:\path\to\Remotecollect
   ```

3. **Publish**
   ```bash
   dotnet publish -c Release -r win-x64
   ```

4. **Find Output**
   - Location: `bin\Release\net8.0-windows\win-x64\publish\Remotecollect.exe`

---

## What You Get

After building, you'll have:

```
bin\Release\net8.0-windows\win-x64\publish\
  └── Remotecollect.exe  (70-100 MB - includes .NET runtime)
```

**Important:**
- ✅ This `.exe` is **self-contained** - no .NET installation needed on target PC
- ✅ Just copy this file to any Windows PC and run as Administrator
- ✅ The large file size is normal (includes .NET 8.0 runtime)

---

## Including PSExec (Required)

After building, you need to add PSExec:

1. **Download PSExec**
   - From: https://docs.microsoft.com/en-us/sysinternals/downloads/psexec
   - Extract the ZIP file

2. **Copy PSExec to Publish Folder**
   - Copy `PSExec64.exe` (recommended) or `PSExec.exe` 
   - Paste into: `bin\Release\net8.0-windows\win-x64\publish\`
   - You only need ONE file (either PSExec64.exe OR PSExec.exe)

3. **Final Distribution Folder**
   ```
   publish\
     ├── Remotecollect.exe
     └── PSExec64.exe  (or PSExec.exe)
   ```

---

## Testing Your Build

1. **Navigate to publish folder**
2. **Right-click** `Remotecollect.exe`
3. **Select** "Run as administrator"
4. **Verify** the application starts correctly

---

## Troubleshooting

### Issue: "Publish" option is grayed out or missing

**Solution:**
- Ensure you have `.NET desktop development` workload installed
- Go to: `Tools` → `Get Tools and Features`
- Check: `.NET desktop development` workload
- Click **Modify** to install

### Issue: Build fails with errors

**Solution:**
- Right-click solution → `Restore NuGet Packages`
- Or: `Tools` → `NuGet Package Manager` → `Package Manager Console`
- Run: `dotnet restore`
- Then try building again

### Issue: Executable is very large

**Solution:**
- This is **normal** for self-contained builds
- The file includes the entire .NET 8.0 runtime
- Typical size: 70-100 MB for x64
- This is expected and correct!

---

## Quick Checklist

- [ ] Opened `Remotecollect.sln` in Visual Studio
- [ ] Right-clicked project → **Publish**
- [ ] Created/selected publish profile
- [ ] Verified settings: Self-contained, win-x64, Single file
- [ ] Clicked **Publish**
- [ ] Build succeeded
- [ ] Copied PSExec64.exe to publish folder
- [ ] Tested the executable

---

**That's it!** Your self-contained executable is ready to distribute. No .NET installation needed on target PCs!
