import React, { useState, useEffect } from 'react';
import { Database, Github, MessageSquare, Globe, RefreshCw, Play, Pause, Settings, AlertCircle, CheckCircle } from 'lucide-react';
import { apiClient } from '../../services/api';

type ScraperType = 'ssb' | 'github' | 'forum' | 'html';

interface ScraperStatus {
  id: string;
  type: ScraperType;
  status: 'idle' | 'running' | 'completed' | 'error';
  lastRun?: string;
  itemsScraped?: number;
  config?: any;
}

const ScraperManagement: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ScraperType>('ssb');
  const [scrapers, setScrapers] = useState<ScraperStatus[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const scraperConfig = {
    ssb: {
      name: 'Service Support Bulletin',
      icon: Database,
      description: 'Scrape SSB database and help portal',
      endpoints: ['database', 'help-portal'],
    },
      github: {
        name: 'GitHub Scanner',
        icon: Github,
      description: 'Scan GitHub repositories and files',
      endpoints: ['repositories', 'files'],
    },
    forum: {
      name: 'Forum Scraper',
      icon: MessageSquare,
      description: 'Scrape forum posts and discussions',
      endpoints: ['posts'],
    },
    html: {
      name: 'HTML Parser',
      icon: Globe,
      description: 'Parse HTML from URLs and text',
      endpoints: ['url', 'text'],
    },
  };

  useEffect(() => {
    loadScraperStatus();
  }, []);

  const loadScraperStatus = async () => {
    setLoading(true);
    setError(null);
    try {
      // This would load status from backend
      const defaultScrapers: ScraperStatus[] = Object.keys(scraperConfig).map(type => ({
        id: type,
        type: type as ScraperType,
        status: 'idle',
        lastRun: undefined,
        itemsScraped: 0,
      }));
      setScrapers(defaultScrapers);
    } catch (err: any) {
      setError(err?.message || 'Failed to load scraper status');
    } finally {
      setLoading(false);
    }
  };

  const handleRunScraper = async (type: ScraperType, endpoint: string) => {
    setLoading(true);
    setError(null);
    try {
      let result: any;
      const config = {
        max_pages: 100,
        delay_between_requests: 1.0,
        timeout: 30,
        retry_attempts: 3,
      };

      switch (type) {
        case 'ssb':
          if (endpoint === 'database') {
            result = await apiClient.scrapeSSB(config);
          } else {
            result = await apiClient.scrapeSSBHelpPortal(config);
          }
          break;
        case 'github':
          if (endpoint === 'repositories') {
            result = await apiClient.scanGitHubRepos(config);
          } else {
            result = await apiClient.scanGitHubFiles(config);
          }
          break;
        case 'forum':
          result = await apiClient.scrapeForumPosts(config);
          break;
        case 'html':
          result = await apiClient.parseHTMLURL('', config);
          break;
      }

      // Update scraper status
      setScrapers(prev => prev.map(s =>
        s.type === type
          ? { ...s, status: 'completed', lastRun: new Date().toISOString(), itemsScraped: result.data?.count || 0 }
          : s
      ));
    } catch (err: any) {
      setError(err?.message || `Failed to run ${type} scraper`);
      console.error('Scraper error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="text-green-600" size={20} />;
      case 'error':
        return <AlertCircle className="text-red-600" size={20} />;
      case 'running':
        return <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>;
      default:
        return <div className="w-5 h-5 rounded-full bg-gray-300"></div>;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-100';
      case 'error':
        return 'text-red-600 bg-red-100';
      case 'running':
        return 'text-blue-600 bg-blue-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Scraper Management</h1>
          <p className="text-gray-600">Manage and monitor content scrapers</p>
        </div>
        <button
          onClick={loadScraperStatus}
          className="btn-secondary"
          disabled={loading}
        >
          <RefreshCw size={16} className={`mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
          <AlertCircle className="text-red-600 mt-0.5 mr-3" size={20} />
          <div className="flex-1">
            <p className="text-sm font-medium text-red-800">Error</p>
            <p className="text-sm text-red-600">{error}</p>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          {Object.entries(scraperConfig).map(([key, config]) => {
            const Icon = config.icon;
            return (
              <button
                key={key}
                onClick={() => setActiveTab(key as ScraperType)}
                className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center ${
                  activeTab === key
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon size={16} className="mr-2" />
                {config.name}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Scraper Content */}
      {Object.entries(scraperConfig).map(([key, config]) => {
        if (activeTab !== key) return null;
        
        const scraper = scrapers.find(s => s.type === key as ScraperType);
        const Icon = config.icon;

        return (
          <div key={key} className="space-y-6">
            {/* Overview Card */}
            <div className="card">
              <div className="flex items-start justify-between">
                <div className="flex items-start">
                  <div className={`p-3 rounded-lg ${
                    key === 'ssb' ? 'bg-blue-100' :
                    key === 'github' ? 'bg-purple-100' :
                    key === 'forum' ? 'bg-green-100' :
                    'bg-yellow-100'
                  }`}>
                    <Icon className={
                      key === 'ssb' ? 'text-blue-600' :
                      key === 'github' ? 'text-purple-600' :
                      key === 'forum' ? 'text-green-600' :
                      'text-yellow-600'
                    } size={32} />
                  </div>
                  <div className="ml-4">
                    <h3 className="text-lg font-semibold text-gray-900">{config.name}</h3>
                    <p className="text-sm text-gray-600 mt-1">{config.description}</p>
                  </div>
                </div>
                {scraper && (
                  <div className="flex items-center space-x-4">
                    <div>
                      <p className="text-xs text-gray-500 mb-1">Status</p>
                      <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(scraper.status)}`}>
                        {getStatusIcon(scraper.status)}
                        <span className="ml-2 capitalize">{scraper.status}</span>
                      </span>
                    </div>
                    {scraper.lastRun && (
                      <div>
                        <p className="text-xs text-gray-500 mb-1">Last Run</p>
                        <p className="text-sm text-gray-900">
                          {new Date(scraper.lastRun).toLocaleDateString()}
                        </p>
                      </div>
                    )}
                    {scraper.itemsScraped !== undefined && (
                      <div>
                        <p className="text-xs text-gray-500 mb-1">Items</p>
                        <p className="text-sm text-gray-900">{scraper.itemsScraped}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {config.endpoints.map((endpoint) => (
                <div key={endpoint} className="card">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 capitalize">
                        {endpoint}
                      </h4>
                      <p className="text-xs text-gray-500 mt-1">
                        Run {config.name} to scrape {endpoint}
                      </p>
                    </div>
                    <button
                      onClick={() => handleRunScraper(key as ScraperType, endpoint)}
                      disabled={loading}
                      className="btn-primary"
                    >
                      <Play size={16} className="mr-2" />
                      Run Now
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {/* Configuration */}
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-sm font-medium text-gray-900 flex items-center">
                  <Settings size={16} className="mr-2" />
                  Configuration
                </h4>
              </div>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Max Pages</span>
                  <span className="text-gray-900">100</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Delay Between Requests</span>
                  <span className="text-gray-900">1.0 seconds</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Timeout</span>
                  <span className="text-gray-900">30 seconds</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Retry Attempts</span>
                  <span className="text-gray-900">3</span>
                </div>
              </div>
              <button className="btn-secondary w-full mt-4">
                <Settings size={16} className="mr-2" />
                Edit Configuration
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default ScraperManagement;

