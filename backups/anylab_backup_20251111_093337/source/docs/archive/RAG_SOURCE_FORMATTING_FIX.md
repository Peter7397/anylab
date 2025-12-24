# RAG Source Formatting Fix
**Status:** ✅ **COMPLETED**  
**Date:** October 2024

---

## Issues Fixed

### 1. "Unknown Document" appearing at top ✅
**Problem:** Sources showing as "Unknown Document" instead of actual filenames

**Root Cause:** DocumentChunk references UploadedFile, but many chunks are created from DocumentFile (scraped content). The query only looked at UploadedFile, missing DocumentFile links.

**Solution:** Updated SQL queries to use `COALESCE` to try both UploadedFile and DocumentFile:
```sql
COALESCE(uf.filename, df.title, 'Unknown Document') as filename
```

**Files Changed:**
- `backend/ai_assistant/improved_rag_service.py`
- `backend/ai_assistant/hybrid_search.py`
- `backend/ai_assistant/rag_service.py`

---

### 2. Missing Page Numbers ✅
**Problem:** Sources listed content but page numbers weren't accessible for display

**Solution:** Added `page_number` field properly extracted from database and added to formatted results.

**Result:** Every source now includes `page_number` for display

---

### 3. No Clickable Links to PDF Viewer ✅
**Problem:** Sources had download links but no way to jump directly to the specific page in the PDF viewer

**Solution:** Added `view_url` field to each source:
```python
view_url = f"/api/ai/pdf/{uploaded_file_id}/view/?page={page_number}"
```

**Result:** Each source now has a clickable `view_url` that opens the PDF viewer at the exact page

---

## Implementation Details

### Added Fields to Source Objects

Each source now includes:

1. **`page_number`**: Page number (defaults to 1 if not set)
2. **`view_url`**: URL to open PDF viewer at specific page
   - Format: `/api/ai/pdf/{uploaded_file_id}/view/?page={page_number}`
   - Example: `/api/ai/pdf/46/view/?page=3`
3. **`source_display`**: Formatted display string
   - Format: `"{filename} (Page {page_number})"`
   - Example: `"Installation_Guide.pdf (Page 3)"`

### Example Source Object

**Before:**
```json
{
  "id": 123,
  "content": "...",
  "uploaded_file_id": 46,
  "page_number": 3,
  "filename": "Unknown Document",
  "similarity": 0.85
}
```

**After:**
```json
{
  "id": 123,
  "content": "...",
  "uploaded_file_id": 46,
  "page_number": 3,
  "filename": "Installation_Guide.pdf",
  "similarity": 0.85,
  "view_url": "/api/ai/pdf/46/view/?page=3",
  "source_display": "Installation_Guide.pdf (Page 3)",
  "download_url": "/api/ai/documents/46/download/"
}
```

---

## SQL Query Improvements

### Before:
```sql
SELECT dc.id, dc.content, dc.uploaded_file_id, dc.page_number, dc.chunk_index,
       uf.filename, uf.file_hash, uf.file_size
FROM ai_assistant_documentchunk dc
LEFT JOIN ai_assistant_uploadedfile uf ON dc.uploaded_file_id = uf.id
```

### After:
```sql
SELECT dc.id, dc.content, dc.uploaded_file_id, dc.page_number, dc.chunk_index,
       COALESCE(uf.filename, df.title, 'Unknown Document') as filename,
       COALESCE(uf.file_hash, '') as file_hash, 
       COALESCE(uf.file_size, df.file_size, 0) as file_size,
       1 - (dc.embedding <=> %s::vector) as similarity
FROM ai_assistant_documentchunk dc
LEFT JOIN ai_assistant_uploadedfile uf ON dc.uploaded_file_id = uf.id
LEFT JOIN ai_assistant_documentfile df ON df.id = dc.uploaded_file_id
```

**Key Changes:**
- Added `LEFT JOIN ai_assistant_documentfile` for DocumentFile references
- Used `COALESCE` to try UploadedFile filename first, then DocumentFile title
- Falls back to 'Unknown Document' only if both are missing

---

## Files Modified

### 1. `backend/ai_assistant/improved_rag_service.py`
- Updated SQL query to include DocumentFile join
- Added `view_url` and `source_display` formatting

### 2. `backend/ai_assistant/hybrid_search.py`
- Updated SQL query for BM25 document loading
- Added `view_url` and `source_display` formatting

### 3. `backend/ai_assistant/rag_service.py`
- Updated SQL query to include DocumentFile join
- Added `view_url` and `source_display` formatting

---

## Testing Recommendations

### 1. Test RAG Search
Query: "How do I install the software?"

**Expected Results:**
- ✅ Sources show actual document names (not "Unknown Document")
- ✅ Page numbers displayed: "Installation_Guide.pdf (Page 5)"
- ✅ Clickable links to open PDF at specific page

### 2. Test PDF Viewer Links
Click on any source's view link.

**Expected:**
- Opens PDF viewer
- Jumps directly to the specific page
- Shows the relevant content highlighted

### 3. Test Mixed Document Types
Search should return:
- PDF uploads (from UploadedFile)
- Scraped content (from DocumentFile)
- GitHub files (from DocumentFile)
- Forum posts (from DocumentFile)
- SSB entries (from DocumentFile)

All should show proper names and page numbers.

---

## Frontend Integration

### Displaying Sources

Frontend should now display:

```jsx
{source.sources.map((source, idx) => (
  <div key={idx}>
    <h4>
      {source.source_display}  {/* "filename.pdf (Page 3)" */}
    </h4>
    <p>{source.content}</p>
    {source.view_url && (
      <a href={source.view_url} target="_blank">
        View in PDF
      </a>
    )}
  </div>
))}
```

### Clickable Links

Users can now click to view the exact page:

```javascript
const handleViewSource = (source) => {
  if (source.view_url) {
    // Open in new tab at specific page
    window.open(source.view_url, '_blank');
    
    // OR open in embedded viewer
    setViewerOpen({
      url: source.view_url,
      page: source.page_number
    });
  }
};
```

---

## Benefits

### For Users:
1. ✅ See actual document names, not "Unknown"
2. ✅ See exact page numbers
3. ✅ Click to jump directly to relevant page
4. ✅ Better context understanding

### For Developers:
1. ✅ Consistent source formatting across all RAG tiers
2. ✅ Better filename resolution with COALESCE
3. ✅ Extensible format for future enhancements

---

## Next Steps (Optional Enhancements)

1. **Add excerpt highlighting** - Show which section on the page is relevant
2. **Add section numbers** - Include section titles if available
3. **Add document type icons** - Different icons for PDF, GitHub, Forum, etc.
4. **Add quality indicators** - Show source quality scores
5. **Add relevance percentages** - Display similarity scores visually

---

## Summary

✅ **All 3 Issues Fixed:**
- No more "Unknown Document" at top
- Page numbers now properly displayed
- Clickable links to PDF viewer at specific pages

**Result:** RAG sources now have proper names, page numbers, and clickable links for better user experience!

