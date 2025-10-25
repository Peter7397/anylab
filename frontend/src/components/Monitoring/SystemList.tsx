import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert';
import { 
  Server, 
  Wifi, 
  WifiOff, 
  Clock,
  XCircle,
  Search,
  RefreshCw,
  Eye,
  AlertTriangle,
  Activity,
  Monitor,
  FileText,
  Cpu,
  MemoryStick,
  HardDrive
} from 'lucide-react';
import * as ApiService from '../../services/api';

interface System {
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
  os_type: string;
  os_version: string;
  agent_version: string;
  agent_type?: 'sysmon' | 'appmon' | 'windows' | 'manual';
  cpu_usage?: number;
  memory_usage?: number;
  disk_usage?: number;
}

const SystemList: React.FC = () => {
  const [systems, setSystems] = useState<System[]>([]);
  const [filteredSystems, setFilteredSystems] = useState<System[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [agentFilter, setAgentFilter] = useState<string>('all');
  const navigate = useNavigate();

  useEffect(() => {
    fetchSystems();
  }, []);

  useEffect(() => {
    // Only call filterSystems if systems is an array
    if (Array.isArray(systems)) {
      filterSystems();
    } else {
      setFilteredSystems([]);
    }
  }, [systems, searchTerm, statusFilter, agentFilter]);

  const fetchSystems = async () => {
    try {
      setLoading(true);
      console.log('ApiService.apiClient:', ApiService.apiClient); // Debug log
      if (!ApiService.apiClient) {
        throw new Error('ApiService.apiClient is undefined');
      }
      const response = await ApiService.apiClient.get<System[]>('/monitoring/api/systems/');
      // Ensure we set an array, even if the API returns something else
      const systemsData = Array.isArray(response.data) ? response.data : [];
      setSystems(systemsData);
    } catch (err) {
      setError('Failed to load systems');
      console.error('Error fetching systems:', err);
      // Set empty array on error
      setSystems([]);
    } finally {
      setLoading(false);
    }
  };

  const filterSystems = () => {
    // Ensure systems is an array
    if (!Array.isArray(systems)) {
      setFilteredSystems([]);
      return;
    }

    let filtered = systems;

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(system =>
        system.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        system.hostname.toLowerCase().includes(searchTerm.toLowerCase()) ||
        system.ip_address.includes(searchTerm)
      );
    }

    // Filter by status
    if (statusFilter !== 'all') {
      filtered = filtered.filter(system => system.status === statusFilter);
    }

    // Filter by agent type
    if (agentFilter !== 'all') {
      filtered = filtered.filter(system => system.agent_type === agentFilter);
    }

    setFilteredSystems(filtered);
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

  const getAgentStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge variant="default" className="bg-green-100 text-green-800">Active</Badge>;
      case 'inactive':
        return <Badge variant="secondary">Inactive</Badge>;
      case 'error':
        return <Badge variant="destructive">Error</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const handleSystemClick = (systemId: number) => {
    navigate(`/monitoring/systems/${systemId}`);
  };

  const acknowledgeAlerts = async (systemId: number) => {
    try {
      await ApiService.apiClient.post(`/monitoring/api/systems/${systemId}/acknowledge_alerts/`);
      fetchSystems(); // Refresh the list
    } catch (err) {
      console.error('Error acknowledging alerts:', err);
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
          <h1 className="text-3xl font-bold tracking-tight">Monitored Systems</h1>
          <p className="text-muted-foreground">
            View and manage all monitored Windows systems
          </p>
        </div>
        <Button onClick={fetchSystems}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search systems..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <Button
                variant={statusFilter === 'all' ? 'default' : 'outline'}
                onClick={() => setStatusFilter('all')}
              >
                All
              </Button>
              <Button
                variant={statusFilter === 'online' ? 'default' : 'outline'}
                onClick={() => setStatusFilter('online')}
              >
                Online
              </Button>
              <Button
                variant={statusFilter === 'offline' ? 'default' : 'outline'}
                onClick={() => setStatusFilter('offline')}
              >
                Offline
              </Button>
              <Button
                variant={statusFilter === 'error' ? 'default' : 'outline'}
                onClick={() => setStatusFilter('error')}
              >
                Error
              </Button>
            </div>
          </div>
          <div className="flex gap-2 mt-2">
            <Button
              variant={agentFilter === 'all' ? 'default' : 'outline'}
              onClick={() => setAgentFilter('all')}
              size="sm"
            >
              All Agents
            </Button>
            <Button
              variant={agentFilter === 'sysmon' ? 'default' : 'outline'}
              onClick={() => setAgentFilter('sysmon')}
              size="sm"
              className="flex items-center space-x-1"
            >
              <Monitor className="h-3 w-3" />
              <span>SysMon</span>
            </Button>
            <Button
              variant={agentFilter === 'appmon' ? 'default' : 'outline'}
              onClick={() => setAgentFilter('appmon')}
              size="sm"
              className="flex items-center space-x-1"
            >
              <FileText className="h-3 w-3" />
              <span>AppMon</span>
            </Button>
            <Button
              variant={agentFilter === 'windows' ? 'default' : 'outline'}
              onClick={() => setAgentFilter('windows')}
              size="sm"
            >
              Windows
            </Button>
            <Button
              variant={agentFilter === 'manual' ? 'default' : 'outline'}
              onClick={() => setAgentFilter('manual')}
              size="sm"
            >
              Manual
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Systems List */}
      <div className="grid gap-4">
        {Array.isArray(filteredSystems) && filteredSystems.map((system) => (
          <Card key={system.id} className="cursor-pointer hover:shadow-md transition-shadow">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  {getStatusIcon(system.status)}
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <h3 className="font-medium">{system.name}</h3>
                      {getStatusBadge(system.status)}
                      {getAgentStatusBadge(system.agent_status)}
                    </div>
                    <p className="text-sm text-muted-foreground">{system.hostname}</p>
                    <p className="text-xs text-muted-foreground">
                      {system.ip_address} • {system.os_type} {system.os_version}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Agent v{system.agent_version} • Last seen: {new Date(system.last_seen).toLocaleString()}
                    </p>
                    {system.agent_type && (
                      <Badge variant="outline" className="mt-1">
                        {system.agent_type === 'sysmon' ? 'SysMon Agent' : 
                         system.agent_type === 'appmon' ? 'AppMon Agent' : system.agent_type}
                      </Badge>
                    )}
                    {/* SysMon Metrics Display */}
                    {system.agent_type === 'sysmon' && (
                      <div className="flex items-center space-x-2 mt-2">
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
                
                <div className="flex items-center space-x-2">
                  {system.alert_count > 0 && (
                    <div className="flex items-center space-x-2">
                      <Badge variant="destructive">
                        <AlertTriangle className="h-3 w-3 mr-1" />
                        {system.alert_count} alerts
                      </Badge>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={(e) => {
                          e?.stopPropagation();
                          acknowledgeAlerts(system.id);
                        }}
                      >
                        Acknowledge
                      </Button>
                    </div>
                  )}
                  
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={(e) => {
                      e?.stopPropagation();
                      handleSystemClick(system.id);
                    }}
                  >
                    <Eye className="h-4 w-4 mr-1" />
                    View Details
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
        
        {(!Array.isArray(filteredSystems) || filteredSystems.length === 0) && (
          <Card>
            <CardContent className="pt-6">
              <div className="text-center py-8">
                <Server className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium">No systems found</h3>
                <p className="text-muted-foreground">
                  {searchTerm || statusFilter !== 'all' 
                    ? 'Try adjusting your search or filters'
                    : 'No systems are currently being monitored'
                  }
                </p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold">{Array.isArray(systems) ? systems.length : 0}</div>
              <div className="text-sm text-muted-foreground">Total Systems</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {Array.isArray(systems) ? systems.filter(s => s.status === 'online').length : 0}
              </div>
              <div className="text-sm text-muted-foreground">Online</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">
                {Array.isArray(systems) ? systems.filter(s => s.status === 'offline').length : 0}
              </div>
              <div className="text-sm text-muted-foreground">Offline</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {Array.isArray(systems) ? systems.filter(s => s.alert_count > 0).length : 0}
              </div>
              <div className="text-sm text-muted-foreground">With Alerts</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SystemList;
