1. Navigation & Layout Components

- Sidebar Navigation
	- Collapsible
	- Grouped sections (Dashboard, Administration, Troubleshooting, AI Assistant, Maintenance, Toolkit, Settings)
	- Icons: Lucide (as listed earlier)
- Top Bar
	- Quick action buttons: Scan, Refresh, Generate Report, AI Analyze
	- AI Mode Toggle: Performance / Lightweight mode chip with dropdown
	- User menu: Profile, Settings, Logout
- Breadcrumbs
	- Display current page path (e.g., Troubleshooting > Log Collection).
- Collapsible Panels (e.g., Maintenance details, Log filtering settings).
---

2. Form Components

- Buttons
	- Primary: Submit, Start Scan, Run Analysis (colored, filled).
	- Secondary: Cancel, Close (outline).
	- Icon buttons: Refresh (refresh-cw), Scan (radar), AI Analyze (sparkles).
- Inputs
	- Text field: For names, descriptions, etc.
	- Search field: For searching logs, knowledge documents.
	- File upload: Drag & drop for PDFs/logs.
	- URL input: For adding knowledge base links.
- Dropdowns
	- Project selection
	- AI Mode selection (Performance vs Lightweight)
	- Date filters for logs (last 2 weeks, 1 month, etc.).
- Toggles / Switches
	- AI mode (Performance vs Lightweight).
	- Enable/disable scheduled scans or log collection.
- Multi-select lists
	- Select PCs to monitor.
	- Select documents as knowledge sources for AI queries.
---

3. Display Components

- Tables
	- System at a Glance: Name, IP, OS, Last Login, Status.
	- Logs Table: Timestamp, Source, Severity, Message, AI Tag (Critical/Warning/Info).
	- Knowledge Library: File name, Type (PDF/URL), Date added, Status (Indexed/Failed).
- Cards
	- Dashboard cards: Quick summary (Total PCs, Issues detected, Pending maintenance).
	- AI Assistant responses: Chat bubble cards with source references.
- Charts & Graphs
	- Resource monitoring: CPU/RAM/Disk usage over time. (Recharts or Chart.js)
	- Log analysis summary: Pie chart of log severity distribution.
- Badges & Tags
	- Status: OK (green), Warning (yellow), Critical (red).
	- Log types: Error, Info, Warning.
- Progress Indicators
	- For log collection and AI analysis progress.
---

4. Feedback & Notifications

- Alerts / Toasts
	- Success, Warning, Error messages (e.g., "Logs collected successfully", "AI analysis failed").
- Modals
	- Confirmation dialogs (e.g., “Are you sure you want to delete this source?”).
	- Detailed log view.
- Inline Alerts
	- Critical system notifications at the top of main panels.
---

5. AI Assistant-Specific Components

- Chat Interface
	- Chat bubbles (AI vs User).
	- Source citation links under each AI response.
- Document Manager
	- Drag & drop upload area for PDFs.
	- URL addition form.
	- Document status table (Indexed/Failed/Processing).
- Filter Bar
	- Select which knowledge sources to include in AI responses.
---

6. Theming & State

- Light/Dark Mode Switch
- Loading Spinners for async actions (log collection, AI analysis).
- Disabled states for buttons when tasks are in progress.
---






