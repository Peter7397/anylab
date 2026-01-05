import React, { useState, useEffect } from 'react';
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  TrendingDown,
  BarChart3,
  FileText,
  Database,
  Cpu,
  HardDrive,
  MemoryStick,
  RefreshCw,
  Loader
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { apiClient } from '../../services/api';

interface ProcessingMetrics {
  time_window_hours: number;
  timestamp: string;
  processing: {
    total_files: number;
    processed_files: number;
    failed_files: number;
    pending_files: number;
    success_rate: number;
    failure_rate: number;
  };
  processing_time: {
    average_seconds: number;
    min_seconds: number;
    max_seconds: number;
    samples: number;
  };
  file_sizes: {
    total_bytes: number;
    total_mb: number;
    average_bytes: number;
    average_mb: number;
  };
  content: {
    total_chunks: number;
    total_embeddings: number;
    chunks_per_file: number;
  };
  errors: {
    breakdown: Array<{ status: string; count: number }>;
    total_errors: number;
  };
  system?: {
    cpu_percent: number;
    memory: {
      percent: number;
      used_gb: number;
      total_gb: number;
    };
    disk: {
      percent: number;
      used_gb: number;
      total_gb: number;
    };
  };
}

interface TimelineData {
  time_window_hours: number;
  interval_hours: number;
  timeline: Array<{
    timestamp: string;
    time_bucket: string;
    total_files: number;
    processed_files: number;
    failed_files: number;
    pending_files: number;
    success_rate: number;
  }>;
}

interface ErrorSummary {
  time_window_hours: number;
  error_breakdown: Record<string, {
    count: number;
    samples: Array<{
      filename: string;
      error: string;
      timestamp: string;
    }>;
  }>;
  total_errors: number;
}

