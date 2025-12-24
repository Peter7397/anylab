# Icon Placement Guide for OnLab Frontend

## 📍 Where to Place Your New Icons

### **Primary Location: `frontend/public/`**

This is the **standard location** for static assets in React applications. Files placed here are:
- ✅ Accessible via `%PUBLIC_URL%` in HTML
- ✅ Accessible via `${process.env.PUBLIC_URL}` in React components
- ✅ Copied to build output during `npm run build`
- ✅ Served as static files

---

## 📁 Recommended Directory Structure

```
frontend/public/
├── icons/                    # ← RECOMMENDED: Create this folder for organized icon management
│   ├── app-icon.svg          # Main application icon (SVG preferred)
│   ├── app-icon-192.png      # 192x192 PNG version
│   ├── app-icon-512.png      # 512x512 PNG version
│   ├── favicon-32.png        # 32x32 favicon
│   └── [other icons...]      # Any additional icons you've created
├── images/                   # Optional: For other images (screenshots, etc.)
├── ai-icon.svg              # Currently referenced (see Sidebar.tsx line 367)
├── ai-logo-192.png          # Currently used as fallback
├── ai-logo-512.png          # App icon sizes
├── ai-favicon-32.png        # Favicon
├── ai-maskable-512.png      # PWA maskable icon
└── favicon.ico              # Default favicon
```

---

## 🎯 Current Icon Usage in Code

### **Referenced Icons:**

1. **Sidebar Logo** (`frontend/src/components/Layout/Sidebar.tsx`):
   ```typescript
   src={`${process.env.PUBLIC_URL || ''}/ai-icon.svg`}
   fallbackSrc={`${process.env.PUBLIC_URL || ''}/ai-logo-192.png`}
   ```
   - **Looking for:** `public/ai-icon.svg`
   - **Fallback:** `public/ai-logo-192.png`

2. **Favicon** (`frontend/public/index.html`):
   ```html
   <link rel="icon" type="image/png" href="%PUBLIC_URL%/ai-favicon-32.png" />
   <link rel="apple-touch-icon" href="%PUBLIC_URL%/ai-logo-192.png" />
   ```
   - **Using:** `public/ai-favicon-32.png` and `public/ai-logo-192.png`

3. **PWA Manifest** (`frontend/public/manifest.json`):
   - References: `ai-favicon-32.png`, `ai-logo-192.png`, `ai-maskable-512.png`

---

## ✅ Recommended Steps

### **Option 1: Replace Existing Icons (Simplest)**

If your new icons are replacements for existing ones:

1. **Place your icons directly in `frontend/public/`:**
   ```bash
   frontend/public/
   ├── ai-icon.svg          # Replace existing if you have SVG version
   ├── ai-logo-192.png      # Replace existing 192x192 icon
   ├── ai-logo-512.png      # Replace existing 512x512 icon
   ├── ai-favicon-32.png    # Replace existing favicon
   └── ai-maskable-512.png  # Replace existing maskable icon
   ```

2. **Keep the same filenames** so existing references continue to work

### **Option 2: Organized Structure (Recommended for Multiple Icons)**

If you have many icons or want better organization:

1. **Create an `icons` subfolder:**
   ```bash
   mkdir -p frontend/public/icons
   ```

2. **Move your icons there:**
   ```bash
   frontend/public/icons/
   ├── app-icon.svg
   ├── app-icon-192.png
   ├── app-icon-512.png
   ├── favicon-32.png
   └── [other icons...]
   ```

3. **Update references in code:**
   - Update `Sidebar.tsx` to reference `/icons/app-icon.svg`
   - Update `index.html` to reference `/icons/favicon-32.png`
   - Update `manifest.json` to reference new paths

### **Option 3: Keep Current Structure + Add New Icons**

If you want to keep existing icons and add new ones:

1. **Keep existing icons in `public/`**
2. **Add new icons alongside them:**
   ```bash
   frontend/public/
   ├── [existing icons...]
   ├── new-icon-1.svg
   ├── new-icon-2.png
   └── [other new icons...]
   ```

---

## 📝 Icon File Naming Conventions

