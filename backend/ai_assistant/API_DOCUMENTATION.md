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
RAG (Retrieval-Augmented Generation) operations, content scraping, and analytics.

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
