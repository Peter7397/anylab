import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Clock, 
  CheckCircle, 
  AlertCircle, 
  XCircle, 
  Loader2,
  Filter,
  RefreshCw,
  Upload,
  Folder,
  Globe,
  Plus,
  Trash2,
  Settings,
  ExternalLink
} from 'lucide-react';
import { apiClient } from '../../services/api';

interface HelpPortalDocument {
  id: number;
  filename: string;
  file_path: string;
  file_size: number;
  file_size_mb: string;
  category: string;
  category_display: string;
  document_type: string;
  version: string;
  status: string;
  status_display: string;
  chunk_count: number;
  error_message: string;
  discovered_date: string;
  processed_date: string;
}

interface HelpPortalStatistics {
  total: number;
  pending: number;
  processing: number;
  completed: number;
  failed: number;
  skipped: number;
}

interface WebsiteSource {
  id: number;
  url: string;
  domain: string;
  title: string;
  description: string;
  processing_status: string;
  processing_status_display: string;
  metadata_extracted: boolean;
  chunks_created: boolean;
  embeddings_created: boolean;
  processing_error: string | null;
  chunk_count: number;
  embedding_count: number;
  page_count: number;
  last_refreshed_date: string;
  next_refresh_date: string;
  auto_refresh: boolean;
  refresh_interval_days: number;
  created_date: string;
  updated_date: string;
  is_ready: boolean;
  progress_percentage: number;
}

interface WebsiteStatistics {
  total_websites: number;
  ready_websites: number;
  processing_websites: number;
  failed_websites: number;
  total_chunks: number;
  total_embeddings: number;
  success_rate: number;
}

