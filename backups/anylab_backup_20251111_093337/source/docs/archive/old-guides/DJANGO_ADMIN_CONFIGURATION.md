# Django Admin Configuration for AnyLab

## ✅ Current Status

The Django admin interface is properly configured and secured.

## 🔐 Access Control

### Built-in Protection
Django admin has **built-in protection** that requires:
- User must be authenticated (`is_authenticated = True`)
- User must be staff (`is_staff = True`) OR superuser (`is_superuser = True`)

### Access Points
- **URL**: `http://localhost:8001/admin/` (or `http://<your-ip>:8001/admin/`)
- **Login Required**: Yes (Django's built-in authentication)
- **Staff Required**: Yes (Django enforces `is_staff=True` automatically)

### Middleware Configuration
The `LoginRequiredMiddleware` exempts `/admin/` from authentication checks, allowing Django admin to handle its own authentication and staff requirement. This is the correct approach.

## 🎨 Customization

### Admin Site Branding
The admin site has been customized with AnyLab branding:

```python
admin.site.site_header = "AnyLab Administration"
admin.site.site_title = "AnyLab Admin"
admin.site.index_title = "Welcome to AnyLab Administration"
```

### Location
Configuration is in: `backend/anylab/admin.py`

### Root URL Handler
The root URL (`/`) now redirects to the frontend to prevent 404 errors:

- **URL**: `http://localhost:8001/` → Redirects to `http://localhost:3000/`
- **Smart Redirect**: Automatically detects hostname (localhost vs LAN)
- **Configuration**: `backend/anylab/urls.py` - `root_redirect` function

## 📋 Registered Models

The following models are registered in Django admin:

### Users & Roles
- `User` (CustomUserAdmin)
- `Role` (RoleAdmin)
- `UserRole` (UserRoleAdmin)

### AI Assistant
- `KnowledgeDocument` (KnowledgeDocumentAdmin)
- `DocumentChunk` (DocumentChunkAdmin)
- `ChatSession` (ChatSessionAdmin)
- `ChatMessage` (ChatMessageAdmin)
- `AIModel` (AIModelAdmin)
- `AIConversationTemplate` (AIConversationTemplateAdmin)
- `AIUsageLog` (AIUsageLogAdmin)

### Forum (from forum app)
- `ForumCategory` (ForumCategoryAdmin)
- `ForumTag` (ForumTagAdmin)
- `ForumPost` (ForumPostAdmin)
- `ForumReply` (ForumReplyAdmin)

### AI Assistant (from ai_assistant app)
- `PDFDocument` (PDFDocumentAdmin)
- `UploadedFile` (UploadedFileAdmin)
- `DocumentFile` (DocumentFileAdmin)
- `WebLink` (WebLinkAdmin)
- `KnowledgeShare` (KnowledgeShareAdmin)
- `QueryHistory` (QueryHistoryAdmin)
- `HelpPortalDocument` (HelpPortalDocumentAdmin)
- `WebsiteSource` (WebsiteSourceAdmin)

## 🔗 Frontend Integration

### Sidebar Link
The frontend sidebar includes a link to Django admin:

```typescript
{
  name: 'Django Admin',
  href: '/admin/',
  icon: Shield,
  external: true  // Opens in same window (backend URL)
}
```

**Location**: `frontend/src/components/Layout/Sidebar.tsx` (line 245)

### Note on External Link
The `external: true` flag means the link opens the backend URL directly. Since the frontend runs on port 3000 and backend on 8001, the link should point to:
- `http://localhost:8001/admin/` (when accessed via localhost)
- `http://<your-ip>:8001/admin/` (when accessed via LAN)

## 🚀 Usage

### Accessing Django Admin

1. **Direct URL**: Navigate to `http://localhost:8001/admin/`
2. **From Frontend**: Click "Django Admin" in the Administration menu (only visible to users with `admin` feature permission)

### Login

Use your Django user credentials:
- **Username**: Your username (e.g., `admin`)
- **Password**: Your password (e.g., `admin123`)

### Making a User Staff

To give a user access to Django admin:

```python
# Via Django shell
python manage.py shell
>>> from users.models import User
>>> user = User.objects.get(username='username')
>>> user.is_staff = True
>>> user.save()
```

Or via the frontend admin UI at `/admin/users` (if you have `admin` feature permission).

## 🔒 Security Notes

1. **Django Admin is Secure**: Django admin requires `is_staff=True` by default. This is enforced by Django's internal mechanisms.

2. **No Additional Configuration Needed**: The middleware correctly exempts `/admin/` routes, allowing Django to handle authentication and authorization.

3. **Production Considerations**:
   - Change `DEBUG = False` in production
   - Use strong `SECRET_KEY`
   - Consider using a custom admin URL (e.g., `/secret-admin/` instead of `/admin/`)
   - Enable HTTPS
   - Consider IP whitelisting for admin access

## 📝 Summary

- ✅ Django admin is properly configured
- ✅ Access restricted to staff and superusers only
- ✅ Custom AnyLab branding applied
- ✅ Frontend integration complete
- ✅ All models registered for admin management

The Django admin interface is ready to use!

