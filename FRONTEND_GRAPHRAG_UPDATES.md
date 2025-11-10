# Frontend GraphRAG Updates - Implementation Guide

## Overview

This document describes the frontend changes needed to support and display semantic entity matching in GraphRAG search.

## Backend Updates (✅ Complete)

1. **Entity Embeddings**
   - All 3,020 entities now have 1024-dimensional embeddings
   - Generated using BGE-M3 model via Ollama
   - Stored in Neo4j entity nodes

2. **GraphRAG API Response**
   - Added `entity_matches` object with:
     - `exact_entities`: Array of exact entity matches
     - `semantic_entities`: Array of semantic matches with similarity scores
     - `total_exact`: Count of exact matches
     - `total_semantic`: Count of semantic matches
   - Updated `graph_stats` with:
     - `semantic_entity_matches`: Number of semantic matches
     - `exact_entity_matches`: Number of exact matches

## Frontend Updates Required

### 1. GraphRagSearch.tsx

#### Interfaces to Add
```typescript
interface EntityMatches {
  exact_entities: Array<{ name: string; type: string }>;
  semantic_entities: Array<{ name: string; type: string; similarity: number }>;
  total_exact: number;
  total_semantic: number;
}
```

#### State Updates
```typescript
const [entityMatches, setEntityMatches] = useState<EntityMatches | null>(null);
```

#### Response Handling
```typescript
// Set entity matches information
if (res.entity_matches) {
  setEntityMatches(res.entity_matches);
}
```

#### UI Display
Add entity match information to the Graph Stats Panel:

1. **Summary Stats** (add to existing stats bar):
   - Exact matches count with blue icon
   - Semantic matches count with purple icon

2. **Entity Details Panel** (collapsible):
   - **Exact Matches Section**:
     - Blue badges showing exact entity matches
     - Entity name and type
   
   - **Semantic Matches Section**:
     - Purple badges showing semantic matches
     - Entity name, type, and similarity percentage
     - Tooltip showing full similarity score

### 2. Visual Indicators

#### Color Scheme
- **Exact Matches**: Blue (`bg-blue-100`, `text-blue-800`)
- **Semantic Matches**: Purple (`bg-purple-100`, `text-purple-800`)
- **Icons**:
  - Exact: `<Check>` icon in blue
  - Semantic: `<Sparkles>` icon in purple

#### Badge Example
```tsx
{/* Exact Match */}
<span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-medium">
  {entity.name}
  <span className="ml-1 text-blue-600">({entity.type})</span>
</span>

{/* Semantic Match */}
<span 
  className="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs font-medium"
  title={`Similarity: ${(entity.similarity * 100).toFixed(1)}%`}
>
  {entity.name}
  <span className="ml-1 text-purple-600">({entity.type})</span>
  <span className="ml-1 text-purple-500">~{(entity.similarity * 100).toFixed(0)}%</span>
</span>
```

### 3. Example Implementation

```tsx
{/* Entity Matches Panel */}
{entityMatches && (entityMatches.exact_entities.length > 0 || entityMatches.semantic_entities.length > 0) && (
  <div className="mt-3 pt-3 border-t border-green-200">
    <div className="grid grid-cols-2 gap-4">
      {/* Exact Matches */}
      {entityMatches.exact_entities.length > 0 && (
        <div>
          <div className="flex items-center mb-2">
            <Check className="mr-2 h-4 w-4 text-blue-600" />
            <div className="text-sm text-gray-600">Exact Matches ({entityMatches.exact_entities.length}):</div>
          </div>
          <div className="flex flex-wrap gap-2">
            {entityMatches.exact_entities.slice(0, 10).map((entity, idx) => (
              <span
                key={idx}
                className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-medium"
              >
                {entity.name}
                <span className="ml-1 text-blue-600">({entity.type})</span>
              </span>
            ))}
          </div>
        </div>
      )}
      
      {/* Semantic Matches */}
      {entityMatches.semantic_entities.length > 0 && (
        <div>
          <div className="flex items-center mb-2">
            <Sparkles className="mr-2 h-4 w-4 text-purple-600" />
            <div className="text-sm text-gray-600">Semantic Matches ({entityMatches.semantic_entities.length}):</div>
          </div>
          <div className="flex flex-wrap gap-2">
            {entityMatches.semantic_entities.slice(0, 10).map((entity, idx) => (
              <span
                key={idx}
                className="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs font-medium"
                title={`Similarity: ${(entity.similarity * 100).toFixed(1)}%`}
              >
                {entity.name}
                <span className="ml-1 text-purple-600">({entity.type})</span>
                <span className="ml-1 text-purple-500">~{(entity.similarity * 100).toFixed(0)}%</span>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  </div>
)}
```

## Testing

### 1. Start the Backend
```bash
cd backend
source venv/bin/activate
python manage.py runserver
```

### 2. Start the Frontend
```bash
cd frontend
npm start
```

### 3. Test Queries

Try these queries to see semantic matching in action:

1. **"installation guide"** - Should find semantically similar entities like "setup", "configuration", etc.

2. **"troubleshooting errors"** - Should match "problem solving", "error codes", etc.

3. **"OpenLab setup"** - Should find "OpenLab CDS", "installation", "configuration"

4. **"version compatibility"** - Should match "version", "compatibility", "requirements"

### 4. Verify Display

Check that:
- Graph stats panel shows exact and semantic match counts
- Entity badges use correct colors (blue for exact, purple for semantic)
- Similarity percentages are displayed for semantic matches
- Tooltips show full similarity scores

## Benefits

1. **Better Query Understanding**: Finds relevant documents even when exact entity names don't match
2. **Visual Feedback**: Users can see which matches are exact vs semantic
3. **Transparency**: Similarity scores show confidence of semantic matches
4. **Improved Recall**: More relevant documents discovered through semantic matching

## Future Enhancements

1. **Adjustable Similarity Threshold**: Allow users to control semantic matching sensitivity
2. **Entity Highlighting**: Highlight matched entities in document content
3. **Interactive Entity Graph**: Visualize entity relationships
4. **Filter by Match Type**: Allow filtering results by exact vs semantic matches

