import React, { useEffect, useMemo, useRef, useState } from 'react';
import { getDocument, GlobalWorkerOptions } from 'pdfjs-dist';
import * as XLSX from 'xlsx';
import { saveAs } from 'file-saver';
import { Download, FileText, Search, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';
// Use worker from public/ to avoid dynamic import issues
GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs';

type DocType = 'pdf' | 'docx' | 'txt' | 'xls' | 'xlsx' | 'ppt' | 'pptx';

interface DocumentViewerProps {
  title: string;
  url: string;
  docType: DocType;
  initialPage?: number;
  initialQuery?: string;
}

interface PdfHit {
  pageNumber: number;
  snippet: string;
}

// Dynamic scale calculation based on container width
const calculateScale = (containerWidth: number, pageWidth: number) => {
  const maxWidth = containerWidth - 32; // Account for padding
  return Math.min(1.5, Math.max(0.5, maxWidth / pageWidth));
};

function multiplyTransforms(m1: number[], m2: number[]): number[] {
  const [a1, b1, c1, d1, e1, f1] = m1;
  const [a2, b2, c2, d2, e2, f2] = m2;
  return [
    a1 * a2 + b1 * c2,
    a1 * b2 + b1 * d2,
    c1 * a2 + d1 * c2,
    c1 * b2 + d1 * d2,
    e1 * a2 + f1 * c2 + e2,
    e1 * b2 + f1 * d2 + f2,
  ];
}

const DocumentViewer: React.FC<DocumentViewerProps> = ({ title, url, docType, initialPage, initialQuery }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState(initialQuery || '');
  const [hits, setHits] = useState<PdfHit[]>([]);
  const [numPages, setNumPages] = useState<number>(0);
  const pageRefs = useRef<Record<number, HTMLCanvasElement | null>>({});
  const overlayRefs = useRef<Record<number, HTMLDivElement | null>>({});
  const [scale, setScale] = useState(1.0);
  const [currentScale, setCurrentScale] = useState(1.0);
  const [debugMode, setDebugMode] = useState(false);
  const [searching, setSearching] = useState(false);
  const [currentMatchIndex, setCurrentMatchIndex] = useState(0);
  const [totalMatches, setTotalMatches] = useState(0);
  const [loadingProgress, setLoadingProgress] = useState<{ current: number; total: number }>({ current: 0, total: 0 });
  const [isRendering, setIsRendering] = useState(false);

  // Render PDF pages
  useEffect(() => {
    if (docType !== 'pdf') {
      setLoading(false);
      return;
    }
    let cancelled = false;
    
    // Cleanup function for memory management
    const cleanup = () => {
      // Clear canvas references to free memory
      Object.values(pageRefs.current).forEach(canvas => {
        if (canvas) {
          const context = canvas.getContext('2d');
          if (context) {
            context.clearRect(0, 0, canvas.width, canvas.height);
          }
        }
      });
      pageRefs.current = {};
      overlayRefs.current = {};
    };
    
    const run = async () => {
      try {
        const headers: Record<string, string> = {};
        const token = localStorage.getItem(process.env.REACT_APP_JWT_STORAGE_KEY || 'onlab_token');
        if (token) headers.Authorization = `Bearer ${token}`;
        const res = await fetch(url, { headers });
        const buf = await res.arrayBuffer();
        if (cancelled) return;

        if (containerRef.current) containerRef.current.innerHTML = '';

        const pdf = await getDocument({ data: buf }).promise;
        if (cancelled) return;
        setNumPages(pdf.numPages);

        // Calculate optimal scale based on container width
        const containerWidth = containerRef.current?.clientWidth || 800;
        const firstPage = await pdf.getPage(1);
        const originalViewport = firstPage.getViewport({ scale: 1.0 });
        const optimalScale = calculateScale(containerWidth, originalViewport.width);
        setScale(optimalScale);

        setLoadingProgress({ current: 0, total: pdf.numPages });
        
        for (let p = 1; p <= pdf.numPages; p += 1) {
          if (cancelled) return;
          
          setLoadingProgress({ current: p, total: pdf.numPages });
          
          const page = await pdf.getPage(p);
          if (cancelled) return;
          const viewport = page.getViewport({ scale: optimalScale });

          // Create wrapper per page
          let wrapper = containerRef.current?.querySelector<HTMLDivElement>(`[data-page='${p}']`);
          if (!wrapper) {
            wrapper = document.createElement('div');
            wrapper.setAttribute('data-page', String(p));
            wrapper.style.position = 'relative';
            wrapper.style.display = 'flex';
            wrapper.style.justifyContent = 'center';
            wrapper.style.marginBottom = '20px';
            wrapper.className = 'relative flex justify-center mb-5';
            containerRef.current?.appendChild(wrapper);
          }

          // Canvas
          let canvas = pageRefs.current[p];
          if (!canvas) {
            canvas = document.createElement('canvas');
            pageRefs.current[p] = canvas;
          }
          if (wrapper && canvas.parentElement !== wrapper) wrapper.appendChild(canvas);

          const context = canvas.getContext('2d');
          if (!context) continue;
          canvas.width = viewport.width;
          canvas.height = viewport.height;
          canvas.style.maxWidth = '100%';
          canvas.style.height = 'auto';
          context.save();
          context.fillStyle = '#ffffff';
          context.fillRect(0, 0, canvas.width, canvas.height);
          context.restore();
          await page.render({ canvasContext: context as any, viewport } as any).promise;

          // Overlay for highlights - positioned relative to canvas for accurate scaling
          let overlay = overlayRefs.current[p];
          if (!overlay) {
            overlay = document.createElement('div');
            overlayRefs.current[p] = overlay;
          }
          overlay.style.position = 'absolute';
          overlay.style.left = '0px';
          overlay.style.top = '0px';
          overlay.style.width = `${viewport.width}px`;
          overlay.style.height = `${viewport.height}px`;
          overlay.style.pointerEvents = 'none';
          overlay.style.maxWidth = '100%';
          overlay.style.transformOrigin = 'top left';
          overlay.style.zIndex = '10';
          overlay.innerHTML = '';
          if (wrapper && overlay.parentElement !== wrapper) wrapper.appendChild(overlay);

          // Debug: Show text boundaries if debug mode is enabled
          if (debugMode) {
            const textContent = await page.getTextContent();
            for (const item of textContent.items) {
              if ('transform' in item && 'str' in item) {
                const transform = item.transform;
                const [a, b, c, d, e, f] = transform;
                const debugEl = document.createElement('div');
                debugEl.style.position = 'absolute';
                debugEl.style.left = `${e}px`;
                debugEl.style.top = `${viewport.height - f - Math.abs((item as any).height || 12)}px`;
                debugEl.style.width = `${(item as any).width}px`;
                debugEl.style.height = `${Math.abs((item as any).height || 12)}px`;
                debugEl.style.border = '1px solid red';
                debugEl.style.background = 'rgba(255, 0, 0, 0.1)';
                debugEl.style.pointerEvents = 'none';
                debugEl.style.fontSize = '8px';
                debugEl.style.color = 'red';
                debugEl.textContent = item.str?.substring(0, 10) || '';
                overlay.appendChild(debugEl);
              }
            }
          }
        }

        setLoading(false);
        setLoadingProgress({ current: 0, total: 0 });
        if (initialPage && pageRefs.current[initialPage]) {
          pageRefs.current[initialPage]?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
        if (initialQuery) {
          findInPdf(initialQuery).catch(() => {});
        }
      } catch (e: any) {
        setError(e?.message || 'Failed to load PDF');
        setLoading(false);
      }
    };
    run();
    return () => { 
      cancelled = true; 
      cleanup();
    };
  }, [url, docType, initialPage, initialQuery]);

  // Re-render highlights when scale changes
  useEffect(() => {
    if (searchQuery.trim() && docType === 'pdf') {
      findInPdf(searchQuery);
    }
  }, [currentScale, searchQuery, docType]);

  // Performance optimization: Debounce search to avoid excessive API calls
  useEffect(() => {
    if (!searchQuery.trim() || docType !== 'pdf') return;
    
    const timeoutId = setTimeout(() => {
      findInPdf(searchQuery);
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [searchQuery, docType]);

  // Re-render debug visualization when debug mode changes
  useEffect(() => {
    if (docType === 'pdf' && debugMode) {
      // Re-render the PDF to show debug visualization
      const event = new Event('resize');
      window.dispatchEvent(event);
    }
  }, [debugMode, docType]);

  // Test function to verify text extraction
  const testTextExtraction = async () => {
    if (docType !== 'pdf') return;
    
    try {
      const headers: Record<string, string> = {};
      const token = localStorage.getItem(process.env.REACT_APP_JWT_STORAGE_KEY || 'onlab_token');
      if (token) headers.Authorization = `Bearer ${token}`;
      
      const res = await fetch(url, { headers });
      const buf = await res.arrayBuffer();
      const pdf = await getDocument({ data: buf }).promise;
      
      const page = await pdf.getPage(1);
      const textContent = await page.getTextContent();
      
      console.log('Text content extracted:', textContent.items.length, 'items');
      console.log('First few items:', textContent.items.slice(0, 5));
      
      // Show first 100 characters of text
      const pageText = textContent.items.map((item: any) => item.str).join(' ');
      console.log('Page text (first 100 chars):', pageText.substring(0, 100));
      
    } catch (error) {
      console.error('Text extraction test failed:', error);
    }
  };

  // Enhanced search + highlight with advanced features from django-pgvector-pdf
  const findInPdf = async (query: string) => {
    try {
      setSearching(true);
      setHits([]);
      
      if (!query.trim()) {
        // Clear all highlights
        Object.values(overlayRefs.current).forEach((overlay) => {
          if (overlay) overlay.innerHTML = '';
        });
        setSearching(false);
        return;
      }

      // Performance optimization: Limit search to first 10 pages for very large PDFs
      const maxSearchPages = Math.min(numPages, 10);

      const headers: Record<string, string> = {};
      const token = localStorage.getItem(process.env.REACT_APP_JWT_STORAGE_KEY || 'onlab_token');
      if (token) headers.Authorization = `Bearer ${token}`;
      
      const res = await fetch(url, { headers });
      const buf = await res.arrayBuffer();
      const pdf = await getDocument({ data: buf }).promise;

      const found: PdfHit[] = [];
      const searchTerm = query.toLowerCase();
      let matchCount = 0;

      // Process each page
      for (let pageNum = 1; pageNum <= maxSearchPages; pageNum++) {
        const page = await pdf.getPage(pageNum);
        const viewport = page.getViewport({ scale: scale * currentScale });
        
        // Get text content for this page
        const textContent = await page.getTextContent();
        
        // Create snippet for search results
        const pageText = textContent.items.map((item: any) => item.str).join(' ');
        const textLower = pageText.toLowerCase();
        const firstMatchIndex = textLower.indexOf(searchTerm);
        
        if (firstMatchIndex >= 0) {
          const start = Math.max(0, firstMatchIndex - 50);
          const end = Math.min(pageText.length, firstMatchIndex + searchTerm.length + 50);
          const snippet = pageText.substring(start, end);
          found.push({ pageNumber: pageNum, snippet });
        }

        // Enhanced highlighting approach with better positioning and zoom handling
        const highlights: Array<{ 
          x: number; 
          y: number; 
          width: number; 
          height: number; 
          isCurrent: boolean;
          matchIndex: number;
        }> = [];
        
        for (const item of textContent.items) {
          if (!('str' in item) || !('transform' in item)) continue;
          
          const text = item.str || '';
          const textLower = text.toLowerCase();
          
          if (!textLower.includes(searchTerm)) continue;
          
          // Find all matches in this text item
          let searchIndex = 0;
          while (true) {
            const matchIndex = textLower.indexOf(searchTerm, searchIndex);
            if (matchIndex === -1) break;
            
            // Get the transform matrix [a, b, c, d, e, f]
            const transform = item.transform;
            const [a, b, c, d, e, f] = transform;
            
            // Calculate character width more accurately using the transform matrix
            const itemWidth = (item as any).width || 0;
            const charWidth = itemWidth / Math.max(1, text.length);
            
            // Calculate the position of the matched text in PDF coordinates
            // Use transform matrix to get accurate positioning
            const matchStartOffset = matchIndex * charWidth;
            const matchLength = searchTerm.length * charWidth;
            
            // Apply transform matrix to get actual coordinates
            const matchStartX = e + (matchStartOffset * a);
            const matchWidth = Math.max(4, matchLength * Math.abs(a) + 2); // Add padding and account for scaling
            
            // Get item height from transform or fallback
            const itemHeight = Math.abs(d) || Math.abs((item as any).height) || 12;
            
            // Convert PDF coordinates to viewport coordinates with proper scaling
            // Account for both the initial scale and current zoom scale
            const totalScale = viewport.scale; // This already includes both scales
            const canvasElement = pageRefs.current[pageNum];
            const canvasScale = canvasElement ? canvasElement.offsetWidth / canvasElement.width : 1;
            
            const highlight = {
              x: (matchStartX - 1) * canvasScale, // Use canvas scale for accurate positioning
              y: (viewport.height - f - itemHeight) * canvasScale,
              width: matchWidth * canvasScale,
              height: itemHeight * canvasScale,
              isCurrent: false,
              matchIndex: matchCount
            };
            
            highlights.push(highlight);
            matchCount++;
            searchIndex = matchIndex + searchTerm.length;
          }
        }

        // Apply enhanced highlights to the overlay
        const overlay = overlayRefs.current[pageNum];
        if (overlay) {
          overlay.innerHTML = '';
          
          for (const highlight of highlights) {
            const highlightEl = document.createElement('div');
            highlightEl.style.position = 'absolute';
            highlightEl.style.left = `${highlight.x}px`;
            highlightEl.style.top = `${highlight.y}px`;
            highlightEl.style.width = `${highlight.width}px`;
            highlightEl.style.height = `${highlight.height}px`;
            highlightEl.style.backgroundColor = highlight.isCurrent ? 'rgba(255, 165, 0, 0.8)' : 'rgba(255, 255, 0, 0.8)';
            highlightEl.style.border = highlight.isCurrent ? '2px solid rgba(255, 140, 0, 0.9)' : '1px solid rgba(255, 200, 0, 0.9)';
            highlightEl.style.pointerEvents = 'none';
            highlightEl.style.borderRadius = '1px';
            highlightEl.style.zIndex = '10';
            highlightEl.style.boxShadow = highlight.isCurrent ? '0 0 4px rgba(255, 140, 0, 0.6)' : '0 0 2px rgba(255, 200, 0, 0.4)';
            highlightEl.setAttribute('data-match-index', highlight.matchIndex.toString());
            overlay.appendChild(highlightEl);
          }
        }
      }

      setHits(found);
      setTotalMatches(matchCount);
      setCurrentMatchIndex(0);
      setSearching(false);
      
      // Auto-scroll to first result if found
      if (found.length > 0) {
        const firstPage = found[0].pageNumber;
        const pageElement = pageRefs.current[firstPage];
        if (pageElement) {
          pageElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }
    } catch (error) {
      console.error('Search error:', error);
      setSearching(false);
    }
  };

  // Navigate to next/previous search result
  const navigateToMatch = (direction: 'next' | 'prev') => {
    if (totalMatches === 0) return;
    
    let newIndex = currentMatchIndex;
    if (direction === 'next') {
      newIndex = (currentMatchIndex + 1) % totalMatches;
    } else {
      newIndex = (currentMatchIndex - 1 + totalMatches) % totalMatches;
    }
    
    setCurrentMatchIndex(newIndex);
    
    // Update highlight colors
    Object.values(overlayRefs.current).forEach((overlay) => {
      if (overlay) {
        const highlights = overlay.querySelectorAll('[data-match-index]');
        highlights.forEach((highlight, index) => {
          const isCurrent = parseInt(highlight.getAttribute('data-match-index') || '0') === newIndex;
          const el = highlight as HTMLElement;
          el.style.backgroundColor = isCurrent ? 'rgba(255, 165, 0, 0.8)' : 'rgba(255, 255, 0, 0.8)';
          el.style.border = isCurrent ? '2px solid rgba(255, 140, 0, 0.9)' : '1px solid rgba(255, 200, 0, 0.9)';
          el.style.boxShadow = isCurrent ? '0 0 4px rgba(255, 140, 0, 0.6)' : '0 0 2px rgba(255, 200, 0, 0.4)';
        });
      }
    });
  };

  // Update highlights when scale changes
  useEffect(() => {
    if (searchQuery.trim() && totalMatches > 0) {
      // Re-run search to update highlight positions with new scale
      findInPdf(searchQuery);
    }
  }, [currentScale]);

  // Keyboard shortcuts for search navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target && (e.target as HTMLElement).tagName === 'INPUT') return;
      
      if (totalMatches > 0) {
        if (e.key === 'ArrowRight' || e.key === 'n') {
          e.preventDefault();
          navigateToMatch('next');
        } else if (e.key === 'ArrowLeft' || e.key === 'p') {
          e.preventDefault();
          navigateToMatch('prev');
        }
      }
      
      // Ctrl+F for search focus
      if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
        e.preventDefault();
        const searchInput = document.querySelector('input[placeholder*="Search"]') as HTMLInputElement;
        if (searchInput) {
          searchInput.focus();
          searchInput.select();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [totalMatches, currentMatchIndex, navigateToMatch]);

  const onSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (docType === 'pdf') {
      findInPdf(searchQuery);
    } else if (docType === 'docx' || docType === 'txt') {
      const root = document.getElementById('docx-root');
      if (!root) return;
      const text = root.textContent || '';
      const idx = text.toLowerCase().indexOf(searchQuery.toLowerCase());
      if (idx >= 0) {
        const range = document.createRange();
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
        let pos = 0;
        let node: Node | null;
        while ((node = walker.nextNode())) {
          const nodeText = (node.textContent || '');
          if (pos + nodeText.length >= idx) {
            const offset = idx - pos;
            try {
              range.setStart(node, offset);
              range.setEnd(node, Math.min(nodeText.length, offset + searchQuery.length));
              const rect = range.getBoundingClientRect();
              window.scrollTo({ top: window.scrollY + rect.top - 100, behavior: 'smooth' });
            } catch {}
            break;
          }
          pos += nodeText.length;
        }
      }
    }
  };

  const rightPanel = useMemo(() => (
    <div className="w-80 border-l p-4 overflow-auto">
      <div className="mb-3">
        <div className="flex items-center space-x-2 mb-2">
          <input
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              // Auto-search as user types (with debounce)
              if (e.target.value.trim() && docType === 'pdf') {
                setTimeout(() => findInPdf(e.target.value), 300);
              } else if (!e.target.value.trim()) {
                // Clear highlights when search is empty
                Object.values(overlayRefs.current).forEach((o) => { if (o) o.innerHTML=''; });
                setHits([]);
                setTotalMatches(0);
                setCurrentMatchIndex(0);
              }
            }}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && docType === 'pdf') {
                findInPdf(searchQuery);
              }
            }}
            placeholder="Search in document..."
            className="flex-1 px-3 py-2 border rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <button
            onClick={() => findInPdf(searchQuery)}
            className="px-3 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 focus:ring-2 focus:ring-blue-500"
          >
            Search
          </button>
        </div>
        
        {/* Enhanced search navigation */}
        {totalMatches > 0 && (
          <div className="flex items-center justify-between mb-2 p-2 bg-blue-50 rounded border">
            <div className="text-sm text-blue-700">
              Match {currentMatchIndex + 1} of {totalMatches}
            </div>
            <div className="flex space-x-1">
              <button
                onClick={() => navigateToMatch('prev')}
                disabled={totalMatches <= 1}
                className="px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                ← Prev
              </button>
              <button
                onClick={() => navigateToMatch('next')}
                disabled={totalMatches <= 1}
                className="px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next →
              </button>
            </div>
          </div>
        )}
        {debugMode && (
          <div className="text-xs text-red-600 mb-2 p-2 bg-red-50 border border-red-200 rounded">
            🔍 Debug mode: Red boxes show text boundaries
          </div>
        )}
        {searchQuery.trim() && (
          <div className="text-xs text-gray-600 mb-2 flex items-center space-x-2">
            <span>Searching for: "{searchQuery}"</span>
            {searching && (
              <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-blue-500"></div>
            )}
          </div>
        )}
      </div>
      {docType === 'pdf' && (
        <div className="space-y-2">
          {searching ? (
            <div className="text-sm text-gray-500 flex items-center space-x-2">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
              <span>Searching...</span>
            </div>
          ) : hits.length === 0 ? (
            searchQuery.trim() ? (
              <p className="text-sm text-gray-500">No results found for "{searchQuery}"</p>
            ) : (
              <p className="text-sm text-gray-500">Enter a search term to find content</p>
            )
          ) : (
            <>
              <div className="text-sm font-medium text-gray-700 mb-2">
                Found {hits.length} result{hits.length !== 1 ? 's' : ''} for "{searchQuery}"
              </div>
              {hits.map((h, i) => (
                <button
                  key={`${h.pageNumber}-${i}`}
                  onClick={() => pageRefs.current[h.pageNumber]?.scrollIntoView({ behavior: 'smooth', block: 'center' })}
                  className="block text-left w-full p-3 border rounded hover:bg-blue-50 hover:border-blue-200 transition-colors"
                >
                  <div className="text-xs text-blue-600 font-medium mb-1">Page {h.pageNumber}</div>
                  <div className="text-sm text-gray-700 leading-relaxed">{h.snippet}</div>
                </button>
              ))}
            </>
          )}
        </div>
      )}
    </div>
  ), [hits, searchQuery, docType]);

  return (
    <div className="flex h-[calc(100vh-220px)] border rounded overflow-hidden">
      <div className="flex-1 flex flex-col">
        <div className="px-4 py-2 border-b font-semibold">{title}</div>
        {loading && (
          <div className="p-6 text-gray-600">
            <div className="flex items-center space-x-2 mb-4">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
              <span>Loading document...</span>
            </div>
            {loadingProgress.total > 0 && (
              <>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${(loadingProgress.current / loadingProgress.total) * 100}%` }}
                  ></div>
                </div>
                <div className="text-sm text-gray-500 mt-2">
                  Page {loadingProgress.current} of {loadingProgress.total}
                </div>
              </>
            )}
          </div>
        )}
        {error && (
          <div className="p-6 text-red-600">{error}</div>
        )}
        {!error && docType === 'pdf' && (
          <>
            <div className="px-4 py-2 border-b bg-gray-50 flex items-center justify-between sticky top-0 z-50">
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-600">Zoom:</span>
                <button
                  onClick={() => setCurrentScale(Math.max(0.5, currentScale - 0.1))}
                  className="px-2 py-1 text-sm bg-white border border-gray-300 rounded hover:bg-gray-50"
                >
                  -
                </button>
                <span className="text-sm font-medium min-w-[60px] text-center">
                  {Math.round(currentScale * 100)}%
                </span>
                <button
                  onClick={() => setCurrentScale(Math.min(2.0, currentScale + 0.1))}
                  className="px-2 py-1 text-sm bg-white border border-gray-300 rounded hover:bg-gray-50"
                >
                  +
                </button>
                <button
                  onClick={() => setCurrentScale(scale)}
                  className="px-2 py-1 text-sm bg-blue-500 text-white border border-blue-500 rounded hover:bg-blue-600"
                >
                  Fit
                </button>
                <button
                  onClick={() => setDebugMode(!debugMode)}
                  className={`px-2 py-1 text-sm border rounded ${
                    debugMode 
                      ? 'bg-red-500 text-white border-red-500 hover:bg-red-600' 
                      : 'bg-white border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  Debug
                </button>
                <button
                  onClick={() => findInPdf('test')}
                  className="px-2 py-1 text-sm bg-green-500 text-white border border-green-500 rounded hover:bg-green-600"
                >
                  Test
                </button>
                <button
                  onClick={testTextExtraction}
                  className="px-2 py-1 text-sm bg-purple-500 text-white border border-purple-500 rounded hover:bg-purple-600"
                >
                  Extract
                </button>
              </div>
              <div className="text-sm text-gray-600">
                Page {numPages > 0 ? `1 of ${numPages}` : ''}
              </div>
            </div>
            <div className="flex-1 overflow-auto">
              <div ref={containerRef} className="p-4 w-full" style={{ transform: `scale(${currentScale})`, transformOrigin: 'top center' }} />
            </div>
          </>
        )}
        {!error && docType === 'docx' && (
          <DocxRenderer url={url} />
        )}
        {!error && docType === 'txt' && (
          <TxtRenderer url={url} />
        )}
        {!error && (docType === 'xls' || docType === 'xlsx') && (
          <XlsRenderer url={url} />
        )}
        {!error && (docType === 'ppt' || docType === 'pptx') && (
          <PptRenderer url={url} />
        )}
      </div>
      {rightPanel}
    </div>
  );
};

const DocxRenderer: React.FC<{ url: string }> = ({ url }) => {
  const [html, setHtml] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<number>(0);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const headers: Record<string, string> = {};
        const token = localStorage.getItem(process.env.REACT_APP_JWT_STORAGE_KEY || 'onlab_token');
        if (token) headers.Authorization = `Bearer ${token}`;
        
        const res = await fetch(url, { headers });
        if (!res.ok) {
          throw new Error(`Failed to fetch document: ${res.status} ${res.statusText}`);
        }
        const buf = await res.arrayBuffer();
        const mammoth = await import('mammoth');
        const result = await mammoth.convertToHtml({ arrayBuffer: buf });
        if (!cancelled) {
          setHtml(result.value);
          setLoading(false);
        }
      } catch (e: any) {
        if (!cancelled) {
          setError(e?.message || 'Failed to load DOCX');
          setLoading(false);
        }
      }
    })();
    return () => { cancelled = true; };
  }, [url]);

  const searchInDocument = (query: string) => {
    const root = document.getElementById('docx-root');
    if (!root || !query.trim()) {
      setSearchResults(0);
      // Clear existing highlights
      const existingHighlights = root?.querySelectorAll('.search-highlight');
      existingHighlights?.forEach(el => {
        const parent = el.parentNode;
        if (parent) {
          parent.replaceChild(document.createTextNode(el.textContent || ''), el);
          parent.normalize();
        }
      });
      return;
    }

    // Clear existing highlights
    const existingHighlights = root.querySelectorAll('.search-highlight');
    existingHighlights.forEach(el => {
      const parent = el.parentNode;
      if (parent) {
        parent.replaceChild(document.createTextNode(el.textContent || ''), el);
        parent.normalize();
      }
    });

    // Search and highlight
    const walker = document.createTreeWalker(
      root,
      NodeFilter.SHOW_TEXT,
      null
    );

    const textNodes: Text[] = [];
    let node;
    while (node = walker.nextNode()) {
      textNodes.push(node as Text);
    }

    let matchCount = 0;
    const searchTerm = query.toLowerCase();

    textNodes.forEach(textNode => {
      const text = textNode.textContent || '';
      const textLower = text.toLowerCase();
      
      if (textLower.includes(searchTerm)) {
        const parent = textNode.parentNode;
        if (!parent) return;

        const parts = text.split(new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi'));
        const fragment = document.createDocumentFragment();

        parts.forEach(part => {
          if (part.toLowerCase() === searchTerm) {
            const highlight = document.createElement('span');
            highlight.className = 'search-highlight bg-yellow-300 px-1 rounded';
            highlight.textContent = part;
            fragment.appendChild(highlight);
            matchCount++;
          } else if (part) {
            fragment.appendChild(document.createTextNode(part));
          }
        });

        parent.replaceChild(fragment, textNode);
      }
    });

    setSearchResults(matchCount);
  };

  const downloadDocx = async () => {
    try {
      const headers: Record<string, string> = {};
      const token = localStorage.getItem(process.env.REACT_APP_JWT_STORAGE_KEY || 'onlab_token');
      if (token) headers.Authorization = `Bearer ${token}`;
      
      const res = await fetch(url, { headers });
      const blob = await res.blob();
      const filename = url.split('/').pop() || 'document.docx';
      saveAs(blob, filename);
    } catch (e: any) {
      console.error('Download failed:', e);
    }
  };

  if (loading) return <div className="p-6 text-gray-600 flex items-center space-x-2">
    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
    <span>Loading Word document...</span>
  </div>;

  if (error) return <div className="p-6 text-red-600">{error}</div>;

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-4 border-b bg-gray-50">
        <div className="flex items-center space-x-4">
          <FileText size={20} className="text-gray-600" />
          <span className="text-sm font-medium text-gray-700">Word Document</span>
        </div>
        
        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-2">
            <Search size={16} className="text-gray-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                searchInDocument(e.target.value);
              }}
              placeholder="Search in document..."
              className="px-3 py-1 text-sm border rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            {searchResults > 0 && (
              <span className="text-sm text-blue-600">{searchResults} matches</span>
            )}
          </div>
          <button
            onClick={downloadDocx}
            className="flex items-center space-x-1 px-3 py-1 text-sm bg-green-500 text-white rounded hover:bg-green-600"
          >
            <Download size={16} />
            <span>Download</span>
          </button>
        </div>
      </div>

      {/* Document content */}
      <div className="flex-1 overflow-auto">
        <div id="docx-root" className="p-4 prose max-w-none" dangerouslySetInnerHTML={{ __html: html }} />
      </div>
    </div>
  );
};

