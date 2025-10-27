import React, { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, TrendingDown, FileText, Search, Users, Activity, AlertCircle, Calendar, RefreshCw } from 'lucide-react';
import { apiClient } from '../../services/api';

interface AnalyticsData {
  userStats?: any;
  contributionStats?: any;
  performanceStats?: any;
  documentStats?: any;
  behaviorStats?: any;
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

const Analytics: React.FC = () => {
  const [data, setData] = useState<AnalyticsData>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState<'7d' | '30d' | '90d' | 'all'>('30d');
  const [activeTab, setActiveTab] = useState<'overview' | 'contributions' | 'performance' | 'documents' | 'behavior'>('overview');

  useEffect(() => {
    loadAnalytics();
  }, [dateRange]);

  const loadAnalytics = async () => {
    setLoading(true);
    setError(null);
    try {
      const [userStats, contributionStats, performanceStats, documentStats, behaviorStats] = await Promise.allSettled([
        apiClient.getUserStatistics(),
        apiClient.getContributionAnalytics(),
        apiClient.getPerformanceAnalytics(),
        apiClient.getDocumentAnalytics(),
        apiClient.getUserBehaviorStats(),
      ]);

      setData({
        userStats: userStats.status === 'fulfilled' ? userStats.value : null,
        contributionStats: contributionStats.status === 'fulfilled' ? contributionStats.value : null,
        performanceStats: performanceStats.status === 'fulfilled' ? performanceStats.value : null,
        documentStats: documentStats.status === 'fulfilled' ? documentStats.value : null,
        behaviorStats: behaviorStats.status === 'fulfilled' ? behaviorStats.value : null,
      });
    } catch (err: any) {
      setError(err?.message || 'Failed to load analytics data');
      console.error('Error loading analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
          <AlertCircle className="text-red-600 mt-0.5 mr-3" size={20} />
          <div>
            <p className="text-sm font-medium text-red-800">Error</p>
            <p className="text-sm text-red-600">{error}</p>
            <button 
              onClick={loadAnalytics}
              className="mt-2 text-sm text-red-700 hover:text-red-900 underline"
            >
              Try again
            </button>
          </div>
        </div>
      </div>
    );
  }

  const { userStats, contributionStats, performanceStats, documentStats, behaviorStats } = data;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h1>
          <p className="text-gray-600">Comprehensive insights into your system usage</p>
        </div>
        <div className="flex items-center space-x-3">
          <select
            className="input-field"
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value as any)}
          >
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
            <option value="all">All time</option>
          </select>
          <button
            onClick={loadAnalytics}
            className="btn-secondary"
          >
            <RefreshCw size={16} className="mr-2" />
            Refresh
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          {[
            { id: 'overview', label: 'Overview' },
            { id: 'contributions', label: 'Contributions' },
            { id: 'performance', label: 'Performance' },
            { id: 'documents', label: 'Documents' },
            { id: 'behavior', label: 'User Behavior' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Stat Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="card">
              <div className="flex items-center">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <FileText className="text-blue-600" size={24} />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Documents</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {userStats?.statistics?.total_documents || 0}
                  </p>
                </div>
              </div>
            </div>
            <div className="card">
              <div className="flex items-center">
                <div className="p-2 bg-green-100 rounded-lg">
                  <Search className="text-green-600" size={24} />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Queries</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {userStats?.statistics?.total_queries || 0}
                  </p>
                </div>
              </div>
            </div>
            <div className="card">
              <div className="flex items-center">
                <div className="p-2 bg-yellow-100 rounded-lg">
                  <Activity className="text-yellow-600" size={24} />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">File Size</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {formatFileSize(userStats?.statistics?.total_file_size || 0)}
                  </p>
                </div>
              </div>
            </div>
            <div className="card">
              <div className="flex items-center">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Users className="text-purple-600" size={24} />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Recent Activity</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {userStats?.statistics?.recent_documents || 0}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Document Types Chart */}
            {documentStats?.by_type && documentStats.by_type.length > 0 && (
              <div className="card">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Documents by Type</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={documentStats.by_type}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }: any) => `${name}: ${percent ? (percent * 100).toFixed(0) : 0}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="count"
                    >
                      {documentStats.by_type.map((entry: any, index: number) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Query Types Chart */}
            {performanceStats?.by_type && performanceStats.by_type.length > 0 && (
              <div className="card">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Queries by Type</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={performanceStats.by_type}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="query_type" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="count" fill="#3b82f6" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Contributions Tab */}
      {activeTab === 'contributions' && (
        <div className="space-y-6">
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Contribution Activity</h3>
            {contributionStats?.by_date && contributionStats.by_date.length > 0 ? (
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={contributionStats.by_date}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="count" stroke="#3b82f6" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-gray-500 text-center py-12">No contribution data available</p>
            )}
          </div>

          {contributionStats?.by_type && contributionStats.by_type.length > 0 && (
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Contributions by Type</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={contributionStats.by_type}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="document_type" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="count" fill="#10b981" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {/* Performance Tab */}
      {activeTab === 'performance' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="card">
              <p className="text-sm font-medium text-gray-600">Total Queries</p>
              <p className="text-3xl font-bold text-gray-900">{performanceStats?.total_queries || 0}</p>
            </div>
            <div className="card">
              <p className="text-sm font-medium text-gray-600">Recent Queries</p>
              <p className="text-3xl font-bold text-green-600">{performanceStats?.recent_queries || 0}</p>
            </div>
            <div className="card">
              <p className="text-sm font-medium text-gray-600">Avg Sources/Query</p>
              <p className="text-3xl font-bold text-blue-600">{performanceStats?.avg_sources_per_query || 0}</p>
            </div>
          </div>

          {performanceStats?.by_type && performanceStats.by_type.length > 0 && (
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Query Distribution</h3>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={performanceStats.by_type}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="query_type" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="count" fill="#f59e0b" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {/* Documents Tab */}
      {activeTab === 'documents' && (
        <div className="space-y-6">
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Document Statistics</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Documents</p>
                <p className="text-3xl font-bold text-gray-900">{documentStats?.total_documents || 0}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">Total Size</p>
                <p className="text-3xl font-bold text-gray-900">
                  {formatFileSize(documentStats?.total_size || 0)}
                </p>
              </div>
            </div>

            {documentStats?.by_type && documentStats.by_type.length > 0 && (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={documentStats.by_type} layout="horizontal">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="document_type" type="category" width={150} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="count" fill="#8b5cf6" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>

          {documentStats?.recent_uploads && documentStats.recent_uploads.length > 0 && (
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Uploads</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Document
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Type
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Size
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Date
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {documentStats.recent_uploads.map((doc: any) => (
                      <tr key={doc.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {doc.title || 'Untitled'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
                            {doc.type}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatFileSize(doc.size)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(doc.uploaded_at).toLocaleDateString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* User Behavior Tab */}
      {activeTab === 'behavior' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="card">
              <p className="text-sm font-medium text-gray-600">Total Queries</p>
              <p className="text-3xl font-bold text-gray-900">{behaviorStats?.total_queries || 0}</p>
            </div>
            <div className="card">
              <p className="text-sm font-medium text-gray-600">Recent Queries (24h)</p>
              <p className="text-3xl font-bold text-green-600">{behaviorStats?.recent_queries || 0}</p>
            </div>
            <div className="card">
              <p className="text-sm font-medium text-gray-600">Avg Query Length</p>
              <p className="text-3xl font-bold text-blue-600">{behaviorStats?.avg_query_length || 0} chars</p>
            </div>
          </div>

          {behaviorStats?.by_type && behaviorStats.by_type.length > 0 && (
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Query Types Distribution</h3>
              <ResponsiveContainer width="100%" height={400}>
                <PieChart>
                  <Pie
                    data={behaviorStats.by_type}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }: any) => `${name}: ${percent ? (percent * 100).toFixed(0) : 0}%`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="count"
                  >
                    {behaviorStats.by_type.map((entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Analytics;

