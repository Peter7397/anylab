# Webpage Recursive Crawler Implementation Plan (Option B)

## Overview
Implement a full-featured recursive webpage crawler with depth control, file preview, enhanced detection, and performance optimizations for the upload queue system.

---

## Architecture & Design Decisions

### 1. **Two-Phase Approach**
   - **Phase 1: Discovery** - Crawl and discover files (async, returns immediately)
   - **Phase 2: Queue** - User reviews and selects files, then queues for download

### 2. **Crawler Architecture**
   - **New Service Class**: `WebpageCrawler` (separate from `UploadQueueManager`)
   - **Crawl State Management**: Track visited URLs, depth levels, discovered files
   - **Concurrent Processing**: Use threading/async for parallel page fetching (with limits)
   - **Robots.txt Support**: Respect robots.txt rules (using `urllib.robotparser`)

### 3. **File Discovery Enhancements**
   - **Multiple Detection Methods**:
     - Direct links (`<a href>`)
     - Embedded content (`<iframe>`, `<embed>`, `<object>`)
     - JavaScript-rendered URLs (basic regex extraction)
     - Content-Type headers (not just file extensions)
     - `data-*` attributes
   - **File Type Detection**: Extension-based + Content-Type header
   - **Size Detection**: HEAD requests to get file size before queuing

### 4. **User Interface Flow**
   ```
   User enters URL → Discovery starts → Progress shown → 
   Files preview modal → User selects/deselects → Queue selected files
   ```

---

## Implementation Phases

### **Phase 1: Backend - Core Crawler Service** (4-6 hours)
**File**: `backend/ai_assistant/service_classes/webpage_crawler.py` (NEW)

**Features**:
1. **Crawler Class** with configuration:
   ```python
   class WebpageCrawlerConfig:
       max_depth: int = 2  # Default depth
       max_pages: int = 50  # Max pages to crawl
       max_files: int = 200  # Max files to discover
       same_domain_only: bool = True  # Only crawl same domain
       respect_robots_txt: bool = True
       delay_between_requests: float = 1.0  # Rate limiting
       timeout_per_page: int = 30
       concurrent_requests: int = 3  # Parallel requests
       file_type_filters: List[str] = []  # Optional filters
       max_file_size_mb: int = 100  # Skip files larger than this
   ```

2. **Core Methods**:
   - `crawl_webpage(url, config)` - Main entry point
   - `_crawl_recursive(url, depth, visited, discovered_files)` - Recursive crawler
   - `_discover_files_on_page(soup, base_url)` - Enhanced file discovery
   - `_check_robots_txt(url)` - Robots.txt validation
   - `_is_same_domain(url1, url2)` - Domain checking
   - `_get_file_info(url)` - HEAD request for size/type

3. **Enhanced File Discovery**:
   - Parse `<a>`, `<link>`, `<iframe>`, `<embed>`, `<object>` tags
   - Extract URLs from JavaScript (basic regex: `/https?:\/\/[^\s"'<>]+\.(pdf|docx?|xlsx?|pptx?)/i`)
   - Check `data-src`, `data-url`, `data-href` attributes
   - Use Content-Type headers when extension is missing

4. **Threading/Concurrency**:
   - Use `ThreadPoolExecutor` for parallel page fetching
   - Queue-based URL processing
   - Thread-safe visited URL tracking

---

### **Phase 2: Backend - API Endpoints** (2-3 hours)
**File**: `backend/ai_assistant/views/upload_queue_views.py` (MODIFY)

**New Endpoints**:
1. **POST `/api/ai/upload/discover-webpage/`** - Discovery only (no queue)
   ```json
   Request: {
     "url": "https://example.com",
     "max_depth": 2,
     "same_domain_only": true,
     "file_type_filters": ["pdf", "docx"],
     "max_file_size_mb": 50
   }
   
   Response: {
     "success": true,
     "data": {
       "discovered_files": [
         {
           "url": "https://example.com/file.pdf",
           "name": "file.pdf",
           "type": "pdf",
           "size": 1024000,
           "size_mb": 1.0,
           "discovered_from": "https://example.com/page1"
         }
       ],
       "total_pages_crawled": 5,
       "total_files_found": 12,
       "crawl_time_seconds": 8.5
     }
   }
   ```

2. **POST `/api/ai/upload/queue-webpage-files/`** - Queue selected files
   ```json
   Request: {
     "files": [
       {"url": "...", "name": "..."},
       ...
     ],
     "source": "https://example.com"
   }
   ```

**Modifications**:
- Update existing `create_upload_job` to support new workflow
- Add progress tracking for discovery (optional: WebSocket/SSE for real-time updates)

---

