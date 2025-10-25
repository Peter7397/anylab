import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert';
import {
  Database,
  Search,
  RefreshCw,
  Eye,
  AlertTriangle,
  Activity,
  Plus,
  Settings,
  TestTube
} from 'lucide-react';
import * as ApiService from '../../services/api';

interface DatabaseInstance {
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

const DatabaseList: React.FC = () => {
  const [databases, setDatabases] = useState<DatabaseInstance[]>([]);
  const [filteredDatabases, setFilteredDatabases] = useState<DatabaseInstance[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const navigate = useNavigate();

  useEffect(() => {
    fetchDatabases();
  }, []);

  useEffect(() => {
    filterDatabases();
  }, [databases, searchTerm, statusFilter]);

  const fetchDatabases = async () => {
    try {
      setLoading(true);
      const response = await ApiService.apiClient.get('/monitoring/api/db-instances/');
      if (Array.isArray(response.data)) {
        setDatabases(response.data as DatabaseInstance[]);
      } else {
        setDatabases([]);
      }
    } catch (err) {
      setError('Failed to load databases');
      console.error('Error fetching databases:', err);
    } finally {
      setLoading(false);
    }
  };

  const filterDatabases = () => {
    let filtered = Array.isArray(databases) ? databases : [];

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(db =>
        db.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        db.host.toLowerCase().includes(searchTerm.toLowerCase()) ||
        db.database_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        db.db_type.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(db => db.status === statusFilter);
    }

    setFilteredDatabases(filtered);
  };

  const handleDatabaseClick = (databaseId: number) => {
    navigate(`/monitoring/databases/${databaseId}`);
  };

  const handleTestConnection = async (databaseId: number) => {
    try {
      await ApiService.apiClient.post(`/monitoring/api/db-instances/${databaseId}/test_connection/`);
      // You could show a success message here
    } catch (err) {
      console.error('Error testing connection:', err);
      // You could show an error message here
    }
  };

  const handleToggleMonitoring = async (databaseId: number) => {
    try {
      await ApiService.apiClient.post(`/monitoring/api/db-instances/${databaseId}/toggle_monitoring/`);
      fetchDatabases(); // Refresh the list
    } catch (err) {
      console.error('Error toggling monitoring:', err);
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

  const getDatabaseTypeIcon = (dbType: string) => {
    switch (dbType.toLowerCase()) {
      case 'postgresql':
        return '🐘';
      case 'mysql':
        return '🐬';
      case 'sqlite':
        return '📱';
      case 'oracle':
        return '🔶';
      case 'sqlserver':
        return '🪟';
      default:
        return '🗄️';
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-lg">Loading databases...</div>
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
        <h1 className="text-3xl font-bold">Database Instances</h1>
        <div className="flex space-x-2">
          <Button onClick={fetchDatabases} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Add Database
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <Input
                  placeholder="Search databases..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="sm:w-48">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Status</option>
                <option value="online">Online</option>
                <option value="offline">Offline</option>
                <option value="unknown">Unknown</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Database List */}
      <Card>
        <CardHeader>
          <CardTitle>
            Databases ({filteredDatabases.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {Array.isArray(filteredDatabases) && filteredDatabases.length > 0 ? (
            <div className="space-y-4">
              {filteredDatabases.map((db) => (
                <div key={db.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50">
                  <div className="flex items-center space-x-4">
                    <div className="flex-shrink-0">
                      <span className="text-2xl">{getDatabaseTypeIcon(db.db_type)}</span>
                    </div>
                    <div>
                      <h3 className="text-lg font-medium">{db.name}</h3>
                      <p className="text-sm text-gray-500">
                        {db.host}:{db.port} - {db.database_name} ({db.db_type})
                      </p>
                      <p className="text-xs text-gray-400">
                        Created: {new Date(db.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="text-right">
                      {db.last_metrics && (
                        <div className="text-sm text-gray-500">
                          <div>Conn: {db.last_metrics.active_connections}</div>
                          <div>QPS: {db.last_metrics.queries_per_second.toFixed(1)}</div>
                          <div>Cache: {db.last_metrics.cache_hit_ratio.toFixed(1)}%</div>
                        </div>
                      )}
                    </div>
                    <div className="flex flex-col items-end space-y-2">
                      <Badge className={getStatusColor(db.status)}>
                        {db.status}
                      </Badge>
                      {db.alert_count > 0 && (
                        <Badge variant="destructive">
                          {db.alert_count} alerts
                        </Badge>
                      )}
                      <div className="flex space-x-1">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={(e) => {
                            e?.stopPropagation();
                            handleTestConnection(db.id);
                          }}
                        >
                          <TestTube className="h-3 w-3" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={(e) => {
                            e?.stopPropagation();
                            handleToggleMonitoring(db.id);
                          }}
                        >
                          <Settings className="h-3 w-3" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={(e) => {
                            e?.stopPropagation();
                            handleDatabaseClick(db.id);
                          }}
                        >
                          <Eye className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <Database className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">
                {Array.isArray(databases) && databases.length === 0 
                  ? 'No databases configured' 
                  : 'No databases match your filters'}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Summary Stats */}
      {Array.isArray(databases) && databases.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">{databases.length}</div>
              <p className="text-xs text-muted-foreground">Total Databases</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">
                {databases.filter(db => db.status === 'online').length}
              </div>
              <p className="text-xs text-muted-foreground">Online</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">
                {databases.filter(db => db.monitoring_enabled).length}
              </div>
              <p className="text-xs text-muted-foreground">Monitoring Enabled</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">
                {databases.reduce((sum, db) => sum + db.alert_count, 0)}
              </div>
              <p className="text-xs text-muted-foreground">Total Alerts</p>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default DatabaseList;
