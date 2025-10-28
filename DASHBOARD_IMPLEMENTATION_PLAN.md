# Dashboard & System Settings Implementation Plan

## Overview
Two main components to implement:
1. **Dashboard** - Main landing page showing system overview and activity
2. **System Settings** - Configuration page for all system parameters

---

## Phase 1: Backend API Endpoints

### 1.1 Dashboard API Endpoint
**File**: `backend/ai_assistant/views/__init__.py` or create `dashboard_views.py`

**Endpoint**: `GET /api/dashboard/stats/`

**Returns**:
```json
{
  "documents": {
    "total": 1234,
    "today": 5,
    "last_7_days": 45
  },
  "chunks": {
    "total": 15678,
    "with_embeddings": 15678,
    "pending": 0
  },
  "rag_queries": {
    "total": 890,
    "today": 12,
    "avg_response_time_ms": 234
  },
  "processing_queue": {
    "pending": 2,
    "processing": 1,
    "failed": 0
  },
  "recent_uploads": [...],
  "recent_queries": [...]
}
```

**Files to modify**:
- `backend/ai_assistant/views/dashboard_views.py` (NEW)
- `backend/ai_assistant/urls.py` (add dashboard URLs)

### 1.2 System Settings API Endpoints
**File**: `backend/ai_assistant/views/system_settings_views.py` (NEW)

**Endpoints**:
- `GET /api/admin/settings/` - Get all settings
- `POST /api/admin/settings/` - Update settings
- `GET /api/admin/settings/groups/` - Get settings by category
- `POST /api/admin/settings/test-connection/` - Test Ollama/Redis

**Returns**:
```json
{
  "file_upload": {
    "max_file_size": 524288000,
    "allowed_extensions": [".pdf", ".mhtml", ...],
    "enable_async_processing": false
  },
  "embeddings": {
    "mode": "auto",
    "model_name": "bge-m3:latest",
    "dimension": 1024,
    "cache_ttl": 86400
  },
  "rag": {
    "ollama_url": "http://localhost:11434",
    "model": "qwen2.5:latest",
    "temperature": 0.3,
    "max_tokens": 256
  }
}
```

### 1.3 Existing Endpoints to Verify
- `/api/ai/documents/` - Get document list
- `/api/ai/analytics/user/stats/` - User stats
- `/api/health/` - Health check
- `/api/ai/rag/info/` - RAG index info

---

## Phase 2: Frontend Dashboard Component

### 2.1 Create Dashboard Component
**File**: `frontend/src/components/Dashboard/Dashboard.tsx` (UPDATE existing)

**Features to implement**:
1. Stats cards (6 cards showing key metrics)
2. Recent uploads table
3. Processing queue status
4. Recent RAG queries chart
5. Quick actions panel
6. Alerts panel

**Components needed**:
- `StatsCard.tsx` (NEW or inline)
- `RecentUploads.tsx` (NEW or inline)
- `ProcessingQueue.tsx` (NEW or inline)
- `RAGActivityChart.tsx` (NEW or inline)
- `QuickActions.tsx` (NEW or inline)
- `AlertsPanel.tsx` (NEW or inline)

**API Integration**:
```typescript
// Add to frontend/src/services/api.ts
async getDashboardStats(): Promise<any> {
  const response = await this.request('/dashboard/stats/');
  return response.data;
}
```

### 2.2 Dashboard UI Layout
```
┌─────────────────────────────────────────────────┐
│  Stats Cards Row (6 cards)                     │
│  ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐         │
│  │D1 │ │D2 │ │D3 │ │D4 │ │D5 │ │D6 │         │
│  └───┘ └───┘ └───┘ └───┘ └───┘ └───┘         │
├─────────────────────────────────────────────────┤
│  Recent Uploads (Left) | Processing Queue (Right)│
│  ┌───────────────┬───────────────┐             │
│  │               │               │             │
│  │  Table        │   Status      │             │
│  │               │   Cards       │             │
│  └───────────────┴───────────────┘             │
├─────────────────────────────────────────────────┤
│  RAG Activity Chart                            │
│  ┌──────────────────────────────────────────┐  │
│  │     Line Chart / Bar Chart              │  │
│  └──────────────────────────────────────────┘  │
├─────────────────────────────────────────────────┤
│  Quick Actions | Alerts                         │
│  ┌───────────────┬───────────────┐             │
│  │  Button Grid  │  Alerts List │             │
│  └───────────────┴───────────────┘             │
└─────────────────────────────────────────────────┘
```

---

## Phase 3: Frontend System Settings Component