### **Phase 3: Frontend - Discovery UI** (3-4 hours)
**File**: `frontend/src/components/AI/UnifiedUploadQueue.tsx` (MODIFY)

**New Components**:
1. **Webpage Discovery Form**:
   - URL input
   - Depth selector (0-5, default: 2)
   - Checkbox: "Same domain only"
   - File type filters (multi-select: PDF, DOC, XLS, PPT, etc.)
   - Max file size slider (MB)
   - "Discover Files" button

2. **Discovery Progress Modal**:
   - Progress bar
   - Status text: "Crawling page 3/10...", "Found 15 files..."
   - Cancel button
   - Real-time updates (polling every 2 seconds)

3. **File Preview Modal** (after discovery):
   - Table with columns:
     - Checkbox (select/deselect)
     - File name
     - File type (with icon)
     - Size
     - Source page URL
     - Actions: Preview link (open in new tab)
   - "Select All" / "Deselect All" buttons
   - Filter/search bar
   - Summary: "X files selected (Y MB total)"
   - "Queue Selected Files" button

**State Management**:
```typescript
const [discoveryConfig, setDiscoveryConfig] = useState({
  url: '',
  maxDepth: 2,
  sameDomainOnly: true,
  fileTypeFilters: [] as string[],
  maxFileSizeMB: 100
});
const [discoveryInProgress, setDiscoveryInProgress] = useState(false);
const [discoveredFiles, setDiscoveredFiles] = useState<DiscoveredFile[]>([]);
const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
const [discoveryProgress, setDiscoveryProgress] = useState({
  pagesCrawled: 0,
  filesFound: 0,
  status: ''
});
```

---

### **Phase 4: Frontend - API Integration** (2 hours)
**File**: `frontend/src/services/api.ts` (MODIFY)

**New Methods**:
```typescript
async discoverWebpageFiles(config: {
  url: string;
  max_depth?: number;
  same_domain_only?: boolean;
  file_type_filters?: string[];
  max_file_size_mb?: number;
}): Promise<any> {
  const response = await this.request('/ai/upload/discover-webpage/', {
    method: 'POST',
    body: JSON.stringify(config)
  });
  return response.data;
}

async queueWebpageFiles(files: any[], source: string): Promise<any> {
  const response = await this.request('/ai/upload/queue-webpage-files/', {
    method: 'POST',
    body: JSON.stringify({ files, source })
  });
  return response.data;
}
```

---

### **Phase 5: Backend - Performance & Safety** (2-3 hours)

**Optimizations**:
1. **Caching**:
   - Cache discovered files per URL (Redis/Django cache)
   - Cache robots.txt parsing
   - TTL: 1 hour

2. **Rate Limiting**:
   - Configurable delay between requests
   - Respect server response headers (Retry-After)
   - Exponential backoff on errors

3. **Memory Management**:
   - Stream large HTML responses
   - Limit concurrent requests
   - Clean up visited URL sets after crawl

4. **Error Handling**:
   - Skip pages that fail (log and continue)
   - Timeout handling per page
   - Network error retries (max 3 attempts)

5. **Security**:
   - Validate URLs (prevent SSRF)
   - Sanitize file names
   - Limit crawl scope (same domain by default)

---

### **Phase 6: Testing & Refinement** (2-3 hours)

**Test Cases**:
1. **Single Page Discovery** (depth=0)
2. **Recursive Crawling** (depth=1, 2)
3. **Domain Restriction** (same_domain_only=true/false)
4. **File Type Filtering**
5. **Size Filtering**
6. **Robots.txt Compliance**
7. **Error Handling** (404, timeout, network errors)
8. **Concurrent Request Limits**
9. **Large Site Handling** (100+ pages)

**Test URLs**:
- Simple static site with PDFs
- Multi-page documentation site
- Site with robots.txt restrictions
- Site with JavaScript-rendered content

---

## Technical Considerations

### **Dependencies**
- **New Python Packages** (if needed):
  - `urllib.robotparser` (built-in) - Robots.txt parsing
  - `concurrent.futures` (built-in) - Threading
  - Existing: `requests`, `beautifulsoup4`

### **Database Changes**
- **None required** - Uses existing `UploadJob` model

### **Configuration**
- Add to `settings.py`:
  ```python
  WEBPAGE_CRAWLER_CONFIG = {
      'default_max_depth': 2,
      'default_max_pages': 50,
      'default_max_files': 200,
      'default_delay_seconds': 1.0,
      'default_concurrent_requests': 3,
      'default_timeout_seconds': 30,
      'respect_robots_txt': True,
  }
  ```

### **Backward Compatibility**
- Keep existing `discover_webpage_files()` method (single-page)
- New recursive crawler is opt-in via API parameters
- Old workflow still works (direct queue without preview)

