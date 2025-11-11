# AnyLab Green Color Palette

## Overview
This document defines the official green color palette for AnyLab UI, replacing all blue/purple/indigo colors with semantically appropriate green shades.

---

## Core Green Palette (Primary Brand)

Already defined in `tailwind.config.js` as `primary`, `brand`, and `success`:

```
50:  #f0fdf4  - Lightest backgrounds, subtle highlights
100: #dcfce7  - Light backgrounds, hover states
200: #bbf7d0  - Borders, dividers
300: #86efac  - Soft accents, secondary elements
400: #4ade80  - Interactive elements, icons
500: #22c55e  - Primary buttons, main CTAs
600: #16a34a  - Primary hover states, active elements
700: #15803d  - Dark accents, pressed states
800: #166534  - Text on light backgrounds
900: #14532d  - Darkest text, maximum contrast
```

---

## Semantic Color Mappings

### Replace Blue/Indigo with Green Variants

| Old Color | New Green Equivalent | Use Case |
|-----------|---------------------|----------|
| `bg-blue-50` | `bg-emerald-50` | Light info backgrounds |
| `bg-blue-100` | `bg-primary-100` | Info badges, light containers |
| `text-blue-600` | `text-primary-600` | Icons, links |
| `text-blue-700` | `text-primary-700` | Hover text, emphasized text |
| `text-blue-800` | `text-primary-800` | Strong text on light backgrounds |
| `border-blue-200` | `border-primary-200` | Light borders |
| `border-blue-300` | `border-primary-300` | Standard borders |
| `bg-blue-600` | `bg-primary-600` | Primary buttons |
| `hover:bg-blue-700` | `hover:bg-primary-700` | Button hover states |
| `focus:ring-blue-500` | `focus:ring-primary-500` | Input focus rings |

### Replace Indigo with Teal/Emerald (Cooler Green)

| Old Color | New Green Equivalent | Use Case |
|-----------|---------------------|----------|
| `bg-indigo-50` | `bg-teal-50` | Alternative light background |
| `bg-indigo-100` | `bg-teal-100` | Alternative badges |
| `text-indigo-600` | `text-teal-600` | Alternative icons |
| `text-indigo-700` | `text-teal-700` | Alternative text |
| `border-indigo-200` | `border-teal-200` | Alternative borders |
| `bg-indigo-600` | `bg-teal-600` | Alternative buttons |

**Teal Palette:**
```
50:  #f0fdfa
100: #ccfbf1
200: #99f6e4
300: #5eead4
400: #2dd4bf
500: #14b8a6
600: #0d9488
700: #0f766e
800: #115e59
900: #134e4a
```

### Replace Purple with Lime (Lighter Green)

| Old Color | New Green Equivalent | Use Case |
|-----------|---------------------|----------|
| `bg-purple-50` | `bg-lime-50` | Special feature backgrounds |
| `bg-purple-100` | `bg-lime-100` | Feature badges |
| `text-purple-600` | `text-lime-600` | Feature icons |
| `text-purple-700` | `text-lime-700` | Feature text |
| `border-purple-200` | `border-lime-200` | Feature borders |
| `bg-purple-600` | `bg-lime-600` | Feature buttons |

**Lime Palette:**
```
50:  #f7fee7
100: #ecfccb
200: #d9f99d
300: #bef264
400: #a3e635
500: #84cc16
600: #65a30d
700: #4d7c0f
800: #3f6212
900: #365314
```

---

## Specialized Use Cases

### Entity Type Colors (GraphRAG)
Use green gradient with different saturations:

```javascript
{
  'DEFAULT': 'bg-emerald-100 text-emerald-800 border-emerald-300',
  'VERSION': 'bg-teal-100 text-teal-800 border-teal-300',
  'PRODUCT': 'bg-primary-100 text-primary-800 border-primary-300',
  'PROBLEM': 'bg-orange-100 text-orange-800 border-orange-300', // Keep for semantic
  'OS': 'bg-yellow-100 text-yellow-800 border-yellow-300', // Keep for semantic
  'DATABASE': 'bg-lime-100 text-lime-800 border-lime-300',
  'FEATURE': 'bg-emerald-100 text-emerald-800 border-emerald-300',
}
```

### Status Colors (Document Processing)

```javascript
{
  pending: 'bg-yellow-100 text-yellow-800', // Keep yellow for pending
  metadata_extracting: 'bg-teal-100 text-teal-800',
  chunking: 'bg-primary-100 text-primary-800',
  embedding: 'bg-emerald-100 text-emerald-800',
  completed: 'bg-green-100 text-green-800',
  error: 'bg-red-100 text-red-800', // Keep red for errors
}
```

### Loading Spinners
Replace all blue/indigo spinners:
- `border-blue-600` → `border-primary-600`
- `border-indigo-600` → `border-primary-600`

