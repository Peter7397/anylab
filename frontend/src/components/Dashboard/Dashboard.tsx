import React, { useState, useEffect, useCallback, useRef } from 'react';
import { 
  Monitor, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  TrendingUp,
  Activity,
  FileText,
  MessageSquare,
  Database,
  Search,
  Loader,
  RefreshCw,
  Network,
  Sparkles,
  Tag,
  GitBranch,
  BarChart3
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { System } from '../../types';
import { apiClient } from '../../services/api';
import MetricsDashboard from './MetricsDashboard';

const Dashboard: React.FC = () => {
  const { t } = useTranslation(['dashboard', 'common']);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [activeView, setActiveView] = useState<'overview' | 'metrics'>('overview');
  const loadingRef = useRef(false);

  const loadDashboardData = useCallback(async () => {
    // Prevent concurrent calls
    if (loadingRef.current) {
      return;
    }

    loadingRef.current = true;
    try {
      const data = await apiClient.getDashboardStats();
      // Only update if data actually changed
      setStats((prevStats: any) => {
        if (JSON.stringify(prevStats) === JSON.stringify(data)) {
          return prevStats;
        }
        return data;
      });
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
      loadingRef.current = false;
    }
  }, []);

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(() => {
      loadDashboardData();
    }, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [loadDashboardData]);

  // Mock data - replace with actual API calls
  const mockSystems: System[] = [
    { id: '1', name: 'LAB-PC-001', ip: '192.168.1.101', os: 'Windows 10 Pro', lastLogin: '2024-01-15 09:30', status: 'online' },
    { id: '2', name: 'LAB-PC-002', ip: '192.168.1.102', os: 'Windows 11 Pro', lastLogin: '2024-01-15 08:45', status: 'online' },
    { id: '3', name: 'LAB-SERVER-01', ip: '192.168.1.10', os: 'Windows Server 2022', lastLogin: '2024-01-15 10:15', status: 'warning' },
    { id: '4', name: 'LAB-PC-003', ip: '192.168.1.103', os: 'Windows 10 Pro', lastLogin: '2024-01-14 16:20', status: 'offline' },
  ];

  // Use real stats if available, otherwise use mock
  const dashboardStats = stats ? [
    { name: t('totalDocuments'), value: stats.documents?.total || '0', icon: FileText, change: `+${stats.documents?.today || 0}`, changeType: stats.documents?.today > 0 ? 'positive' : 'neutral' },
    { name: t('chunksIndexed'), value: stats.chunks?.total || '0', icon: Database, change: `${stats.chunks?.with_embeddings || 0} ${t('embedded')}`, changeType: stats.chunks?.pending === 0 ? 'positive' : 'neutral' },
    { name: t('ragQueriesToday'), value: stats.rag_queries?.today || '0', icon: Search, change: `${stats.rag_queries?.total || 0} ${t('total')}`, changeType: stats.rag_queries?.today > 0 ? 'positive' : 'neutral' },
    { name: t('processingQueue'), value: (stats.processing_queue?.pending || 0) + (stats.processing_queue?.processing || 0), icon: Loader, change: stats.processing_queue?.failed ? `-${stats.processing_queue.failed} ${t('failed')}` : t('allClear'), changeType: stats.processing_queue?.failed > 0 ? 'negative' : 'positive' },
  ] : [
    { name: t('totalPcs'), value: '24', icon: Monitor, change: '+2', changeType: 'positive' },
    { name: t('issuesDetected'), value: '3', icon: AlertTriangle, change: '-1', changeType: 'negative' },
    { name: t('systemsOnline'), value: '21', icon: CheckCircle, change: '+1', changeType: 'positive' },
    { name: t('pendingMaintenance'), value: '5', icon: Clock, change: '+2', changeType: 'neutral' },
  ];



  if (loading && !stats) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader className="animate-spin text-primary-600" size={32} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('title')}</h1>
          <p className="text-gray-600">{t('subtitle')}</p>
        </div>
        <div className="flex space-x-3 items-center">
          <button onClick={loadDashboardData} className="btn-secondary">
            <RefreshCw size={16} className="mr-2" />
            {t('refresh')}
          </button>
          <span className="text-xs text-gray-500">
            {t('lastUpdate')}: {lastUpdate.toLocaleTimeString()}
          </span>
        </div>
      </div>

      {/* View Toggle */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveView('overview')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeView === 'overview'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveView('metrics')}
            className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm ${
              activeView === 'metrics'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <BarChart3 size={18} />
            <span>Metrics</span>
          </button>
        </nav>
      </div>

      {/* Metrics View */}
      {activeView === 'metrics' && <MetricsDashboard />}

      {/* Overview View */}
      {activeView === 'overview' && (
        <>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {dashboardStats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.name} className="card">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <Icon size={24} className="text-gray-400" />
                </div>
                <div className="ml-4 flex-1">
                  <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                  <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                </div>
                <div className={`text-sm ${
                  stat.changeType === 'positive' ? 'text-success-600' :
                  stat.changeType === 'negative' ? 'text-danger-600' : 'text-gray-600'
                }`}>
                  {stat.change}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* GraphRAG Section */}
      {stats?.graphrag && (
        <div className="card bg-gradient-to-br from-green-50 to-blue-50">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <Network className="text-green-600" size={24} />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-gray-900">{t('graphragKnowledgeGraph')}</h2>
                <p className="text-sm text-gray-600">{t('entityEmbeddingsSemanticSearch')}</p>
              </div>
            </div>
          </div>

          {/* GraphRAG Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            {/* Entity Embeddings */}
            <div className="bg-white rounded-lg p-4 border border-green-200">
              <div className="flex items-center justify-between mb-2">
                <Sparkles className="text-lime-600" size={20} />
                <span className="text-xs font-medium text-lime-600 bg-lime-100 px-2 py-0.5 rounded">
                  {stats.graphrag.entities.coverage_percentage}%
                </span>
              </div>
              <p className="text-2xl font-bold text-gray-900">{stats.graphrag.entities.with_embeddings}</p>
              <p className="text-sm text-gray-600">{t('entityEmbeddings')}</p>
              <div className="mt-2 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-lime-500 to-emerald-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${stats.graphrag.entities.coverage_percentage}%` }}
                />
              </div>
            </div>

            {/* Total Entities */}
            <div className="bg-white rounded-lg p-4 border border-green-200">
              <Tag className="text-primary-600 mb-2" size={20} />
              <p className="text-2xl font-bold text-gray-900">{stats.graphrag.entities.total}</p>
              <p className="text-sm text-gray-600">{t('totalEntities')}</p>
              <p className="text-xs text-gray-500 mt-1">
                {stats.graphrag.entities.without_embeddings} {t('pending')}
              </p>
            </div>

            {/* Graph Nodes */}
            <div className="bg-white rounded-lg p-4 border border-green-200">
              <GitBranch className="text-green-600 mb-2" size={20} />
              <p className="text-2xl font-bold text-gray-900">{stats.graphrag.graph.total_nodes}</p>
              <p className="text-sm text-gray-600">{t('graphNodes')}</p>
              <p className="text-xs text-gray-500 mt-1">
                {stats.graphrag.graph.documents_in_graph} {t('documents')}
              </p>
            </div>

            {/* GraphRAG Queries */}
            <div className="bg-white rounded-lg p-4 border border-green-200">
              <Network className="text-teal-600 mb-2" size={20} />
              <p className="text-2xl font-bold text-gray-900">{stats.graphrag.queries.today}</p>
              <p className="text-sm text-gray-600">{t('ragQueriesToday')}</p>
              <p className="text-xs text-gray-500 mt-1">
                {stats.graphrag.queries.total} {t('total')}
              </p>
            </div>
          </div>

          {/* Recent GraphRAG Queries */}
          {stats.graphrag.recent_queries && stats.graphrag.recent_queries.length > 0 && (
            <div className="bg-white rounded-lg p-4 border border-green-200">
              <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
                <Search className="mr-2 text-green-600" size={16} />
                {t('recentGraphragQueries')}
              </h3>
              <div className="space-y-2">
                {stats.graphrag.recent_queries.map((query: any) => (
                  <div key={query.id} className="flex items-start space-x-2 p-2 bg-gray-50 rounded">
                    <Sparkles className="text-green-600 mt-0.5 flex-shrink-0" size={14} />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-900 truncate">{query.query}</p>
                      <p className="text-xs text-gray-500">
                        {new Date(query.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Uploads */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Recent Uploads</h2>
            <button className="text-sm text-primary-600 hover:text-primary-700">
              View All
            </button>
          </div>
          <div className="space-y-3">
            {stats?.recent_uploads?.length > 0 ? (
              stats.recent_uploads.slice(0, 5).map((upload: any) => (
                <div key={upload.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <FileText className="text-gray-400" size={20} />
                    <div>
                      <p className="text-sm font-medium text-gray-900">{upload.title}</p>
                      <p className="text-xs text-gray-500">{upload.filename} • {upload.document_type}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-500">
                      {(upload.file_size / (1024 * 1024)).toFixed(2)} MB
                    </p>
                    <p className="text-xs text-gray-500">{new Date(upload.uploaded_at).toLocaleDateString()}</p>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-gray-500 text-center py-8">No recent uploads</p>
            )}
          </div>
        </div>

        {/* Recent RAG Queries */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Recent Queries</h2>
            <button className="text-sm text-primary-600 hover:text-primary-700">
              View All
            </button>
          </div>
          <div className="space-y-3">
            {stats?.recent_queries?.length > 0 ? (
              stats.recent_queries.slice(0, 5).map((query: any) => (
                <div key={query.id} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                  <Search className="text-gray-400 mt-0.5" size={20} />
                  <div className="flex-1">
                    <p className="text-sm text-gray-900">{query.query}</p>
                    <div className="flex items-center space-x-2 mt-1">
                      <span className="text-xs px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded">
                        {query.query_type}
                      </span>
                      <span className="text-xs text-gray-500">
                        {new Date(query.created_at).toLocaleString()}
                      </span>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-gray-500 text-center py-8">No recent queries</p>
            )}
          </div>
        </div>

      </div>

      {/* Quick Actions */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
            <MessageSquare size={20} className="text-primary-600 mr-3" />
            <div className="text-left">
              <p className="text-sm font-medium text-gray-900">AI Assistant</p>
              <p className="text-xs text-gray-500">Get help with troubleshooting</p>
            </div>
          </button>
          <button className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
            <Activity size={20} className="text-primary-600 mr-3" />
            <div className="text-left">
              <p className="text-sm font-medium text-gray-900">Log Analysis</p>
              <p className="text-xs text-gray-500">Analyze system logs</p>
            </div>
          </button>
          <button className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
            <Clock size={20} className="text-primary-600 mr-3" />
            <div className="text-left">
              <p className="text-sm font-medium text-gray-900">Maintenance</p>
              <p className="text-xs text-gray-500">Schedule maintenance tasks</p>
            </div>
          </button>
        </div>
      </div>
        </>
      )}
    </div>
  );
};

export default Dashboard; 