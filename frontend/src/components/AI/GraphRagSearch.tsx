import React, { useState, useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { 
  Send, 
  Clock, 
  FileText, 
  Copy, 
  Check, 
  Loader2,
  History,
  X,
  Zap,
  Target,
  Network,
  Tag,
  Sparkles,
  BarChart3,
  ChevronDown,
  ChevronUp,
  GitBranch,
  Maximize2,
  AlertTriangle,
  ExternalLink
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { apiClient } from '../../services/api';
import { useUnifiedChatHistory } from '../../hooks/useUnifiedChatHistory';
import DocumentViewer from './DocumentViewer';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  references?: Array<{
    title: string;
    content: string;
    page?: number;
    score?: number;
    source?: 'vector+graph' | 'vector' | 'graph';
    graph_boost?: boolean;
    matched_entities?: Array<{ name: string; type: string }>;
    view_url?: string;
  }>;
}

interface GraphStats {
  total_results: number;
  graph_enhanced: number;
  vector_only: number;
  query_entities: Array<{ name: string; type: string; normalized?: string }>;
  semantic_entity_matches?: number;
  exact_entity_matches?: number;
}

interface EntityMatches {
  exact_entities: Array<{ name: string; type: string }>;
  semantic_entities: Array<{ name: string; type: string; similarity: number }>;
  total_exact: number;
  total_semantic: number;
}

const GraphRagSearch: React.FC = () => {
  const { t } = useTranslation('ai');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showHistory, setShowHistory] = useState(true);
  const [showGraphStats, setShowGraphStats] = useState(false);
  
  // Document viewer state for split-screen
  const [viewerDocument, setViewerDocument] = useState<{
    fileId: string;
    title: string;
    url: string;
    type: 'pdf'|'docx'|'txt'|'xls'|'xlsx'|'ppt'|'pptx'|'html';
    page?: number;
  } | null>(null);
  const [isLoadingDocument, setIsLoadingDocument] = useState(false);
  const [showEntities, setShowEntities] = useState(false);
  const { history: unifiedHistory, recordUserPrompt, refresh: refreshUnifiedHistory } = useUnifiedChatHistory(200);
  const [chatHistory, setChatHistory] = useState<Array<{ 
    id: string; 
    prompt: string; 
    preview: string; 
    timestamp: string;
    response?: string;
    sources?: Array<{ title: string; content: string; page?: number; score?: number; view_url?: string }>;
  }>>([]);
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const [graphStats, setGraphStats] = useState<GraphStats | null>(null);
  const [entityMatches, setEntityMatches] = useState<EntityMatches | null>(null);
  const [performanceStats, setPerformanceStats] = useState<any>(null);
  const [currentQuery, setCurrentQuery] = useState<string>('');
  const [showGraphModal, setShowGraphModal] = useState(false);
  const [graphData, setGraphData] = useState<any>(null);
  const [loadingGraph, setLoadingGraph] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const graphSvgRef = useRef<SVGSVGElement>(null);
  
  // Storage keys
  const GRAPH_HISTORY_STORAGE_KEY = 'anylab_graph_rag_history';
  const GRAPH_MESSAGES_STORAGE_KEY = 'anylab_graph_rag_messages';

  // Load history and messages on component mount
  useEffect(() => {
    try {
      console.log('Loading Graph RAG history from localStorage...');
      
      const graphHistoryRaw = localStorage.getItem(GRAPH_HISTORY_STORAGE_KEY);
      if (graphHistoryRaw) {
        const parsed = JSON.parse(graphHistoryRaw);
        if (Array.isArray(parsed)) {
          setChatHistory(parsed);
        }
      }

      const graphMessagesRaw = localStorage.getItem(GRAPH_MESSAGES_STORAGE_KEY);
      if (graphMessagesRaw) {
        const parsed = JSON.parse(graphMessagesRaw);
        if (Array.isArray(parsed)) {
          setMessages(parsed);
        }
      }
    } catch (error) {
      console.error('Error loading Graph RAG history:', error);
    }
  }, []);

  // Save history and messages
  useEffect(() => {
    localStorage.setItem(GRAPH_HISTORY_STORAGE_KEY, JSON.stringify(chatHistory));
  }, [chatHistory]);

  useEffect(() => {
    localStorage.setItem(GRAPH_MESSAGES_STORAGE_KEY, JSON.stringify(messages));
  }, [messages]);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Cross-post receiver
  useEffect(() => {
    try {
      const raw = localStorage.getItem('anylab_cross_post');
      if (raw) {
        const payload = JSON.parse(raw);
        if (payload?.channel === 'rag_graph' && typeof payload?.content === 'string') {
          localStorage.removeItem('anylab_cross_post');
          setInputMessage(payload.content);
          setTimeout(() => handleGraphSearch(), 0);
        }
      }
    } catch (_) {}
  }, []);

  // D3 Force-Directed Graph Rendering
  useEffect(() => {
    if (!graphData || !graphSvgRef.current) return;
    
    // Validate graph data structure
    if (!graphData.nodes || !Array.isArray(graphData.nodes) || graphData.nodes.length === 0) {
      console.warn('Invalid or empty graph nodes data:', graphData);
      return;
    }
    
    if (!graphData.edges || !Array.isArray(graphData.edges)) {
      console.warn('Invalid graph edges data:', graphData);
      return;
    }

    const svg = d3.select(graphSvgRef.current);
    svg.selectAll('*').remove(); // Clear previous graph

    const width = graphSvgRef.current.clientWidth;
    const height = 600;

    // Create color scales for different node types
    const nodeColors: { [key: string]: string } = {
      'query_entity': '#10b981', // green
      'related_entity': '#14b8a6', // teal
      'document': '#3b82f6' // blue
    };

    // Prepare graph data - ensure all nodes have valid IDs
    const nodes = graphData.nodes
      .filter((d: any) => d && d.id !== undefined && d.id !== null)
      .map((d: any) => ({ ...d }));
    
    if (nodes.length === 0) {
      console.warn('No valid nodes with IDs found in graph data');
      return;
    }
    
    // Create a Set of valid node IDs for quick lookup
    const nodeIds = new Set(nodes.map((n: any) => n.id));
    
    // Filter links to only include those with valid source and target nodes
    const links = graphData.edges
      .filter((d: any) => {
        if (!d || d.source === undefined || d.target === undefined) {
          console.warn('Invalid link found:', d);
          return false;
        }
        if (!nodeIds.has(d.source) || !nodeIds.has(d.target)) {
          console.warn('Link references non-existent node:', d);
          return false;
        }
        return true;
      })
      .map((d: any) => ({
        source: d.source,
        target: d.target,
        type: d.type || 'related'
      }));

    // Create force simulation
    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id((d: any) => d.id).distance(120))
      .force('charge', d3.forceManyBody().strength(-400))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(50));

    // Create zoom behavior
    const zoom = d3.zoom()
      .scaleExtent([0.5, 3])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoom as any);

    // Create main group for zooming/panning
    const g = svg.append('g');

    // Create arrow markers for edges
    svg.append('defs').selectAll('marker')
      .data(['end'])
      .enter().append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 25)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#94a3b8');

    // Create links
    const link = g.append('g')
      .selectAll('line')
      .data(links)
      .enter().append('line')
      .attr('stroke', '#94a3b8')
      .attr('stroke-width', 2)
      .attr('stroke-opacity', 0.6)
      .attr('marker-end', 'url(#arrowhead)');

    // Create link labels
    const linkLabel = g.append('g')
      .selectAll('text')
      .data(links)
      .enter().append('text')
      .attr('font-size', 10)
      .attr('fill', '#64748b')
      .attr('text-anchor', 'middle')
      .text((d: any) => d.type);

    // Create nodes
    const node = g.append('g')
      .selectAll('circle')
      .data(nodes)
      .enter().append('circle')
      .attr('r', (d: any) => {
        if (d.group === 'query_entity') return 20;
        if (d.type === 'document') return 15;
        return 12;
      })
      .attr('fill', (d: any) => {
        if (d.group === 'query_entity') return nodeColors['query_entity'];
        if (d.type === 'document') return nodeColors['document'];
        return nodeColors['related_entity'];
      })
      .attr('stroke', '#fff')
      .attr('stroke-width', 3)
      .style('cursor', 'pointer')
      .call(d3.drag<any, any>()
        .on('start', (event, d: any) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on('drag', (event, d: any) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on('end', (event, d: any) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        })
      );

    // Add node labels
    const nodeLabel = g.append('g')
      .selectAll('text')
      .data(nodes)
      .enter().append('text')
      .attr('font-size', 11)
      .attr('font-weight', (d: any) => d.group === 'query_entity' ? 'bold' : 'normal')
      .attr('fill', '#1f2937')
      .attr('text-anchor', 'middle')
      .attr('dy', 30)
      .style('pointer-events', 'none')
      .text((d: any) => d.label.length > 20 ? d.label.substring(0, 20) + '...' : d.label);

    // Add tooltips
    node.append('title')
      .text((d: any) => `${d.label}\nType: ${d.entityType || d.type || 'Unknown'}`);

    // Update positions on each tick
    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      linkLabel
        .attr('x', (d: any) => (d.source.x + d.target.x) / 2)
        .attr('y', (d: any) => (d.source.y + d.target.y) / 2);

      node
        .attr('cx', (d: any) => d.x)
        .attr('cy', (d: any) => d.y);

      nodeLabel
        .attr('x', (d: any) => d.x)
        .attr('y', (d: any) => d.y);
    });

    // Cleanup on unmount
    return () => {
      simulation.stop();
    };
  }, [graphData, showGraphModal]);

  const handleGraphSearch = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const currentQuery = inputMessage.trim();
    const messageId = Date.now().toString();
    
    const userMessage: ChatMessage = {
      id: messageId,
      role: 'user',
      content: currentQuery,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    try { await recordUserPrompt('rag_graph', currentQuery); } catch (e) { console.error('Failed to record unified history:', e); }

    const historyItem = {
      id: messageId,
      prompt: currentQuery,
      preview: currentQuery.substring(0, 50) + (currentQuery.length > 50 ? '...' : ''),
      timestamp: new Date().toISOString()
    };
    setChatHistory(prev => [historyItem, ...prev.slice(0, 9)]);

    try {
      const startTime = Date.now();
      
      const res = await apiClient.graphRagSearch(currentQuery, 10);
      
      const endTime = Date.now();
      const responseTime = endTime - startTime;

      // Store current query for graph visualization
      setCurrentQuery(currentQuery);

      // Set graph stats and show panel
      if (res.graph_stats) {
        setGraphStats(res.graph_stats);
        setShowGraphStats(true);
        if (res.graph_stats.query_entities.length > 0) {
          setShowEntities(true);
        }
      }
      
      // Set entity matches information
      if (res.entity_matches) {
        setEntityMatches(res.entity_matches);
      }

      setPerformanceStats({
        responseTime,
        searchResults: res.sources?.length || 0
      });

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: res.response || t('noResponseReceived'),
        timestamp: new Date().toISOString(),
        references: res.sources?.map((source: any) => ({
          title: source.title || source.filename || 'Unknown Document',
          content: source.content || '',
          page: source.page || source.page_number,
          score: source.similarity || source.final_rerank_score || source.score,
          source: source.source || 'vector',
          graph_boost: source.graph_boost || false,
          matched_entities: source.matched_entities || []
        })) || []
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      setChatHistory(prev => prev.map(item => 
        item.id === messageId 
          ? { ...item, response: res.response, sources: res.sources?.map((source: any) => ({
              title: source.title || source.filename || 'Unknown Document',
              content: source.content || '',
              page: source.page || source.page_number,
              score: source.similarity || source.score,
              view_url: source.view_url
            })) || [] }
          : item
      ));
    } catch (error) {
      console.error('Graph RAG search error:', error);
      
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: t('graphRagSearchFailed'),
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      refreshUnifiedHistory();
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleGraphSearch();
    }
  };

  const formatContentForDisplay = (text: string) => {
    let formatted = text
      .replace(/\*\*([^*]+)\*\*/g, '$1')
      .replace(/\*([^*\n]+?)\*/g, '$1')
      .replace(/`([^`]+)`/g, '$1')
      .replace(/^#{1,6}\s+(.+)$/gm, '$1')
      .replace(/^(\d+)\.\s+(.+)$/gm, '$1. $2')
      .replace(/^[-*•]\s+(.+)$/gm, '• $1')
      .replace(/[ \t]+/g, ' ')
      .replace(/\n{3,}/g, '\n\n');
    
    formatted = formatted.replace(/\n/g, '<br>');
    
    return formatted;
  };

  const copyToClipboard = async (text: string, messageId: string) => {
    try {
      const message = messages.find(m => m.id === messageId);
      
      let formattedText = text
        .replace(/\*\*([^*]+)\*\*/g, '$1')
        .replace(/\*([^*\n]+?)\*/g, '$1')
        .replace(/^#{1,6}\s+/gm, '')
        .replace(/`([^`]+)`/g, '$1')
        .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
        .replace(/\n{3,}/g, '\n\n')
        .replace(/[ \t]+/g, ' ')
        .trim();
      
      if (message?.references && message.references.length > 0) {
        formattedText += '\n\n--- REFERENCES ---\n';
        message.references.forEach((ref, index) => {
          formattedText += `\n${index + 1}. ${ref.title}`;
          if (ref.page) {
            formattedText += ` (Page ${ref.page})`;
          }
          formattedText += `\n   ${ref.content.substring(0, 200)}...`;
        });
      }
      
      await navigator.clipboard.writeText(formattedText);
      setCopiedMessageId(messageId);
      setTimeout(() => setCopiedMessageId(null), 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  const getSourceBadgeColor = (source?: string) => {
    if (source === 'vector+graph') {
      return 'bg-green-100 text-green-800 border-green-300';
    } else if (source === 'graph') {
      return 'bg-lime-100 text-lime-800 border-lime-300';
    }
    return 'bg-emerald-100 text-emerald-800 border-emerald-300';
  };

  const getEntityTypeColor = (type: string) => {
    const colors: { [key: string]: string } = {
      'PRODUCT': 'bg-primary-100 text-primary-800',
      'VERSION': 'bg-teal-100 text-teal-800',
      'ERROR_CODE': 'bg-red-100 text-red-800',
      'SOLUTION': 'bg-green-100 text-green-800',
      'PROBLEM': 'bg-orange-100 text-orange-800',
      'OS': 'bg-yellow-100 text-yellow-800',
      'DATABASE': 'bg-lime-100 text-lime-800',
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  const handleViewGraph = async () => {
    if (!currentQuery) return;
    
    setLoadingGraph(true);
    setShowGraphModal(true);
    
    try {
      const data = await apiClient.getGraphForQuery(currentQuery, 50, 2);
      
      // Validate the returned data structure
      if (!data || typeof data !== 'object') {
        console.error('Invalid graph data received:', data);
        setGraphData({ error: true, message: 'Invalid graph data structure' });
        return;
      }
      
      // Ensure data has required properties
      if (!data.nodes || !Array.isArray(data.nodes)) {
        console.error('Graph data missing nodes array:', data);
        data.nodes = [];
      }
      
      if (!data.edges || !Array.isArray(data.edges)) {
        console.error('Graph data missing edges array:', data);
        data.edges = [];
      }
      
      setGraphData(data);
    } catch (error) {
      console.error('Error loading graph:', error);
      setGraphData({ 
        error: true, 
        message: error instanceof Error ? error.message : 'Failed to load graph data',
        nodes: [],
        edges: []
      });
    } finally {
      setLoadingGraph(false);
    }
  };

  // Open document in right panel viewer
  const openDocumentInViewer = async (fileId: string, title: string, page: number) => {
    setIsLoadingDocument(true);
    try {
      const fileInfo = await apiClient.getFileProcessingStatus(parseInt(fileId));
      const filename = fileInfo.filename || title;
      const fileExt = filename.split('.').pop()?.toLowerCase() || 'pdf';
      
      let docType: 'pdf'|'docx'|'txt'|'xls'|'xlsx'|'ppt'|'pptx'|'html' = 'pdf';
      if (fileExt === 'doc' || fileExt === 'docx') docType = 'docx';
      else if (fileExt === 'xls') docType = 'xls';
      else if (fileExt === 'xlsx') docType = 'xlsx';
      else if (fileExt === 'ppt') docType = 'ppt';
      else if (fileExt === 'pptx') docType = 'pptx';
      else if (fileExt === 'txt') docType = 'txt';
      else if (fileExt === 'html' || fileExt === 'htm') docType = 'html';
      else docType = 'pdf';
      
      const viewUrl = `/api/ai/documents/pdf/${fileId}/view/`;
      
      setViewerDocument({
        fileId,
        title: filename,
        url: viewUrl,
        type: docType,
        page: page
      });
      setIsLoadingDocument(false);
    } catch (error: any) {
      console.error('Failed to load document:', error);
      // Show user-friendly error message
      const errorMessage = error?.message || error?.error || 'Failed to load document';
      if (errorMessage.includes('not found') || errorMessage.includes('File not found')) {
        alert(`Document not found: The file may have been deleted or is no longer available.`);
      } else {
        alert(`Failed to load document: ${errorMessage}`);
      }
      setIsLoadingDocument(false);
    }
  };

  const closeDocumentViewer = () => {
    setViewerDocument(null);
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <Network className="h-6 w-6 text-green-600" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">{t('graphRag')}</h1>
              <p className="text-sm text-gray-500">{t('entityAwareSearch')}</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {graphStats && (
              <button
                onClick={() => setShowGraphStats(!showGraphStats)}
                className="flex items-center px-3 py-1 text-sm text-green-600 hover:text-green-700"
              >
                <BarChart3 className="mr-1 h-4 w-4" />
                {t('stats')}
              </button>
            )}
            {graphStats && graphStats.query_entities.length > 0 && (
              <button
                onClick={() => setShowEntities(!showEntities)}
                className="flex items-center px-3 py-1 text-sm text-teal-600 hover:text-teal-700"
              >
                <Tag className="mr-1 h-4 w-4" />
                {t('entities')}
              </button>
            )}
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="flex items-center px-3 py-1 text-sm text-gray-600 hover:text-gray-700"
            >
              <History className="mr-1 h-4 w-4" />
              {t('history')}
            </button>
          </div>
        </div>
      </div>

      {/* Graph Stats Panel */}
      {showGraphStats && graphStats && (
        <div className="bg-green-50 border-b border-green-200 px-6 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-6 text-sm">
              <span className="flex items-center">
                <Target className="mr-1 h-4 w-4 text-green-600" />
                <span className="font-medium">{t('total')}: {graphStats.total_results}</span>
              </span>
              <span className="flex items-center">
                <Sparkles className="mr-1 h-4 w-4 text-green-600" />
                <span className="font-medium text-green-700">{t('graphEnhanced')}: {graphStats.graph_enhanced}</span>
              </span>
              <span className="flex items-center">
                <FileText className="mr-1 h-4 w-4 text-emerald-600" />
                {t('vectorOnly')}: {graphStats.vector_only}
              </span>
              {graphStats.query_entities.length > 0 && (
                <span className="flex items-center">
                  <Tag className="mr-1 h-4 w-4 text-teal-600" />
                  {t('entities')}: {graphStats.query_entities.length}
                </span>
              )}
            </div>
            <button
              onClick={() => setShowGraphStats(false)}
              className="text-green-600 hover:text-green-700"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* Entity Panel */}
      {showEntities && graphStats && graphStats.query_entities.length > 0 && (
        <div className="bg-teal-50 border-b border-teal-200 px-6 py-3">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-teal-900">{t('extractedEntities')}</h3>
            <button
              onClick={() => setShowEntities(false)}
              className="text-teal-600 hover:text-teal-700"
            >
              <ChevronUp className="h-4 w-4" />
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {graphStats.query_entities.map((entity, idx) => (
              <span
                key={idx}
                className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${getEntityTypeColor(entity.type)}`}
              >
                <Tag className="mr-1 h-3 w-3" />
                {entity.name}
                <span className="ml-1 opacity-75">({entity.type})</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Content - Split Screen Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Chat Area */}
        <div className={`flex flex-col transition-all ${viewerDocument ? 'w-1/2 border-r border-gray-200' : 'flex-1'}`}>
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6">
            {messages.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <Network className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">{t('startGraphRagSearch')}</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    {t('graphRagDescription')}
                  </p>
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                {messages.map((message) => (
                  <div key={message.id} className="flex space-x-4">
                    <div className={`flex-1 ${message.role === 'user' ? 'text-right' : 'text-left'}`}>
                      <div className={`inline-block max-w-3xl rounded-lg px-4 py-2 ${
                        message.role === 'user' 
                          ? 'bg-green-600 text-white' 
                          : 'bg-white border border-gray-200'
                      }`}>
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div 
                              className="text-sm font-normal leading-relaxed text-gray-800"
                              dangerouslySetInnerHTML={{ 
                                __html: formatContentForDisplay(message.content) 
                              }}
                            />
                          </div>
                          <div className="flex items-center space-x-2">
                            {message.role === 'user' && (
                              <select
                                onChange={(e) => {
                                  const target = e.target.value as 'chat'|'rag_basic'|'rag'|'rag_comprehensive'|'rag_graph'|'troubleshooting';
                                  if (!target) return;
                                  try {
                                    localStorage.setItem('anylab_cross_post', JSON.stringify({ channel: target, content: message.content, ts: Date.now() }));
                                  } catch (err) {}
                                  e.currentTarget.selectedIndex = 0;
                                }}
                                className="text-xs border border-gray-300 rounded px-1 py-0.5 text-gray-600 bg-white"
                                defaultValue=""
                                title={t('askIn')}
                              >
                                <option value="">{t('askInPlaceholder')}</option>
                                <option value="chat">{t('freeChat')}</option>
                                <option value="rag_basic">{t('basicRag')}</option>
                                <option value="rag">{t('advancedRag')}</option>
                                <option value="rag_comprehensive">{t('comprehensiveRag')}</option>
                                <option value="troubleshooting">{t('troubleshooting')}</option>
                              </select>
                            )}
                            <button
                              onClick={() => copyToClipboard(message.content, message.id)}
                              className="ml-2 text-gray-400 hover:text-gray-600 transition-colors"
                              title={t('copyFormattedTextWithReferences')}
                            >
                              {copiedMessageId === message.id ? (
                                <Check className="h-4 w-4 text-green-600" />
                              ) : (
                                <Copy className="h-4 w-4" />
                              )}
                            </button>
                          </div>
                        </div>
                        
                        {/* View Graph Button for Assistant Messages */}
                        {message.role === 'assistant' && currentQuery && (
                          <div className="mt-3 pt-3 border-t border-gray-200">
                            <button
                              onClick={handleViewGraph}
                              className="flex items-center px-3 py-1.5 bg-green-50 hover:bg-green-100 text-green-700 rounded text-xs font-medium transition-colors"
                            >
                              <GitBranch className="mr-1.5 h-4 w-4" />
                              {t('viewGraph')}
                            </button>
                          </div>
                        )}

                        {/* References */}
                        {message.references && message.references.length > 0 && (
                          <div className="mt-3 pt-3 border-t border-gray-200">
                            <p className="text-xs font-medium text-gray-600 mb-2">{t('references')}:</p>
                            <div className="space-y-2">
                              {message.references.map((ref, index) => (
                                <div 
                                  key={index} 
                                  className={`text-xs p-3 rounded border transition-all ${
                                    ref.view_url 
                                      ? 'bg-blue-50 border-blue-200 hover:bg-blue-100 cursor-pointer' 
                                      : 'bg-gray-50 border-gray-200'
                                  }`}
                                  onClick={() => {
                                    if (ref.view_url) {
                                      const match = ref.view_url.match(/\/pdf\/(\d+)\/view/);
                                      if (match) {
                                        const fileId = match[1];
                                        openDocumentInViewer(fileId, ref.title || 'Document', ref.page || 1);
                                      }
                                    }
                                  }}
                                >
                                  <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                      <div className="flex items-center justify-between mb-1">
                                        <p className="font-medium text-gray-700">{ref.title}</p>
                                        <div className="flex items-center gap-2">
                                          {ref.source && (
                                            <span className={`px-2 py-0.5 rounded text-xs font-medium border ${getSourceBadgeColor(ref.source)}`}>
                                              {ref.source === 'vector+graph' && <><Sparkles className="inline mr-1 h-3 w-3" /> {t('graphEnhanced')}</>}
                                              {ref.source === 'graph' && t('graphOnly')}
                                              {ref.source === 'vector' && t('vectorOnly')}
                                            </span>
                                          )}
                                          {ref.view_url && (
                                            <ExternalLink className="h-4 w-4 text-blue-600 flex-shrink-0" />
                                          )}
                                        </div>
                                      </div>
                                      <p className="text-gray-600 mt-1">{ref.content.substring(0, 150)}...</p>
                                      {ref.page && (
                                        <p className="text-gray-500 mt-1">{t('page')}: {ref.page}</p>
                                      )}
                                      {ref.matched_entities && ref.matched_entities.length > 0 && (
                                        <div className="flex flex-wrap gap-1 mt-2">
                                          {ref.matched_entities.slice(0, 3).map((entity, idx) => (
                                            <span key={idx} className={`px-1.5 py-0.5 rounded text-xs ${getEntityTypeColor(entity.type)}`}>
                                              {entity.name}
                                            </span>
                                          ))}
                                          {ref.matched_entities.length > 3 && (
                                            <span className="text-xs text-gray-500">+{ref.matched_entities.length - 3}</span>
                                          )}
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
            
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-white border border-gray-200 rounded-lg px-4 py-3">
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-green-600"></div>
                    <span className="text-gray-600">{t('searchingWithGraphRelationships')}</span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="bg-white border-t border-gray-200 p-6">
            <div className="flex space-x-4">
              <div className="flex-1">
                <textarea
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder={t('askAboutProductsVersionsErrors')}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent resize-none"
                  rows={3}
                  disabled={isLoading}
                />
              </div>
              <button
                onClick={handleGraphSearch}
                disabled={!inputMessage.trim() || isLoading}
                className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Send className="h-5 w-5" />
              </button>
            </div>
            
            <div className="mt-3 text-xs text-gray-500">
              {t('graphRagNote')}
            </div>
          </div>
        </div>

        {/* History Sidebar - Only show if document viewer is not open */}
        {showHistory && !viewerDocument && (
          <div className="w-80 bg-white border-l border-gray-200 flex flex-col">
            <div className="p-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">{t('searchHistory')}</h3>
                <button
                  onClick={() => refreshUnifiedHistory()}
                  className="text-sm text-green-600 hover:text-green-700"
                >
                  {t('refresh')}
                </button>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              {unifiedHistory.length === 0 ? (
                <div className="text-center py-8">
                  <History className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">{t('noSearchHistory')}</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    {t('graphRagConversationsWillAppear')}
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {unifiedHistory.map((item) => (
                    <div key={item.id} className="border border-gray-200 rounded-lg p-3">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <button
                            onClick={() => { setInputMessage(item.content); setShowHistory(false); }}
                            className="text-sm font-medium text-gray-900 hover:text-green-600 transition-colors text-left"
                          >
                            {item.content}
                          </button>
                          <p className="text-xs text-gray-500 mt-1">
                            {new Date(item.created_at).toLocaleString()} • {item.channel}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Right Panel - Document Viewer */}
        {viewerDocument && (
          <div className="w-1/2 flex flex-col bg-white border-l border-gray-200 relative">
            {/* Close button - positioned absolutely in top-right corner */}
            <button
              onClick={closeDocumentViewer}
              className="absolute top-2 right-2 z-[200] p-2 bg-white hover:bg-gray-100 rounded shadow-md border border-gray-200 transition-colors"
              title="Close document viewer"
            >
              <X className="h-5 w-5 text-gray-600" />
            </button>
            
            {/* Document Viewer Content */}
            <div className="flex-1 overflow-hidden">
              {isLoadingDocument ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <Loader2 className="mx-auto h-8 w-8 animate-spin text-primary-600" />
                    <p className="mt-2 text-sm text-gray-600">Loading document...</p>
                  </div>
                </div>
              ) : (
                <DocumentViewer
                  key={viewerDocument.fileId}
                  title={viewerDocument.title}
                  url={viewerDocument.url}
                  docType={viewerDocument.type}
                  initialPage={viewerDocument.page}
                />
              )}
            </div>
          </div>
        )}
      </div>

      {/* Graph Visualization Modal */}
      {showGraphModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => setShowGraphModal(false)}>
          <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl mx-4 max-h-[90vh] overflow-hidden flex flex-col" onClick={(e) => e.stopPropagation()}>
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <div className="flex items-center space-x-3">
                <Network className="h-6 w-6 text-green-600" />
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">{t('knowledgeGraphVisualization')}</h2>
                  <p className="text-sm text-gray-500 mt-1">{t('query')}: {currentQuery}</p>
                </div>
              </div>
              <button
                onClick={() => setShowGraphModal(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            {/* Graph Content */}
            <div className="flex-1 overflow-auto p-6">
              {loadingGraph ? (
                <div className="flex items-center justify-center h-96">
                  <div className="text-center">
                    <Loader2 className="h-12 w-12 text-green-600 animate-spin mx-auto mb-4" />
                    <p className="text-gray-600">{t('loadingGraphData')}</p>
                  </div>
                </div>
              ) : graphData && graphData.error ? (
                <div className="flex items-center justify-center h-96">
                  <div className="text-center">
                    <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
                    <p className="text-gray-900 font-medium mb-2">Failed to load graph data</p>
                    <p className="text-gray-600 text-sm">{graphData.message || 'An error occurred while loading the graph'}</p>
                  </div>
                </div>
              ) : graphData ? (
                <div>
                  {/* Stats */}
                  {graphData.stats && (
                    <div className="mb-6 grid grid-cols-3 gap-4">
                      <div className="bg-green-50 rounded-lg p-4">
                        <p className="text-sm text-gray-600">Nodes</p>
                        <p className="text-2xl font-bold text-green-600">{graphData.stats.total_nodes}</p>
                      </div>
                      <div className="bg-emerald-50 rounded-lg p-4">
                        <p className="text-sm text-gray-600">Relationships</p>
                        <p className="text-2xl font-bold text-emerald-600">{graphData.stats.total_edges}</p>
                      </div>
                      <div className="bg-teal-50 rounded-lg p-4">
                        <p className="text-sm text-gray-600">Query Entities</p>
                        <p className="text-2xl font-bold text-teal-600">{graphData.stats.query_entities}</p>
                      </div>
                    </div>
                  )}

                  {/* Force-Directed Graph Visualization with D3.js */}
                  <div className="border-2 border-gray-200 rounded-lg bg-gradient-to-br from-gray-50 to-gray-100">
                    {graphData.nodes.length === 0 ? (
                      <div className="flex items-center justify-center h-96">
                        <div className="text-center">
                          <Network className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                          <p className="text-gray-600">No graph data available for this query</p>
                        </div>
                      </div>
                    ) : (
                      <div>
                        {/* Interactive Graph Canvas */}
                        <div className="relative">
                          <svg
                            ref={graphSvgRef}
                            className="w-full border-b border-gray-200 bg-white"
                            style={{ height: '600px' }}
                          />
                          <div className="absolute top-4 right-4 bg-white bg-opacity-90 rounded-lg p-3 shadow-md text-xs">
                            <p className="font-semibold text-gray-700 mb-2">Legend:</p>
                            <div className="space-y-1">
                              <div className="flex items-center">
                                <div className="w-4 h-4 rounded-full bg-green-500 mr-2"></div>
                                <span className="text-gray-600">Query Entities</span>
                              </div>
                              <div className="flex items-center">
                                <div className="w-4 h-4 rounded-full bg-teal-500 mr-2"></div>
                                <span className="text-gray-600">Related Entities</span>
                              </div>
                              <div className="flex items-center">
                                <div className="w-4 h-4 rounded-full bg-blue-500 mr-2"></div>
                                <span className="text-gray-600">Documents</span>
                              </div>
                            </div>
                            <p className="text-gray-500 mt-2 pt-2 border-t border-gray-200">
                              💡 Drag nodes • Scroll to zoom
                            </p>
                          </div>
                        </div>

                        {/* Entity Summary Below Graph */}
                        <div className="p-6 space-y-4">
                          {/* Query Entities */}
                          {graphData.nodes.filter((n: any) => n.group === 'query_entity').length > 0 && (
                            <div>
                              <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center">
                                <Sparkles className="mr-2 h-4 w-4 text-green-600" />
                                Query Entities ({graphData.nodes.filter((n: any) => n.group === 'query_entity').length})
                              </h4>
                              <div className="flex flex-wrap gap-2">
                                {graphData.nodes
                                  .filter((n: any) => n.group === 'query_entity')
                                  .map((node: any) => (
                                    <div
                                      key={node.id}
                                      className="px-3 py-1.5 bg-green-100 border border-green-300 text-green-800 rounded text-xs font-medium"
                                    >
                                      {node.label}
                                      {node.entityType && (
                                        <span className="ml-1.5 text-[10px] opacity-75">({node.entityType})</span>
                                      )}
                                    </div>
                                  ))}
                              </div>
                            </div>
                          )}

                          {/* Related Entities */}
                          {graphData.nodes.filter((n: any) => n.group === 'related_entity').length > 0 && (
                            <div>
                              <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center">
                                <GitBranch className="mr-2 h-4 w-4 text-teal-600" />
                                Related Entities ({graphData.nodes.filter((n: any) => n.group === 'related_entity').length})
                              </h4>
                              <div className="flex flex-wrap gap-2">
                                {graphData.nodes
                                  .filter((n: any) => n.group === 'related_entity')
                                  .map((node: any) => (
                                    <div
                                      key={node.id}
                                      className={`px-2 py-1 border rounded text-xs font-medium ${getEntityTypeColor(node.entityType || 'UNKNOWN')}`}
                                    >
                                      {node.label}
                                      {node.entityType && (
                                        <span className="ml-1 text-[10px] opacity-75">({node.entityType})</span>
                                      )}
                                    </div>
                                  ))}
                              </div>
                            </div>
                          )}

                          {/* Documents */}
                          {graphData.nodes.filter((n: any) => n.type === 'document').length > 0 && (
                            <div>
                              <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center">
                                <FileText className="mr-2 h-4 w-4 text-blue-600" />
                                Related Documents ({graphData.nodes.filter((n: any) => n.type === 'document').length})
                              </h4>
                              <div className="space-y-1.5">
                                {graphData.nodes
                                  .filter((n: any) => n.type === 'document')
                                  .map((node: any) => (
                                    <div
                                      key={node.id}
                                      className="px-3 py-1.5 bg-blue-50 border border-blue-200 text-blue-800 rounded text-xs"
                                    >
                                      {node.label}
                                    </div>
                                  ))}
                              </div>
                            </div>
                          )}

                          {/* Relationship Info */}
                          {graphData.edges.length > 0 && (
                            <div className="pt-4 border-t border-gray-200">
                              <p className="text-sm text-gray-600">
                                <strong>{graphData.edges.length}</strong> relationships found between entities
                              </p>
                              <div className="mt-2 text-xs text-gray-500">
                                Relationship types: {Array.from(new Set(graphData.edges.map((e: any) => e.type))).join(', ')}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Entity List */}
                  {graphData.entities && graphData.entities.length > 0 && (
                    <div className="mt-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-3">Extracted Entities</h3>
                      <div className="flex flex-wrap gap-2">
                        {graphData.entities.map((entity: any, idx: number) => (
                          <span
                            key={idx}
                            className={`inline-flex items-center px-3 py-1.5 rounded text-sm font-medium ${getEntityTypeColor(entity.type)}`}
                          >
                            <Tag className="mr-1.5 h-3.5 w-3.5" />
                            {entity.name}
                            <span className="ml-1.5 opacity-75">({entity.type})</span>
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex items-center justify-center h-96">
                  <div className="text-center">
                    <AlertTriangle className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
                    <p className="text-gray-600">Failed to load graph data</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GraphRagSearch;

