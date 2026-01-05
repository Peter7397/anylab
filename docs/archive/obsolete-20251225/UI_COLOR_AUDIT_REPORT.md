# UI Color Unification Audit Report

## Overview
This report lists all UI components currently using **blue, indigo, purple, violet, pink, rose, orange, yellow, cyan, teal** colors instead of the green theme.

---

## 1. CSS Files

### `/frontend/src/index.css`
- **Line 81**: `badge-info` class uses `bg-blue-50 text-blue-700 border-blue-200`

### `/frontend/src/App.css`
- **Line 17**: `background-color: #282c34` (dark background - likely OK)
- **Line 28**: `color: #61dafb` (cyan link color)

---

## 2. UI Component Files

### `/frontend/src/components/ui/badge.tsx`
- **Line 18**: `info` variant uses `bg-blue-50 text-blue-800`

### `/frontend/src/components/ui/alert.tsx`
- **Line 17**: `default` variant uses `bg-blue-50 border-blue-200 text-blue-800`

---

## 3. Dashboard Component (`/frontend/src/components/Dashboard/Dashboard.tsx`)

| Line | Element | Color Used | Context |
|------|---------|------------|---------|
| 158 | Icon | `text-purple-600` | Sparkles icon |
| 159 | Badge | `text-purple-600 bg-purple-100` | Status badge |
| 175 | Icon | `text-blue-600` | Tag icon |
| 195 | Icon | `text-indigo-600` | Network icon |
| 280 | Badge | `bg-blue-100 text-blue-800` | Status indicator |

---

## 4. GraphRAG Search Component (`/frontend/src/components/AI/GraphRagSearch.tsx`)

### Entity Type Colors
| Line | Entity Type | Color Classes |
|------|-------------|---------------|
| 305 | Default entity | `bg-purple-100 text-purple-800 border-purple-300` |
| 307 | VERSION | `bg-blue-100 text-blue-800 border-blue-300` |
| 312 | PRODUCT | `bg-indigo-100 text-indigo-800` |
| 313 | VERSION | `bg-blue-100 text-blue-800` |
| 316 | PROBLEM | `bg-orange-100 text-orange-800` |
| 317 | OS | `bg-yellow-100 text-yellow-800` |
| 318 | DATABASE | `bg-purple-100 text-purple-800` |

### UI Elements
| Line | Element | Color Used | Context |
|------|---------|------------|---------|
| 367 | Link | `text-indigo-600 hover:text-indigo-700` | Filter link |
| 398 | Icon | `text-blue-600` | FileText icon |
| 403 | Icon | `text-indigo-600` | Tag icon |
| 420 | Header background | `bg-indigo-50 border-indigo-200` | Entity header |
| 422 | Text | `text-indigo-900` | Header text |
| 425 | Button | `text-indigo-600 hover:text-indigo-700` | Close button |
| 706 | Stats card | `bg-blue-50` | Edges stat background |
| 708 | Number | `text-blue-600` | Edges count |
| 710 | Stats card | `bg-indigo-50` | Query entities background |
| 712 | Number | `text-indigo-600` | Entities count |
| 757 | Icon | `text-indigo-600` | GitBranch icon |
| 782 | Icon | `text-blue-600` | FileText icon |
| 791 | Dropdown | `bg-blue-50 border-blue-200 text-blue-800` | Select element |
| 837 | Icon | `text-yellow-500` | Warning icon |

---

## 5. Home Page Component (`/frontend/src/components/Home/HomePage.tsx`)