---

## UI/UX Flow Diagram

```
┌─────────────────────────────────────┐
│  Webpage Tab                        │
│  ┌───────────────────────────────┐  │
│  │ URL: [https://example.com]   │  │
│  │ Depth: [2 ▼]                  │  │
│  │ ☑ Same domain only            │  │
│  │ File types: [PDF ☑] [DOC ☐]  │  │
│  │ Max size: [100 MB]            │  │
│  │ [Discover Files]              │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  Discovery Progress Modal            │
│  ┌───────────────────────────────┐  │
│  │ ════════════░░░░░░░░░░ 60%    │  │
│  │ Crawling page 5/10...         │  │
│  │ Found 23 files so far         │  │
│  │ [Cancel]                       │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  File Preview Modal                  │
│  ┌───────────────────────────────┐  │
│  │ ☑ All  │ Name │ Type │ Size  │  │
│  │ ☑      │ doc1 │ PDF  │ 2.1MB │  │
│  │ ☑      │ doc2 │ DOCX │ 1.5MB │  │
│  │ ☐      │ img1 │ JPG  │ 500KB │  │
│  │ ...                            │  │
│  │ Selected: 2 files (3.6 MB)    │  │
│  │ [Queue Selected Files]         │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  Upload Queue                        │
│  (Job appears with all queued files) │
└─────────────────────────────────────┘
```

---

## Estimated Timeline

| Phase | Task | Hours | Dependencies |
|-------|------|-------|--------------|
| 1 | Backend - Core Crawler | 4-6 | None |
| 2 | Backend - API Endpoints | 2-3 | Phase 1 |
| 3 | Frontend - Discovery UI | 3-4 | Phase 2 |
| 4 | Frontend - API Integration | 2 | Phase 2 |
| 5 | Backend - Performance & Safety | 2-3 | Phase 1, 2 |
| 6 | Testing & Refinement | 2-3 | All phases |
| **Total** | | **15-21 hours** | |

**Estimated Duration**: 2-3 days of focused development

---

## Risk Assessment & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Crawler gets stuck in infinite loop | High | Medium | Implement visited URL tracking, max pages limit |
| Server overloads target website | High | Medium | Rate limiting, delays, concurrent request limits |
| Memory issues on large sites | Medium | Low | Stream responses, limit concurrent requests, cleanup |
| JavaScript-rendered content missed | Medium | High | Accept limitation, document it, future: Selenium integration |
| Robots.txt parsing errors | Low | Low | Fallback to permissive mode, log errors |
| Network timeouts | Medium | Medium | Retry logic, timeout configuration |

---

## Future Enhancements (Post-MVP)

1. **JavaScript Rendering**: Integrate Selenium/Playwright for SPAs
2. **Sitemap.xml Support**: Use sitemaps for faster discovery
3. **Incremental Discovery**: Resume interrupted crawls
4. **Export/Import**: Save discovered file lists
5. **Scheduled Crawls**: Periodic re-crawling of URLs
6. **Advanced Filters**: Regex patterns, URL patterns, date ranges

---

## Success Criteria

✅ **Functional Requirements**:
- [ ] Recursive crawling up to depth 5
- [ ] File preview before queuing
- [ ] File type and size filtering
- [ ] Same-domain restriction option
- [ ] Progress indication during discovery
- [ ] Respect robots.txt

✅ **Performance Requirements**:
- [ ] Discovery completes in < 60 seconds for 50 pages
- [ ] Memory usage < 500MB for typical crawl
- [ ] No server overload (rate limiting works)

✅ **User Experience**:
- [ ] Intuitive UI with clear options
- [ ] Real-time progress feedback
- [ ] Easy file selection/deselection
- [ ] Clear error messages

---

## Questions for Review

1. **Depth Limit**: Maximum depth? (Recommend: 5)
2. **Default Settings**: What should defaults be? (Recommend: depth=2, same_domain_only=true)
3. **File Size Limit**: Default max file size? (Recommend: 100MB)
4. **Concurrent Requests**: How many parallel requests? (Recommend: 3)
5. **Progress Updates**: Real-time (WebSocket) or polling? (Recommend: polling for simplicity)
6. **JavaScript Support**: Include Selenium now or later? (Recommend: later, document limitation)

---

## Next Steps

1. **Review this plan** - Confirm approach and settings
2. **Approve dependencies** - Confirm no new packages needed
3. **Start Phase 1** - Begin backend crawler implementation
4. **Iterative development** - Test after each phase

---

**Document Version**: 1.0  
**Created**: 2025-12-28  
**Status**: Awaiting Review

