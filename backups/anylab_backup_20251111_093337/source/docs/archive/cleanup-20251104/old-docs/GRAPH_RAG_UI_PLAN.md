# 🎨 Graph RAG UI Implementation Plan

## 📋 Overview

Plan for integrating Graph RAG search into the frontend with enhanced visualizations and entity relationship displays.

## 🎯 Design Goals

1. **Consistent UX**: Follow existing RAG component patterns
2. **Graph Visualization**: Show entity relationships and connections
3. **Enhanced Information**: Display graph-specific stats and insights
4. **Visual Indicators**: Clearly show graph-enhanced vs vector-only results

## 🏗️ Architecture

### Component Structure

```
frontend/src/
├── components/AI/
│   └── GraphRagSearch.tsx          # New Graph RAG component
├── services/
│   └── api.ts                      # Add graphRagSearch method
└── components/Layout/
    └── Sidebar.tsx                 # Add Graph RAG menu item
```

## 📦 Implementation Steps

### Step 1: API Service Layer ✅
- Add `graphRagSearch()` method to `api.ts`
- Handle Graph RAG response format
- Support graph_stats and entity data

### Step 2: GraphRagSearch Component ✅
- Create new component following ComprehensiveRagSearch pattern
- Add graph-specific features:
  - Entity relationship visualization
  - Graph stats panel
  - Source badges (Graph-Enhanced vs Vector-Only)
  - Entity tags display

### Step 3: UI Features ✅

#### Main Features:
1. **Chat Interface** (similar to other RAG components)
   - Message history
   - Input field
   - Send button
   - Loading states

2. **Graph Stats Panel** (new)
   - Total results count
   - Graph-enhanced count
   - Vector-only count
   - Entities found (with types)

3. **Source Display Enhancement** (new)
   - Badge indicators:
     - 🟢 "Graph-Enhanced" (found via both methods)
     - 🔵 "Vector Only" (semantic search only)
     - 🟡 "Graph Only" (graph traversal only)
   - Entity tags per source
   - Relationship connections

4. **Entity Visualization** (new)
   - Expandable entity panel
   - Show extracted entities from query
   - Display entity relationships
   - Visual connection graph (optional, future)

#### Visual Design:
- Use existing design system
- Graph-themed icons (Network, GitBranch, Share2)
- Color coding:
  - Green: Graph-enhanced results
  - Blue: Vector-only results
  - Purple: Entity badges

### Step 4: Routing & Navigation ✅
- Add route: `/ai/graph-rag`
- Add to Sidebar under "AI Assistant" section
- Icon: `Network` or `GitBranch`

## 🎨 UI Components Breakdown

### 1. GraphRagSearch Component

**Props:** None (standalone)

**State:**
```typescript
- messages: ChatMessage[]
- inputMessage: string
- isLoading: boolean
- showHistory: boolean
- showGraphStats: boolean
- graphStats: GraphStats | null
- selectedEntities: Entity[]
```

**Features:**
- Chat interface with message history
- Graph stats toggle button
- Entity panel expand/collapse
- Source badges and indicators

### 2. Graph Stats Panel

**Displays:**
- Total Results: X
- Graph-Enhanced: Y (boosted results)
- Vector Only: Z
- Entities Found: [List with types]

**Design:**
- Collapsible panel
- Icons for each stat
- Color-coded badges

### 3. Source Card Enhancement

**New Fields:**
- `sourceType`: 'graph+vector' | 'vector' | 'graph'
- `graphBoost`: boolean
- `matchedEntities`: Entity[]
- `graphScore`: number

**Visual:**
- Badge showing source type
- Entity chips/tags
- Graph boost indicator (✨ or badge)

### 4. Entity Panel

**Shows:**
- Extracted entities from query
- Entity types (PRODUCT, VERSION, ERROR_CODE, etc.)
- Related entities (from graph)
- Co-occurrence counts

**Design:**
- Collapsible sidebar or bottom panel
- Entity cards with type badges
- Click to filter/highlight in sources

## 🔌 API Integration

### Request Format
```typescript
POST /api/ai/rag/search/graph/
{
  query: string;
  top_k: number; // default: 10
}
```

### Response Format
```typescript
{
  success: true;
  data: {
    response: string;
    sources: Array<{
      title: string;
      content: string;
      page?: number;
      score?: number;
      source?: 'vector+graph' | 'vector' | 'graph';
      graph_boost?: boolean;
      matched_entities?: Array<{
        name: string;
        type: string;
      }>;
    }>;
    query: string;
    search_method: 'graph_rag';
    graph_stats: {
      total_results: number;
      graph_enhanced: number;
      vector_only: number;
      query_entities: Array<{
        name: string;
        type: string;
        normalized: string;
      }>;
    };
  };
}
```

## 🎯 User Experience Flow

1. **User enters query**
   - Type question about products, versions, errors

2. **Graph RAG processes**
   - Shows loading state
   - Extracts entities in background

3. **Results displayed**
   - Response text (enhanced with graph context)
   - Sources with badges
   - Graph stats panel (auto-expands)
   - Entity panel (shows extracted entities)

4. **User explores**
   - Click sources to view details
   - Expand entity panel to see relationships
   - View graph stats for insights

## 🎨 Visual Design Specs

### Colors
- Graph-Enhanced: `bg-green-100 text-green-800 border-green-300`
- Vector Only: `bg-blue-100 text-blue-800 border-blue-300`
- Graph Only: `bg-purple-100 text-purple-800 border-purple-300`
- Entity Badge: `bg-indigo-100 text-indigo-800`

### Icons
- Graph RAG: `Network` or `GitBranch`
- Graph-Enhanced: `Zap` or `Sparkles`
- Entity: `Tag` or `Hash`
- Stats: `BarChart3` or `Activity`

## 📱 Responsive Design

- Mobile: Stack panels vertically
- Tablet: Side-by-side stats and entities
- Desktop: Full layout with expandable panels

## ✅ Implementation Checklist

- [ ] Add `graphRagSearch()` to API service
- [ ] Create `GraphRagSearch.tsx` component
- [ ] Add Graph Stats Panel
- [ ] Add Source Badges (Graph-Enhanced indicators)
- [ ] Add Entity Panel
- [ ] Add route to routing config
- [ ] Add menu item to Sidebar
- [ ] Test with real queries
- [ ] Add loading states
- [ ] Error handling
- [ ] LocalStorage persistence

## 🚀 Future Enhancements (Optional)

1. **Interactive Graph Visualization**
   - D3.js or vis.js network graph
   - Click nodes to filter sources
   - Zoom/pan capabilities

2. **Entity Filtering**
   - Filter sources by entity type
   - Highlight related sources

3. **Relationship Path Display**
   - Show how documents are connected
   - Visual path from query entities to results

4. **Comparison Mode**
   - Side-by-side: Graph RAG vs Vector Only
   - Toggle to see difference

## 📊 Success Metrics

- Users can easily identify graph-enhanced results
- Entity relationships are clear and useful
- Graph stats provide valuable insights
- UI is consistent with existing components

---

**Status**: Ready for Implementation
**Priority**: High
**Estimated Time**: 2-3 hours

