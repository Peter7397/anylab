import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

interface ResourceData {
  name: string;
  used: number;
  available: number;
  total: number;
  percentage: number;
}

interface SystemResource {
  id: string;
  name: string;
  type: 'CPU' | 'Memory' | 'Disk' | 'Network';
  status: 'healthy' | 'warning' | 'critical';
  usage: number;
  capacity: number;
  unit: string;
}

const SystemResources: React.FC = () => {
  const [resources, setResources] = useState<SystemResource[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Mock data
    const mockResources: SystemResource[] = [
      {
        id: '1',
        name: 'CPU Core 1',
        type: 'CPU',
        status: 'healthy',
        usage: 45,
        capacity: 100,
        unit: '%'
      },
      {
        id: '2',
        name: 'CPU Core 2',
        type: 'CPU',
        status: 'warning',
        usage: 78,
        capacity: 100,
        unit: '%'
      },
      {
        id: '3',
        name: 'RAM',
        type: 'Memory',
        status: 'healthy',
        usage: 6.2,
        capacity: 16,
        unit: 'GB'
      },
      {
        id: '4',
        name: 'SSD',
        type: 'Disk',
        status: 'critical',
        usage: 890,
        capacity: 1000,
        unit: 'GB'
      },
      {
        id: '5',
        name: 'Network Interface',
        type: 'Network',
        status: 'healthy',
        usage: 125,
        capacity: 1000,
        unit: 'Mbps'
      }
    ];

    setResources(mockResources);
    setLoading(false);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600 bg-green-100';
      case 'warning': return 'text-yellow-600 bg-yellow-100';
      case 'critical': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return '●';
      case 'warning': return '●';
      case 'critical': return '●';
      default: return '●';
    }
  };

  const chartData = resources.map(resource => ({
    name: resource.name,
    used: resource.usage,
    available: resource.capacity - resource.usage,
    total: resource.capacity,
    percentage: (resource.usage / resource.capacity) * 100
  }));

  const pieData = [
    { name: 'Used', value: resources.reduce((sum, r) => sum + r.usage, 0), color: '#3B82F6' },
    { name: 'Available', value: resources.reduce((sum, r) => sum + (r.capacity - r.usage), 0), color: '#10B981' }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">System Resources</h1>
        <div className="text-sm text-gray-500">
          Last updated: {new Date().toLocaleString()}
        </div>
      </div>

      {/* Resource Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm font-medium text-gray-500">Total Resources</div>
          <div className="text-2xl font-bold text-gray-900">{resources.length}</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm font-medium text-gray-500">Healthy</div>
          <div className="text-2xl font-bold text-green-600">
            {resources.filter(r => r.status === 'healthy').length}
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm font-medium text-gray-500">Warning</div>
          <div className="text-2xl font-bold text-yellow-600">
            {resources.filter(r => r.status === 'warning').length}
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm font-medium text-gray-500">Critical</div>
          <div className="text-2xl font-bold text-red-600">
            {resources.filter(r => r.status === 'critical').length}
          </div>
        </div>
      </div>

      {/* Resource List */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Resource Details</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Resource
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Usage
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Capacity
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Progress
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {resources.map((resource) => (
                <tr key={resource.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {resource.name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {resource.type}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {resource.usage} {resource.unit}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {resource.capacity} {resource.unit}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(resource.status)}`}>
                      <span className={`mr-1 ${getStatusColor(resource.status).includes('green') ? 'text-green-600' : getStatusColor(resource.status).includes('yellow') ? 'text-yellow-600' : 'text-red-600'}`}>
                        {getStatusIcon(resource.status)}
                      </span>
                      {resource.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          resource.status === 'healthy' ? 'bg-green-600' :
                          resource.status === 'warning' ? 'bg-yellow-600' : 'bg-red-600'
                        }`}
                        style={{ width: `${(resource.usage / resource.capacity) * 100}%` }}
                      ></div>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {((resource.usage / resource.capacity) * 100).toFixed(1)}%
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Resource Usage Chart */}
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Resource Usage Overview</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="used" fill="#3B82F6" />
              <Bar dataKey="available" fill="#10B981" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Usage Distribution */}
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Overall Usage Distribution</h3>
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
        </div>
      </div>
    </div>
  );
};

export default SystemResources;
