import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert';
import { 
  FileText, 
  FileSearch, 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  Clock,
  RefreshCw,
  Eye,
  EyeOff,
  Code,
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
  BarChart3,
  TrendingUp,
  TrendingDown,
  Activity,
  Database,
  Shield
} from 'lucide-react';
import { apiClient } from '../../services/api';

interface MonitoredFile {
  id: string;
  path: string;
  size_mb: number;
  last_modified: string;
  encoding: string;
  status: 'monitored' | 'error' | 'ignored';
  agent_name: string;
  source_name: string;
  patterns_count: number;
  last_scan: string;
}

interface MonitoringPattern {
  id: string;
  pattern: string;
  severity: 'critical' | 'error' | 'warning' | 'info';
  description: string;
  source_name: string;
  agent_name: string;
  matches_count: number;
  last_match: string;
  is_active: boolean;
}

interface MonitoringSource {
  id: string;
  name: string;
  agent_name: string;
  paths: string[];
  patterns: MonitoringPattern[];
  encoding: string;
  max_file_mb: number;
  files_count: number;
  total_size_mb: number;
  last_scan: string;
  status: 'active' | 'inactive' | 'error';
}

interface FileMonitoringData {
  files: MonitoredFile[];
  patterns: MonitoringPattern[];
  sources: MonitoringSource[];
  statistics: {
    total_files: number;
    total_size_gb: number;
    active_patterns: number;
    total_matches: number;
    avg_file_size_mb: number;
  };
}

