import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer, 
  LineChart, 
  Line, 
  PieChart, 
  Pie, 
  Cell 
} from 'recharts';
import { 
  Activity, 
  Cpu, 
  HardDrive, 
  Wifi, 
  Thermometer,
  TrendingUp,
  TrendingDown,
  AlertTriangle
} from 'lucide-react';

interface PerformanceData {
  timestamp: string;
  cpu: number;
  memory: number;
  disk: number;
  network: number;
  temperature: number;
}

interface SystemResource {
  id: string;
  name: string;
  type: 'CPU' | 'Memory' | 'Disk' | 'Network' | 'Temperature';
  status: 'healthy' | 'warning' | 'critical';
  usage: number;
  capacity: number;
  unit: string;
  trend: 'up' | 'down' | 'stable';
}

interface SystemMetrics {
  totalSystems: number;
  healthySystems: number;
  warningSystems: number;
  criticalSystems: number;
  avgCpu: number;
  avgMemory: number;
  avgDisk: number;
  avgTemperature: number;
}

const SystemPerformanceResources: React.FC = () => {
  const [performanceData, setPerformanceData] = useState<PerformanceData[]>([]);
  const [resources, setResources] = useState<SystemResource[]>([]);
  const [metrics, setMetrics] = useState<SystemMetrics>({
    totalSystems: 0,
    healthySystems: 0,
    warningSystems: 0,
    criticalSystems: 0,
    avgCpu: 0,
    avgMemory: 0,
    avgDisk: 0,
    avgTemperature: 0
  });
  const [selectedTimeRange, setSelectedTimeRange] = useState('24h');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, [selectedTimeRange]);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Mock data for demonstration
      const mockPerformanceData: PerformanceData[] = Array.from({ length: 24 }, (_, i) => ({
        timestamp: `${i}:00`,
        cpu: Math.random() * 100,
        memory: Math.random() * 100,
        disk: Math.random() * 100,
        network: Math.random() * 100,
        temperature: 30 + Math.random() * 20
      }));

      const mockResources: SystemResource[] = [
        {
          id: '1',
          name: 'CPU Core 1',
          type: 'CPU',
          status: 'healthy',
          usage: 45,
          capacity: 100,
          unit: '%',
          trend: 'stable'
        },
        {
          id: '2',
          name: 'CPU Core 2',
          type: 'CPU',
          status: 'warning',
          usage: 78,
          capacity: 100,
          unit: '%',
          trend: 'up'
        },
        {
          id: '3',
          name: 'RAM',
          type: 'Memory',
          status: 'healthy',
          usage: 6.2,
          capacity: 16,
          unit: 'GB',
          trend: 'stable'
        },
        {
          id: '4',
          name: 'SSD',
          type: 'Disk',
          status: 'critical',
          usage: 890,
          capacity: 1000,
          unit: 'GB',
          trend: 'up'
        },
        {
          id: '5',
          name: 'Network Interface',
          type: 'Network',
          status: 'healthy',
          usage: 125,
          capacity: 1000,
          unit: 'Mbps',
          trend: 'down'
        },
        {
          id: '6',
          name: 'System Temperature',
          type: 'Temperature',
          status: 'warning',
          usage: 65,
          capacity: 85,
          unit: '°C',
          trend: 'up'
        }
      ];

      const mockMetrics: SystemMetrics = {
        totalSystems: 12,
        healthySystems: 8,
        warningSystems: 3,
        criticalSystems: 1,
        avgCpu: 45.2,
        avgMemory: 62.8,
        avgDisk: 78.5,
        avgTemperature: 42.3
      };

      setPerformanceData(mockPerformanceData);
      setResources(mockResources);
      setMetrics(mockMetrics);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600 bg-green-100';
      case 'warning': return 'text-yellow-600 bg-yellow-100';
      case 'critical': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return <TrendingUp className="h-4 w-4 text-red-500" />;
      case 'down': return <TrendingDown className="h-4 w-4 text-green-500" />;
      case 'stable': return <Activity className="h-4 w-4 text-blue-500" />;
      default: return <Activity className="h-4 w-4 text-gray-500" />;
    }
  };

  const getResourceIcon = (type: string) => {
    switch (type) {
      case 'CPU': return <Cpu className="h-4 w-4" />;
      case 'Memory': return <span className="text-green-500">●</span>;
      case 'Disk': return <HardDrive className="h-4 w-4" />;
      case 'Network': return <Wifi className="h-4 w-4" />;
      case 'Temperature': return <Thermometer className="h-4 w-4" />;
      default: return <Activity className="h-4 w-4" />;
    }
  };

  const pieData = [
    { name: 'Healthy', value: metrics.healthySystems, color: '#10B981' },
    { name: 'Warning', value: metrics.warningSystems, color: '#F59E0B' },
    { name: 'Critical', value: metrics.criticalSystems, color: '#EF4444' }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Performance & Resources</h1>
          <p className="text-muted-foreground">
            Monitor system performance metrics and resource utilization
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <Select value={selectedTimeRange} onValueChange={setSelectedTimeRange}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1h">1 Hour</SelectItem>
              <SelectItem value="24h">24 Hours</SelectItem>
              <SelectItem value="7d">7 Days</SelectItem>
              <SelectItem value="30d">30 Days</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={fetchData}>
            <Activity className="mr-2 h-4 w-4" />
            Refresh
          </Button>
        </div>
      </div>

      {/* System Health Overview */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Systems</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.totalSystems}</div>
            <p className="text-xs text-muted-foreground">
              {metrics.healthySystems} healthy, {metrics.criticalSystems} critical
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Average CPU</CardTitle>
            <Cpu className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.avgCpu.toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">
              Across all systems
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Average Memory</CardTitle>
            <span className="text-green-500">●</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.avgMemory.toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">
              Utilization rate
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Average Temperature</CardTitle>
            <Thermometer className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.avgTemperature.toFixed(1)}°C</div>
            <p className="text-xs text-muted-foreground">
              System temperature
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Performance Charts */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* System Performance Over Time */}
        <Card>
          <CardHeader>
            <CardTitle>Performance Over Time</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="cpu" stroke="#3B82F6" strokeWidth={2} name="CPU" />
                <Line type="monotone" dataKey="memory" stroke="#10B981" strokeWidth={2} name="Memory" />
                <Line type="monotone" dataKey="disk" stroke="#F59E0B" strokeWidth={2} name="Disk" />
                <Line type="monotone" dataKey="network" stroke="#8B5CF6" strokeWidth={2} name="Network" />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* System Health Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>System Health Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Resource Details */}
      <Card>
        <CardHeader>
          <CardTitle>Resource Utilization</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {resources.map((resource) => (
              <div key={resource.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-4">
                  {getResourceIcon(resource.type)}
                  <div>
                    <h3 className="font-medium">{resource.name}</h3>
                    <p className="text-sm text-muted-foreground">{resource.type}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="text-right">
                    <p className="text-sm font-medium">
                      {resource.usage} / {resource.capacity} {resource.unit}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {((resource.usage / resource.capacity) * 100).toFixed(1)}% utilized
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    {getTrendIcon(resource.trend)}
                    <Badge className={getStatusColor(resource.status)}>
                      {resource.status}
                    </Badge>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Temperature Monitoring */}
      <Card>
        <CardHeader>
          <CardTitle>Temperature Monitoring</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={performanceData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="temperature" stroke="#EF4444" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
};

export default SystemPerformanceResources;
