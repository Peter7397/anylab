Visual Studio Installation Guide

This guide will help you install Visual Studio on a new PC for developing the Remotecollect application.

Step 1: Download Visual Studio

1. Go to the Visual Studio website:
   - Visit: https://visualstudio.microsoft.com/downloads/
   - Or sign in to your Visual Studio subscription portal: https://my.visualstudio.com/

2. Choose Your Edition:
   - If you have a subscription, you can download:
     - Visual Studio Professional (recommended for most developers)
     - Visual Studio Enterprise (includes advanced features)
   - If you don't have a subscription, you can use:
     - Visual Studio Community (free, for individual developers and small teams)

3. Download the Installer:
   - Click "Download" for your chosen edition
   - Run the downloaded installer (e.g., `vs_professional.exe` or `vs_enterprise.exe`)
   - The installer is small (~3-5 MB) and will download components as needed

Step 2: Run the Visual Studio Installer

1. Launch the installer
2. If prompted by User Account Control (UAC), click "Yes"
3. You may be asked to sign in with your Microsoft account (required for subscription activation)

Step 3: Select Workloads

The installer will show you different "workloads" (groups of features). For the Remotecollect project, you need:

Required Workload:

1. .NET desktop development
   - This workload includes:
     - .NET Framework 4.8 targeting pack
     - .NET Framework 4.8 SDK
     - Windows Forms designer
     - All necessary tools for building Windows Forms applications
   
   To select it:
   - Check the box next to ".NET desktop development"
   - This will automatically select the required components

Optional but Recommended:

2. .NET Multi-platform App UI development (optional)
   - Only needed if you plan to work on other .NET projects
   - Not required for this project

3. Desktop development with C++ (optional)
   - Only needed if you work with C++ projects
   - Not required for this project

Step 4: Individual Components (Verify)

After selecting the workload, you can verify individual components. The following should be automatically selected:

Required Components (auto-selected with .NET desktop development workload):
- .NET Framework 4.8 targeting pack
- .NET Framework 4.8 SDK
- Windows Forms designer
- Windows 10/11 SDK (latest version)
- MSBuild
- NuGet package manager

Step 5: Installation Location

1. Choose Installation Location (optional):
   - Default location is usually fine: `C:\Program Files\Microsoft Visual Studio\2022\Professional` (or Enterprise/Community)
   - You can change this if you have space constraints on C: drive

2. Click "Install" or "Modify" (if updating existing installation)

Step 6: Wait for Installation

1. The installer will download and install components
2. This may take 30-60 minutes depending on:
   - Your internet speed
   - Selected workloads
   - System performance
3. You can continue using your PC during installation (it will be slower)

Step 7: Sign In and Activate (For Subscription Users)

1. After installation, launch Visual Studio
2. Sign in with your Microsoft account that has the Visual Studio subscription
3. Visual Studio will automatically activate your subscription
4. You may need to accept license terms

Step 8: Verify Installation

1. Launch Visual Studio
2. Check that you can create/open projects:
   - File → New → Project
   - You should see "Windows Forms App (.NET Framework)" template
3. Verify .NET Framework 4.8 is available:
   - Create a test project
   - Right-click project → Properties
   - Check "Target framework" dropdown - should include ".NET Framework 4.8"

Step 9: Open Your Remotecollect Project

1. In Visual Studio, go to: File → Open → Project/Solution
2. Navigate to your project folder
3. Select `Remotecollect.sln`
4. Click "Open"
5. Visual Studio will restore NuGet packages automatically (first time may take a few minutes)

System Requirements

Minimum Requirements:
- Windows 10 version 1903 or higher (64-bit)
- Windows 11 (64-bit)
- Windows Server 2019 or later
- 4 GB RAM (8 GB recommended)
- 20 GB free disk space (40 GB recommended for full installation)
- Internet connection for initial download

Recommended Requirements:
- Windows 10/11 (64-bit)
- 16 GB RAM or more
- SSD with 50+ GB free space
- Fast internet connection

Troubleshooting

Issue: Installer won't start or crashes

Solution:
- Run installer as Administrator (right-click → Run as administrator)
- Check Windows Update is current
- Temporarily disable antivirus/firewall
- Check available disk space (need at least 20 GB free)

Issue: Can't find .NET Framework 4.8 in project properties

Solution:
- Ensure ".NET desktop development" workload is installed
- Go to: Tools → Get Tools and Features
- Check ".NET desktop development" workload
- Click "Modify" to install missing components
- Restart Visual Studio

Issue: Subscription activation fails

Solution:
- Verify you're signed in with the correct Microsoft account
- Check your subscription status at: https://my.visualstudio.com/
- Ensure your subscription is active
- Try signing out and signing back in to Visual Studio

Issue: Project won't build after opening

Solution:
- Right-click solution → Restore NuGet Packages
- Go to: Tools → NuGet Package Manager → Package Manager Console
- Run: `dotnet restore`
- Check Output window for specific error messages
- Ensure all project files are present (especially `Remotecollect.csproj`)

Issue: Missing icon file error

Solution:
- Ensure `log8.ico` is in the LogCollector folder
- In Visual Studio, right-click `log8.ico` in Solution Explorer
- Select "Properties"
- Set "Build Action" to "EmbeddedResource"
- Rebuild the project

Quick Installation Checklist

Before Installation:
- [ ] Verified system meets requirements
- [ ] Have at least 20 GB free disk space
- [ ] Have stable internet connection
- [ ] Have Microsoft account credentials ready (for subscription)

During Installation:
- [ ] Downloaded Visual Studio installer
- [ ] Ran installer as administrator
- [ ] Selected ".NET desktop development" workload
- [ ] Started installation
- [ ] Waited for installation to complete (30-60 minutes)

After Installation:
- [ ] Launched Visual Studio
- [ ] Signed in with subscription account
- [ ] Verified subscription activation
- [ ] Opened Remotecollect.sln project
- [ ] Verified project loads without errors
- [ ] Tested building the project (Build → Rebuild Solution)

Next Steps

After Visual Studio is installed:

1. Open Your Project:
   - File → Open → Project/Solution
   - Select `Remotecollect.sln`

2. Restore Packages:
   - Right-click solution → Restore NuGet Packages
   - Wait for packages to download

3. Build the Project:
   - Build → Rebuild Solution
   - Check Output window for any errors

4. Set Up Icon (if needed):
   - Ensure `log8.ico` is in the project folder
   - Add it to the project if missing: Right-click project → Add → Existing Item
   - Set Build Action to "EmbeddedResource"

5. Configure Build:
   - The project is already configured for .NET Framework 4.8
   - You can build using: Build → Build Solution (Debug) or Build → Rebuild Solution (Release)

For detailed build instructions, see:
- BUILD_GUIDE_VISUAL_STUDIO.md
- QUICK_BUILD_VISUAL_STUDIO.md

Additional Resources

- Visual Studio Documentation: https://docs.microsoft.com/visualstudio/
- Visual Studio Subscriptions: https://my.visualstudio.com/
- .NET Framework Downloads: https://dotnet.microsoft.com/download/dotnet-framework
- Visual Studio Community: https://visualstudio.microsoft.com/vs/community/

Last Updated: February 2026
