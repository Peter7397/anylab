# OnLab Backend API Documentation

---

## Table of Contents
1. [Authentication (JWT)](#authentication)
2. [PDF Management](#pdf-management)
3. [AI Assistant Endpoints](#ai-assistant)
4. [RAG Search Endpoints](#rag-search)
5. [Document Management](#document-management)
6. [Content Filtering](#content-filtering)
7. [User Management](#user-management)
8. [Health Check](#health-check)

---

## <a name="authentication"></a>1. Authentication (JWT)

### Obtain Token
- **Endpoint:** `POST /api/token/`
- **Description:** Obtain JWT access and refresh tokens
- **Request Body:**
```json
{
  "username": "your_username",
  "password": "your_password"
}
```
- **Response:**
```json
{
  "refresh": "<refresh_token>",
  "access": "<access_token>"
}
```

### Refresh Token
- **Endpoint:** `POST /api/token/refresh/`
- **Request Body:**
```json
{
  "refresh": "<refresh_token>"
}
```
- **Response:**
```json
{
  "access": "<new_access_token>"
}
```

### Verify Token
- **Endpoint:** `POST /api/token/verify/`
- **Request Body:**
```json
{
  "token": "<access_token>"
}
```
- **Response:**
```json
{}
```

---

## <a name="pdf-management"></a>2. PDF Management

### Upload PDF
- **Endpoint:** `POST /api/ai/pdfs/upload/`
- **Auth:** Optional (AllowAny by default)
- **Content-Type:** `multipart/form-data`
- **Form Data:**
  - `file`: PDF file (required)
  - `title`: string (required)
  - `description`: string (optional)
- **Response:**
```json
{
  "message": "PDF uploaded successfully.",
  "pdf": { ...pdf metadata... }
}
```

### List PDFs
- **Endpoint:** `GET /api/ai/pdfs/`
- **Auth:** Optional
- **Response:**
```json
{
  "pdfs": [ ... ],
  "count": 1
}
```

### Download PDF
- **Endpoint:** `GET /api/ai/pdfs/{id}/download/`
- **Auth:** Optional
- **Response:** PDF file (binary)

### Search PDFs
- **Endpoint:** `POST /api/ai/pdfs/search/`
- **Content-Type:** `application/json`
- **Body:**
```json
{
  "query": "search term",
  "search_type": "title|content|both"
}
```
- **Response:**
```json
{
  "pdfs": [ ... ],
  "count": 1,
  "query": "search term",
  "search_type": "title"
}
```

### Delete PDF
- **Endpoint:** `DELETE /api/ai/pdfs/{id}/delete/`
- **Auth:** Optional
- **Response:**
```json
{
  "message": "PDF deleted successfully."
}
```

---

## <a name="ai-assistant"></a>3. AI Assistant Endpoints

### Chat with AI
- **Endpoint:** `POST /api/ai/chat/`
- **Body:**
```json
{
  "message": "Your question here"
}
```
- **Response:**
```json
{
  "response": "AI's answer"
}
```

### Generate Embeddings
- **Endpoint:** `POST /api/ai/embeddings/`
- **Body:**
```json
{
  "text": "Text to embed"
}
```
- **Response:**
```json
{
  "embedding": [ ... ]
}
```

### Model Info
- **Endpoint:** `GET /api/ai/model-info/`
- **Response:**
```json
{
  "model": "qwen:latest",
  "details": { ... }
}
```

### RAG PDF Upload (for future use)
- **Endpoint:** `POST /api/ai/rag/upload/`
- **Form Data:**
  - `file`: PDF file
- **Response:**
```json
{
  "message": "RAG service is temporarily disabled."
}
```

---

## <a name="rag-search"></a>4. RAG Search Endpoints

### Basic RAG Search
- **Endpoint:** `POST /api/ai/rag/search/`
- **Auth:** Required
- **Content-Type:** `application/json`
- **Request Body:**
```json
{
  "query": "your search query",
  "top_k": 8,
  "search_mode": "enhanced"
}
```
- **Response:**
```json
{
  "message": "RAG search completed successfully",
  "data": {
    "response": "AI generated answer",
    "sources": [...],
    "query": "your search query",
    "performance": {
      "search_time_ms": 1234.56,
      "total_time_ms": 1456.78,
      "search_mode": "enhanced",
      "top_k": 8
    }
  }
}
```

### Advanced RAG Search
- **Endpoint:** `POST /api/ai/rag/search/advanced/`
- **Auth:** Required
- **Content-Type:** `application/json`
- **Request Body:**
```json
{
  "query": "your search query",
  "top_k": 8,
  "search_mode": "hybrid"
}
```
- **Response:** Same as Basic RAG, with hybrid search + reranking

### Comprehensive RAG Search
- **Endpoint:** `POST /api/ai/rag/search/comprehensive/`
- **Auth:** Required
- **Content-Type:** `application/json`
- **Request Body:**
```json
{
  "query": "your search query",
  "top_k": 15,
  "include_stats": false
}
```
- **Response:** Maximum detail with 15 results

### Vector Search
- **Endpoint:** `POST /api/ai/rag/search/vector/`
- **Auth:** Required
- **Content-Type:** `application/json`
- **Request Body:**
```json
{
  "query": "your search query",
  "top_k": 5
}
```
- **Response:** Vector similarity results

---

## <a name="document-management"></a>5. Document Management Endpoints

### List Documents
- **Endpoint:** `GET /api/ai/documents/`
- **Auth:** Required
- **Query Parameters:**
  - `page`: int (default: 1)
  - `page_size`: int (default: 20)
- **Response:**
```json
{
  "message": "Documents retrieved successfully",
  "documents": [...],
  "total": 17,
  "page": 1,
  "page_size": 20
}
```

### Upload Document
- **Endpoint:** `POST /api/ai/documents/upload/`
- **Auth:** Required
- **Content-Type:** `multipart/form-data`
- **Form Data:**
  - `file`: Document file
  - `title`: string
  - `description`: string
- **Response:** Document metadata

### Download Document
- **Endpoint:** `GET /api/ai/documents/{id}/download/`
- **Auth:** Required
- **Response:** File download

### Delete Document
- **Endpoint:** `DELETE /api/ai/documents/{id}/delete/`
- **Auth:** Required
- **Response:** Success message

### Search Documents
- **Endpoint:** `POST /api/ai/documents/search/`
- **Auth:** Required
- **Request Body:**
```json
{
  "query": "search term",
  "search_type": "title|description|both"
}
```
- **Response:** Search results

### Query History
- **Endpoint:** `GET /api/ai/documents/history/`
- **Auth:** Required
- **Query Parameters:**
  - `page`: int (default: 1)
  - `page_size`: int (default: 50)
- **Response:** User's query history

### Index Information
- **Endpoint:** `GET /api/ai/documents/index/info/`
- **Auth:** Required
- **Response:** Index statistics and distribution

### List Uploaded Files
- **Endpoint:** `GET /api/ai/documents/files/`
- **Auth:** Required
- **Query Parameters:**
  - `page`: int (default: 1)
  - `page_size`: int (default: 50)
- **Response:** List of uploaded files

### Performance Statistics
- **Endpoint:** `GET /api/ai/documents/performance/stats/`
- **Auth:** Required
- **Response:** System performance metrics

### Search Analytics
- **Endpoint:** `GET /api/ai/documents/search/analytics/`
- **Auth:** Required
- **Response:** Search analytics and statistics

---

## <a name="content-filtering"></a>6. Content Filtering Endpoints

### Filter Documents
- **Endpoint:** `POST /api/ai/content/filter/`
- **Auth:** Required
- **Request Body:**
```json
{
  "query": "search query",
  "organization_mode": "general|lab-informatics",
  "filters": [
    {
      "field": "document_type",
      "operator": "equals",
      "value": "pdf"
    }
  ],
  "sort_order": "relevance|date_newest|date_oldest",
  "page": 1,
  "page_size": 20
}
```
- **Response:** Filtered documents with metadata

### Get Filter Suggestions
- **Endpoint:** `GET /api/ai/content/suggestions/`
- **Auth:** Required
- **Query Parameters:**
  - `organization_mode`: "general|lab-informatics"
- **Response:** Available filter options

### Save Filter Preset
- **Endpoint:** `POST /api/ai/content/presets/`
- **Auth:** Required
- **Request Body:**
```json
{
  "name": "My Preset",
  "preset_data": {
    "filters": [...],
    "organization_mode": "general"
  }
}
```
- **Response:** Saved preset ID

---

## <a name="user-management"></a>7. User Management

### List Users
- **Endpoint:** `GET /api/users/`
- **Auth:** JWT required
- **Response:**
```json
[
  {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    ...
  }
]
```

### Create User
- **Endpoint:** `POST /api/users/`
- **Auth:** JWT required
- **Body:**
```json
{
  "username": "newuser",
  "password": "password",
  "email": "user@example.com"
}
```
- **Response:**
```json
{
  "id": 2,
  "username": "newuser",
  ...
}
```

### Get User Details
- **Endpoint:** `GET /api/users/{id}/`
- **Auth:** JWT required
- **Response:**
```json
{
  "id": 2,
  "username": "newuser",
  ...
}
```

### Update User
- **Endpoint:** `PUT /api/users/{id}/`
- **Auth:** JWT required
- **Body:**
```json
{
  "email": "newemail@example.com"
}
```
- **Response:**
```json
{
  "id": 2,
  "username": "newuser",
  "email": "newemail@example.com",
  ...
}
```

### Delete User
- **Endpoint:** `DELETE /api/users/{id}/`
- **Auth:** JWT required
- **Response:**
```json
{
  "message": "User deleted successfully."
}
```

---

## <a name="health-check"></a>8. Health Check

### Health Check
- **Endpoint:** `GET /api/health/`
- **Response:**
```json
{
  "status": "healthy",
  "service": "onlab-backend"
}
```

---

## Notes
- All endpoints under `/api/`.
- JWT authentication required for user management and some AI endpoints.
- PDF endpoints are open by default but can be restricted in production.
- For file uploads, use `multipart/form-data`.
- For all other POST/PUT requests, use `application/json`.

---

**Last updated:** $(date)
