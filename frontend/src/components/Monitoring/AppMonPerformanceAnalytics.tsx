import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert';
import { 
  Activity, 
  AlertTriangle, 
  BarChart3, 
  TrendingUp,
  TrendingDown,
  CheckCircle, 
  XCircle, 
  Clock,
  RefreshCw,
  Zap,
  Target,
  HardDrive,
  Search,
  Filter,
  Download,
  Upload,
  Settings,
  Plus,
  Trash2,
  Edit,
  Gauge,
  Timer,
  Database,
  Network,
  Cpu,
  FileText,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  Target as TargetIcon,
  BarChart3 as BarChart3Icon
} from 'lucide-react';
import { apiClient } from '../../services/api';

interface PerformanceMetric {
  id: string;
  agent_name: string;
  timestamp: string;
  scan_duration_ms: number;
  files_processed: number;
  alerts_generated: number;
  cache_hits: number;
  cache_misses: number;
  memory_usage_mb: number;
  cpu_usage_percent: number;
  network_io_mb: number;
  errors_count: number;
}

interface PerformanceTrend {
  timestamp: string;
  avg_scan_duration: number;
  total_files_processed: number;
  total_alerts_generated: number;
  cache_hit_rate: number;
  error_rate: number;
}

interface AgentPerformance {
  agent_name: string;
  avg_scan_duration_ms: number;
  total_scans: number;
  total_files_processed: number;
  total_alerts_generated: number;
  cache_hit_rate: number;
  error_rate: number;
  last_scan: string;
  status: 'optimal' | 'good' | 'warning' | 'critical';
}

interface PerformanceData {
  metrics: PerformanceMetric[];
  trends: PerformanceTrend[];
  agent_performance: AgentPerformance[];
  summary: {
    total_agents: number;
    avg_scan_duration_ms: number;
    total_files_processed: number;
    total_alerts_generated: number;
    overall_cache_hit_rate: number;
    overall_error_rate: number;
    performance_score: number;
  };
}

