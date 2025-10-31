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
  Layers
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
  }>;
}

const ComprehensiveRagSearch: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showHistory, setShowHistory] = useState(true);
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
  const [performanceStats, setPerformanceStats] = useState<any>(null);
  const [showPerformanceStats, setShowPerformanceStats] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Storage keys
  const COMPREHENSIVE_HISTORY_STORAGE_KEY = 'anylab_comprehensive_history';
  const COMPREHENSIVE_MESSAGES_STORAGE_KEY = 'anylab_comprehensive_messages';

  // Load history and messages on component mount
  useEffect(() => {
    try {
      console.log('Loading Comprehensive RAG history from localStorage...');
      
      // Load Comprehensive history
      const comprehensiveHistoryRaw = localStorage.getItem(COMPREHENSIVE_HISTORY_STORAGE_KEY);
      if (comprehensiveHistoryRaw) {
        const parsed = JSON.parse(comprehensiveHistoryRaw);
        if (Array.isArray(parsed)) {
          setChatHistory(parsed);
          console.log('Loaded Comprehensive history:', parsed.length, 'items');
        }
      }

      // Load Comprehensive messages
      const comprehensiveMessagesRaw = localStorage.getItem(COMPREHENSIVE_MESSAGES_STORAGE_KEY);
      if (comprehensiveMessagesRaw) {
        const parsed = JSON.parse(comprehensiveMessagesRaw);
        if (Array.isArray(parsed)) {
          setMessages(parsed);
          console.log('Loaded Comprehensive messages:', parsed.length, 'items');
        }
      }
    } catch (error) {
      console.error('Error loading Comprehensive history from localStorage:', error);
    }
  }, []);

  // Save history whenever it changes
  useEffect(() => {
    localStorage.setItem(COMPREHENSIVE_HISTORY_STORAGE_KEY, JSON.stringify(chatHistory));
    console.log('Saved Comprehensive history:', chatHistory.length, 'items');
  }, [chatHistory]);

  // Save messages whenever they change
  useEffect(() => {
    localStorage.setItem(COMPREHENSIVE_MESSAGES_STORAGE_KEY, JSON.stringify(messages));
    console.log('Saved Comprehensive messages:', messages.length, 'items');
  }, [messages]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Cross-post receiver for Comprehensive RAG
  useEffect(() => {
    try {
      const raw = localStorage.getItem('anylab_cross_post');
      if (raw) {
        const payload = JSON.parse(raw);
        if (payload?.channel === 'rag_comprehensive' && typeof payload?.content === 'string') {
          localStorage.removeItem('anylab_cross_post');
          setInputMessage(payload.content);
          setTimeout(() => handleComprehensiveSearch(), 0);
        }
      }
    } catch (_) {}
  }, []);

  const handleComprehensiveSearch = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const currentQuery = inputMessage.trim();
    const messageId = Date.now().toString();
    
    // Add user message
    const userMessage: ChatMessage = {
      id: messageId,
      role: 'user',
      content: currentQuery,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    try { await recordUserPrompt('rag_comprehensive', currentQuery); } catch (e) { console.error('Failed to record unified history:', e); }

    // Add to history (will be updated with response later)
    const historyItem = {
      id: messageId,
      prompt: currentQuery,
      preview: currentQuery.substring(0, 50) + (currentQuery.length > 50 ? '...' : ''),
      timestamp: new Date().toISOString()
    };
    setChatHistory(prev => [historyItem, ...prev.slice(0, 9)]); // Keep last 10

    try {
      const startTime = Date.now();
      
      // Use comprehensive RAG search endpoint
      const res = await apiClient.comprehensiveRagSearch(currentQuery, 15, true);
      
      const endTime = Date.now();
      const responseTime = endTime - startTime;

      // Set performance stats
      setPerformanceStats({
        responseTime,
        tokensUsed: res.tokens_used || 'N/A',
        searchResults: res.sources?.length || 0
      });

      // Add assistant message
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: res.response || 'No response received',
        timestamp: new Date().toISOString(),
        references: res.sources?.map((source: any) => ({
          title: source.title || 'Unknown Document',
          content: source.content || '',
          page: source.page || source.page_number,
          score: source.similarity || source.score,
          view_url: source.view_url
        })) || []
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      // Update history with response
      setChatHistory(prev => prev.map(item => 
        item.id === messageId 
          ? { ...item, response: res.response, sources: res.sources?.map((source: any) => ({
              title: source.title || 'Unknown Document',
              content: source.content || '',
              page: source.page || source.page_number,
              score: source.similarity || source.score,
              view_url: source.view_url
            })) || [] }
          : item
      ));
    } catch (error) {
      console.error('Comprehensive RAG search error:', error);
      
      // Add error message
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Comprehensive RAG search failed. Please try again.',
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
      handleComprehensiveSearch();
    }
  };

  const formatContentForDisplay = (text: string) => {
    // Preserve paragraph structure while ensuring font consistency
    let formatted = text
      // Remove any remaining markdown formatting that could cause font issues
      .replace(/\*\*([^*]+)\*\*/g, '$1')  // Remove bold formatting
      .replace(/\*([^*\n]+?)\*/g, '$1')   // Remove italic formatting
      .replace(/`([^`]+)`/g, '$1')        // Remove code formatting
      .replace(/^#{1,6}\s+(.+)$/gm, '$1') // Remove headers
      // Preserve list structure
      .replace(/^(\d+)\.\s+(.+)$/gm, '$1. $2')
      .replace(/^[-*•]\s+(.+)$/gm, '• $1')
      // Normalize whitespace while preserving paragraph breaks
      .replace(/[ \t]+/g, ' ')  // Normalize spaces within lines
      .replace(/\n{3,}/g, '\n\n');  // Limit consecutive newlines
    
    // Convert newlines to <br> tags for proper display, preserving paragraph structure
    formatted = formatted.replace(/\n/g, '<br>');
    
    return formatted;
  };

  const copyToClipboard = async (text: string, messageId: string) => {
    try {
      // Find the message to get references
      const message = messages.find(m => m.id === messageId);
      
      // Clean up markdown formatting more thoroughly
      let formattedText = text
        // Remove bold formatting (double asterisks) - process first
        .replace(/\*\*([^*]+)\*\*/g, '$1')
        // Remove italic formatting (single asterisks) - process remaining ones
        .replace(/\*([^*\n]+?)\*/g, '$1')
        // Remove headers
        .replace(/^#{1,6}\s+/gm, '')
        // Remove code backticks
        .replace(/`([^`]+)`/g, '$1')
        // Convert links to text
        .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
        // Clean up extra whitespace
        .replace(/\n{3,}/g, '\n\n')
        .replace(/[ \t]+/g, ' ')
        .trim();
      
      // Add references if available
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

  const loadFromHistory = (historyItem: { id: string; prompt: string; preview: string; timestamp: string }) => {
    setInputMessage(historyItem.prompt);
    setShowHistory(false);
  };

  const clearHistory = () => {
    setChatHistory([]);
    setMessages([]);
    localStorage.removeItem(COMPREHENSIVE_HISTORY_STORAGE_KEY);
    localStorage.removeItem(COMPREHENSIVE_MESSAGES_STORAGE_KEY);
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-primary-100 rounded-lg">
              <Layers className="h-6 w-6 text-primary-600" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">Comprehensive RAG</h1>
              <p className="text-sm text-gray-500">Deep, comprehensive analysis with maximum detail</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {performanceStats && (
              <button
                onClick={() => setShowPerformanceStats(!showPerformanceStats)}
                className="flex items-center px-3 py-1 text-sm text-primary-600 hover:text-primary-700"
              >
                <Zap className="mr-1 h-4 w-4" />
                Performance
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

      {/* Performance Stats */}
      {showPerformanceStats && performanceStats && (
        <div className="bg-primary-50 border-b border-primary-200 px-6 py-3">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center space-x-4">
              <span className="flex items-center">
                <Clock className="mr-1 h-4 w-4 text-primary-600" />
                Response: {performanceStats.responseTime}ms
              </span>
              <span className="flex items-center">
                <Target className="mr-1 h-4 w-4 text-primary-600" />
                Results: {performanceStats.searchResults}
              </span>
              <span className="flex items-center">
                <FileText className="mr-1 h-4 w-4 text-primary-600" />
                Tokens: {performanceStats.tokensUsed}
              </span>
            </div>
            <button
              onClick={() => setShowPerformanceStats(false)}
              className="text-primary-600 hover:text-primary-700"
            >
              <X className="h-4 w-4" />
            </button>
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
              <Layers className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">Start Comprehensive RAG Search</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Ask questions for deep, comprehensive analysis with maximum detail and complete answers.
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
                          ? 'bg-blue-600 text-white' 
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
                                  const target = e.target.value as 'chat'|'rag_basic'|'rag'|'rag_comprehensive'|'troubleshooting';
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
                        
                        {/* References */}
                        {message.references && message.references.length > 0 && (
                          <div className="mt-3 pt-3 border-t border-gray-200">
                            <p className="text-xs font-medium text-gray-600 mb-2">References:</p>
                            <div className="space-y-2">
                              {message.references.map((ref, index) => (
                                <div key={index} className="text-xs bg-gray-50 p-2 rounded">
                                  <p className="font-medium text-gray-700">{ref.title}</p>
                                  <p className="text-gray-600 mt-1">{ref.content.substring(0, 150)}...</p>
                                  {ref.page && (
                                    <p className="text-gray-500 mt-1">Page: {ref.page}</p>
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
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                    <span className="text-gray-600">Searching documents...</span>
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
                  placeholder="Ask a question about your documents..."
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  rows={3}
                  disabled={isLoading}
                />
              </div>
              <button
                onClick={handleComprehensiveSearch}
                disabled={!inputMessage.trim() || isLoading}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Send className="h-5 w-5" />
              </button>
            </div>
            
            <div className="mt-3 text-xs text-gray-500">
              Comprehensive RAG provides deep analysis with maximum detail. For faster results, try Basic or Advanced RAG.
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
                  className="text-sm text-blue-600 hover:text-blue-700"
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
                    Your comprehensive RAG conversations will appear here.
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
                            className="text-sm font-medium text-gray-900 hover:text-blue-600 transition-colors text-left"
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
    </div>
  );
};

export default ComprehensiveRagSearch;
