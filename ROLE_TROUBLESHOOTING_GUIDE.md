# Role & Permission Troubleshooting Guide

## Issue: User with "ai_rag_user" role cannot see RAG features

### Quick Diagnosis

Run this command to check the user's permissions:

```bash
cd backend
python check_user_permissions.py test
```

This will show you:
- ✅ If the user exists
- ✅ What roles are assigned
- ✅ What permissions the user has
- ✅ If the ai_rag_user role exists in the database

---

## Common Issues & Solutions

### 1. ❌ Role Not Seeded in Database

**Symptom:** `'ai_rag_user' role NOT FOUND!`

**Solution:**
```bash
cd backend
python manage.py seed_roles
```

This creates all default roles including:
- `system_admin` - Full access
- `content_uploader` - Can upload documents
- `bulk_importer` - Can bulk import
- `help_portal_editor` - Can edit help portal
- **`ai_rag_user`** - Can access AI RAG features ⭐
- `forum_moderator` - Can moderate forum
- `forum_user` - Can use forum
- `viewer` - Read-only access

---

### 2. ❌ Role Not Assigned to User

**Symptom:** `No roles assigned to this user`

**Solution via Django Admin:**
1. Go to `http://anylab.dpdns.org:8001/admin/`
2. Login as admin
3. Navigate to **Users > User roles**
4. Click **Add user role**
5. Select:
   - User: `test`
   - Role: `ai_rag_user`
   - Is active: ✅ (checked)
6. Click **Save**

**Solution via API (as admin):**
```bash
curl -X POST http://anylab.dpdns.org:8001/api/users/roles/assign/ \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": USER_ID,
    "role_id": ROLE_ID
  }'
```

---

### 3. ❌ Role Assigned but INACTIVE

**Symptom:** `❌ INACTIVE Role: ai_rag_user`

**Solution:**
The role assignment exists but is marked as inactive. Reactivate it:

1. Go to Django Admin
2. Find the UserRole entry
3. Check the **Is active** checkbox
4. Save

---

### 4. ❌ Frontend Not Refreshing Permissions

**Symptom:** Role is assigned and active, but user still can't see RAG

**Solution:**
The frontend caches permissions. User needs to:

1. **Log out completely**
2. **Clear browser cache** (Ctrl+Shift+Delete)
3. **Log back in**

Or force refresh permissions:
```javascript
// In browser console
localStorage.removeItem('anylab_token');
localStorage.removeItem('anylab_refresh_token');
window.location.href = '/login';
```

---

## How Permissions Work

### Backend (Django)

1. **Role Definition** (`users/models.py`):
   ```python
   class Role(models.Model):
       name = models.CharField(max_length=100, unique=True)
       permissions = models.JSONField(default=dict)
   ```

2. **User-Role Assignment** (`users/models.py`):
   ```python
   class UserRole(models.Model):
       user = models.ForeignKey(User, on_delete=models.CASCADE)
       role = models.ForeignKey(Role, on_delete=models.CASCADE)
       is_active = models.BooleanField(default=True)
   ```

3. **Permission Merging** (`users/permissions.py`):
   ```python
   def get_merged_permissions_for_user(user):
       # Merges all active roles' permissions
       # Staff and superusers get all permissions automatically
   ```

### Frontend (React)

1. **Permission Loading** (`context/AuthContext.tsx`):
   - Loads permissions via `/api/users/me/permissions/`
   - Stores in React context

2. **Route Protection** (`App.tsx`):
   ```tsx
   <Route path="/ai/rag" element={
     <RequireFeature feature="ai.rag">
       <ComprehensiveRagSearch />
     </RequireFeature>
   } />
   ```

3. **Sidebar Filtering** (`components/Layout/Sidebar.tsx`):
   - Checks `permissions.features['ai.rag']`
   - Hides menu items if permission is false

---

## Testing Permissions

### Test 1: Check Backend Permissions API

```bash
# Get auth token
TOKEN=$(curl -X POST http://anylab.dpdns.org:8001/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"YOUR_PASSWORD"}' \
  | jq -r '.access')

# Check permissions
curl http://anylab.dpdns.org:8001/api/users/me/permissions/ \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.permissions.features'
```

Expected output for ai_rag_user:
```json
{
  "ai.rag": true,
  "forum.view": true,
  "forum.post": true,
  "forum.reply": true,
  "forum.edit": true
}
```

### Test 2: Check Frontend Permissions

1. Open browser console (F12)
2. Log in as the test user
3. Run:
```javascript
// Check if token exists
console.log('Token:', localStorage.getItem('anylab_token'));

// Check permissions in React DevTools
// Look for AuthContext > permissions > features > ai.rag
```

---

## Permission Hierarchy

```
Superuser (is_superuser=True)
  └─ Has ALL permissions automatically
     └─ No role assignment needed

Staff (is_staff=True)
  └─ Has ALL permissions automatically
     └─ No role assignment needed

Regular User
  └─ Needs role assignment
     └─ Permissions = Union of all active roles
        └─ ai_rag_user role → ai.rag permission
```

---

## Debugging Checklist

- [ ] Run `python check_user_permissions.py test`
- [ ] Verify `ai_rag_user` role exists in database
- [ ] Verify role is assigned to user
- [ ] Verify role assignment is **active** (is_active=True)
- [ ] Verify role has correct permissions in JSON field
- [ ] User logs out and logs back in
- [ ] Clear browser cache
- [ ] Check browser console for permission logs
- [ ] Check `/api/users/me/permissions/` API response

---

## Quick Fix Script

If you want to quickly fix a user's permissions:

```bash
cd backend
python manage.py shell
```

```python
from users.models import User, Role, UserRole

# Get user and role
user = User.objects.get(username='test')
role = Role.objects.get(name='ai_rag_user')

# Assign role (or reactivate if exists)
user_role, created = UserRole.objects.get_or_create(
    user=user,
    role=role,
    defaults={'is_active': True}
)

if not created:
    user_role.is_active = True
    user_role.save()
    print("Role reactivated")
else:
    print("Role assigned")

# Verify
from users.permissions import get_merged_permissions_for_user
perms = get_merged_permissions_for_user(user)
print(f"Has ai.rag: {perms.get('features', {}).get('ai.rag', False)}")
```

---

## Contact

If issues persist after following this guide, check:
1. Backend logs: `backend/logs/anylab.log`
2. Browser console errors
3. Network tab in DevTools (check API responses)

