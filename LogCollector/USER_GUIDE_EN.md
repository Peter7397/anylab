Multi-Method Remote Log Collector - User Guide (English)

Overview

The Multi-Method Remote Log Collector is a Windows Forms administrative tool designed to scan Active Directory domains and collect Agilent/OpenLab log files from multiple remote PCs using a robust three-tier failover connection strategy.

System Requirements

- Operating System: Windows 10/11 or Windows Server 2016/2019/2022
- Privileges: Domain Administrator account
- Network: Access to Active Directory domain and target computers
- Required: .NET Framework 4.8 or higher must be installed (.NET Framework 4.8 is built into Windows 10 version 1809 and later, Windows 11, and Windows Server 2019/2022)
- Note: PSExec is included with the application (only needed on the collector machine, not on target PCs)

Quick Start

1. Run the Application
   - Right-click `Remotecollect.exe`
   - Select "Run as administrator"
   - Click "Yes" when prompted

2. Use the Application
   - Click "Scan Domain" to discover PCs
   - Select the PCs you want to collect logs from
   - Click "Collect Logs" to start collection
   - Monitor progress in the console log

Note: .NET Framework 4.8 or higher must be installed. .NET Framework 4.8 is built into Windows 10 version 1809 and later, Windows 11, and Windows Server 2019/2022.

Getting Started

Prerequisites

1. Domain Administrator Account - You must have Domain Administrator privileges:
   - If you are logged in as a Domain Administrator, the application will run directly
   - If you are not a Domain Administrator, the application will prompt you to enter Domain Administrator credentials
   - Required privileges:
     - Domain Administrator account
     - Active Directory read access
     - Network administrative share access (C$)
2. .NET Framework 4.8 or higher - Must be installed on the PC running this application:
   - .NET Framework 4.8 is built into Windows 10 version 1809 and later, Windows 11, and Windows Server 2019/2022
   - For older Windows versions, .NET Framework 4.8 must be installed separately
   - Download from: https://dotnet.microsoft.com/download/dotnet-framework/net48
3. PSExec - Included in the application folder for Method 3 fallback (only needed on the collector machine)

Running the Application

1. Locate the Executable
   - The application file is named `Remotecollect.exe`
   - It may be in a folder with other required files

2. Run the Application
   - Right-click on `Remotecollect.exe`
   - Select "Run as administrator"   - Click "Yes" when prompted by User Account Control (UAC)

If you are not a Domain Administrator:   - The application will display a credential dialog
   - Enter your Domain Administrator credentials:
     - Domain: Your domain name (pre-filled from current environment)
     - Username: Domain Administrator username
     - Password: Domain Administrator password
   - Click "OK" to validate credentials
   - The application will verify your credentials before proceeding

Important: This application requires Domain Administrator privileges. If credentials cannot be validated, the application will exit.


User Interface Overview

The application interface consists of:

1. Application Icon - The application features a custom icon embedded in the executable that represents the remote log collection tool. The icon appears in:
   - Windows Explorer (as the file icon for Remotecollect.exe)
   - Application window title bar
   - Windows taskbar when the application is running
   - The icon is embedded in the executable, so no separate icon file is needed for deployment
2. Scan Domain Button - Initiates Active Directory domain scan (disabled after successful scan)
3. Collect Logs Button - Starts log collection from selected PCs
4. Manual PC Input - Text field and "Add PC" button to manually add PCs by hostname or IP address
   - Located below the Scan Domain and Collect Logs buttons
   - Enter hostname or IP address, then click "Add PC" to add to the list
5. PC List (CheckedListBox) - Displays discovered computers with checkboxes for selection
   - The localhost (host machine) is always displayed at the top with `[localhost]` indicator
   - Localhost is always present, even if the machine is not in a domain or domain scan fails
   - Other computers are listed alphabetically below localhost
6. Progress Bar - Shows collection progress across multiple PCs
7. Status Label - Displays current operation status
8. Console Log (RichTextBox) - Real-time logging with color-coded messages:
   - Cyan - Informational messages
   - Green - Success messages
   - Yellow - Warning messages
   - Red - Error messages

Usage Instructions

Step 1: Scan Active Directory Domain or Add PCs Manually