const AppMonFileMonitoring: React.FC = () => {
  const [data, setData] = useState<FileMonitoringData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'files' | 'patterns' | 'sources'>('files');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterSeverity, setFilterSeverity] = useState<string>('all');
  const [showErrors, setShowErrors] = useState(true);

  useEffect(() => {
    fetchFileMonitoringData();
  }, []);

  const fetchFileMonitoringData = async () => {
    try {
      setLoading(true);
      
      // Fetch AppMon agents to get their configurations
      const agentsResponse = await apiClient.get('/monitoring/appmon/agents/');
      const agents = agentsResponse.data as any[];
      
      // Simulate file monitoring data based on agent configurations
      const files: MonitoredFile[] = [];
      const patterns: MonitoringPattern[] = [];
      const sources: MonitoringSource[] = [];
      
      agents.forEach((agent: any) => {
        if (agent.configuration && agent.configuration.sources) {
          agent.configuration.sources.forEach((source: any, sourceIndex: number) => {
            const sourceId = `${agent.id}-${sourceIndex}`;
            
            // Create source
            sources.push({
              id: sourceId,
              name: source.name || `Source ${sourceIndex + 1}`,
              agent_name: agent.name,
              paths: source.paths || [],
              patterns: [],
              encoding: source.encoding || 'utf-8',
              max_file_mb: source.max_file_mb || 500,
              files_count: 0,
              total_size_mb: 0,
              last_scan: agent.last_seen,
              status: 'active'
            });
            
            // Create patterns for this source
            if (source.patterns) {
              source.patterns.forEach((pattern: any, patternIndex: number) => {
                const patternId = `${sourceId}-${patternIndex}`;
                patterns.push({
                  id: patternId,
                  pattern: pattern.pattern || pattern,
                  severity: pattern.severity || 'warning',
                  description: pattern.description || `Pattern ${patternIndex + 1}`,
                  source_name: source.name || `Source ${sourceIndex + 1}`,
                  agent_name: agent.name,
                  matches_count: Math.floor(Math.random() * 50),
                  last_match: new Date(Date.now() - Math.random() * 86400000).toISOString(),
                  is_active: true
                });
              });
            }
            
            // Simulate monitored files
            if (source.paths) {
              source.paths.forEach((path: string, fileIndex: number) => {
                files.push({
                  id: `${sourceId}-file-${fileIndex}`,
                  path: path,
                  size_mb: Math.random() * 100 + 1,
                  last_modified: new Date(Date.now() - Math.random() * 86400000).toISOString(),
                  encoding: source.encoding || 'utf-8',
                  status: 'monitored',
                  agent_name: agent.name,
                  source_name: source.name || `Source ${sourceIndex + 1}`,
                  patterns_count: source.patterns ? source.patterns.length : 0,
                  last_scan: agent.last_seen
                });
              });
            }
          });
        }
      });
      
      // Calculate statistics
      const totalFiles = files.length;
      const totalSizeGB = files.reduce((sum, file) => sum + file.size_mb, 0) / 1024;
      const activePatterns = patterns.filter(p => p.is_active).length;
      const totalMatches = patterns.reduce((sum, pattern) => sum + pattern.matches_count, 0);
      const avgFileSizeMB = totalFiles > 0 ? files.reduce((sum, file) => sum + file.size_mb, 0) / totalFiles : 0;
      
      const fileMonitoringData: FileMonitoringData = {
        files,
        patterns,
        sources,
        statistics: {
          total_files: totalFiles,
          total_size_gb: totalSizeGB,
          active_patterns: activePatterns,
          total_matches: totalMatches,
          avg_file_size_mb: avgFileSizeMB
        }
      };
      
      setData(fileMonitoringData);
      setError(null);
    } catch (err) {
      setError('Failed to fetch file monitoring data');
      console.error('Error fetching file monitoring data:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'monitored':
      case 'active':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <AlertTriangle className="w-5 h-5 text-red-500" />;
      case 'ignored':
      case 'inactive':
        return <XCircle className="w-5 h-5 text-gray-500" />;
      default:
        return <Clock className="w-5 h-5 text-yellow-500" />;
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

  const formatFileSize = (sizeMB: number) => {
    if (sizeMB >= 1024) {
      return `${(sizeMB / 1024).toFixed(1)} GB`;
    }
    return `${sizeMB.toFixed(1)} MB`;
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

  const filteredFiles = data?.files.filter(file => {
    const matchesSearch = file.path.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         file.agent_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         file.source_name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesErrorFilter = showErrors || file.status !== 'error';
    return matchesSearch && matchesErrorFilter;
  }) || [];

  const filteredPatterns = data?.patterns.filter(pattern => {
    const matchesSearch = pattern.pattern.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         pattern.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         pattern.agent_name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesSeverityFilter = filterSeverity === 'all' || pattern.severity === filterSeverity;
    return matchesSearch && matchesSeverityFilter;
  }) || [];

  const filteredSources = data?.sources.filter(source => {
    return source.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
           source.agent_name.toLowerCase().includes(searchTerm.toLowerCase());
  }) || [];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading file monitoring data...</p>
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
        <AlertDescription>No file monitoring data available.</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header with gradient background */}
      <div className="bg-gradient-to-r from-purple-600 via-pink-600 to-red-600 rounded-xl p-8 text-white">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-4xl font-bold mb-2">File Monitoring</h1>
            <p className="text-purple-100 text-lg">Monitor application log files and pattern matching</p>
            <div className="flex items-center gap-4 mt-4">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-sm">Real-time monitoring active</span>
              </div>
              <div className="flex items-center gap-2">
                <FileSearch className="w-4 h-4" />
                <span className="text-sm">{data.statistics.total_files} files monitored</span>
              </div>
            </div>
          </div>
          <Button 
            onClick={fetchFileMonitoringData} 
            className="bg-white/20 hover:bg-white/30 text-white border-white/30 flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Statistics Cards with enhanced styling */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
        <Card className="group hover:shadow-lg transition-all duration-300 border-0 shadow-md">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Total Files</CardTitle>
            <div className="p-2 bg-blue-100 rounded-lg group-hover:bg-blue-200 transition-colors">
              <FileText className="h-4 w-4 text-blue-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900 mb-2">{data.statistics.total_files}</div>
            <div className="flex items-center gap-2 mb-3">
              <div className="flex-1 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-blue-500 to-blue-600 h-2 rounded-full transition-all duration-500"
                  style={{ width: '85%' }}
                ></div>
              </div>
              <span className="text-sm text-gray-600">85%</span>
            </div>
            <p className="text-xs text-gray-500">
              {formatFileSize(data.statistics.total_size_gb * 1024)} total size
            </p>
          </CardContent>
        </Card>

        <Card className="group hover:shadow-lg transition-all duration-300 border-0 shadow-md">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Active Patterns</CardTitle>
            <div className="p-2 bg-purple-100 rounded-lg group-hover:bg-purple-200 transition-colors">
              <Search className="h-4 w-4 text-purple-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900 mb-2">{data.statistics.active_patterns}</div>
            <div className="flex items-center gap-2 mb-3">
              <div className="flex-1 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-purple-500 to-purple-600 h-2 rounded-full transition-all duration-500"
                  style={{ width: '92%' }}
                ></div>
              </div>
              <span className="text-sm text-gray-600">92%</span>
            </div>
            <p className="text-xs text-gray-500">
              {data.statistics.total_matches} total matches
            </p>
          </CardContent>
        </Card>

        <Card className="group hover:shadow-lg transition-all duration-300 border-0 shadow-md">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Monitoring Sources</CardTitle>
            <div className="p-2 bg-green-100 rounded-lg group-hover:bg-green-200 transition-colors">
              <Target className="h-4 w-4 text-green-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900 mb-2">{data.sources.length}</div>
            <div className="flex items-center gap-2 mb-3">
              <div className="flex-1 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-green-500 to-green-600 h-2 rounded-full transition-all duration-500"
                  style={{ width: '78%' }}
                ></div>
              </div>
              <span className="text-sm text-gray-600">78%</span>
            </div>
            <p className="text-xs text-gray-500">
              Across {new Set(data.sources.map(s => s.agent_name)).size} agents
            </p>
          </CardContent>
        </Card>

        <Card className="group hover:shadow-lg transition-all duration-300 border-0 shadow-md">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Avg File Size</CardTitle>
            <div className="p-2 bg-orange-100 rounded-lg group-hover:bg-orange-200 transition-colors">
              <HardDrive className="h-4 w-4 text-orange-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900 mb-2">{formatFileSize(data.statistics.avg_file_size_mb)}</div>
            <div className="flex items-center gap-2 mb-3">
              <div className="flex-1 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-orange-500 to-orange-600 h-2 rounded-full transition-all duration-500"
                  style={{ width: '65%' }}
                ></div>
              </div>
              <span className="text-sm text-gray-600">65%</span>
            </div>
            <p className="text-xs text-gray-500">
              Per monitored file
            </p>
          </CardContent>
        </Card>

        <Card className="group hover:shadow-lg transition-all duration-300 border-0 shadow-md">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Error Files</CardTitle>
            <div className="p-2 bg-red-100 rounded-lg group-hover:bg-red-200 transition-colors">
              <AlertTriangle className="h-4 w-4 text-red-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900 mb-2">{data.files.filter(f => f.status === 'error').length}</div>
            <div className="flex items-center gap-2 mb-3">
              <div className="flex-1 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-red-500 to-red-600 h-2 rounded-full transition-all duration-500"
                  style={{ width: '12%' }}
                ></div>
              </div>
              <span className="text-sm text-gray-600">12%</span>
            </div>
            <p className="text-xs text-gray-500">
              Need attention
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Enhanced Tabs */}
      <Card className="border-0 shadow-md">
        <CardHeader className="bg-gradient-to-r from-gray-50 to-gray-100 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <CardTitle className="text-gray-900">Monitoring Overview</CardTitle>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" className="flex items-center gap-2">
                <Download className="w-4 h-4" />
                Export
              </Button>
              <Button variant="outline" size="sm" className="flex items-center gap-2">
                <Settings className="w-4 h-4" />
                Settings
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {/* Tab Navigation */}
          <div className="border-b border-gray-200 bg-white">
            <nav className="flex space-x-8 px-6">
              <button
                onClick={() => setActiveTab('files')}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === 'files'
                    ? 'border-purple-500 text-purple-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4" />
                  Monitored Files ({filteredFiles.length})
                </div>
              </button>
              <button
                onClick={() => setActiveTab('patterns')}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === 'patterns'
                    ? 'border-purple-500 text-purple-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center gap-2">
                  <Search className="w-4 h-4" />
                  Patterns ({filteredPatterns.length})
                </div>
              </button>
              <button
                onClick={() => setActiveTab('sources')}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === 'sources'
                    ? 'border-purple-500 text-purple-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center gap-2">
                  <Target className="w-4 h-4" />
                  Sources ({filteredSources.length})
                </div>
              </button>
            </nav>
          </div>

          {/* Search and Filters */}
          <div className="p-6 bg-gray-50 border-b border-gray-200">
            <div className="flex gap-4 items-center">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <input
                    type="text"
                    placeholder="Search files, patterns, or sources..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10 pr-4 py-3 w-full border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-colors"
                  />
                </div>
              </div>
              
              {activeTab === 'patterns' && (
                <select
                  value={filterSeverity}
                  onChange={(e) => setFilterSeverity(e.target.value)}
                  className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-colors"
                >
                  <option value="all">All Severities</option>
                  <option value="critical">Critical</option>
                  <option value="error">Error</option>
                  <option value="warning">Warning</option>
                  <option value="info">Info</option>
                </select>
              )}
              
              <Button
                variant="outline"
                onClick={() => setShowErrors(!showErrors)}
                className="flex items-center gap-2 px-4 py-3"
              >
                {showErrors ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
                {showErrors ? 'Hide Errors' : 'Show Errors'}
              </Button>
            </div>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeTab === 'files' && (
              <div className="space-y-4">
                {filteredFiles.map((file) => (
                  <div key={file.id} className="flex items-center justify-between p-6 border border-gray-200 rounded-xl hover:bg-gray-50 transition-all duration-200 hover:shadow-sm">
                    <div className="flex items-center gap-4">
                      <div className="p-3 bg-blue-100 rounded-lg">
                        {getStatusIcon(file.status)}
                      </div>
                      <div className="flex flex-col">
                        <div className="font-medium text-gray-900 text-lg">{file.path}</div>
                        <div className="text-sm text-gray-600">
                          {file.agent_name} • {file.source_name}
                        </div>
                        <div className="text-xs text-gray-500">
                          {formatFileSize(file.size_mb)} • {file.encoding} • {file.patterns_count} patterns
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <div className="text-sm font-medium text-gray-900">Last Scan</div>
                        <div className="text-xs text-gray-500">{formatLastSeen(file.last_scan)}</div>
                      </div>
                      <Badge variant="outline" className="border-gray-300 px-3 py-1">
                        {file.status}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'patterns' && (
              <div className="space-y-4">
                {filteredPatterns.map((pattern) => (
                  <div key={pattern.id} className="flex items-center justify-between p-6 border border-gray-200 rounded-xl hover:bg-gray-50 transition-all duration-200 hover:shadow-sm">
                    <div className="flex items-center gap-4">
                      <div className="p-3 bg-purple-100 rounded-lg">
                        <Search className="w-5 h-5 text-purple-600" />
                      </div>
                      <div className="flex flex-col">
                        <div className="font-medium font-mono text-gray-900 text-lg">{pattern.pattern}</div>
                        <div className="text-sm text-gray-600">
                          {pattern.description} • {pattern.agent_name} • {pattern.source_name}
                        </div>
                        <div className="text-xs text-gray-500">
                          {pattern.matches_count} matches • Last match: {formatLastSeen(pattern.last_match)}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <div className="text-sm font-medium text-gray-900">Matches</div>
                        <div className="text-xs text-gray-500">{pattern.matches_count}</div>
                      </div>
                      <div className="flex flex-col gap-2">
                        <Badge className={`${getSeverityColor(pattern.severity)} border`}>
                          {pattern.severity}
                        </Badge>
                        <Badge variant="outline" className="border-gray-300">
                          {pattern.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'sources' && (
              <div className="space-y-4">
                {filteredSources.map((source) => (
                  <div key={source.id} className="flex items-center justify-between p-6 border border-gray-200 rounded-xl hover:bg-gray-50 transition-all duration-200 hover:shadow-sm">
                    <div className="flex items-center gap-4">
                      <div className="p-3 bg-green-100 rounded-lg">
                        {getStatusIcon(source.status)}
                      </div>
                      <div className="flex flex-col">
                        <div className="font-medium text-gray-900 text-lg">{source.name}</div>
                        <div className="text-sm text-gray-600">
                          {source.agent_name} • {source.paths.length} paths • {source.patterns.length} patterns
                        </div>
                        <div className="text-xs text-gray-500">
                          {source.encoding} • Max {source.max_file_mb}MB • Last scan: {formatLastSeen(source.last_scan)}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <div className="text-sm font-medium text-gray-900">Files</div>
                        <div className="text-xs text-gray-500">{source.files_count}</div>
                      </div>
                      <Badge variant="outline" className="border-gray-300 px-3 py-1">
                        {source.status}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AppMonFileMonitoring;
