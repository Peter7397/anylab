# 🌐 Localization Testing Guide

## ✅ What's Been Completed

### Phase 1: Infrastructure ✅
- ✅ i18n setup with react-i18next
- ✅ Language switcher component
- ✅ Translation file structure
- ✅ Sidebar translations

### Phase 2: Component Translations ✅
- ✅ **Dashboard** - Fully translated
- ✅ **Login/Auth** - Fully translated
- ✅ **Sidebar** - Fully translated
- ✅ **AI Components**:
  - ✅ ChatAssistant
  - ✅ BasicRagSearch
  - ✅ ComprehensiveRagSearch
  - ✅ GraphRagSearch
  - ✅ TroubleshootingAI
  - ✅ KnowledgeLibrary
  - ✅ DocumentManager
  - ✅ DocumentViewer
- ✅ **Administration**:
  - ✅ UsersRoles

### Phase 2: Still Pending
- ⏳ SystemSettings
- ⏳ Analytics
- ⏳ License
- ⏳ Forum components
- ⏳ Other components

---

## 🧪 How to Test

### 1. Start the Application

Since you're using `anylab.dpdns.org`, make sure:

**Backend is running:**
```bash
cd backend
docker compose up -d
```

**Frontend is running:**
```bash
cd frontend
npm start
```

**Access the app at:** `https://anylab.dpdns.org` (or `http://anylab.dpdns.org`)

### 2. Test Language Switcher

1. **Find the Language Switcher:**
   - Look in the top-right corner of the page
   - Should be next to the AI Mode toggle
   - Shows current language (e.g., "English" or "简体中文")

2. **Switch Languages:**
   - Click the language dropdown
   - Select "简体中文" (Simplified Chinese)
   - **Verify:** UI should change immediately to Chinese
   - Select "English"
   - **Verify:** UI should change back to English

3. **Test Persistence:**
   - Set language to Chinese
   - Refresh the page (F5 or Cmd+R)
   - **Verify:** Language should remain Chinese
   - Close and reopen browser
   - **Verify:** Language preference should persist

### 3. Test Translated Components

#### ✅ Sidebar (Should be fully translated)
- Switch to Chinese
- **Verify:** All menu items show in Chinese:
  - "仪表板" (Dashboard)
  - "知识库" (Knowledge Library)
  - "AI助手" (AI Assistant)
  - "论坛" (Forum)
  - "管理" (Administration)
- Switch to English
- **Verify:** All items show in English

#### ✅ Dashboard (Should be fully translated)
1. Navigate to Dashboard (`/dashboard`)
2. Switch to Chinese
3. **Verify:**
   - Page title: "仪表板"
   - All stats cards show Chinese labels
   - "总用户数", "活跃用户", etc.
   - All buttons and text in Chinese
4. Switch to English
5. **Verify:** All text changes to English

#### ✅ Login Page (Should be fully translated)
1. Log out (if logged in)
2. Navigate to login page
3. Switch to Chinese
4. **Verify:**
   - "用户名" (Username)
   - "密码" (Password)
   - "登录" (Login)
   - All error messages in Chinese
5. Switch to English
6. **Verify:** All text in English

#### ✅ AI Components (Should be fully translated)
1. Navigate to any AI component:
   - Chat Assistant (`/ai/chat`)
   - Basic RAG Search (`/ai/rag-basic`)
   - Comprehensive RAG (`/ai/rag-comprehensive`)
   - Graph RAG (`/ai/rag-graph`)
   - Troubleshooting AI (`/ai/troubleshooting`)
   - Knowledge Library (`/ai/knowledge`)
   - Document Manager (`/ai/documents`)
   - Document Viewer (when viewing a document)

2. Switch to Chinese
3. **Verify:** All UI text, buttons, labels, messages are in Chinese
4. Switch to English
5. **Verify:** All text in English

#### ✅ Administration - Users & Roles (Should be fully translated)
1. Navigate to `/admin/users` (requires admin permission)
2. Switch to Chinese
3. **Verify:**
   - Page title: "用户和角色"
   - Stats cards: "总用户数", "活跃用户", "角色", "非活跃"
   - Table headers: "用户", "角色", "状态", "部门", "操作"
   - Buttons: "添加用户", "管理角色"
   - All modals and forms in Chinese