On First Launch:
- The localhost (host machine) is always present at the top of the PC list with `[localhost]` indicator
- If you have previously scanned the domain, saved scan results will be automatically loaded
- The status bar will show: "Loaded X computers from saved scan results (scanned on YYYY-MM-DD HH:MM:SS)"
- You can proceed immediately or click "Scan Domain" to refresh the list

To Perform a New Domain Scan:
1. Click the "Scan Domain" button
2. The application will:
   - Query Active Directory for all computer objects (if machine is in a domain)
   - Resolve hostnames and IP addresses
   - Display discovered computers in the PC list
   - Always ensure localhost is at the top with `[localhost]` indicator
   - Save scan results to `DomainScanResults.json` (same folder as executable)
3. Wait for the scan to complete (progress bar will show activity)
4. Review the console log for scan results
5. The "Scan Domain" button will be disabled after successful scan

Note: The scan may take several minutes depending on the size of your domain. Scan results are automatically saved and will be loaded on next startup.

Note: If your machine is not in a domain, the domain scan will return no additional computers, but localhost will still be available. You can manually add PCs using the Manual PC Input field.

Manual PC Input:
- Enter a hostname or IP address in the "Manual PC (hostname or IP):" field
- Click the "Add PC" button to add it to the PC list
- Manually added PCs are saved to `DomainScanResults.json` and will be loaded on next startup
- You can add multiple PCs manually, one at a time

Saved Scan Results

The application automatically saves domain scan results to `DomainScanResults.json` in the same folder as the executable. This allows you to:

- Skip re-scanning: On next startup, saved results are automatically loaded
- Faster startup: Begin log collection immediately without waiting for a new scan
- Offline access: View previously scanned computers even when not connected to the domain
- Refresh option: Click "Scan Domain" anytime to refresh the list with current domain state

File Location: `DomainScanResults.json` (same folder as `Remotecollect.exe`)

Note: Scan results include the scan date, so you can see when the list was last updated.

Step 2: Select Target PCs

1. Review the list of discovered computers in the CheckedListBox
   - Localhost is always at the top with `[localhost]` indicator
   - Other computers (from domain scan or manual input) are listed below
2. Check the boxes next to the PCs you want to collect logs from
   - You can select localhost, domain-discovered PCs, manually added PCs, or any combination
3. You can select multiple PCs for batch collection

Step 3: Collect Logs

1. Click the "Collect Logs" button
2. The application will attempt to collect logs from each selected PC using a three-tier failover strategy:

Method 1: SMB Administrative Shares (C$)   - Direct file access via UNC paths (\\PCName\C$\...)
   - Fastest method when available
   - Requires network share access

Method 2: PowerShell Remoting (WinRM)   - Uses Windows Remote Management
   - Compresses logs remotely before transfer
   - Requires WinRM to be enabled and configured

Method 3: PSExec Fallback   - Uses Sysinternals PSExec as last resort
   - Executes remote script to collect and compress logs
   - Note: PSExec only needs to be on the PC running Remotecollect.exe (the collector machine), not on target PCs

3. Monitor progress:
   - Progress bar shows completion status
   - Console log displays detailed information for each PC
   - Status label shows current operation

4. Collection results are saved to:
   ```
   Documents\Logs_{SessionTimestamp}\{Hostname}_{Timestamp}\
   ```
   - All collections from the same session are grouped in the same `Logs_{SessionTimestamp}` folder
   - Each PC gets its own subfolder with timestamp
   - A complete collection process log is also saved in the same folder

Log Collection Details

Collected Data Types

The application collects the following types of information from each target PC:

1. Agilent/OpenLab Application Logs - Log files from various Agilent software components
2. System Information - System configuration, installed updates, programs, and services
3. Windows Event Logs - Application, System, and Security event logs
4. SQL Server Logs - SQL Server error logs and related files (if SQL Server is installed)

Collected Log Paths

The application collects logs from the following Agilent/OpenLab directories:

