import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import * as ApiService from '../../services/api';

interface ApplicationAlert {
  id: number;
  module: number;
  module_name: string;
  title: string;
  message: string;
  severity: string;
  alert_type: string;
  status: string;
  acknowledged_by: number | null;
  acknowledged_by_name: string | null;
  resolved_by: number | null;
  resolved_by_name: string | null;
  acknowledged_at: string | null;
  resolved_at: string | null;
  created_at: string;
  updated_at: string;
}

const ApplicationAlerts: React.FC = () => {
  const [alerts, setAlerts] = useState<ApplicationAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');

  useEffect(() => {
    fetchAlerts();
  }, []);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const response = await ApiService.apiClient.get('/monitoring/application/api/application-alerts/');
      if (Array.isArray(response.data)) {
        setAlerts(response.data);
      } else {
        setAlerts([]);
      }
    } catch (err) {
      console.error('Error fetching alerts:', err);
      setError('Failed to fetch alerts');
    } finally {
      setLoading(false);
    }
  };

  const handleAcknowledge = async (alertId: number) => {
    try {
      // This would be implemented with a proper API endpoint
      console.log('Acknowledge alert:', alertId);
      await fetchAlerts(); // Refresh data
    } catch (err) {
      console.error('Error acknowledging alert:', err);
    }
  };

  const handleResolve = async (alertId: number) => {
    try {
      // This would be implemented with a proper API endpoint
      console.log('Resolve alert:', alertId);
      await fetchAlerts(); // Refresh data
    } catch (err) {
      console.error('Error resolving alert:', err);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL': return 'bg-red-500';
      case 'HIGH': return 'bg-orange-500';
      case 'MEDIUM': return 'bg-yellow-500';
      case 'LOW': return 'bg-blue-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ACTIVE': return 'bg-red-500';
      case 'ACKNOWLEDGED': return 'bg-yellow-500';
      case 'RESOLVED': return 'bg-green-500';
      default: return 'bg-gray-500';
    }
  };

  const getTypeBadgeVariant = (type: string) => {
    switch (type) {
      case 'ERROR_RATE': return 'destructive';
      case 'RESPONSE_TIME': return 'secondary';
      case 'MEMORY_USAGE': return 'outline';
      case 'CPU_USAGE': return 'outline';
      case 'DISK_USAGE': return 'outline';
      case 'CONNECTION_FAILURE': return 'destructive';
      case 'AUTHENTICATION_FAILURE': return 'destructive';
      default: return 'outline';
    }
  };

  const filteredAlerts = alerts.filter(alert => {
    const matchesSearch = alert.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         alert.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         alert.module_name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesSeverity = severityFilter === 'all' || alert.severity === severityFilter;
    const matchesStatus = statusFilter === 'all' || alert.status === statusFilter;
    const matchesType = typeFilter === 'all' || alert.alert_type === typeFilter;
    return matchesSearch && matchesSeverity && matchesStatus && matchesType;
  });

  if (loading) {
    return (
      <div className="p-6">
        <div className="text-center">Loading application alerts...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="text-red-500 text-center">{error}</div>
        <Button onClick={fetchAlerts} className="mt-4">Retry</Button>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Application Alerts</h1>
        <Button onClick={fetchAlerts}>Refresh</Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Alerts</CardTitle>
            <Badge variant="outline">{alerts.length}</Badge>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{alerts.length}</div>
            <p className="text-xs text-muted-foreground">
              All time
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Alerts</CardTitle>
            <Badge variant="destructive">
              {alerts.filter(a => a.status === 'ACTIVE').length}
            </Badge>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {alerts.filter(a => a.status === 'ACTIVE').length}
            </div>
            <p className="text-xs text-muted-foreground">
              Require attention
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Critical Alerts</CardTitle>
            <Badge variant="destructive">
              {alerts.filter(a => a.severity === 'CRITICAL' && a.status === 'ACTIVE').length}
            </Badge>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {alerts.filter(a => a.severity === 'CRITICAL' && a.status === 'ACTIVE').length}
            </div>
            <p className="text-xs text-muted-foreground">
              Immediate action needed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Resolved Alerts</CardTitle>
            <Badge variant="outline">
              {alerts.filter(a => a.status === 'RESOLVED').length}
            </Badge>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {alerts.filter(a => a.status === 'RESOLVED').length}
            </div>
            <p className="text-xs text-muted-foreground">
              Successfully resolved
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <div className="flex-1">
          <Input
            placeholder="Search alerts..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <Select value={severityFilter} onValueChange={setSeverityFilter}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Filter by severity" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Severities</SelectItem>
            <SelectItem value="CRITICAL">Critical</SelectItem>
            <SelectItem value="HIGH">High</SelectItem>
            <SelectItem value="MEDIUM">Medium</SelectItem>
            <SelectItem value="LOW">Low</SelectItem>
          </SelectContent>
        </Select>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="ACTIVE">Active</SelectItem>
            <SelectItem value="ACKNOWLEDGED">Acknowledged</SelectItem>
            <SelectItem value="RESOLVED">Resolved</SelectItem>
          </SelectContent>
        </Select>
        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Filter by type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="ERROR_RATE">Error Rate</SelectItem>
            <SelectItem value="RESPONSE_TIME">Response Time</SelectItem>
            <SelectItem value="MEMORY_USAGE">Memory Usage</SelectItem>
            <SelectItem value="CPU_USAGE">CPU Usage</SelectItem>
            <SelectItem value="DISK_USAGE">Disk Usage</SelectItem>
            <SelectItem value="CONNECTION_FAILURE">Connection Failure</SelectItem>
            <SelectItem value="AUTHENTICATION_FAILURE">Authentication Failure</SelectItem>
            <SelectItem value="CUSTOM">Custom</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Alerts List */}
      <Card>
        <CardHeader>
          <CardTitle>Application Alerts</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredAlerts.length === 0 ? (
              <div className="text-center text-muted-foreground py-8">
                No alerts found
              </div>
            ) : (
              filteredAlerts.map((alert) => (
                <div
                  key={alert.id}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
                >
                  <div className="flex items-center space-x-4">
                    <div className={`w-3 h-3 rounded-full ${getSeverityColor(alert.severity)}`} />
                    <div>
                      <h3 className="font-medium">{alert.title}</h3>
                      <p className="text-sm text-muted-foreground">{alert.message}</p>
                      <p className="text-xs text-muted-foreground">
                        Module: {alert.module_name} • Created: {new Date(alert.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <Badge variant={getTypeBadgeVariant(alert.alert_type)}>
                      {alert.alert_type.replace('_', ' ')}
                    </Badge>
                    <Badge variant={alert.severity === 'CRITICAL' ? 'destructive' : 'secondary'}>
                      {alert.severity}
                    </Badge>
                    <Badge variant={alert.status === 'ACTIVE' ? 'destructive' : 'outline'}>
                      {alert.status}
                    </Badge>
                    <div className="flex space-x-2">
                      {alert.status === 'ACTIVE' && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={(e) => {
                            e?.stopPropagation();
                            handleAcknowledge(alert.id);
                          }}
                        >
                          Acknowledge
                        </Button>
                      )}
                      {alert.status !== 'RESOLVED' && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={(e) => {
                            e?.stopPropagation();
                            handleResolve(alert.id);
                          }}
                        >
                          Resolve
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ApplicationAlerts;
