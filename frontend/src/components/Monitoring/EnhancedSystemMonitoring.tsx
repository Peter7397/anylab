import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert';
import { 
  Activity, 
  AlertTriangle, 
  Server, 
  Wifi, 
  WifiOff, 
  Clock,
  TrendingUp,
  TrendingDown,
  CheckCircle,
  XCircle,
  Monitor,
  FileText,
  Cpu,
  MemoryStick,
  HardDrive,
  Network,
  Zap,
  BarChart3,
  Bell,
  Settings,
  RefreshCw,
  Eye,
  EyeOff,
  Download,
  Upload,
  Thermometer,
  Gauge,
  Database,
  Shield,
  Globe,
  Users,
  Calendar,
  FileSearch,
  FolderOpen,
  Share2,
  ChevronRight,
  ChevronDown,
  Plus,
  Trash2,
  Edit,
  Play,
  Pause,
  Square
} from 'lucide-react';
import { apiClient } from '../../services/api';

interface SystemMetrics {
  id: number;
  system: number;
  timestamp: string;
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  network_in: number;
  network_out: number;
  uptime: number;
  temperature?: number;
  details: {
    cpu_details: any;
    memory_details: any;
    disk_details: any;
    network_details: any;
    system_details: any;
    agent_version: string;
    agent_stats: any;
    collection_time_ms: number;
  };
}

interface System {
  id: number;
  name: string;
  hostname: string;
  ip_address: string;
  mac_address: string;
  os_type: string;
  os_version: string;
  status: 'online' | 'offline' | 'maintenance' | 'error';
  last_seen: string;
  created_at: string;
  updated_at: string;
  notes: string;
  metrics: SystemMetrics[];
}

interface Alert {
  id: number;
  title: string;
  description: string;
  system: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: 'active' | 'acknowledged' | 'resolved' | 'dismissed';
  created_at: string;
  acknowledged_at?: string;
  resolved_at?: string;
  system_name: string;
  system_hostname: string;
}

interface DashboardStats {
  systems: {
    total: number;
    online: number;
    offline: number;
    maintenance: number;
    error: number;
  };
  metrics: {
    total_collected: number;
    last_24h: number;
    avg_cpu: number;
    avg_memory: number;
    avg_disk: number;
  };
  alerts: {
    total: number;
    active: number;
    critical: number;
    acknowledged: number;
    resolved: number;
  };
  performance: {
    avg_response_time: number;
    uptime_percentage: number;
    error_rate: number;
  };
}

