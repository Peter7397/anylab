import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Alert, AlertDescription } from '../ui/alert';
import { apiClient } from '../../services/api';

interface SysMonAgent {
  id: number;
  name: string;
  hostname: string;
  ip_address: string;
  status: 'online' | 'offline' | 'maintenance' | 'error';
  last_seen: string;
}

const SysMonAgents: React.FC = () => {
  const [agents, setAgents] = useState<SysMonAgent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAgents();
  }, []);

  const fetchAgents = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get<SysMonAgent[]>('/monitoring/sysmon/agents/');
      setAgents(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch sysmon agents');
      console.error('Error fetching agents:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'bg-green-500';
      case 'offline': return 'bg-red-500';
      case 'maintenance': return 'bg-yellow-500';
      case 'error': return 'bg-red-600';
      default: return 'bg-gray-500';
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64">
      <div className="text-lg">Loading sysmon agents...</div>
    </div>;
  }

  if (error) {
    return <Alert className="mb-4">
      <AlertDescription>{error}</AlertDescription>
    </Alert>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">SysMon Agents</h2>
        <Button onClick={fetchAgents} variant="outline">Refresh</Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Connected Agents ({agents.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {agents.map((agent) => (
              <div key={agent.id} className="p-3 border rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold">{agent.name}</h3>
                    <p className="text-sm text-gray-600">{agent.hostname}</p>
                    <p className="text-xs text-gray-500">{agent.ip_address}</p>
                  </div>
                  <div className="text-right">
                    <Badge className={`${getStatusColor(agent.status)} text-white`}>
                      {agent.status}
                    </Badge>
                    <p className="text-xs text-gray-500 mt-1">
                      Last seen: {new Date(agent.last_seen).toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>
            ))}
            {agents.length === 0 && (
              <div className="text-center text-gray-500 py-8">
                No sysmon agents connected
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SysMonAgents;
