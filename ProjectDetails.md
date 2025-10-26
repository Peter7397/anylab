Purpose:
AnyLab is a web-based lab IT operations and troubleshooting platform integrating:

**Slogan: AI eNlighteN Your Lab**
- AI-driven troubleshooting (RAG-based Q&A using manuals, KBs, logs)
- AI RAG driving Assist 
This design focuses on the AI Assistant and how it integrates with the rest of the platform.
---

1. Technology Stack


Backend

- Django + Django REST Framework (DRF):
	- Core web API
	- User & role management (RBAC)
	- API endpoints for logs, AI analysis, document management
- Celery + Redis:
	- For background tasks:
		- Domain PC scanning
		- Log collection (scheduled & on-demand)
		- AI-based log analysis
		- RAG indexing (document ingestion)
		- Report generation
- PostgreSQL + pgvector:
	- Relational DB for users, logs, settings
	- Vector database for storing embeddings of PDFs, websites, and logs

AI Models

- Qwen 2.5‑7B‑Instruct (Ollama/vLLM):
	- Main model for log analysis & contextual troubleshooting Q&A
	- Dual‑mode support:
		- Performance Mode: Full‑precision Qwen 2.5‑7B (max accuracy)
		- Lightweight Mode: Quantized (4‑bit) Qwen 2.5‑7B (low resource)
- BAAI/bge‑m3 (embeddings):
	- Performance Mode: Full‑precision (high‑accuracy RAG search)
	- Lightweight Mode: INT8 quantized or fallback to MiniLM‑L6‑v2 (faster, low‑resource)

Document & Log Processing

- LangChain: Orchestrates RAG pipeline:
	- PDF parsing → chunking → embeddings → pgvector storage
	- Query rewriting for better retrieval
- PyMuPDF: High‑performance PDF text extraction.
- Playwright / BeautifulSoup: Web page scraping for knowledge ingestion.

Frontend

- React + Tailwind + Shadcn/UI: Modern SPA design (dashboard‑style layout).
- React Router: For multi‑page navigation.
- Framer Motion: Smooth UI animations.

Containerization

- Docker Compose: Multi‑service setup:
	- django (backend API + Celery)
	- react (frontend SPA)
	- postgres (database + pgvector)
	- redis (Celery broker)
	- qwen (Ollama/vLLM for Qwen inference)
	- nginx (reverse proxy for unified access)
---

2. Key Modules


A. Administration

- System at a Glance:
	- Active Directory domain scan (via ldap3 / pyad).
	- Displays IP, hostname, OS, last login.
- Account & Privilege Management:
	- Role-based access with Django Groups & Permissions.
- System Connection Info:
	- Select which PCs to monitor.
- System Reports:
	- Export CSV/PDF reports of PCs and network inventory.
---

B. Troubleshooting & Monitoring

- Log Collection:
- Sources:
	- Windows Event Logs (via pywin32 / PowerShell).
	- MSSQL logs (via pyodbc).
	- Application logs: Copy from custom folders (e.g., C:\ProgramData\Agilent\LogFiles, Tomcat logs, Flexera logs, etc.).
		- Runtime filtering options:
			- Press Enter: collect all.
			- 1: logs from last 1 year.
			- 2: logs from last quarter (3 months).
			- 3: logs from last month.
			- 4: logs from last 2 weeks.
	- Folder selection UI: Admins can configure log source folders in Django settings.
- Collection Modes:
	- On-demand (triggered by user from dashboard).
	- Scheduled (Celery periodic tasks).
- Storage:
	- Raw logs stored in a structured folder per PC/session.
	- Filtered logs stored in PostgreSQL for AI analysis.
- Log Filtering:
	- Apply custom filters to retain only critical logs.
- AI Log Analysis:
	- Send logs → Qwen for root cause & resolution insights.
- Resource Monitoring:
	- Lightweight agent reporting CPU/RAM/Disk metrics.
- Reports & Alerts:
	- Scheduled PDF/HTML system health reports.
	- Email/SMS/Web alerts for critical findings.
---

C. AI Assistant (RAG)

- Knowledge Management:
	- Upload PDFs (manuals, SOPs).
	- Add Web Links (official support pages).
	- Process → chunk → embed → store in pgvector.
	- Manage sources (view, delete, update).
- Chat Interface:
	- Conversational assistant (like ChatGPT).
	- Filter responses by document source.
	- Display references/citations in answers.
- Integrated Log Troubleshooting:
	- Combine logs + RAG knowledge for contextual AI diagnosis.
---

D. Maintenance

- Maintenance Calendar:
	- Plan SQL tasks, service restarts, reboots.
- SQL Health:
	- Index rebuilding, optimization, backup checks.
---

E. Toolkit

- SAL Index Rebuilding
- Certificate Management: Create, register, renew.
- Pluggable Tools: Expandable for future utilities.
---

3. GUI Layout


Sidebar Navigation

