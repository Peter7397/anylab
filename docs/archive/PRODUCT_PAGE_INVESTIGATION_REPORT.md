# Product Page Investigation Report
**URL**: `http://localhost:3000/lab-informatics/openlab/cds`  
**Issue**: Returns 404 error  
**Date**: Investigation Report

---

## Investigation Summary

### 1. Frontend Routing ✅ CORRECT
**Location**: `frontend/src/App.tsx` line 65

```typescript
<Route path="/lab-informatics/:suite/:product" element={<ProductDocumentGrid />} />
```

**Status**: Route is properly configured

---

### 2. Frontend Component ✅ EXISTS
**Location**: `frontend/src/components/Products/ProductDocumentGrid.tsx`

**Status**: Component exists and is properly implemented

**Key Issue Found** (Line 53):
```typescript
const response = await apiClient.getProductDocuments(product, { latestOnly: showLatestOnly });
```

When URL is `/lab-informatics/openlab/cds`:
- `suite = "openlab"`
- `product = "cds"`

Component calls API with just `"cds"`, but backend expects `"openlab_cds"`.

---

### 3. Backend API Endpoint ✅ EXISTS
**Location**: `backend/ai_assistant/views/product_views.py`

**URL Pattern**:
```
/api/ai/products/<product_category>/documents/
```

**URL Routing Chain**:
1. `anylab/urls.py` line 40: `path('api/ai/', include('ai_assistant.urls'))`
2. `ai_assistant/urls.py` line 38: `path('products/', include('ai_assistant.urls.product_urls'))`
3. `product_urls.py` line 9: `path('<str:product_category>/documents/', ...)`

**Final URL**: `/api/ai/products/{product_category}/documents/`

---

### 4. Root Cause Analysis

#### Problem 1: Product Category Mismatch
**Current Behavior**:
- Frontend sends: `/api/ai/products/cds/documents/` ❌
- Backend expects: `/api/ai/products/openlab_cds/documents/` ✅

**Metadata Format in Database**:
```json
{
  "product_category": "openlab_cds",  // Full category code
  "content_type": "installation_guide",
  "version": "3.2.1"
}
```

**Solution Required**:
Frontend needs to map URL slug to full product category:
```typescript
const productSlug = "cds";  // From URL params
const productCategory = "openlab_" + productSlug;  // Map to: "openlab_cds"
```

#### Problem 2: Backend Query Logic
**Location**: `backend/ai_assistant/views/product_views.py` line 34-36

```python
documents = DocumentFile.objects.filter(
    metadata__icontains=f'"product_category": "{product_category}"'
).order_by('-uploaded_at')
```

**Issue**: This query might not work correctly if `document.metadata` is stored as a dict rather than a JSON string.

---

### 5. Data Flow Analysis

```
User accesses: /lab-informatics/openlab/cds
         ↓
React Router extracts: { suite: "openlab", product: "cds" }
         ↓
ProductDocumentGrid calls: apiClient.getProductDocuments("cds", ...)
         ↓
API URL becomes: /api/ai/products/cds/documents/
         ↓
Backend tries to find: product_category = "cds"
         ↓
Database has documents with: product_category = "openlab_cds"
         ↓
❌ NO MATCH - Returns empty results or 404
```

---

### 6. Why 404 Error?

The error is actually likely a 200 response with empty data, OR the backend has an issue when no documents are found. The `icontains` filter on JSONField might also be causing issues.

---

## Required Fixes

### Fix 1: Product Slug Mapping (CRITICAL)
**File**: `frontend/src/components/Products/ProductDocumentGrid.tsx`

**Change needed** (around line 53):
```typescript
// BEFORE:
const response = await apiClient.getProductDocuments(product, { latestOnly: showLatestOnly });

// AFTER:
const productCategoryMap: { [key: string]: string } = {
  'cds': 'openlab_cds',
  'ecm': 'openlab_ecm',
  'eln': 'openlab_eln',
  'server': 'openlab_server',
  'workstation': 'masshunter_workstation',
  'quantitative': 'masshunter_quantitative',
  'qualitative': 'masshunter_qualitative',
  'bioconfirm': 'masshunter_bioconfirm',
  'metabolomics': 'masshunter_metabolomics',
  'current': 'vnmrj_current',
  'legacy': 'vnmrj_legacy'
};

const productCategory = productCategoryMap[product] || `openlab_${product}`;
const response = await apiClient.getProductDocuments(productCategory, { latestOnly: showLatestOnly });
```

### Fix 2: Backend Query Logic
**File**: `backend/ai_assistant/views/product_views.py`

**Issue**: JSONField query might not work correctly

**Current** (line 34-36):
```python
documents = DocumentFile.objects.filter(
    metadata__icontains=f'"product_category": "{product_category}"'
)
```

**Problem**: If metadata is stored as dict (not JSON string), `icontains` won't work.

**Better approach**:
```python
# Query by JSON field key
documents = DocumentFile.objects.filter(
    metadata__product_category=product_category
)
```

---

## Current Status

### ✅ Working:
- React Router configuration
- Component implementation
- Backend API endpoint exists
- URL routing structure

### ❌ Not Working:
- Product slug to category mapping
- Database query method (icontains vs JSON field key lookup)
- Empty results handling

---

## Recommended Implementation Order

1. **Fix product slug mapping** in ProductDocumentGrid (15 minutes)
2. **Fix backend query** to use proper JSON field lookup (10 minutes)
3. **Add error handling** for no documents found (5 minutes)
4. **Test with actual data** (verify documents exist with metadata)

---

## Estimated Fix Time
**Total**: ~30 minutes to fully fix

---

## Notes
- Frontend needs to know the product category format from the beginning
- Backend query method needs to handle Django JSONField properly
- Consider adding a helper function to map all product slugs to their full codes

