"""
API Documentation

This module provides comprehensive API documentation for the AI Assistant application.
"""

# API Documentation for AI Assistant
# ===================================

"""
# AI Assistant API Documentation

## Overview
The AI Assistant API provides comprehensive functionality for document management, 
RAG (Retrieval-Augmented Generation) operations, content scraping, users/roles management,
and analytics.

## Update: December 2024

**New Features Added:**
- ✅ Complete Users & Roles management system
- ✅ Scraper API integration (SSB, GitHub, Forum, HTML)
- ✅ Enhanced document types support
- ✅ Source URL tracking for scraped content
- ✅ Metadata support for documents

## Base URL
```
https://anylab.dpdns.org/api/ai/
```

## Authentication
All endpoints require authentication using JWT tokens.

## Response Format
All responses follow a consistent format:

### Success Response
```json
{
    "message": "Operation completed successfully",
    "timestamp": "2024-01-01T00:00:00Z",
    "data": { ... }
}
```

### Error Response
```json
{
    "error": {
        "type": "ErrorType",
        "message": "Error message",
        "code": "error_code",
        "timestamp": "2024-01-01T00:00:00Z",
        "suggestion": "Helpful suggestion"
    }
}
```

## Endpoints

### Users & Roles Management (NEW)

#### List All Roles
- **GET** `/api/users/roles/`
- **Description**: List all available roles
- **Permission**: Admin only
- **Response**: Array of role objects

#### Create Role
- **POST** `/api/users/roles/`
- **Description**: Create a new role
- **Permission**: Admin only
- **Request Body**:
  ```json
  {
      "name": "Role Name",
      "description": "Role description",
      "permissions": {},
      "is_active": true
  }
  ```

#### Role Detail
- **GET** `/api/users/roles/<id>/` - Get role details
- **PUT** `/api/users/roles/<id>/` - Update role
- **DELETE** `/api/users/roles/<id>/` - Delete role

#### Assign Role to User
- **POST** `/api/users/roles/assign/`
- **Description**: Assign a role to a user
- **Permission**: Admin only
- **Request Body**:
  ```json
  {
      "user_id": 1,
      "role_id": 2
  }
  ```

#### Remove Role from User
- **POST** `/api/users/roles/remove/`
- **Description**: Remove a role from a user
- **Permission**: Admin only

#### Get User's Roles
- **GET** `/api/users/<user_id>/roles/`
- **Description**: Get all roles assigned to a user
- **Response**: Array of role assignments

### RAG Operations

#### Chat with Ollama
- **POST** `/rag/chat/`
- **Description**: Generate chat responses using Ollama
- **Request Body**:
  ```json
  {
      "prompt": "Your question here",
      "max_tokens": 256,
      "temperature": 0.3,
      "top_p": 0.9,
      "top_k": 40,
      "repeat_penalty": 1.1,
      "num_ctx": 1024
  }
  ```
- **Response**: Chat response with generated text

#### RAG Search
- **POST** `/rag/search/`
- **Description**: Perform RAG search with different modes
- **Request Body**:
  ```json
  {
      "query": "Search query",
      "search_mode": "comprehensive",
      "top_k": 10,
      "include_stats": false
  }
  ```
- **Response**: Search results with relevant documents

#### Vector Search
- **POST** `/rag/search/vector/`
- **Description**: Perform vector similarity search
- **Request Body**:
  ```json
  {
      "query": "Search query",
      "search_mode": "comprehensive",
      "top_k": 10
  }
  ```
- **Response**: Vector search results

#### Document Upload
- **POST** `/rag/upload/pdf/`
- **Description**: Upload and process PDF documents
- **Request Body**: Multipart form data with file
- **Response**: Upload confirmation and processing results

### SSB Scraper Operations

#### Scrape SSB Database
- **POST** `/ssb/scrape/database/`
- **Description**: Scrape Service Support Bulletin database
- **Request Body**:
  ```json
  {
      "config": {
          "max_pages": 100,
          "delay_between_requests": 1.0,
          "timeout": 30,
          "retry_attempts": 3
      }
  }
  ```
- **Response**: Scraping results and statistics

#### Get SSB Status
- **GET** `/ssb/status/`
- **Description**: Get current SSB scraping status
- **Response**: Status information and statistics

### Content Management

#### Filter Documents
- **POST** `/content/filter/`
- **Description**: Filter documents based on criteria
- **Request Body**:
  ```json
  {
      "query": "Search query",
      "organization_mode": "general",
      "filters": [
          {
              "field": "document_type",
              "operator": "eq",
              "value": "PDF"
          }
      ],
      "sort_order": "relevance",
      "page": 1,
      "page_size": 20
  }
  ```
- **Response**: Filtered documents and metadata

#### Get Filter Suggestions
- **GET** `/content/filter/suggestions/`
- **Description**: Get dynamic filter suggestions
- **Query Parameters**: `organization_mode`
- **Response**: Available filter options

### Document Management

#### List Documents
- **GET** `/documents/`
- **Description**: List all documents
- **Response**: Document list with metadata

#### Upload Document
- **POST** `/documents/upload/`
- **Description**: Upload documents
- **Request Body**: Multipart form data
- **Response**: Upload confirmation

### Bulk Import (NEW)

#### Scan Folder
- **POST** `/api/ai/bulk-import/scan/`
- **Description**: Scan a folder and discover supported files
- **Request Body**:
  ```json
  {
      "folder_path": "/path/to/folder"
  }
  ```
- **Response**:
  ```json
  {
      "success": true,
      "folder_path": "/path/to/folder",
      "file_count": 25,
      "total_size": 10485760,
      "files": [
          {
              "filename": "document.pdf",
              "file_path": "/path/to/document.pdf",
              "file_size": 102400,
              "file_extension": ".pdf",
              "relative_path": "document.pdf"
          }
      ]
  }
  ```

#### Bulk Import Files
- **POST** `/api/ai/bulk-import/`
- **Description**: Import multiple files from a scanned folder
- **Request Body**:
  ```json
  {
      "files": [
          {
              "file_path": "/path/to/document.pdf",
              "filename": "document.pdf"
          }
      ]
  }
  ```
- **Response**:
  ```json
  {
      "success": true,
      "results": {
          "total": 10,
          "successful": 8,
          "failed": 1,
          "skipped": 1,
          "details": [
              {
                  "filename": "document.pdf",
                  "status": "success",
                  "uploaded_file_id": 123,
                  "document_id": 456,
                  "file_url": "/api/ai/documents/456/",
                  "document_type": "pdf"
              }
          ],
          "errors": []
      }
  }
  ```
- **Features**:
  - Creates both `UploadedFile` AND `DocumentFile` records
  - Automatic metadata extraction (product category, version, content type)
  - File deduplication (hash-based + filename)
  - Error handling per file (doesn't stop entire import)
  - Automatic processing via async Celery tasks

#### Get Bulk Import Status
- **GET** `/api/ai/bulk-import/status/`
- **Description**: Get status of bulk import operations
- **Query Parameters**: `status` (optional: pending, metadata_extracting, chunking, embedding, ready, failed)
- **Response**:
  ```json
  {
      "success": true,
      "files": [
          {
              "id": 123,
              "filename": "document.pdf",
              "file_size": 102400,
              "processing_status": "ready",
              "chunk_count": 45,
              "embedding_count": 45,
              "metadata_extracted": true,
              "chunks_created": true,
              "embeddings_created": true,
              "is_ready": true,
              "document_id": 456,
              "document_title": "document",
              "document_type": "pdf",
              "file_url": "/api/ai/documents/456/",
              "uploaded_at": "2024-01-01T00:00:00Z"
          }
      ],
      "statistics": {
          "total": 100,
          "pending": 5,
          "metadata_extracting": 2,
          "chunking": 3,
          "embedding": 4,
          "ready": 85,
          "failed": 1,
          "document_files_total": 100,
          "document_files_with_uploaded_files": 95,
          "document_files_ready": 85,
          "document_files_processing": 10
      }
  }
  ```

#### Key Features of Bulk Import
- ✅ **Automatic DocumentFile Creation**: Creates both UploadedFile and DocumentFile records
- ✅ **Async Processing**: Uses Celery for background processing (metadata, chunking, embedding)
- ✅ **Crash Prevention**: 2000 chunk limit per document prevents server crashes
- ✅ **Metadata Extraction**: Automatically detects product category, version, content type
- ✅ **File Deduplication**: Prevents duplicate imports using hash + filename
- ✅ **Error Isolation**: Per-file error handling doesn't stop entire import
- ✅ **URL Generation**: file_url automatically generated for API access
- ✅ **Status Tracking**: Track processing status in real-time

## Error Codes

| Code | Description |
|------|-------------|
| `rag_service_error` | RAG service unavailable |
| `scraping_error` | Scraping operation failed |
| `validation_error` | Request validation failed |
| `authentication_error` | Authentication required |
| `permission_error` | Permission denied |
| `not_found_error` | Resource not found |
| `rate_limit_error` | Rate limit exceeded |
| `external_service_error` | External service unavailable |

## Rate Limits
- Chat requests: 60 requests per minute
- Search requests: 120 requests per minute
- Upload requests: 10 requests per minute
- Scraping requests: 5 requests per minute

## Examples

### Chat Request
```bash
curl -X POST "https://anylab.dpdns.org/api/ai/rag/chat/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is the best way to troubleshoot OpenLab issues?",
    "max_tokens": 256,
    "temperature": 0.3
  }'
```

### Search Request
```bash
curl -X POST "https://anylab.dpdns.org/api/ai/rag/search/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "OpenLab troubleshooting",
    "search_mode": "comprehensive",
    "top_k": 10
  }'
```

### Document Upload
```bash
curl -X POST "https://anylab.dpdns.org/api/ai/rag/upload/pdf/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@document.pdf" \
  -F "title=Test Document" \
  -F "description=Test PDF document"
```

## Support
For API support and questions, please contact the development team.
"""
