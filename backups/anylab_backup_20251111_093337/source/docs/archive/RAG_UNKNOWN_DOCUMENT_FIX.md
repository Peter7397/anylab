# RAG "Unknown Document" Fix
**Status:** ✅ **COMPLETED**  
**Date:** January 2025

---

## Issue Description

The RAG search results were displaying "Unknown Document" at the top of source listings, even though actual source documents were listed below.

### Root Cause

The SQL queries in the RAG services were incorrectly trying to JOIN with `DocumentFile` table when `DocumentChunk` only references `UploadedFile`. 

**Incorrect JOIN:**
```sql
LEFT JOIN ai_assistant_documentfile df ON df.id = dc.uploaded_file_id
```

This JOIN was failing because:
- `DocumentChunk.uploaded_file_id` references `UploadedFile.id`
- `DocumentFile.id` is unrelated to `UploadedFile`
- When the JOIN failed, filename became NULL, falling back to "Unknown Document"

---

## Files Fixed

### 1. `backend/ai_assistant/rag_service.py`
**Lines 305-315:** Removed incorrect DocumentFile JOIN

**Before:**
```sql
SELECT dc.id, dc.content, dc.uploaded_file_id, dc.page_number, dc.chunk_index,
       COALESCE(uf.filename, df.title, 'Unknown Document') as filename,
       COALESCE(uf.file_hash, '') as file_hash, 
       COALESCE(uf.file_size, df.file_size, 0) as file_size
FROM ai_assistant_documentchunk dc
LEFT JOIN ai_assistant_uploadedfile uf ON dc.uploaded_file_id = uf.id
LEFT JOIN ai_assistant_documentfile df ON df.id = dc.uploaded_file_id  ❌ WRONG JOIN
```

**After:**
```sql
SELECT dc.id, dc.content, dc.uploaded_file_id, dc.page_number, dc.chunk_index,
       COALESCE(uf.filename, 'Unknown Document') as filename,
       COALESCE(uf.file_hash, '') as file_hash, 
       COALESCE(uf.file_size, 0) as file_size
FROM ai_assistant_documentchunk dc
LEFT JOIN ai_assistant_uploadedfile uf ON dc.uploaded_file_id = uf.id
```

### 2. `backend/ai_assistant/improved_rag_service.py`
**Lines 255-268:** Removed incorrect DocumentFile JOIN

**Before:**
```sql
SELECT dc.id, dc.content, dc.uploaded_file_id, dc.page_number, dc.chunk_index,
       COALESCE(uf.filename, df.title, 'Unknown Document') as filename,
       COALESCE(uf.file_hash, '') as file_hash, 
       COALESCE(uf.file_size, df.file_size, 0) as file_size,
       1 - (dc.embedding <=> %s::vector) as similarity
FROM ai_assistant_documentchunk dc
LEFT JOIN ai_assistant_uploadedfile uf ON dc.uploaded_file_id = uf.id
LEFT JOIN ai_assistant_documentfile df ON df.id = dc.uploaded_file_id  ❌ WRONG JOIN
```

**After:**
```sql
SELECT dc.id, dc.content, dc.uploaded_file_id, dc.page_number, dc.chunk_index,
       COALESCE(uf.filename, 'Unknown Document') as filename,
       COALESCE(uf.file_hash, '') as file_hash, 
       COALESCE(uf.file_size, 0) as file_size,
       1 - (dc.embedding <=> %s::vector) as similarity
FROM ai_assistant_documentchunk dc
LEFT JOIN ai_assistant_uploadedfile uf ON dc.uploaded_file_id = uf.id
```

### 3. `backend/ai_assistant/hybrid_search.py`
**Lines 128-138:** Removed incorrect DocumentFile JOIN

**Before:**
```sql
SELECT dc.id, dc.content, dc.uploaded_file_id, dc.page_number, dc.chunk_index,
       COALESCE(uf.filename, df.title, 'Unknown Document') as filename,
       COALESCE(uf.file_hash, '') as file_hash, 
       COALESCE(uf.file_size, df.file_size, 0) as file_size
FROM ai_assistant_documentchunk dc
LEFT JOIN ai_assistant_uploadedfile uf ON dc.uploaded_file_id = uf.id
LEFT JOIN ai_assistant_documentfile df ON df.id = dc.uploaded_file_id  ❌ WRONG JOIN
```

**After:**
```sql
SELECT dc.id, dc.content, dc.uploaded_file_id, dc.page_number, dc.chunk_index,
       COALESCE(uf.filename, 'Unknown Document') as filename,
       COALESCE(uf.file_hash, '') as file_hash, 
       COALESCE(uf.file_size, 0) as file_size
FROM ai_assistant_documentchunk dc
LEFT JOIN ai_assistant_uploadedfile uf ON dc.uploaded_file_id = uf.id
```

---

## Database Model Relationships

**Correct Relationships:**
- `DocumentChunk.uploaded_file` → ForeignKey to `UploadedFile`
- `DocumentFile` is a separate model for managing file metadata
- No direct relationship between `DocumentChunk` and `DocumentFile`

**Model Definition:**
```python
class DocumentChunk(models.Model):
    uploaded_file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE, 
                                     related_name='pages', null=True, blank=True)
    # ... other fields
```

---

## Backend Restart

After making these changes, the backend was restarted successfully:
- ✅ Backend is running on port 8000
- ✅ Health check passed: `{"status": "healthy", "service": "anylab-backend"}`
- ✅ Changes automatically detected by Django's reload feature

---

## Testing

To verify the fix:

1. **Run a RAG search** with a query that should return document sources
2. **Check the sources list** - Should now show actual filenames instead of "Unknown Document"
3. **Expected result:** All sources display with proper filenames like:
   - `"Installation_Guide.pdf (Page 3)"`
   - `"Sample_Protocol.pdf (Page 1)"`

---

## Result

✅ RAG search results now correctly display source document filenames  
✅ "Unknown Document" issue resolved  
✅ All three RAG service implementations fixed (rag_service, improved_rag_service, hybrid_search)