### Form Focus States
Replace all blue/indigo focus rings:
- `focus:ring-blue-500` → `focus:ring-primary-500`
- `focus:border-blue-500` → `focus:border-primary-500`
- `focus:ring-indigo-500` → `focus:ring-primary-500`

### Gradient Backgrounds
Replace multi-color gradients with green variants:

```
// Old: from-blue-50 to-indigo-50
// New: from-emerald-50 to-teal-50

// Old: from-purple-50 to-violet-50
// New: from-lime-50 to-emerald-50

// Old: from-pink-50 to-rose-50
// New: from-green-50 to-emerald-50

// Old: from-indigo-50 to-blue-50
// New: from-teal-50 to-primary-50
```

---

## Color Families Quick Reference

### Primary Actions (Most Important)
- Background: `bg-primary-600` (#16a34a)
- Hover: `hover:bg-primary-700` (#15803d)
- Text: `text-white`
- Focus: `focus:ring-primary-500`

### Secondary Actions
- Background: `bg-primary-50` (#f0fdf4)
- Text: `text-primary-700` (#15803d)
- Border: `border-primary-200` (#bbf7d0)
- Hover: `hover:bg-primary-100`

### Info/Neutral (Replace Blue)
- Background: `bg-emerald-50`
- Text: `text-emerald-800`
- Border: `border-emerald-200`
- Icons: `text-emerald-600`

### Alternative/Secondary (Replace Indigo)
- Background: `bg-teal-50`
- Text: `text-teal-800`
- Border: `border-teal-200`
- Icons: `text-teal-600`

### Feature Highlights (Replace Purple)
- Background: `bg-lime-50`
- Text: `text-lime-800`
- Border: `border-lime-200`
- Icons: `text-lime-600`

### Keep These Colors (Semantic)
- **Success**: Green shades (keep as-is)
- **Warning**: Yellow/Amber shades (keep for warnings)
- **Error/Danger**: Red shades (keep for errors)
- **Pending**: Yellow shades (keep for pending states)

---

## Chart Colors (For Analytics)

Replace blue-dominant palette with green-based:

```javascript
// Old
const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

// New (Green-first with semantic colors)
const COLORS = [
  '#16a34a', // Primary green (600)
  '#0d9488', // Teal (600)
  '#65a30d', // Lime (600)
  '#059669', // Emerald (600)
  '#f59e0b', // Amber/Warning (keep)
  '#ef4444', // Red/Error (keep)
];

// For fills in Recharts
// Old: fill="#8884d8" (blue), fill="#3b82f6" (blue)
// New: fill="#16a34a" (primary), fill="#0d9488" (teal)
```

---

## Implementation Classes

### Add to Tailwind Config (if needed)

```javascript
extend: {
  colors: {
    // Emerald for info (replaces blue)
    emerald: {
      50: '#ecfdf5',
      100: '#d1fae5',
      200: '#a7f3d0',
      300: '#6ee7b7',
      400: '#34d399',
      500: '#10b981',
      600: '#059669',
      700: '#047857',
      800: '#065f46',
      900: '#064e3b',
    },
    // Teal for secondary (replaces indigo)
    teal: {
      50: '#f0fdfa',
      100: '#ccfbf1',
      200: '#99f6e4',
      300: '#5eead4',
      400: '#2dd4bf',
      500: '#14b8a6',
      600: '#0d9488',
      700: '#0f766e',
      800: '#115e59',
      900: '#134e4a',
    },
    // Lime for features (replaces purple)
    lime: {
      50: '#f7fee7',
      100: '#ecfccb',
      200: '#d9f99d',
      300: '#bef264',
      400: '#a3e635',
      500: '#84cc16',
      600: '#65a30d',
      700: '#4d7c0f',
      800: '#3f6212',
      900: '#365314',
    },
  }
}
```

---

## Migration Checklist

- [x] Define green color palette
- [ ] Update base UI components (badge, alert, button)
- [ ] Update CSS utility classes
- [ ] Replace blue in HomePage
- [ ] Replace blue/purple in Dashboard
- [ ] Replace blue in DocumentManager
- [ ] Replace blue/indigo in GraphRagSearch
- [ ] Replace blue in ChatAssistant
- [ ] Replace indigo in Login
- [ ] Update chart colors in Analytics
- [ ] Replace blue in all form inputs
- [ ] Replace blue in all loading spinners
- [ ] Update entity type colors
- [ ] Update status badge colors
- [ ] Test all components visually

---

## Visual Harmony Tips

1. **Consistency**: Use the same green shade for the same purpose across all components
2. **Contrast**: Ensure text on green backgrounds meets WCAG AA standards
3. **Hierarchy**: Use lighter greens (50-200) for backgrounds, darker (600-900) for text
4. **Accent**: Use teal/lime sparingly for visual interest while maintaining green dominance
5. **Semantic**: Keep yellow/orange/red for warnings/errors to maintain clear meaning

---

*Created: November 11, 2025*
*For: AnyLab UI Color Unification Project*