```
Dashboard
├─ Administration
│  ├─ Users & Roles
│  ├─ Source Library
│  └─ System Connection
├─ Troubleshooting & Monitoring
│  ├─ System at a Glance
│  ├─ Log Collection
│  ├─ Log Analysis
│  ├─ Resource Monitoring
│  ├─ Alerts
│  └─ Reports
├─ AI Assistant
│  ├─ Knowledge Library
│  └─ Chat Assistant
├─ Maintenance
│  ├─ Calendar
│  └─ SQL Health
├─ Toolkit
│  ├─ SAL Index
│  ├─ Certificate Management
│  └─ More Tools
└─ Settings
   ├─ AI Mode (Performance / Lightweight)
   ├─ System Config
   └─ Notifications
```

AI Assistant Tab

- Knowledge Library:
	- Upload PDFs (drag & drop).
	- Add/edit/remove web links.
	- Show processed documents with metadata.
- Chat Assistant:
	- Chat-like interface with Qwen.
	- Document filters to restrict context.
	- References to source docs/websites.

Settings

- AI Mode Switch:
	- Performance Mode: Full-precision models.
	- Lightweight Mode: Quantized (low-resource).
	- Tooltip with system requirements.
---

4. Dual‑Mode AI (Performance vs Lightweight)


Performance Mode

- Qwen 2.5‑7B full precision (max accuracy).
- BGE‑m3 full precision embeddings.
- Runs on: Mac Mini M3 32 GB or PC with 16–24 GB GPU.

Lightweight Mode

- Qwen 2.5‑7B 4‑bit quantized.
- BGE‑m3 INT8 or fallback MiniLM‑L6‑v2.
- Runs on: Mac Mini M2/M3 16 GB or low‑spec PCs.
Switching:
- Settings → AI Mode toggle in UI.
- Changes docker-compose env & restarts AI container.
- Fallback: If Performance Mode fails (OOM), auto‑switch to Lightweight Mode and log an alert.
---

5. Data Flow

5956. Knowledge Upload:
      PDFs / URLs → Extract text → Chunk → Generate embeddings → Store in pgvector.
5957. User Query:
      Retrieve top‑k relevant chunks → Pass with query to Qwen → Generate contextual answer.
5958. Log Analysis:
      Logs → Pre‑processed & filtered → Qwen generates structured root cause + resolution.
5959. Alerts & Reports:
      Celery tasks generate reports or trigger email/SMS/web alerts.
---

6. Docker Setup


docker-compose.yml (excerpt)

```
yaml
复制编辑
version: '3.9'
services:
  django:
    build: ./backend
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis

  react:
    build: ./frontend
    ports:
      - "3000:3000"

  postgres:
    image: ankane/pgvector
    environment:
      POSTGRES_USER: labdog
      POSTGRES_PASSWORD: password
      POSTGRES_DB: labdogdb
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7

  qwen:
    image: vllm/vllm-openai:latest
    command: --model ${QWEN_MODEL}
    ports:
      - "8001:8000"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf

volumes:
  pgdata:

```

---

7. Why Qwen 2.5‑7B + BGE‑m3?

- Qwen: Great reasoning & long context (128K tokens) → can handle large logs & manuals.
- BGE‑m3: State‑of‑the‑art multilingual embeddings → best for manuals, troubleshooting KBs.
- Quantization: Reduces resource load → fits Mac Mini or small servers.

---

8. API Overview

- Base URL: `/api/`
- Auth (JWT):
  - `POST /api/token/` (username, password)
  - `POST /api/token/refresh/`
  - `POST /api/token/verify/`
- Health:
  - `GET /api/health/`
- Users: see `backend/users/urls.py`
- Monitoring:
  - `GET /api/monitoring/` (placeholder)
- Maintenance:
  - `GET /api/maintenance/` (placeholder)
- AI Assistant:
  - Chat (Ollama proxy): `POST /api/ai/chat/ollama/` { prompt }
  - Embeddings (disabled placeholder): `POST /api/ai/embeddings/`
  - Similarity (disabled placeholder): `POST /api/ai/similarity/`
  - Model info (disabled placeholder): `GET /api/ai/model-info/`
  - Switch embedding mode (disabled placeholder): `POST /api/ai/switch-mode/` { mode }
  - RAG Upload (disabled placeholder): `POST /api/ai/rag/upload/`
  - RAG Chat (disabled placeholder): `POST /api/ai/rag/chat/`
  - RAG Info (disabled placeholder): `GET /api/ai/rag/info/`
- PDF Management (under AI):
  - `GET /api/ai/pdfs/`
  - `POST /api/ai/pdfs/upload/` (multipart: title, file, description)
  - `GET /api/ai/pdfs/{id}/`
  - `GET /api/ai/pdfs/{id}/download/`
  - `DELETE /api/ai/pdfs/{id}/delete/`
  - `POST /api/ai/pdfs/search/` { query, search_type }

---

9. Key Data Models (selected)

