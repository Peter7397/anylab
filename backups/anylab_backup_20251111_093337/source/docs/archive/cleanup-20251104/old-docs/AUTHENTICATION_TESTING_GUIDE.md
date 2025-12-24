# Authentication Testing Guide

## 🏠 Homepage Overview

The **homepage** (`/`) is a **public landing page** that serves as the entry point for your application.

### What It Shows:

1. **For Unauthenticated Users** (No Login Token):
   - Landing page with:
     - Welcome message and branding
     - Feature highlights (Forum, Knowledge Sharing, Community)
     - **Public forum preview** - shows public forum posts (read-only)
     - "Login" buttons to navigate to login page
   
2. **For Authenticated Users** (Has Login Token):
   - Automatically redirects to `/dashboard` (with loading spinner during redirect)

---

## 🧪 Testing Steps - Start Here

### **Step 1: Access the Homepage** 
📍 **URL:** http://localhost:3000/

**What to check:**
- ✅ Page loads without errors
- ✅ See landing page content (if not logged in)
- ✅ See "登录" (Login) button in header
- ✅ See forum preview section at bottom
- ✅ If already logged in, should redirect to dashboard

---

### **Step 2: Test Login Flow**

1. **Click "登录" button** → Should go to `/login`
   - **URL:** http://localhost:3000/login

2. **Login Page:**
   - Enter credentials (use your admin/test account)
   - Submit form
   - ✅ Should redirect to `/dashboard`
   - ✅ Should see user name in top-right corner
   - ✅ Should see sidebar navigation

**Test Credentials:**
- You'll need to check if you have a test user created
- Default might be: `admin` / `admin123!@#` (check backend)

---

### **Step 3: Test Authentication Protection**

**Test Unauthenticated Access:**
1. **Clear browser localStorage:**
   - Open DevTools (F12)
   - Application tab → Local Storage → Clear all
2. **Try accessing protected routes:**
   - http://localhost:3000/dashboard
   - ✅ Should redirect to `/login`
   
3. **Try accessing feature-protected routes:**
   - http://localhost:3000/ai/chat
   - ✅ Should redirect to `/login` (if no token) or `/dashboard` (if token but no permissions)

---

### **Step 4: Test Public Routes (No Login Required)**

**These should work without authentication:**

1. **Homepage:** http://localhost:3000/
   - ✅ Should show landing page
   - ✅ Should show forum preview

2. **Public Forum:** http://localhost:3000/forum
   - ✅ Should show forum posts (read-only)
   - ✅ Cannot post/reply without login

3. **Forum Post Detail:** http://localhost:3000/forum/post/1
   - ✅ Should show individual post
   - ✅ Cannot reply without login

---

### **Step 5: Test Document Loading (Main Issue)**

**After logging in:**

1. **Navigate to:** http://localhost:3000/dashboard
2. **Go to Knowledge Library:** http://localhost:3000/ai/knowledge
3. **Or Document Manager:** http://localhost:3000/ai/knowledge/manager
4. **Try loading/uploading documents:**
   - ✅ Documents should load without errors
   - ✅ No "Authentication required" errors
   - ✅ Document viewer should work

**If documents don't load:**
- Check browser console for errors
- Check backend logs: `tail -f /tmp/backend.log`
- Verify JWT token is being sent in API requests

---

## 🔍 Quick Debugging

### Check if Backend is Running:
```bash
curl http://localhost:8000/api/health/
# Should return: {"status": "healthy", "service": "anylab-backend"}
```

### Check if Frontend is Running:
```bash
curl http://localhost:3000
# Should return HTML
```

### Check Authentication Token:
1. Open Browser DevTools (F12)
2. Go to **Application** tab → **Local Storage** → `http://localhost:3000`
3. Look for key: `anylab_token`
4. ✅ Should see JWT token if logged in

### Check API Requests:
1. Open Browser DevTools (F12)
2. Go to **Network** tab
3. Try accessing a protected page
4. Check requests to `/api/ai/documents/`
5. ✅ Should see `Authorization: Bearer <token>` header
6. ✅ Should get 200 status, not 401

---

## 📋 Test Checklist

### ✅ Pre-Login (Public Access)
- [ ] Homepage (`/`) loads and shows content
- [ ] Forum (`/forum`) loads and shows posts
- [ ] Can view forum posts without login
- [ ] Cannot post/reply without login
- [ ] Login button navigates to `/login`

### ✅ Login Flow
- [ ] Login page loads correctly
- [ ] Can submit credentials
- [ ] Redirects to `/dashboard` after login
- [ ] Token is stored in localStorage
- [ ] User info loads (name shows in top bar)

### ✅ Authenticated Routes
- [ ] Dashboard loads
- [ ] Sidebar navigation works
- [ ] Cannot access protected routes without token (redirects to login)
- [ ] Feature-protected routes check permissions correctly

### ✅ Document Management (Main Test)
- [ ] Can access `/ai/knowledge/manager`
- [ ] Documents list loads
- [ ] Can upload new documents
- [ ] Can view documents
- [ ] Document viewer works
- [ ] No authentication errors in console

### ✅ Error Handling
- [ ] Invalid login shows error message
- [ ] Expired token triggers refresh or redirect
- [ ] Network errors show appropriate messages
- [ ] Permission denied redirects correctly

---

## 🚀 Recommended Testing Order

1. **Start Fresh:** Clear browser cache and localStorage
2. **Visit Homepage:** http://localhost:3000/
3. **Browse Forum:** Click forum section, verify public access
4. **Login:** Click "登录", enter credentials
5. **Test Dashboard:** Verify redirect and navigation
6. **Test Documents:** Go to Knowledge Library, verify document loading works
7. **Test Permissions:** Try accessing admin routes (should require admin feature)
8. **Test Logout:** Click logout, verify redirect to login

---

## 🐛 Common Issues to Check

### Issue: "Authentication required" when trying to access documents
**Fix Applied:** Middleware now allows all `/api/*` requests through to DRF
**Verify:** Documents should load now

### Issue: Token expires but doesn't refresh
**Fix Applied:** Token expiration check and auto-refresh
**Verify:** Should auto-refresh before expiration

### Issue: Permissions don't load
**Fix Applied:** Better error handling in AuthContext
**Verify:** Check browser console for specific errors

---

## 📍 Current Status

- ✅ Backend: Running on http://localhost:8000
- ✅ Frontend: Running on http://localhost:3000
- ✅ Database: Connected (PostgreSQL on port 5433)
- ✅ Middleware: Fixed to allow API requests through
- ✅ All authentication fixes: Implemented

**You're ready to test! Start at the homepage:** http://localhost:3000/

