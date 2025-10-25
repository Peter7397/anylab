import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';

interface MetricData {
  timestamp: string;
  cpu: number;
  memory: number;
  disk: number;
  network: number;
  temperature: number;
}

const SystemMetrics: React.FC = () => {
  const [metrics, setMetrics] = useState<MetricData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Mock metrics data
    const mockData: MetricData[] = Array.from({ length: 24 }, (_, i) => ({
      timestamp: `${i}:00`,
      cpu: Math.random() * 100,
      memory: Math.random() * 100,
      disk: Math.random() * 100,
      network: Math.random() * 100,
      temperature: 30 + Math.random() * 20
    }));

    setMetrics(mockData);
    setLoading(false);
  }, []);

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
        <h1 className="text-2xl font-bold text-gray-900">System Metrics</h1>
        <div className="text-sm text-gray-500">
          Last updated: {new Date().toLocaleString()}
        </div>
      </div>

      {/* Metrics Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm font-medium text-gray-500">Average CPU</div>
          <div className="text-2xl font-bold text-blue-600">
            {(metrics.reduce((sum, m) => sum + m.cpu, 0) / metrics.length).toFixed(1)}%
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm font-medium text-gray-500">Average Memory</div>
          <div className="text-2xl font-bold text-green-600">
            {(metrics.reduce((sum, m) => sum + m.memory, 0) / metrics.length).toFixed(1)}%
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm font-medium text-gray-500">Average Disk</div>
          <div className="text-2xl font-bold text-yellow-600">
            {(metrics.reduce((sum, m) => sum + m.disk, 0) / metrics.length).toFixed(1)}%
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm font-medium text-gray-500">Average Temperature</div>
          <div className="text-2xl font-bold text-red-600">
            {(metrics.reduce((sum, m) => sum + m.temperature, 0) / metrics.length).toFixed(1)}°C
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* System Performance Over Time */}
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">System Performance Over Time</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={metrics}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="cpu" stroke="#3B82F6" strokeWidth={2} />
              <Line type="monotone" dataKey="memory" stroke="#10B981" strokeWidth={2} />
              <Line type="monotone" dataKey="disk" stroke="#F59E0B" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Temperature Monitoring */}
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Temperature Monitoring</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={metrics}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="temperature" stroke="#EF4444" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Network Usage */}
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Network Usage</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={metrics.slice(-6)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="network" fill="#8B5CF6" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Resource Distribution */}
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Current Resource Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={[
                  { name: 'CPU', value: metrics[metrics.length - 1]?.cpu || 0, color: '#3B82F6' },
                  { name: 'Memory', value: metrics[metrics.length - 1]?.memory || 0, color: '#10B981' },
                  { name: 'Disk', value: metrics[metrics.length - 1]?.disk || 0, color: '#F59E0B' },
                  { name: 'Network', value: metrics[metrics.length - 1]?.network || 0, color: '#8B5CF6' }
                ]}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {[
                  { name: 'CPU', value: metrics[metrics.length - 1]?.cpu || 0, color: '#3B82F6' },
                  { name: 'Memory', value: metrics[metrics.length - 1]?.memory || 0, color: '#10B981' },
                  { name: 'Disk', value: metrics[metrics.length - 1]?.disk || 0, color: '#F59E0B' },
                  { name: 'Network', value: metrics[metrics.length - 1]?.network || 0, color: '#8B5CF6' }
                ].map((entry, index) => (
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

export default SystemMetrics;
