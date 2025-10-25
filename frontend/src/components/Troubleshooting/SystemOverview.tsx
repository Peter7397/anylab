import React from 'react';
import { Activity, AlertTriangle, CheckCircle, Clock, Server, Database, HardDrive, Cpu } from 'lucide-react';

interface SystemStatus {
  id: string;
  name: string;
  status: 'online' | 'offline' | 'warning';
  lastSeen: string;
  cpu: number;
  memory: number;
  disk: number;
  network: number;
}

const SystemOverview: React.FC = () => {
  const systems: SystemStatus[] = [
    {
      id: 'PC-001',
      name: 'Lab PC 1',
      status: 'online',
      lastSeen: '2 minutes ago',
      cpu: 45,
      memory: 67,
      disk: 23,
      network: 12
    },
    {
      id: 'PC-002',
      name: 'Lab PC 2',
      status: 'warning',
      lastSeen: '5 minutes ago',
      cpu: 89,
      memory: 92,
      disk: 78,
      network: 34
    },
    {
      id: 'PC-003',
      name: 'Lab PC 3',
      status: 'offline',
      lastSeen: '15 minutes ago',
      cpu: 0,
      memory: 0,
      disk: 0,
      network: 0
    },
    {
      id: 'SERVER-001',
      name: 'Main Server',
      status: 'online',
      lastSeen: '1 minute ago',
      cpu: 23,
      memory: 45,
      disk: 67,
      network: 8
    }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'text-green-600 bg-green-100';
      case 'warning': return 'text-yellow-600 bg-yellow-100';
      case 'offline': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'online': return <CheckCircle size={16} />;
      case 'warning': return <AlertTriangle size={16} />;
      case 'offline': return <Clock size={16} />;
      default: return <Activity size={16} />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">System Overview</h1>
          <p className="text-gray-600">Monitor all connected systems and their status</p>
        </div>
        <div className="flex space-x-3">
          <button className="btn-primary">
            <Activity size={16} className="mr-2" />
            Refresh
          </button>
          <button className="btn-secondary">
            <AlertTriangle size={16} className="mr-2" />
            View Alerts
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <CheckCircle className="text-green-600" size={24} />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Online Systems</p>
              <p className="text-2xl font-bold text-gray-900">2</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <AlertTriangle className="text-yellow-600" size={24} />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Warning</p>
              <p className="text-2xl font-bold text-gray-900">1</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center">
            <div className="p-2 bg-red-100 rounded-lg">
              <Clock className="text-red-600" size={24} />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Offline</p>
              <p className="text-2xl font-bold text-gray-900">1</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Server className="text-blue-600" size={24} />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Systems</p>
              <p className="text-2xl font-bold text-gray-900">4</p>
            </div>
          </div>
        </div>
      </div>

      {/* Systems Table */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">System Status</h2>
          <div className="flex space-x-2">
            <input
              type="text"
              placeholder="Search systems..."
              className="input-field"
            />
            <select className="input-field">
              <option>All Status</option>
              <option>Online</option>
              <option>Warning</option>
              <option>Offline</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  System
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Last Seen
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  CPU
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Memory
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Disk
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Network
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {systems.map((system) => (
                <tr key={system.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{system.name}</div>
                      <div className="text-sm text-gray-500">{system.id}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(system.status)}`}>
                      {getStatusIcon(system.status)}
                      <span className="ml-1 capitalize">{system.status}</span>
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {system.lastSeen}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <Cpu size={16} className="text-gray-400 mr-2" />
                      <span className="text-sm text-gray-900">{system.cpu}%</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <Database size={16} className="text-gray-400 mr-2" />
                      <span className="text-sm text-gray-900">{system.memory}%</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <HardDrive size={16} className="text-gray-400 mr-2" />
                      <span className="text-sm text-gray-900">{system.disk}%</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <Activity size={16} className="text-gray-400 mr-2" />
                      <span className="text-sm text-gray-900">{system.network}%</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button className="text-blue-600 hover:text-blue-900 mr-3">Details</button>
                    <button className="text-green-600 hover:text-green-900">Connect</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default SystemOverview; 