- `C:\Program Files (x86)\Agilent Technologies\OpenLAB Data Store\tomcat\logs` (TomcatLogFiles)
- `C:\ProgramData\Agilent\installLogs` (installLogs)
- `C:\SVReports` (SVReports)
- `C:\ProgramData\Agilent\LogFiles` (CDSLogs)
- `C:\Program Files (x86)\Agilent Technologies\OpenLAB Services\Licensing\Flexera\logs` (flexLogs)
- `C:\Program Files (x86)\Agilent Technologies\Content Management Search Services\logs` (searchLogs)
- `C:\Program Files (x86)\Agilent Technologies\Content Management Search Services\solr\server\logs` (SolrLogs)
- `C:\Program Files (x86)\Agilent Technologies\OpenLab Reverse Proxy Configuration Service\ConfigurationService\logs\service` (RPCFGlogs)
- `C:\Program Files\OpenLab Reverse Proxy\Apache24\logs` (2.7RPlogs)
- `C:\Program Files (x86)\OpenLab Reverse Proxy\Apache24\logs` (2.6RPlogs)
- `C:\ProgramData\Agilent\installation` (installConf)
- `C:\ProgramData\Agilent\OpenLab ECM XT Import Scheduler\Logs` (imporschedulerlog)
- `D:\MassHunter\log` (MassHunterLog)
- `C:\ProgramData\Agilent Technologies\ChemStation` (ChemstationLog)

System Information Collected

For each PC, the following system information is collected:

- System Configuration (`systeminfo.txt`) - Complete system information including OS version, hardware details, network configuration
- Installed Updates (`installed_updates.txt`) - List of Windows hotfixes and updates sorted by installation date
- Installed Programs (`installed_programs.txt`) - List of all installed software from Windows registry
- System Services (`system_services.txt`) - Status and details of all Windows services

Windows Event Logs Collected

The following Windows Event Logs are exported as `.evtx` files:

- Application.evtx - Application-level events and errors
- System.evtx - System-level events, driver issues, and hardware problems
- Security.evtx - Security-related events including login attempts and access control

SQL Server Logs

If SQL Server is installed on the target PC, the application will automatically detect and collect:

- SQL Server error logs (ERRORLOG files)
- Log files from all SQL Server instances found
- Located in standard SQL Server installation directories

File Filtering

- Excluded: All `.dmp` (memory dump) files are automatically excluded from collection
- Included: All other log files from the target directories

Output Structure

Collected logs are organized as follows:

```
Documents\Logs_{SessionTimestamp}\
  ├── PC-NAME_20241215_143022\
  ├── CollectionProcessLog_{Timestamp}.txt\
      ├── System_Info\
      │   ├── systeminfo.txt
      │   ├── installed_updates.txt
      │   ├── installed_programs.txt
      │   ├── system_services.txt
      │   └── EventLogs\
      │       ├── Application.evtx
      │       ├── System.evtx
      │       └── Security.evtx
      ├── SQLServer_Logs\
      │   └── [SQL instance folders with error logs]
      ├── TomcatLogFiles\
      ├── installLogs\
      ├── SVReports\
      ├── CDSLogs\
      ├── flexLogs\
      ├── searchLogs\
      ├── SolrLogs\
      ├── RPCFGlogs\
      ├── 2.7RPlogs\
      ├── 2.6RPlogs\
      ├── installConf\
      ├── imporschedulerlog\
      ├── MassHunterLog\
      └── ChemstationLog\
```

Troubleshooting

Domain Scan Issues

Problem: No computers found
- Solution: Verify you have Domain Administrator privileges and can access Active Directory

Problem: Scan fails with access denied
- Solution: Ensure you're running as Domain Administrator and have proper AD permissions

Connection Method Failures

Method 1 (SMB) Fails:- Verify network connectivity to target PC
- Check if administrative shares (C$) are enabled
- Ensure firewall allows SMB traffic (port 445)

Method 2 (WinRM) Fails:- Verify WinRM is enabled on target PCs:
  ```powershell
  Enable-PSRemoting -Force
  ```
- Check WinRM service is running
- Verify firewall allows WinRM (ports 5985/5986)

Method 3 (PSExec) Fails:- Ensure PSExec.exe is in the same folder as Remotecollect.exe (or in system PATH on the collector machine)
- Note: PSExec only needs to be on the collector machine, not on target PCs
- Verify target PC allows remote execution
- Check firewall allows RPC/DCOM traffic

General Issues

Application won't start:- Ensure you're running `Remotecollect.exe` as administrator (right-click → Run as administrator)
- Check if .NET Framework 4.8 is installed: Check Windows Features or Control Panel > Programs and Features
  - .NET Framework 4.8 is built into Windows 10 version 1809 and later, Windows 11, and Windows Server 2019/2022
  - For older Windows versions, download and install from: https://dotnet.microsoft.com/download/dotnet-framework/net48
