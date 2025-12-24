# RAG Clickable Sources with Page Navigation
**Status:** ✅ **COMPLETED**  
**Date:** January 2025

---

## Feature Implementation

Source document titles in RAG search results are now **clickable links** that open the PDF viewer at the specific page number referenced.

---

## Changes Made

### Frontend Updates (3 files updated)

#### 1. `BasicRagSearch.tsx`
#### 2. `RagSearch.tsx`
#### 3. `ComprehensiveRagSearch.tsx`

### Changes Applied:

#### A. **Pass `view_url` from Backend Response** (Lines 133-154, 160-168)

**Before:**
```typescript
references: res.sources?.map((source: any) => ({
  title: source.title || 'Unknown Document',
  content: source.content || '',
  page: source.page,
  score: source.similarity || source.score
})) || []
```

**After:**
```typescript
references: res.sources?.map((source: any) => ({
  title: source.title || 'Unknown Document',
  content: source.content || '',
  page: source.page || source.page_number,
  score: source.similarity || source.score,
  view_url: source.view_url  // ✅ Added view_url
})) || []
```

#### B. **Make Titles Clickable Links** (Lines 503-514, 532-544)

**Before:**
```tsx
<p className="font-medium text-gray-800">{source.title}</p>
```

**After:**
```tsx
{source.view_url ? (
  <a 
    href={source.view_url} 
    target="_blank" 
    rel="noopener noreferrer"
    className="font-medium text-blue-600 hover:text-blue-800 hover:underline cursor-pointer"
  >
    {source.title}
  </a>
) : (
  <p className="font-medium text-gray-800">{source.title}</p>
)}
```

---

## Backend Integration

The backend already generates the `view_url` with page navigation (from previous fixes):

```python
view_url = f"/api/ai/pdf/{uploaded_file_id}/view/?page={page_number}"
```

Example URLs:
- `/api/ai/pdf/69/view/?page=3`
- `/api/ai/pdf/44/view/?page=1`

---

## User Experience

### How It Works:

1. **User performs RAG search** → Gets results with sources
2. **Source list displays** → Shows document titles
3. **User clicks on a title** → Opens PDF viewer in new tab
4. **PDF viewer loads** → Jumps directly to the referenced page number

### Visual Indicators:

- **Clickable titles:** Blue color (`text-blue-600`) with hover effect
- **Hover state:** Darker blue with underline animation
- **Non-clickable titles:** Gray if `view_url` is missing (fallback)

---

## Example Flow

**RAG Search Result:**
```
Sources:
  📄 Sample_Scheduler_for_OpenLab_Installation_Configuration_Guide_en (Page 3)
  📄 openlab-server-ecmxt-v2.8-administration-guide-en (Page 15)
  📄 CDS_v2.8_QuickReferenceSheet_en (Page 1)
```

**User clicks on second source** → Opens: `/api/ai/pdf/48/view/?page=15`

---

## Benefits

✅ **Direct navigation** - Jump straight to the referenced page  
✅ **Quick verification** - Users can easily check sources  
✅ **Better UX** - No need to manually search for the document and page  
✅ **Visual feedback** - Clear indication that titles are clickable  
✅ **Safe navigation** - Opens in new tab (`target="_blank"`)  

---

## Testing

To test the feature:

1. Run a RAG search query
2. View the sources listed in the results
3. Click on any document title (blue text)
4. PDF viewer should open at the correct page number

---

## Summary

✅ All 3 RAG components updated (BasicRagSearch, RagSearch, ComprehensiveRagSearch)  
✅ Clickable document titles with page navigation  
✅ Backend `view_url` integrated  
✅ No linter errors  
✅ Opens PDF viewer at specific page in new tab  

**Users can now click on any source document title to view the exact page referenced in the RAG response!**