| Line | Element | Color Used | Context |
|------|---------|------------|---------|
| 42 | Spinner | `border-blue-600` | Loading spinner |
| 65 | Button | `bg-blue-600 hover:bg-blue-700` | CTA button |
| 77 | Badge | `bg-blue-100 text-blue-700` | Feature badge |
| 92 | Button | `bg-blue-600 hover:bg-blue-700` | Primary CTA |
| 109 | Icon background | `bg-blue-100` | Feature icon container |
| 110 | Icon | `text-blue-600` | Brain icon |
| 129 | Icon background | `bg-purple-100` | Feature icon container |
| 130 | Icon | `text-purple-600` | Database icon |
| 153 | Card | `from-blue-50 to-indigo-50 border-blue-200` | Feature card gradient |
| 155 | Icon | `text-blue-600` | Brain icon |
| 205 | Card | `from-purple-50 to-violet-50 border-purple-200` | Feature card gradient |
| 207 | Icon | `text-purple-600` | BookOpen icon |
| 233 | Icon | `text-orange-600` | AlertTriangle icon |
| 257 | Card | `from-indigo-50 to-blue-50 border-indigo-200` | Feature card gradient |
| 259 | Icon | `text-indigo-600` | Database icon |
| 283 | Card | `from-pink-50 to-rose-50 border-pink-200` | Feature card gradient |
| 285 | Icon | `text-pink-600` | MessageSquare icon |
| 322 | Icon | `text-yellow-500` | Zap icon |
| 327 | Icon | `text-blue-500` | Layers icon |
| 332 | Icon | `text-purple-500` | Network icon |
| 351 | Text | `text-blue-100` | Hero text |
| 357 | Button | `bg-white text-blue-600 hover:bg-gray-50` | CTA button |
| 371 | Icon | `text-blue-400` | Brain icon |
| 399 | Button | `bg-blue-600 hover:bg-blue-700` | Get started button |

---

## 6. Document Manager Component (`/frontend/src/components/AI/DocumentManager.tsx`)

### Status Colors
| Line | Status | Color Classes |
|------|--------|---------------|
| 284 | pending | `bg-yellow-100 text-yellow-800` |
| 285 | metadata_extracting | `bg-indigo-100 text-indigo-800` |
| 286 | chunking | `bg-blue-100 text-blue-800` |
| 287 | embedding | `bg-purple-100 text-purple-800` |

### UI Elements
| Line | Element | Color Used | Context |
|------|---------|------------|---------|
| 308 | Warning badge | `bg-orange-100 text-orange-800` | Warning indicator |
| 1148 | Button | `bg-purple-600 hover:bg-purple-700` | Reprocess button |
| 1164 | Button | `bg-blue-600 hover:bg-blue-700` | Upload button |
| 1184+ | Multiple inputs | `focus:ring-blue-500` | Form inputs (17 instances) |
| 1226 | Button | `bg-indigo-600 hover:bg-indigo-700` | Metadata button |
| 1237 | Info box | `bg-indigo-50 border-indigo-200` | Info panel |
| 1382 | Border | `border-indigo-200` | Section divider |
| 1399 | Button | `text-indigo-700 border-indigo-300 hover:bg-indigo-100` | Cancel button |
| 1405 | Button | `bg-indigo-600 hover:bg-indigo-700` | Confirm button |
| 1450 | Spinner | `border-blue-600` | Loading spinner |
| 1471 | Icon | `text-blue-600` | Document icon |
| 1473 | Badge | `bg-blue-100 text-blue-800` | Document type badge |
| 1509 | Button | `text-blue-600 hover:bg-blue-50` | View button |
| 1530 | Button | `text-orange-600 hover:bg-orange-50` | Reprocess button |
| 1548 | Button | `text-purple-600 hover:bg-purple-50` | Delete button |
| 1627+ | Multiple tag buttons | `bg-blue-100 text-blue-700 hover:bg-blue-200 border-blue-300` | Tag filters |
| 1847 | Button | `bg-blue-600 hover:bg-blue-700` | Create button |
| 1954 | Button | `bg-blue-600 hover:bg-blue-700` | Upload button |
| 2031 | Selected state | `bg-blue-50 border-blue-500 text-blue-700` | Selected file |
| 2057 | Selected state | `bg-blue-50 border-blue-500 text-blue-700` | Selected item |
| 2121 | Progress panel | `bg-blue-50 border-blue-200` | Processing status |
| 2123 | Spinner | `border-blue-600` | Progress spinner |
| 2132-2133 | Status text | `text-blue-600`, `text-blue-800` | Processing text |
| 2168+ | Multiple tag buttons | `bg-blue-100 text-blue-700 hover:bg-blue-200 border-blue-300` | Tag management |
| 2336 | Status icon | `text-blue-600` | Metadata status |
| 2339 | Status icon | `text-blue-600` | Chunking status |
| 2342 | Status icon | `text-blue-600` | Embedding status |
| 2344 | Status text | `text-yellow-600` | Waiting status |
| 2377 | Error list | `border-orange-200 bg-orange-50` | Error container |
| 2382-2385 | Error items | `text-orange-700`, `bg-orange-400`, `text-orange-500` | Error details |
| 2409 | Skipped count | `text-yellow-600` | Skipped indicator |
| 2438-2442 | Error details | `bg-yellow-50 border-yellow-200 text-yellow-900/700/600` | Error messages |
| 2500 | Button | `bg-orange-600 hover:bg-orange-700` | Close button |
| 2514 | Header | `bg-blue-50` | Upload header |
| 2516 | Spinner | `border-blue-600` | Upload spinner |
| 2541 | Status color | `text-blue-600` | Uploading status |
| 2542 | Status color | `text-yellow-600` | Processing status |
| 2589 | Progress bar | `bg-yellow-500` | Processing progress |
| 2590 | Progress bar | `bg-blue-500` | Uploading progress |
| 2619 | Status text | `text-blue-600` | In progress text |
| 2620 | Status text | `text-blue-700` | Progress count |

