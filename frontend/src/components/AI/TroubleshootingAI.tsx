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
  CheckCircle
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { apiClient } from '../../services/api';
import { useUnifiedChatHistory } from '../../hooks/useUnifiedChatHistory';

interface TroubleshootingAIProps {
  onOpenInViewer?: (args: { id: string; title: string; url: string; type: 'pdf'|'docx'|'txt'|'xls'|'xlsx'|'ppt'|'pptx'|'html' }) => void;
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
  const { t } = useTranslation('ai');
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
  const { history: unifiedHistory, recordUserPrompt, refresh: refreshUnifiedHistory } = useUnifiedChatHistory(200);
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

  // Cross-post receiver for Troubleshooting
  useEffect(() => {
    try {
      const raw = localStorage.getItem('anylab_cross_post');
      if (raw) {
        const payload = JSON.parse(raw);
        if (payload?.channel === 'troubleshooting' && typeof payload?.content === 'string') {
          localStorage.removeItem('anylab_cross_post');
          setInputMessage(payload.content);
          setTimeout(() => handleSend(), 0);
        }
      }
    } catch (_) {}
  }, []);

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
    const trimmed = inputMessage.trim();
    // If no text and no file, do nothing
    if (!trimmed && !uploadedFile) return;
    // If file only, provide a sensible default prompt
    const currentQuery = trimmed || (uploadedFile ? t('pleaseAnalyzeLogFile') : '');
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

      try { await recordUserPrompt('troubleshooting', currentQuery); } catch (e) { console.error('Failed to record unified history:', e); }
      
      // Add to history
      const historyItem = {
        id: messageId,
        prompt: currentQuery,
        preview: logContent ? `${t('logFile')}: ${uploadedFile?.name}` : currentQuery,
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
        content: response.analysis || t('noAnalysisProvided'),
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

    } catch (error: any) {
      console.error('Troubleshooting error:', error);
      const serverMessage = (error && error.message) ? String(error.message) : t('failedToAnalyzeLogFile');
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: serverMessage,
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
            <div className="p-2 bg-primary-100 rounded-lg">
              <AlertCircle className="h-6 w-6 text-primary-600" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">{t('troubleshooting')}</h1>
              <p className="text-sm text-gray-500">{t('aiPoweredLogAnalysis')}</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {/* History Toggle Button */}
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              title={showHistory ? t('hideHistory') : t('showHistory')}
            >
              <History className="h-5 w-5" />
            </button>

            {/* Clear History Button */}
            <button
              onClick={clearHistory}
              className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
              title={t('clearHistory')}
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
                <h3 className="text-lg font-medium text-gray-900 mb-2">{t('troubleshooting')}</h3>
                <p className="text-gray-600 mb-6 max-w-md mx-auto">
                  {t('uploadLogFilesDescription')}
                </p>
                <div className="bg-primary-50 border border-primary-200 rounded-lg p-4 max-w-md mx-auto text-left">
                  <p className="text-sm text-primary-800 font-medium mb-2">{t('supportedLogTypes')}:</p>
                  <ul className="text-sm text-primary-700 space-y-1">
                    <li>• {t('applicationLogs')}</li>
                    <li>• {t('errorLogs')}</li>
                    <li>• {t('systemLogs')}</li>
                    <li>• {t('debugOutput')}</li>
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
                          ? 'bg-primary-600 text-white'
                          : 'bg-white border border-gray-200'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          {message.logContent && (
                            <div className={`mb-3 p-3 rounded ${message.role === 'user' ? 'bg-primary-700' : 'bg-gray-50'}`}>
                              <div className={`text-xs font-medium mb-1 ${message.role === 'user' ? 'text-primary-200' : 'text-gray-600'}`}>
                                {t('logFileContent')}:
                              </div>
                              <pre className={`text-xs overflow-auto max-h-40 ${message.role === 'user' ? 'text-primary-100' : 'text-gray-700'}`}>
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
                                <CheckCircle size={16} className="text-green-600 mr-2" />
                                <span className="text-sm font-semibold text-gray-900">{t('suggestedSolutions')}:</span>
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
                              className={`text-xs border border-gray-300 rounded px-1 py-0.5 bg-white ${message.role === 'user' ? 'text-primary-800' : 'text-gray-600'}`}
                              defaultValue=""
                              title={t('askIn')}
                            >
                              <option value="">{t('askInPlaceholder')}</option>
                              <option value="chat">{t('freeChat')}</option>
                              <option value="rag_basic">{t('basicRag')}</option>
                              <option value="rag">{t('advancedRag')}</option>
                              <option value="rag_comprehensive">{t('comprehensiveRag')}</option>
                            </select>
                          )}
                          <button
                            onClick={() => copyToClipboard(message.content, message.id)}
                            className={`ml-2 p-1 rounded ${message.role === 'user' ? 'hover:bg-primary-700' : 'hover:bg-gray-100'}`}
                            title={t('copyMessage')}
                          >
                            {copiedMessageId === message.id ? (
                              <Check className="h-4 w-4 text-green-600" />
                            ) : (
                              <Copy className={`h-4 w-4 ${message.role === 'user' ? 'text-white' : 'text-gray-600'}`} />
                            )}
                          </button>
                        </div>
                      </div>
                      
                      <p className={`text-xs mt-2 ${
                        message.role === 'user' ? 'text-primary-200' : 'text-gray-500'
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
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600"></div>
                        <span className="text-gray-600">{t('analyzingLogFile')}</span>
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
              <div className="mb-3 flex items-center justify-between bg-primary-50 border border-primary-200 rounded-lg p-3">
                <div className="flex items-center space-x-2">
                  <FileText size={16} className="text-primary-600" />
                  <span className="text-sm text-primary-900 font-medium">{uploadedFile.name}</span>
                  <span className="text-xs text-primary-600">
                    ({(uploadedFile.size / 1024).toFixed(1)} KB)
                  </span>
                </div>
                <button
                  onClick={removeFile}
                  className="p-1 hover:bg-primary-100 rounded"
                >
                  <X size={16} className="text-primary-600" />
                </button>
              </div>
            )}

            <div className="flex items-end space-x-3">
              {/* File Upload Button */}
              <button
                onClick={() => fileInputRef.current?.click()}
                className="p-3 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors border border-gray-300"
                title={t('uploadLogFile')}
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
                  placeholder={t('describeIssueOrAskQuestions')}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                  rows={3}
                  disabled={isLoading}
                />
              </div>

              {/* Send Button */}
              <button
                onClick={handleSend}
                disabled={isLoading || (!inputMessage.trim() && !uploadedFile)}
                className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Send className="h-5 w-5" />
              </button>
            </div>
            
            <div className="mt-3 text-xs text-gray-500">
              {t('troubleshootingNote')}
            </div>
          </div>
        </div>

        {/* History Sidebar */}
        {showHistory && (
          <div className="w-80 bg-white border-l border-gray-200 flex flex-col">
            <div className="p-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">{t('troubleshootingHistory')}</h3>
                <button
                  onClick={() => refreshUnifiedHistory()}
                  className="text-sm text-primary-600 hover:text-primary-700"
                >
                  {t('refresh')}
                </button>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              {unifiedHistory.length === 0 ? (
                <div className="text-center py-8">
                  <History className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">{t('noTroubleshootingHistory')}</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    {t('troubleshootingSessionsWillAppear')}
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
                            className="text-sm font-medium text-gray-900 hover:text-primary-600 transition-colors text-left"
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

export default TroubleshootingAI;