- Users (`users.models.User`): extends Django `AbstractUser` with `employee_id`, `department`, `position`, `phone`, `avatar`, `last_login_ip`.
- Roles (`users.models.Role`, `users.models.UserRole`): JSON `permissions`, many‑to‑many assignments.
- Monitoring (`monitoring.models`):
  - `System` (hostname, ip, status), `SystemMetrics` (cpu/mem/disk/net),
    `LogEntry` (level, source, message), `Alert` (severity, status),
    `NetworkConnection`, `DatabaseMetrics`.
- Maintenance (`maintenance.models`):
  - `MaintenanceTask` (type, priority, schedule, assignee, systems M2M),
    `MaintenanceSchedule` (recurrence), `SQLQuery`, `DatabaseBackup`, `PerformanceBaseline`.
- AI Assistant (`ai_assistant.models`):
  - `KnowledgeDocument` and `DocumentChunk` (RAG corpus, embeddings JSON),
    `ChatSession`, `ChatMessage` (messages with `sources`),
    `AIModel` (mode, config), `AIConversationTemplate`, `AIUsageLog`,
    `PDFDocument` (uploads metadata).

---

10. RAG Pipeline & Current Status

- **CURRENT STATUS: FULLY FUNCTIONAL** ✅
  - RAG system is fully implemented and operational
  - Multiple search modes available: Comprehensive, Advanced, Enhanced, and Basic
  - All endpoints are active and returning proper responses
  - Files implemented: `backend/ai_assistant/views.py`, `backend/ai_assistant/rag_service.py`, 
    `backend/ai_assistant/improved_rag_service.py`, `backend/ai_assistant/advanced_rag_service.py`,
    `backend/ai_assistant/comprehensive_rag_service.py`
- **Implemented Pipeline:**
  - Ingestion: PDF/URL → extract → chunk → embed (BGE‑m3 via Ollama) → store (pgvector)
  - Retrieval: query processing → top‑k vector search → Qwen generation with citations
  - Advanced features: Hybrid search, reranking, smart caching, duplicate detection
- **Performance Optimizations:**
  - Multi-level caching (embeddings, search results, responses)
  - Optimized chunking strategies
  - Smart similarity scoring
  - Query history tracking

---

11. Configuration & Environment

- Backend environment (examples):
  - `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`
  - Database: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST`, `POSTGRES_PORT`
  - Redis: `REDIS_HOST`, `REDIS_PORT`
  - AI: `OLLAMA_API_URL` (default `http://ollama:11434`), `QWEN_MODEL`, `EMBEDDING_MODEL`
  - Django media/static: `MEDIA_ROOT`, `MEDIA_URL`, `STATIC_ROOT`, `STATIC_URL`
- Frontend env:
  - `VITE_API_BASE_URL` or `REACT_APP_API_BASE_URL` (match frontend setup) pointing to backend `/api/`.

---

12. Run & Deploy

- Local with Docker Compose (backend stack):
  - From `backend/`: `docker compose up -d --build`
  - Services: Django API, Postgres (pgvector), Redis, optional LLM (vLLM/Ollama), Nginx (if configured).
- Dev without Docker:
  - Backend: create venv, `pip install -r backend/requirements.txt`, set env, `python manage.py migrate`, `python manage.py runserver`.
  - Frontend: `cd frontend && npm install && npm start` (or `npm run dev` if Vite).
- Notes:
  - Media storage for `/media/` must be writable for PDF uploads.
  - Configure CORS (frontend origin) if serving separately.

---

13. Security Considerations

- JWT auth endpoints available; protect AI, monitoring, and maintenance APIs with proper permissions.
- File uploads: 50 MB limit and extension checks for PDFs; store uploader when authenticated.
- Serve media via Django only to authenticated users in production or via signed URLs (future).
- Secrets in env, never in repo; restrict admin access; enable HTTPS in reverse proxy.
- Add request size limits and rate limiting for AI endpoints (future task).

---

14. Near‑Term Roadmap

- ✅ **COMPLETED**: RAG service implementation with BGE‑m3 and Qwen integration
- ✅ **COMPLETED**: Document persistence and search with pgvector
- ✅ **COMPLETED**: Multiple RAG search modes (Comprehensive, Advanced, Enhanced, Basic)
- ✅ **COMPLETED**: Frontend integration for PDF Library and RAG Chat
- **IN PROGRESS**: Finish Monitoring and Maintenance API CRUD, list, filters, and permissions
- **PLANNED**: Alerting pipeline (Celery): thresholds → notifications (email/webhook)
- **PLANNED**: Mode switch UI → toggles model configs and restarts AI container if needed
- **PLANNED**: Enhanced document type support (Word, Excel, PowerPoint)

---

15. Testing

- Backend: `pytest` or `python manage.py test` (tests under each app’s `tests.py`).
- Add API tests for AI PDF upload/list/detail, and later for RAG responses and monitoring endpoints.