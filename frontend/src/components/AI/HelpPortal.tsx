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
  Folder
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

  useEffect(() => {
    fetchDocuments();
  }, [categoryFilter, statusFilter]);

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
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Help Portal Documents</h1>
        <p className="text-gray-600">
          Manage and monitor help portal documentation processing status
        </p>
      </div>

      {/* Statistics Cards */}
      {statistics && (
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
      <div className="flex flex-wrap gap-4 mb-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
        <button
          onClick={checkDuplicates}
          disabled={checkingDuplicates}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
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
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
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
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {statuses.map(status => (
              <option key={status.value} value={status.value}>{status.label}</option>
            ))}
          </select>
        </div>
        <button
          onClick={fetchDocuments}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
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
    </div>
  );
};

export default HelpPortal;