const HelpPortal: React.FC = () => {
  const [documents, setDocuments] = useState<HelpPortalDocument[]>([]);
  const [statistics, setStatistics] = useState<HelpPortalStatistics | null>(null);
  const [loading, setLoading] = useState(false);
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [importing, setImporting] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [duplicateInfo, setDuplicateInfo] = useState<any>(null);
  const [checkingDuplicates, setCheckingDuplicates] = useState(false);
  
  // Website-related state
  const [websites, setWebsites] = useState<WebsiteSource[]>([]);
  const [websiteStatistics, setWebsiteStatistics] = useState<WebsiteStatistics | null>(null);
  const [websiteLoading, setWebsiteLoading] = useState(false);
  const [showAddWebsiteModal, setShowAddWebsiteModal] = useState(false);
  const [newWebsite, setNewWebsite] = useState({
    url: '',
    title: '',
    description: '',
    auto_refresh: true,
    refresh_interval_days: 7
  });
  const [addingWebsite, setAddingWebsite] = useState(false);
  const [activeTab, setActiveTab] = useState<'documents' | 'websites'>('documents');

  useEffect(() => {
    fetchDocuments();
    if (activeTab === 'websites') {
      fetchWebsites();
    }
  }, [categoryFilter, statusFilter, activeTab]);

  // Real-time status polling for websites
  useEffect(() => {
    if (activeTab === 'websites') {
      const processingWebsites = websites.filter(w => 
        ['pending', 'fetching', 'metadata_extracting', 'chunking', 'embedding'].includes(w.processing_status)
      );
      
      if (processingWebsites.length > 0) {
        const interval = setInterval(() => {
          fetchWebsites();
        }, 3000); // Poll every 3 seconds
        
        return () => clearInterval(interval);
      }
    }
  }, [activeTab, websites]);

  const checkDuplicates = async () => {
    setCheckingDuplicates(true);
    try {
      const response = await apiClient.get<any>('/ai/help-portal/check-duplicates/');
      setDuplicateInfo(response.data);
      setShowImportModal(true);
    } catch (error) {
      console.error('Error checking duplicates:', error);
      alert('Failed to check for duplicates');
    } finally {
      setCheckingDuplicates(false);
    }
  };

  const runImport = async (force: boolean = false) => {
    setImporting(true);
    try {
      const response = await apiClient.post<any>('/ai/help-portal/import/', {
        force,
        folder_path: ''
      });
      
      if (response.data.success) {
        alert('Import completed successfully!');
        setShowImportModal(false);
        fetchDocuments(); // Refresh the list
      } else {
        alert('Import failed: ' + response.data.error);
      }
    } catch (error) {
      console.error('Error running import:', error);
      alert('Import failed');
    } finally {
      setImporting(false);
    }
  };

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const params: string[] = [];
      if (categoryFilter !== 'all') params.push(`category=${categoryFilter}`);
      if (statusFilter !== 'all') params.push(`status=${statusFilter}`);
      
      const queryString = params.length > 0 ? `?${params.join('&')}` : '';
      const endpoint = `/ai/help-portal/${queryString}`;

      interface HelpPortalResponse {
        documents: HelpPortalDocument[];
        statistics: HelpPortalStatistics;
      }

      const response = await apiClient.get<HelpPortalResponse>(endpoint);
      setDocuments(response.data.documents);
      setStatistics(response.data.statistics);
    } catch (error) {
      console.error('Error fetching help portal documents:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'processing':
        return <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-600" />;
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-600" />;
      case 'skipped':
        return <AlertCircle className="w-4 h-4 text-gray-600" />;
      default:
        return <AlertCircle className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'processing':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'failed':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'skipped':
        return 'bg-gray-100 text-gray-800 border-gray-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  // Website-related functions
  const fetchWebsites = async () => {
    setWebsiteLoading(true);
    try {
      const response = await apiClient.get<{websites: WebsiteSource[], count: number}>('/ai/websites/');
      setWebsites(response.data.websites);
      
      // Fetch statistics
      const statsResponse = await apiClient.get<WebsiteStatistics>('/ai/websites/statistics/');
      setWebsiteStatistics(statsResponse.data);
    } catch (error) {
      console.error('Error fetching websites:', error);
    } finally {
      setWebsiteLoading(false);
    }
  };

  const addWebsite = async () => {
    if (!newWebsite.url.trim()) {
      alert('Please enter a valid URL');
      return;
    }

    // Check for duplicate URL
    const existingWebsite = websites.find(w => w.url.toLowerCase() === newWebsite.url.toLowerCase());
    if (existingWebsite) {
      alert('This website URL has already been added. Please choose a different URL.');
      return;
    }

    setAddingWebsite(true);
    try {
      const response = await apiClient.post<{message: string, website: WebsiteSource}>('/ai/websites/add/', newWebsite);
      
      if (response.data.message) {
        alert('Website added successfully! Processing will begin automatically.');
        setShowAddWebsiteModal(false);
        setNewWebsite({
          url: '',
          title: '',
          description: '',
          auto_refresh: true,
          refresh_interval_days: 7
        });
        fetchWebsites(); // Refresh the list
      }
    } catch (error: any) {
      console.error('Error adding website:', error);
      const errorMessage = error.response?.data?.error || 'Failed to add website';
      alert(`Error: ${errorMessage}`);
    } finally {
      setAddingWebsite(false);
    }
  };

  const refreshWebsite = async (websiteId: number) => {
    try {
      const response = await apiClient.post<{message: string, website: WebsiteSource}>(`/ai/websites/${websiteId}/refresh/`);
      if (response.data.message) {
        alert('Website refresh initiated!');
        fetchWebsites(); // Refresh the list
      }
    } catch (error) {
      console.error('Error refreshing website:', error);
      alert('Failed to refresh website');
    }
  };

  const deleteWebsite = async (websiteId: number) => {
    if (!confirm('Are you sure you want to delete this website? This action cannot be undone.')) {
      return;
    }

    try {
      const response = await apiClient.delete<{message: string}>(`/ai/websites/${websiteId}/delete/`);
      if (response.data.message) {
        alert('Website deleted successfully!');
        fetchWebsites(); // Refresh the list
      }
    } catch (error) {
      console.error('Error deleting website:', error);
      alert('Failed to delete website');
    }
  };

  const retryWebsiteProcessing = async (websiteId: number) => {
    try {
      const response = await apiClient.post<{message: string}>(`/ai/websites/${websiteId}/retry/`);
      if (response.data.message) {
        alert('Website processing retry initiated!');
        fetchWebsites(); // Refresh the list
      }
    } catch (error) {
      console.error('Error retrying website processing:', error);
      alert('Failed to retry website processing');
    }
  };

  const getWebsiteStatusIcon = (status: string) => {
    switch (status) {
      case 'ready':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'fetching':
      case 'metadata_extracting':
      case 'chunking':
      case 'embedding':
        return <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-600" />;
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-600" />;
      default:
        return <AlertCircle className="w-4 h-4 text-gray-400" />;
    }
  };

  const getWebsiteStatusColor = (status: string) => {
    switch (status) {
      case 'ready':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'fetching':
      case 'metadata_extracting':
      case 'chunking':
      case 'embedding':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'failed':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const categories = [
    { value: 'all', label: 'All Categories' },
    { value: 'cds', label: 'OpenLab CDS' },
    { value: 'ecm', label: 'OpenLab Server/ECM XT' },
    { value: 'services', label: 'Test Services' },
    { value: 'shared', label: 'Shared Services' },
    { value: 'other', label: 'Other' },
  ];

  const statuses = [
    { value: 'all', label: 'All Statuses' },
    { value: 'completed', label: 'Completed' },
    { value: 'processing', label: 'Processing' },
    { value: 'pending', label: 'Pending' },
    { value: 'failed', label: 'Failed' },
    { value: 'skipped', label: 'Skipped' },
  ];

  return (
    <div className="p-6 bg-white rounded-lg shadow-sm">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Help Portal</h1>
        <p className="text-gray-600">
          Manage and monitor help portal documentation and external website sources
        </p>
      </div>

      {/* Tabs */}
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('documents')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'documents'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4" />
                Help Portal Documents
              </div>
            </button>
            <button
              onClick={() => setActiveTab('websites')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'websites'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center gap-2">
                <Globe className="w-4 h-4" />
                External Website Sources
              </div>
            </button>
          </nav>
        </div>
      </div>

      {/* Statistics Cards */}
      {activeTab === 'documents' && statistics && (
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-600">Total</span>
              <FileText className="w-5 h-5 text-gray-500" />
            </div>
            <p className="text-2xl font-bold text-gray-900 mt-1">{statistics.total}</p>
          </div>
          <div className="bg-green-50 rounded-lg p-4 border border-green-200">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-green-700">Completed</span>
              <CheckCircle className="w-5 h-5 text-green-600" />
            </div>
            <p className="text-2xl font-bold text-green-900 mt-1">{statistics.completed}</p>
          </div>
          <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-yellow-700">Pending</span>
              <Clock className="w-5 h-5 text-yellow-600" />
            </div>
            <p className="text-2xl font-bold text-yellow-900 mt-1">{statistics.pending}</p>
          </div>
          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-blue-700">Processing</span>
              <Loader2 className="w-5 h-5 text-blue-600" />
            </div>
            <p className="text-2xl font-bold text-blue-900 mt-1">{statistics.processing}</p>
          </div>
          <div className="bg-red-50 rounded-lg p-4 border border-red-200">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-red-700">Failed</span>
              <XCircle className="w-5 h-5 text-red-600" />
            </div>
            <p className="text-2xl font-bold text-red-900 mt-1">{statistics.failed}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">Skipped</span>
              <AlertCircle className="w-5 h-5 text-gray-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900 mt-1">{statistics.skipped}</p>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex flex-wrap gap-4 mb-6 p-4 bg-primary-50 rounded-lg border border-primary-200">
        <button
          onClick={checkDuplicates}
          disabled={checkingDuplicates}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
        >
          {checkingDuplicates ? <Loader2 className="w-4 h-4 animate-spin" /> : <Folder className="w-4 h-4" />}
          Check & Import Documents
        </button>
        <button
          onClick={fetchDocuments}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh Status
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
        <div className="flex items-center gap-2">
          <Filter className="w-5 h-5 text-gray-500" />
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            {categories.map(cat => (
              <option key={cat.value} value={cat.value}>{cat.label}</option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            {statuses.map(status => (
              <option key={status.value} value={status.value}>{status.label}</option>
            ))}
          </select>
        </div>
        <button
          onClick={fetchDocuments}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Documents Table */}
      {loading && !documents.length ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      ) : documents.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
          <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">No help portal documents found.</p>
          <p className="text-sm text-gray-500 mt-2">
            Run the import command to process help portal documents.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 border border-gray-200 rounded-lg">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Document
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Category
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Size
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Chunks
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Processed
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {documents.map((doc) => (
                <tr key={doc.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{doc.filename}</div>
                      {doc.version && (
                        <div className="text-xs text-gray-500">{doc.version}</div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm text-gray-900">{doc.category_display}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm text-gray-600">{doc.document_type || '-'}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(doc.status)}`}>
                      {getStatusIcon(doc.status)}
                      {doc.status_display}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {doc.file_size_mb}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {doc.chunk_count || 0}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-xs text-gray-600">
                      {doc.processed_date || doc.discovered_date}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {documents.map(doc => doc.status === 'failed' && doc.error_message && (
        <div key={`error-${doc.id}`} className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center gap-2 text-red-800 font-medium mb-1">
            <AlertCircle className="w-5 h-5" />
            {doc.filename}
          </div>
          <p className="text-sm text-red-700">{doc.error_message}</p>
        </div>
      ))}

      {/* Import Confirmation Modal */}
      {showImportModal && duplicateInfo && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4">
            <div className="p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4">Document Import Preview</h3>
              
              <div className="mb-6 space-y-3">
                <div className="flex items-center justify-between p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <span className="text-sm font-medium text-blue-900">Total Files:</span>
                  <span className="text-2xl font-bold text-blue-900">{duplicateInfo.total_files}</span>
                </div>
                <div className="flex items-center justify-between p-4 bg-green-50 border border-green-200 rounded-lg">
                  <span className="text-sm font-medium text-green-900">New Files to Process:</span>
                  <span className="text-2xl font-bold text-green-900">{duplicateInfo.new_files}</span>
                </div>
                {duplicateInfo.duplicates > 0 && (
                  <div className="flex items-center justify-between p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <span className="text-sm font-medium text-yellow-900">Duplicates (skipped):</span>
                    <span className="text-2xl font-bold text-yellow-900">{duplicateInfo.duplicates}</span>
                  </div>
                )}
              </div>

              {duplicateInfo.duplicates > 0 && (
                <div className="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <div className="flex items-start gap-2">
                    <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-yellow-900">Warning: Duplicates Detected</p>
                      <p className="text-sm text-yellow-700 mt-1">
                        {duplicateInfo.duplicates} files are already in the database and will be skipped.
                        Only {duplicateInfo.new_files} new files will be processed.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              <div className="flex gap-3 justify-end">
                <button
                  onClick={() => setShowImportModal(false)}
                  className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 font-medium"
                >
                  Cancel
                </button>
                <button
                  onClick={() => runImport(false)}
                  disabled={importing}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium flex items-center gap-2"
                >
                  {importing ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Importing...
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4" />
                      Start Import
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Websites Tab Content */}
      {activeTab === 'websites' && (
        <>
          {/* Website Statistics Cards */}
          {websiteStatistics && (
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-600">Total Websites</span>
                  <Globe className="w-5 h-5 text-gray-500" />
                </div>
                <p className="text-2xl font-bold text-gray-900 mt-1">{websiteStatistics.total_websites}</p>
              </div>
              <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-green-700">Ready</span>
                  <CheckCircle className="w-5 h-5 text-green-600" />
                </div>
                <p className="text-2xl font-bold text-green-900 mt-1">{websiteStatistics.ready_websites}</p>
              </div>
              <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-blue-700">Processing</span>
                  <Loader2 className="w-5 h-5 text-blue-600" />
                </div>
                <p className="text-2xl font-bold text-blue-900 mt-1">{websiteStatistics.processing_websites}</p>
              </div>
              <div className="bg-red-50 rounded-lg p-4 border border-red-200">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-red-700">Failed</span>
                  <XCircle className="w-5 h-5 text-red-600" />
                </div>
                <p className="text-2xl font-bold text-red-900 mt-1">{websiteStatistics.failed_websites}</p>
              </div>
              <div className="bg-lime-50 rounded-lg p-4 border border-lime-200">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-lime-700">Total Chunks</span>
                  <FileText className="w-5 h-5 text-lime-600" />
                </div>
                <p className="text-2xl font-bold text-lime-900 mt-1">{websiteStatistics.total_chunks}</p>
              </div>
              <div className="bg-teal-50 rounded-lg p-4 border border-teal-200">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-teal-700">Success Rate</span>
                  <CheckCircle className="w-5 h-5 text-teal-600" />
                </div>
                <p className="text-2xl font-bold text-teal-900 mt-1">{websiteStatistics.success_rate}%</p>
              </div>
            </div>
          )}

          {/* Website Action Buttons */}
          <div className="flex flex-wrap gap-4 mb-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <button
              onClick={() => setShowAddWebsiteModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium"
            >
              <Plus className="w-4 h-4" />
              Add Website
            </button>
            <button
              onClick={fetchWebsites}
              disabled={websiteLoading}
              className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              <RefreshCw className={`w-4 h-4 ${websiteLoading ? 'animate-spin' : ''}`} />
              Refresh Status
            </button>
          </div>

          {/* Websites Table */}
          {websiteLoading && !websites.length ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
            </div>
          ) : websites.length === 0 ? (
            <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
              <Globe className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No external websites added yet.</p>
              <p className="text-sm text-gray-500 mt-2">
                Add websites to automatically fetch and process their content for RAG search.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 border border-gray-200 rounded-lg">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Website
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Progress
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Chunks
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Last Updated
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {websites.map((website) => (
                    <tr key={website.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {website.title || website.domain}
                          </div>
                          <div className="text-xs text-gray-500 flex items-center gap-1">
                            <ExternalLink className="w-3 h-3" />
                            <a 
                              href={website.url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="hover:text-blue-600"
                            >
                              {website.url}
                            </a>
                          </div>
                          {website.description && (
                            <div className="text-xs text-gray-600 mt-1">{website.description}</div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium border ${getWebsiteStatusColor(website.processing_status)}`}>
                          {getWebsiteStatusIcon(website.processing_status)}
                          {website.processing_status_display}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                            <div 
                              className="bg-blue-600 h-2 rounded-full" 
                              style={{ width: `${website.progress_percentage}%` }}
                            ></div>
                          </div>
                          <span className="text-xs text-gray-600">{website.progress_percentage}%</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {website.chunk_count || 0}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-xs text-gray-600">
                          {website.last_refreshed_date || website.updated_date}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => refreshWebsite(website.id)}
                            className="text-blue-600 hover:text-blue-900"
                            title="Refresh"
                          >
                            <RefreshCw className="w-4 h-4" />
                          </button>
                          {website.processing_status === 'failed' && (
                            <button
                              onClick={() => retryWebsiteProcessing(website.id)}
                              className="text-yellow-600 hover:text-yellow-900"
                              title="Retry"
                            >
                              <AlertCircle className="w-4 h-4" />
                            </button>
                          )}
                          <button
                            onClick={() => deleteWebsite(website.id)}
                            className="text-red-600 hover:text-red-900"
                            title="Delete"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Website Error Messages */}
          {websites.map(website => website.processing_status === 'failed' && website.processing_error && (
            <div key={`error-${website.id}`} className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center gap-2 text-red-800 font-medium mb-1">
                <AlertCircle className="w-5 h-5" />
                {website.title || website.domain}
              </div>
              <p className="text-sm text-red-700">{website.processing_error}</p>
            </div>
          ))}
        </>
      )}

      {/* Add Website Modal */}
      {showAddWebsiteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4">Add External Website</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Website URL *
                  </label>
                  <input
                    type="url"
                    value={newWebsite.url}
                    onChange={(e) => setNewWebsite({...newWebsite, url: e.target.value})}
                    placeholder="https://example.com"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Title (optional)
                  </label>
                  <input
                    type="text"
                    value={newWebsite.title}
                    onChange={(e) => setNewWebsite({...newWebsite, title: e.target.value})}
                    placeholder="Website title"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description (optional)
                  </label>
                  <textarea
                    value={newWebsite.description}
                    onChange={(e) => setNewWebsite({...newWebsite, description: e.target.value})}
                    placeholder="Brief description of the website content"
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="auto_refresh"
                    checked={newWebsite.auto_refresh}
                    onChange={(e) => setNewWebsite({...newWebsite, auto_refresh: e.target.checked})}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="auto_refresh" className="ml-2 block text-sm text-gray-700">
                    Auto-refresh content
                  </label>
                </div>
                
                {newWebsite.auto_refresh && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Refresh Interval (days)
                    </label>
                    <select
                      value={newWebsite.refresh_interval_days}
                      onChange={(e) => setNewWebsite({...newWebsite, refresh_interval_days: parseInt(e.target.value)})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value={1}>Daily</option>
                      <option value={7}>Weekly</option>
                      <option value={30}>Monthly</option>
                    </select>
                  </div>
                )}
              </div>

              <div className="flex gap-3 justify-end mt-6">
                <button
                  onClick={() => setShowAddWebsiteModal(false)}
                  className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 font-medium"
                >
                  Cancel
                </button>
                <button
                  onClick={addWebsite}
                  disabled={addingWebsite}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium flex items-center gap-2"
                >
                  {addingWebsite ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Adding...
                    </>
                  ) : (
                    <>
                      <Plus className="w-4 h-4" />
                      Add Website
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HelpPortal;

