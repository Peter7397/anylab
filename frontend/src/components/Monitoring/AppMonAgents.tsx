import React, { useState, useEffect } from 'react';
import { apiClient } from '../../services/api';
import { 
  Monitor, 
  Activity, 
  FileText, 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  Clock,
  HardDrive,
  Zap,
  Eye,
  EyeOff
} from 'lucide-react';

interface AppMonAgent {
  id: number;
  name: string;
  system_name: string;
  system_hostname: string;
  agent_type: string;
  status: 'active' | 'inactive' | 'error' | 'maintenance';
  version: string;
  last_seen: string;
  created_at: string;
  updated_at: string;
  configuration: any;
  notes: string;
}

const AppMonAgents: React.FC = () => {
  const [agents, setAgents] = useState<AppMonAgent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showOffline, setShowOffline] = useState(true);

  useEffect(() => {
    fetchAgents();
  }, []);

  const fetchAgents = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get<AppMonAgent[]>('/monitoring/appmon/agents/');
      setAgents(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch AppMon agents');
      console.error('Error fetching AppMon agents:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'inactive':
        return <XCircle className="w-5 h-5 text-gray-500" />;
      case 'error':
        return <AlertTriangle className="w-5 h-5 text-red-500" />;
      case 'maintenance':
        return <Clock className="w-5 h-5 text-yellow-500" />;
      default:
        return <Monitor className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'inactive':
        return 'bg-gray-100 text-gray-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      case 'maintenance':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatLastSeen = (lastSeen: string) => {
    const date = new Date(lastSeen);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  const isAgentOnline = (lastSeen: string) => {
    const date = new Date(lastSeen);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    return diffMins < 5; // Consider online if seen in last 5 minutes
  };

  const filteredAgents = agents.filter(agent => 
    showOffline || isAgentOnline(agent.last_seen)
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <AlertTriangle className="w-5 h-5 text-red-500 mr-2" />
          <span className="text-red-700">{error}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AppMon Agents</h1>
          <p className="text-gray-600">Application monitoring agents and their status</p>
        </div>
        <div className="flex items-center space-x-4">
          <button
            onClick={() => setShowOffline(!showOffline)}
            className={`flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              showOffline 
                ? 'bg-blue-100 text-blue-700' 
                : 'bg-gray-100 text-gray-700'
            }`}
          >
            {showOffline ? <Eye className="w-4 h-4 mr-1" /> : <EyeOff className="w-4 h-4 mr-1" />}
            {showOffline ? 'Show All' : 'Online Only'}
          </button>
          <button
            onClick={fetchAgents}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Activity className="w-4 h-4 mr-2" />
            Refresh
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border">
          <div className="flex items-center">
            <Monitor className="w-8 h-8 text-blue-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Total Agents</p>
              <p className="text-2xl font-bold text-gray-900">{agents.length}</p>
            </div>
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg border">
          <div className="flex items-center">
            <CheckCircle className="w-8 h-8 text-green-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Online</p>
              <p className="text-2xl font-bold text-gray-900">
                {agents.filter(agent => isAgentOnline(agent.last_seen)).length}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg border">
          <div className="flex items-center">
            <AlertTriangle className="w-8 h-8 text-red-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Errors</p>
              <p className="text-2xl font-bold text-gray-900">
                {agents.filter(agent => agent.status === 'error').length}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg border">
          <div className="flex items-center">
            <FileText className="w-8 h-8 text-purple-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Active</p>
              <p className="text-2xl font-bold text-gray-900">
                {agents.filter(agent => agent.status === 'active').length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Agents List */}
      <div className="bg-white rounded-lg border">
        <div className="px-6 py-4 border-b">
          <h2 className="text-lg font-semibold text-gray-900">Agent Details</h2>
        </div>
        <div className="divide-y divide-gray-200">
          {filteredAgents.length === 0 ? (
            <div className="px-6 py-8 text-center">
              <Monitor className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">No AppMon agents found</p>
            </div>
          ) : (
            filteredAgents.map((agent) => (
              <div key={agent.id} className="px-6 py-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    {getStatusIcon(agent.status)}
                    <div>
                      <h3 className="text-lg font-medium text-gray-900">{agent.name}</h3>
                      <p className="text-sm text-gray-500">
                        System: {agent.system_name} ({agent.system_hostname})
                      </p>
                      <div className="flex items-center space-x-4 mt-1">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(agent.status)}`}>
                          {agent.status}
                        </span>
                        <span className="text-xs text-gray-500">
                          Version: {agent.version || 'Unknown'}
                        </span>
                        <span className="text-xs text-gray-500">
                          Last seen: {formatLastSeen(agent.last_seen)}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className={`w-2 h-2 rounded-full ${
                      isAgentOnline(agent.last_seen) ? 'bg-green-500' : 'bg-gray-400'
                    }`} />
                    <span className="text-xs text-gray-500">
                      {isAgentOnline(agent.last_seen) ? 'Online' : 'Offline'}
                    </span>
                  </div>
                </div>
                {agent.notes && (
                  <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-700">{agent.notes}</p>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default AppMonAgents;
