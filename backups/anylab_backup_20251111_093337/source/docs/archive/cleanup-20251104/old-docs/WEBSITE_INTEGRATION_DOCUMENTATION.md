# Website Integration Documentation

## Overview

The Website Integration feature allows users to add external websites to the RAG (Retrieval-Augmented Generation) system. These websites are automatically fetched, processed, and made searchable alongside regular documents.

## Architecture

### Backend Components

#### 1. Database Model (`WebsiteSource`)
- **Location**: `backend/ai_assistant/models.py`
- **Purpose**: Stores website metadata and processing status
- **Key Fields**:
  - `url`: Website URL (unique)
  - `domain`: Extracted domain name
  - `title`: Website title
  - `description`: User-provided description
  - `processing_status`: Current processing state
  - `chunk_count`: Number of content chunks created
  - `embedding_count`: Number of embeddings generated
  - `auto_refresh`: Whether to automatically refresh content
  - `refresh_interval_days`: How often to refresh (1, 7, or 30 days)

#### 2. Website Processor (`WebsiteProcessor`)
- **Location**: `backend/ai_assistant/website_processor.py`
- **Purpose**: Handles website content fetching and processing
- **Workflow**:
  1. Fetch HTML content from URL
  2. Parse and clean HTML using existing HTMLParser
  3. Convert to UploadedFile format
  4. Use AutomaticFileProcessor for metadata, chunking, and embeddings
  5. Update WebsiteSource status

#### 3. API Endpoints
- **Location**: `backend/ai_assistant/views/website_views.py`
- **Endpoints**:
  - `GET /api/ai/websites/` - List websites
  - `POST /api/ai/websites/add/` - Add new website
  - `GET /api/ai/websites/{id}/status/` - Get website status
  - `POST /api/ai/websites/{id}/refresh/` - Refresh website content
  - `DELETE /api/ai/websites/{id}/delete/` - Delete website
  - `POST /api/ai/websites/{id}/retry/` - Retry failed processing
  - `PUT /api/ai/websites/{id}/settings/` - Update website settings
  - `GET /api/ai/websites/statistics/` - Get website statistics

#### 4. Celery Tasks
- **Location**: `backend/ai_assistant/tasks.py`
- **Tasks**:
  - `process_website_automatically`: Process website content
  - `refresh_expired_websites`: Periodic refresh of expired websites

#### 5. Django Signals
- **Location**: `backend/ai_assistant/signals.py`
- **Purpose**: Automatically trigger processing when new websites are added

### Frontend Components

#### 1. Help Portal Component
- **Location**: `frontend/src/components/AI/HelpPortal.tsx`
- **Features**:
  - Tabbed interface (Documents | Websites)
  - Website statistics dashboard
  - Add website modal with validation
  - Website management table with actions
  - Real-time status polling
  - Progress indicators

#### 2. API Client Methods
- **Location**: `frontend/src/services/api.ts`
- **Methods**:
  - `getWebsites()` - Fetch websites with optional filtering
  - `addWebsite()` - Add new website
  - `getWebsiteStatus()` - Get processing status
  - `refreshWebsite()` - Trigger refresh
  - `deleteWebsite()` - Remove website
  - `retryWebsiteProcessing()` - Retry failed processing
  - `updateWebsiteSettings()` - Update settings
  - `getWebsiteStatistics()` - Get statistics

## Processing Pipeline

### 1. Website Addition
```
User adds URL → WebsiteSource created → Signal triggers → Celery task starts
```

### 2. Content Processing
```
Fetch HTML → Parse content → Convert to UploadedFile → Process via AutomaticFileProcessor
```

### 3. RAG Integration
```
Website content → DocumentChunk records → Vector embeddings → Searchable in RAG
```

## Configuration

### Periodic Refresh
- **Schedule**: Daily at 3:00 AM UTC
- **Configuration**: `backend/anylab/celery.py`
- **Task**: `refresh_expired_websites`

### Processing Settings
- **Chunk Size**: 600 characters (same as file uploads)
- **Chunk Overlap**: 120 characters (20%)
- **Embedding Model**: BGE-M3 (1024 dimensions)
- **Batch Size**: 50 chunks per API call

## Usage Guide

### Adding Websites

1. Navigate to Help Portal → External Website Sources tab
2. Click "Add Website" button
3. Enter website URL (required)
4. Optionally add title and description
5. Configure auto-refresh settings
6. Click "Add Website"

### Managing Websites

- **View Status**: Processing status with progress indicators
- **Refresh**: Manually refresh website content
- **Retry**: Retry failed processing
- **Delete**: Remove website and all associated data
- **Settings**: Update title, description, and refresh settings

### Monitoring

- **Statistics Dashboard**: Overview of all websites
- **Real-time Updates**: Status polling every 3 seconds for processing websites
- **Error Handling**: Clear error messages for failed processing

## API Reference

### Add Website
```http
POST /api/ai/websites/add/
Content-Type: application/json

{
  "url": "https://example.com",
  "title": "Example Website",
  "description": "Description of website content",
  "auto_refresh": true,
  "refresh_interval_days": 7
}
```

### List Websites
```http
GET /api/ai/websites/?status=ready&domain=example.com&search=keyword
```

### Refresh Website
```http
POST /api/ai/websites/123/refresh/
```

## Error Handling

### Common Issues

1. **Invalid URL**: Frontend validation prevents invalid URLs
2. **Duplicate URLs**: Backend and frontend check for duplicates
3. **Network Errors**: Retry mechanism with exponential backoff
4. **Processing Failures**: Clear error messages and retry options

### Status Codes

- `pending`: Waiting to be processed
- `fetching`: Downloading HTML content
- `metadata_extracting`: Extracting metadata
- `chunking`: Creating content chunks
- `embedding`: Generating vector embeddings
- `ready`: Successfully processed and searchable
- `failed`: Processing failed (with error details)

## Performance Considerations

### Caching
- HTML content cached during processing
- Embeddings cached for reuse
- Search results cached for 1 hour

### Rate Limiting
- Respects website robots.txt
- Configurable timeout settings
- Retry with exponential backoff

### Resource Management
- Maximum content size: 1MB per website
- Batch processing for embeddings
- Automatic cleanup of failed processing

## Security

### Content Validation
- URL format validation
- HTML sanitization
- Content size limits
- Domain whitelist support (configurable)

### Access Control
- Authentication required for all operations
- User attribution for added websites
- Admin-only access to certain operations

## Troubleshooting

### Website Not Processing
1. Check URL validity
2. Verify network connectivity
3. Check Celery worker status
4. Review error logs

### Content Not Appearing in Search
1. Verify processing completed successfully
2. Check chunk count > 0
3. Verify embeddings created
4. Test RAG search functionality

### Refresh Not Working
1. Check auto-refresh settings
2. Verify Celery beat scheduler
3. Check next_refresh_at timestamp
4. Review periodic task logs

## Future Enhancements

### Planned Features
- Multi-page website crawling
- Content change detection
- Advanced filtering options
- Bulk website operations
- Website health monitoring

### Integration Opportunities
- GitHub repository integration
- Documentation site crawling
- API documentation parsing
- Social media content integration

## Support

For technical support or feature requests, please contact the development team or create an issue in the project repository.
