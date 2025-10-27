# Debug Steps for UI KPR Display Issue

## Current Status
- ✅ Backend has 2,246 KPR entries in database
- ✅ API returns 2,246 results (verified in logs)
- ✅ Serializer now includes 'metadata' field
- ❌ UI shows "No SSB Entries Found"

## Check These in Browser DevTools

### 1. Network Tab
1. Open Browser DevTools (F12)
2. Go to Network tab
3. Load the SSB page
4. Find the request to `/api/ai/documents/search/`
5. Click on it
6. Go to "Response" tab
7. Look at the JSON response

**Expected:**
```json
{
  "success": true,
  "message": "Documents found",
  "data": {
    "results": [
      {
        "id": 2292,
        "title": "Product:68xx Driver Software 6890 6.25",
        "document_type": "SSB_KPR",
        "metadata": {...},
        "description": "..."
      },
      ...
    ],
    "count": 2246
  }
}
```

### 2. Console Tab
Look for errors like:
- "Cannot read property 'map' of undefined"
- "results is undefined"

### 3. Check the Mapping
In SSBDatabase.tsx line 102, verify:
```typescript
const entries: SSBEntry[] = documents.data?.results?.map((doc: any) => {
```

The structure might be:
- `documents.data.results` - array of docs
- `documents.data.count` - total count

## Common Issues

### Issue 1: Wrong Response Structure
If the API response is:
```json
{"results": [...], "count": 2246}
```

But we're expecting:
```json
{"data": {"results": [...], "count": 2246}}
```

### Issue 2: Metadata Parsing
The frontend expects `doc.metadata` to be a string (JSON), then parses it.
But if backend already returns parsed JSON, this will fail.

## Quick Fix to Test
Add console.log to see what's being received:

```typescript
const documents = await apiClient.searchDocuments('', 'both', 'SSB_KPR');
console.log('API Response:', documents);
console.log('Results:', documents.data?.results?.length);
```