const TxtRenderer: React.FC<{ url: string }> = ({ url }) => {
  const [text, setText] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<number>(0);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const headers: Record<string, string> = {};
        const token = localStorage.getItem(process.env.REACT_APP_JWT_STORAGE_KEY || 'onlab_token');
        if (token) headers.Authorization = `Bearer ${token}`;
        
        const res = await fetch(url, { headers });
        if (!res.ok) {
          throw new Error(`Failed to fetch document: ${res.status} ${res.statusText}`);
        }
        const t = await res.text();
        if (!cancelled) {
          setText(t);
          setLoading(false);
        }
      } catch (e: any) {
        if (!cancelled) {
          setError(e?.message || 'Failed to load text file');
          setLoading(false);
        }
      }
    })();
    return () => { cancelled = true; };
  }, [url]);

  const getHighlightedText = (text: string, query: string) => {
    if (!query.trim()) {
      setSearchResults(0);
      return text;
    }

    const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    const matches = text.match(regex);
    setSearchResults(matches ? matches.length : 0);

    return text.split(regex).map((part, index) => {
      if (part.toLowerCase() === query.toLowerCase()) {
        return `<mark class="bg-yellow-300 px-1 rounded">${part}</mark>`;
      }
      return part;
    }).join('');
  };

  const downloadTxt = async () => {
    try {
      const headers: Record<string, string> = {};
      const token = localStorage.getItem(process.env.REACT_APP_JWT_STORAGE_KEY || 'onlab_token');
      if (token) headers.Authorization = `Bearer ${token}`;
      
      const res = await fetch(url, { headers });
      const blob = await res.blob();
      const filename = url.split('/').pop() || 'document.txt';
      saveAs(blob, filename);
    } catch (e: any) {
      console.error('Download failed:', e);
    }
  };

  if (loading) return <div className="p-6 text-gray-600 flex items-center space-x-2">
    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
    <span>Loading text file...</span>
  </div>;

  if (error) return <div className="p-6 text-red-600">{error}</div>;

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-4 border-b bg-gray-50">
        <div className="flex items-center space-x-4">
          <FileText size={20} className="text-gray-600" />
          <span className="text-sm font-medium text-gray-700">Text Document</span>
        </div>
        
        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-2">
            <Search size={16} className="text-gray-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search in text..."
              className="px-3 py-1 text-sm border rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            {searchResults > 0 && (
              <span className="text-sm text-blue-600">{searchResults} matches</span>
            )}
          </div>
          <button
            onClick={downloadTxt}
            className="flex items-center space-x-1 px-3 py-1 text-sm bg-green-500 text-white rounded hover:bg-green-600"
          >
            <Download size={16} />
            <span>Download</span>
          </button>
        </div>
      </div>

      {/* Text content */}
      <div className="flex-1 overflow-auto">
        <pre 
          className="p-4 whitespace-pre-wrap break-words font-mono text-sm"
          dangerouslySetInnerHTML={{ 
            __html: getHighlightedText(text, searchQuery) 
          }}
        />
      </div>
    </div>
  );
};

