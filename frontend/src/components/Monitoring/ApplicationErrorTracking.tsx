import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert';
import { 
  AlertTriangle, 
  Activity, 
  Filter, 
  Search, 
  RefreshCw,
  TrendingUp,
  TrendingDown,
  BarChart3,
  Clock,
  FileText,
  XCircle,
  CheckCircle
} from 'lucide-react';
import { apiClient } from '../../services/api';

interface ErrorEntry {
  id: number;
  application_name: string;
  system_name: string;
  error_type: string;
  message: string;
  severity: string;
  timestamp: string;
  frequency: number;
  status: 'active' | 'resolved' | 'acknowledged';
  file_path: string;
  line_number: number;
  stack_trace?: string;
  context: any;
}

const ApplicationErrorTracking: React.FC = () => {
  const [errors, setErrors] = useState<ErrorEntry[]>([]);
  const [filteredErrors, setFilteredErrors] = useState<ErrorEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [applicationFilter, setApplicationFilter] = useState<string>('all');
  const [showStackTrace, setShowStackTrace] = useState<number | null>(null);

  useEffect(() => {
    fetchErrors();
  }, []);

  useEffect(() => {
    filterErrors();
  }, [errors, searchTerm, severityFilter, statusFilter, applicationFilter]);

  const fetchErrors = async () => {
    try {
      setLoading(true);
      // This would be a new endpoint for error tracking
      const response = await apiClient.get<ErrorEntry[]>('/monitoring/appmon/errors/');
      setErrors(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch errors');
      console.error('Error fetching errors:', err);
    } finally {
      setLoading(false);
    }
  };

  const filterErrors = () => {
    let filtered = errors;

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(err =>
        err.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
        err.application_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        err.system_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        err.error_type.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Filter by severity
    if (severityFilter !== 'all') {
      filtered = filtered.filter(err => err.severity === severityFilter);
    }

    // Filter by status
    if (statusFilter !== 'all') {
      filtered = filtered.filter(err => err.status === statusFilter);
    }

    // Filter by application
    if (applicationFilter !== 'all') {
      filtered = filtered.filter(err => err.application_name === applicationFilter);
    }

    setFilteredErrors(filtered);
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <Badge variant="destructive">Critical</Badge>;
      case 'error':
        return <Badge variant="default" className="bg-red-100 text-red-800">Error</Badge>;
      case 'warning':
        return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">Warning</Badge>;
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
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const getApplications = () => {
    const apps = Array.from(new Set(errors.map(err => err.application_name)));
    return apps.sort();
  };

  const acknowledgeError = async (errorId: number) => {
    try {
      await apiClient.post(`/monitoring/appmon/errors/${errorId}/acknowledge/`);
      fetchErrors(); // Refresh the list
    } catch (err) {
      console.error('Error acknowledging error:', err);
    }
  };

  const resolveError = async (errorId: number) => {
    try {
      await apiClient.post(`/monitoring/appmon/errors/${errorId}/resolve/`);
      fetchErrors(); // Refresh the list
    } catch (err) {
      console.error('Error resolving error:', err);
    }
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
          <h1 className="text-2xl font-bold text-gray-900">Error Tracking</h1>
          <p className="text-gray-600">Track and manage application errors</p>
        </div>
        <Button
          onClick={fetchErrors}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center">
              <AlertTriangle className="w-8 h-8 text-red-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Total Errors</p>
                <p className="text-2xl font-bold text-gray-900">{errors.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center">
              <XCircle className="w-8 h-8 text-red-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Active</p>
                <p className="text-2xl font-bold text-gray-900">
                  {errors.filter(err => err.status === 'active').length}
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
                  {errors.filter(err => err.status === 'resolved').length}
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
              placeholder="Search errors..."
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

      {/* Error Trends */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <TrendingUp className="h-5 w-5" />
              <span>Error Trends</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Critical Errors</span>
                <span className="text-sm text-red-600 font-medium">
                  {errors.filter(err => err.severity === 'critical').length}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">High Frequency</span>
                <span className="text-sm text-orange-600 font-medium">
                  {errors.filter(err => err.frequency > 10).length}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Resolution Rate</span>
                <span className="text-sm text-green-600 font-medium">
                  {errors.length > 0 
                    ? Math.round((errors.filter(err => err.status === 'resolved').length / errors.length) * 100)
                    : 0}%
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Activity className="h-5 w-5" />
              <span>Error Distribution</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {getApplications().slice(0, 5).map(app => {
                const appErrors = errors.filter(err => err.application_name === app);
                return (
                  <div key={app} className="flex items-center justify-between">
                    <span className="text-sm font-medium">{app}</span>
                    <span className="text-sm text-gray-600">
                      {appErrors.length} errors
                    </span>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Error List */}
      <Card>
        <CardHeader>
          <CardTitle>Error Details</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredErrors.length === 0 ? (
              <div className="text-center py-8">
                <AlertTriangle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">No errors found</p>
              </div>
            ) : (
              filteredErrors.map((err) => (
                <div key={err.id} className="p-4 border rounded-lg">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <h4 className="font-medium">{err.error_type}</h4>
                        {getSeverityBadge(err.severity)}
                        {getStatusBadge(err.status)}
                      </div>
                      <p className="text-sm text-gray-700 mb-2">{err.message}</p>
                      <div className="text-xs text-gray-500 space-y-1">
                        <p>Application: {err.application_name} • System: {err.system_name}</p>
                        <p>File: {err.file_path}:{err.line_number}</p>
                        <p>Frequency: {err.frequency} occurrences</p>
                        <p>Time: {formatTimestamp(err.timestamp)}</p>
                      </div>
                    </div>
                    <div className="ml-4 flex flex-col space-y-2">
                      {err.status === 'active' && (
                        <>
                          <Button
                            onClick={() => acknowledgeError(err.id)}
                            variant="outline"
                            size="sm"
                          >
                            Acknowledge
                          </Button>
                          <Button
                            onClick={() => resolveError(err.id)}
                            variant="outline"
                            size="sm"
                          >
                            Resolve
                          </Button>
                        </>
                      )}
                      {err.stack_trace && (
                        <Button
                          onClick={() => setShowStackTrace(showStackTrace === err.id ? null : err.id)}
                          variant="outline"
                          size="sm"
                        >
                          {showStackTrace === err.id ? 'Hide Stack' : 'Show Stack'}
                        </Button>
                      )}
                    </div>
                  </div>
                  
                  {/* Stack Trace */}
                  {showStackTrace === err.id && err.stack_trace && (
                    <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                      <h5 className="text-sm font-medium text-gray-700 mb-2">Stack Trace:</h5>
                      <div className="bg-gray-900 text-gray-100 p-3 rounded font-mono text-sm overflow-x-auto">
                        <pre>{err.stack_trace}</pre>
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

export default ApplicationErrorTracking;