### 3.1 Create System Settings Component
**File**: `frontend/src/components/Administration/SystemSettings.tsx` (NEW)

**Features to implement**:
1. Tabbed interface for categories
2. Settings forms with validation
3. Test connection buttons
4. Export/Import settings
5. Reset to defaults
6. Save/Revert buttons

**API Integration**:
```typescript
// Add to frontend/src/services/api.ts
async getSystemSettings(): Promise<any> {
  const response = await this.request('/admin/settings/');
  return response.data;
}

async updateSystemSettings(settings: any): Promise<any> {
  const response = await this.request('/admin/settings/', {
    method: 'POST',
    body: JSON.stringify(settings)
  });
  return response.data;
}

async testConnection(type: string, config: any): Promise<any> {
  const response = await this.request('/admin/settings/test-connection/', {
    method: 'POST',
    body: JSON.stringify({ type, config })
  });
  return response.data;
}
```

### 3.2 System Settings UI Layout
```
┌─────────────────────────────────────────────────┐
│  Tab Navigation                                 │
│  [General] [Upload] [Embed] [RAG] [Cache] [...] │
├─────────────────────────────────────────────────┤
│                                                 │
│  Settings Form for Selected Tab                │
│  ┌────────────────────────────────────────┐   │
│  │ Setting 1: [Input Field]   [Description]│   │
│  │ Setting 2: [Dropdown]     [Test Button] │   │
│  │ Setting 3: [Toggle]                    │   │
│  │ ...                                     │   │
│  └────────────────────────────────────────┘   │
│                                                 │
│  [Save Changes] [Revert] [Reset to Defaults]  │
└─────────────────────────────────────────────────┘
```

**Tab Categories**:
1. **General** - Site name, URLs, debug mode
2. **File Upload** - Size limits, extensions, processing
3. **Embeddings** - Model, dimension, cache
4. **RAG** - Ollama config, generation params
5. **Cache** - Redis config, TTLs
6. **Workers** - Celery config
7. **Security** - CORS, cookies, headers
8. **Maintenance** - Actions, export/import

---

## Phase 4: Testing & Integration

### 4.1 Backend Testing
- Test all API endpoints return correct data
- Verify settings can be updated
- Test connection endpoints work
- Check authentication/permissions

### 4.2 Frontend Testing
- Verify Dashboard loads and displays data
- Test System Settings forms
- Test save/revert functionality
- Test export/import settings
- Verify mobile responsiveness

### 4.3 Integration Testing
- Upload document → verify it appears on dashboard
- Run RAG query → verify metrics update
- Change settings → verify they take effect
- Test error handling

---

## Phase 5: Code Review & Deployment

### 5.1 Code Review Checklist
- [ ] All API endpoints documented
- [ ] TypeScript types defined
- [ ] Error handling implemented
- [ ] Loading states added
- [ ] Mobile responsive
- [ ] No console errors
- [ ] No linting errors
- [ ] Performance optimized

### 5.2 Deployment
- [ ] Test in development
- [ ] Test in staging (if applicable)
- [ ] Update documentation
- [ ] Commit to git
- [ ] Deploy to production

---

## Estimated Timeline

- **Phase 1** (Backend APIs): 2-3 hours
- **Phase 2** (Dashboard UI): 3-4 hours
- **Phase 3** (System Settings): 4-5 hours
- **Phase 4** (Testing): 2-3 hours
- **Phase 5** (Review & Deploy): 1 hour

**Total**: ~12-16 hours

---

## File Structure

### Backend
```
backend/ai_assistant/
├── views/
│   ├── dashboard_views.py (NEW)
│   └── system_settings_views.py (NEW)
├── urls/
│   └── dashboard_urls.py (NEW)
└── serializers.py (add dashboard/settings serializers)
```

### Frontend
```
frontend/src/
├── components/
│   ├── Dashboard/
│   │   ├── Dashboard.tsx (UPDATE)
│   │   ├── StatsCard.tsx (NEW)
│   │   ├── RecentUploads.tsx (NEW)
│   │   ├── ProcessingQueue.tsx (NEW)
│   │   ├── RAGActivityChart.tsx (NEW)
│   │   ├── QuickActions.tsx (NEW)
│   │   └── AlertsPanel.tsx (NEW)
│   └── Administration/
│       └── SystemSettings.tsx (NEW)
├── services/
│   └── api.ts (add dashboard/settings methods)
└── types/
    └── settings.ts (NEW)
```

---

## Notes

- Dashboard should auto-refresh every 30 seconds
- System Settings should validate inputs before save
- All sensitive data should be masked with reveal option
- Changes should be logged for audit trail
- Consider adding feature flags for beta features