---

## 7. Chat Assistant Component (`/frontend/src/components/AI/ChatAssistant.tsx`)

| Line | Element | Color Used | Context |
|------|---------|------------|---------|
| 85 | Sources panel | `bg-blue-50 border-blue-200` | Source display |
| 86 | Header text | `text-blue-900` | Section header |
| 105 | Entities panel | `bg-blue-50 border-blue-200` | Entity display |
| 106 | Header text | `text-blue-900` | Section header |
| 129 | Button | `text-blue-600 hover:text-blue-800 hover:bg-blue-100` | Copy button |
| 138 | Button | `text-blue-600 hover:text-blue-800 hover:bg-blue-100` | Share button |
| 495 | Icon background | `bg-blue-100` | Message icon container |
| 496 | Icon | `text-blue-600` | MessageSquare icon |
| 507 | Link | `text-blue-600 hover:text-blue-700` | View all link |
| 526 | Header | `bg-blue-50 border-blue-200` | Session info header |
| 530 | Icon | `text-blue-600` | Clock icon |
| 534 | Icon | `text-blue-600` | Target icon |
| 538 | Icon | `text-blue-600` | FileText icon |
| 544 | Button | `text-blue-600 hover:text-blue-700` | Close button |
| 575 | Active tab | `bg-blue-600` | Selected tab |
| 622 | User message time | `text-blue-200` | Timestamp |
| 637 | Spinner | `border-blue-600` | Loading spinner |
| 656 | Input focus | `focus:ring-blue-500` | Message input |

---

## 8. Login Component (`/frontend/src/components/Auth/Login.tsx`)

| Line | Element | Color Used | Context |
|------|---------|------------|---------|
| 89 | Input focus | `focus:border-indigo-500 focus:ring-indigo-500` | Username input |
| 105 | Input focus | `focus:border-indigo-500 focus:ring-indigo-500` | Password input |
| 113 | Button | `bg-indigo-600 hover:bg-indigo-700 focus:ring-indigo-500` | Login button |
| 122 | Link | `text-indigo-600 hover:text-indigo-700` | Forgot password |

---

## 9. Forum Components

### ForumPost.tsx
| Line | Element | Color Used | Context |
|------|---------|------------|---------|
| 209 | Icon | `text-yellow-500` | Pin icon |
| 212 | Icon | `text-orange-500` | Star icon |

### Forum.tsx
| Line | Element | Color Used | Context |
|------|---------|------------|---------|
| 244 | Badge | `bg-yellow-500` | Pinned badge |
| 258 | Badge | `bg-orange-500` | Featured badge |
| 290 | Border | `border-yellow-400 border-l-4` | Pinned post highlight |
| 298 | Icon | `text-yellow-500` | Pin icon |
| 301 | Icon | `text-orange-500` | Star icon |

---

## 10. Administration Components

### Analytics.tsx
| Line | Element | Color Used | Context |
|------|---------|------------|---------|
| 14 | Chart colors array | `['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']` | Multiple chart colors |
| 179 | Icon background | `bg-yellow-100` | Activity icon container |
| 180 | Icon | `text-yellow-600` | Activity icon |
| 192 | Icon background | `bg-purple-100` | Users icon container |
| 193 | Icon | `text-purple-600` | Users icon |
| 220 | Chart fill | `fill="#8884d8"` | Chart color |
| 244 | Bar color | `fill="#3b82f6"` | Blue bar chart |
| 266 | Line color | `stroke="#3b82f6"` | Blue line chart |
| 284 | Bar color | `fill="#10b981"` | Green bar (OK) |
| 320 | Bar color | `fill="#f59e0b"` | Orange bar chart |
| 354 | Bar color | `fill="#8b5cf6"` | Purple bar chart |
| 438 | Chart fill | `fill="#8884d8"` | Chart color |