const XlsRenderer: React.FC<{ url: string }> = ({ url }) => {
  const [workbook, setWorkbook] = useState<XLSX.WorkBook | null>(null);
  const [activeSheet, setActiveSheet] = useState<string>('');
  const [sheetData, setSheetData] = useState<any[][]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Array<{row: number, col: number, value: string}>>([]);
  const [visibleRows, setVisibleRows] = useState<number>(50); // Performance: Show only first 50 rows initially
  const [isLoadingMore, setIsLoadingMore] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const headers: Record<string, string> = {};
        const token = localStorage.getItem(process.env.REACT_APP_JWT_STORAGE_KEY || 'onlab_token');
        if (token) headers.Authorization = `Bearer ${token}`;
        
        const res = await fetch(url, { headers });
        if (!res.ok) {
          throw new Error(`Failed to fetch Excel file: ${res.status} ${res.statusText}`);
        }
        const buf = await res.arrayBuffer();
        
        if (cancelled) return;
        
        const wb = XLSX.read(buf, { type: 'array' });
        setWorkbook(wb);
        
        // Set first sheet as active
        const firstSheetName = wb.SheetNames[0];
        if (firstSheetName) {
          setActiveSheet(firstSheetName);
          const sheet = wb.Sheets[firstSheetName];
          const data = XLSX.utils.sheet_to_json(sheet, { header: 1, defval: '' });
          setSheetData(data as any[][]);
        }
        
        setLoading(false);
      } catch (e: any) {
        if (!cancelled) {
          setError(e?.message || 'Failed to load Excel file');
          setLoading(false);
        }
      }
    })();
    return () => { cancelled = true; };
  }, [url]);

  const switchSheet = (sheetName: string) => {
    if (workbook && workbook.Sheets[sheetName]) {
      setActiveSheet(sheetName);
      const sheet = workbook.Sheets[sheetName];
      const data = XLSX.utils.sheet_to_json(sheet, { header: 1, defval: '' });
      setSheetData(data as any[][]);
      setSearchResults([]); // Clear search results when switching sheets
    }
  };

  const searchInSheet = (query: string) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }

    const results: Array<{row: number, col: number, value: string}> = [];
    const searchTerm = query.toLowerCase();

    // Performance optimization: Limit search to visible rows for large datasets
    const searchLimit = Math.min(sheetData.length, visibleRows + 100);
    
    for (let rowIndex = 0; rowIndex < searchLimit; rowIndex++) {
      const row = sheetData[rowIndex];
      if (!row) continue;
      
      for (let colIndex = 0; colIndex < row.length; colIndex++) {
        const cell = row[colIndex];
        const cellValue = String(cell || '').toLowerCase();
        if (cellValue.includes(searchTerm)) {
          results.push({
            row: rowIndex,
            col: colIndex,
            value: String(cell || '')
          });
        }
      }
    }

    setSearchResults(results);
  };

  const loadMoreRows = () => {
    setIsLoadingMore(true);
    setTimeout(() => {
      setVisibleRows(prev => Math.min(prev + 50, sheetData.length));
      setIsLoadingMore(false);
    }, 100);
  };

  const downloadExcel = () => {
    if (workbook) {
      const wbout = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
      const blob = new Blob([wbout], { type: 'application/octet-stream' });
      saveAs(blob, `${activeSheet || 'spreadsheet'}.xlsx`);
    }
  };

  if (loading) return <div className="p-6 text-gray-600 flex items-center space-x-2">
    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
    <span>Loading Excel file...</span>
  </div>;
  
  if (error) return <div className="p-6 text-red-600">{error}</div>;

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-4 border-b bg-gray-50">
        <div className="flex items-center space-x-4">
          {/* Sheet tabs */}
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-700">Sheets:</span>
            {workbook?.SheetNames.map(sheetName => (
              <button
                key={sheetName}
                onClick={() => switchSheet(sheetName)}
                className={`px-3 py-1 text-sm rounded ${
                  activeSheet === sheetName 
                    ? 'bg-blue-500 text-white' 
                    : 'bg-white border border-gray-300 hover:bg-gray-50'
                }`}
              >
                {sheetName}
              </button>
            ))}
          </div>
        </div>
        
        {/* Search and actions */}
        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-2">
            <Search size={16} className="text-gray-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                searchInSheet(e.target.value);
              }}
              placeholder="Search in sheet..."
              className="px-3 py-1 text-sm border rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            {searchResults.length > 0 && (
              <span className="text-sm text-blue-600">{searchResults.length} matches</span>
            )}
          </div>
          <button
            onClick={downloadExcel}
            className="flex items-center space-x-1 px-3 py-1 text-sm bg-green-500 text-white rounded hover:bg-green-600"
          >
            <Download size={16} />
            <span>Download</span>
          </button>
        </div>
      </div>

      {/* Spreadsheet content */}
      <div className="flex-1 overflow-auto">
        <table className="min-w-full border-collapse">
          <tbody>
            {sheetData.slice(0, visibleRows).map((row, rowIndex) => (
              <tr key={rowIndex} className="border-b">
                <td className="px-2 py-1 bg-gray-100 border-r text-xs text-gray-600 font-mono w-12 text-center">
                  {rowIndex + 1}
                </td>
                {row.map((cell, colIndex) => {
                  const isSearchMatch = searchResults.some(result => 
                    result.row === rowIndex && result.col === colIndex
                  );
                  return (
                    <td
                      key={colIndex}
                      className={`px-2 py-1 border-r text-sm ${
                        isSearchMatch ? 'bg-yellow-200' : 'hover:bg-gray-50'
                      }`}
                      style={{ minWidth: '100px' }}
                    >
                      {String(cell || '')}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
        
        {/* Load more button for large datasets */}
        {visibleRows < sheetData.length && (
          <div className="p-4 text-center border-t">
            <button
              onClick={loadMoreRows}
              disabled={isLoadingMore}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoadingMore ? (
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Loading...</span>
                </div>
              ) : (
                `Load More (${visibleRows} of ${sheetData.length} rows)`
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

const PptRenderer: React.FC<{ url: string }> = ({ url }) => {
  const [slides, setSlides] = useState<Array<{title: string, content: string, image?: string}>>([]);
  const [currentSlide, setCurrentSlide] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Array<{slide: number, content: string}>>([]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const headers: Record<string, string> = {};
        const token = localStorage.getItem(process.env.REACT_APP_JWT_STORAGE_KEY || 'onlab_token');
        if (token) headers.Authorization = `Bearer ${token}`;
        
        const res = await fetch(url, { headers });
        if (!res.ok) {
          throw new Error(`Failed to fetch PowerPoint file: ${res.status} ${res.statusText}`);
        }

        // For now, we'll provide a fallback viewer with download option
        // In a production environment, you might want to convert PPT to PDF or images server-side
        if (!cancelled) {
          setError('PowerPoint files require conversion for web viewing. Please use the download option below to view the file locally.');
          setLoading(false);
        }
      } catch (e: any) {
        if (!cancelled) {
          setError(e?.message || 'Failed to load PowerPoint file');
          setLoading(false);
        }
      }
    })();
    return () => { cancelled = true; };
  }, [url]);

  const downloadPpt = async () => {
    try {
      const headers: Record<string, string> = {};
      const token = localStorage.getItem(process.env.REACT_APP_JWT_STORAGE_KEY || 'onlab_token');
      if (token) headers.Authorization = `Bearer ${token}`;
      
      const res = await fetch(url, { headers });
      const blob = await res.blob();
      const filename = url.split('/').pop() || 'presentation.pptx';
      saveAs(blob, filename);
    } catch (e: any) {
      console.error('Download failed:', e);
    }
  };

  if (loading) return <div className="p-6 text-gray-600 flex items-center space-x-2">
    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
    <span>Loading PowerPoint file...</span>
  </div>;

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-4 border-b bg-gray-50">
        <div className="flex items-center space-x-4">
          <FileText size={20} className="text-gray-600" />
          <span className="text-sm font-medium text-gray-700">PowerPoint Presentation</span>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={downloadPpt}
            className="flex items-center space-x-1 px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            <Download size={16} />
            <span>Download to View</span>
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="mb-4">
            <FileText size={64} className="text-gray-400 mx-auto mb-4" />
          </div>
          {error && (
            <div className="mb-4">
              <p className="text-red-600 mb-2">{error}</p>
              <p className="text-sm text-gray-600">
                PowerPoint files cannot be displayed directly in the browser. 
                Please download the file to view it with Microsoft PowerPoint, 
                LibreOffice Impress, or Google Slides.
              </p>
            </div>
          )}
          <div className="space-y-2">
            <p className="text-sm text-gray-600">
              Supported viewers:
            </p>
            <ul className="text-xs text-gray-500 space-y-1">
              <li>• Microsoft PowerPoint</li>
              <li>• LibreOffice Impress</li>
              <li>• Google Slides (upload required)</li>
              <li>• Apple Keynote</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentViewer;
