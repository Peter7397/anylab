import React, { useState, useEffect } from 'react';
import { 
  Search, 
  RefreshCw, 
  Play, 
  Trash2,
  Cpu,
  Clock,
  User
} from 'lucide-react';

interface Process {
  id: number;
  name: string;
  user: string;
  cpu: number;
  memory: number;
  status: 'running' | 'sleeping' | 'stopped' | 'zombie';
  startTime: string;
  command: string;
}

const SystemProcesses: React.FC = () => {
  const [processes, setProcesses] = useState<Process[]>([]);
  const [filteredProcesses, setFilteredProcesses] = useState<Process[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [loading, setLoading] = useState(false);

  // Mock data for demonstration
  const mockProcesses: Process[] = [
    {
      id: 1,
      name: 'node',
      user: 'pinggenchen',
      cpu: 2.5,
      memory: 128,
      status: 'running',
      startTime: '2024-01-15 10:30:00',
      command: '/usr/bin/node --max-old-space-size=4096'
    },
    {
      id: 2,
      name: 'docker',
      user: 'root',
      cpu: 1.2,
      memory: 256,
      status: 'running',
      startTime: '2024-01-15 09:15:00',
      command: '/usr/bin/docker daemon'
    },
    {
      id: 3,
      name: 'nginx',
      user: 'www-data',
      cpu: 0.8,
      memory: 64,
      status: 'running',
      startTime: '2024-01-15 08:45:00',
      command: '/usr/sbin/nginx -g daemon off'
    },
    {
      id: 4,
      name: 'postgres',
      user: 'postgres',
      cpu: 1.5,
      memory: 512,
      status: 'running',
      startTime: '2024-01-15 08:30:00',
      command: '/usr/lib/postgresql/13/bin/postgres'
    },
    {
      id: 5,
      name: 'redis-server',
      user: 'redis',
      cpu: 0.3,
      memory: 32,
      status: 'running',
      startTime: '2024-01-15 08:25:00',
      command: '/usr/bin/redis-server'
    }
  ];

  useEffect(() => {
    loadProcesses();
  }, []);

  useEffect(() => {
    filterProcesses();
  }, [processes, searchTerm, statusFilter]);

  const loadProcesses = async () => {
    setLoading(true);
    try {
      // In a real implementation, this would fetch from the API
      // const response = await fetch('/api/monitoring/processes');
      // const data = await response.json();
      
      // Using mock data for now
      setTimeout(() => {
        setProcesses(mockProcesses);
        setLoading(false);
      }, 1000);
    } catch (error) {
      console.error('Failed to load processes:', error);
      setLoading(false);
    }
  };

  const filterProcesses = () => {
    let filtered = processes;

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(process =>
        process.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        process.user.toLowerCase().includes(searchTerm.toLowerCase()) ||
        process.command.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Filter by status
    if (statusFilter !== 'all') {
      filtered = filtered.filter(process => process.status === statusFilter);
    }

    setFilteredProcesses(filtered);
  };

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      running: { color: 'bg-green-500', text: 'Running' },
      sleeping: { color: 'bg-yellow-500', text: 'Sleeping' },
      stopped: { color: 'bg-red-500', text: 'Stopped' },
      zombie: { color: 'bg-gray-500', text: 'Zombie' }
    };

    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.running;

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color} text-white`}>
        {config.text}
      </span>
    );
  };

  const handleKillProcess = async (processId: number) => {
    try {
      // In a real implementation, this would call the API
      // await fetch(`/api/monitoring/processes/${processId}/kill`, { method: 'POST' });
      
      setProcesses(processes.filter(p => p.id !== processId));
    } catch (error) {
      console.error('Failed to kill process:', error);
    }
  };

  const handleRestartProcess = async (processId: number) => {
    try {
      // In a real implementation, this would call the API
      // await fetch(`/api/monitoring/processes/${processId}/restart`, { method: 'POST' });
      
      // For now, just reload the processes
      loadProcesses();
    } catch (error) {
      console.error('Failed to restart process:', error);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Cpu className="h-5 w-5" />
            System Processes
          </h2>
        </div>
        <div className="p-6">
          {/* Controls */}
          <div className="flex flex-col sm:flex-row gap-4 mb-6">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <input
                  type="text"
                  placeholder="Search processes..."
                  value={searchTerm}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            
            <div className="flex gap-2">
              <select
                value={statusFilter}
                onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setStatusFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Status</option>
                <option value="running">Running</option>
                <option value="sleeping">Sleeping</option>
                <option value="stopped">Stopped</option>
                <option value="zombie">Zombie</option>
              </select>
              
              <button
                onClick={loadProcesses}
                disabled={loading}
                className="px-3 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>

          {/* Process Table */}
          <div className="border rounded-lg overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">PID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">CPU %</th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Memory (MB)</th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Start Time</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Command</th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredProcesses.map((process) => (
                  <tr key={process.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">{process.id}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{process.name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{process.user}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-center">
                      <div className="flex items-center justify-center gap-1">
                        <Cpu className="h-3 w-3 text-blue-500" />
                        {process.cpu.toFixed(1)}%
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-center">
                      <div className="flex items-center justify-center gap-1">
                        <span className="text-green-500">●</span>
                        {process.memory}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-center">
                      {getStatusBadge(process.status)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div className="flex items-center gap-1">
                        <Clock className="h-3 w-3 text-gray-500" />
                        {process.startTime}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate" title={process.command}>
                      {process.command}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-center">
                      <div className="flex gap-1 justify-center">
                        <button
                          onClick={() => handleRestartProcess(process.id)}
                          className="p-1 text-gray-400 hover:text-gray-600"
                          title="Restart"
                        >
                          <Play className="h-3 w-3" />
                        </button>
                        <button
                          onClick={() => handleKillProcess(process.id)}
                          className="p-1 text-gray-400 hover:text-red-600"
                          title="Kill"
                        >
                          <Trash2 className="h-3 w-3" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {filteredProcesses.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No processes found matching your criteria.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SystemProcesses;