### UsersRoles.tsx
| Line | Element | Color Used | Context |
|------|---------|------------|---------|
| 337 | Icon background | `bg-yellow-100` | Shield icon container |
| 338 | Icon | `text-yellow-600` | Shield icon |

### License.tsx
| Line | Element | Color Used | Context |
|------|---------|------------|---------|
| 85 | Badge | `bg-indigo-50 text-indigo-700 border-indigo-200` | Module badge |
| 105 | Button | `bg-indigo-600` | Import button |

---

## 11. Help Portal Component (`/frontend/src/components/AI/HelpPortal.tsx`)

| Line | Element | Color Used | Context |
|------|---------|------------|---------|
| 204 | Icon | `text-yellow-600` | Pending status icon |
| 221 | Badge | `bg-yellow-100 text-yellow-800 border-yellow-300` | Pending badge |
| 339 | Icon | `text-yellow-600` | Pending status icon |
| 357 | Badge | `bg-yellow-100 text-yellow-800 border-yellow-300` | Pending badge |
| 441 | Stats card | `bg-yellow-50 border-yellow-200` | Pending stats |
| 443 | Text | `text-yellow-700` | Stat label |
| 444 | Icon | `text-yellow-600` | Clock icon |
| 446 | Number | `text-yellow-900` | Stat number |
| 636 | Info panel | `bg-yellow-50 border-yellow-200` | Duplicates info |
| 637-638 | Text | `text-yellow-900` | Duplicate count |
| 644 | Warning panel | `bg-yellow-50 border-yellow-200` | Warning message |
| 646 | Icon | `text-yellow-600` | Warning icon |
| 648-649 | Text | `text-yellow-900`, `text-yellow-700` | Warning text |
| 722 | Stats card | `bg-purple-50 border-purple-200` | Total chunks |
| 724 | Text | `text-purple-700` | Stat label |
| 725 | Icon | `text-purple-600` | FileText icon |
| 727 | Number | `text-purple-900` | Stat number |
| 729 | Stats card | `bg-indigo-50 border-indigo-200` | Success rate |
| 731 | Text | `text-indigo-700` | Stat label |
| 732 | Icon | `text-indigo-600` | CheckCircle icon |
| 734 | Number | `text-indigo-900` | Stat number |
| 857 | Button | `text-yellow-600 hover:text-yellow-900` | Edit button |

---

## 12. Document Viewer Component (`/frontend/src/components/AI/DocumentViewer.tsx`)

| Line | Element | Color Used | Context |
|------|---------|------------|---------|
| 145 | Canvas fill | `#ffffff` | White background (OK) |
| 704 | Button | `bg-purple-500 hover:bg-purple-600` | Download button |
| 831 | Highlight | `bg-yellow-300` | Search highlight |
| 972 | Mark tag | `bg-yellow-300` | Search result highlight |
| 1304 | Search match | `bg-yellow-200` | Selected search result |

---

## 13. Troubleshooting AI Component (`/frontend/src/components/AI/TroubleshootingAI.tsx`)

| Line | Element | Color Used | Context |
|------|---------|------------|---------|
| 258 | Icon background | `bg-orange-100` | Alert icon container |
| 259 | Icon | `text-orange-600` | AlertCircle icon |
| 480 | Button | `bg-orange-600 hover:bg-orange-700` | Analyze button |
| 523 | Link | `hover:text-orange-600` | Solution link |

---

## 14. Scraper Management Component (`/frontend/src/components/Scrapers/ScraperManagement.tsx`)

| Line | Element | Color Used | Context |
|------|---------|------------|---------|
| 214 | Background | `bg-purple-100` or `bg-yellow-100` | GitHub/Website scraper |
| 216 | Background | `bg-yellow-100` | Website scraper |
| 220 | Icon | `text-purple-600` or `text-yellow-600` | Scraper icon |
| 222 | Icon | `text-yellow-600` | Website icon |

