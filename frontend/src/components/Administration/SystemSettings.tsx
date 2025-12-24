import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
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
  Loader,
  RefreshCw
} from 'lucide-react';
import { apiClient } from '../../services/api';

const SystemSettings: React.FC = () => {
  const { t } = useTranslation('admin');
  const [activeTab, setActiveTab] = useState('general');
  const [settings, setSettings] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<Record<string, any>>({});
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
  const [editingModel, setEditingModel] = useState(false);
  const [modelValue, setModelValue] = useState('');
  const [saving, setSaving] = useState(false);
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);

  useEffect(() => {
    loadSettings();
    loadAvailableModels();
  }, []);

  const loadAvailableModels = async () => {
    setLoadingModels(true);
    try {
      const models = await apiClient.getAvailableModels();
      setAvailableModels(models);
    } catch (error) {
      console.error('Failed to load available models:', error);
      setAvailableModels([]);
    } finally {
      setLoadingModels(false);
    }
  };

  const loadSettings = async () => {
    try {
      const data = await apiClient.getSystemSettings();
      setSettings(data);
      if (data?.rag?.model) {
        setModelValue(data.rag.model);
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
      setMessage({ type: 'error', text: t('failedToLoadSystemSettings') });
    } finally {
      setLoading(false);
    }
  };

  const handleSaveModel = async () => {
    if (!modelValue.trim()) {
      setMessage({ type: 'error', text: 'Model name cannot be empty' });
      return;
    }

    setSaving(true);
    try {
      await apiClient.updateSystemSettings({
        rag: { model: modelValue.trim() }
      });
      setEditingModel(false);
      setMessage({ type: 'success', text: `Ollama model updated to ${modelValue.trim()}` });
      // Reload settings to get updated values
      await loadSettings();
    } catch (error: any) {
      setMessage({ type: 'error', text: error?.message || 'Failed to update model' });
    } finally {
      setSaving(false);
    }
  };

  const testConnection = async (type: 'ollama' | 'redis' | 'neo4j') => {
    setTesting(type);
    setTestResults((prev: Record<string, any>) => ({ ...prev, [type]: null }));
    try {
      const payload = type === 'neo4j' ? (settings?.neo4j || settings?.graph?.neo4j || {}) : (settings?.rag || settings?.cache || {});
      const result = await apiClient.testConnection(type, payload);
      setTestResults((prev: Record<string, any>) => ({ ...prev, [type]: result }));
      setMessage({ type: result.ok ? 'success' : 'error', text: result.ok ? t('connectionSuccessful') : result.error });
    } catch (error: any) {
      setTestResults((prev: Record<string, any>) => ({ ...prev, [type]: { ok: false, error: error.message } }));
      setMessage({ type: 'error', text: t('connectionTestFailed') });
    } finally {
      setTesting(null);
    }
  };

  const tabs = [
    { id: 'general', label: t('general'), icon: Settings },
    { id: 'upload', label: t('fileUpload'), icon: FileText },
    { id: 'embed', label: t('embeddings'), icon: Database },
    { id: 'rag', label: t('rag'), icon: Sparkles },
    { id: 'cache', label: t('cache'), icon: Network },
    { id: 'workers', label: t('workers'), icon: Server },
    { id: 'security', label: t('security'), icon: Shield },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader className="animate-spin text-primary-600" size={32} />
      </div>
    );
  }

  const renderSetting = (label: string, value: any, description?: string, testType?: 'ollama' | 'redis' | 'neo4j') => (
    <div className="mb-6">
      <label className="block text-sm font-medium text-gray-700 mb-2">{label}</label>
      {typeof value === 'boolean' ? (
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600">{value ? t('enabled') : t('disabled')}</span>
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
          className={`mt-2 px-3 py-1 text-sm rounded disabled:opacity-50 ${testType === 'neo4j' ? 'bg-green-100 hover:bg-green-200' : 'bg-primary-100 hover:bg-primary-200'}`}
        >
          {testing === testType ? (
            <Loader className="inline animate-spin mr-2" size={14} />
          ) : (
            <Network className="inline mr-2" size={14} />
          )}
          {t('testConnection')}
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
          {testResults[testType!].ok ? t('connected') : testResults[testType!].error || t('failed')}
        </div>
      )}
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{t('systemSettings')}</h1>
        <p className="text-gray-600">{t('configureSystemParametersAndConnections')}</p>
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
            <h2 className="text-lg font-semibold mb-4">{t('generalSettings')}</h2>
            {renderSetting(t('debugMode'), settings.app.debug, t('shouldBeDisabledInProduction'))}
            {renderSetting(t('allowedHosts'), settings.app.allowed_hosts)}
            {renderSetting(t('staticUrl'), settings.app.static_url)}
            {renderSetting(t('mediaUrl'), settings.app.media_url)}
          </div>
        )}

        {activeTab === 'upload' && settings?.file_upload && (
          <div>
            <h2 className="text-lg font-semibold mb-4">{t('fileUploadSettings')}</h2>
            {renderSetting(t('maxFileSize'), `${settings.file_upload.max_file_size / (1024 * 1024)} MB`)}
            {renderSetting(t('allowedExtensions'), settings.file_upload.allowed_extensions)}
            {renderSetting(t('asyncProcessing'), settings.file_upload.enable_async_processing)}
          </div>
        )}

        {activeTab === 'embed' && settings?.embeddings && (
          <div>
            <h2 className="text-lg font-semibold mb-4">{t('embeddingSettings')}</h2>
            {renderSetting(t('mode'), settings.embeddings.mode)}
            {renderSetting(t('offlineOnly'), settings.embeddings.offline_only)}
            {renderSetting(t('modelName'), settings.embeddings.model_name)}
            {renderSetting(t('fallbackModel'), settings.embeddings.fallback_model)}
            {renderSetting(t('dimension'), settings.embeddings.dimension)}
            {renderSetting(t('cacheTtlSeconds'), settings.embeddings.cache_ttl)}
          </div>
        )}

          {activeTab === 'rag' && settings?.rag && (
          <div>
            <h2 className="text-lg font-semibold mb-4">{t('ragAndGraphSettings')}</h2>
            {renderSetting(t('ollamaUrl'), settings.rag.ollama_url, undefined, 'ollama')}
            
            {/* AI Mode Integration Info */}
            {settings.rag.ai_mode && (
              <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-blue-900">
                      Current AI Mode: <span className="capitalize">{settings.rag.ai_mode}</span>
                    </p>
                    <p className="text-xs text-blue-700 mt-1">
                      Switch AI mode from the top bar to automatically change the model. 
<<<<<<< Updated upstream
                      Performance mode uses {settings.rag.recommended_models?.performance || 'qwen2.5:7b'}, 
                      Lightweight mode uses {settings.rag.recommended_models?.lightweight || 'qwen2:2b'}.
=======
                      Performance mode uses a more capable model, 
                      Lightweight mode uses a faster, smaller model.
>>>>>>> Stashed changes
                    </p>
                  </div>
                </div>
              </div>
            )}
            
            {/* Editable Model Field */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('model')} {settings.rag.ai_mode && <span className="text-xs text-gray-500">(Current: {settings.rag.model})</span>}
              </label>
              {editingModel ? (
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    {loadingModels ? (
                      <div className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm bg-gray-50 flex items-center">
                        <Loader className="animate-spin mr-2" size={14} />
                        <span className="text-gray-500">Loading models...</span>
                      </div>
                    ) : (
                      <div className="flex-1 flex items-center space-x-2">
                        <select
                          value={modelValue}
                          onChange={(e) => setModelValue(e.target.value)}
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
                          disabled={saving || availableModels.length === 0}
                        >
                          {availableModels.length === 0 ? (
                            <option value="">No models available (check Ollama connection)</option>
                          ) : (
                            <>
                              <option value="">Select a model...</option>
                              {availableModels.map((model) => (
                                <option key={model} value={model}>
                                  {model}
                                </option>
                              ))}
                            </>
                          )}
                        </select>
                        <button
                          onClick={loadAvailableModels}
                          disabled={loadingModels}
                          className="p-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
                          title="Refresh models list"
                        >
                          <RefreshCw className={`w-4 h-4 text-gray-600 ${loadingModels ? 'animate-spin' : ''}`} />
                        </button>
                      </div>
                    )}
                    <button
                      onClick={handleSaveModel}
                      disabled={saving || !modelValue.trim() || availableModels.length === 0}
                      className="px-4 py-2 bg-primary-600 text-white rounded-md text-sm hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {saving ? <Loader className="inline animate-spin mr-2" size={14} /> : null}
                      {saving ? 'Saving...' : 'Save'}
                    </button>
                    <button
                      onClick={() => {
                        setEditingModel(false);
                        setModelValue(settings.rag.model);
                      }}
                      disabled={saving}
                      className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md text-sm hover:bg-gray-300 disabled:opacity-50"
                    >
                      Cancel
                    </button>
                  </div>
                  {settings.rag.recommended_models && availableModels.length > 0 && (
                    <div className="flex items-center space-x-4 text-xs text-gray-600">
                      <span>Quick select:</span>
                      {availableModels.includes(settings.rag.recommended_models.performance) && (
                        <button
                          onClick={() => setModelValue(settings.rag.recommended_models.performance)}
                          className="px-2 py-1 bg-purple-100 text-purple-700 rounded hover:bg-purple-200"
                        >
                          Performance ({settings.rag.recommended_models.performance})
                        </button>
                      )}
                      {availableModels.includes(settings.rag.recommended_models.lightweight) && (
                        <button
                          onClick={() => setModelValue(settings.rag.recommended_models.lightweight)}
                          className="px-2 py-1 bg-green-100 text-green-700 rounded hover:bg-green-200"
                        >
                          Lightweight ({settings.rag.recommended_models.lightweight})
                        </button>
                      )}
                    </div>
                  )}
                  {availableModels.length === 0 && !loadingModels && (
                    <p className="text-xs text-red-600">
                      Could not load models from Ollama. Please check if Ollama is running and accessible.
                    </p>
                  )}
                </div>
              ) : (
                <div className="flex items-center space-x-2">
                  <p className="text-sm text-gray-900 bg-gray-50 p-2 rounded flex-1">{settings.rag.model}</p>
                  <button
                    onClick={() => {
                      setEditingModel(true);
                      setModelValue(settings.rag.model);
                    }}
                    className="px-3 py-2 bg-primary-100 text-primary-700 rounded-md text-sm hover:bg-primary-200"
                  >
                    <Wrench size={14} className="inline mr-1" />
                    Edit
                  </button>
                </div>
              )}
              <p className="text-xs text-gray-500 mt-1">
                Change the Ollama model used for RAG queries. Switch AI mode from the top bar to automatically change models.
              </p>
            </div>
            
            {renderSetting(t('requestTimeout'), `${settings.rag.request_timeout}s`)}
            {renderSetting(t('contextSize'), settings.rag.num_ctx)}
            {renderSetting(t('maxTokens'), settings.rag.max_tokens)}
            {renderSetting(t('temperature'), settings.rag.temperature)}

            {/* Graph RAG */}
            {settings.graph && (
              <div className="mt-6 pt-4 border-t border-gray-200">
                {renderSetting(t('graphRagEnabled'), settings.graph.enabled ?? true, t('enableHybridVectorGraphRetrieval'))}
                {renderSetting(t('graphDepth'), settings.graph.depth ?? 2, t('traversalDepthForRelationships'))}
                {renderSetting(t('maxGraphNodes'), settings.graph.max_nodes ?? 50, t('limitNodesInVisualizationQueries'))}
              </div>
            )}

            {/* Neo4j */}
            {settings.neo4j && (
              <div className="mt-6 pt-4 border-t border-gray-200">
                <h3 className="text-md font-semibold mb-2">Neo4j</h3>
                {renderSetting(t('boltUri'), settings.neo4j.uri)}
                {renderSetting(t('database'), settings.neo4j.database || 'neo4j')}
                {renderSetting(t('user'), settings.neo4j.user || 'neo4j')}
                {renderSetting(t('testConnection'), t('clickToTest'), undefined, 'neo4j')}
              </div>
            )}
          </div>
        )}

        {activeTab === 'cache' && settings?.cache && (
          <div>
            <h2 className="text-lg font-semibold mb-4">{t('cacheSettings')}</h2>
            {renderSetting(t('defaultTimeout'), `${settings.cache.default_timeout}s`)}
            {renderSetting(t('searchCacheTtl'), `${settings.cache.search_cache_ttl}s`)}
            {renderSetting(t('responseCacheTtl'), `${settings.cache.response_cache_ttl}s`)}
            {renderSetting(t('redisUrl'), settings.cache.redis_url, undefined, 'redis')}
          </div>
        )}

        {activeTab === 'workers' && settings?.workers && (
          <div>
            <h2 className="text-lg font-semibold mb-4">{t('workerSettings')}</h2>
            {renderSetting(t('brokerUrl'), settings.workers.broker_url)}
            {renderSetting(t('resultBackend'), settings.workers.result_backend)}
            {renderSetting(t('concurrency'), settings.workers.concurrency || t('auto'))}
          </div>
        )}

        {activeTab === 'security' && settings?.security && (
          <div>
            <h2 className="text-lg font-semibold mb-4">{t('securitySettings')}</h2>
            {renderSetting(t('corsAllowedOrigins'), settings.security.cors_allowed_origins)}
            {renderSetting(t('corsAllowCredentials'), settings.security.cors_allow_credentials)}
            {renderSetting(t('xFrameOptions'), settings.security.x_frame_options)}
          </div>
        )}
      </div>

      {/* Note */}
      <div className="bg-primary-50 border border-primary-200 rounded-lg p-4">
        <p className="text-sm text-primary-800">
          <strong>{t('note')}:</strong> {t('settingsReadOnlyNote')}
        </p>
      </div>
    </div>
  );
};

export default SystemSettings;

