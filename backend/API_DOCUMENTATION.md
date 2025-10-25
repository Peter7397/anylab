# OnLab Backend API Documentation

---

## Table of Contents
1. [Authentication (JWT)](#authentication)
2. [PDF Management](#pdf-management)
3. [AI Assistant Endpoints](#ai-assistant)
4. [User Management](#user-management)
5. [Health Check](#health-check)

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

## <a name="user-management"></a>4. User Management

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

## <a name="health-check"></a>5. Health Check

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
