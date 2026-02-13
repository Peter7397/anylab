# Debug Guide - Remotecollect

## Logging Features

The application now includes comprehensive logging to help diagnose issues when the application doesn't respond or shows errors.

## Log File Location

Log files are automatically created in:
- **Primary Location:** `%AppData%\Remotecollect\Logs\`
  - Full path example: `C:\Users\YourName\AppData\Roaming\Remotecollect\Logs\`
- **Fallback Location:** `%Temp%\` (if AppData is not accessible)
  - Full path example: `C:\Users\YourName\AppData\Local\Temp\`

Log files are named: `Remotecollect_YYYYMMDD_HHMMSS.log`

## What Gets Logged

### Application Startup
- Application version and environment information
- OS version and .NET version
- Machine name and user name
- Administrator status check
- Working directory and application directory

### UI Events
- Form initialization
- Button clicks
- Control creation
- Form load and shown events

### Operations
- Domain scanning start/completion
- Log collection operations
- Connection method attempts (SMB, WinRM, PSExec)
- Success and failure messages
- All errors with full stack traces

### System Information
- All exceptions with details
- Inner exceptions
- Stack traces for debugging

## How to Access Logs

### Method 1: Check Status Bar
- The status bar at the bottom shows the log file name
- Format: `Ready - Log: Remotecollect_YYYYMMDD_HHMMSS.log`

### Method 2: Navigate to Log Folder
1. Press `Win + R`
2. Type: `%AppData%\Remotecollect\Logs`
3. Press Enter
4. Open the most recent log file

### Method 3: From Error Messages
- All error dialogs show the log file path
- Copy the path and navigate to it in File Explorer

## Debugging "No Response" Issues

If the application shows nothing or doesn't respond:

### Step 1: Check if Application Started
1. Open Task Manager (`Ctrl + Shift + Esc`)
2. Look for `Remotecollect.exe` in the Processes tab
3. If it's running, check the log file

### Step 2: Check Log File
1. Navigate to log file location (see above)
2. Open the most recent log file in Notepad
3. Look for:
   - `ERROR` entries - these indicate problems
   - `Fatal error` - application couldn't start
   - Last log entry - shows where it stopped

### Step 3: Common Issues in Logs

**"Failed to initialize logging"**
- AppData folder may not be accessible
- Check folder permissions

**"Application started without administrator privileges"**
- Application requires admin rights
- Right-click and "Run as administrator"

**"Failed to scan Active Directory domain"**
- Domain connectivity issue
- Check network connection
- Verify domain administrator account

**"Fatal error in MainForm constructor"**
- UI initialization failed
- Check for missing dependencies
- Verify .NET Runtime is included (for self-contained builds)

**No log file created at all**
- Application may not be starting
- Check Windows Event Viewer
- Verify executable isn't blocked

## Log Levels

- **INFO** - Normal operation messages
- **DEBUG** - Detailed debugging information
- **WARN** - Warning messages (non-fatal issues)
- **ERROR** - Error messages with exception details

## Example Log Entries

```
[2024-12-15 14:30:25.123] [INFO] === Remotecollect Application Started ===
[2024-12-15 14:30:25.125] [INFO] Application Version: 1.0.0
[2024-12-15 14:30:25.126] [INFO] OS Version: Microsoft Windows NT 10.0.19045.0
[2024-12-15 14:30:25.127] [INFO] .NET Version: 8.0.0
[2024-12-15 14:30:25.128] [INFO] Machine Name: PC-NAME
[2024-12-15 14:30:25.129] [INFO] User Name: DOMAIN\username
[2024-12-15 14:30:25.130] [INFO] Is Administrator: True
[2024-12-15 14:30:25.200] [INFO] MainForm constructor started
[2024-12-15 14:30:25.250] [DEBUG] Initializing UI components...
[2024-12-15 14:30:25.300] [INFO] MainForm constructor completed successfully
```

## Troubleshooting Tips

1. **Application doesn't start:**
   - Check Windows Event Viewer (Win + X → Event Viewer)
   - Look for .NET Runtime errors
   - Verify all files are in the same folder

2. **Form doesn't appear:**
   - Check log for "MainForm Shown" entry
   - Verify no exceptions in InitializeComponent
   - Check if form is minimized or off-screen

3. **Buttons don't work:**
   - Check log for button click events
   - Look for exceptions in event handlers
   - Verify UI thread isn't blocked

4. **Domain scan fails:**
   - Check log for AD connection errors
   - Verify network connectivity
   - Check domain administrator permissions

## Getting Help

When reporting issues, include:
1. The complete log file
2. Screenshot of any error messages
3. Steps to reproduce the issue
4. OS version and .NET version (shown in log)

---

**Note:** Log files can grow large over time. Old log files are not automatically deleted. You can manually clean them up if needed.
