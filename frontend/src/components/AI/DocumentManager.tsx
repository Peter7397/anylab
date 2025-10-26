import React, { useState, useEffect } from 'react';
import { 
  Upload, 
  FileText, 
  Search, 
  Download, 
  Trash2, 
  Eye, 
  Calendar,
  HardDrive,
  User,
  AlertCircle,
  CheckCircle,
  X,
  File,
  FileSpreadsheet,
  Presentation,
  FileCode
} from 'lucide-react';
import { apiClient } from '../../services/api';

// Debug: Ensure this component is using updated code
console.log('DocumentManager component loaded with updated imports');

interface DocumentFile {
  id: number;
  title: string;
  filename: string;
  document_type: string;
  description?: string;
  uploaded_by: string;
  uploaded_at: string;
  uploaded_date: string;
  page_count?: number;
  file_size_mb: string;
  file_url?: string;
}

interface DocumentSearchParams {
  query: string;
  search_type: 'title' | 'content' | 'both';
  document_type: string;
}

const DocumentManager: React.FC<{ onOpenInViewer?: (doc: DocumentFile) => void }> = ({ onOpenInViewer }) => {
  const [documents, setDocuments] = useState<DocumentFile[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [searchParams, setSearchParams] = useState<DocumentSearchParams>({
    query: '',
    search_type: 'both',
    document_type: 'all'
  });
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploadForm, setUploadForm] = useState({
    title: '',
    description: '',
    document_type: 'pdf'
  });
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<DocumentFile | null>(null);
  const [showViewer, setShowViewer] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Document type configurations
  const documentTypes = [
    { value: 'pdf', label: 'PDF Document', icon: FileText, extensions: ['.pdf'] },
    { value: 'doc', label: 'Word Document', icon: File, extensions: ['.doc', '.docx'] },
    { value: 'xls', label: 'Excel Spreadsheet', icon: FileSpreadsheet, extensions: ['.xls', '.xlsx'] },
    { value: 'ppt', label: 'PowerPoint Presentation', icon: Presentation, extensions: ['.ppt', '.pptx'] },
    { value: 'txt', label: 'Text Document', icon: FileCode, extensions: ['.txt', '.rtf'] },
  ];

  // Load documents on component mount
  useEffect(() => {
    loadDocuments();
  }, []);

  // Debug: Check authentication status
  useEffect(() => {
    const token = localStorage.getItem(process.env.REACT_APP_JWT_STORAGE_KEY || 'anylab_token');
    console.log('Auth token exists:', !!token);
    if (token) {
      console.log('Token preview:', token.substring(0, 50) + '...');
    } else {
      console.log('No auth token found - please log in first');
    }
  }, []);

  const loadDocuments = async () => {
    setLoading(true);
    try {
      const response = await apiClient.getDocuments();
      // Handle both old format (array) and new format (object with documents array)
      if (Array.isArray(response)) {
        setDocuments(response);
      } else if (response && response.documents) {
        setDocuments(response.documents);
      } else {
        setDocuments([]);
      }
      setError(null);
    } catch (err) {
      setError('Failed to load documents');
      console.error('Error loading documents:', err);
    } finally {
      setLoading(false);
    }
  };

  const getFileIcon = (documentType: string) => {
    const type = documentTypes.find(t => t.value === documentType);
    return type ? type.icon : FileText;
  };

  const getAcceptedExtensions = (documentType: string) => {
    const type = documentTypes.find(t => t.value === documentType);
    return type ? type.extensions.join(',') : '.pdf';
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    if (files.length === 0) return;

    const validFiles: File[] = [];
    const invalidFiles: string[] = [];

    files.forEach(file => {
      const extension = '.' + file.name.split('.').pop()?.toLowerCase();
      const selectedType = documentTypes.find(t => 
        t.extensions.includes(extension)
      );
      
      if (selectedType) {
        validFiles.push(file);
      } else {
        invalidFiles.push(file.name);
      }
    });

    if (invalidFiles.length > 0) {
      setError(`Invalid file type(s): ${invalidFiles.join(', ')}`);
    }

    if (validFiles.length > 0) {
      setSelectedFiles(validFiles);
      // Set document type based on first file
      const firstFile = validFiles[0];
      const extension = '.' + firstFile.name.split('.').pop()?.toLowerCase();
      const selectedType = documentTypes.find(t => 
        t.extensions.includes(extension)
      );
      
      if (selectedType) {
        setUploadForm(prev => ({ 
          ...prev, 
          document_type: selectedType.value
        }));
      }
    }
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      setError('Please select at least one file');
      return;
    }

    setUploading(true);
    setError(null);

    // Debug: Check auth token before upload
    const token = localStorage.getItem(process.env.REACT_APP_JWT_STORAGE_KEY || 'anylab_token');
    console.log('Upload attempt - Auth token exists:', !!token);
    if (!token) {
      setError('Not authenticated. Please log in first.');
      setUploading(false);
      return;
    }

    try {
      const uploadPromises = selectedFiles.map(async (file, index) => {
        const title = uploadForm.title.trim() 
          ? `${uploadForm.title}${selectedFiles.length > 1 ? ` (${index + 1})` : ''}`
          : file.name.replace(/\.[^/.]+$/, ''); // Remove file extension
        
        return apiClient.uploadDocument(
          file, 
          title, 
          uploadForm.description, 
          uploadForm.document_type
        );
      });

      await Promise.all(uploadPromises);

      setSuccess(`Successfully uploaded ${selectedFiles.length} document(s)!`);
      setUploadForm({ title: '', description: '', document_type: 'pdf' });
      setSelectedFiles([]);
      setShowUploadModal(false);
      loadDocuments(); // Reload the list
    } catch (err: any) {
      console.error('Upload error:', err);
      setError(err.message || 'Failed to upload document(s)');
    } finally {
      setUploading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchParams.query.trim()) {
      loadDocuments();
      return;
    }

    setLoading(true);
    try {
      const response = await apiClient.searchDocuments(
        searchParams.query, 
        searchParams.search_type, 
        searchParams.document_type
      );
      setDocuments(response.results || []);
      setError(null);
    } catch (err) {
      setError('Failed to search documents');
      console.error('Error searching documents:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (docId: number) => {
    if (!window.confirm('Are you sure you want to delete this document?')) {
      return;
    }

    try {
      await apiClient.deleteDocument(docId);
      setSuccess('Document deleted successfully!');
      loadDocuments();
    } catch (err: any) {
      setError(err.message || 'Failed to delete document');
    }
  };

  const handleDownload = async (doc: DocumentFile) => {
    try {
      const blob = await apiClient.downloadDocument(doc.id);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', doc.filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError('Failed to download document');
    }
  };

  const handleView = (doc: DocumentFile) => {
    // For all document types, use the embedded viewer
    if (onOpenInViewer && doc.file_url) {
      // Open in the embedded DocumentViewer component
      onOpenInViewer({
        id: String(doc.id),  // Convert number to string
        title: doc.title,
        url: doc.file_url,
        type: doc.document_type as any,
      });
    } else if (doc.document_type === 'pdf' && doc.file_url) {
      // Fallback: Open PDF in new tab if file_url is available
      window.open(doc.file_url, '_blank');
    } else {
      // For other document types without file_url, show error
      setError('Document URL not available');
    }
  };

  const formatFileSize = (size: string) => {
    return size;
  };

  return (
    <div className="p-6 bg-white rounded-lg shadow-sm">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Document Manager</h2>
          <p className="text-gray-600">Upload, view, and manage your documents (PDF, Word, Excel, PowerPoint, Text)</p>
        </div>
        <button
          onClick={() => setShowUploadModal(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
        >
          <Upload size={20} />
          Upload Document
        </button>
      </div>

      {/* Search Bar */}
      <div className="mb-6 p-4 bg-gray-50 rounded-lg">
        <div className="flex gap-4 items-end">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Search Documents
            </label>
            <input
              type="text"
              value={searchParams.query}
              onChange={(e) => setSearchParams(prev => ({ ...prev, query: e.target.value }))}
              placeholder="Search by title, filename, or description..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Document Type
            </label>
            <select
              value={searchParams.document_type}
              onChange={(e) => setSearchParams(prev => ({ ...prev, document_type: e.target.value }))}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All Types</option>
              {documentTypes.map(type => (
                <option key={type.value} value={type.value}>{type.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Search Type
            </label>
            <select
              value={searchParams.search_type}
              onChange={(e) => setSearchParams(prev => ({ ...prev, search_type: e.target.value as any }))}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="both">Title & Content</option>
              <option value="title">Title Only</option>
              <option value="content">Content Only</option>
            </select>
          </div>
          <button
            onClick={handleSearch}
            className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
          >
            <Search size={20} />
            Search
          </button>
        </div>
      </div>

      {/* Error/Success Messages */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
          <AlertCircle size={20} className="text-red-500" />
          <span className="text-red-700">{error}</span>
          <button
            onClick={() => setError(null)}
            className="ml-auto text-red-500 hover:text-red-700"
          >
            <X size={16} />
          </button>
        </div>
      )}

      {success && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center gap-2">
          <CheckCircle size={20} className="text-green-500" />
          <span className="text-green-700">{success}</span>
          <button
            onClick={() => setSuccess(null)}
            className="ml-auto text-green-500 hover:text-green-700"
          >
            <X size={16} />
          </button>
        </div>
      )}

      {/* Document List */}
      <div className="space-y-4">
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-gray-600">Loading documents...</p>
          </div>
        ) : documents.length === 0 ? (
          <div className="text-center py-8">
            <FileText size={48} className="mx-auto text-gray-400 mb-4" />
            <p className="text-gray-600">No documents found</p>
            <p className="text-gray-500 text-sm">Upload your first document to get started</p>
          </div>
        ) : (
          <div className="grid gap-4">
            {documents.map((doc) => {
              const IconComponent = getFileIcon(doc.document_type);
              return (
                <div
                  key={doc.id}
                  className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <IconComponent size={20} className="text-blue-600" />
                        <h3 className="text-lg font-semibold text-gray-900">{doc.title}</h3>
                        <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                          {documentTypes.find(t => t.value === doc.document_type)?.label || doc.document_type}
                        </span>
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600 mb-3">
                        <div className="flex items-center gap-1">
                          <HardDrive size={16} />
                          <span>{formatFileSize(doc.file_size_mb)}</span>
                        </div>
                        {doc.page_count && (
                          <div className="flex items-center gap-1">
                            <FileText size={16} />
                            <span>{doc.page_count} pages</span>
                          </div>
                        )}
                        <div className="flex items-center gap-1">
                          <Calendar size={16} />
                          <span>{doc.uploaded_date}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <User size={16} />
                          <span>{doc.uploaded_by}</span>
                        </div>
                      </div>

                      {doc.description && (
                        <p className="text-gray-600 text-sm mb-3">{doc.description}</p>
                      )}
                    </div>

                    <div className="flex gap-2 ml-4">
                      {onOpenInViewer ? (
                        <button
                          onClick={() => onOpenInViewer(doc)}
                          className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                          title="Open in Viewer"
                        >
                          <Eye size={18} />
                        </button>
                      ) : (
                        <button
                          onClick={() => handleView(doc)}
                          className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                          title="View Document"
                        >
                          <Eye size={18} />
                        </button>
                      )}
                      <button
                        onClick={() => handleDownload(doc)}
                        className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                        title="Download Document"
                      >
                        <Download size={18} />
                      </button>
                      <button
                        onClick={() => handleDelete(doc.id)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        title="Delete Document"
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Upload Document</h3>
              <button
                onClick={() => setShowUploadModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X size={20} />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Document Type
                </label>
                <select
                  value={uploadForm.document_type}
                  onChange={(e) => setUploadForm(prev => ({ ...prev, document_type: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {documentTypes.map(type => (
                    <option key={type.value} value={type.value}>{type.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Document Files (Multiple Selection)
                </label>
                <input
                  type="file"
                  multiple
                  accept={getAcceptedExtensions(uploadForm.document_type)}
                  onChange={handleFileSelect}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                {selectedFiles.length > 0 && (
                  <div className="mt-2">
                    <p className="text-sm text-gray-600 mb-2">Selected files ({selectedFiles.length}):</p>
                    <div className="max-h-32 overflow-y-auto space-y-1">
                      {selectedFiles.map((file, index) => (
                        <div key={index} className="text-sm text-gray-700 bg-gray-50 p-2 rounded">
                          {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Title *
                </label>
                <input
                  type="text"
                  value={uploadForm.title}
                  onChange={(e) => setUploadForm(prev => ({ ...prev, title: e.target.value }))}
                  placeholder="Enter document title"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                </label>
                <textarea
                  value={uploadForm.description}
                  onChange={(e) => setUploadForm(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Enter document description (optional)"
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  onClick={() => setShowUploadModal(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleUpload}
                  disabled={uploading || selectedFiles.length === 0}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {uploading ? `Uploading ${selectedFiles.length} file(s)...` : `Upload ${selectedFiles.length} file(s)`}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Document Viewer Modal */}
      {showViewer && selectedDocument && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg w-full max-w-4xl h-5/6 mx-4 flex flex-col">
            <div className="flex justify-between items-center p-4 border-b">
              <h3 className="text-lg font-semibold">{selectedDocument.title}</h3>
              <button
                onClick={() => setShowViewer(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X size={20} />
              </button>
            </div>
            <div className="flex-1 p-4">
              {selectedDocument.file_url ? (
                <iframe
                  src={selectedDocument.file_url}
                  className="w-full h-full border-0"
                  title={selectedDocument.title}
                />
              ) : (
                <div className="flex items-center justify-center h-full text-gray-500">
                  <p>Document viewer not available</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentManager;
