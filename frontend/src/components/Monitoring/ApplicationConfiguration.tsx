import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert';
import { 
  Settings, 
  FileText, 
  Download, 
  Upload, 
  RefreshCw,
  Save,
  Edit,
  Eye,
  EyeOff,
  CheckCircle,
  XCircle,
  AlertTriangle
} from 'lucide-react';
import { apiClient } from '../../services/api';

interface Configuration {
  id: number;
  name: string;
  description: string;
  type: 'global' | 'local' | 'application';
  content: any;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  version: string;
}

const ApplicationConfiguration: React.FC = () => {
  const [configurations, setConfigurations] = useState<Configuration[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedConfig, setSelectedConfig] = useState<Configuration | null>(null);
  const [editing, setEditing] = useState(false);
  const [configContent, setConfigContent] = useState('');
  const [showSecrets, setShowSecrets] = useState(false);

  useEffect(() => {
    fetchConfigurations();
  }, []);

  const fetchConfigurations = async () => {
    try {
      setLoading(true);
      // This would be a new endpoint for configurations
      const response = await apiClient.get<Configuration[]>('/monitoring/appmon/configurations/');
      setConfigurations(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch configurations');
      console.error('Error fetching configurations:', err);
    } finally {
      setLoading(false);
    }
  };

  const getTypeBadge = (type: string) => {
    switch (type) {
      case 'global':
        return <Badge variant="default" className="bg-blue-100 text-blue-800">Global</Badge>;
      case 'local':
        return <Badge variant="secondary" className="bg-green-100 text-green-800">Local</Badge>;
      case 'application':
        return <Badge variant="outline" className="bg-purple-100 text-purple-800">Application</Badge>;
      default:
        return <Badge variant="outline">{type}</Badge>;
    }
  };

  const getStatusBadge = (isActive: boolean) => {
    return isActive ? 
      <Badge variant="default" className="bg-green-100 text-green-800">Active</Badge> :
      <Badge variant="secondary" className="bg-gray-100 text-gray-800">Inactive</Badge>;
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const editConfiguration = (config: Configuration) => {
    setSelectedConfig(config);
    setConfigContent(JSON.stringify(config.content, null, 2));
    setEditing(true);
  };

  const saveConfiguration = async () => {
    if (!selectedConfig) return;

    try {
      const updatedConfig = {
        ...selectedConfig,
        content: JSON.parse(configContent),
        updated_at: new Date().toISOString()
      };

      await apiClient.put(`/monitoring/appmon/configurations/${selectedConfig.id}/`, updatedConfig);
      fetchConfigurations();
      setEditing(false);
      setSelectedConfig(null);
    } catch (err) {
      console.error('Error saving configuration:', err);
    }
  };

  const downloadConfiguration = (config: Configuration) => {
    const data = {
      name: config.name,
      description: config.description,
      type: config.type,
      content: config.content,
      version: config.version,
      exported_at: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${config.name}-config.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const uploadConfiguration = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const content = await file.text();
      const config = JSON.parse(content);
      
      // This would upload the configuration
      await apiClient.post('/monitoring/appmon/configurations/', config);
      fetchConfigurations();
    } catch (err) {
      console.error('Error uploading configuration:', err);
    }
  };

  const toggleConfigurationStatus = async (config: Configuration) => {
    try {
      const updatedConfig = {
        ...config,
        is_active: !config.is_active
      };

      await apiClient.put(`/monitoring/appmon/configurations/${config.id}/`, updatedConfig);
      fetchConfigurations();
    } catch (err) {
      console.error('Error toggling configuration status:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Configuration Management</h1>
          <p className="text-gray-600">Manage AppMon agent configurations</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            onClick={() => setShowSecrets(!showSecrets)}
            variant="outline"
            size="sm"
          >
            {showSecrets ? <Eye className="w-4 h-4 mr-2" /> : <EyeOff className="w-4 h-4 mr-2" />}
            {showSecrets ? 'Hide Secrets' : 'Show Secrets'}
          </Button>
          <input
            type="file"
            accept=".json"
            onChange={uploadConfiguration}
            className="hidden"
            id="config-upload"
          />
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => document.getElementById('config-upload')?.click()}
          >
            <Upload className="w-4 h-4 mr-2" />
            Import
          </Button>
          <Button
            onClick={fetchConfigurations}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center">
              <Settings className="w-8 h-8 text-blue-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Total Configs</p>
                <p className="text-2xl font-bold text-gray-900">{configurations.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center">
              <CheckCircle className="w-8 h-8 text-green-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Active</p>
                <p className="text-2xl font-bold text-gray-900">
                  {configurations.filter(c => c.is_active).length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center">
              <FileText className="w-8 h-8 text-purple-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Global</p>
                <p className="text-2xl font-bold text-gray-900">
                  {configurations.filter(c => c.type === 'global').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center">
              <AlertTriangle className="w-8 h-8 text-orange-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Local</p>
                <p className="text-2xl font-bold text-gray-900">
                  {configurations.filter(c => c.type === 'local').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Configuration Editor */}
      {editing && selectedConfig && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Editing: {selectedConfig.name}</span>
              <div className="flex items-center space-x-2">
                <Button
                  onClick={() => setEditing(false)}
                  variant="outline"
                  size="sm"
                >
                  Cancel
                </Button>
                <Button
                  onClick={saveConfiguration}
                  size="sm"
                >
                  <Save className="w-4 h-4 mr-2" />
                  Save
                </Button>
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <textarea
              value={configContent}
              onChange={(e) => setConfigContent(e.target.value)}
              className="w-full h-96 p-4 border rounded-lg font-mono text-sm"
              placeholder="Enter JSON configuration..."
            />
          </CardContent>
        </Card>
      )}

      {/* Configurations List */}
      <Card>
        <CardHeader>
          <CardTitle>Configuration Files</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {configurations.length === 0 ? (
              <div className="text-center py-8">
                <Settings className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">No configurations found</p>
              </div>
            ) : (
              configurations.map((config) => (
                <div key={config.id} className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div>
                        <h4 className="font-medium">{config.name}</h4>
                        <p className="text-sm text-gray-500">{config.description}</p>
                        <div className="flex items-center space-x-2 mt-2">
                          {getTypeBadge(config.type)}
                          {getStatusBadge(config.is_active)}
                          <span className="text-xs text-gray-500">v{config.version}</span>
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          <p>Created: {formatTimestamp(config.created_at)}</p>
                          <p>Updated: {formatTimestamp(config.updated_at)}</p>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Button
                        onClick={() => editConfiguration(config)}
                        variant="outline"
                        size="sm"
                      >
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button
                        onClick={() => downloadConfiguration(config)}
                        variant="outline"
                        size="sm"
                      >
                        <Download className="w-4 h-4" />
                      </Button>
                      <Button
                        onClick={() => toggleConfigurationStatus(config)}
                        variant="outline"
                        size="sm"
                      >
                        {config.is_active ? <XCircle className="w-4 h-4" /> : <CheckCircle className="w-4 h-4" />}
                      </Button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ApplicationConfiguration;
