import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert';
import {
  Database,
  AlertTriangle,
  Server,
  Activity,
  Clock,
  TrendingUp,
  TrendingDown,
  CheckCircle,
  XCircle,
  Zap,
  HardDrive,
  Network
} from 'lucide-react';
import * as ApiService from '../../services/api';

interface DatabaseSummary {
  id: number;
  name: string;
  host: string;
  port: number;
  database_name: string;
  db_type: string;
  is_active: boolean;
  monitoring_enabled: boolean;
  status: string;
  alert_count: number;
  last_metrics?: {
    active_connections: number;
    connection_utilization: number;
    queries_per_second: number;
    avg_query_time: number;
    cache_hit_ratio: number;
    timestamp: string;
  };
  created_at: string;
}

interface DatabaseAlert {
  id: number;
  database_name: string;
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  alert_type: string;
  status: string;
  created_at: string;
}

interface DatabaseQuery {
  id: number;
  database_name: string;
  query_text: string;
  execution_time: number;
  query_type: string;
  table_name: string;
  is_slow: boolean;
  timestamp: string;
}

interface ConnectionPool {
  id: number;
  database_name: string;
  total_connections: number;
  active_connections: number;
  idle_connections: number;
  waiting_connections: number;
  pool_utilization: number;
  pool_healthy: boolean;
  timestamp: string;
}

interface DashboardData {
  databases: {
    total: number;
    active: number;
    monitored: number;
    offline: number;
  };
  alerts: {
    total: number;
    active: number;
    critical: number;
  };
  queries: {
    total: number;
    slow: number;
    recent_24h: number;
  };
  recent_alerts: DatabaseAlert[];
  recent_queries: DatabaseQuery[];
  connection_pools: ConnectionPool[];
}

const DatabaseMonitoringDashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [databases, setDatabases] = useState<DatabaseSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDashboardData();
    fetchDatabases();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await ApiService.apiClient.get('/monitoring/database/dashboard/summary/');
      if (Array.isArray(response.data)) {
        // If response.data is an array, it's not the expected format
        setDashboardData(null);
      } else {
        setDashboardData(response.data as DashboardData);
      }
    } catch (err) {
      setError('Failed to load dashboard data');
      console.error('Error fetching dashboard data:', err);
    }
  };

  const fetchDatabases = async () => {
    try {
      const response = await ApiService.apiClient.get('/monitoring/database/dashboard/databases/');
      if (Array.isArray(response.data)) {
        setDatabases(response.data as DatabaseSummary[]);
      } else {
        setDatabases([]);
      }
    } catch (err) {
      setError('Failed to load databases data');
      console.error('Error fetching databases:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online':
        return 'bg-green-100 text-green-800';
      case 'offline':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800';
      case 'high':
        return 'bg-orange-100 text-orange-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'low':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-lg">Loading database monitoring dashboard...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Database Monitoring Dashboard</h1>
        <Button onClick={fetchDashboardData} variant="outline">
          <Activity className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Summary Cards */}
      {dashboardData && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Databases</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{dashboardData.databases.total}</div>
              <p className="text-xs text-muted-foreground">
                {dashboardData.databases.active} active, {dashboardData.databases.offline} offline
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
              <CardTitle className="text-sm font-medium">Slow Queries</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{dashboardData.queries.slow}</div>
              <p className="text-xs text-muted-foreground">
                {dashboardData.queries.recent_24h} in last 24h
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Connection Pools</CardTitle>
              <Network className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{dashboardData.connection_pools.length}</div>
              <p className="text-xs text-muted-foreground">
                {dashboardData.connection_pools.filter(p => p.pool_healthy).length} healthy
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Database List */}
      <Card>
        <CardHeader>
          <CardTitle>Database Instances</CardTitle>
        </CardHeader>
        <CardContent>
          {Array.isArray(databases) && databases.length > 0 ? (
            <div className="space-y-4">
              {databases.map((db) => (
                <div key={db.id} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center space-x-4">
                    <div className="flex-shrink-0">
                      <Database className="h-8 w-8 text-blue-600" />
                    </div>
                    <div>
                      <h3 className="text-lg font-medium">{db.name}</h3>
                      <p className="text-sm text-gray-500">
                        {db.host}:{db.port} - {db.database_name} ({db.db_type})
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <Badge className={getStatusColor(db.status)}>
                      {db.status}
                    </Badge>
                    {db.alert_count > 0 && (
                      <Badge variant="destructive">
                        {db.alert_count} alerts
                      </Badge>
                    )}
                    {db.last_metrics && (
                      <div className="text-sm text-gray-500">
                        <div>Conn: {db.last_metrics.active_connections}</div>
                        <div>QPS: {db.last_metrics.queries_per_second.toFixed(1)}</div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <Database className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">No databases configured</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recent Alerts */}
      {dashboardData && Array.isArray(dashboardData.recent_alerts) && dashboardData.recent_alerts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {dashboardData.recent_alerts.map((alert) => (
                <div key={alert.id} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center space-x-4">
                    <AlertTriangle className="h-5 w-5 text-red-500" />
                    <div>
                      <h4 className="font-medium">{alert.title}</h4>
                      <p className="text-sm text-gray-500">{alert.database_name}</p>
                      <p className="text-sm text-gray-600">{alert.description}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge className={getSeverityColor(alert.severity)}>
                      {alert.severity}
                    </Badge>
                    <span className="text-sm text-gray-500">
                      {new Date(alert.created_at).toLocaleString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Slow Queries */}
      {dashboardData && Array.isArray(dashboardData.recent_queries) && dashboardData.recent_queries.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Slow Queries</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {dashboardData.recent_queries.map((query) => (
                <div key={query.id} className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <Clock className="h-4 w-4 text-orange-500" />
                      <span className="font-medium">{query.database_name}</span>
                      <Badge variant="outline">{query.query_type}</Badge>
                      {query.is_slow && (
                        <Badge variant="destructive">Slow</Badge>
                      )}
                    </div>
                    <span className="text-sm text-gray-500">
                      {query.execution_time.toFixed(2)}ms
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 font-mono bg-gray-50 p-2 rounded">
                    {query.query_text.substring(0, 100)}...
                  </p>
                  {query.table_name && (
                    <p className="text-xs text-gray-500 mt-1">
                      Table: {query.table_name}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Connection Pools */}
      {dashboardData && Array.isArray(dashboardData.connection_pools) && dashboardData.connection_pools.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Connection Pools</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {dashboardData.connection_pools.map((pool) => (
                <div key={pool.id} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center space-x-4">
                    <Network className="h-5 w-5 text-blue-500" />
                    <div>
                      <h4 className="font-medium">{pool.database_name}</h4>
                      <p className="text-sm text-gray-500">
                        {pool.active_connections}/{pool.total_connections} active connections
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="text-right">
                      <div className="text-sm font-medium">
                        {pool.pool_utilization.toFixed(1)}% utilization
                      </div>
                      <div className="text-xs text-gray-500">
                        {pool.idle_connections} idle, {pool.waiting_connections} waiting
                      </div>
                    </div>
                    <Badge className={pool.pool_healthy ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                      {pool.pool_healthy ? 'Healthy' : 'Unhealthy'}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default DatabaseMonitoringDashboard;
