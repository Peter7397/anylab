import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert';
import { 
  Bell, 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  Clock,
  Search,
  RefreshCw,
  Filter,
  Eye,
  EyeOff,
  BarChart3,
  Settings,
  Download
} from 'lucide-react';
import { apiClient } from '../../services/api';

interface ApplicationAlert {
  id: number;
  application_name: string;
  system_name: string;
  title: string;
  message: string;
  severity: 'critical' | 'error' | 'warning' | 'info';
  status: 'active' | 'acknowledged' | 'resolved' | 'dismissed';
  source_name: string;
  file_path: string;
  line_number: number;
  pattern_matched: string;
  context_lines: string[];
  fingerprint: string;
  created_at: string;
  acknowledged_at: string | null;
  acknowledged_by_name: string | null;
  resolved_at: string | null;
  resolved_by_name: string | null;
  metadata: any;
}

const ApplicationAlertManagement: React.FC = () => {
  const [alerts, setAlerts] = useState<ApplicationAlert[]>([]);
  const [filteredAlerts, setFilteredAlerts] = useState<ApplicationAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [applicationFilter, setApplicationFilter] = useState<string>('all');
  const [showContext, setShowContext] = useState<number | null>(null);
  const [selectedAlerts, setSelectedAlerts] = useState<number[]>([]);

  useEffect(() => {
    fetchAlerts();
  }, []);

  useEffect(() => {
    filterAlerts();
  }, [alerts, searchTerm, severityFilter, statusFilter, applicationFilter]);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get<ApplicationAlert[]>('/monitoring/appmon/alerts/');
      setAlerts(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch alerts');
      console.error('Error fetching alerts:', err);
    } finally {
      setLoading(false);
    }
  };

  const filterAlerts = () => {
    let filtered = alerts;

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(alert =>
        alert.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        alert.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
        alert.application_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        alert.system_name.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Filter by severity
    if (severityFilter !== 'all') {
      filtered = filtered.filter(alert => alert.severity === severityFilter);
    }

    // Filter by status
    if (statusFilter !== 'all') {
      filtered = filtered.filter(alert => alert.status === statusFilter);
    }

    // Filter by application
    if (applicationFilter !== 'all') {
      filtered = filtered.filter(alert => alert.application_name === applicationFilter);
    }

    setFilteredAlerts(filtered);
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <Badge variant="destructive">Critical</Badge>;
      case 'error':
        return <Badge variant="default" className="bg-red-100 text-red-800">Error</Badge>;
      case 'warning':
        return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">Warning</Badge>;
      case 'info':
        return <Badge variant="outline">Info</Badge>;
      default:
        return <Badge variant="outline">{severity}</Badge>;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge variant="destructive">Active</Badge>;
      case 'acknowledged':
        return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">Acknowledged</Badge>;
      case 'resolved':
        return <Badge variant="default" className="bg-green-100 text-green-800">Resolved</Badge>;
      case 'dismissed':
        return <Badge variant="outline">Dismissed</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const getApplications = () => {
    const apps = Array.from(new Set(alerts.map(alert => alert.application_name)));
    return apps.sort();
  };

  const acknowledgeAlert = async (alertId: number) => {
    try {
      await apiClient.post(`/monitoring/appmon/alerts/${alertId}/acknowledge/`);
      fetchAlerts(); // Refresh the list
    } catch (err) {
      console.error('Error acknowledging alert:', err);
    }
  };

  const resolveAlert = async (alertId: number) => {
    try {
      await apiClient.post(`/monitoring/appmon/alerts/${alertId}/resolve/`);
      fetchAlerts(); // Refresh the list
    } catch (err) {
      console.error('Error resolving alert:', err);
    }
  };

  const dismissAlert = async (alertId: number) => {
    try {
      await apiClient.post(`/monitoring/appmon/alerts/${alertId}/dismiss/`);
      fetchAlerts(); // Refresh the list
    } catch (err) {
      console.error('Error dismissing alert:', err);
    }
  };

  const bulkAcknowledge = async () => {
    try {
      await Promise.all(selectedAlerts.map(id => acknowledgeAlert(id)));
      setSelectedAlerts([]);
    } catch (err) {
      console.error('Error bulk acknowledging alerts:', err);
    }
  };

  const bulkResolve = async () => {
    try {
      await Promise.all(selectedAlerts.map(id => resolveAlert(id)));
      setSelectedAlerts([]);
    } catch (err) {
      console.error('Error bulk resolving alerts:', err);
    }
  };

  const downloadAlerts = () => {
    const data = {
      timestamp: new Date().toISOString(),
      alerts: filteredAlerts,
      filters: {
        searchTerm,
        severityFilter,
        statusFilter,
        applicationFilter
      }
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `appmon-alerts-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
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
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Alert Management</h1>
          <p className="text-gray-600">Manage and respond to application alerts</p>
        </div>
        <div className="flex items-center space-x-2">
          {selectedAlerts.length > 0 && (
            <>
              <Button
                onClick={bulkAcknowledge}
                variant="outline"
                size="sm"
              >
                Acknowledge ({selectedAlerts.length})
              </Button>
              <Button
                onClick={bulkResolve}
                variant="outline"
                size="sm"
              >
                Resolve ({selectedAlerts.length})
              </Button>
            </>
          )}
          <Button
            onClick={downloadAlerts}
            variant="outline"
            size="sm"
          >
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
          <Button
            onClick={fetchAlerts}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center">
              <Bell className="w-8 h-8 text-blue-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Total Alerts</p>
                <p className="text-2xl font-bold text-gray-900">{alerts.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center">
              <AlertTriangle className="w-8 h-8 text-red-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Active</p>
                <p className="text-2xl font-bold text-gray-900">
                  {alerts.filter(alert => alert.status === 'active').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center">
              <CheckCircle className="w-8 h-8 text-green-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Resolved</p>
                <p className="text-2xl font-bold text-gray-900">
                  {alerts.filter(alert => alert.status === 'resolved').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center">
              <BarChart3 className="w-8 h-8 text-purple-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Applications</p>
                <p className="text-2xl font-bold text-gray-900">
                  {getApplications().length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Filter className="w-4 h-4 text-gray-500" />
              <span className="text-sm font-medium text-gray-700">Filters:</span>
            </div>
            <Input
              placeholder="Search alerts..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-64"
            />
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm"
            >
              <option value="all">All Severities</option>
              <option value="critical">Critical</option>
              <option value="error">Error</option>
              <option value="warning">Warning</option>
              <option value="info">Info</option>
            </select>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm"
            >
              <option value="all">All Statuses</option>
              <option value="active">Active</option>
              <option value="acknowledged">Acknowledged</option>
              <option value="resolved">Resolved</option>
              <option value="dismissed">Dismissed</option>
            </select>
            <select
              value={applicationFilter}
              onChange={(e) => setApplicationFilter(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm"
            >
              <option value="all">All Applications</option>
              {getApplications().map(app => (
                <option key={app} value={app}>{app}</option>
              ))}
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Alerts List */}
      <Card>
        <CardHeader>
          <CardTitle>Alert Details</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredAlerts.length === 0 ? (
              <div className="text-center py-8">
                <Bell className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">No alerts found</p>
              </div>
            ) : (
              filteredAlerts.map((alert) => (
                <div key={alert.id} className="p-4 border rounded-lg">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3 flex-1">
                      <input
                        type="checkbox"
                        checked={selectedAlerts.includes(alert.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedAlerts([...selectedAlerts, alert.id]);
                          } else {
                            setSelectedAlerts(selectedAlerts.filter(id => id !== alert.id));
                          }
                        }}
                        className="mt-1"
                      />
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <h4 className="font-medium">{alert.title}</h4>
                          {getSeverityBadge(alert.severity)}
                          {getStatusBadge(alert.status)}
                        </div>
                        <p className="text-sm text-gray-700 mb-2">{alert.message}</p>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
                          <div>
                            <p><strong>Application:</strong> {alert.application_name}</p>
                            <p><strong>System:</strong> {alert.system_name}</p>
                            <p><strong>Source:</strong> {alert.source_name}</p>
                          </div>
                          <div>
                            <p><strong>File:</strong> {alert.file_path}</p>
                            {alert.line_number && <p><strong>Line:</strong> {alert.line_number}</p>}
                            {alert.pattern_matched && <p><strong>Pattern:</strong> {alert.pattern_matched}</p>}
                          </div>
                        </div>
                        <div className="mt-3 text-xs text-gray-500">
                          <p>Created: {formatTimestamp(alert.created_at)}</p>
                          {alert.acknowledged_at && (
                            <p>Acknowledged: {formatTimestamp(alert.acknowledged_at)} by {alert.acknowledged_by_name}</p>
                          )}
                          {alert.resolved_at && (
                            <p>Resolved: {formatTimestamp(alert.resolved_at)} by {alert.resolved_by_name}</p>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex flex-col space-y-2">
                      {alert.status === 'active' && (
                        <>
                          <Button
                            onClick={() => acknowledgeAlert(alert.id)}
                            variant="outline"
                            size="sm"
                          >
                            Acknowledge
                          </Button>
                          <Button
                            onClick={() => resolveAlert(alert.id)}
                            variant="outline"
                            size="sm"
                          >
                            Resolve
                          </Button>
                          <Button
                            onClick={() => dismissAlert(alert.id)}
                            variant="outline"
                            size="sm"
                          >
                            Dismiss
                          </Button>
                        </>
                      )}
                      {alert.context_lines && alert.context_lines.length > 0 && (
                        <Button
                          onClick={() => setShowContext(showContext === alert.id ? null : alert.id)}
                          variant="outline"
                          size="sm"
                        >
                          {showContext === alert.id ? 'Hide Context' : 'Show Context'}
                        </Button>
                      )}
                    </div>
                  </div>
                  
                  {/* Context Lines */}
                  {showContext === alert.id && alert.context_lines && alert.context_lines.length > 0 && (
                    <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                      <h5 className="text-sm font-medium text-gray-700 mb-2">Context:</h5>
                      <div className="bg-gray-900 text-gray-100 p-3 rounded font-mono text-sm overflow-x-auto">
                        {alert.context_lines.map((line, index) => (
                          <div key={index} className="whitespace-pre-wrap">{line}</div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ApplicationAlertManagement;