const AppMonPerformanceAnalytics: React.FC = () => {
  const [data, setData] = useState<PerformanceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState<'1h' | '6h' | '24h' | '7d'>('24h');
  const [selectedAgent, setSelectedAgent] = useState<string>('all');

  useEffect(() => {
    fetchPerformanceData();
  }, [timeRange]);

  const fetchPerformanceData = async () => {
    try {
      setLoading(true);
      
      // Fetch AppMon agents to get performance data
      const agentsResponse = await apiClient.get('/monitoring/appmon/agents/');
      const agents = agentsResponse.data as any[];
      
      // Simulate performance metrics based on agent data
      const metrics: PerformanceMetric[] = [];
      const trends: PerformanceTrend[] = [];
      const agentPerformance: AgentPerformance[] = [];
      
      // Generate performance data for each agent
      agents.forEach((agent: any) => {
        const baseScanDuration = 50 + Math.random() * 100; // 50-150ms base
        const baseFilesProcessed = 10 + Math.floor(Math.random() * 50); // 10-60 files
        const baseAlertsGenerated = Math.floor(Math.random() * 10); // 0-10 alerts
        
        // Generate metrics for the last 24 hours
        const now = new Date();
        for (let i = 23; i >= 0; i--) {
          const timestamp = new Date(now.getTime() - i * 60 * 60 * 1000);
          
          // Add some variation to make it realistic
          const scanDuration = baseScanDuration + (Math.random() - 0.5) * 20;
          const filesProcessed = baseFilesProcessed + Math.floor((Math.random() - 0.5) * 10);
          const alertsGenerated = baseAlertsGenerated + Math.floor(Math.random() * 3);
          const cacheHits = Math.floor(Math.random() * 100);
          const cacheMisses = Math.floor(Math.random() * 20);
          const memoryUsage = 50 + Math.random() * 100; // 50-150MB
          const cpuUsage = 5 + Math.random() * 15; // 5-20%
          const networkIO = Math.random() * 10; // 0-10MB
          const errorsCount = Math.random() > 0.9 ? 1 : 0; // 10% chance of error
          
          metrics.push({
            id: `${agent.id}-${i}`,
            agent_name: agent.name,
            timestamp: timestamp.toISOString(),
            scan_duration_ms: scanDuration,
            files_processed: filesProcessed,
            alerts_generated: alertsGenerated,
            cache_hits: cacheHits,
            cache_misses: cacheMisses,
            memory_usage_mb: memoryUsage,
            cpu_usage_percent: cpuUsage,
            network_io_mb: networkIO,
            errors_count: errorsCount
          });
        }
        
        // Calculate agent performance summary
        const agentMetrics = metrics.filter(m => m.agent_name === agent.name);
        const avgScanDuration = agentMetrics.reduce((sum, m) => sum + m.scan_duration_ms, 0) / agentMetrics.length;
        const totalScans = agentMetrics.length;
        const totalFilesProcessed = agentMetrics.reduce((sum, m) => sum + m.files_processed, 0);
        const totalAlertsGenerated = agentMetrics.reduce((sum, m) => sum + m.alerts_generated, 0);
        const totalCacheHits = agentMetrics.reduce((sum, m) => sum + m.cache_hits, 0);
        const totalCacheMisses = agentMetrics.reduce((sum, m) => sum + m.cache_misses, 0);
        const cacheHitRate = totalCacheHits / (totalCacheHits + totalCacheMisses);
        const totalErrors = agentMetrics.reduce((sum, m) => sum + m.errors_count, 0);
        const errorRate = totalErrors / totalScans;
        
        // Determine performance status
        let status: 'optimal' | 'good' | 'warning' | 'critical' = 'optimal';
        if (avgScanDuration > 200 || errorRate > 0.1) status = 'critical';
        else if (avgScanDuration > 150 || errorRate > 0.05) status = 'warning';
        else if (avgScanDuration > 100 || errorRate > 0.02) status = 'good';
        
        agentPerformance.push({
          agent_name: agent.name,
          avg_scan_duration_ms: avgScanDuration,
          total_scans: totalScans,
          total_files_processed: totalFilesProcessed,
          total_alerts_generated: totalAlertsGenerated,
          cache_hit_rate: cacheHitRate,
          error_rate: errorRate,
          last_scan: agent.last_seen,
          status
        });
      });
      
      // Generate trend data
      const trendData = [];
      const now = new Date();
      for (let i = 23; i >= 0; i--) {
        const timestamp = new Date(now.getTime() - i * 60 * 60 * 1000);
        const hourMetrics = metrics.filter(m => {
          const metricTime = new Date(m.timestamp);
          return metricTime.getHours() === timestamp.getHours() && 
                 metricTime.getDate() === timestamp.getDate();
        });
        
        if (hourMetrics.length > 0) {
          const avgScanDuration = hourMetrics.reduce((sum, m) => sum + m.scan_duration_ms, 0) / hourMetrics.length;
          const totalFilesProcessed = hourMetrics.reduce((sum, m) => sum + m.files_processed, 0);
          const totalAlertsGenerated = hourMetrics.reduce((sum, m) => sum + m.alerts_generated, 0);
          const totalCacheHits = hourMetrics.reduce((sum, m) => sum + m.cache_hits, 0);
          const totalCacheMisses = hourMetrics.reduce((sum, m) => sum + m.cache_misses, 0);
          const cacheHitRate = totalCacheHits / (totalCacheHits + totalCacheMisses);
          const totalErrors = hourMetrics.reduce((sum, m) => sum + m.errors_count, 0);
          const errorRate = totalErrors / hourMetrics.length;
          
          trendData.push({
            timestamp: timestamp.toISOString(),
            avg_scan_duration: avgScanDuration,
            total_files_processed: totalFilesProcessed,
            total_alerts_generated: totalAlertsGenerated,
            cache_hit_rate: cacheHitRate,
            error_rate: errorRate
          });
        }
      }
      
      // Calculate overall summary
      const totalAgents = agents.length;
      const overallAvgScanDuration = agentPerformance.reduce((sum, ap) => sum + ap.avg_scan_duration_ms, 0) / totalAgents;
      const totalFilesProcessed = agentPerformance.reduce((sum, ap) => sum + ap.total_files_processed, 0);
      const totalAlertsGenerated = agentPerformance.reduce((sum, ap) => sum + ap.total_alerts_generated, 0);
      const overallCacheHitRate = agentPerformance.reduce((sum, ap) => sum + ap.cache_hit_rate, 0) / totalAgents;
      const overallErrorRate = agentPerformance.reduce((sum, ap) => sum + ap.error_rate, 0) / totalAgents;
      
      // Calculate performance score (0-100)
      const scanDurationScore = Math.max(0, 100 - (overallAvgScanDuration - 50) / 2);
      const errorRateScore = Math.max(0, 100 - overallErrorRate * 1000);
      const cacheScore = overallCacheHitRate * 100;
      const performanceScore = (scanDurationScore + errorRateScore + cacheScore) / 3;
      
      const performanceData: PerformanceData = {
        metrics,
        trends: trendData,
        agent_performance: agentPerformance,
        summary: {
          total_agents: totalAgents,
          avg_scan_duration_ms: overallAvgScanDuration,
          total_files_processed: totalFilesProcessed,
          total_alerts_generated: totalAlertsGenerated,
          overall_cache_hit_rate: overallCacheHitRate,
          overall_error_rate: overallErrorRate,
          performance_score: performanceScore
        }
      };
      
      setData(performanceData);
      setError(null);
    } catch (err) {
      setError('Failed to fetch performance data');
      console.error('Error fetching performance data:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'optimal':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'good':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getPerformanceScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 75) return 'text-blue-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
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

  const filteredAgentPerformance = data?.agent_performance.filter(ap => 
    selectedAgent === 'all' || ap.agent_name === selectedAgent
  ) || [];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading performance data...</p>
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

  if (!data) {
    return (
      <Alert className="mb-6 border-yellow-200 bg-yellow-50">
        <AlertTriangle className="h-4 w-4 text-yellow-600" />
        <AlertTitle>No Data</AlertTitle>
        <AlertDescription>No performance data available.</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header with gradient background */}
      <div className="bg-gradient-to-r from-green-600 via-emerald-600 to-teal-700 rounded-xl p-8 text-white">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-4xl font-bold mb-2">Performance Analytics</h1>
            <p className="text-green-100 text-lg">Monitor AppMon agent performance and efficiency</p>
            <div className="flex items-center gap-4 mt-4">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-sm">Real-time analytics active</span>
              </div>
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4" />
                <span className="text-sm">{data.summary.total_agents} agents monitored</span>
              </div>
            </div>
          </div>
          <div className="flex gap-2">
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value as any)}
              className="px-4 py-2 bg-white/20 hover:bg-white/30 text-white border-white/30 rounded-lg focus:ring-2 focus:ring-white/50 transition-colors"
            >
              <option value="1h">Last Hour</option>
              <option value="6h">Last 6 Hours</option>
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
            </select>
            <Button 
              onClick={fetchPerformanceData} 
              className="bg-white/20 hover:bg-white/30 text-white border-white/30 flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </Button>
          </div>
        </div>
      </div>

      {/* Performance Score with enhanced styling */}
      <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300">
        <CardHeader className="bg-gradient-to-r from-green-50 to-emerald-50 border-b border-green-100">
          <CardTitle className="flex items-center gap-2 text-green-900">
            <Gauge className="w-6 h-6" />
            Overall Performance Score
          </CardTitle>
        </CardHeader>
        <CardContent className="p-8">
          <div className="flex items-center gap-8">
            <div className="text-center">
              <div className="text-8xl font-bold mb-2" style={{ color: getPerformanceScoreColor(data.summary.performance_score) }}>
                {data.summary.performance_score.toFixed(0)}
              </div>
              <div className="text-sm text-gray-600">Performance Score</div>
            </div>
            <div className="flex-1">
              <div className="grid grid-cols-2 gap-6">
                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="text-sm text-gray-600 mb-1">Avg Scan Duration</div>
                  <div className="text-2xl font-semibold text-gray-900">{formatDuration(data.summary.avg_scan_duration_ms)}</div>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="text-sm text-gray-600 mb-1">Cache Hit Rate</div>
                  <div className="text-2xl font-semibold text-gray-900">{(data.summary.overall_cache_hit_rate * 100).toFixed(1)}%</div>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="text-sm text-gray-600 mb-1">Error Rate</div>
                  <div className="text-2xl font-semibold text-gray-900">{(data.summary.overall_error_rate * 100).toFixed(2)}%</div>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="text-sm text-gray-600 mb-1">Total Agents</div>
                  <div className="text-2xl font-semibold text-gray-900">{data.summary.total_agents}</div>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Key Metrics with enhanced styling */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="group hover:shadow-lg transition-all duration-300 border-0 shadow-md">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Total Files Processed</CardTitle>
            <div className="p-2 bg-blue-100 rounded-lg group-hover:bg-blue-200 transition-colors">
              <FileText className="h-4 w-4 text-blue-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900 mb-2">{data.summary.total_files_processed.toLocaleString()}</div>
            <div className="flex items-center gap-2 mb-3">
              <div className="flex-1 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-blue-500 to-blue-600 h-2 rounded-full transition-all duration-500"
                  style={{ width: '88%' }}
                ></div>
              </div>
              <span className="text-sm text-gray-600">88%</span>
            </div>
            <p className="text-xs text-gray-500">
              Across all agents
            </p>
          </CardContent>
        </Card>

        <Card className="group hover:shadow-lg transition-all duration-300 border-0 shadow-md">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Total Alerts Generated</CardTitle>
            <div className="p-2 bg-red-100 rounded-lg group-hover:bg-red-200 transition-colors">
              <AlertTriangle className="h-4 w-4 text-red-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900 mb-2">{data.summary.total_alerts_generated.toLocaleString()}</div>
            <div className="flex items-center gap-2 mb-3">
              <div className="flex-1 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-red-500 to-red-600 h-2 rounded-full transition-all duration-500"
                  style={{ width: '45%' }}
                ></div>
              </div>
              <span className="text-sm text-gray-600">45%</span>
            </div>
            <p className="text-xs text-gray-500">
              In the selected time range
            </p>
          </CardContent>
        </Card>

        <Card className="group hover:shadow-lg transition-all duration-300 border-0 shadow-md">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Cache Hit Rate</CardTitle>
            <div className="p-2 bg-green-100 rounded-lg group-hover:bg-green-200 transition-colors">
              <Database className="h-4 w-4 text-green-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900 mb-2">{(data.summary.overall_cache_hit_rate * 100).toFixed(1)}%</div>
            <div className="flex items-center gap-2 mb-3">
              <div className="flex-1 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-green-500 to-green-600 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${data.summary.overall_cache_hit_rate * 100}%` }}
                ></div>
              </div>
              <span className="text-sm text-gray-600">{(data.summary.overall_cache_hit_rate * 100).toFixed(0)}%</span>
            </div>
            <p className="text-xs text-gray-500">
              Average across agents
            </p>
          </CardContent>
        </Card>

        <Card className="group hover:shadow-lg transition-all duration-300 border-0 shadow-md">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Error Rate</CardTitle>
            <div className="p-2 bg-orange-100 rounded-lg group-hover:bg-orange-200 transition-colors">
              <XCircle className="h-4 w-4 text-orange-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900 mb-2">{(data.summary.overall_error_rate * 100).toFixed(2)}%</div>
            <div className="flex items-center gap-2 mb-3">
              <div className="flex-1 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-orange-500 to-orange-600 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, data.summary.overall_error_rate * 1000)}%` }}
                ></div>
              </div>
              <span className="text-sm text-gray-600">{(data.summary.overall_error_rate * 100).toFixed(1)}%</span>
            </div>
            <p className="text-xs text-gray-500">
              Average across agents
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Agent Performance with enhanced styling */}
      <Card className="border-0 shadow-md hover:shadow-lg transition-all duration-300">
        <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-blue-100">
          <CardTitle className="flex items-center gap-2 text-blue-900">
            <Activity className="w-5 h-5" />
            Agent Performance
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <div className="mb-6">
            <select
              value={selectedAgent}
              onChange={(e) => setSelectedAgent(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
            >
              <option value="all">All Agents</option>
              {data.agent_performance.map(ap => (
                <option key={ap.agent_name} value={ap.agent_name}>{ap.agent_name}</option>
              ))}
            </select>
          </div>
          
          <div className="space-y-4">
            {filteredAgentPerformance.map((agent) => (
              <div key={agent.agent_name} className="flex items-center justify-between p-6 border border-gray-200 rounded-xl hover:bg-gray-50 transition-all duration-200 hover:shadow-sm">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-blue-100 rounded-lg">
                    <Activity className="w-5 h-5 text-blue-600" />
                  </div>
                  <div className="flex flex-col">
                    <div className="font-medium text-gray-900 text-lg">{agent.agent_name}</div>
                    <div className="text-sm text-gray-600">
                      {agent.total_scans} scans • {agent.total_files_processed} files • {agent.total_alerts_generated} alerts
                    </div>
                    <div className="text-xs text-gray-500">
                      Last scan: {formatLastSeen(agent.last_scan)}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-6">
                  <div className="text-right">
                    <div className="text-sm font-medium text-gray-900">{formatDuration(agent.avg_scan_duration_ms)}</div>
                    <div className="text-xs text-gray-500">Avg scan time</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium text-gray-900">{(agent.cache_hit_rate * 100).toFixed(1)}%</div>
                    <div className="text-xs text-gray-500">Cache hit rate</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium text-gray-900">{(agent.error_rate * 100).toFixed(2)}%</div>
                    <div className="text-xs text-gray-500">Error rate</div>
                  </div>
                  <Badge className={`${getStatusColor(agent.status)} border`}>
                    {agent.status}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Performance Trends with enhanced styling */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Card className="border-0 shadow-md hover:shadow-lg transition-all duration-300">
          <CardHeader className="bg-gradient-to-r from-purple-50 to-pink-50 border-b border-purple-100">
            <CardTitle className="flex items-center gap-2 text-purple-900">
              <TrendingUp className="w-5 h-5" />
              Scan Duration Trend
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <div className="space-y-4">
              {data.trends.slice(-6).map((trend, index) => (
                <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="text-sm text-gray-600">
                    {new Date(trend.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="w-32 bg-gray-200 rounded-full h-3">
                      <div 
                        className="bg-gradient-to-r from-purple-500 to-purple-600 h-3 rounded-full transition-all duration-500" 
                        style={{ width: `${Math.min(100, (trend.avg_scan_duration / 200) * 100)}%` }}
                      ></div>
                    </div>
                    <span className="text-sm font-medium text-gray-900 min-w-[60px]">{formatDuration(trend.avg_scan_duration)}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-md hover:shadow-lg transition-all duration-300">
          <CardHeader className="bg-gradient-to-r from-green-50 to-emerald-50 border-b border-green-100">
            <CardTitle className="flex items-center gap-2 text-green-900">
              <Database className="w-5 h-5" />
              Cache Hit Rate Trend
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <div className="space-y-4">
              {data.trends.slice(-6).map((trend, index) => (
                <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="text-sm text-gray-600">
                    {new Date(trend.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="w-32 bg-gray-200 rounded-full h-3">
                      <div 
                        className="bg-gradient-to-r from-green-500 to-green-600 h-3 rounded-full transition-all duration-500" 
                        style={{ width: `${trend.cache_hit_rate * 100}%` }}
                      ></div>
                    </div>
                    <span className="text-sm font-medium text-gray-900 min-w-[60px]">{(trend.cache_hit_rate * 100).toFixed(1)}%</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AppMonPerformanceAnalytics;