### **Standard Sizes:**
- **Favicon:** `favicon-32.png` or `favicon.ico` (32x32px)
- **App Icon (Small):** `app-icon-192.png` (192x192px)
- **App Icon (Large):** `app-icon-512.png` (512x512px)
- **Maskable (PWA):** `app-maskable-512.png` (512x512px)
- **SVG (Scalable):** `app-icon.svg` (vector, preferred)

### **Naming Patterns Used in Project:**
- Current: `ai-icon.svg`, `ai-logo-192.png`, `ai-favicon-32.png`
- Pattern: `[prefix]-[type]-[size].[ext]`

---

## 🔧 How to Reference Icons in Code

### **In React Components:**
```typescript
// Using process.env.PUBLIC_URL (recommended)
<img src={`${process.env.PUBLIC_URL}/icons/app-icon.svg`} alt="App Icon" />

// Or for public/ root
<img src={`${process.env.PUBLIC_URL}/ai-icon.svg`} alt="App Icon" />

// Direct path (works but not recommended for CRA)
<img src="/icons/app-icon.svg" alt="App Icon" />
```

### **In HTML (index.html):**
```html
<!-- Using %PUBLIC_URL% placeholder -->
<link rel="icon" href="%PUBLIC_URL%/icons/favicon-32.png" />
<link rel="apple-touch-icon" href="%PUBLIC_URL%/icons/app-icon-192.png" />
```

### **In manifest.json:**
```json
{
  "icons": [
    {
      "src": "icons/favicon-32.png",
      "sizes": "32x32",
      "type": "image/png"
    },
    {
      "src": "icons/app-icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    }
  ]
}
```

---

## 🎨 Icon Format Recommendations

### **SVG (Preferred):**
- ✅ Scalable (no pixelation)
- ✅ Small file size
- ✅ Crisp at any size
- ✅ Best for logos and simple icons

### **PNG (For Specific Sizes):**
- ✅ Good for complex icons
- ✅ Required for PWA manifest sizes (192x192, 512x512)
- ✅ Good for favicons (32x32)

### **ICO (Legacy):**
- ⚠️ Only for favicon.ico (browser compatibility)
- ⚠️ PNG is preferred for modern browsers

---

## 📋 Checklist for Adding New Icons

- [ ] Decide on placement (public/ or public/icons/)
- [ ] Ensure proper file formats (SVG preferred, PNG for specific sizes)
- [ ] Use consistent naming convention
- [ ] Include required sizes:
  - [ ] 32x32 (favicon)
  - [ ] 192x192 (app icon, PWA)
  - [ ] 512x512 (app icon, PWA maskable)
- [ ] Update `index.html` if replacing favicon
- [ ] Update `manifest.json` if replacing PWA icons
- [ ] Update component references if changing paths
- [ ] Test in browser after changes
- [ ] Verify icons display correctly after `npm run build`

---

## 🚀 Quick Start (Recommended)

**If you just want to replace existing icons:**

1. **Place your icons in `frontend/public/` with these exact names:**
   - `ai-icon.svg` (or keep existing PNG)
   - `ai-logo-192.png`
   - `ai-logo-512.png`
   - `ai-favicon-32.png`
   - `ai-maskable-512.png`

2. **No code changes needed** - existing references will work!

3. **Test by running:**
   ```bash
   cd frontend
   npm start
   ```

4. **Verify icons appear correctly in:**
   - Browser tab (favicon)
   - Sidebar logo
   - PWA installation (if applicable)

---

## 💡 Additional Tips

1. **Optimize your icons:**
   - Use tools like [SVGO](https://github.com/svg/svgo) for SVG optimization
   - Compress PNGs (use tools like [TinyPNG](https://tinypng.com/))
   - Keep file sizes small for faster loading

2. **Accessibility:**
   - Always include `alt` text for icon images
   - Ensure icons have sufficient contrast

3. **Testing:**
   - Test icons in different browsers
   - Verify they look good at different sizes
   - Check both light and dark themes if applicable

---

## 📞 Need Help?

If you're unsure about:
- Which icons to replace
- How to update references
- File format or sizing

Just let me know what icons you've created and I can help you integrate them!

