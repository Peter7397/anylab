import React, { useState, useEffect } from 'react';
import {
  Settings,
  Server,
  Database,
  FileText,
  Sparkles,
  Network,
  Shield,
  Wrench,
  CheckCircle,
  XCircle,
  Loader
} from 'lucide-react';
import { apiClient } from '../../services/api';

const SystemSettings: React.FC = () => {
  const [activeTab, setActiveTab] = useState('general');
  const [settings, setSettings] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<any>({});
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const data = await apiClient.getSystemSettings();
      setSettings(data);
    } catch (error) {
      console.error('Failed to load settings:', error);
      setMessage({ type: 'error', text: 'Failed to load system settings' });
    } finally {
      setLoading(false);
    }
  };

  const testConnection = async (type: 'ollama' | 'redis') => {
    setTesting(type);
    setTestResults(prev => ({ ...prev, [type]: null }));
    try {
      const result = await apiClient.testConnection(type, settings?.rag || settings?.cache || {});
      setTestResults(prev => ({ ...prev, [type]: result }));
      setMessage({ type: result.ok ? 'success' : 'error', text: result.ok ? 'Connection successful' : result.error });
    } catch (error: any) {
      setTestResults(prev => ({ ...prev, [type]: { ok: false, error: error.message } }));
      setMessage({ type: 'error', text: 'Connection test failed' });
    } finally {
      setTesting(null);
    }
  };

  const tabs = [
    { id: 'general', label: 'General', icon: Settings },
    { id: 'upload', label: 'File Upload', icon: FileText },
    { id: 'embed', label: 'Embeddings', icon: Database },
    { id: 'rag', label: 'RAG', icon: Sparkles },
    { id: 'cache', label: 'Cache', icon: Network },
    { id: 'workers', label: 'Workers', icon: Server },
    { id: 'security', label: 'Security', icon: Shield },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader className="animate-spin text-primary-600" size={32} />
      </div>
    );
  }

  const renderSetting = (label: string, value: any, description?: string, testType?: 'ollama' | 'redis') => (
    <div className="mb-6">
      <label className="block text-sm font-medium text-gray-700 mb-2">{label}</label>
      {typeof value === 'boolean' ? (
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600">{value ? 'Enabled' : 'Disabled'}</span>
        </div>
      ) : Array.isArray(value) ? (
        <div className="flex flex-wrap gap-2">
          {value.map((item: string, i: number) => (
            <span key={i} className="px-2 py-1 bg-gray-100 rounded text-sm">{item}</span>
          ))}
        </div>
      ) : typeof value === 'object' && value !== null ? (
        <div className="bg-gray-50 p-3 rounded text-sm">
          <pre className="whitespace-pre-wrap break-words">{JSON.stringify(value, null, 2)}</pre>
        </div>
      ) : (
        <p className="text-sm text-gray-900 bg-gray-50 p-2 rounded">{String(value)}</p>
      )}
      {description && <p className="text-xs text-gray-500 mt-1">{description}</p>}
      {testType && (
        <button
          onClick={() => testConnection(testType)}
          disabled={testing === testType}
          className="mt-2 px-3 py-1 text-sm bg-blue-100 hover:bg-blue-200 rounded disabled:opacity-50"
        >
          {testing === testType ? (
            <Loader className="inline animate-spin mr-2" size={14} />
          ) : (
            <Network className="inline mr-2" size={14} />
          )}
          Test Connection
        </button>
      )}
      {testResults[testType!] && (
        <div className={`mt-2 flex items-center text-sm ${
          testResults[testType!].ok ? 'text-green-600' : 'text-red-600'
        }`}>
          {testResults[testType!].ok ? (
            <CheckCircle size={16} className="mr-1" />
          ) : (
            <XCircle size={16} className="mr-1" />
          )}
          {testResults[testType!].ok ? 'Connected' : testResults[testType!].error || 'Failed'}
        </div>
      )}
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">System Settings</h1>
        <p className="text-gray-600">Configure system parameters and connections</p>
      </div>

      {/* Message */}
      {message && (
        <div className={`p-4 rounded ${message.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>
          {message.text}
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon size={18} className="mr-2" />
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Content */}
      <div className="bg-white rounded-lg border p-6">
        {activeTab === 'general' && settings?.app && (
          <div>
            <h2 className="text-lg font-semibold mb-4">General Settings</h2>
            {renderSetting('Debug Mode', settings.app.debug, 'Should be disabled in production')}
            {renderSetting('Allowed Hosts', settings.app.allowed_hosts)}
            {renderSetting('Static URL', settings.app.static_url)}
            {renderSetting('Media URL', settings.app.media_url)}
          </div>
        )}

        {activeTab === 'upload' && settings?.file_upload && (
          <div>
            <h2 className="text-lg font-semibold mb-4">File Upload Settings</h2>
            {renderSetting('Max File Size', `${settings.file_upload.max_file_size / (1024 * 1024)} MB`)}
            {renderSetting('Allowed Extensions', settings.file_upload.allowed_extensions)}
            {renderSetting('Async Processing', settings.file_upload.enable_async_processing)}
          </div>
        )}

        {activeTab === 'embed' && settings?.embeddings && (
          <div>
            <h2 className="text-lg font-semibold mb-4">Embedding Settings</h2>
            {renderSetting('Mode', settings.embeddings.mode)}
            {renderSetting('Offline Only', settings.embeddings.offline_only)}
            {renderSetting('Model Name', settings.embeddings.model_name)}
            {renderSetting('Fallback Model', settings.embeddings.fallback_model)}
            {renderSetting('Dimension', settings.embeddings.dimension)}
            {renderSetting('Cache TTL (seconds)', settings.embeddings.cache_ttl)}
          </div>
        )}

        {activeTab === 'rag' && settings?.rag && (
          <div>
            <h2 className="text-lg font-semibold mb-4">RAG Settings</h2>
            {renderSetting('Ollama URL', settings.rag.ollama_url, undefined, 'ollama')}
            {renderSetting('Model', settings.rag.model)}
            {renderSetting('Request Timeout', `${settings.rag.request_timeout}s`)}
            {renderSetting('Context Size', settings.rag.num_ctx)}
            {renderSetting('Max Tokens', settings.rag.max_tokens)}
            {renderSetting('Temperature', settings.rag.temperature)}
          </div>
        )}

        {activeTab === 'cache' && settings?.cache && (
          <div>
            <h2 className="text-lg font-semibold mb-4">Cache Settings</h2>
            {renderSetting('Default Timeout', `${settings.cache.default_timeout}s`)}
            {renderSetting('Search Cache TTL', `${settings.cache.search_cache_ttl}s`)}
            {renderSetting('Response Cache TTL', `${settings.cache.response_cache_ttl}s`)}
            {renderSetting('Redis URL', settings.cache.redis_url, undefined, 'redis')}
          </div>
        )}

        {activeTab === 'workers' && settings?.workers && (
          <div>
            <h2 className="text-lg font-semibold mb-4">Worker Settings</h2>
            {renderSetting('Broker URL', settings.workers.broker_url)}
            {renderSetting('Result Backend', settings.workers.result_backend)}
            {renderSetting('Concurrency', settings.workers.concurrency || 'Auto')}
          </div>
        )}

        {activeTab === 'security' && settings?.security && (
          <div>
            <h2 className="text-lg font-semibold mb-4">Security Settings</h2>
            {renderSetting('CORS Allowed Origins', settings.security.cors_allowed_origins)}
            {renderSetting('CORS Allow Credentials', settings.security.cors_allow_credentials)}
            {renderSetting('X-Frame-Options', settings.security.x_frame_options)}
          </div>
        )}
      </div>

      {/* Note */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          <strong>Note:</strong> Settings are read-only in this implementation. To modify settings, edit the backend configuration files or environment variables.
        </p>
      </div>
    </div>
  );
};

export default SystemSettings;

