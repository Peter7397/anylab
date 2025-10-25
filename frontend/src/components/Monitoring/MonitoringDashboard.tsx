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
  HardDrive
} from 'lucide-react';
import * as ApiService from '../../services/api';

interface SystemSummary {
  id: number;
  name: string;
  hostname: string;
  ip_address: string;
  status: 'online' | 'offline' | 'maintenance' | 'error';
  last_seen: string;
  alert_count: number;
  last_event_time: string | null;
  agent_status: string;
  monitoring_enabled: boolean;
  agent_type?: 'sysmon' | 'windows' | 'manual';
  cpu_usage?: number;
  memory_usage?: number;
  disk_usage?: number;
}

interface DashboardData {
  systems: {
    total: number;
    online: number;
    with_alerts: number;
    offline: number;
    sysmon_agents: number;
    windows_agents: number;
    appmon_agents: number;
  };
  alerts: {
    active: number;
    critical: number;
    last_24h: number;
  };
  events: {
    last_24h: number;
    errors_last_24h: number;
  };
  appmon: {
    total_agents: number;
    online_agents: number;
    active_alerts: number;
    critical_alerts: number;
  };
  recent_alerts: Array<{
    id: number;
    title: string;
    description: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    status: string;
    created_at: string;
    system_name: string;
    system_hostname: string;
  }>;
  recent_events: Array<{
    id: number;
    event_id: number;
    event_level: string;
    event_source: string;
    event_message: string;
    event_time_created: string;
    system_name: string;
  }>;
}

const MonitoringDashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [systems, setSystems] = useState<SystemSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDashboardData();
    fetchSystems();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await ApiService.apiClient.get<DashboardData>('/monitoring/dashboard/summary/');
      setDashboardData(response.data);
    } catch (err) {
      setError('Failed to load dashboard data');
      console.error('Error fetching dashboard data:', err);
    }
  };

  const fetchSystems = async () => {
    try {
      const response = await ApiService.apiClient.get<SystemSummary[]>('/monitoring/dashboard/systems/');
      setSystems(response.data);
    } catch (err) {
      setError('Failed to load systems data');
      console.error('Error fetching systems:', err);
    } finally {
      setLoading(false);
    }
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
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Server className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'online':
        return <Badge variant="default" className="bg-green-100 text-green-800">Online</Badge>;
      case 'offline':
        return <Badge variant="destructive">Offline</Badge>;
      case 'maintenance':
        return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">Maintenance</Badge>;
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
        return <Badge variant="default" className="bg-red-100 text-red-800">High</Badge>;
      case 'medium':
        return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">Medium</Badge>;
      case 'low':
        return <Badge variant="outline">Low</Badge>;
      default:
        return <Badge variant="outline">{severity}</Badge>;
    }
  };

  const getEventLevelBadge = (level: string) => {
    switch (level) {
      case 'Critical':
        return <Badge variant="destructive">Critical</Badge>;
      case 'Error':
        return <Badge variant="default" className="bg-red-100 text-red-800">Error</Badge>;
      case 'Warning':
        return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">Warning</Badge>;
      case 'Information':
        return <Badge variant="outline">Info</Badge>;
      default:
        return <Badge variant="outline">{level}</Badge>;
    }
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">System Monitoring</h1>
          <p className="text-muted-foreground">
            Monitor Windows systems, events, and alerts in real-time
          </p>
        </div>
        <Button onClick={fetchDashboardData}>
          <Activity className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Statistics Cards */}
      {dashboardData && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Systems</CardTitle>
              <Server className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{dashboardData.systems.total}</div>
              <p className="text-xs text-muted-foreground">
                {dashboardData.systems.online} online, {dashboardData.systems.offline} offline
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Alerts</CardTitle>
              <AlertTriangle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{dashboardData.alerts.active}</div>
              <p className="text-xs text-muted-foreground">
                {dashboardData.alerts.critical} critical alerts
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Events (24h)</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{dashboardData.events.last_24h}</div>
              <p className="text-xs text-muted-foreground">
                {dashboardData.events.errors_last_24h} error events
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Systems with Alerts</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{dashboardData.systems.with_alerts}</div>
              <p className="text-xs text-muted-foreground">
                Require attention
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Systems Overview */}
      <Card>
        <CardHeader>
          <CardTitle>Systems Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {systems.map((system) => (
              <div key={system.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-4">
                  {getStatusIcon(system.status)}
                  <div>
                    <h3 className="font-medium">{system.name}</h3>
                    <p className="text-sm text-muted-foreground">{system.hostname}</p>
                    <p className="text-xs text-muted-foreground">{system.ip_address}</p>
                    {system.agent_type && (
                      <Badge variant="outline" className="mt-1">
                        {system.agent_type === 'sysmon' ? 'SysMon Agent' : system.agent_type}
                      </Badge>
                    )}
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  {getStatusBadge(system.status)}
                  {system.alert_count > 0 && (
                    <Badge variant="destructive">{system.alert_count} alerts</Badge>
                  )}
                  <div className="text-right">
                    <p className="text-sm text-muted-foreground">
                      Last seen: {new Date(system.last_seen).toLocaleString()}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Agent: {system.agent_status}
                    </p>
                    {/* SysMon Metrics Display */}
                    {system.agent_type === 'sysmon' && (
                      <div className="flex items-center space-x-2 mt-1">
                        {system.cpu_usage !== undefined && (
                          <div className="flex items-center space-x-1">
                            <Cpu className="h-3 w-3 text-blue-500" />
                            <span className="text-xs">{system.cpu_usage.toFixed(1)}%</span>
                          </div>
                        )}
                        {system.memory_usage !== undefined && (
                          <div className="flex items-center space-x-1">
                            <MemoryStick className="h-3 w-3 text-green-500" />
                            <span className="text-xs">{system.memory_usage.toFixed(1)}%</span>
                          </div>
                        )}
                        {system.disk_usage !== undefined && (
                          <div className="flex items-center space-x-1">
                            <HardDrive className="h-3 w-3 text-orange-500" />
                            <span className="text-xs">{system.disk_usage.toFixed(1)}%</span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Agent Summaries */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* SysMon Agents Summary */}
        {dashboardData && dashboardData.systems.sysmon_agents > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Monitor className="h-5 w-5" />
                <span>SysMon Agents</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-3">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{dashboardData.systems.sysmon_agents}</div>
                  <div className="text-sm text-muted-foreground">Total Agents</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {systems.filter(s => s.agent_type === 'sysmon' && s.status === 'online').length}
                  </div>
                  <div className="text-sm text-muted-foreground">Online</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-orange-600">
                    {systems.filter(s => s.agent_type === 'sysmon' && s.alert_count > 0).length}
                  </div>
                  <div className="text-sm text-muted-foreground">With Alerts</div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* AppMon Agents Summary */}
        {dashboardData && dashboardData.appmon && dashboardData.appmon.total_agents > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <FileText className="h-5 w-5" />
                <span>AppMon Agents</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">{dashboardData.appmon.total_agents}</div>
                  <div className="text-sm text-muted-foreground">Total Agents</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">{dashboardData.appmon.online_agents}</div>
                  <div className="text-sm text-muted-foreground">Online</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-600">{dashboardData.appmon.active_alerts}</div>
                  <div className="text-sm text-muted-foreground">Active Alerts</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-orange-600">{dashboardData.appmon.critical_alerts}</div>
                  <div className="text-sm text-muted-foreground">Critical</div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Recent Alerts and Events */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Recent Alerts */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {dashboardData?.recent_alerts.map((alert) => (
                <div key={alert.id} className="p-4 border rounded-lg">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h4 className="font-medium">{alert.title}</h4>
                      <p className="text-sm text-muted-foreground mt-1">
                        {alert.description}
                      </p>
                      <p className="text-xs text-muted-foreground mt-2">
                        {alert.system_name} • {new Date(alert.created_at).toLocaleString()}
                      </p>
                    </div>
                    <div className="ml-4">
                      {getSeverityBadge(alert.severity)}
                    </div>
                  </div>
                </div>
              ))}
              {dashboardData?.recent_alerts.length === 0 && (
                <p className="text-center text-muted-foreground py-4">
                  No recent alerts
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Recent Events */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Events</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {dashboardData?.recent_events.map((event) => (
                <div key={event.id} className="p-4 border rounded-lg">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-mono">ID: {event.event_id}</span>
                        {getEventLevelBadge(event.event_level)}
                      </div>
                      <p className="text-sm text-muted-foreground mt-1">
                        {event.event_message}
                      </p>
                      <p className="text-xs text-muted-foreground mt-2">
                        {event.system_name} • {event.event_source} • {new Date(event.event_time_created).toLocaleString()}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
              {dashboardData?.recent_events.length === 0 && (
                <p className="text-center text-muted-foreground py-4">
                  No recent events
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default MonitoringDashboard;
