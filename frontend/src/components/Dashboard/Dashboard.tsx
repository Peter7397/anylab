import React, { useState, useEffect } from 'react';
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
  RefreshCw
} from 'lucide-react';
import { System } from '../../types';
import { apiClient } from '../../services/api';

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(() => {
      loadDashboardData();
    }, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      const data = await apiClient.getDashboardStats();
      setStats(data);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Mock data - replace with actual API calls
  const mockSystems: System[] = [
    { id: '1', name: 'LAB-PC-001', ip: '192.168.1.101', os: 'Windows 10 Pro', lastLogin: '2024-01-15 09:30', status: 'online' },
    { id: '2', name: 'LAB-PC-002', ip: '192.168.1.102', os: 'Windows 11 Pro', lastLogin: '2024-01-15 08:45', status: 'online' },
    { id: '3', name: 'LAB-SERVER-01', ip: '192.168.1.10', os: 'Windows Server 2022', lastLogin: '2024-01-15 10:15', status: 'warning' },
    { id: '4', name: 'LAB-PC-003', ip: '192.168.1.103', os: 'Windows 10 Pro', lastLogin: '2024-01-14 16:20', status: 'offline' },
  ];

  // Use real stats if available, otherwise use mock
  const dashboardStats = stats ? [
    { name: 'Total Documents', value: stats.documents?.total || '0', icon: FileText, change: `+${stats.documents?.today || 0}`, changeType: stats.documents?.today > 0 ? 'positive' : 'neutral' },
    { name: 'Chunks Indexed', value: stats.chunks?.total || '0', icon: Database, change: `${stats.chunks?.with_embeddings || 0} embedded`, changeType: stats.chunks?.pending === 0 ? 'positive' : 'neutral' },
    { name: 'RAG Queries Today', value: stats.rag_queries?.today || '0', icon: Search, change: `${stats.rag_queries?.total || 0} total`, changeType: stats.rag_queries?.today > 0 ? 'positive' : 'neutral' },
    { name: 'Processing Queue', value: (stats.processing_queue?.pending || 0) + (stats.processing_queue?.processing || 0), icon: Loader, change: stats.processing_queue?.failed ? `-${stats.processing_queue.failed} failed` : 'All clear', changeType: stats.processing_queue?.failed > 0 ? 'negative' : 'positive' },
  ] : [
    { name: 'Total PCs', value: '24', icon: Monitor, change: '+2', changeType: 'positive' },
    { name: 'Issues Detected', value: '3', icon: AlertTriangle, change: '-1', changeType: 'negative' },
    { name: 'Systems Online', value: '21', icon: CheckCircle, change: '+1', changeType: 'positive' },
    { name: 'Pending Maintenance', value: '5', icon: Clock, change: '+2', changeType: 'neutral' },
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
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">System overview and quick insights</p>
        </div>
        <div className="flex space-x-3 items-center">
          <button onClick={loadDashboardData} className="btn-secondary">
            <RefreshCw size={16} className="mr-2" />
            Refresh
          </button>
          <span className="text-xs text-gray-500">
            Updated: {lastUpdate.toLocaleTimeString()}
          </span>
        </div>
      </div>

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
                      <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-800 rounded">
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
    </div>
  );
};

export default Dashboard; 