const EnhancedSystemMonitoring: React.FC = () => {
  const [systems, setSystems] = useState<System[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSystem, setSelectedSystem] = useState<System | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  useEffect(() => {
    fetchData();
    
    if (autoRefresh) {
      const interval = setInterval(fetchData, refreshInterval * 1000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch systems with their latest metrics
      const systemsResponse = await apiClient.get<System[]>('/monitoring/sysmon/agents/');
      setSystems(systemsResponse.data);
      
      // Fetch alerts
      const alertsResponse = await apiClient.get<Alert[]>('/monitoring/alerts/');
      setAlerts(alertsResponse.data);
      
      // Calculate dashboard stats
      calculateStats(systemsResponse.data, alertsResponse.data);
      
      setError(null);
    } catch (err) {
      setError('Failed to fetch monitoring data');
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  const calculateStats = (systemsData: System[], alertsData: Alert[]) => {
    const systemsStats = {
      total: systemsData.length,
      online: systemsData.filter(s => s.status === 'online').length,
      offline: systemsData.filter(s => s.status === 'offline').length,
      maintenance: systemsData.filter(s => s.status === 'maintenance').length,
      error: systemsData.filter(s => s.status === 'error').length,
    };

    const alertsStats = {
      total: alertsData.length,
      active: alertsData.filter(a => a.status === 'active').length,
      critical: alertsData.filter(a => a.severity === 'critical').length,
      acknowledged: alertsData.filter(a => a.status === 'acknowledged').length,
      resolved: alertsData.filter(a => a.status === 'resolved').length,
    };

    // Calculate average metrics
    const allMetrics = systemsData.flatMap(s => s.metrics || []);
    const metricsStats = {
      total_collected: allMetrics.length,
      last_24h: allMetrics.filter(m => {
        const metricTime = new Date(m.timestamp);
        const dayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
        return metricTime > dayAgo;
      }).length,
      avg_cpu: allMetrics.length > 0 ? allMetrics.reduce((sum, m) => sum + m.cpu_usage, 0) / allMetrics.length : 0,
      avg_memory: allMetrics.length > 0 ? allMetrics.reduce((sum, m) => sum + m.memory_usage, 0) / allMetrics.length : 0,
      avg_disk: allMetrics.length > 0 ? allMetrics.reduce((sum, m) => sum + m.disk_usage, 0) / allMetrics.length : 0,
    };

    const performanceStats = {
      avg_response_time: 150, // Mock data
      uptime_percentage: systemsStats.online / systemsStats.total * 100,
      error_rate: alertsStats.critical / systemsStats.total * 100,
    };

    setStats({
      systems: systemsStats,
      metrics: metricsStats,
      alerts: alertsStats,
      performance: performanceStats,
    });
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'online':
        return <Wifi className="h-4 w-4 text-green-500" />;
      case 'offline':
        return <WifiOff className="h-4 w-4 text-red-500" />;
      case 'maintenance':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-600" />;
      default:
        return <Server className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'online':
        return <Badge className="bg-green-100 text-green-800">Online</Badge>;
      case 'offline':
        return <Badge variant="destructive">Offline</Badge>;
      case 'maintenance':
        return <Badge className="bg-yellow-100 text-yellow-800">Maintenance</Badge>;
      case 'error':
        return <Badge variant="destructive">Error</Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <Badge variant="destructive">Critical</Badge>;
      case 'high':
        return <Badge className="bg-red-100 text-red-800">High</Badge>;
      case 'medium':
        return <Badge className="bg-yellow-100 text-yellow-800">Medium</Badge>;
      case 'low':
        return <Badge variant="outline">Low</Badge>;
      default:
        return <Badge variant="outline">{severity}</Badge>;
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  if (loading && !stats) {
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Enhanced System Monitoring</h1>
          <p className="text-muted-foreground">
            Real-time system monitoring with SysMon agents
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            {autoRefresh ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
            {autoRefresh ? 'Auto' : 'Manual'}
          </Button>
          <Button variant="outline" size="sm" onClick={fetchData}>
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
          <Button variant="outline" size="sm" onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}>
            {viewMode === 'grid' ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
            {viewMode === 'grid' ? 'Grid' : 'List'}
          </Button>
        </div>
      </div>

      {/* Statistics Cards */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Systems</CardTitle>
              <Server className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.systems.total}</div>
              <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                <div className="flex items-center space-x-1">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>{stats.systems.online} online</span>
                </div>
                <div className="flex items-center space-x-1">
                  <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                  <span>{stats.systems.offline} offline</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Alerts</CardTitle>
              <AlertTriangle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.alerts.active}</div>
              <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                <span>{stats.alerts.critical} critical</span>
                <span>•</span>
                <span>{stats.alerts.acknowledged} acknowledged</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Metrics Collected</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.metrics.total_collected}</div>
              <div className="text-xs text-muted-foreground">
                {stats.metrics.last_24h} in last 24h
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">System Health</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.performance.uptime_percentage.toFixed(1)}%</div>
              <div className="text-xs text-muted-foreground">
                Average uptime
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Performance Overview */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Cpu className="h-5 w-5" />
                <span>CPU Usage</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-600">
                {stats.metrics.avg_cpu.toFixed(1)}%
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${Math.min(stats.metrics.avg_cpu, 100)}%` }}
                ></div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <MemoryStick className="h-5 w-5" />
                <span>Memory Usage</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-600">
                {stats.metrics.avg_memory.toFixed(1)}%
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                <div 
                  className="bg-green-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${Math.min(stats.metrics.avg_memory, 100)}%` }}
                ></div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <HardDrive className="h-5 w-5" />
                <span>Disk Usage</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-orange-600">
                {stats.metrics.avg_disk.toFixed(1)}%
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                <div 
                  className="bg-orange-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${Math.min(stats.metrics.avg_disk, 100)}%` }}
                ></div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Systems Grid/List */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Monitored Systems</CardTitle>
            <div className="flex items-center space-x-2">
              <Badge variant="outline">{systems.length} systems</Badge>
              <Button variant="outline" size="sm">
                <Plus className="h-4 w-4" />
                Add System
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {viewMode === 'grid' ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {systems.map((system) => {
                const latestMetrics = system.metrics?.[system.metrics.length - 1];
                return (
                  <div
                    key={system.id}
                    className="p-4 border rounded-lg hover:shadow-md transition-shadow cursor-pointer"
                    onClick={() => setSelectedSystem(system)}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(system.status)}
                        <div>
                          <h3 className="font-semibold">{system.name}</h3>
                          <p className="text-sm text-muted-foreground">{system.hostname}</p>
                        </div>
                      </div>
                      {getStatusBadge(system.status)}
                    </div>

                    {latestMetrics && (
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="flex items-center space-x-1">
                            <Cpu className="h-3 w-3 text-blue-500" />
                            <span>CPU</span>
                          </span>
                          <span className="font-medium">{latestMetrics.cpu_usage.toFixed(1)}%</span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="flex items-center space-x-1">
                            <MemoryStick className="h-3 w-3 text-green-500" />
                            <span>RAM</span>
                          </span>
                          <span className="font-medium">{latestMetrics.memory_usage.toFixed(1)}%</span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="flex items-center space-x-1">
                            <HardDrive className="h-3 w-3 text-orange-500" />
                            <span>Disk</span>
                          </span>
                          <span className="font-medium">{latestMetrics.disk_usage.toFixed(1)}%</span>
                        </div>
                        {latestMetrics.uptime && (
                          <div className="flex items-center justify-between text-sm">
                            <span className="flex items-center space-x-1">
                              <Clock className="h-3 w-3 text-purple-500" />
                              <span>Uptime</span>
                            </span>
                            <span className="font-medium">{formatUptime(latestMetrics.uptime)}</span>
                          </div>
                        )}
                      </div>
                    )}

                    <div className="mt-3 pt-3 border-t">
                      <p className="text-xs text-muted-foreground">
                        Last seen: {new Date(system.last_seen).toLocaleString()}
                      </p>
                      {system.os_type && (
                        <p className="text-xs text-muted-foreground">
                          OS: {system.os_type} {system.os_version}
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="space-y-4">
              {systems.map((system) => {
                const latestMetrics = system.metrics?.[system.metrics.length - 1];
                return (
                  <div
                    key={system.id}
                    className="flex items-center justify-between p-4 border rounded-lg hover:shadow-md transition-shadow cursor-pointer"
                    onClick={() => setSelectedSystem(system)}
                  >
                    <div className="flex items-center space-x-4">
                      {getStatusIcon(system.status)}
                      <div>
                        <h3 className="font-semibold">{system.name}</h3>
                        <p className="text-sm text-muted-foreground">{system.hostname}</p>
                        <p className="text-xs text-muted-foreground">{system.ip_address}</p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-4">
                      {latestMetrics && (
                        <div className="flex items-center space-x-4 text-sm">
                          <div className="flex items-center space-x-1">
                            <Cpu className="h-4 w-4 text-blue-500" />
                            <span>{latestMetrics.cpu_usage.toFixed(1)}%</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <MemoryStick className="h-4 w-4 text-green-500" />
                            <span>{latestMetrics.memory_usage.toFixed(1)}%</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <HardDrive className="h-4 w-4 text-orange-500" />
                            <span>{latestMetrics.disk_usage.toFixed(1)}%</span>
                          </div>
                        </div>
                      )}
                      {getStatusBadge(system.status)}
                      <ChevronRight className="h-4 w-4 text-muted-foreground" />
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {systems.length === 0 && (
            <div className="text-center py-8">
              <Server className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium mb-2">No systems monitored</h3>
              <p className="text-muted-foreground mb-4">
                Start monitoring your systems by deploying SysMon agents
              </p>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Deploy SysMon Agent
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recent Alerts */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Alerts</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {alerts.slice(0, 5).map((alert) => (
              <div key={alert.id} className="p-4 border rounded-lg">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <h4 className="font-medium">{alert.title}</h4>
                      {getSeverityBadge(alert.severity)}
                    </div>
                    <p className="text-sm text-muted-foreground mb-2">
                      {alert.description}
                    </p>
                    <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                      <span>{alert.system_name}</span>
                      <span>•</span>
                      <span>{new Date(alert.created_at).toLocaleString()}</span>
                      <span>•</span>
                      <span className="capitalize">{alert.status}</span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button variant="outline" size="sm">
                      <Eye className="h-4 w-4" />
                    </Button>
                    <Button variant="outline" size="sm">
                      <Edit className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
            {alerts.length === 0 && (
              <div className="text-center py-8">
                <Bell className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium mb-2">No alerts</h3>
                <p className="text-muted-foreground">
                  All systems are running normally
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default EnhancedSystemMonitoring;
