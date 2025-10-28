# License Endpoint Fix

## Issue
The License component was trying to call non-existent backend endpoints:
- `GET /api/admin/licenses/` - 404 Not Found
- `GET /api/admin/licenses/status/` - 404 Not Found

## Solution Applied
Since license management endpoints don't exist yet in the backend, I've temporarily mocked the API responses in the frontend to prevent errors.

### Changes Made

**File**: `frontend/src/services/api.ts`

1. **getLicenseStatus()** - Returns mock active license status
2. **listLicenses()** - Returns empty array
3. **importLicense()** - Throws error indicating not yet implemented

### Future Implementation

To fully implement license management, you need to:

1. **Create backend endpoints**:
   - `GET /api/admin/licenses/` - List all licenses
   - `GET /api/admin/licenses/status/` - Get current license status
   - `POST /api/admin/licenses/import/` - Import license file
   - `POST /api/admin/licenses/activate/` - Activate with license key

2. **Implement models** (if needed):
   - License model to store license information
   - License validation logic

3. **Update frontend API calls**:
   - Replace mock implementations with actual API calls

### Current Behavior
- License page loads without errors
- Shows "placeholder" status
- Import/activation features show "not implemented" messages

The component now gracefully handles the missing backend functionality.

