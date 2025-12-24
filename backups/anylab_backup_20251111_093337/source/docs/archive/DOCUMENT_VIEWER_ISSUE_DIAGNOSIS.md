# Document Viewer Issue Diagnosis

## Problem Identified

The document viewer is not working because the backend serializer is not generating proper file URLs.

## Root Cause

**Location**: `backend/ai_assistant/views/rag_views.py` line 249

**Issue**: The `DocumentSerializer` is not being passed the request context, which means `get_file_url()` method returns `None`.

### Current Code (BROKEN):
```python
serializer = DocumentSerializer(docs[start:end], many=True)
```

### The Problem:
The serializer's `get_file_url()` method tries to access the request from context:
```python
def get_file_url(self, obj):
    if obj.file:
        request = self.context.get('request')  # ← This returns None!
        if request:
            return request.build_absolute_uri(obj.file.url)
    return None
```

Since context is not passed, it returns `None`, and the frontend gets documents without `file_url`.

## The Fix

### Backend Fix Required:
```python
# Line 249 in rag_views.py needs to be:
serializer = DocumentSerializer(docs[start:end], many=True, context={'request': request})
```

Also need to fix line 343 (document_search):
```python
# Change from:
serializer = DocumentSerializer(docs, many=True)

# To:
serializer = DocumentSerializer(docs, many=True, context={'request': request})
```

## Additional Issues Found

### 1. File Serving Configuration
- ✅ Media files ARE being served at `/media/<path:path>` (line 50 in urls.py)
- ✅ The endpoint exists and is configured correctly

### 2. Frontend Configuration
- ✅ Frontend has DocumentViewer component (fully implemented)
- ✅ DocumentManager fetches documents correctly
- ✅ The viewer can receive `url` prop and render PDFs

### 3. The Missing Link
- ❌ When documents are retrieved from backend, they don't have `file_url` field
- ❌ Frontend tries to use `file_url` from document object
- ❌ Since `file_url` is None, the viewer receives an invalid URL

## Files That Need Updating

### 1. `backend/ai_assistant/views/rag_views.py`
- Line 249: Add context to DocumentSerializer
- Line 343: Add context to DocumentSerializer in document_search

### 2. Check These Locations
Need to verify context is passed in ALL places where DocumentSerializer is used.

## Expected File URL Format

After the fix, documents should return with URLs like:
```
http://localhost:8000/media/documents/example.pdf
```

## Testing After Fix

1. Upload a document via the frontend
2. Check the API response - should include `file_url` field
3. Click "View" on a document
4. DocumentViewer should receive a valid URL
5. PDF should render correctly

## Summary

**Issue**: Missing request context in serializer initialization  
**Impact**: Documents have no `file_url`, viewer cannot load  
**Fix**: Add `context={'request': request}` to all DocumentSerializer calls  
**Effort**: 5 minutes to fix  
**Files to modify**: 1-2 files in backend  

