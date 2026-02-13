# Ping File Validation Guide

## Overview

The Remotecollect application includes a **1-year expiration check**. After 1 year from the reference date (December 15, 2024), the application will require a **ping file** to continue running.

## How It Works

1. **First Year (Before February 7, 2027):**
   - Application runs normally
   - No ping file required

2. **After 1 Year (On or After February 7, 2027):**
   - Application checks for `Remotecollect.ping` file in the application directory
   - If file doesn't exist, shows error message and exits
   - If file exists and is valid, application continues

## Error Message

If ping file is missing after 1 year, users will see:

```
The application has detected that your system is not compatible with the application.

This application requires a compatibility update after 2027-02-07.

Continuing to run the tool may lead to unexpected errors.

Please contact the developer to get an update.
```

## Generating Ping Files

### Using the PingFileGenerator Tool

1. **Open the PingFileGenerator project**
   - Located in: `PingFileGenerator` folder

2. **Run the application**
   - Select a PIN from the dropdown
   - Choose output location (or use default)
   - Click "Generate PIN File"

3. **Rename the file**
   - Rename the generated file to: `Remotecollect.ping`
   - The default name is `SQLMonitorService.pin`, so rename it

4. **Distribute to users**
   - Send the `Remotecollect.ping` file to users
   - Users place it in the same folder as `Remotecollect.exe`

### Valid PINs

You can use any of these PINs:
- `Tina1@`
- `Tina2@`
- `Tina3@`
- `Tina4@`
- `Just4U`
- `AC942ecust`
- `User@1`
- `Tina@5`
- `Tina@6`
- `GPTW@A`

## File Placement

Users must place the ping file in the **same directory** as `Remotecollect.exe`:

```
C:\Remotecollect\
  ├── Remotecollect.exe
  ├── Remotecollect.dll
  ├── [other files...]
  └── Remotecollect.ping  ← Ping file goes here
```

## Security Features

- **Encrypted**: Ping files are encrypted using AES-256
- **HMAC Protected**: Files are protected against tampering
- **Time-Limited**: Files expire 90 days from generation (but this is for the generator's original purpose)
- **Validated**: Application validates file integrity and authenticity

## Important Dates

- **Reference Date**: February 7, 2026
- **Expiration Date**: February 7, 2027
- **After Expiration**: Ping file required

## For Developers

### Updating the Expiration Date

To change the expiration date, edit `PingFileValidator.cs`:

```csharp
// Change these dates as needed
private static readonly DateTime ReferenceDate = new DateTime(2026, 2, 7);
private static readonly DateTime ExpirationDate = ReferenceDate.AddYears(1); // 2027-02-07
```

### Testing

1. **Test before expiration:**
   - Application should run normally
   - No ping file needed

2. **Test after expiration (simulate):**
   - Temporarily change `ExpirationDate` to a past date
   - Run application without ping file → should show error
   - Place ping file → should run normally

## Troubleshooting

### "Ping file not found" error

**Solution:**
1. Generate a new ping file using PingFileGenerator
2. Rename it to `Remotecollect.ping`
3. Place it in the same folder as `Remotecollect.exe`
4. Restart the application

### "Ping file is invalid" error

**Possible causes:**
- File is corrupted
- File was tampered with
- File is from wrong application

**Solution:**
1. Generate a new ping file
2. Ensure file is named exactly `Remotecollect.ping`
3. Ensure file is in the correct location

### File not being recognized

**Check:**
1. File name is exactly `Remotecollect.ping` (case-sensitive on some systems)
2. File is in the same directory as `Remotecollect.exe`
3. File was generated using the correct PingFileGenerator tool
4. File wasn't corrupted during transfer

## Distribution Workflow

1. **Before expiration date:**
   - No action needed
   - Application runs normally

2. **Approaching expiration (1-2 weeks before):**
   - Generate ping files for all users
   - Distribute ping files to users
   - Provide instructions for placement

3. **After expiration:**
   - Users who have ping file: Continue working
   - Users without ping file: Contact developer for ping file

## Notes

- Ping files are **not single-use** for this application (unlike the SQLMonitorService)
- Ping files can be reused as long as they are valid
- Each ping file has a timestamp, but validation checks are based on the 1-year expiration date
- Users need a new ping file each year (after the next expiration date)
