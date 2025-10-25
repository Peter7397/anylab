import React, { useState } from 'react';
import { Database, Activity, AlertTriangle, CheckCircle, Clock, RefreshCw, Play, Pause } from 'lucide-react';

interface SQLQuery {
  id: string;
  query: string;
  executionTime: number;
  status: 'running' | 'completed' | 'failed' | 'queued';
  timestamp: string;
  user: string;
  database: string;
}

interface DatabaseMetrics {
  name: string;
  size: string;
  connections: number;
  activeQueries: number;
  avgResponseTime: number;
  status: 'healthy' | 'warning' | 'critical';
}

const SQLHealth: React.FC = () => {
  const [isMonitoring, setIsMonitoring] = useState(true);

  const databases: DatabaseMetrics[] = [
    {
      name: 'onlab_main',
      size: '2.4 GB',
      connections: 45,
      activeQueries: 12,
      avgResponseTime: 120,
      status: 'healthy'
    },
    {
      name: 'onlab_logs',
      size: '8.7 GB',
      connections: 23,
      activeQueries: 8,
      avgResponseTime: 85,
      status: 'warning'
    },
    {
      name: 'onlab_analytics',
      size: '15.2 GB',
      connections: 67,
      activeQueries: 25,
      avgResponseTime: 320,
      status: 'critical'
    }
  ];

  const recentQueries: SQLQuery[] = [
    {
      id: '1',
      query: 'SELECT * FROM users WHERE last_login > NOW() - INTERVAL 24 HOUR',
      executionTime: 45,
      status: 'completed',
      timestamp: '2024-01-15 14:30:25',
      user: 'admin',
      database: 'onlab_main'
    },
    {
      id: '2',
      query: 'UPDATE system_logs SET processed = true WHERE created_at < NOW() - INTERVAL 1 DAY',
      executionTime: 1200,
      status: 'running',
      timestamp: '2024-01-15 14:29:18',
      user: 'system',
      database: 'onlab_logs'
    },
    {
      id: '3',
      query: 'SELECT COUNT(*) FROM analytics_data WHERE date = CURRENT_DATE',
      executionTime: 0,
      status: 'failed',
      timestamp: '2024-01-15 14:28:45',
      user: 'analytics_user',
      database: 'onlab_analytics'
    },
    {
      id: '4',
      query: 'CREATE INDEX idx_user_email ON users(email)',
      executionTime: 0,
      status: 'queued',
      timestamp: '2024-01-15 14:27:32',
      user: 'dba',
      database: 'onlab_main'
    }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600 bg-green-100';
      case 'warning': return 'text-yellow-600 bg-yellow-100';
      case 'critical': return 'text-red-600 bg-red-100';
      case 'completed': return 'text-green-600 bg-green-100';
      case 'running': return 'text-blue-600 bg-blue-100';
      case 'failed': return 'text-red-600 bg-red-100';
      case 'queued': return 'text-gray-600 bg-gray-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'completed': return <CheckCircle size={16} />;
      case 'warning': return <AlertTriangle size={16} />;
      case 'critical':
      case 'failed': return <AlertTriangle size={16} />;
      case 'running': return <Activity size={16} />;
      case 'queued': return <Clock size={16} />;
      default: return <Activity size={16} />;
    }
  };

  const formatExecutionTime = (time: number) => {
    if (time === 0) return '-';
    return `${time}ms`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">SQL Health Monitor</h1>
          <p className="text-gray-600">Monitor database performance and query health</p>
        </div>
        <div className="flex space-x-3">
          <button 
            className={`btn ${isMonitoring ? 'btn-secondary' : 'btn-primary'}`}
            onClick={() => setIsMonitoring(!isMonitoring)}
          >
            {isMonitoring ? <Pause size={16} className="mr-2" /> : <Play size={16} className="mr-2" />}
            {isMonitoring ? 'Pause' : 'Start'} Monitoring
          </button>
          <button className="btn-secondary">
            <RefreshCw size={16} className="mr-2" />
            Refresh
          </button>
        </div>
      </div>

      {/* Database Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {databases.map((db) => (
          <div key={db.name} className="card">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <Database className="text-blue-600 mr-2" size={20} />
                <h3 className="text-lg font-semibold text-gray-900">{db.name}</h3>
              </div>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(db.status)}`}>
                {getStatusIcon(db.status)}
                <span className="ml-1 capitalize">{db.status}</span>
              </span>
            </div>
            
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Size:</span>
                <span className="text-sm font-medium text-gray-900">{db.size}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Connections:</span>
                <span className="text-sm font-medium text-gray-900">{db.connections}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Active Queries:</span>
                <span className="text-sm font-medium text-gray-900">{db.activeQueries}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Avg Response:</span>
                <span className="text-sm font-medium text-gray-900">{db.avgResponseTime}ms</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Performance Metrics */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Performance Metrics</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">156</div>
            <div className="text-sm text-gray-600">Total Queries</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">142</div>
            <div className="text-sm text-gray-600">Successful</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">8</div>
            <div className="text-sm text-gray-600">Failed</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-600">6</div>
            <div className="text-sm text-gray-600">Running</div>
          </div>
        </div>
      </div>

      {/* Recent Queries */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Recent Queries</h2>
          <div className="flex space-x-2">
            <select className="input-field">
              <option>All Databases</option>
              <option>onlab_main</option>
              <option>onlab_logs</option>
              <option>onlab_analytics</option>
            </select>
            <select className="input-field">
              <option>All Status</option>
              <option>Completed</option>
              <option>Running</option>
              <option>Failed</option>
              <option>Queued</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Query
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Database
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Execution Time
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Timestamp
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {recentQueries.map((query) => (
                <tr key={query.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="max-w-md">
                      <div className="text-sm text-gray-900 font-mono truncate" title={query.query}>
                        {query.query}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {query.database}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {query.user}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(query.status)}`}>
                      {getStatusIcon(query.status)}
                      <span className="ml-1 capitalize">{query.status}</span>
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatExecutionTime(query.executionTime)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {query.timestamp}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button className="text-blue-600 hover:text-blue-900 mr-3">View</button>
                    {query.status === 'running' && (
                      <button className="text-red-600 hover:text-red-900">Kill</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Slow Query Analysis */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Slow Query Analysis</h2>
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-center">
              <AlertTriangle className="text-yellow-600 mr-3" size={20} />
              <div>
                <h3 className="text-sm font-medium text-yellow-800">Slow Query Detected</h3>
                <p className="text-sm text-yellow-700">Query taking longer than 5 seconds detected in onlab_analytics</p>
              </div>
            </div>
            <button className="text-yellow-800 hover:text-yellow-900 text-sm font-medium">
              View Details
            </button>
          </div>
          
          <div className="flex items-center justify-between p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center">
              <AlertTriangle className="text-red-600 mr-3" size={20} />
              <div>
                <h3 className="text-sm font-medium text-red-800">Connection Pool Warning</h3>
                <p className="text-sm text-red-700">High connection usage detected in onlab_analytics (85% capacity)</p>
              </div>
            </div>
            <button className="text-red-800 hover:text-red-900 text-sm font-medium">
              Optimize
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SQLHealth; 