const MetricsDashboard: React.FC = () => {
  const { t } = useTranslation(['dashboard', 'common']);
  const [activeTab, setActiveTab] = useState<'overview' | 'timeline' | 'errors' | 'system'>('overview');
  const [metrics, setMetrics] = useState<ProcessingMetrics | null>(null);
  const [timeline, setTimeline] = useState<TimelineData | null>(null);
  const [errorSummary, setErrorSummary] = useState<ErrorSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeWindow, setTimeWindow] = useState(24);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const loadMetrics = async () => {
    try {
      setLoading(true);
      const [metricsData, timelineData, errorsData] = await Promise.all([
        apiClient.getProcessingMetrics(timeWindow, true),
        apiClient.getProcessingTimeline(timeWindow, 1),
        apiClient.getErrorSummary(timeWindow, 20)
      ]);
      setMetrics(metricsData);
      setTimeline(timelineData);
      setErrorSummary(errorsData);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Failed to load metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMetrics();
    const interval = setInterval(loadMetrics, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, [timeWindow]);

  if (loading && !metrics) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader className="animate-spin text-primary-600" size={32} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Processing Metrics</h1>
          <p className="text-gray-600">Monitor file processing performance and system health</p>
        </div>
        <div className="flex items-center space-x-3">
          <select
            value={timeWindow}
            onChange={(e) => setTimeWindow(Number(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
          >
            <option value={1}>Last Hour</option>
            <option value={6}>Last 6 Hours</option>
            <option value={24}>Last 24 Hours</option>
            <option value={168}>Last Week</option>
          </select>
          <button
            onClick={loadMetrics}
            className="btn-secondary flex items-center"
            disabled={loading}
          >
            <RefreshCw size={16} className={`mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <span className="text-xs text-gray-500">
            Updated: {lastUpdate.toLocaleTimeString()}
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          {[
            { id: 'overview', label: 'Overview', icon: BarChart3 },
            { id: 'timeline', label: 'Timeline', icon: TrendingUp },
            { id: 'errors', label: 'Errors', icon: AlertTriangle },
            { id: 'system', label: 'System', icon: Activity }
          ].map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id as any)}
              className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === id
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Icon size={18} />
              <span>{label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && metrics && (
        <div className="space-y-6">
          {/* Key Metrics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="card">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Success Rate</p>
                  <p className="text-3xl font-bold text-gray-900">
                    {metrics.processing.success_rate.toFixed(1)}%
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {metrics.processing.processed_files} of {metrics.processing.total_files} files
                  </p>
                </div>
                <div className={`p-3 rounded-lg ${
                  metrics.processing.success_rate >= 95 ? 'bg-green-100' :
                  metrics.processing.success_rate >= 80 ? 'bg-yellow-100' : 'bg-red-100'
                }`}>
                  <CheckCircle className={`${
                    metrics.processing.success_rate >= 95 ? 'text-green-600' :
                    metrics.processing.success_rate >= 80 ? 'text-yellow-600' : 'text-red-600'
                  }`} size={24} />
                </div>
              </div>
            </div>

            <div className="card">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Avg Processing Time</p>
                  <p className="text-3xl font-bold text-gray-900">
                    {metrics.processing_time.average_seconds.toFixed(1)}s
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {metrics.processing_time.samples} samples
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-blue-100">
                  <Clock className="text-blue-600" size={24} />
                </div>
              </div>
            </div>

            <div className="card">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Chunks</p>
                  <p className="text-3xl font-bold text-gray-900">
                    {metrics.content.total_chunks.toLocaleString()}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {metrics.content.chunks_per_file.toFixed(1)} per file
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-purple-100">
                  <Database className="text-purple-600" size={24} />
                </div>
              </div>
            </div>

            <div className="card">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Errors</p>
                  <p className="text-3xl font-bold text-gray-900">
                    {metrics.errors.total_errors}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {metrics.processing.failure_rate.toFixed(1)}% failure rate
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-red-100">
                  <AlertTriangle className="text-red-600" size={24} />
                </div>
              </div>
            </div>
          </div>

          {/* Processing Statistics */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Processing Statistics</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Total Files</span>
                  <span className="text-lg font-semibold">{metrics.processing.total_files}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Processed</span>
                  <span className="text-lg font-semibold text-green-600">
                    {metrics.processing.processed_files}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Failed</span>
                  <span className="text-lg font-semibold text-red-600">
                    {metrics.processing.failed_files}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Pending</span>
                  <span className="text-lg font-semibold text-yellow-600">
                    {metrics.processing.pending_files}
                  </span>
                </div>
                <div className="pt-4 border-t border-gray-200">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">Success Rate</span>
                    <span className="text-sm font-semibold">
                      {metrics.processing.success_rate.toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-green-600 h-2 rounded-full transition-all"
                      style={{ width: `${metrics.processing.success_rate}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Content Statistics</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Total Chunks</span>
                  <span className="text-lg font-semibold">
                    {metrics.content.total_chunks.toLocaleString()}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Total Embeddings</span>
                  <span className="text-lg font-semibold">
                    {metrics.content.total_embeddings.toLocaleString()}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Chunks per File</span>
                  <span className="text-lg font-semibold">
                    {metrics.content.chunks_per_file.toFixed(1)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Total File Size</span>
                  <span className="text-lg font-semibold">
                    {metrics.file_sizes.total_mb.toFixed(2)} MB
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Avg File Size</span>
                  <span className="text-lg font-semibold">
                    {metrics.file_sizes.average_mb.toFixed(2)} MB
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Processing Time Stats */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Processing Time Statistics</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <p className="text-sm text-gray-600 mb-1">Average</p>
                <p className="text-2xl font-bold text-gray-900">
                  {metrics.processing_time.average_seconds.toFixed(2)}s
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-1">Minimum</p>
                <p className="text-2xl font-bold text-green-600">
                  {metrics.processing_time.min_seconds.toFixed(2)}s
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-1">Maximum</p>
                <p className="text-2xl font-bold text-red-600">
                  {metrics.processing_time.max_seconds.toFixed(2)}s
                </p>
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-4">
              Based on {metrics.processing_time.samples} processed files
            </p>
          </div>
        </div>
      )}

      {/* Timeline Tab */}
      {activeTab === 'timeline' && timeline && (
        <div className="space-y-6">
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Processing Timeline</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Time Period
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Total
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Processed
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Failed
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Pending
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Success Rate
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {timeline.timeline.map((bucket, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                        {bucket.time_bucket}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-gray-900">
                        {bucket.total_files}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-green-600">
                        {bucket.processed_files}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-red-600">
                        {bucket.failed_files}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-yellow-600">
                        {bucket.pending_files}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-right">
                        <span className={`font-semibold ${
                          bucket.success_rate >= 95 ? 'text-green-600' :
                          bucket.success_rate >= 80 ? 'text-yellow-600' : 'text-red-600'
                        }`}>
                          {bucket.success_rate.toFixed(1)}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Errors Tab */}
      {activeTab === 'errors' && errorSummary && (
        <div className="space-y-6">
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Error Summary</h3>
              <span className="text-sm text-gray-500">
                Total Errors: {errorSummary.total_errors}
              </span>
            </div>
            <div className="space-y-4">
              {Object.entries(errorSummary.error_breakdown).map(([status, data]) => (
                <div key={status} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-2">
                      <AlertTriangle className="text-red-600" size={20} />
                      <span className="font-semibold text-gray-900 capitalize">
                        {status.replace('_', ' ')}
                      </span>
                    </div>
                    <span className="text-lg font-bold text-red-600">{data.count}</span>
                  </div>
                  {data.samples.length > 0 && (
                    <div className="space-y-2 mt-3 pt-3 border-t border-gray-200">
                      <p className="text-xs font-medium text-gray-500 uppercase">Sample Errors:</p>
                      {data.samples.map((sample, index) => (
                        <div key={index} className="bg-gray-50 rounded p-2">
                          <p className="text-sm font-medium text-gray-900">{sample.filename}</p>
                          <p className="text-xs text-gray-600 mt-1">{sample.error}</p>
                          <p className="text-xs text-gray-500 mt-1">
                            {new Date(sample.timestamp).toLocaleString()}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              {errorSummary.total_errors === 0 && (
                <div className="text-center py-8">
                  <CheckCircle className="mx-auto text-green-600 mb-2" size={48} />
                  <p className="text-gray-600">No errors in the selected time window</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* System Tab */}
      {activeTab === 'system' && metrics?.system && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">CPU Usage</h3>
                <Cpu className="text-blue-600" size={24} />
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Usage</span>
                  <span className={`text-2xl font-bold ${
                    metrics.system.cpu_percent > 80 ? 'text-red-600' :
                    metrics.system.cpu_percent > 60 ? 'text-yellow-600' : 'text-green-600'
                  }`}>
                    {metrics.system.cpu_percent.toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full transition-all ${
                      metrics.system.cpu_percent > 80 ? 'bg-red-600' :
                      metrics.system.cpu_percent > 60 ? 'bg-yellow-600' : 'bg-green-600'
                    }`}
                    style={{ width: `${metrics.system.cpu_percent}%` }}
                  />
                </div>
              </div>
            </div>

            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Memory Usage</h3>
                <MemoryStick className="text-purple-600" size={24} />
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Usage</span>
                  <span className={`text-2xl font-bold ${
                    metrics.system.memory.percent > 80 ? 'text-red-600' :
                    metrics.system.memory.percent > 60 ? 'text-yellow-600' : 'text-green-600'
                  }`}>
                    {metrics.system.memory.percent.toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full transition-all ${
                      metrics.system.memory.percent > 80 ? 'bg-red-600' :
                      metrics.system.memory.percent > 60 ? 'bg-yellow-600' : 'bg-green-600'
                    }`}
                    style={{ width: `${metrics.system.memory.percent}%` }}
                  />
                </div>
                <div className="text-xs text-gray-500">
                  {metrics.system.memory.used_gb.toFixed(2)} GB / {metrics.system.memory.total_gb.toFixed(2)} GB
                </div>
              </div>
            </div>

            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Disk Usage</h3>
                <HardDrive className="text-orange-600" size={24} />
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Usage</span>
                  <span className={`text-2xl font-bold ${
                    metrics.system.disk.percent > 80 ? 'text-red-600' :
                    metrics.system.disk.percent > 60 ? 'text-yellow-600' : 'text-green-600'
                  }`}>
                    {metrics.system.disk.percent.toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full transition-all ${
                      metrics.system.disk.percent > 80 ? 'bg-red-600' :
                      metrics.system.disk.percent > 60 ? 'bg-yellow-600' : 'bg-green-600'
                    }`}
                    style={{ width: `${metrics.system.disk.percent}%` }}
                  />
                </div>
                <div className="text-xs text-gray-500">
                  {metrics.system.disk.used_gb.toFixed(2)} GB / {metrics.system.disk.total_gb.toFixed(2)} GB
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MetricsDashboard;

