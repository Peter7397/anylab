import React, { useState, useEffect, useRef } from 'react';
import { Send, Copy, Check, History, Trash2, Clock, Zap, FileText, Search } from 'lucide-react';
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

interface PerformanceStats {
  responseTime: number;
  tokensUsed: string;
  searchResults: number;
}

const BASIC_HISTORY_STORAGE_KEY = 'basic_rag_history';
const BASIC_MESSAGES_STORAGE_KEY = 'basic_rag_messages';

const BasicRagSearch: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const [chatHistory, setChatHistory] = useState<Array<{ 
    id: string; 
    prompt: string; 
    preview: string; 
    timestamp: string;
    response?: string;
    sources?: Array<{ title: string; content: string; page?: number; score?: number; view_url?: string }>;
  }>>([]);
  const [showHistory, setShowHistory] = useState(false);
  const { history: unifiedHistory, recordUserPrompt, refresh: refreshUnifiedHistory } = useUnifiedChatHistory(200);
  const [performanceStats, setPerformanceStats] = useState<PerformanceStats>({
    responseTime: 0,
    tokensUsed: 'N/A',
    searchResults: 0
  });
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load saved messages and history on component mount
  useEffect(() => {
    const savedMessages = localStorage.getItem(BASIC_MESSAGES_STORAGE_KEY);
    const savedHistory = localStorage.getItem(BASIC_HISTORY_STORAGE_KEY);
    
    if (savedMessages) {
      try {
        setMessages(JSON.parse(savedMessages));
      } catch (error) {
        console.error('Error loading saved messages:', error);
      }
    }
    
    if (savedHistory) {
      try {
        setChatHistory(JSON.parse(savedHistory));
      } catch (error) {
        console.error('Error loading saved history:', error);
      }
    }
  }, []);

  // Save messages and history to localStorage
  useEffect(() => {
    localStorage.setItem(BASIC_MESSAGES_STORAGE_KEY, JSON.stringify(messages));
  }, [messages]);

  useEffect(() => {
    localStorage.setItem(BASIC_HISTORY_STORAGE_KEY, JSON.stringify(chatHistory));
  }, [chatHistory]);

  // Auto-scroll to bottom when new messages are added
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Cross-post receiver for Basic RAG
  useEffect(() => {
    try {
      const raw = localStorage.getItem('anylab_cross_post');
      if (raw) {
        const payload = JSON.parse(raw);
        if (payload?.channel === 'rag_basic' && typeof payload?.content === 'string') {
          localStorage.removeItem('anylab_cross_post');
          setInputMessage(payload.content);
          setTimeout(() => handleBasicRagSearch(), 0);
        }
      }
    } catch (_) {}
  }, []);

  const handleBasicRagSearch = async () => {
    const currentQuery = inputMessage.trim();
    if (!currentQuery || isLoading) return;

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
    try { await recordUserPrompt('rag_basic', currentQuery); } catch (e) { console.error('Failed to record unified history:', e); }

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
      
      // Use basic RAG search for quick, straightforward answers
      const res = await apiClient.ragSearch(currentQuery, 8, 'basic'); // Use basic mode
      
      const endTime = Date.now();
      const responseTime = endTime - startTime;

      // Set performance stats
      setPerformanceStats({
        responseTime,
        tokensUsed: 'N/A', // Basic RAG doesn't return tokens_used
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
          ? { ...item, response: res.response, sources: res.sources?.map((source: any) => {
              const mappedSource = {
                title: source.title || 'Unknown Document',
                content: source.content || '',
                page: source.page || source.page_number,
                score: source.similarity || source.score,
                view_url: source.view_url
              };
              // Debug log to verify view_url is being captured
              if (source.view_url) {
                console.log('Source view_url:', source.view_url);
              }
              return mappedSource;
            }) || [] }
          : item
      ));
    } catch (error) {
      console.error('Basic RAG search error:', error);
      
      // Add error message
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Basic RAG search failed. Please try again.',
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
      handleBasicRagSearch();
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
    localStorage.removeItem(BASIC_HISTORY_STORAGE_KEY);
    localStorage.removeItem(BASIC_MESSAGES_STORAGE_KEY);
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Search className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">Basic RAG Search</h1>
              <p className="text-sm text-gray-500">Quick and straightforward document-based answers</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {/* Performance Stats */}
            <div className="flex items-center space-x-4 text-sm text-gray-500">
              <div className="flex items-center space-x-1">
                <Clock className="h-4 w-4" />
                <span>{performanceStats.responseTime}ms</span>
              </div>
              <div className="flex items-center space-x-1">
                <Zap className="h-4 w-4" />
                <span>{performanceStats.tokensUsed}</span>
              </div>
              <div className="flex items-center space-x-1">
                <FileText className="h-4 w-4" />
                <span>{performanceStats.searchResults} sources</span>
              </div>
            </div>
            
            {/* History Button */}
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              title="Chat History"
            >
              <History className="h-5 w-5" />
            </button>
            
            {/* Clear History */}
            <button
              onClick={clearHistory}
              className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
              title="Clear History"
            >
              <Trash2 className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>

            {/* Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6">
        {messages.length === 0 ? (
          <div className="text-center py-12">
            <Search className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Basic RAG Search</h3>
            <p className="text-gray-500 max-w-md mx-auto">
              Ask questions about your documents and get quick, straightforward answers. 
              This mode provides fast responses using basic vector similarity search.
            </p>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
              className={`max-w-3xl rounded-lg px-4 py-3 ${
                  message.role === 'user'
                    ? 'bg-primary-600 text-white'
                    : 'bg-white border border-gray-200'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div 
                      className="prose prose-sm max-w-none font-normal text-gray-800"
                      dangerouslySetInnerHTML={{ 
                        __html: formatContentForDisplay(message.content) 
                      }}
                    />
                    
                    {/* References for assistant messages */}
                    {message.role === 'assistant' && message.references && message.references.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-gray-100">
                        <p className="text-sm font-medium text-gray-700 mb-2">Sources:</p>
                        <div className="space-y-2">
                          {message.references.map((ref, index) => (
                            <div key={index} className="text-sm bg-gray-50 p-2 rounded">
                              <p className="font-medium text-gray-800">{ref.title}</p>
                              {ref.page && <p className="text-gray-600">Page: {ref.page}</p>}
                              {ref.score && <p className="text-gray-600">Relevance: {(ref.score * 100).toFixed(1)}%</p>}
                              <p className="text-gray-700 mt-1">{ref.content.substring(0, 150)}...</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
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
                        <option value="rag">Advanced RAG</option>
                        <option value="rag_comprehensive">Comprehensive RAG</option>
                        <option value="troubleshooting">Troubleshooting</option>
                      </select>
                    )}
                    <button
                      onClick={() => copyToClipboard(message.content, message.id)}
                      className={`ml-2 p-1 rounded transition-colors ${
                        message.role === 'user'
                          ? 'text-blue-200 hover:text-white'
                          : 'text-gray-400 hover:text-gray-600'
                      }`}
                      title="Copy formatted text"
                    >
                      {copiedMessageId === message.id ? (
                        <Check className="h-4 w-4" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </div>
                
                <p className={`text-xs mt-2 ${
                  message.role === 'user' ? 'text-blue-200' : 'text-gray-500'
                }`}>
                  {new Date(message.timestamp).toLocaleString()}
                </p>
              </div>
            </div>
          ))
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
            onClick={handleBasicRagSearch}
            disabled={!inputMessage.trim() || isLoading}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="h-5 w-5" />
          </button>
        </div>
        
        <div className="mt-3 text-xs text-gray-500">
          Basic RAG provides quick answers using vector similarity search. For more advanced features, try Advanced RAG or Comprehensive RAG.
        </div>
      </div>
        </div>

            {/* History Sidebar */
            }
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
                    Your basic RAG searches will appear here.
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

export default BasicRagSearch;
