# 🔐 Forced Logout Issue - Root Cause Analysis

## Problem
You were forced logged out as admin unexpectedly.

## Root Cause
The JWT configuration has a **mismatch**:

1. **Settings configured for token blacklisting:**
   ```python
   SIMPLE_JWT = {
       'ROTATE_REFRESH_TOKENS': True,
       'BLACKLIST_AFTER_ROTATION': True,  # ← This is enabled
       ...
   }
   ```

2. **But the blacklist app is NOT installed:**
   ```python
   INSTALLED_APPS = [
       ...
       'rest_framework_simplejwt',  # ← JWT app installed
       # ❌ 'rest_framework_simplejwt.token_blacklist' is MISSING!
   ]
   ```

## What Happens
When you refresh your token:
1. Django tries to blacklist the old refresh token (because `BLACKLIST_AFTER_ROTATION: True`)
2. The blacklist app isn't installed, so the operation fails
3. Token refresh fails → frontend detects 401 → clears auth → forces logout

## Solutions

### Option 1: Disable Blacklisting (Quickest Fix)
Since you don't have the blacklist app installed, disable it:

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=5),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,  # ← Change to False
    ...
}
```

**Pros:** Quick fix, no database migrations needed
**Cons:** Old refresh tokens remain valid until they expire (1 day)

### Option 2: Install Token Blacklist (Recommended for Security)
Properly set up token blacklisting:

1. **Install the app:**
   ```python
   INSTALLED_APPS = [
       ...
       'rest_framework_simplejwt',
       'rest_framework_simplejwt.token_blacklist',  # ← Add this
       ...
   ]
   ```

2. **Run migrations:**
   ```bash
   cd backend
   source venv/bin/activate
   python manage.py migrate
   ```

**Pros:** More secure - old tokens are properly invalidated
**Cons:** Requires database migration

## Recommended Action
**Use Option 1** for immediate fix, then consider Option 2 later for better security.

## Additional Notes
- Your access tokens are valid for 5 hours
- Refresh tokens are valid for 1 day
- With blacklisting disabled, old refresh tokens remain valid until expiration
- This is acceptable for most use cases unless you need immediate token revocation

