import React, { useEffect, useMemo, useRef, useState } from 'react';
import { getDocument, GlobalWorkerOptions } from 'pdfjs-dist';
import * as XLSX from 'xlsx';
import { saveAs } from 'file-saver';
import { useTranslation } from 'react-i18next';
import { Download, FileText, FileSearch, ZoomIn, ZoomOut, RotateCcw, PanelRightClose, PanelRightOpen } from 'lucide-react';

// Configure PDF.js worker - use dynamic path based on current origin
// This ensures it works in both development (localhost) and production (anylab.dpdns.org)
if (typeof window !== 'undefined') {
  // Use relative path from current origin to avoid CORS issues
  const workerPath = `${window.location.origin}/pdf.worker.min.mjs`;
  GlobalWorkerOptions.workerSrc = workerPath;
}

type DocType = 'pdf' | 'docx' | 'txt' | 'xls' | 'xlsx' | 'ppt' | 'pptx' | 'html';

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
  const { t } = useTranslation('ai');
  const containerRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [authError, setAuthError] = useState(false);
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
  const [searchPanelWidth, setSearchPanelWidth] = useState(320); // Default 320px (w-80)
  const [showSearchPanel, setShowSearchPanel] = useState(true);
  const [isResizing, setIsResizing] = useState(false);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [pageInputValue, setPageInputValue] = useState<string>('');
  const [showPageInput, setShowPageInput] = useState(false);

  // Render PDF pages with performance optimizations
  useEffect(() => {
    if (docType !== 'pdf') {
      setLoading(false);
      return;
    }
    let cancelled = false;
    let abortController: AbortController | null = null;
    
    // Cleanup function for memory management
    const cleanup = () => {
      // Cancel fetch if in progress
      if (abortController) {
        abortController.abort();
      }
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
    
    // Render a single page asynchronously
    const renderPage = async (pdf: any, pageNum: number, optimalScale: number): Promise<void> => {
      if (cancelled) return;
      
      const page = await pdf.getPage(pageNum);
      if (cancelled) return;
      
      const viewport = page.getViewport({ scale: optimalScale });

      // Create wrapper per page
      let wrapper = containerRef.current?.querySelector<HTMLDivElement>(`[data-page='${pageNum}']`);
      if (!wrapper) {
        wrapper = document.createElement('div');
        wrapper.setAttribute('data-page', String(pageNum));
        wrapper.style.position = 'relative';
        wrapper.style.display = 'flex';
        wrapper.style.justifyContent = 'center';
        wrapper.style.marginBottom = '20px';
        wrapper.className = 'relative flex justify-center mb-5';
        containerRef.current?.appendChild(wrapper);
      }

      // Canvas
      let canvas = pageRefs.current[pageNum];
      if (!canvas) {
        canvas = document.createElement('canvas');
        pageRefs.current[pageNum] = canvas;
      }
      if (wrapper && canvas.parentElement !== wrapper) wrapper.appendChild(canvas);

      const context = canvas.getContext('2d');
      if (!context) return;
      
      canvas.width = viewport.width;
      canvas.height = viewport.height;
      canvas.style.maxWidth = '100%';
      canvas.style.height = 'auto';
      context.save();
      context.fillStyle = '#ffffff';
      context.fillRect(0, 0, canvas.width, canvas.height);
      context.restore();
      
      await page.render({ canvasContext: context as any, viewport } as any).promise;
      if (cancelled) return;

      // Overlay for highlights
      let overlay = overlayRefs.current[pageNum];
      if (!overlay) {
        overlay = document.createElement('div');
        overlayRefs.current[pageNum] = overlay;
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

      // Debug mode text extraction (only if enabled)
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
    };
    
    const run = async () => {
      try {
        setError(null);
        setLoading(true);
        
        // Convert relative URL to absolute URL if needed
        // Use the same port detection logic as api.ts to ensure consistency
        let absoluteUrl = url;
        if (url.startsWith('/')) {
          const hostname = window.location.hostname;
          const protocol = window.location.protocol;
          const port = '8000';  // Backend port (Docker exposes on 8000)
          
          // Helper function to check if hostname is an IP address
          const isIPAddress = (host: string): boolean => {
            const ipv4Pattern = /^(\d{1,3}\.){3}\d{1,3}$/;
            const ipv6Pattern = /^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$/;
            return ipv4Pattern.test(host) || ipv6Pattern.test(host);
          };
          
          if (hostname === 'localhost' || hostname === '127.0.0.1') {
            absoluteUrl = `${protocol}//localhost:${port}${url}`;
          } else if (!isIPAddress(hostname)) {
            // Domain name detected - use same domain (Nginx reverse proxy will route to backend)
            absoluteUrl = `${protocol}//${hostname}${url}`;
          } else {
            // IP address - use same hostname with port
            absoluteUrl = `${protocol}//${hostname}:${port}${url}`;
          }
        }
        
        // Prepare headers with authentication
        const headers: Record<string, string> = {};
        const token = localStorage.getItem('anylab_token');
        
        if (token && token.length > 0) {
          headers['Authorization'] = `Bearer ${token}`;
        } else {
          console.error('PDF Viewer - No authentication token found');
        }
        
        // Create AbortController for request cancellation
        abortController = new AbortController();
        
        const res = await fetch(absoluteUrl, { 
          headers,
          signal: abortController.signal
        });
        
        const contentType = res.headers.get('content-type') || '';
        
        // Check if response is OK
        if (!res.ok) {
          if (res.status === 401) {
            setAuthError(true);
            throw new Error('Authentication failed. Please log in again.');
          }
          const clonedRes = res.clone();
          const errorContentType = clonedRes.headers.get('content-type');
          if (errorContentType && errorContentType.includes('application/json')) {
            const errorData = await clonedRes.json();
throw new Error(errorData.error || errorData.message || errorData.detail || `HTTP ${res.status}: ${res.statusText}`);
          } else {
            const text = await clonedRes.text();
            throw new Error(`HTTP ${res.status}: ${res.statusText}. ${text.substring(0, 200)}`);
          }
        }
        
// Check content type
        if (!contentType.includes('application/pdf') && !contentType.includes('application/octet-stream')) {
          const clonedRes = res.clone();
          const text = await clonedRes.text();
          try {
            const errorData = JSON.parse(text);
            throw new Error(errorData.error || errorData.message || 'Server returned non-PDF content');
          } catch {
            throw new Error(`Expected PDF but received ${contentType}. Response: ${text.substring(0, 200)}`);
          }
        }
        
        const buf = await res.arrayBuffer();
        if (cancelled) return;
        
// Quick PDF header validation
        const uint8Array = new Uint8Array(buf);
        const headerBytes = Array.from(uint8Array.slice(0, 4));
        const pdfHeader = String.fromCharCode(...headerBytes);
        
        if (pdfHeader !== '%PDF') {
          throw new Error(`Invalid PDF structure: File does not start with PDF header. Found: "${pdfHeader}"`);
        }

        if (containerRef.current) containerRef.current.innerHTML = '';

// Load PDF document
        const pdf = await getDocument({ data: buf }).promise;
        console.log('PDF Viewer - PDF loaded successfully. Pages:', pdf.numPages);
        if (cancelled) return;
        
        setNumPages(pdf.numPages);

        // Calculate optimal scale based on container width
        const containerWidth = containerRef.current?.clientWidth || 800;
        const firstPage = await pdf.getPage(1);
        if (cancelled) return;
        
        const originalViewport = firstPage.getViewport({ scale: 1.0 });
        const optimalScale = calculateScale(containerWidth, originalViewport.width);
        setScale(optimalScale);

        setLoadingProgress({ current: 0, total: pdf.numPages });
        
        // PROGRESSIVE RENDERING: Render first page immediately, then others asynchronously
        // This shows content to user much faster
        await renderPage(pdf, 1, optimalScale);
        if (cancelled) return;
        
        // Update progress after first page (user sees content immediately)
        setLoadingProgress({ current: 1, total: pdf.numPages });
        
        // Render remaining pages asynchronously in batches
        const batchSize = 3; // Render 3 pages at a time
        const totalPages = pdf.numPages;
        
        for (let startPage = 2; startPage <= totalPages; startPage += batchSize) {
          if (cancelled) return;
          
          // Render batch of pages in parallel
          const batchPromises: Promise<void>[] = [];
          const endPage = Math.min(startPage + batchSize - 1, totalPages);
          
          for (let p = startPage; p <= endPage; p++) {
            batchPromises.push(renderPage(pdf, p, optimalScale));
          }
          
          // Wait for batch to complete
          await Promise.all(batchPromises);
          if (cancelled) return;
          
          // Update progress (batched - only update every batchSize pages)
          setLoadingProgress({ current: endPage, total: totalPages });
          
          // Yield to browser to prevent blocking
          await new Promise(resolve => setTimeout(resolve, 0));
        }

        setLoading(false);
        setLoadingProgress({ current: 0, total: 0 });
        
        // Scroll to initial page if specified (scroll the container, not the page element)
        if (initialPage && pageRefs.current[initialPage] && scrollContainerRef.current) {
          const pageElement = pageRefs.current[initialPage];
          const container = scrollContainerRef.current;
          const pageTop = pageElement.offsetTop;
          container.scrollTo({ top: pageTop, behavior: 'smooth' });
          setCurrentPage(initialPage);
        }
        
        // Perform initial search if query provided
        if (initialQuery) {
          findInPdf(initialQuery).catch(() => {});
        }
      } catch (e: any) {
// Only log actual errors, not cancellation
        if (e?.name !== 'AbortError' && !cancelled) {
          console.error('PDF loading error:', e);
        }
        
        if (cancelled) return;
        let errorMessage = t('failedToLoadPdf');
        
        if (e?.message) {
          errorMessage = e.message;
        } else if (e?.name === 'InvalidPDFException') {
          errorMessage = 'Invalid PDF structure: The file may be corrupted or not a valid PDF.';
        } else if (e?.name === 'MissingPDFException') {
          errorMessage = 'PDF file not found or could not be loaded.';
        } else if (e?.name === 'UnexpectedResponseException') {
          errorMessage = 'Unexpected response from server. Please check if the file exists.';
        } else if (typeof e === 'string') {
          errorMessage = e;
        }
        
        setError(errorMessage);
        setLoading(false);
        setLoadingProgress({ current: 0, total: 0 });
      }
    };
    
    run();
    return () => { 
      cancelled = true; 
      cleanup();
    };
  }, [url, docType, initialPage, initialQuery, debugMode]);

  // Re-render highlights when scale changes
  useEffect(() => {
    if (searchQuery.trim() && docType === 'pdf') {
      findInPdf(searchQuery);
    }
  }, [currentScale, searchQuery, docType]);

  // Track current page based on scroll position
  useEffect(() => {
    if (docType !== 'pdf' || !scrollContainerRef.current || numPages === 0) return;

    const container = scrollContainerRef.current;
    
    const updateCurrentPage = () => {
      if (!container) return;
      
      const scrollTop = container.scrollTop;
      const containerHeight = container.clientHeight;
      const viewportCenter = scrollTop + containerHeight / 2;
      
      // Find which page is currently in the center of the viewport
      let currentPageNum = 1;
      for (let pageNum = 1; pageNum <= numPages; pageNum++) {
        const pageElement = pageRefs.current[pageNum];
        if (pageElement) {
          const pageTop = pageElement.offsetTop;
          const pageHeight = pageElement.offsetHeight;
          const pageBottom = pageTop + pageHeight;
          
          if (viewportCenter >= pageTop && viewportCenter <= pageBottom) {
            currentPageNum = pageNum;
            break;
          }
          // If we've scrolled past this page, update current page
          if (viewportCenter > pageTop) {
            currentPageNum = pageNum;
          }
        }
      }
      
      setCurrentPage(currentPageNum);
    };

    container.addEventListener('scroll', updateCurrentPage);
    // Also update on initial load and when pages are rendered
    updateCurrentPage();
    
    // Update when scale changes (pages might resize)
    const interval = setInterval(updateCurrentPage, 100);
    
    return () => {
      container.removeEventListener('scroll', updateCurrentPage);
      clearInterval(interval);
    };
  }, [docType, numPages, currentScale]);

  // Jump to specific page
  const goToPage = (pageNum: number) => {
    if (pageNum < 1 || pageNum > numPages || !scrollContainerRef.current) return;
    
    const pageElement = pageRefs.current[pageNum];
    if (pageElement) {
      const container = scrollContainerRef.current;
      const pageTop = pageElement.offsetTop;
      container.scrollTo({ top: pageTop, behavior: 'smooth' });
      setCurrentPage(pageNum);
    }
    setShowPageInput(false);
    setPageInputValue('');
  };

  // Handle page input submission
  const handlePageInputSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const pageNum = parseInt(pageInputValue);
    if (!isNaN(pageNum) && pageNum >= 1 && pageNum <= numPages) {
      goToPage(pageNum);
    } else {
      setPageInputValue('');
      setShowPageInput(false);
    }
  };

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
      const token = localStorage.getItem('anylab_token'); // Use hardcoded key for consistency
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
      const token = localStorage.getItem('anylab_token'); // Use hardcoded key for consistency
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
      
      // Auto-scroll to first result if found (scroll the container, not the page element)
      if (found.length > 0 && scrollContainerRef.current) {
        const firstPage = found[0].pageNumber;
        const pageElement = pageRefs.current[firstPage];
        if (pageElement) {
          const container = scrollContainerRef.current;
          const pageTop = pageElement.offsetTop;
          const containerHeight = container.clientHeight;
          container.scrollTo({ top: pageTop - (containerHeight / 2), behavior: 'smooth' });
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

  // Handle panel resize
  const handleMouseDown = React.useCallback((e: React.MouseEvent) => {
    setIsResizing(true);
    e.preventDefault();
  }, []);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;
      const newWidth = window.innerWidth - e.clientX;
      setSearchPanelWidth(Math.max(280, Math.min(600, newWidth))); // Min 280px, Max 600px
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing]);

  const rightPanel = useMemo(() => {
    if (!showSearchPanel) return null;
    
    return (
      <>
        {/* Resize Handle */}
        <div
          className={`w-1 bg-gray-200 hover:bg-primary-400 cursor-col-resize transition-colors ${
            isResizing ? 'bg-primary-500' : ''
          }`}
          onMouseDown={handleMouseDown}
          title="Drag to resize"
        />
        {/* Search Panel */}
        <div 
          className="border-l p-4 overflow-auto bg-white flex-shrink-0"
          style={{ width: `${searchPanelWidth}px` }}
        >

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
            placeholder={t('searchInDocument')}
            className="flex-1 px-3 py-2 border rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <button
            onClick={() => findInPdf(searchQuery)}
            className="px-3 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 focus:ring-2 focus:ring-primary-500"
          >
            {t('search')}
          </button>
        </div>
        
        {/* Enhanced search navigation */}
        {totalMatches > 0 && (
          <div className="flex items-center justify-between mb-2 p-2 bg-primary-50 rounded border border-primary-200">
            <div className="text-sm text-primary-700">
              {t('matchOf', { current: currentMatchIndex + 1, total: totalMatches })}
            </div>
            <div className="flex space-x-1">
              <button
                onClick={() => navigateToMatch('prev')}
                disabled={totalMatches <= 1}
                className="px-2 py-1 text-xs bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                ← {t('prev')}
              </button>
              <button
                onClick={() => navigateToMatch('next')}
                disabled={totalMatches <= 1}
                className="px-2 py-1 text-xs bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {t('next')} →
              </button>
            </div>
          </div>
        )}
        {debugMode && (
          <div className="text-xs text-red-600 mb-2 p-2 bg-red-50 border border-red-200 rounded">
            🔍 {t('debugModeRedBoxes')}
          </div>
        )}
        {searchQuery.trim() && (
          <div className="text-xs text-gray-600 mb-2 flex items-center space-x-2">
            <span>{t('searchingFor', { query: searchQuery })}</span>
            {searching && (
              <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-primary-500"></div>
            )}
          </div>
        )}
      </div>
      {docType === 'pdf' && (
        <div className="space-y-2">
          {searching ? (
            <div className="text-sm text-gray-500 flex items-center space-x-2">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-500"></div>
              <span>{t('searching')}</span>
            </div>
          ) : hits.length === 0 ? (
            searchQuery.trim() ? (
              <p className="text-sm text-gray-500">{t('noResultsFoundFor', { query: searchQuery })}</p>
            ) : (
              <p className="text-sm text-gray-500">{t('enterSearchTerm')}</p>
            )
          ) : (
            <>
              <div className="text-sm font-medium text-gray-700 mb-2">
                {t('foundResultsFor', { count: hits.length, query: searchQuery })}
              </div>
              {hits.map((h, i) => (
                <button
                  key={`${h.pageNumber}-${i}`}
                  onClick={() => {
                    const pageElement = pageRefs.current[h.pageNumber];
                    if (pageElement && scrollContainerRef.current) {
                      const container = scrollContainerRef.current;
                      const pageTop = pageElement.offsetTop;
                      const containerHeight = container.clientHeight;
                      container.scrollTo({ top: pageTop - (containerHeight / 2), behavior: 'smooth' });
                    }
                  }}
                  className="block text-left w-full p-3 border rounded hover:bg-primary-50 hover:border-primary-200 transition-colors"
                >
                  <div className="text-xs text-primary-600 font-medium mb-1">{t('page')} {h.pageNumber}</div>
                  <div className="text-sm text-gray-700 leading-relaxed">{h.snippet}</div>
                </button>
              ))}
            </>
          )}
        </div>
      )}
        </div>
      </>
    );
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hits, searchQuery, docType, showSearchPanel, searchPanelWidth, isResizing, searching, totalMatches, currentMatchIndex, debugMode, t]);

  return (
    <>
      <style>{`
        .pdf-scroll-container::-webkit-scrollbar {
          width: 12px;
        }
        .pdf-scroll-container::-webkit-scrollbar-track {
          background: #f7fafc;
        }
        .pdf-scroll-container::-webkit-scrollbar-thumb {
          background: #cbd5e0;
          border-radius: 6px;
        }
        .pdf-scroll-container::-webkit-scrollbar-thumb:hover {
          background: #a0aec0;
        }
      `}</style>
      <div className="flex h-full border rounded overflow-hidden">
        <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
        {/* Title only shown for non-PDF documents - PDFs have toolbar instead */}
        {(!error && docType !== 'pdf') && (
          <div className="px-4 py-2 border-b font-semibold flex-shrink-0">{title}</div>
        )}
        {loading && (
          <div className="p-6 text-gray-600">
            <div className="flex items-center space-x-2 mb-4">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-500"></div>
              <span>{t('loadingDocument')}</span>
            </div>
            {loadingProgress.total > 0 && (
              <>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${(loadingProgress.current / loadingProgress.total) * 100}%` }}
                  ></div>
                </div>
                <div className="text-sm text-gray-500 mt-2">
                  {t('page')} {loadingProgress.current} {t('of')} {loadingProgress.total}
                </div>
              </>
            )}
          </div>
        )}
        {error && (
          <div className="p-6">
            {authError ? (
              <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-yellow-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-yellow-800">{t('authenticationRequired')}</h3>
                    <div className="mt-2 text-sm text-yellow-700">
                      <p>{error}</p>
                      <p className="mt-2">{t('pleaseRefreshAndLogin')}</p>
                    </div>
                    <div className="mt-4">
                      <button
                        onClick={() => {
                          // Clear token and redirect to login
                          localStorage.removeItem('anylab_token');
                          localStorage.removeItem('anylab_refresh_token');
                          window.location.href = '/login';
                        }}
                        className="bg-yellow-600 hover:bg-yellow-700 text-white font-medium py-2 px-4 rounded"
                      >
                        {t('goToLogin')}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-red-600">{error}</div>
            )}
          </div>
        )}
        {!error && docType === 'pdf' && (
          <div className="flex-1 flex flex-col min-h-0 relative">
            {/* Floating Toolbar - Absolutely positioned at bottom, always visible */}
            <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 bg-white rounded-lg shadow-lg border border-gray-200 z-[9999] px-3 py-2">
              <div className="flex items-center space-x-1 sm:space-x-2">
                <button
                  onClick={() => setCurrentScale(Math.max(0.5, currentScale - 0.1))}
                  className="px-2 sm:px-3 py-1.5 text-sm bg-white border border-gray-300 rounded hover:bg-gray-50 transition-colors flex-shrink-0"
                  title="Zoom Out"
                >
                  −
                </button>
                <span className="text-sm font-medium min-w-[50px] sm:min-w-[60px] text-center text-gray-700 flex-shrink-0">
                  {Math.round(currentScale * 100)}%
                </span>
                <button
                  onClick={() => setCurrentScale(Math.min(2.0, currentScale + 0.1))}
                  className="px-2 sm:px-3 py-1.5 text-sm bg-white border border-gray-300 rounded hover:bg-gray-50 transition-colors flex-shrink-0"
                  title="Zoom In"
                >
                  +
                </button>
                <button
                  onClick={() => setCurrentScale(1.0)}
                  className="px-2 sm:px-3 py-1.5 text-sm bg-white border border-gray-300 rounded hover:bg-gray-50 transition-colors flex-shrink-0"
                  title="Reset to 100%"
                >
                  <RotateCcw className="h-4 w-4" />
                </button>
                <button
                  onClick={() => setCurrentScale(scale)}
                  className="px-2 sm:px-3 py-1.5 text-sm bg-primary-600 text-white border border-primary-600 rounded hover:bg-primary-700 transition-colors flex-shrink-0 whitespace-nowrap"
                  title="Fit to Width"
                >
                  <span className="hidden sm:inline">{t('fit')}</span>
                  <span className="sm:hidden">Fit</span>
                </button>
                <div className="h-6 w-px bg-gray-300 mx-1 sm:mx-2 flex-shrink-0"></div>
                <button
                  onClick={() => setShowSearchPanel(!showSearchPanel)}
                  className="px-2 sm:px-3 py-1.5 text-sm bg-white border border-gray-300 rounded hover:bg-gray-50 transition-colors flex items-center space-x-1 flex-shrink-0"
                  title={showSearchPanel ? "Hide Search Panel" : "Show Search Panel"}
                >
                  {showSearchPanel ? <PanelRightClose className="h-4 w-4" /> : <PanelRightOpen className="h-4 w-4" />}
                  <span className="hidden lg:inline ml-1">{showSearchPanel ? t('hideSearch') : t('showSearch')}</span>
                </button>
                {numPages > 0 && (
                  <div className="flex items-center space-x-1 sm:space-x-2 flex-shrink-0 ml-2">
                    {showPageInput ? (
                      <form onSubmit={handlePageInputSubmit} className="flex items-center space-x-1">
                        <input
                          type="number"
                          min="1"
                          max={numPages}
                          value={pageInputValue}
                          onChange={(e) => setPageInputValue(e.target.value)}
                          onBlur={() => {
                            if (!pageInputValue) setShowPageInput(false);
                          }}
                          autoFocus
                          className="w-12 sm:w-16 px-2 py-1 text-xs sm:text-sm border border-gray-300 rounded text-center focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                          placeholder={currentPage.toString()}
                        />
                        <span className="text-xs sm:text-sm text-gray-600">/ {numPages}</span>
                        <button
                          type="submit"
                          className="px-2 py-1 text-xs sm:text-sm bg-primary-600 text-white rounded hover:bg-primary-700"
                          title="Go to page"
                        >
                          Go
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            setShowPageInput(false);
                            setPageInputValue('');
                          }}
                          className="px-2 py-1 text-xs sm:text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
                          title="Cancel"
                        >
                          ×
                        </button>
                      </form>
                    ) : (
                      <button
                        onClick={() => {
                          setShowPageInput(true);
                          setPageInputValue(currentPage.toString());
                        }}
                        className="px-2 sm:px-3 py-1.5 text-xs sm:text-sm bg-white border border-gray-300 rounded hover:bg-gray-50 transition-colors flex items-center space-x-1"
                        title="Click to jump to a page"
                      >
                        <FileText className="h-3 w-3 sm:h-4 sm:w-4" />
                        <span className="text-gray-700">
                          {t('page')} {currentPage} / {numPages}
                        </span>
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>
            {/* PDF Content Area - Scrollable (no padding needed since toolbar is floating) */}
            <div 
              ref={scrollContainerRef} 
              className="flex-1 overflow-y-auto overflow-x-hidden bg-gray-100 relative min-h-0 pdf-scroll-container"
              style={{ 
                scrollbarWidth: 'thin', // Firefox
                scrollbarColor: '#cbd5e0 #f7fafc' // Firefox: thumb track
              }}
            >
              <div 
                ref={containerRef} 
                className="p-4 w-full origin-top-center" 
                style={{ 
                  transform: `scale(${currentScale})`, 
                  transformOrigin: 'top center',
                  minHeight: '100%'
                }} 
              />
            </div>
          </div>
        )}
        {!error && docType === 'docx' && (
          <DocxRenderer url={url} />
        )}
        {!error && docType === 'txt' && (
          <TxtRenderer url={url} />
        )}
        {!error && docType === 'html' && (
          <HtmlRenderer url={url} />
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
    </>
  );
};

const DocxRenderer: React.FC<{ url: string }> = ({ url }) => {
  const { t } = useTranslation('ai');
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
        const token = localStorage.getItem('anylab_token'); // Use hardcoded key for consistency
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
          setError(e?.message || t('failedToLoadDocx'));
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
      const token = localStorage.getItem('anylab_token'); // Use hardcoded key for consistency
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
    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-500"></div>
    <span>{t('loadingWordDocument')}</span>
  </div>;

  if (error) return <div className="p-6 text-red-600">{error}</div>;

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-4 border-b bg-gray-50">
        <div className="flex items-center space-x-4">
          <FileText size={20} className="text-gray-600" />
          <span className="text-sm font-medium text-gray-700">{t('wordDocument')}</span>
        </div>
        
        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-2">
            <FileSearch size={16} className="text-gray-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                searchInDocument(e.target.value);
              }}
              placeholder={t('searchInDocument')}
              className="px-3 py-1 text-sm border rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            {searchResults > 0 && (
              <span className="text-sm text-primary-600">{searchResults} {t('matches')}</span>
            )}
          </div>
          <button
            onClick={downloadDocx}
            className="flex items-center space-x-1 px-3 py-1 text-sm bg-green-500 text-white rounded hover:bg-green-600"
          >
            <Download size={16} />
            <span>{t('download')}</span>
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
  const { t } = useTranslation('ai');
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
        const token = localStorage.getItem('anylab_token'); // Use hardcoded key for consistency
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
          setError(e?.message || t('failedToLoadTextFile'));
          setLoading(false);
        }
      }
    })();
    return () => { cancelled = true; };
  }, [url]);

  // Update search results count when search query or text changes
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults(0);
      return;
    }

    try {
      const regex = new RegExp(`(${searchQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
      const matches = text.match(regex);
      setSearchResults(matches ? matches.length : 0);
    } catch (e) {
      setSearchResults(0);
    }
  }, [searchQuery, text]);

  const getHighlightedText = (text: string, query: string) => {
    if (!query.trim()) {
      return text;
    }

    try {
      const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
      return text.split(regex).map((part, index) => {
        if (part.toLowerCase() === query.toLowerCase()) {
          return `<mark class="bg-yellow-300 px-1 rounded">${part}</mark>`;
        }
        return part;
      }).join('');
    } catch (e) {
      return text;
    }
  };

  const downloadTxt = async () => {
    try {
      const headers: Record<string, string> = {};
      const token = localStorage.getItem('anylab_token'); // Use hardcoded key for consistency
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
    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-500"></div>
    <span>{t('loadingTextFile')}</span>
  </div>;

  if (error) return <div className="p-6 text-red-600">{error}</div>;

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-4 border-b bg-gray-50">
        <div className="flex items-center space-x-4">
          <FileText size={20} className="text-gray-600" />
          <span className="text-sm font-medium text-gray-700">{t('textDocument')}</span>
        </div>
        
        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-2">
            <FileSearch size={16} className="text-gray-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={t('searchInText')}
              className="px-3 py-1 text-sm border rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            {searchResults > 0 && (
              <span className="text-sm text-blue-600">{searchResults} {t('matches')}</span>
            )}
          </div>
          <button
            onClick={downloadTxt}
            className="flex items-center space-x-1 px-3 py-1 text-sm bg-green-500 text-white rounded hover:bg-green-600"
          >
            <Download size={16} />
            <span>{t('download')}</span>
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

const HtmlRenderer: React.FC<{ url: string }> = ({ url }) => {
  const { t } = useTranslation('ai');
  const [error, setError] = useState<string | null>(null);

  const handleIframeError = () => {
    setError(t('failedToLoadHtmlContent'));
  };

  const downloadHtml = async () => {
    try {
      const headers: Record<string, string> = {};
      const token = localStorage.getItem('anylab_token'); // Use hardcoded key for consistency
      if (token) headers.Authorization = `Bearer ${token}`;
      
      const res = await fetch(url, { headers });
      const blob = await res.blob();
      const filename = url.split('/').pop() || 'document.html';
      saveAs(blob, filename);
    } catch (e: any) {
      console.error('Download failed:', e);
    }
  };

  if (error) {
    return (
      <div className="p-6 text-red-600">
        <p>{error}</p>
        <button
          onClick={() => setError(null)}
          className="mt-2 px-4 py-2 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          {t('retry')}
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-4 border-b bg-gray-50">
        <div className="flex items-center space-x-4">
          <FileText size={20} className="text-gray-600" />
          <span className="text-sm font-medium text-gray-700">{t('htmlDocument')}</span>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={downloadHtml}
            className="flex items-center space-x-1 px-3 py-1 text-sm bg-green-500 text-white rounded hover:bg-green-600"
          >
            <Download size={16} />
            <span>{t('download')}</span>
          </button>
        </div>
      </div>

      {/* HTML content in iframe */}
      <div className="flex-1 overflow-hidden">
        <iframe
          src={url}
          className="w-full h-full border-0"
          sandbox="allow-same-origin allow-scripts allow-popups allow-forms"
          title="HTML Document"
          onError={handleIframeError}
          onLoad={() => setError(null)}
        />
      </div>
    </div>
  );
};

const XlsRenderer: React.FC<{ url: string }> = ({ url }) => {
  const { t } = useTranslation('ai');
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
        const token = localStorage.getItem('anylab_token'); // Use hardcoded key for consistency
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
          setError(e?.message || t('failedToLoadExcelFile'));
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
    <span>{t('loadingExcelFile')}</span>
  </div>;
  
  if (error) return <div className="p-6 text-red-600">{error}</div>;

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-4 border-b bg-gray-50">
        <div className="flex items-center space-x-4">
          {/* Sheet tabs */}
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-700">{t('sheets')}:</span>
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
            <FileSearch size={16} className="text-gray-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                searchInSheet(e.target.value);
              }}
              placeholder={t('searchInSheet')}
              className="px-3 py-1 text-sm border rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            {searchResults.length > 0 && (
              <span className="text-sm text-primary-600">{searchResults.length} {t('matches')}</span>
            )}
          </div>
          <button
            onClick={downloadExcel}
            className="flex items-center space-x-1 px-3 py-1 text-sm bg-green-500 text-white rounded hover:bg-green-600"
          >
            <Download size={16} />
            <span>{t('download')}</span>
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
              className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoadingMore ? (
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>{t('loading')}</span>
                </div>
              ) : (
                t('loadMoreRows', { visible: visibleRows, total: sheetData.length })
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

const PptRenderer: React.FC<{ url: string }> = ({ url }) => {
  const { t } = useTranslation('ai');
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
        const token = localStorage.getItem('anylab_token'); // Use hardcoded key for consistency
        if (token) headers.Authorization = `Bearer ${token}`;
        
        const res = await fetch(url, { headers });
        if (!res.ok) {
          throw new Error(`Failed to fetch PowerPoint file: ${res.status} ${res.statusText}`);
        }

        // For now, we'll provide a fallback viewer with download option
        // In a production environment, you might want to convert PPT to PDF or images server-side
        if (!cancelled) {
          setError(t('powerpointRequiresConversion'));
          setLoading(false);
        }
      } catch (e: any) {
        if (!cancelled) {
          setError(e?.message || t('failedToLoadPowerPointFile'));
          setLoading(false);
        }
      }
    })();
    return () => { cancelled = true; };
  }, [url]);

  const downloadPpt = async () => {
    try {
      const headers: Record<string, string> = {};
      const token = localStorage.getItem('anylab_token'); // Use hardcoded key for consistency
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
    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-500"></div>
    <span>{t('loadingPowerPointFile')}</span>
  </div>;

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-4 border-b bg-gray-50">
        <div className="flex items-center space-x-4">
          <FileText size={20} className="text-gray-600" />
          <span className="text-sm font-medium text-gray-700">{t('powerPointPresentation')}</span>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={downloadPpt}
            className="flex items-center space-x-1 px-3 py-1 text-sm bg-primary-600 text-white rounded hover:bg-primary-700"
          >
            <Download size={16} />
            <span>{t('downloadToView')}</span>
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
                {t('powerPointCannotBeDisplayed')}
              </p>
            </div>
          )}
          <div className="space-y-2">
            <p className="text-sm text-gray-600">
              {t('supportedViewers')}:
            </p>
            <ul className="text-xs text-gray-500 space-y-1">
              <li>• {t('microsoftPowerPoint')}</li>
              <li>• {t('libreOfficeImpress')}</li>
              <li>• {t('googleSlidesUploadRequired')}</li>
              <li>• {t('appleKeynote')}</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentViewer;