---

## 15. Troubleshooting Components

### LogCollection.tsx
| Line | Element | Color Used | Context |
|------|---------|------------|---------|
| 67 | Warning status | `text-yellow-600 bg-yellow-100` | Warning logs |

### SystemOverview.tsx
| Line | Element | Color Used | Context |
|------|---------|------------|---------|
| 62 | Warning status | `text-yellow-600 bg-yellow-100` | Warning state |
| 112 | Icon background | `bg-yellow-100` | Warning icon container |
| 113 | Icon | `text-yellow-600` | AlertTriangle icon |

---

## 16. Other Components

### DocumentProcessing.tsx
| Line | Element | Color Used | Context |
|------|---------|------------|---------|
| 270 | File type background | `bg-blue-100` or `bg-purple-100` | Video/Image file type |
| 273 | Icon | `text-blue-600` or `text-purple-600` | FileVideo icon |
| 275 | Icon | `text-purple-600` | Image icon |

### SharingCollaborationPage.tsx
| Line | Element | Color Used | Context |
|------|---------|------------|---------|
| 188 | Status indicator | `bg-yellow-500` | Pending status |

### RequireFeature.tsx
| Line | Element | Color Used | Context |
|------|---------|------------|---------|
| 19 | Spinner | `border-indigo-600` | Loading spinner |

---

## Summary Statistics

### Color Usage by Type:
- **Blue** (various shades): ~180 instances
- **Indigo**: ~29 instances
- **Purple/Violet**: ~24 instances
- **Yellow**: ~40 instances
- **Orange**: ~22 instances
- **Pink/Rose**: ~2 instances

### Most Affected Components:
1. **DocumentManager.tsx** - 100+ blue/purple/indigo instances
2. **HomePage.tsx** - 30+ blue/purple/pink instances
3. **GraphRagSearch.tsx** - 25+ blue/indigo/purple instances
4. **ChatAssistant.tsx** - 15+ blue instances
5. **Analytics.tsx** - Multiple chart color instances

### Critical Changes Needed:
1. ✅ **Base UI Components** (badge.tsx, alert.tsx) - Use green instead of blue for info/default
2. ✅ **CSS Classes** (index.css) - Replace blue info badges with green
3. ✅ **Form Focus States** - Change from blue/indigo to green ring colors
4. ✅ **Primary Buttons** - Already using green (good!)
5. ✅ **Status Indicators** - Convert blue/purple to green variants
6. ✅ **Entity Type Colors** - Standardize to green-based palette
7. ✅ **Loading Spinners** - Change from blue/indigo to green
8. ⚠️ **Warning/Error Colors** (yellow/orange/red) - Consider keeping for semantic meaning
9. ⚠️ **Chart Colors** - May need color differentiation (Analytics)

---

## Recommendations

### Keep These Colors (Semantic Meaning):
- ⚠️ **Warning**: Yellow/Orange (for alerts, pending states, warnings)
- ❌ **Danger/Error**: Red (for errors, delete actions)
- ✅ **Success**: Green (already implemented)

### Convert These to Green:
- All **blue** primary buttons, links, and CTAs
- All **blue** info badges and alerts
- All **indigo** authentication UI elements
- All **purple** feature highlights
- All **blue/indigo** focus states and rings
- All **blue** loading spinners
- Entity type colors in GraphRAG (use green gradient variants)

### Consider Green Gradient Palette:
For different states/types, use green shades instead of different colors:
- Light green (50-200): Info, secondary
- Medium green (300-500): Primary, active
- Dark green (600-900): Hover, selected
- With yellow/orange/red reserved for warnings/errors only

---

## Implementation Priority

### Phase 1 (High Impact):
1. Base UI components (badge, alert)
2. CSS utility classes (index.css)
3. Home page CTAs and hero section
4. Authentication pages (Login)

### Phase 2 (Medium Impact):
1. Document Manager UI
2. GraphRAG Search interface
3. Chat Assistant
4. Dashboard cards

### Phase 3 (Lower Impact):
1. Admin panels
2. Forum components
3. Help Portal
4. Troubleshooting UI

---

*Report Generated: November 11, 2025*
*Total Files Analyzed: 30+*
*Total Color Instances Found: 300+*

