import React, { useState, useRef, useEffect, useCallback } from 'react';
import { 
  Send, 
  FileText, 
  Globe, 
  Filter, 
  Sparkles,
  Copy,
  Check,
  Loader2,
  Download,
  ExternalLink,
  Eye,
  History,
  Zap,
  Clock,
  Target,
  X,
  MessageSquare
} from 'lucide-react';
import { ChatMessage, KnowledgeDocument } from '../../types';
import { apiClient } from '../../services/api';

// Unified Loading Component - Shows same loading state across all tabs
const LoadingMessage: React.FC = () => {
  return (
    <div className="flex justify-start">
      <div className="bg-gray-100 rounded-lg p-4 max-w-3xl">
        <div className="flex items-center space-x-3">
          <Loader2 size={16} className="text-primary-600 animate-spin" />
          <div>
            <span className="text-gray-700 font-medium">AI is thinking...</span>
            <div className="text-xs text-gray-500 mt-1">
              Generating response with Qwen 7B model
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// References Component for RAG responses
const ReferencesList: React.FC<{ sources: any[] }> = ({ sources }) => {
  const handleDownload = async (downloadUrl: string, filename: string) => {
    try {
      const response = await apiClient.downloadDocument(parseInt(downloadUrl.split('/').slice(-2)[0]));
      const blob = new Blob([response]);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Download failed:', error);
      alert('Download failed. Please try again.');
    }
  };

  const handleViewDocument = (source: any) => {
    if (source.uploaded_file_id) {
      const viewerUrl = `${process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000'}/api/ai/pdf/${source.uploaded_file_id}/view/?page=${source.page_number || 1}`;
      window.open(viewerUrl, '_blank');
    }
  };

  if (!sources || sources.length === 0) return null;

  // Check if sources are strings (legacy format) or objects (new format)
  const isLegacyFormat = typeof sources[0] === 'string';

  if (isLegacyFormat) {
    // Legacy format - just display as strings
    return (
      <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
        <h4 className="text-sm font-semibold text-blue-900 mb-2 flex items-center">
          <FileText size={14} className="mr-1" />
          参考文献 ({sources.length})
        </h4>
        <div className="space-y-1">
          {sources.map((source, index) => (
            <div key={index} className="text-sm text-gray-700">
              • {source}
            </div>
          ))}
        </div>
      </div>
    );
  }

  // New format - display only the most relevant source (first one)
  const mostRelevantSource = sources[0];
  
  return (
    <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
      <h4 className="text-sm font-semibold text-blue-900 mb-2 flex items-center">
        <FileText size={14} className="mr-1" />
        最相关参考文献
      </h4>
      <div className="flex items-center justify-between p-2 bg-white rounded border">
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium text-gray-900 truncate">
            {mostRelevantSource.filename || mostRelevantSource.title || 'Document'}
          </div>
          <div className="text-xs text-gray-500">
            第 {mostRelevantSource.page_number || 'N/A'} 页, 块 {mostRelevantSource.chunk_index || 'N/A'}
            {mostRelevantSource.file_size && ` • ${(mostRelevantSource.file_size / 1024 / 1024).toFixed(2)} MB`}
          </div>
          {mostRelevantSource.content && (
            <div className="text-xs text-gray-600 mt-1 truncate max-w-md">
              {mostRelevantSource.content.length > 100 ? `${mostRelevantSource.content.substring(0, 100)}...` : mostRelevantSource.content}
            </div>
          )}
        </div>
        <div className="flex items-center gap-1 ml-2">
          {mostRelevantSource.uploaded_file_id && (
            <button
              onClick={() => handleViewDocument(mostRelevantSource)}
              className="p-1 text-blue-600 hover:text-blue-800 hover:bg-blue-100 rounded transition-colors"
              title="在查看器中打开文档"
            >
              <Eye size={14} />
            </button>
          )}
          {mostRelevantSource.download_url && (
            <button
              onClick={() => handleDownload(mostRelevantSource.download_url, mostRelevantSource.filename || mostRelevantSource.title || 'document')}
              className="p-1 text-blue-600 hover:text-blue-800 hover:bg-blue-100 rounded transition-colors"
              title="下载文档"
            >
              <Download size={14} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

const ChatAssistant: React.FC = () => {
  // Check authentication status
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      type: 'ai',
      content: 'Hello! I\'m your AI assistant. You can ask any question here — troubleshooting, system analysis, or anything from your knowledge library. Answers are AI-generated and may be incorrect or incomplete; please verify important information. How can I help you today?',
      timestamp: new Date().toISOString(),
      sources: ['System Manual v2.1.pdf', 'Troubleshooting Guide'],
    },
  ]);

  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showHistory, setShowHistory] = useState(true);
  
  // Chat history
  const [chatHistory, setChatHistory] = useState<Array<{ id: string; prompt: string; preview: string; timestamp: string }>>([]);

  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const [performanceStats, setPerformanceStats] = useState<any>(null);
  const [showPerformanceStats, setShowPerformanceStats] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    const token = localStorage.getItem(process.env.REACT_APP_JWT_STORAGE_KEY || 'anylab_token');
    setIsAuthenticated(!!token);
  }, []);

  // Show login prompt if not authenticated
  // Temporarily disabled for testing
  /*
  if (!isAuthenticated) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center p-8 bg-white rounded-lg shadow-md">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Authentication Required</h2>
          <p className="text-gray-600 mb-6">
            Please log in to use the AI Assistant features.
          </p>
          <button
            onClick={() => window.location.href = '/login'}
            className="btn-primary"
          >
            Go to Login
          </button>
        </div>
      </div>
    );
  }
  */

  // Storage keys
  const CHAT_HISTORY_STORAGE_KEY = 'anylab_chat_history';
  const CHAT_MESSAGES_STORAGE_KEY = 'anylab_chat_messages';

  // Load chat history and messages on component mount
  useEffect(() => {
    try {
      console.log('Loading chat history from localStorage...');
      
      // Load chat history
      const chatHistoryRaw = localStorage.getItem(CHAT_HISTORY_STORAGE_KEY);
      if (chatHistoryRaw) {
        const parsed = JSON.parse(chatHistoryRaw);
        if (Array.isArray(parsed)) {
          setChatHistory(parsed);
          console.log('Loaded chat history:', parsed.length, 'items');
        }
      }

      // Load chat messages
      const chatMessagesRaw = localStorage.getItem(CHAT_MESSAGES_STORAGE_KEY);
      if (chatMessagesRaw) {
        const parsed = JSON.parse(chatMessagesRaw);
        if (Array.isArray(parsed) && parsed.length > 0) {
          setMessages(parsed);
          console.log('Loaded chat messages:', parsed.length, 'items');
        }
      }
      
      console.log('Chat history loading completed');
    } catch (error) {
      console.error('Error loading chat history from localStorage:', error);
    }
  }, []);

  // Save chat history whenever it changes
  useEffect(() => {
    try {
      localStorage.setItem(CHAT_HISTORY_STORAGE_KEY, JSON.stringify(chatHistory));
      console.log('Saved chat history:', chatHistory.length, 'items');
    } catch (error) {
      console.error('Error saving chat history:', error);
    }
  }, [chatHistory]);

  // Save chat messages whenever they change
  useEffect(() => {
    try {
      localStorage.setItem(CHAT_MESSAGES_STORAGE_KEY, JSON.stringify(messages));
      console.log('Saved chat messages:', messages.length, 'items');
    } catch (error) {
      console.error('Error saving chat messages:', error);
    }
  }, [messages]);

  // Add a cleanup effect to ensure data is saved before component unmounts
  useEffect(() => {
    const handleBeforeUnload = () => {
      // Force save current state to localStorage
      try {
        localStorage.setItem(CHAT_HISTORY_STORAGE_KEY, JSON.stringify(chatHistory));
        localStorage.setItem(CHAT_MESSAGES_STORAGE_KEY, JSON.stringify(messages));
        console.log('Emergency save completed before unload');
      } catch (error) {
        console.error('Error during emergency save:', error);
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      // Also save on component unmount
      handleBeforeUnload();
    };
  }, [chatHistory, messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Fetch performance stats
  const fetchPerformanceStats = async () => {
    try {
      const response = await apiClient.getPerformanceStats();
      setPerformanceStats(response);
    } catch (error) {
      console.error('Failed to fetch performance stats:', error);
    }
  };

  useEffect(() => {
    if (showPerformanceStats) {
      fetchPerformanceStats();
    }
  }, [showPerformanceStats]);

  const handleSendMessage = useCallback(async () => {
    if (!inputMessage.trim()) return;

    const startTime = Date.now();
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = inputMessage;
    setInputMessage('');
    setIsLoading(true);

    // Create a placeholder AI message for streaming
    const aiMessageId = (Date.now() + 1).toString();
    const aiResponse: ChatMessage = {
      id: aiMessageId,
      type: 'ai',
      content: '',
      timestamp: new Date().toISOString(),
    };
    
    setMessages(prev => [...prev, aiResponse]);

    try {
      // Optimized parameters for faster response with Qwen 7B
      const res = await apiClient.chatWithOllama(currentInput, { 
        max_tokens: 512, // Limit tokens for faster response
        temperature: 0.3, // Lower temperature for more focused responses
        top_p: 0.9, // Add top_p for better quality/speed balance
        top_k: 40, // Add top_k for faster generation
        repeat_penalty: 1.1, // Prevent repetition
        num_ctx: 2048 // Smaller context for faster processing
      });
      
      const responseTime = Date.now() - startTime;
      console.log(`Response time: ${responseTime}ms`);
      
      // Update the AI message with the response
      setMessages(prev => prev.map(msg => 
        msg.id === aiMessageId 
          ? { ...msg, content: res.response || 'No response' }
          : msg
      ));
      
      // Record to chat history
      setChatHistory(prev => [
        {
          id: aiMessageId,
          prompt: currentInput,
          preview: (res.response || '').slice(0, 120),
          timestamp: aiResponse.timestamp,
        },
        ...prev
      ].slice(0, 50)); // Keep last 50 entries
    } catch (e) {
      console.error('Chat error:', e);
      const responseTime = Date.now() - startTime;
      console.log(`Error response time: ${responseTime}ms`);
      // Update the AI message with error
      setMessages(prev => prev.map(msg => 
        msg.id === aiMessageId 
          ? { ...msg, content: 'Sorry, I encountered an error. Please try again or check if the Ollama service is running.' }
          : msg
      ));
    } finally {
      setIsLoading(false);
    }
  }, [inputMessage]);



  // Get chat history
  const getCurrentHistory = () => {
    return chatHistory;
  };

  const handleComposerKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
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

  const clearCurrentHistory = () => {
    if (window.confirm('Are you sure you want to clear the chat history? This action cannot be undone.')) {
      setChatHistory([]);
      setMessages([{
        id: '1',
        type: 'ai',
        content: 'Hello! I\'m your AI assistant. You can ask any question here — troubleshooting, system analysis, or anything from your knowledge library. Answers are AI-generated and may be incorrect or incomplete; please verify important information. How can I help you today?',
        timestamp: new Date().toISOString(),
        sources: ['System Manual v2.1.pdf', 'Troubleshooting Guide'],
      }]);
    }
  };

  const clearAllHistory = () => {
    if (window.confirm('Are you sure you want to clear the chat history? This action cannot be undone.')) {
      setChatHistory([]);
      setMessages([{
        id: '1',
        type: 'ai',
        content: 'Hello! I\'m your AI assistant. You can ask any question here — troubleshooting, system analysis, or anything from your knowledge library. Answers are AI-generated and may be incorrect or incomplete; please verify important information. How can I help you today?',
        timestamp: new Date().toISOString(),
        sources: ['System Manual v2.1.pdf', 'Troubleshooting Guide'],
      }]);
    }
  };



  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <MessageSquare className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">Free AI Chat</h1>
              <p className="text-sm text-gray-500">Open conversation with Qwen 7B for brainstorming and general questions</p>
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
                Model: {performanceStats.ollama_model}
              </span>
              <span className="flex items-center">
                <FileText className="mr-1 h-4 w-4 text-blue-600" />
                Queries: {performanceStats.recent_queries?.total_queries || 0}
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
                  <MessageSquare className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">Start Free AI Chat</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Ask anything for open, GPT‑like conversation with Qwen 7B.
                  </p>
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                {messages.map((message) => (
                  <div key={message.id} className="flex space-x-4">
                    <div className={`flex-1 ${message.type === 'user' ? 'text-right' : 'text-left'}`}>
                      <div className={`inline-block max-w-3xl rounded-lg px-4 py-2 ${
                        message.type === 'user' 
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
                        
                        <p className={`text-xs mt-2 ${
                          message.type === 'user' ? 'text-blue-200' : 'text-gray-500'
                        }`}>
                          {new Date(message.timestamp).toLocaleString()}
                        </p>
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
                    <span className="text-gray-600">AI is thinking...</span>
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
                  onKeyPress={handleComposerKeyPress}
                  placeholder="Ask anything (Free AI Chat)..."
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  rows={3}
                  disabled={isLoading}
                />
              </div>
              <button
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || isLoading}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Send className="h-5 w-5" />
              </button>
            </div>
            
            <div className="mt-3 text-xs text-gray-500">
              Free AI Chat provides open conversation without document search. For document-based answers, try Basic, Advanced, or Comprehensive RAG.
            </div>
          </div>
        </div>

        {/* History Sidebar */}
        {showHistory && (
          <div className="w-80 bg-white border-l border-gray-200 flex flex-col">
            <div className="p-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">Chat History</h3>
                <button
                  onClick={clearCurrentHistory}
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
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No chat history</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Your conversations will appear here.
                  </p>
                </div>
              ) : (
                <div className="space-y-2">
                  {chatHistory.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => {
                        // Load from history functionality can be added here
                        setInputMessage(item.prompt);
                      }}
                      className="w-full text-left p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
                    >
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {item.prompt}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        {new Date(item.timestamp).toLocaleString()}
                      </p>
                    </button>
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

export default ChatAssistant; 