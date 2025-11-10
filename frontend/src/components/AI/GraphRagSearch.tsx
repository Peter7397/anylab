import React, { useState, useEffect, useRef } from 'react';
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
  AlertTriangle
} from 'lucide-react';
import { apiClient } from '../../services/api';
import { useUnifiedChatHistory } from '../../hooks/useUnifiedChatHistory';

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
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showHistory, setShowHistory] = useState(true);
  const [showGraphStats, setShowGraphStats] = useState(false);
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
        content: res.response || 'No response received',
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
        content: 'Graph RAG search failed. Please try again.',
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
      return 'bg-purple-100 text-purple-800 border-purple-300';
    }
    return 'bg-blue-100 text-blue-800 border-blue-300';
  };

  const getEntityTypeColor = (type: string) => {
    const colors: { [key: string]: string } = {
      'PRODUCT': 'bg-indigo-100 text-indigo-800',
      'VERSION': 'bg-blue-100 text-blue-800',
      'ERROR_CODE': 'bg-red-100 text-red-800',
      'SOLUTION': 'bg-green-100 text-green-800',
      'PROBLEM': 'bg-orange-100 text-orange-800',
      'OS': 'bg-yellow-100 text-yellow-800',
      'DATABASE': 'bg-purple-100 text-purple-800',
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  const handleViewGraph = async () => {
    if (!currentQuery) return;
    
    setLoadingGraph(true);
    setShowGraphModal(true);
    
    try {
      const data = await apiClient.getGraphForQuery(currentQuery, 50, 2);
      setGraphData(data);
    } catch (error) {
      console.error('Error loading graph:', error);
      setGraphData(null);
    } finally {
      setLoadingGraph(false);
    }
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
              <h1 className="text-xl font-semibold text-gray-900">Graph RAG</h1>
              <p className="text-sm text-gray-500">Entity-aware search with knowledge graph relationships</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {graphStats && (
              <button
                onClick={() => setShowGraphStats(!showGraphStats)}
                className="flex items-center px-3 py-1 text-sm text-green-600 hover:text-green-700"
              >
                <BarChart3 className="mr-1 h-4 w-4" />
                Stats
              </button>
            )}
            {graphStats && graphStats.query_entities.length > 0 && (
              <button
                onClick={() => setShowEntities(!showEntities)}
                className="flex items-center px-3 py-1 text-sm text-indigo-600 hover:text-indigo-700"
              >
                <Tag className="mr-1 h-4 w-4" />
                Entities
              </button>
            )}
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="flex items-center px-3 py-1 text-sm text-gray-600 hover:text-gray-700"
            >
              <History className="mr-1 h-4 w-4" />
              History
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
                <span className="font-medium">Total: {graphStats.total_results}</span>
              </span>
              <span className="flex items-center">
                <Sparkles className="mr-1 h-4 w-4 text-green-600" />
                <span className="font-medium text-green-700">Graph-Enhanced: {graphStats.graph_enhanced}</span>
              </span>
              <span className="flex items-center">
                <FileText className="mr-1 h-4 w-4 text-blue-600" />
                Vector Only: {graphStats.vector_only}
              </span>
              {graphStats.query_entities.length > 0 && (
                <span className="flex items-center">
                  <Tag className="mr-1 h-4 w-4 text-indigo-600" />
                  Entities: {graphStats.query_entities.length}
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
        <div className="bg-indigo-50 border-b border-indigo-200 px-6 py-3">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-indigo-900">Extracted Entities</h3>
            <button
              onClick={() => setShowEntities(false)}
              className="text-indigo-600 hover:text-indigo-700"
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

      {/* Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6">
            {messages.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <Network className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">Start Graph RAG Search</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Ask questions with specific entities like products, versions, or error codes for enhanced search with knowledge graph relationships.
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
                                title="Ask in..."
                              >
                                <option value="">Ask in…</option>
                                <option value="chat">Free Chat</option>
                                <option value="rag_basic">Basic RAG</option>
                                <option value="rag">Advanced RAG</option>
                                <option value="rag_comprehensive">Comprehensive RAG</option>
                                <option value="troubleshooting">Troubleshooting</option>
                              </select>
                            )}
                            <button
                              onClick={() => copyToClipboard(message.content, message.id)}
                              className="ml-2 text-gray-400 hover:text-gray-600 transition-colors"
                              title="Copy formatted text with references"
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
                              View Graph
                            </button>
                          </div>
                        )}

                        {/* References */}
                        {message.references && message.references.length > 0 && (
                          <div className="mt-3 pt-3 border-t border-gray-200">
                            <p className="text-xs font-medium text-gray-600 mb-2">References:</p>
                            <div className="space-y-2">
                              {message.references.map((ref, index) => (
                                <div key={index} className="text-xs bg-gray-50 p-2 rounded border">
                                  <div className="flex items-center justify-between mb-1">
                                    <p className="font-medium text-gray-700">{ref.title}</p>
                                    {ref.source && (
                                      <span className={`px-2 py-0.5 rounded text-xs font-medium border ${getSourceBadgeColor(ref.source)}`}>
                                        {ref.source === 'vector+graph' && <><Sparkles className="inline mr-1 h-3 w-3" /> Graph-Enhanced</>}
                                        {ref.source === 'graph' && 'Graph Only'}
                                        {ref.source === 'vector' && 'Vector Only'}
                                      </span>
                                    )}
                                  </div>
                                  <p className="text-gray-600 mt-1">{ref.content.substring(0, 150)}...</p>
                                  {ref.page && (
                                    <p className="text-gray-500 mt-1">Page: {ref.page}</p>
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
                    <span className="text-gray-600">Searching with graph relationships...</span>
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
                  placeholder="Ask about products, versions, errors, or solutions (e.g., 'OpenLab CDS version 2.8 installation')..."
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
              Graph RAG uses entity extraction and knowledge graph relationships for enhanced search. Try queries with specific products, versions, or error codes.
            </div>
          </div>
        </div>

        {/* History Sidebar */}
        {showHistory && (
          <div className="w-80 bg-white border-l border-gray-200 flex flex-col">
            <div className="p-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">Search History</h3>
                <button
                  onClick={() => refreshUnifiedHistory()}
                  className="text-sm text-green-600 hover:text-green-700"
                >
                  Refresh
                </button>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              {unifiedHistory.length === 0 ? (
                <div className="text-center py-8">
                  <History className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No search history</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Your graph RAG conversations will appear here.
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
                  <h2 className="text-xl font-semibold text-gray-900">Knowledge Graph Visualization</h2>
                  <p className="text-sm text-gray-500 mt-1">Query: {currentQuery}</p>
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
                    <p className="text-gray-600">Loading graph data...</p>
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
                      <div className="bg-blue-50 rounded-lg p-4">
                        <p className="text-sm text-gray-600">Relationships</p>
                        <p className="text-2xl font-bold text-blue-600">{graphData.stats.total_edges}</p>
                      </div>
                      <div className="bg-indigo-50 rounded-lg p-4">
                        <p className="text-sm text-gray-600">Query Entities</p>
                        <p className="text-2xl font-bold text-indigo-600">{graphData.stats.query_entities}</p>
                      </div>
                    </div>
                  )}

                  {/* Simple Graph Visualization */}
                  <div className="border-2 border-gray-200 rounded-lg p-6 bg-gradient-to-br from-gray-50 to-gray-100">
                    {graphData.nodes.length === 0 ? (
                      <div className="flex items-center justify-center h-96">
                        <div className="text-center">
                          <Network className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                          <p className="text-gray-600">No graph data available for this query</p>
                        </div>
                      </div>
                    ) : (
                      <div>
                        {/* Query Entities (Center/Hub) */}
                        {graphData.nodes.filter((n: any) => n.group === 'query_entity').length > 0 && (
                          <div className="mb-6">
                            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
                              <Sparkles className="mr-2 h-4 w-4 text-green-600" />
                              Query Entities
                            </h4>
                            <div className="flex flex-wrap gap-2">
                              {graphData.nodes
                                .filter((n: any) => n.group === 'query_entity')
                                .map((node: any) => (
                                  <div
                                    key={node.id}
                                    className="px-4 py-2 bg-green-100 border-2 border-green-400 text-green-800 rounded-lg text-sm font-medium shadow-md"
                                  >
                                    {node.label}
                                    {node.entityType && (
                                      <span className="ml-2 text-xs opacity-75">({node.entityType})</span>
                                    )}
                                  </div>
                                ))}
                            </div>
                          </div>
                        )}

                        {/* Related Entities */}
                        {graphData.nodes.filter((n: any) => n.group === 'related_entity').length > 0 && (
                          <div className="mb-6">
                            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
                              <GitBranch className="mr-2 h-4 w-4 text-indigo-600" />
                              Related Entities
                            </h4>
                            <div className="flex flex-wrap gap-2">
                              {graphData.nodes
                                .filter((n: any) => n.group === 'related_entity')
                                .map((node: any) => (
                                  <div
                                    key={node.id}
                                    className={`px-3 py-1.5 border-2 rounded-lg text-xs font-medium shadow-sm ${getEntityTypeColor(node.entityType || 'UNKNOWN')} border-opacity-50`}
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

                        {/* Documents */}
                        {graphData.nodes.filter((n: any) => n.type === 'document').length > 0 && (
                          <div>
                            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
                              <FileText className="mr-2 h-4 w-4 text-blue-600" />
                              Related Documents
                            </h4>
                            <div className="space-y-2">
                              {graphData.nodes
                                .filter((n: any) => n.type === 'document')
                                .map((node: any) => (
                                  <div
                                    key={node.id}
                                    className="px-3 py-2 bg-blue-50 border border-blue-200 text-blue-800 rounded text-sm"
                                  >
                                    {node.label}
                                  </div>
                                ))}
                            </div>
                          </div>
                        )}

                        {/* Connections Info */}
                        {graphData.edges.length > 0 && (
                          <div className="mt-6 pt-6 border-t border-gray-300">
                            <p className="text-sm text-gray-600">
                              <strong>{graphData.edges.length}</strong> relationships found between entities
                            </p>
                            <div className="mt-3 text-xs text-gray-500">
                              Relationship types: {Array.from(new Set(graphData.edges.map((e: any) => e.type))).join(', ')}
                            </div>
                          </div>
                        )}
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

