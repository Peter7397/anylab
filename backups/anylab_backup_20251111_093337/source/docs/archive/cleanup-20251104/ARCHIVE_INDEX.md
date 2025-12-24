# Cleanup Archive Index
Created: Tue Nov  4 07:53:28 CST 2025

## Archived Files

### Documentation
Archived old documentation files that are no longer actively used.
Essential docs (README.md, QUICK_START_GUIDE.md, etc.) remain in root.

### Logs
Archived old log files. Current logs remain in backend/logs/.

### Test Files
Archived test scripts and test documents.

### Unused Scripts
Archived cleanup and utility scripts that are no longer needed.

## Restore

To restore any archived file:
```bash
# Find the file
find docs/archive/cleanup-* -name "filename"

# Restore it
cp docs/archive/cleanup-YYYYMMDD/path/to/file /original/location/
```

