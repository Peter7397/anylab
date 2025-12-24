# Frontend Localization Testing Guide

**Date:** 2025-01-XX  
**Status:** Phase 1 Frontend Testing

## Quick Test Checklist

### 1. Language Switcher Test ✅

**Location:** Top Bar (top right, next to AI Mode toggle)

**Test Steps:**
1. Open the application in browser (http://localhost:3000)
2. Look for the language switcher dropdown in the top bar
3. Click the dropdown - you should see:
   - "简体中文" (Simplified Chinese)
   - "English"
4. Select "简体中文"
5. Verify the language changes immediately

**Expected Results:**
- Language switcher is visible in TopBar
- Dropdown shows both language options
- Selecting a language changes the UI immediately
- Language preference is saved to localStorage

### 2. Sidebar Translation Test ✅

**Location:** Left sidebar navigation

**Test Steps:**
1. With language set to "简体中文", check the sidebar
2. Verify all menu items are in Chinese:
   - "仪表板" (Dashboard)
   - "知识库" (Knowledge Library)
   - "AI助手" (AI Assistant)
   - "论坛" (Forum)
   - etc.
3. Switch to "English" and verify items change back to English
4. Test both organization modes (General Agilent / Lab Informatics)

**Expected Results:**
- All sidebar items display in selected language
- Navigation works correctly in both languages
- Organization mode toggle text is translated
- "Discovered Products" section is translated

### 3. Language Persistence Test

**Test Steps:**
1. Set language to "简体中文"
2. Refresh the page (F5 or Cmd+R)
3. Verify language remains "简体中文"
4. Close and reopen the browser
5. Verify language preference persists

**Expected Results:**
- Language preference persists across page refreshes
- Language preference persists across browser sessions
- localStorage key `anylab_language` contains the selected language

### 4. Browser Console Check

**Test Steps:**
1. Open browser DevTools (F12)
2. Check Console tab for errors
3. Check for any i18n-related warnings

**Expected Results:**
- No errors related to i18n
- No missing translation warnings
- Translations load correctly

### 5. Translation Coverage Check

**What Should Be Translated:**
- ✅ Sidebar navigation (all items)
- ✅ Language switcher
- ✅ Organization mode labels
- ⏳ Dashboard (not yet translated - Phase 2)
- ⏳ Login page (not yet translated - Phase 2)
- ⏳ Other components (Phase 2-3)

**Current Status:**
- Phase 1 Complete: Sidebar, Language Switcher, Infrastructure
- Phase 2 Pending: Dashboard, Auth, AI Components, etc.

## Testing Commands

### Start Frontend Development Server
```bash
cd frontend
npm start
```

The app should open at: http://localhost:3000

### Check Translation Files
```bash
# View Chinese translations
cat frontend/src/locales/zh-CN/sidebar.json

# View English translations
cat frontend/src/locales/en-US/sidebar.json
```

### Check Browser localStorage
```javascript
// In browser console
localStorage.getItem('anylab_language')  // Should return 'zh-CN' or 'en-US'
```

## Known Issues / Notes

1. **Dashboard and other components** are not yet translated (Phase 2)
2. **Some console warnings** may appear - these are pre-existing and not related to i18n
3. **Language detection** - If no preference is set, it will detect from browser settings

## What to Test

### ✅ Phase 1 Features (Ready to Test)
- [x] Language switcher appears in TopBar
- [x] Language switcher changes language
- [x] Sidebar navigation displays in Chinese
- [x] Sidebar navigation displays in English
- [x] Language preference persists
- [x] Organization mode labels are translated
- [x] No console errors related to i18n

### ⏳ Phase 2 Features (Not Yet Implemented)
- [ ] Dashboard translations
- [ ] Login page translations
- [ ] AI component translations
- [ ] Form validation messages
- [ ] Error messages

## Troubleshooting

### Language Switcher Not Appearing
- Check if `LanguageSwitcher` component is imported in `TopBar.tsx`
- Check browser console for import errors
- Verify `frontend/src/components/Layout/LanguageSwitcher.tsx` exists

### Translations Not Working
- Check browser console for errors
- Verify `frontend/src/i18n/config.ts` is imported in `App.tsx`
- Check that translation JSON files exist in `frontend/src/locales/`
- Clear browser cache and localStorage

### Sidebar Not Translated
- Verify `useTranslation('sidebar')` is called in `Sidebar.tsx`
- Check that `sidebar.json` files exist in both `zh-CN` and `en-US` folders
- Verify navigation functions use `t()` function

### Language Not Persisting
- Check browser localStorage: `localStorage.getItem('anylab_language')`
- Verify LanguageDetector is configured in `i18n/config.ts`
- Check browser console for localStorage errors

## Next Steps After Testing

Once frontend testing is complete:
1. Report any issues found
2. Continue with Phase 1.7-1.9 (Backend i18n setup)
3. Then proceed to Phase 2 (Translate remaining components)

## Test Results Template

```
Date: ___________
Tester: ___________

Phase 1 Frontend Testing Results:

Language Switcher:
[ ] Appears correctly
[ ] Changes language correctly
[ ] Persists across refresh

Sidebar Translation:
[ ] Chinese displays correctly
[ ] English displays correctly
[ ] Navigation works in both languages

Issues Found:
- 

Notes:
- 
```

