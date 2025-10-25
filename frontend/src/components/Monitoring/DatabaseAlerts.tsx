import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert';
import {
  AlertTriangle,
  Search,
  RefreshCw,
  CheckCircle,
  XCircle,
  Clock,
  Database,
  Filter
} from 'lucide-react';
import * as ApiService from '../../services/api';

interface DatabaseAlert {
  id: number;
  database_name: string;
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  alert_type: string;
  status: string;
  created_at: string;
  acknowledged_at?: string;
  resolved_at?: string;
  acknowledged_by_username?: string;
  resolved_by_username?: string;
}

const DatabaseAlerts: React.FC = () => {
  const [alerts, setAlerts] = useState<DatabaseAlert[]>([]);
  const [filteredAlerts, setFilteredAlerts] = useState<DatabaseAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [alertTypeFilter, setAlertTypeFilter] = useState<string>('all');

  useEffect(() => {
    fetchAlerts();
  }, []);

  useEffect(() => {
    filterAlerts();
  }, [alerts, searchTerm, severityFilter, statusFilter, alertTypeFilter]);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const response = await ApiService.apiClient.get('/monitoring/api/db-alerts/');
      if (Array.isArray(response.data)) {
        setAlerts(response.data as DatabaseAlert[]);
      } else {
        setAlerts([]);
      }
    } catch (err) {
      setError('Failed to load alerts');
      console.error('Error fetching alerts:', err);
    } finally {
      setLoading(false);
    }
  };

  const filterAlerts = () => {
    let filtered = Array.isArray(alerts) ? alerts : [];

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(alert =>
        alert.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        alert.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        alert.database_name.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Apply severity filter
    if (severityFilter !== 'all') {
      filtered = filtered.filter(alert => alert.severity === severityFilter);
    }

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(alert => alert.status === statusFilter);
    }

    // Apply alert type filter
    if (alertTypeFilter !== 'all') {
      filtered = filtered.filter(alert => alert.alert_type === alertTypeFilter);
    }

    setFilteredAlerts(filtered);
  };

  const handleAcknowledgeAlert = async (alertId: number) => {
    try {
      await ApiService.apiClient.post(`/monitoring/api/db-alerts/${alertId}/acknowledge/`);
      fetchAlerts(); // Refresh the list
    } catch (err) {
      console.error('Error acknowledging alert:', err);
    }
  };

  const handleResolveAlert = async (alertId: number) => {
    try {
      await ApiService.apiClient.post(`/monitoring/api/db-alerts/${alertId}/resolve/`);
      fetchAlerts(); // Refresh the list
    } catch (err) {
      console.error('Error resolving alert:', err);
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-red-100 text-red-800';
      case 'acknowledged':
        return 'bg-yellow-100 text-yellow-800';
      case 'resolved':
        return 'bg-green-100 text-green-800';
      case 'dismissed':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getAlertTypeIcon = (alertType: string) => {
    switch (alertType) {
      case 'connection_failed':
        return '🔌';
      case 'high_utilization':
        return '📈';
      case 'slow_queries':
        return '🐌';
      case 'connection_errors':
        return '❌';
      case 'storage_full':
        return '💾';
      case 'cache_miss':
        return '🎯';
      case 'lock_timeout':
        return '🔒';
      case 'query_timeout':
        return '⏰';
      default:
        return '⚠️';
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-lg">Loading database alerts...</div>
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
        <h1 className="text-3xl font-bold">Database Alerts</h1>
        <Button onClick={fetchAlerts} variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
              <Input
                placeholder="Search alerts..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={severityFilter} onValueChange={setSeverityFilter}>
              <SelectTrigger>
                <SelectValue placeholder="Severity" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Severities</SelectItem>
                <SelectItem value="critical">Critical</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="low">Low</SelectItem>
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger>
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="acknowledged">Acknowledged</SelectItem>
                <SelectItem value="resolved">Resolved</SelectItem>
                <SelectItem value="dismissed">Dismissed</SelectItem>
              </SelectContent>
            </Select>
            <Select value={alertTypeFilter} onValueChange={setAlertTypeFilter}>
              <SelectTrigger>
                <SelectValue placeholder="Alert Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="connection_failed">Connection Failed</SelectItem>
                <SelectItem value="high_utilization">High Utilization</SelectItem>
                <SelectItem value="slow_queries">Slow Queries</SelectItem>
                <SelectItem value="connection_errors">Connection Errors</SelectItem>
                <SelectItem value="storage_full">Storage Full</SelectItem>
                <SelectItem value="cache_miss">Cache Miss</SelectItem>
                <SelectItem value="lock_timeout">Lock Timeout</SelectItem>
                <SelectItem value="query_timeout">Query Timeout</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Alerts List */}
      <Card>
        <CardHeader>
          <CardTitle>
            Alerts ({filteredAlerts.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {Array.isArray(filteredAlerts) && filteredAlerts.length > 0 ? (
            <div className="space-y-4">
              {filteredAlerts.map((alert) => (
                <div key={alert.id} className="p-4 border rounded-lg">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-4">
                      <div className="flex-shrink-0">
                        <span className="text-2xl">{getAlertTypeIcon(alert.alert_type)}</span>
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <h3 className="text-lg font-medium">{alert.title}</h3>
                          <Badge className={getSeverityColor(alert.severity)}>
                            {alert.severity}
                          </Badge>
                          <Badge className={getStatusColor(alert.status)}>
                            {alert.status}
                          </Badge>
                        </div>
                        <p className="text-sm text-gray-600 mb-2">{alert.description}</p>
                        <div className="flex items-center space-x-4 text-sm text-gray-500">
                          <span className="flex items-center">
                            <Database className="h-4 w-4 mr-1" />
                            {alert.database_name}
                          </span>
                          <span className="flex items-center">
                            <Clock className="h-4 w-4 mr-1" />
                            {new Date(alert.created_at).toLocaleString()}
                          </span>
                          {alert.acknowledged_at && (
                            <span className="flex items-center">
                              <CheckCircle className="h-4 w-4 mr-1" />
                              Acknowledged: {new Date(alert.acknowledged_at).toLocaleString()}
                              {alert.acknowledged_by_username && ` by ${alert.acknowledged_by_username}`}
                            </span>
                          )}
                          {alert.resolved_at && (
                            <span className="flex items-center">
                              <XCircle className="h-4 w-4 mr-1" />
                              Resolved: {new Date(alert.resolved_at).toLocaleString()}
                              {alert.resolved_by_username && ` by ${alert.resolved_by_username}`}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex space-x-2">
                      {alert.status === 'active' && (
                        <>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleAcknowledgeAlert(alert.id)}
                          >
                            <CheckCircle className="h-4 w-4 mr-1" />
                            Acknowledge
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleResolveAlert(alert.id)}
                          >
                            <XCircle className="h-4 w-4 mr-1" />
                            Resolve
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <AlertTriangle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">
                {Array.isArray(alerts) && alerts.length === 0 
                  ? 'No database alerts found' 
                  : 'No alerts match your filters'}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Summary Stats */}
      {Array.isArray(alerts) && alerts.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">{alerts.length}</div>
              <p className="text-xs text-muted-foreground">Total Alerts</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">
                {alerts.filter(alert => alert.status === 'active').length}
              </div>
              <p className="text-xs text-muted-foreground">Active</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">
                {alerts.filter(alert => alert.severity === 'critical').length}
              </div>
              <p className="text-xs text-muted-foreground">Critical</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">
                {alerts.filter(alert => alert.status === 'resolved').length}
              </div>
              <p className="text-xs text-muted-foreground">Resolved</p>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default DatabaseAlerts;
