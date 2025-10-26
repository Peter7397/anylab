import React, { useState, useEffect, useRef } from 'react';
import { 
  Search, 
  Send, 
  Clock, 
  FileText, 
  Copy, 
  Check, 
  Loader2,
  History,
  X,
  Zap,
  Target
} from 'lucide-react';
import { apiClient } from '../../services/api';

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

const RagSearch: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showHistory, setShowHistory] = useState(true);
  const [chatHistory, setChatHistory] = useState<Array<{ 
    id: string; 
    prompt: string; 
    preview: string; 
    timestamp: string;
    response?: string;
    sources?: Array<{ title: string; content: string; page?: number; score?: number }>;
  }>>([]);
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const [performanceStats, setPerformanceStats] = useState<any>(null);
  const [showPerformanceStats, setShowPerformanceStats] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Storage keys
  const RAG_HISTORY_STORAGE_KEY = 'anylab_rag_history';
  const RAG_MESSAGES_STORAGE_KEY = 'anylab_rag_messages';

  // Load history and messages on component mount
  useEffect(() => {
    try {
      console.log('Loading RAG history from localStorage...');
      
      // Load RAG history
      const ragHistoryRaw = localStorage.getItem(RAG_HISTORY_STORAGE_KEY);
      if (ragHistoryRaw) {
        const parsed = JSON.parse(ragHistoryRaw);
        if (Array.isArray(parsed)) {
          setChatHistory(parsed);
          console.log('Loaded RAG history:', parsed.length, 'items');
        }
      }

      // Load RAG messages
      const ragMessagesRaw = localStorage.getItem(RAG_MESSAGES_STORAGE_KEY);
      if (ragMessagesRaw) {
        const parsed = JSON.parse(ragMessagesRaw);
        if (Array.isArray(parsed)) {
          setMessages(parsed);
          console.log('Loaded RAG messages:', parsed.length, 'items');
        }
      }
    } catch (error) {
      console.error('Error loading RAG history from localStorage:', error);
    }
  }, []);

  // Save history whenever it changes
  useEffect(() => {
    localStorage.setItem(RAG_HISTORY_STORAGE_KEY, JSON.stringify(chatHistory));
    console.log('Saved RAG history:', chatHistory.length, 'items');
  }, [chatHistory]);

  // Save messages whenever they change
  useEffect(() => {
    localStorage.setItem(RAG_MESSAGES_STORAGE_KEY, JSON.stringify(messages));
    console.log('Saved RAG messages:', messages.length, 'items');
  }, [messages]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleRagSearch = async () => {
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
      
      // Use advanced RAG search with better coverage
      const res = await apiClient.advancedRagSearch(currentQuery, 8, 'hybrid'); // Increased topK for better results
      
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
          page: source.page,
          score: source.similarity || source.score
        })) || []
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      // Update history with response
      setChatHistory(prev => prev.map(item => 
        item.id === messageId 
          ? { ...item, response: res.response, sources: res.sources?.map((source: any) => ({
              title: source.title || 'Unknown Document',
              content: source.content || '',
              page: source.page,
              score: source.similarity || source.score
            })) || [] }
          : item
      ));
    } catch (error) {
      console.error('RAG search error:', error);
      
      // Add error message
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'RAG search failed. Please try again.',
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleRagSearch();
    }
  };

  const copyToClipboard = async (text: string, messageId: string) => {
    try {
      await navigator.clipboard.writeText(text);
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
    localStorage.removeItem(RAG_HISTORY_STORAGE_KEY);
    localStorage.removeItem(RAG_MESSAGES_STORAGE_KEY);
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
              <h1 className="text-xl font-semibold text-gray-900">Advanced RAG</h1>
              <p className="text-sm text-gray-500">Hybrid search with reranking for better accuracy</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {performanceStats && (
              <button
                onClick={() => setShowPerformanceStats(!showPerformanceStats)}
                className="flex items-center px-3 py-1 text-sm text-blue-600 hover:text-blue-700"
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
        <div className="bg-blue-50 border-b border-blue-200 px-6 py-3">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center space-x-4">
              <span className="flex items-center">
                <Clock className="mr-1 h-4 w-4 text-blue-600" />
                Response: {performanceStats.responseTime}ms
              </span>
              <span className="flex items-center">
                <Target className="mr-1 h-4 w-4 text-blue-600" />
                Results: {performanceStats.searchResults}
              </span>
              <span className="flex items-center">
                <FileText className="mr-1 h-4 w-4 text-blue-600" />
                Tokens: {performanceStats.tokensUsed}
              </span>
            </div>
            <button
              onClick={() => setShowPerformanceStats(false)}
              className="text-blue-600 hover:text-blue-700"
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
                  <Search className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">Start Advanced RAG Search</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Ask questions to search through your knowledge base with hybrid search and reranking.
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
                            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                          </div>
                          <button
                            onClick={() => copyToClipboard(message.content, message.id)}
                            className="ml-2 text-gray-400 hover:text-gray-600"
                          >
                            {copiedMessageId === message.id ? (
                              <Check className="h-4 w-4 text-green-600" />
                            ) : (
                              <Copy className="h-4 w-4" />
                            )}
                          </button>
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
                onClick={handleRagSearch}
                disabled={!inputMessage.trim() || isLoading}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Send className="h-5 w-5" />
              </button>
            </div>
            
            <div className="mt-3 text-xs text-gray-500">
              Advanced RAG uses hybrid search with reranking for better accuracy. For simpler searches, try Basic RAG.
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
                  onClick={clearHistory}
                  className="text-sm text-red-600 hover:text-red-700"
                >
                  Clear All
                </button>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              {chatHistory.length === 0 ? (
                <div className="text-center py-8">
                  <History className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No search history</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Your RAG searches will appear here.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {chatHistory.map((item) => (
                    <div key={item.id} className="border border-gray-200 rounded-lg p-3">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <button
                            onClick={() => loadFromHistory(item)}
                            className="text-sm font-medium text-gray-900 hover:text-blue-600 transition-colors text-left"
                          >
                            {item.prompt}
                          </button>
                          <p className="text-xs text-gray-500 mt-1">
                            {new Date(item.timestamp).toLocaleString()}
                          </p>
                        </div>
                        {item.response && (
                          <button
                            onClick={() => {
                              const newMessages: ChatMessage[] = [
                                {
                                  id: item.id,
                                  role: 'user',
                                  content: item.prompt,
                                  timestamp: item.timestamp
                                },
                                {
                                  id: (parseInt(item.id) + 1).toString(),
                                  role: 'assistant',
                                  content: item.response || 'No response available',
                                  timestamp: new Date().toISOString(),
                                  references: item.sources || []
                                }
                              ];
                              setMessages(newMessages);
                              setShowHistory(false);
                            }}
                            className="ml-2 px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
                          >
                            View
                          </button>
                        )}
                      </div>
                      
                      {/* Expandable Response */}
                      {item.response && (
                        <div className="mt-3 pt-3 border-t border-gray-100">
                          <details className="group">
                            <summary className="cursor-pointer text-sm text-gray-600 hover:text-gray-800 transition-colors">
                              <span className="group-open:hidden">Show response</span>
                              <span className="hidden group-open:inline">Hide response</span>
                            </summary>
                            <div className="mt-2 text-sm text-gray-700 bg-gray-50 p-3 rounded">
                              <p className="whitespace-pre-wrap">{item.response}</p>
                              
                              {/* Sources */}
                              {item.sources && item.sources.length > 0 && (
                                <div className="mt-3 pt-3 border-t border-gray-200">
                                  <p className="text-xs font-medium text-gray-600 mb-2">Sources:</p>
                                  <div className="space-y-2">
                                    {item.sources.map((source, index) => (
                                      <div key={index} className="text-xs bg-white p-2 rounded border">
                                        <p className="font-medium text-gray-800">{source.title}</p>
                                        {source.page && <p className="text-gray-600">Page: {source.page}</p>}
                                        {source.score && <p className="text-gray-600">Relevance: {(source.score * 100).toFixed(1)}%</p>}
                                        <p className="text-gray-700 mt-1">{source.content.substring(0, 100)}...</p>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          </details>
                        </div>
                      )}
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

export default RagSearch;
