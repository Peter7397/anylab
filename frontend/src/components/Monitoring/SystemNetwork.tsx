import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';

interface NetworkData {
  timestamp: string;
  bandwidth: number;
  latency: number;
  packets: number;
  errors: number;
}

interface NetworkInterface {
  id: string;
  name: string;
  status: 'up' | 'down' | 'error';
  ipAddress: string;
  macAddress: string;
  bandwidth: number;
  latency: number;
  packetsSent: number;
  packetsReceived: number;
  errors: number;
}

const SystemNetwork: React.FC = () => {
  const [networkData, setNetworkData] = useState<NetworkData[]>([]);
  const [interfaces, setInterfaces] = useState<NetworkInterface[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Mock network data
    const mockData: NetworkData[] = Array.from({ length: 24 }, (_, i) => ({
      timestamp: `${i}:00`,
      bandwidth: Math.random() * 1000,
      latency: Math.random() * 100,
      packets: Math.random() * 10000,
      errors: Math.random() * 10
    }));

    const mockInterfaces: NetworkInterface[] = [
      {
        id: '1',
        name: 'eth0',
        status: 'up',
        ipAddress: '192.168.1.100',
        macAddress: '00:1B:44:11:3A:B7',
        bandwidth: 850,
        latency: 15,
        packetsSent: 1250000,
        packetsReceived: 980000,
        errors: 2
      },
      {
        id: '2',
        name: 'wlan0',
        status: 'up',
        ipAddress: '192.168.1.101',
        macAddress: '00:1B:44:11:3A:B8',
        bandwidth: 450,
        latency: 25,
        packetsSent: 890000,
        packetsReceived: 750000,
        errors: 5
      },
      {
        id: '3',
        name: 'lo',
        status: 'up',
        ipAddress: '127.0.0.1',
        macAddress: '00:00:00:00:00:00',
        bandwidth: 1000,
        latency: 1,
        packetsSent: 500000,
        packetsReceived: 500000,
        errors: 0
      }
    ];

    setNetworkData(mockData);
    setInterfaces(mockInterfaces);
    setLoading(false);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'up': return 'text-green-600 bg-green-100';
      case 'down': return 'text-red-600 bg-red-100';
      case 'error': return 'text-yellow-600 bg-yellow-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

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
        <h1 className="text-2xl font-bold text-gray-900">System Network</h1>
        <div className="text-sm text-gray-500">
          Last updated: {new Date().toLocaleString()}
        </div>
      </div>

      {/* Network Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm font-medium text-gray-500">Total Interfaces</div>
          <div className="text-2xl font-bold text-gray-900">{interfaces.length}</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm font-medium text-gray-500">Active Interfaces</div>
          <div className="text-2xl font-bold text-green-600">
            {interfaces.filter(i => i.status === 'up').length}
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm font-medium text-gray-500">Total Bandwidth</div>
          <div className="text-2xl font-bold text-blue-600">
            {interfaces.reduce((sum, i) => sum + i.bandwidth, 0)} Mbps
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm font-medium text-gray-500">Total Errors</div>
          <div className="text-2xl font-bold text-red-600">
            {interfaces.reduce((sum, i) => sum + i.errors, 0)}
          </div>
        </div>
      </div>

      {/* Network Interfaces */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Network Interfaces</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Interface
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  IP Address
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  MAC Address
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Bandwidth
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Latency
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Packets
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Errors
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {interfaces.map((interface_) => (
                <tr key={interface_.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {interface_.name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(interface_.status)}`}>
                      {interface_.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {interface_.ipAddress}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {interface_.macAddress}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {interface_.bandwidth} Mbps
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {interface_.latency} ms
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {interface_.packetsSent.toLocaleString()} / {interface_.packetsReceived.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {interface_.errors}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bandwidth Over Time */}
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Bandwidth Usage Over Time</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={networkData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="bandwidth" stroke="#3B82F6" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Latency Over Time */}
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Network Latency Over Time</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={networkData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="latency" stroke="#10B981" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Packet Statistics */}
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Packet Statistics</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={networkData.slice(-6)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="packets" fill="#3B82F6" />
              <Bar dataKey="errors" fill="#EF4444" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Interface Bandwidth Comparison */}
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Interface Bandwidth Comparison</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={interfaces}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="bandwidth" fill="#3B82F6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default SystemNetwork;