4. Switch to English
5. **Verify:** All text in English

### 4. Browser Console Check

1. Open browser DevTools (F12)
2. Go to Console tab
3. **Check for:**
   - ❌ No errors related to i18n
   - ❌ No "translation key not found" warnings
   - ✅ Translations load correctly

### 5. Check localStorage

In browser console, run:
```javascript
localStorage.getItem('anylab_language')
// Should return: 'zh-CN' or 'en-US'
```

---

## 🐛 Troubleshooting

### Language Switcher Not Visible
- Check browser console for errors
- Verify `LanguageSwitcher` is imported in `TopBar.tsx`
- Clear browser cache

### Translations Not Working
- Check browser console for errors
- Verify translation files exist in `frontend/src/locales/`
- Clear localStorage: `localStorage.clear()` then refresh
- Restart frontend dev server

### Some Components Not Translated
- This is expected! We're still working through Phase 2
- Check the "What's Been Completed" section above
- Components not listed are still pending translation

### Chinese Characters Not Displaying
- Check browser font settings
- Verify UTF-8 encoding
- Try a different browser

---

## 📊 Testing Checklist

### Basic Functionality
- [ ] Language switcher appears in top bar
- [ ] Can switch between English and Chinese
- [ ] Language preference persists after refresh
- [ ] Language preference persists after browser restart
- [ ] No console errors related to i18n

### Component Translation Coverage
- [ ] Sidebar - All items translated
- [ ] Dashboard - All text translated
- [ ] Login page - All text translated
- [ ] ChatAssistant - All text translated
- [ ] BasicRagSearch - All text translated
- [ ] ComprehensiveRagSearch - All text translated
- [ ] GraphRagSearch - All text translated
- [ ] TroubleshootingAI - All text translated
- [ ] KnowledgeLibrary - All text translated
- [ ] DocumentManager - All text translated
- [ ] DocumentViewer - All text translated
- [ ] UsersRoles - All text translated

### Still Pending (Not Yet Translated)
- [ ] SystemSettings
- [ ] Analytics
- [ ] License
- [ ] Forum components
- [ ] Other components

---

## 🎯 What's Next?

### Immediate Next Steps:
1. **Continue Phase 2.4:** Translate remaining Administration components
   - SystemSettings
   - Analytics
   - License

2. **Phase 2.5:** Translate Forum components
   - Forum
   - ForumPost
   - PostEditor
   - ReplyEditor

3. **Phase 2.6-2.9:** Complete remaining Phase 2 tasks

### After Phase 2:
- Phase 3: Translate remaining components
- Phase 4: Testing and quality assurance

---

## 📝 Test Results Template

```
Date: ___________
Tester: ___________
Browser: ___________
URL: ___________

Language Switcher:
[ ] Appears correctly
[ ] Changes language correctly
[ ] Persists across refresh
[ ] Persists across browser restart

Component Testing:
[ ] Sidebar - Chinese ✓ / English ✓
[ ] Dashboard - Chinese ✓ / English ✓
[ ] Login - Chinese ✓ / English ✓
[ ] ChatAssistant - Chinese ✓ / English ✓
[ ] BasicRagSearch - Chinese ✓ / English ✓
[ ] ComprehensiveRagSearch - Chinese ✓ / English ✓
[ ] GraphRagSearch - Chinese ✓ / English ✓
[ ] TroubleshootingAI - Chinese ✓ / English ✓
[ ] KnowledgeLibrary - Chinese ✓ / English ✓
[ ] DocumentManager - Chinese ✓ / English ✓
[ ] DocumentViewer - Chinese ✓ / English ✓
[ ] UsersRoles - Chinese ✓ / English ✓

Console Errors:
[ ] No i18n errors
[ ] No missing translation warnings

Issues Found:
- 

Notes:
- 
```

---

## 💡 Quick Test Commands

```bash
# Check if frontend is running
curl http://localhost:3000

# Check if backend is running
curl http://localhost:8000/api/health

# View translation files
cat frontend/src/locales/zh-CN/sidebar.json
cat frontend/src/locales/en-US/sidebar.json
```

---

**Happy Testing! 🎉**

