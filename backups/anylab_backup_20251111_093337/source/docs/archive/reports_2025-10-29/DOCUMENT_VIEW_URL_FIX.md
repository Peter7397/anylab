# Document View URL Fix

## 🐛 Issue Reported

User reported error: **"Document URL not available"** when clicking the "View" button on uploaded documents.

---

## 🔍 Root Cause

**Location**: `backend/ai_assistant/serializers.py` - `get_file_url()` method

**Problem**: 
- Uploaded documents don't have `DocumentFile.file` field set (it's `null`)
- Files are stored in `media/uploads/filename.ext` directory
- File reference is stored in `UploadedFile.filename` as `'uploads/filename.ext'`
- Serializer only checked `obj.file` which returned `None`
- Frontend received `file_url: null`
- Error shown: "Document URL not available"

**Original Code**:
```python
def get_file_url(self, obj):
    if obj.file:  # ← Returns None for uploaded documents
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.file.url)
    return None  # ← file_url is None
```

---

## ✅ Solution Implemented

### 1. Updated Serializer to Handle Uploaded Files

**File**: `backend/ai_assistant/serializers.py`

**Changes**:
```python
def get_file_url(self, obj):
    request = self.context.get('request')
    if not request:
        return None
    
    # For SSB_KPR documents (MHTML), use the HTML view endpoint
    if obj.document_type == 'SSB_KPR':
        return request.build_absolute_uri(f'/api/ai/documents/{obj.id}/html/')
    
    # Check if DocumentFile has a file field (legacy documents)
    if obj.file and hasattr(obj.file, 'url'):
        return request.build_absolute_uri(obj.file.url)
    
    # For uploaded documents, file is stored via UploadedFile
    if hasattr(obj, 'uploaded_file') and obj.uploaded_file:
        # uploaded_file.filename is stored as 'uploads/filename.ext'
        media_url = request.build_absolute_uri(f'/media/{obj.uploaded_file.filename}')
        return media_url
    
    return None
```

**What it does**:
1. ✅ Handles legacy documents with `DocumentFile.file` field
2. ✅ Handles uploaded documents via `UploadedFile.filename`
3. ✅ Generates proper `/media/uploads/filename.ext` URL
4. ✅ Still handles SSB_KPR documents specially

---

### 2. Updated Document Download Function

**File**: `backend/ai_assistant/views/rag_views.py` - `document_download()`

**Changes**:
```python
def document_download(request, doc_id):
    doc = DocumentFile.objects.get(id=doc_id)
    
    # Try DocumentFile.file field first (legacy documents)
    if doc.file and hasattr(doc.file, 'path') and os.path.exists(doc.file.path):
        return FileResponse(open(doc.file.path, 'rb'))
    
    # For uploaded documents, file is stored via UploadedFile
    if hasattr(doc, 'uploaded_file') and doc.uploaded_file:
        from django.conf import settings
        file_path = os.path.join(settings.MEDIA_ROOT, doc.uploaded_file.filename)
        if os.path.exists(file_path):
            return FileResponse(open(file_path, 'rb'))
    
    return error_response("File not found")
```

**What it does**:
1. ✅ Downloads legacy documents from `DocumentFile.file.path`
2. ✅ Downloads uploaded documents from `media/uploads/` directory
3. ✅ Works for both storage methods

---

### 3. Updated Document Delete Function

**File**: `backend/ai_assistant/views/rag_views.py` - `document_delete()`

**Changes**:
```python
# Delete file if exists
file_deleted = False

# Try DocumentFile.file field first (legacy documents)
if doc.file and hasattr(doc.file, 'path'):
    if os.path.exists(doc.file.path):
        os.remove(doc.file.path)
        file_deleted = True

# For uploaded documents, file is stored via UploadedFile
if not file_deleted and hasattr(doc, 'uploaded_file') and doc.uploaded_file:
    from django.conf import settings
    file_path = os.path.join(settings.MEDIA_ROOT, doc.uploaded_file.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        file_deleted = True
```

**What it does**:
1. ✅ Deletes legacy document files
2. ✅ Deletes uploaded document files from `media/uploads/`
3. ✅ Handles both storage methods

---

## 📋 Files Changed

1. ✅ `backend/ai_assistant/serializers.py` - Updated `get_file_url()` method
2. ✅ `backend/ai_assistant/views/rag_views.py` - Updated `document_download()` method
3. ✅ `backend/ai_assistant/views/rag_views.py` - Updated `document_delete()` method

---

## ✅ Expected Results

### Before Fix
- User uploads document → DocumentFile created
- User clicks "View" button → Error: "Document URL not available"
- `file_url` is `null` in API response

### After Fix
- User uploads document → DocumentFile created with `uploaded_file` FK
- Backend generates `file_url`: `http://localhost:8000/media/uploads/filename.pdf`
- User clicks "View" button → Document opens successfully
- API returns proper `file_url`

---

## 🧪 Testing

To test the fix:

1. **Upload a document** via Library Manager
2. **Check API response** for `file_url` field
3. **Click "View"** button on the document
4. **Verify** document opens correctly in DocumentViewer
5. **Test download** - should download file successfully
6. **Test delete** - should delete both file and database record

---

## 📊 Impact

### Affected Documents
- ✅ Bulk imported documents (already have `uploaded_file` FK)
- ✅ Uploaded documents via Library Manager (have `uploaded_file` FK)
- ✅ Legacy documents (have `DocumentFile.file` field)

### Benefits
- ✅ Users can now view uploaded documents
- ✅ Download functionality works for all document types
- ✅ Delete functionality works properly
- ✅ Backward compatible with legacy documents
- ✅ No database changes required

---

## 🎯 Summary

**Problem**: Document URL not available because `DocumentFile.file` was null  
**Root Cause**: Uploaded files stored in different location  
**Solution**: Generate URL from `UploadedFile.filename`  
**Files Modified**: 2 files, 3 functions  
**Status**: ✅ **FIXED**

---

**Date**: January 2025  
**Status**: ✅ **COMPLETE**  
**Testing**: Ready for user verification

