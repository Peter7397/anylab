import React, { useState } from 'react';
import { Download, Upload, Search, Filter, FileText, Clock, AlertTriangle, Info } from 'lucide-react';

interface LogEntry {
  id: string;
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'debug';
  source: string;
  message: string;
  system: string;
}

const LogCollection: React.FC = () => {
  const [selectedSystems, setSelectedSystems] = useState<string[]>([]);
  const [selectedLevels, setSelectedLevels] = useState<string[]>([]);
  const [timeRange, setTimeRange] = useState('24h');

  const logs: LogEntry[] = [
    {
      id: '1',
      timestamp: '2024-01-15 14:30:25',
      level: 'error',
      source: 'System',
      message: 'Failed to connect to database server',
      system: 'PC-001'
    },
    {
      id: '2',
      timestamp: '2024-01-15 14:29:18',
      level: 'warning',
      source: 'Application',
      message: 'High memory usage detected (85%)',
      system: 'PC-002'
    },
    {
      id: '3',
      timestamp: '2024-01-15 14:28:45',
      level: 'info',
      source: 'Network',
      message: 'Network connection established',
      system: 'PC-001'
    },
    {
      id: '4',
      timestamp: '2024-01-15 14:27:32',
      level: 'debug',
      source: 'Service',
      message: 'Service startup completed',
      system: 'SERVER-001'
    },
    {
      id: '5',
      timestamp: '2024-01-15 14:26:15',
      level: 'error',
      source: 'Hardware',
      message: 'Disk space critical (95% used)',
      system: 'PC-003'
    }
  ];

  const systems = ['PC-001', 'PC-002', 'PC-003', 'SERVER-001'];
  const levels = ['info', 'warning', 'error', 'debug'];

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'error': return 'text-red-600 bg-red-100';
      case 'warning': return 'text-yellow-600 bg-yellow-100';
      case 'info': return 'text-blue-600 bg-blue-100';
      case 'debug': return 'text-gray-600 bg-gray-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'error': return <AlertTriangle size={16} />;
      case 'warning': return <AlertTriangle size={16} />;
      case 'info': return <Info size={16} />;
      case 'debug': return <FileText size={16} />;
      default: return <Info size={16} />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Log Collection</h1>
          <p className="text-gray-600">Collect and analyze system logs for troubleshooting</p>
        </div>
        <div className="flex space-x-3">
          <button className="btn-primary">
            <Upload size={16} className="mr-2" />
            Collect Logs
          </button>
          <button className="btn-secondary">
            <Download size={16} className="mr-2" />
            Export
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
          <button className="text-blue-600 hover:text-blue-900 text-sm">
            Clear All
          </button>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Systems Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Systems
            </label>
            <select 
              multiple 
              className="input-field h-32"
              value={selectedSystems}
              onChange={(e) => {
                const values = Array.from(e.target.selectedOptions, option => option.value);
                setSelectedSystems(values);
              }}
            >
              {systems.map(system => (
                <option key={system} value={system}>{system}</option>
              ))}
            </select>
          </div>

          {/* Log Levels Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Log Levels
            </label>
            <div className="space-y-2">
              {levels.map(level => (
                <label key={level} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={selectedLevels.includes(level)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedLevels([...selectedLevels, level]);
                      } else {
                        setSelectedLevels(selectedLevels.filter(l => l !== level));
                      }
                    }}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700 capitalize">{level}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Time Range */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Time Range
            </label>
            <select 
              className="input-field"
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
            >
              <option value="1h">Last Hour</option>
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
              <option value="custom">Custom Range</option>
            </select>
          </div>

          {/* Search */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Search
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={16} />
              <input
                type="text"
                placeholder="Search logs..."
                className="input-field pl-10"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Logs Table */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Log Entries</h2>
          <div className="flex items-center space-x-2 text-sm text-gray-500">
            <Clock size={16} />
            <span>Last updated: 2 minutes ago</span>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Timestamp
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Level
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  System
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Source
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Message
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {log.timestamp}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getLevelColor(log.level)}`}>
                      {getLevelIcon(log.level)}
                      <span className="ml-1 capitalize">{log.level}</span>
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {log.system}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {log.source}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900 max-w-md truncate">
                    {log.message}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button className="text-blue-600 hover:text-blue-900 mr-3">View</button>
                    <button className="text-green-600 hover:text-green-900">Copy</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between mt-4">
          <div className="text-sm text-gray-500">
            Showing 1 to 5 of 5 results
          </div>
          <div className="flex space-x-2">
            <button className="px-3 py-1 text-sm text-gray-500 bg-gray-100 rounded hover:bg-gray-200">
              Previous
            </button>
            <button className="px-3 py-1 text-sm text-white bg-blue-600 rounded">
              1
            </button>
            <button className="px-3 py-1 text-sm text-gray-500 bg-gray-100 rounded hover:bg-gray-200">
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LogCollection; 