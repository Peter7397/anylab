import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert';
import { 
  FileSearch, 
  Activity, 
  Filter, 
  Search, 
  RefreshCw,
  Download,
  Eye,
  EyeOff,
  BarChart3,
  Clock,
  FileText,
  AlertTriangle
} from 'lucide-react';
import { apiClient } from '../../services/api';

interface LogEntry {
  id: number;
  application_name: string;
  system_name: string;
  file_path: string;
  line_number: number;
  message: string;
  severity: string;
  timestamp: string;
  pattern_matched: string;
  context_lines: string[];
}

const ApplicationLogAnalysis: React.FC = () => {
  const [logEntries, setLogEntries] = useState<LogEntry[]>([]);
  const [filteredEntries, setFilteredEntries] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [applicationFilter, setApplicationFilter] = useState<string>('all');
  const [showContext, setShowContext] = useState<number | null>(null);
  const [dateRange, setDateRange] = useState<string>('24h');

  useEffect(() => {
    fetchLogEntries();
  }, [dateRange]);

  useEffect(() => {
    filterLogEntries();
  }, [logEntries, searchTerm, severityFilter, applicationFilter]);

  const fetchLogEntries = async () => {
    try {
      setLoading(true);
      // This would be a new endpoint for log analysis
      const response = await apiClient.get<LogEntry[]>('/monitoring/appmon/logs/');
      setLogEntries(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch log entries');
      console.error('Error fetching log entries:', err);
    } finally {
      setLoading(false);
    }
  };

  const filterLogEntries = () => {
    let filtered = logEntries;

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(entry =>
        entry.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
        entry.application_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        entry.system_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        entry.file_path.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Filter by severity
    if (severityFilter !== 'all') {
      filtered = filtered.filter(entry => entry.severity === severityFilter);
    }

    // Filter by application
    if (applicationFilter !== 'all') {
      filtered = filtered.filter(entry => entry.application_name === applicationFilter);
    }

    setFilteredEntries(filtered);
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

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const getApplications = () => {
    const apps = Array.from(new Set(logEntries.map(entry => entry.application_name)));
    return apps.sort();
  };

  const downloadLogs = () => {
    const data = {
      timestamp: new Date().toISOString(),
      entries: filteredEntries,
      filters: {
        searchTerm,
        severityFilter,
        applicationFilter,
        dateRange
      }
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `appmon-logs-${new Date().toISOString().split('T')[0]}.json`;
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
          <h1 className="text-2xl font-bold text-gray-900">Log Analysis</h1>
          <p className="text-gray-600">Analyze application logs and patterns</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            onClick={downloadLogs}
            variant="outline"
            size="sm"
          >
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
          <Button
            onClick={fetchLogEntries}
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
              <FileSearch className="w-8 h-8 text-blue-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Total Entries</p>
                <p className="text-2xl font-bold text-gray-900">{logEntries.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center">
              <AlertTriangle className="w-8 h-8 text-red-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Errors</p>
                <p className="text-2xl font-bold text-gray-900">
                  {logEntries.filter(entry => entry.severity === 'error').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center">
              <FileText className="w-8 h-8 text-purple-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Applications</p>
                <p className="text-2xl font-bold text-gray-900">
                  {getApplications().length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center">
              <BarChart3 className="w-8 h-8 text-green-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Patterns</p>
                <p className="text-2xl font-bold text-gray-900">
                  {new Set(logEntries.map(entry => entry.pattern_matched)).size}
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
              placeholder="Search logs..."
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
              value={applicationFilter}
              onChange={(e) => setApplicationFilter(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm"
            >
              <option value="all">All Applications</option>
              {getApplications().map(app => (
                <option key={app} value={app}>{app}</option>
              ))}
            </select>
            <select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm"
            >
              <option value="1h">Last Hour</option>
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Log Entries */}
      <Card>
        <CardHeader>
          <CardTitle>Log Entries</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredEntries.length === 0 ? (
              <div className="text-center py-8">
                <FileSearch className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">No log entries found</p>
              </div>
            ) : (
              filteredEntries.map((entry) => (
                <div key={entry.id} className="p-4 border rounded-lg">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <h4 className="font-medium">{entry.application_name}</h4>
                        {getSeverityBadge(entry.severity)}
                        <span className="text-sm text-gray-500">
                          {entry.system_name}
                        </span>
                      </div>
                      <p className="text-sm text-gray-700 mb-2">{entry.message}</p>
                      <div className="text-xs text-gray-500 space-y-1">
                        <p>File: {entry.file_path}:{entry.line_number}</p>
                        <p>Pattern: {entry.pattern_matched}</p>
                        <p>Time: {formatTimestamp(entry.timestamp)}</p>
                      </div>
                    </div>
                    <div className="ml-4">
                      {entry.context_lines && entry.context_lines.length > 0 && (
                        <Button
                          onClick={() => setShowContext(showContext === entry.id ? null : entry.id)}
                          variant="outline"
                          size="sm"
                        >
                          {showContext === entry.id ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                        </Button>
                      )}
                    </div>
                  </div>
                  
                  {/* Context Lines */}
                  {showContext === entry.id && entry.context_lines && entry.context_lines.length > 0 && (
                    <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                      <h5 className="text-sm font-medium text-gray-700 mb-2">Context:</h5>
                      <div className="bg-gray-900 text-gray-100 p-3 rounded font-mono text-sm overflow-x-auto">
                        {entry.context_lines.map((line, index) => (
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

export default ApplicationLogAnalysis;