- Check if the executable file is blocked (right-click → Properties → Unblock if present)
- Verify all required files are in the same folder as the executable (including PSExec.exe if present)
- Ensure Windows Defender or antivirus isn't blocking the application
- Review Windows Event Viewer for errors

Collection takes too long:- Large log directories may take time
- Network latency affects transfer speed
- Consider collecting from fewer PCs at once

No logs collected:- Verify Agilent/OpenLab is installed on target PCs
- Check if log directories exist
- Review console log for specific error messages

System information not collected:- Verify PowerShell remoting is available (for WinRM method)
- Check if target PC allows remote command execution
- Ensure administrative shares are accessible (for SMB method)

Event logs not collected:- Verify you have permissions to read event logs on target PC
- Check if event log service is running on target PC
- Some event logs (especially Security) may require additional permissions

SQL Server logs not found:- SQL Server logs are only collected if SQL Server is installed
- Verify SQL Server installation paths are standard
- Check console log for SQL Server detection messages

Best Practices

1. Run during off-hours - Log collection can be resource-intensive
2. Select PCs strategically - Start with a few PCs to test connectivity
3. Monitor console log - Watch for warnings and errors
4. Verify output - Check collected logs folder after completion
5. Keep PSExec updated - If using Method 3, ensure latest version on the collector machine (target PCs don't need PSExec)

Security Considerations

- This tool requires Domain Administrator privileges
- Collected logs may contain sensitive information
- Store collected logs securely
- Follow your organization's data retention policies
- Review logs before sharing or archiving

Support

For issues or questions:
1. Check the console log for detailed error messages
2. Verify all prerequisites are met
3. Review troubleshooting section above
4. Contact your IT administrator if problems persist

Version Information

- Version: 1.0.2.1
- Release: 260212
- Executable: Remotecollect.exe
- Target Framework: .NET Framework 4.8
- Platform: Windows Forms
- Distribution: Framework-dependent executable (requires .NET Framework 4.8 or higher to be installed)
- Included Tools: PSExec (for Method 3 fallback)
- Application Icon: Custom multi-resolution icon embedded in the executable (log8.ico). The icon is embedded as a resource, so no separate icon file is required for deployment. The icon appears in Windows Explorer, the application window, and the taskbar.

Release 260212 Features

- Manual PC Input: Added manual PC input field and "Add PC" button to allow adding PCs by hostname or IP address without domain scanning
- Localhost Always Present: Localhost is always displayed at the top of the PC list with `[localhost]` indicator, regardless of domain membership or scan results
- Non-Domain Support: Application works even when the machine is not in a domain - domain scan gracefully returns empty list, but localhost and manually added PCs are still available
- UI Layout Improvements: Reorganized UI layout with Scan Domain and Collect Logs buttons at the top, manual PC input below, and PC list below that
- Enhanced Flexibility: Users can now collect logs from localhost and manually specified PCs without requiring Active Directory domain membership

Release 20260212 Features

- .NET Framework 4.8 Compatibility: Application now targets .NET Framework 4.8 for improved compatibility and stability
- Improved Compatibility: All components updated for .NET Framework 4.8 compatibility
- Enhanced Stability: Fixed compatibility issues with JSON serialization and nullable types

Release 260211 Features

- Credential Dialog: If current user is not a Domain Administrator, the application prompts for Domain Administrator credentials with clear explanation of required privileges
- Scan Results Persistence: Domain scan results are automatically saved to `DomainScanResults.json` and loaded on startup, eliminating the need to re-scan every time
- Improved User Experience:
  - Faster startup with automatic loading of saved scan results
  - Scan date displayed in status bar
  - Option to refresh scan results anytime with "Scan Domain" button

Previous Release Features (20260208)

- Localhost Detection: Automatically adds the host machine to the PC list with `[localhost]` indicator after domain scan
- Timestamp Organization: All collections from the same session are grouped in `Logs_{SessionTimestamp}` folder for better organization
- Console Log Saving: Complete collection process log is automatically saved to `CollectionProcessLog_{Timestamp}.txt` in the same folder
- UI Improvements:
  - Scan Domain button is disabled after successful scan to prevent unnecessary re-scans
  - Improved layout handling for window resizing and full-screen mode

---

Last Updated: February 2026
