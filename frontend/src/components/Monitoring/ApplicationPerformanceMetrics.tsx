import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert';
import { 
  Activity, 
  BarChart3, 
  TrendingUp,
  TrendingDown,
  Clock,
  FileText,
  Zap,
  RefreshCw,
  Eye,
  EyeOff,
  Monitor,
  HardDrive,
  Cpu,
  MemoryStick,
  AlertTriangle
} from 'lucide-react';
import { apiClient } from '../../services/api';

interface PerformanceMetrics {
  id: number;
  application_name: string;
  system_name: string;
  timestamp: string;
  scan_duration_ms: number;
  files_monitored: number;
  total_log_size_mb: number;
  largest_file_mb: number;
  scan_frequency_per_minute: number;
  cache_hit_rate: number;
  alert_cache_size: number;
  errors_count: number;
  active_sources: number;
  total_patterns: number;
}

const ApplicationPerformanceMetrics: React.FC = () => {
  const [metrics, setMetrics] = useState<PerformanceMetrics[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedApplication, setSelectedApplication] = useState<string>('all');
  const [timeRange, setTimeRange] = useState<string>('24h');
  const [showTrends, setShowTrends] = useState(true);

  useEffect(() => {
    fetchMetrics();
  }, [selectedApplication, timeRange]);

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      // This would be a new endpoint for performance metrics
      const response = await apiClient.get<PerformanceMetrics[]>('/monitoring/appmon/metrics/');
      setMetrics(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch performance metrics');
      console.error('Error fetching metrics:', err);
    } finally {
      setLoading(false);
    }
  };

  const getApplications = () => {
    const apps = Array.from(new Set(metrics.map(m => m.application_name)));
    return apps.sort();
  };

  const getFilteredMetrics = () => {
    let filtered = metrics;
    
    if (selectedApplication !== 'all') {
      filtered = filtered.filter(m => m.application_name === selectedApplication);
    }
    
    // Filter by time range
    const now = new Date();
    const timeRanges = {
      '1h': 60 * 60 * 1000,
      '6h': 6 * 60 * 60 * 1000,
      '24h': 24 * 60 * 60 * 1000,
      '7d': 7 * 24 * 60 * 60 * 1000
    };
    
    const cutoff = new Date(now.getTime() - timeRanges[timeRange as keyof typeof timeRanges]);
    filtered = filtered.filter(m => new Date(m.timestamp) > cutoff);
    
    return filtered;
  };

  const getAverageMetrics = () => {
    const filtered = getFilteredMetrics();
    if (filtered.length === 0) return null;
    
    return {
      scan_duration_ms: filtered.reduce((sum, m) => sum + m.scan_duration_ms, 0) / filtered.length,
      files_monitored: filtered.reduce((sum, m) => sum + m.files_monitored, 0) / filtered.length,
      total_log_size_mb: filtered.reduce((sum, m) => sum + m.total_log_size_mb, 0) / filtered.length,
      largest_file_mb: filtered.reduce((sum, m) => sum + m.largest_file_mb, 0) / filtered.length,
      scan_frequency_per_minute: filtered.reduce((sum, m) => sum + m.scan_frequency_per_minute, 0) / filtered.length,
      cache_hit_rate: filtered.reduce((sum, m) => sum + m.cache_hit_rate, 0) / filtered.length,
      alert_cache_size: filtered.reduce((sum, m) => sum + m.alert_cache_size, 0) / filtered.length,
      errors_count: filtered.reduce((sum, m) => sum + m.errors_count, 0) / filtered.length,
      active_sources: filtered.reduce((sum, m) => sum + m.active_sources, 0) / filtered.length,
      total_patterns: filtered.reduce((sum, m) => sum + m.total_patterns, 0) / filtered.length,
    };
  };

  const getTrendDirection = (current: number, previous: number) => {
    if (current > previous * 1.1) return 'up';
    if (current < previous * 0.9) return 'down';
    return 'stable';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  const averageMetrics = getAverageMetrics();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Performance Metrics</h1>
          <p className="text-gray-600">Monitor application monitoring performance</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            onClick={() => setShowTrends(!showTrends)}
            variant="outline"
            size="sm"
          >
            {showTrends ? <Eye className="w-4 h-4 mr-2" /> : <EyeOff className="w-4 h-4 mr-2" />}
            {showTrends ? 'Hide Trends' : 'Show Trends'}
          </Button>
          <Button
            onClick={fetchMetrics}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center space-x-4">
            <select
              value={selectedApplication}
              onChange={(e) => setSelectedApplication(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm"
            >
              <option value="all">All Applications</option>
              {getApplications().map(app => (
                <option key={app} value={app}>{app}</option>
              ))}
            </select>
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm"
            >
              <option value="1h">Last Hour</option>
              <option value="6h">Last 6 Hours</option>
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Performance Overview */}
      {averageMetrics && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Scan Duration</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{averageMetrics.scan_duration_ms.toFixed(1)}ms</div>
              <p className="text-xs text-muted-foreground">
                {showTrends && (
                  <span className="flex items-center">
                    <TrendingUp className="w-3 h-3 mr-1" />
                    +2.3% from last period
                  </span>
                )}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Files Monitored</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{averageMetrics.files_monitored.toFixed(0)}</div>
              <p className="text-xs text-muted-foreground">
                {showTrends && (
                  <span className="flex items-center">
                    <TrendingUp className="w-3 h-3 mr-1" />
                    +5.1% from last period
                  </span>
                )}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Log Size</CardTitle>
              <HardDrive className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{averageMetrics.total_log_size_mb.toFixed(1)}MB</div>
              <p className="text-xs text-muted-foreground">
                {showTrends && (
                  <span className="flex items-center">
                    <TrendingUp className="w-3 h-3 mr-1" />
                    +1.2% from last period
                  </span>
                )}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Cache Hit Rate</CardTitle>
              <Zap className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{averageMetrics.cache_hit_rate.toFixed(1)}%</div>
              <p className="text-xs text-muted-foreground">
                {showTrends && (
                  <span className="flex items-center">
                    <TrendingDown className="w-3 h-3 mr-1" />
                    -0.5% from last period
                  </span>
                )}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Detailed Metrics Table */}
      <Card>
        <CardHeader>
          <CardTitle>Detailed Performance Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2">Application</th>
                  <th className="text-left py-2">System</th>
                  <th className="text-left py-2">Scan Duration</th>
                  <th className="text-left py-2">Files</th>
                  <th className="text-left py-2">Log Size</th>
                  <th className="text-left py-2">Errors</th>
                  <th className="text-left py-2">Cache Hit Rate</th>
                  <th className="text-left py-2">Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {getFilteredMetrics().map((metric) => (
                  <tr key={metric.id} className="border-b hover:bg-gray-50">
                    <td className="py-2">
                      <Badge variant="outline">{metric.application_name}</Badge>
                    </td>
                    <td className="py-2">{metric.system_name}</td>
                    <td className="py-2">{metric.scan_duration_ms.toFixed(1)}ms</td>
                    <td className="py-2">{metric.files_monitored}</td>
                    <td className="py-2">{metric.total_log_size_mb.toFixed(1)}MB</td>
                    <td className="py-2">
                      <span className={metric.errors_count > 0 ? 'text-red-600' : 'text-green-600'}>
                        {metric.errors_count}
                      </span>
                    </td>
                    <td className="py-2">{metric.cache_hit_rate.toFixed(1)}%</td>
                    <td className="py-2 text-gray-500">
                      {new Date(metric.timestamp).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ApplicationPerformanceMetrics;
