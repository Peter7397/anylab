import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert';
import { 
  Download,
  Server,
  Monitor,
  Settings,
  Copy,
  CheckCircle,
  AlertTriangle,
  Terminal,
  FileText,
  Key,
  Activity,
  RefreshCw,
  Play
} from 'lucide-react';

const SysMonDeployment: React.FC = () => {
  const [serverUrl, setServerUrl] = useState('http://localhost:8000');
  const [apiKey, setApiKey] = useState('');
  const [hostnameAlias, setHostnameAlias] = useState('');
  const [copied, setCopied] = useState(false);

  const generateScript = () => {
    return `#!/bin/bash
# SysMon Agent Deployment Script
ONELAB_SERVER="${serverUrl}"
API_KEY="${apiKey}"
HOSTNAME_ALIAS="${hostnameAlias}"

echo "Deploying SysMon Agent..."
# Add your deployment logic here
`;
  };

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(generateScript());
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">SysMon Agent Deployment</h1>
          <p className="text-muted-foreground">
            Deploy SysMon agents for system monitoring
          </p>
        </div>
        <Button variant="outline">
          <Download className="h-4 w-4 mr-2" />
          Download Agent
        </Button>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Configuration</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="server_url">AnyLab Server URL</Label>
              <Input
                value={serverUrl}
                onChange={(e) => setServerUrl(e.target.value)}
                placeholder="http://your-server:8000"
              />
            </div>
            <div>
              <Label htmlFor="api_key">API Key</Label>
              <Input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Enter API key"
              />
            </div>
            <div>
              <Label htmlFor="hostname">Hostname Alias (Optional)</Label>
              <Input
                value={hostnameAlias}
                onChange={(e) => setHostnameAlias(e.target.value)}
                placeholder="Custom hostname"
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Deployment Script</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Button onClick={copyToClipboard} className="w-full">
                {copied ? <CheckCircle className="h-4 w-4 mr-2" /> : <Copy className="h-4 w-4 mr-2" />}
                {copied ? 'Copied!' : 'Copy Script'}
              </Button>
              <div className="bg-gray-50 p-4 rounded-lg">
                <pre className="text-sm overflow-x-auto">
                  {generateScript()}
                </pre>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>System Requirements</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <h4 className="font-medium mb-2">Software</h4>
              <ul className="space-y-1 text-sm">
                <li>• Python 3.7+</li>
                <li>• pip package manager</li>
                <li>• systemd (Linux)</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-2">Hardware</h4>
              <ul className="space-y-1 text-sm">
                <li>• 512MB RAM minimum</li>
                <li>• 100MB disk space</li>
                <li>• Network connectivity</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SysMonDeployment;
