import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert';
import { 
  Activity, 
  AlertTriangle, 
  FileText, 
  Monitor, 
  Server, 
  TrendingUp,
  TrendingDown,
  CheckCircle,
  XCircle,
  Clock,
  Zap,
  BarChart3,
  RefreshCw,
  Eye,
  EyeOff,
  FileSearch,
  Code,
  HardDrive,
  Network,
  Database,
  Shield,
  Target,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  Search
} from 'lucide-react';
import { apiClient } from '../../services/api';

interface AppMonAgent {
  id: number;
  name: string;
  system_name: string;
  system_hostname: string;
  status: string;
  version: string;
  last_seen: string;
  configuration: any;
}

interface AppMonMetrics {
  files_monitored: number;
  total_log_size_mb: number;
  largest_file_mb: number;
  total_alerts_sent: number;
  unique_alerts_sent: number;
  duplicate_alerts_suppressed: number;
  scan_duration_ms: number;
  scan_frequency_per_minute: number;
  active_sources: number;
  total_patterns: number;
  errors_count: number;
  alert_cache_size: number;
  cache_hit_rate: number;
}

interface AppMonAlert {
  id: number;
  application_name: string;
  system_name: string;
  title: string;
  severity: string;
  status: string;
  source_name: string;
  file_path: string;
  line_number: number;
  pattern_matched: string;
  created_at: string;
}

interface DashboardData {
  agents: {
    total: number;
    online: number;
    offline: number;
    error: number;
  };
  metrics: {
    total_files_monitored: number;
    total_log_size_gb: number;
    total_alerts_sent: number;
    duplicate_alerts_suppressed: number;
    avg_scan_duration_ms: number;
    cache_hit_rate: number;
  };
  alerts: {
    total: number;
    active: number;
    critical: number;
    resolved: number;
  };
  sources: {
    total_sources: number;
    active_patterns: number;
    files_being_monitored: number;
  };
  recent_alerts: AppMonAlert[];
  recent_agents: AppMonAgent[];
  performance_trends: {
    scan_duration: number[];
    alert_frequency: number[];
    file_growth: number[];
  };
}

const AppMonEnhancedDashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showOffline, setShowOffline] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch AppMon agents
      const agentsResponse = await apiClient.get<AppMonAgent[]>('/monitoring/appmon/agents/');
      const agents = agentsResponse.data;
      
      // Fetch recent alerts
      const alertsResponse = await apiClient.get<AppMonAlert[]>('/monitoring/appmon/alerts/');
      const alerts = alertsResponse.data;
      
      // Calculate dashboard metrics
      const onlineAgents = agents.filter(agent => {
        const lastSeen = new Date(agent.last_seen);
        const now = new Date();
        return (now.getTime() - lastSeen.getTime()) < 5 * 60 * 1000; // 5 minutes
      });
      
      const offlineAgents = agents.filter(agent => {
        const lastSeen = new Date(agent.last_seen);
        const now = new Date();
        return (now.getTime() - lastSeen.getTime()) >= 5 * 60 * 1000;
      });
      
      const errorAgents = agents.filter(agent => agent.status === 'error');
      
      const activeAlerts = alerts.filter(alert => alert.status === 'active');
      const criticalAlerts = alerts.filter(alert => alert.severity === 'critical');
      const resolvedAlerts = alerts.filter(alert => alert.status === 'resolved');
      
      // Calculate aggregated metrics
      let totalFilesMonitored = 0;
      let totalLogSizeGB = 0;
      let totalAlertsSent = 0;
      let duplicateAlertsSuppressed = 0;
      let totalScanDuration = 0;
      let totalCacheHitRate = 0;
      let totalSources = 0;
      let totalPatterns = 0;
      
      agents.forEach(agent => {
        if (agent.configuration) {
          const sources = agent.configuration.sources || [];
          totalSources += sources.length;
          sources.forEach((source: any) => {
            totalPatterns += (source.patterns || []).length;
          });
        }
      });
      
      const dashboardData: DashboardData = {
        agents: {
          total: agents.length,
          online: onlineAgents.length,
          offline: offlineAgents.length,
          error: errorAgents.length
        },
        metrics: {
          total_files_monitored: totalFilesMonitored,
          total_log_size_gb: totalLogSizeGB,
          total_alerts_sent: totalAlertsSent,
          duplicate_alerts_suppressed: duplicateAlertsSuppressed,
          avg_scan_duration_ms: totalScanDuration / Math.max(agents.length, 1),
          cache_hit_rate: totalCacheHitRate / Math.max(agents.length, 1)
        },
        alerts: {
          total: alerts.length,
          active: activeAlerts.length,
          critical: criticalAlerts.length,
          resolved: resolvedAlerts.length
        },
        sources: {
          total_sources: totalSources,
          active_patterns: totalPatterns,
          files_being_monitored: totalFilesMonitored
        },
        recent_alerts: alerts.slice(0, 10),
        recent_agents: agents.slice(0, 5),
        performance_trends: {
          scan_duration: [120, 95, 110, 85, 100, 90, 105],
          alert_frequency: [5, 8, 3, 12, 7, 9, 6],
          file_growth: [2.1, 2.3, 2.5, 2.8, 3.1, 3.4, 3.7]
        }
      };
      
      setDashboardData(dashboardData);
      setError(null);
    } catch (err) {
      setError('Failed to fetch dashboard data');
      console.error('Error fetching dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'inactive':
        return <XCircle className="w-5 h-5 text-gray-500" />;
      case 'error':
        return <AlertTriangle className="w-5 h-5 text-red-500" />;
      case 'maintenance':
        return <Clock className="w-5 h-5 text-yellow-500" />;
      default:
        return <Monitor className="w-5 h-5 text-gray-400" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'error':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'info':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const formatLastSeen = (lastSeen: string) => {
    const date = new Date(lastSeen);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  const getTrendIcon = (current: number, previous: number) => {
    if (current > previous) return <ArrowUpRight className="w-4 h-4 text-red-500" />;
    if (current < previous) return <ArrowDownRight className="w-4 h-4 text-green-500" />;
    return <Minus className="w-4 h-4 text-gray-500" />;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading AppMon dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert className="mb-6 border-red-200 bg-red-50">
        <AlertTriangle className="h-4 w-4 text-red-600" />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  if (!dashboardData) {
    return (
      <Alert className="mb-6 border-yellow-200 bg-yellow-50">
        <AlertTriangle className="h-4 w-4 text-yellow-600" />
        <AlertTitle>No Data</AlertTitle>
        <AlertDescription>No dashboard data available.</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header with gradient background */}
      <div className="bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-700 rounded-xl p-8 text-white">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-4xl font-bold mb-2">AppMon Enhanced Dashboard</h1>
            <p className="text-blue-100 text-lg">Comprehensive application monitoring and log analysis</p>
            <div className="flex items-center gap-4 mt-4">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-sm">Live monitoring active</span>
              </div>
              <div className="flex items-center gap-2">
                <Monitor className="w-4 h-4" />
                <span className="text-sm">{dashboardData.agents.total} agents connected</span>
              </div>
            </div>
          </div>
          <Button 
            onClick={fetchDashboardData} 
            className="bg-white/20 hover:bg-white/30 text-white border-white/30 flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Key Metrics Cards with enhanced styling */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Agents Status */}
        <Card className="group hover:shadow-lg transition-all duration-300 border-0 shadow-md">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">AppMon Agents</CardTitle>
            <div className="p-2 bg-blue-100 rounded-lg group-hover:bg-blue-200 transition-colors">
              <Monitor className="h-4 w-4 text-blue-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900 mb-2">{dashboardData.agents.total}</div>
            <div className="flex items-center gap-2 mb-3">
              <div className="flex-1 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-green-500 to-green-600 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${(dashboardData.agents.online / dashboardData.agents.total) * 100}%` }}
                ></div>
              </div>
              <span className="text-sm text-gray-600">{Math.round((dashboardData.agents.online / dashboardData.agents.total) * 100)}%</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <Badge variant="outline" className="text-green-600 border-green-200 bg-green-50">
                {dashboardData.agents.online} Online
              </Badge>
              <Badge variant="outline" className="text-red-600 border-red-200 bg-red-50">
                {dashboardData.agents.offline} Offline
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Files Monitored */}
        <Card className="group hover:shadow-lg transition-all duration-300 border-0 shadow-md">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Files Monitored</CardTitle>
            <div className="p-2 bg-purple-100 rounded-lg group-hover:bg-purple-200 transition-colors">
              <FileSearch className="h-4 w-4 text-purple-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900 mb-2">
              {dashboardData.sources.files_being_monitored.toLocaleString()}
            </div>
            <div className="flex items-center gap-2 mb-3">
              <div className="flex-1 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-purple-500 to-purple-600 h-2 rounded-full transition-all duration-500"
                  style={{ width: '75%' }}
                ></div>
              </div>
              <span className="text-sm text-gray-600">75%</span>
            </div>
            <p className="text-xs text-gray-500">
              {dashboardData.metrics.total_log_size_gb.toFixed(1)} GB total log size
            </p>
          </CardContent>
        </Card>

        {/* Active Alerts */}
        <Card className="group hover:shadow-lg transition-all duration-300 border-0 shadow-md">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Active Alerts</CardTitle>
            <div className="p-2 bg-red-100 rounded-lg group-hover:bg-red-200 transition-colors">
              <AlertTriangle className="h-4 w-4 text-red-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900 mb-2">{dashboardData.alerts.active}</div>
            <div className="flex items-center gap-2 mb-3">
              <div className="flex-1 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-red-500 to-red-600 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, (dashboardData.alerts.active / Math.max(dashboardData.alerts.total, 1)) * 100)}%` }}
                ></div>
              </div>
              <span className="text-sm text-gray-600">
                {Math.round((dashboardData.alerts.active / Math.max(dashboardData.alerts.total, 1)) * 100)}%
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-red-600 border-red-200 bg-red-50">
                {dashboardData.alerts.critical} Critical
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Performance */}
        <Card className="group hover:shadow-lg transition-all duration-300 border-0 shadow-md">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Avg Scan Duration</CardTitle>
            <div className="p-2 bg-green-100 rounded-lg group-hover:bg-green-200 transition-colors">
              <Activity className="h-4 w-4 text-green-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900 mb-2">
              {dashboardData.metrics.avg_scan_duration_ms.toFixed(0)}ms
            </div>
            <div className="flex items-center gap-2 mb-3">
              <div className="flex-1 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-green-500 to-green-600 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, (dashboardData.metrics.avg_scan_duration_ms / 200) * 100)}%` }}
                ></div>
              </div>
              <span className="text-sm text-gray-600">
                {Math.round((dashboardData.metrics.avg_scan_duration_ms / 200) * 100)}%
              </span>
            </div>
            <p className="text-xs text-gray-500">
              Cache hit rate: {(dashboardData.metrics.cache_hit_rate * 100).toFixed(1)}%
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Metrics with enhanced styling */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Monitoring Sources */}
        <Card className="border-0 shadow-md hover:shadow-lg transition-all duration-300">
          <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-blue-100">
            <CardTitle className="flex items-center gap-2 text-blue-900">
              <Target className="w-5 h-5" />
              Monitoring Sources
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <div className="space-y-6">
              <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Target className="w-4 h-4 text-blue-600" />
                  </div>
                  <span className="text-sm text-gray-600">Total Sources</span>
                </div>
                <span className="font-semibold text-lg">{dashboardData.sources.total_sources}</span>
              </div>
              <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <Search className="w-4 h-4 text-purple-600" />
                  </div>
                  <span className="text-sm text-gray-600">Active Patterns</span>
                </div>
                <span className="font-semibold text-lg">{dashboardData.sources.active_patterns}</span>
              </div>
              <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <FileText className="w-4 h-4 text-green-600" />
                  </div>
                  <span className="text-sm text-gray-600">Files Being Monitored</span>
                </div>
                <span className="font-semibold text-lg">{dashboardData.sources.files_being_monitored.toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-orange-100 rounded-lg">
                    <HardDrive className="w-4 h-4 text-orange-600" />
                  </div>
                  <span className="text-sm text-gray-600">Total Log Size</span>
                </div>
                <span className="font-semibold text-lg">{dashboardData.metrics.total_log_size_gb.toFixed(1)} GB</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Alert Statistics */}
        <Card className="border-0 shadow-md hover:shadow-lg transition-all duration-300">
          <CardHeader className="bg-gradient-to-r from-red-50 to-pink-50 border-b border-red-100">
            <CardTitle className="flex items-center gap-2 text-red-900">
              <AlertTriangle className="w-5 h-5" />
              Alert Statistics
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <div className="space-y-6">
              <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-red-100 rounded-lg">
                    <AlertTriangle className="w-4 h-4 text-red-600" />
                  </div>
                  <span className="text-sm text-gray-600">Total Alerts Sent</span>
                </div>
                <span className="font-semibold text-lg">{dashboardData.metrics.total_alerts_sent.toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <CheckCircle className="w-4 h-4 text-blue-600" />
                  </div>
                  <span className="text-sm text-gray-600">Unique Alerts</span>
                </div>
                <span className="font-semibold text-lg">{dashboardData.metrics.total_alerts_sent - dashboardData.metrics.duplicate_alerts_suppressed}</span>
              </div>
              <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-yellow-100 rounded-lg">
                    <Shield className="w-4 h-4 text-yellow-600" />
                  </div>
                  <span className="text-sm text-gray-600">Duplicates Suppressed</span>
                </div>
                <span className="font-semibold text-lg">{dashboardData.metrics.duplicate_alerts_suppressed.toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <Activity className="w-4 h-4 text-green-600" />
                  </div>
                  <span className="text-sm text-gray-600">Active Alerts</span>
                </div>
                <span className="font-semibold text-lg">{dashboardData.alerts.active}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Alerts with enhanced styling */}
      <Card className="border-0 shadow-md hover:shadow-lg transition-all duration-300">
        <CardHeader className="bg-gradient-to-r from-red-50 to-pink-50 border-b border-red-100">
          <CardTitle className="flex items-center gap-2 text-red-900">
            <AlertTriangle className="w-5 h-5" />
            Recent Alerts
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <div className="space-y-4">
            {dashboardData.recent_alerts.map((alert) => (
              <div key={alert.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                <div className="flex items-center gap-4">
                  <div className="flex flex-col">
                    <div className="font-medium text-gray-900">{alert.title}</div>
                    <div className="text-sm text-gray-600">
                      {alert.application_name} • {alert.source_name}
                    </div>
                    <div className="text-xs text-gray-500">
                      {alert.file_path}:{alert.line_number} • {new Date(alert.created_at).toLocaleString()}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge className={`${getSeverityColor(alert.severity)} border`}>
                    {alert.severity}
                  </Badge>
                  <Badge variant="outline" className="border-gray-300">
                    {alert.status}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recent Agents with enhanced styling */}
      <Card className="border-0 shadow-md hover:shadow-lg transition-all duration-300">
        <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-blue-100">
          <CardTitle className="flex items-center gap-2 text-blue-900">
            <Monitor className="w-5 h-5" />
            Recent AppMon Agents
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <div className="space-y-4">
            {dashboardData.recent_agents.map((agent) => (
              <div key={agent.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                <div className="flex items-center gap-4">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    {getStatusIcon(agent.status)}
                  </div>
                  <div className="flex flex-col">
                    <div className="font-medium text-gray-900">{agent.name}</div>
                    <div className="text-sm text-gray-600">
                      {agent.system_name} ({agent.system_hostname})
                    </div>
                    <div className="text-xs text-gray-500">
                      Version {agent.version} • Last seen {formatLastSeen(agent.last_seen)}
                    </div>
                  </div>
                </div>
                <Badge variant="outline" className="border-gray-300">
                  {agent.status}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AppMonEnhancedDashboard;
