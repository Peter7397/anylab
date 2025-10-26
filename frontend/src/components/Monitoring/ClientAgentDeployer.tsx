import React, { useState, useEffect } from 'react';
import { Download, CheckCircle, AlertCircle, Loader, Monitor, Shield, Zap } from 'lucide-react';
import { apiClient } from '../../services/api';

interface DeploymentStatus {
  status: 'idle' | 'preparing' | 'ready' | 'downloading' | 'installing' | 'complete' | 'error';
  message: string;
  downloadUrl?: string;
  systemId?: number;
  instructions?: any;
}

const ClientAgentDeployer: React.FC = () => {
  const [deploymentStatus, setDeploymentStatus] = useState<DeploymentStatus>({
    status: 'idle',
    message: 'Ready to deploy AnyLab Client Agent'
  });
  const [clientInfo, setClientInfo] = useState({
    hostname: '',
    ip: '',
    os: ''
  });

  useEffect(() => {
    // Detect client information
    detectClientInfo();
  }, []);

  const detectClientInfo = () => {
    // Get hostname from browser
    const hostname = window.location.hostname;
    
    // Get IP (this will be the server IP, client IP will be detected server-side)
    const ip = window.location.hostname;
    
    // Detect OS
    const os = navigator.platform.includes('Win') ? 'Windows' : 
               navigator.platform.includes('Mac') ? 'macOS' : 
               navigator.platform.includes('Linux') ? 'Linux' : 'Unknown';
    
    setClientInfo({ hostname, ip, os });
  };

  const handleDeploy = async () => {
    try {
      setDeploymentStatus({
        status: 'preparing',
        message: 'Preparing deployment package...'
      });

      // Call the deployment API
      const response = await apiClient.post('/monitoring/client/deploy/', {
        hostname: clientInfo.hostname || 'Unknown'
      });

      const responseData = response.data as any;

      if (responseData.status === 'success') {
        setDeploymentStatus({
          status: 'ready',
          message: 'Deployment package ready!',
          downloadUrl: responseData.download_url,
          systemId: responseData.system_id,
          instructions: responseData.installation_instructions
        });
      } else {
        throw new Error(responseData.message);
      }
    } catch (error) {
      setDeploymentStatus({
        status: 'error',
        message: `Deployment failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      });
    }
  };

  const handleDownload = async () => {
    if (!deploymentStatus.downloadUrl) return;

    try {
      setDeploymentStatus({
        ...deploymentStatus,
        status: 'downloading',
        message: 'Downloading deployment package...'
      });

      // Trigger download
      const link = document.createElement('a');
      link.href = deploymentStatus.downloadUrl;
      link.download = `onlab_client_agent_${clientInfo.hostname}.zip`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      setDeploymentStatus({
        ...deploymentStatus,
        status: 'complete',
        message: 'Download complete! Follow the installation instructions below.'
      });
    } catch (error) {
      setDeploymentStatus({
        status: 'error',
        message: `Download failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      });
    }
  };

  const getStatusIcon = () => {
    switch (deploymentStatus.status) {
      case 'preparing':
        return <Loader className="animate-spin" />;
      case 'ready':
        return <CheckCircle className="text-green-600" />;
      case 'downloading':
        return <Download className="animate-pulse" />;
      case 'complete':
        return <CheckCircle className="text-green-600" />;
      case 'error':
        return <AlertCircle className="text-red-600" />;
      default:
        return <Monitor />;
    }
  };

  const getStatusColor = () => {
    switch (deploymentStatus.status) {
      case 'ready':
      case 'complete':
        return 'text-green-600';
      case 'error':
        return 'text-red-600';
      case 'preparing':
      case 'downloading':
        return 'text-blue-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">AnyLab Client Agent Deployer</h1>
        <div className="text-sm text-gray-500">
          One-click deployment for Windows monitoring
        </div>
      </div>

      {/* Client Information */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Client Information</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Hostname</label>
            <div className="mt-1 text-sm text-gray-900">{clientInfo.hostname}</div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">IP Address</label>
            <div className="mt-1 text-sm text-gray-900">{clientInfo.ip}</div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Operating System</label>
            <div className="mt-1 text-sm text-gray-900">{clientInfo.os}</div>
          </div>
        </div>
      </div>

      {/* Deployment Status */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center space-x-3 mb-4">
          {getStatusIcon()}
          <h2 className="text-lg font-semibold">Deployment Status</h2>
        </div>
        
        <div className={`text-sm ${getStatusColor()}`}>
          {deploymentStatus.message}
        </div>

        <div className="mt-6 space-y-4">
          {deploymentStatus.status === 'idle' && (
            <button
              onClick={handleDeploy}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium flex items-center space-x-2"
            >
              <Zap size={20} />
              <span>Deploy Client Agent</span>
            </button>
          )}

          {deploymentStatus.status === 'ready' && (
            <button
              onClick={handleDownload}
              className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-medium flex items-center space-x-2"
            >
              <Download size={20} />
              <span>Download Deployment Package</span>
            </button>
          )}

          {deploymentStatus.status === 'error' && (
            <button
              onClick={handleDeploy}
              className="bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-lg font-medium"
            >
              Try Again
            </button>
          )}
        </div>
      </div>

      {/* Installation Instructions */}
      {deploymentStatus.instructions && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Installation Instructions</h2>
          
          <div className="space-y-6">
            {/* Steps */}
            <div>
              <h3 className="font-medium text-gray-900 mb-2">Installation Steps:</h3>
              <ol className="list-decimal list-inside space-y-1 text-sm text-gray-700">
                {deploymentStatus.instructions.steps?.map((step: string, index: number) => (
                  <li key={index}>{step}</li>
                ))}
              </ol>
            </div>

            {/* Requirements */}
            <div>
              <h3 className="font-medium text-gray-900 mb-2">Requirements:</h3>
              <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
                {deploymentStatus.instructions.requirements?.map((req: string, index: number) => (
                  <li key={index}>{req}</li>
                ))}
              </ul>
            </div>

            {/* What it does */}
            <div>
              <h3 className="font-medium text-gray-900 mb-2">What the Agent Does:</h3>
              <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
                {deploymentStatus.instructions.what_it_does?.map((item: string, index: number) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Features */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center space-x-3 mb-3">
            <Monitor className="text-blue-600" size={24} />
            <h3 className="font-semibold text-gray-900">System Monitoring</h3>
          </div>
          <p className="text-sm text-gray-600">
            Monitors CPU, memory, disk usage, and network activity in real-time.
          </p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center space-x-3 mb-3">
            <Shield className="text-green-600" size={24} />
            <h3 className="font-semibold text-gray-900">Event Log Collection</h3>
          </div>
          <p className="text-sm text-gray-600">
            Collects Windows Event Logs for system, application, and security events.
          </p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center space-x-3 mb-3">
            <Zap className="text-purple-600" size={24} />
            <h3 className="font-semibold text-gray-900">Automatic Service</h3>
          </div>
          <p className="text-sm text-gray-600">
            Runs as a Windows service and starts automatically on system reboot.
          </p>
        </div>
      </div>

      {/* Security Notice */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <AlertCircle className="text-yellow-600 mt-0.5" size={20} />
          <div>
            <h3 className="font-medium text-yellow-800">Security Notice</h3>
            <p className="text-sm text-yellow-700 mt-1">
              The client agent requires administrator privileges to access Windows Event Logs and install as a service. 
              The agent only collects system monitoring data and sends it to your AnyLab server for analysis.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ClientAgentDeployer;
