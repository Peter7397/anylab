# Forum Permissions Added to Roles System

## ✅ Changes Made

Forum module permissions have been successfully integrated into the roles and permissions system.

## 📋 Forum Permission Structure

### Permission Levels

1. **`forum.view`** - View forum posts and categories
   - Basic read access
   - Public by default, but can be restricted

2. **`forum.post`** - Create new forum posts
   - Required to create posts
   - Includes draft creation

3. **`forum.reply`** - Create replies to posts
   - Required to reply to existing posts
   - Includes nested replies

4. **`forum.edit`** - Edit own posts and replies
   - Users can edit their own content
   - Does not allow editing others' content

5. **`forum.moderate`** - Moderate forum content
   - Pin/unpin posts
   - Lock/unlock posts
   - Delete any post/reply
   - Edit any post/reply
   - Feature posts

6. **`forum.manage`** - Manage forum structure
   - Create/edit/delete categories
   - Manage tags
   - Full forum administration

## 🎭 Updated Role Permissions

### 1. **system_admin**
- All forum permissions: ✅
- Full access to all forum features

### 2. **content_uploader**
- `forum.view`: ✅
- `forum.post`: ✅
- `forum.reply`: ✅
- `forum.edit`: ✅
- Can participate in forum discussions

### 3. **bulk_importer**
- `forum.view`: ✅
- `forum.post`: ✅
- `forum.reply`: ✅
- `forum.edit`: ✅
- Can participate in forum discussions

### 4. **help_portal_editor**
- `forum.view`: ✅
- `forum.post`: ✅
- `forum.reply`: ✅
- `forum.edit`: ✅
- Can participate in forum discussions

### 5. **ai_rag_user**
- `forum.view`: ✅
- `forum.post`: ✅
- `forum.reply`: ✅
- `forum.edit`: ✅
- Can participate in forum discussions

### 6. **forum_moderator** (NEW)
- `forum.view`: ✅
- `forum.post`: ✅
- `forum.reply`: ✅
- `forum.edit`: ✅
- `forum.moderate`: ✅
- Can moderate forum content without full admin access

### 7. **forum_user** (NEW)
- `forum.view`: ✅
- `forum.post`: ✅
- `forum.reply`: ✅
- `forum.edit`: ✅
- Standard forum participation

### 8. **viewer**
- `forum.view`: ✅
- Read-only forum access

## 🔧 Implementation Details

### Backend Changes

1. **`backend/users/permissions.py`**:
   - Updated superuser/staff default permissions to include all forum permissions

2. **`backend/users/management/commands/seed_roles.py`**:
   - Added forum permissions to existing roles
   - Added new `forum_moderator` role
   - Added new `forum_user` role
   - Updated `viewer` role to include `forum.view`

### Permission Hierarchy

```
forum.view (lowest)
  ↓
forum.post
  ↓
forum.reply
  ↓
forum.edit
  ↓
forum.moderate
  ↓
forum.manage (highest)
```

## 🚀 Usage

### Assign Forum Roles

```bash
# Via Django Admin
Navigate to: /admin/users/userrole/

# Via API
POST /api/users/roles/assign/
{
  "user_id": 1,
  "role_id": 7  # forum_moderator
}
```

### Check Permissions

```bash
# Get user permissions
GET /api/users/me/permissions/
{
  "permissions": {
    "features": {
      "forum.view": true,
      "forum.post": true,
      "forum.reply": true,
      "forum.edit": true
    }
  }
}
```

## 📝 Frontend Integration

The forum routes are currently public for viewing, but you can now:

1. **Protect Forum Creation/Editing**:
   ```typescript
   <Route path="/forum/new" element={
     <RequireFeature feature="forum.post">
       <PostEditor />
     </RequireFeature>
   } />
   ```

2. **Protect Forum Moderation**:
   ```typescript
   // In ForumPost component
   {permissions?.features?.['forum.moderate'] && (
     <button onClick={handlePin}>Pin Post</button>
   )}
   ```

## 🔍 Verification

Run the seed command to update roles:

```bash
cd backend
source venv/bin/activate
python manage.py seed_roles
```

Check roles in database:

```bash
python manage.py shell
>>> from users.models import Role
>>> Role.objects.filter(name='forum_moderator').first().permissions
```

## 📊 Summary

- ✅ Forum permissions added to all roles
- ✅ 2 new roles created: `forum_moderator` and `forum_user`
- ✅ Superuser/staff get all forum permissions automatically
- ✅ Permission hierarchy established
- ✅ Ready for frontend integration

The forum module is now fully integrated into the roles and permissions system!

