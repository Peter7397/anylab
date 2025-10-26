# RAG Endpoints Summary

## Backend Endpoints (Configured)

### Base URL: `/api/ai/rag/`

All endpoints require:
- **Method**: POST
- **Authentication**: Required (JWT token)
- **Content-Type**: application/json

### 1. Basic RAG Search
- **Endpoint**: `/api/ai/rag/search/`
- **View**: `rag_search()`
- **Parameters**: `query`, `top_k`, `search_mode`
- **Description**: Enhanced RAG search with improved chunking and similarity scoring

### 2. Advanced RAG Search  
- **Endpoint**: `/api/ai/rag/search/advanced/`
- **View**: `advanced_rag_search()`
- **Parameters**: `query`, `top_k`, `search_mode` (default: 'hybrid')
- **Description**: Advanced RAG search with hybrid search and reranking

### 3. Comprehensive RAG Search
- **Endpoint**: `/api/ai/rag/search/comprehensive/`
- **View**: `comprehensive_rag_search()`
- **Parameters**: `query`, `top_k`, `include_stats`
- **Description**: Comprehensive RAG search with maximum detail and complete answers

### 4. Vector Search
- **Endpoint**: `/api/ai/rag/search/vector/`
- **View**: `vector_search()`
- **Parameters**: `query`, `top_k`, `search_mode`
- **Description**: Vector similarity search with history tracking

### 5. Chat with Ollama
- **Endpoint**: `/api/ai/rag/chat/`
- **View**: `chat_with_ollama()`
- **Parameters**: `prompt`, plus generation parameters
- **Description**: Direct chat with Ollama without RAG

## Frontend API Methods

### API Client Methods in `api.ts`:

1. **`ragSearch(query, topK, searchMode)`**
   - Calls: `/ai/rag/search/`
   - Defaults: topK=10, searchMode='advanced'

2. **`advancedRagSearch(query, topK, searchMode)`**
   - Calls: `/ai/rag/search/advanced/`
   - Defaults: topK=5, searchMode='hybrid'

3. **`comprehensiveRagSearch(query, topK, includeStats)`**
   - Calls: `/ai/rag/search/comprehensive/`
   - Defaults: topK=10, includeStats=false

4. **`vectorSearch(query, topK)`**
   - Calls: `/ai/rag/search/vector/`
   - Defaults: topK=5

5. **`ragChat(prompt)`**
   - Calls: `/ai/rag/chat/`
   - Description: Direct chat without retrieval

## React Components Using RAG

1. **RagSearch.tsx** - Uses `advancedRagSearch()`
2. **ComprehensiveRagSearch.tsx** - Uses `comprehensiveRagSearch()`
3. **BasicRagSearch.tsx** - Uses `ragSearch()`
4. **ChatAssistant.tsx** - Uses `ragChat()`

## Status

✅ All backend views have proper decorators
✅ All URL routes are configured correctly
✅ Frontend API paths updated to match backend
✅ All endpoints require authentication

## Testing

To test RAG search endpoints:
1. Log in to get authentication token
2. Send POST request with:
   ```json
   {
     "query": "your search query",
     "top_k": 8,
     "search_mode": "hybrid"
   }
   ```
3. Expected response includes:
   - `response`: AI-generated answer
   - `sources`: Array of source documents
   - `query`: Original query
   - Additional metadata (tokens_used, search_method, etc.)

