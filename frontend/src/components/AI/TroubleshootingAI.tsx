import React, { useState, useEffect, useRef } from 'react';
import { 
  Upload, 
  Send, 
  FileText, 
  X, 
  Copy, 
  Check, 
  Loader2, 
  AlertCircle,
  History,
  Trash2,
  FileCode,
  CheckCircle2
} from 'lucide-react';
import { apiClient } from '../../services/api';

interface TroubleshootingAIProps {
  onOpenInViewer?: (args: { id: string; title: string; url: string; type: 'pdf'|'docx'|'txt'|'xls'|'xlsx'|'ppt'|'pptx' }) => void;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  logContent?: string;
  suggestions?: string[];
}

const TROUBLESHOOTING_HISTORY_STORAGE_KEY = 'troubleshooting_history';
const TROUBLESHOOTING_MESSAGES_STORAGE_KEY = 'troubleshooting_messages';

const TroubleshootingAI: React.FC<TroubleshootingAIProps> = ({ onOpenInViewer }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const [chatHistory, setChatHistory] = useState<Array<{ 
    id: string; 
    prompt: string; 
    preview: string; 
    timestamp: string;
    response?: string;
    logContent?: string;
    suggestions?: string[];
  }>>([]);
  const [showHistory, setShowHistory] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load saved messages and history on component mount
  useEffect(() => {
    const savedMessages = localStorage.getItem(TROUBLESHOOTING_MESSAGES_STORAGE_KEY);
    const savedHistory = localStorage.getItem(TROUBLESHOOTING_HISTORY_STORAGE_KEY);
    
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
    localStorage.setItem(TROUBLESHOOTING_MESSAGES_STORAGE_KEY, JSON.stringify(messages));
  }, [messages]);

  useEffect(() => {
    localStorage.setItem(TROUBLESHOOTING_HISTORY_STORAGE_KEY, JSON.stringify(chatHistory));
  }, [chatHistory]);

  // Auto-scroll to bottom when new messages are added
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadedFile(file);
    }
  };

  const removeFile = () => {
    setUploadedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSend = async () => {
    const currentQuery = inputMessage.trim() || 'Please analyze this log file';
    if (!currentQuery && !uploadedFile) return;
    if (isLoading) return;

    const messageId = Date.now().toString();
    setIsLoading(true);

    try {
      // Read file content if file is uploaded
      let logContent = '';
      if (uploadedFile) {
        logContent = await uploadedFile.text();
      }

      // Add user message
      const userMessage: Message = {
        id: messageId,
        role: 'user',
        content: currentQuery,
        timestamp: new Date().toISOString(),
        logContent: logContent || undefined
      };

      setMessages(prev => [...prev, userMessage]);
      
      // Add to history
      const historyItem = {
        id: messageId,
        prompt: currentQuery,
        preview: logContent ? `Log file: ${uploadedFile?.name}` : currentQuery,
        timestamp: new Date().toISOString()
      };
      setChatHistory(prev => [historyItem, ...prev.slice(0, 9)]); // Keep last 10

      // Clear inputs
      setInputMessage('');
      setUploadedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }

      // Call API to analyze logs
      const response = await apiClient.analyzeLogs({
        query: currentQuery,
        log_content: logContent
      });

      // Add assistant response
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.analysis || 'No analysis provided',
        timestamp: new Date().toISOString(),
        suggestions: response.suggestions || []
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Update history with response
      setChatHistory(prev => prev.map(item => 
        item.id === messageId 
          ? { ...item, response: response.analysis, logContent: logContent, suggestions: response.suggestions }
          : item
      ));

    } catch (error) {
      console.error('Troubleshooting error:', error);
      
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: 'Failed to analyze log file. Please try again.',
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
      handleSend();
    }
  };

  const copyToClipboard = async (text: string, messageId: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedMessageId(messageId);
      setTimeout(() => setCopiedMessageId(null), 2000);
    } catch (error) {
      console.error('Copy failed:', error);
    }
  };

  const formatMessage = (text: string) => {
    // Convert markdown to HTML
    let formatted = text
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      .replace(/`(.+?)`/g, '<code class="bg-gray-100 px-1 rounded">$1</code>')
      .replace(/^#\s+(.+)$/gm, '<h3 class="font-bold text-lg mt-2 mb-1">$1</h3>')
      .replace(/^##\s+(.+)$/gm, '<h4 class="font-semibold text-base mt-1 mb-1">$1</h4>')
      .replace(/^(\d+)\.\s+(.+)$/gm, '<div class="ml-4 mb-1"><span class="font-medium">$1.</span> $2</div>')
      .replace(/^[-*]\s+(.+)$/gm, '<div class="ml-4 mb-1">• $1</div>')
      .replace(/\n/g, '<br>');
    
    return formatted;
  };

  const loadFromHistory = (historyItem: { id: string; prompt: string; preview: string; timestamp: string }) => {
    setInputMessage(historyItem.prompt);
    setShowHistory(false);
  };

  const clearHistory = () => {
    setChatHistory([]);
    setMessages([]);
    localStorage.removeItem(TROUBLESHOOTING_HISTORY_STORAGE_KEY);
    localStorage.removeItem(TROUBLESHOOTING_MESSAGES_STORAGE_KEY);
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-orange-100 rounded-lg">
              <AlertCircle className="h-6 w-6 text-orange-600" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">Troubleshooting AI</h1>
              <p className="text-sm text-gray-500">AI-powered log analysis and troubleshooting</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {/* History Toggle Button */}
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              title={showHistory ? "Hide History" : "Show History"}
            >
              <History className="h-5 w-5" />
            </button>

            {/* Clear History Button */}
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
                <FileCode className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">Troubleshooting AI</h3>
                <p className="text-gray-600 mb-6 max-w-md mx-auto">
                  Upload log files to get AI-powered troubleshooting suggestions and diagnostic insights.
                </p>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 max-w-md mx-auto text-left">
                  <p className="text-sm text-blue-800 font-medium mb-2">Supported Log Types:</p>
                  <ul className="text-sm text-blue-700 space-y-1">
                    <li>• Application logs (.log, .txt)</li>
                    <li>• Error logs</li>
                    <li>• System logs</li>
                    <li>• Debug output</li>
                  </ul>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-3xl rounded-lg p-4 ${
                        message.role === 'user'
                          ? 'bg-blue-600 text-white'
                          : 'bg-white border border-gray-200'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          {message.logContent && (
                            <div className={`mb-3 p-3 rounded ${message.role === 'user' ? 'bg-blue-700' : 'bg-gray-50'}`}>
                              <div className={`text-xs font-medium mb-1 ${message.role === 'user' ? 'text-blue-200' : 'text-gray-600'}`}>
                                Log File Content:
                              </div>
                              <pre className={`text-xs overflow-auto max-h-40 ${message.role === 'user' ? 'text-blue-100' : 'text-gray-700'}`}>
                                {message.logContent.substring(0, 500)}
                                {message.logContent.length > 500 && '...'}
                              </pre>
                            </div>
                          )}
                          
                          <div
                            className={`text-sm ${
                              message.role === 'user' ? 'text-white' : 'text-gray-700'
                            }`}
                            dangerouslySetInnerHTML={{ __html: formatMessage(message.content) }}
                          />

                          {message.suggestions && message.suggestions.length > 0 && (
                            <div className="mt-4 pt-4 border-t border-gray-200">
                              <div className="flex items-center mb-3">
                                <CheckCircle2 size={16} className="text-green-600 mr-2" />
                                <span className="text-sm font-semibold text-gray-900">Suggested Solutions:</span>
                              </div>
                              <ol className="list-decimal list-inside space-y-2">
                                {message.suggestions.map((suggestion, index) => (
                                  <li key={index} className="text-sm text-gray-700 ml-2">
                                    {suggestion}
                                  </li>
                                ))}
                              </ol>
                            </div>
                          )}
                        </div>

                        <button
                          onClick={() => copyToClipboard(message.content, message.id)}
                          className={`ml-2 p-1 rounded ${message.role === 'user' ? 'hover:bg-blue-700' : 'hover:bg-gray-100'}`}
                          title="Copy message"
                        >
                          {copiedMessageId === message.id ? (
                            <Check className="h-4 w-4 text-green-600" />
                          ) : (
                            <Copy className={`h-4 w-4 ${message.role === 'user' ? 'text-white' : 'text-gray-600'}`} />
                          )}
                        </button>
                      </div>
                      
                      <p className={`text-xs mt-2 ${
                        message.role === 'user' ? 'text-blue-200' : 'text-gray-500'
                      }`}>
                        {new Date(message.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </div>
                ))}

                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-white border border-gray-200 rounded-lg px-4 py-3">
                      <div className="flex items-center space-x-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-orange-600"></div>
                        <span className="text-gray-600">Analyzing log file...</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="bg-white border-t border-gray-200 p-6">
            {/* File Upload Indicator */}
            {uploadedFile && (
              <div className="mb-3 flex items-center justify-between bg-blue-50 border border-blue-200 rounded-lg p-3">
                <div className="flex items-center space-x-2">
                  <FileText size={16} className="text-blue-600" />
                  <span className="text-sm text-blue-900 font-medium">{uploadedFile.name}</span>
                  <span className="text-xs text-blue-600">
                    ({(uploadedFile.size / 1024).toFixed(1)} KB)
                  </span>
                </div>
                <button
                  onClick={removeFile}
                  className="p-1 hover:bg-blue-100 rounded"
                >
                  <X size={16} className="text-blue-600" />
                </button>
              </div>
            )}

            <div className="flex items-end space-x-3">
              {/* File Upload Button */}
              <button
                onClick={() => fileInputRef.current?.click()}
                className="p-3 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors border border-gray-300"
                title="Upload log file"
              >
                <Upload size={20} className="text-gray-600" />
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".log,.txt,.err"
                onChange={handleFileUpload}
                className="hidden"
              />

              {/* Text Input */}
              <div className="flex-1">
                <textarea
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Describe your issue or ask questions about the log file..."
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent resize-none"
                  rows={3}
                  disabled={isLoading}
                />
              </div>

              {/* Send Button */}
              <button
                onClick={handleSend}
                disabled={isLoading || (!inputMessage.trim() && !uploadedFile)}
                className="px-6 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Send className="h-5 w-5" />
              </button>
            </div>
            
            <div className="mt-3 text-xs text-gray-500">
              Upload a log file or describe your issue, and AI will provide troubleshooting suggestions
            </div>
          </div>
        </div>

        {/* History Sidebar */}
        {showHistory && (
          <div className="w-80 bg-white border-l border-gray-200 flex flex-col">
            <div className="p-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">Troubleshooting History</h3>
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
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No troubleshooting history</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Your troubleshooting sessions will appear here.
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
                            className="text-sm font-medium text-gray-900 hover:text-orange-600 transition-colors text-left"
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
                              // Load full conversation from history
                              const newMessages: Message[] = [
                                {
                                  id: item.id,
                                  role: 'user',
                                  content: item.prompt,
                                  timestamp: item.timestamp,
                                  logContent: item.logContent
                                },
                                {
                                  id: (parseInt(item.id) + 1).toString(),
                                  role: 'assistant',
                                  content: item.response || '',
                                  timestamp: item.timestamp,
                                  suggestions: item.suggestions
                                }
                              ];
                              setMessages(newMessages);
                              setShowHistory(false);
                            }}
                            className="ml-2 px-2 py-1 text-xs bg-orange-100 text-orange-700 rounded hover:bg-orange-200 transition-colors"
                          >
                            Load
                          </button>
                        )}
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

export default TroubleshootingAI;
