import React, { useState, useEffect, useImperativeHandle, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
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
  FileCode,
  Edit,
  Wand2,
  FolderInput,
  FolderOpen,
  Filter,
  ChevronDown,
  ChevronUp,
  ExternalLink
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { apiClient } from '../../services/api';
import FileSelectionModal from './FileSelectionModal';

// Debug: Ensure this component is using updated code
console.log('DocumentManager component loaded with updated imports v2.0 with Auto-Extract button');

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
  product_category?: string;
  content_type?: string;
  processing_status?: string;
  metadata?: {
    product_category?: string;
    content_type?: string;
    version?: string;
    [key: string]: any;
  };
}

interface DocumentSearchParams {
  query: string;
  search_type: 'title' | 'content' | 'both';
  document_type: string;
}

interface DocumentManagerProps {
  onOpenInViewer?: (args: { id: string; title: string; url: string; type: 'pdf'|'docx'|'txt'|'xls'|'xlsx'|'ppt'|'pptx'|'html' }) => void;
  defaultDocType?: string;
}

export interface DocumentManagerRef {
  handleExtractMetadata: () => Promise<void>;
  openUploadModal: () => void;
}

const DocumentManager = React.forwardRef<DocumentManagerRef, DocumentManagerProps>(
  ({ onOpenInViewer, defaultDocType = 'all' }, ref) => {
  const { t } = useTranslation('ai');
  const navigate = useNavigate();
  const [documents, setDocuments] = useState<DocumentFile[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchParams, setSearchParams] = useState<DocumentSearchParams>({
    query: '',
    search_type: 'both',
    document_type: defaultDocType
  });
  
  // NEW: Advanced filter state
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [advancedFilters, setAdvancedFilters] = useState({
    product_category: '',
    content_type: '',
    processing_status: '',
    uploaded_by: '',
    date_from: '',
    date_to: '',
    file_size_min: '',
    file_size_max: '',
    sort_by: 'uploaded_at',
    sort_order: 'desc'
  });
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  // Individual metadata per file
  const [fileMetadata, setFileMetadata] = useState<Array<{
    file: File;
    title: string;
    description: string;
    document_type: string;
    product_category: string;
    content_type: string;
    version: string;
  }>>([]);
  const [uploadForm, setUploadForm] = useState({
    title: '',
    description: '',
    document_type: 'pdf',
    product_category: '',
    version: '',
    content_type: ''
  });
  const [showFileSelectionModal, setShowFileSelectionModal] = useState(false);
  
  // Simplified upload state - just track if uploading
  const [isUploading, setIsUploading] = useState(false);
  // State for "Apply to All" dropdowns
  const [applyProductKey, setApplyProductKey] = useState(0);
  const [applyContentTypeKey, setApplyContentTypeKey] = useState(0);
  const [selectedDocument, setSelectedDocument] = useState<DocumentFile | null>(null);
  const [showViewer, setShowViewer] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editMetadata, setEditMetadata] = useState({
    product_category: '',
    content_type: '',
    version: ''
  });
  const [extracting, setExtracting] = useState(false);
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(false); // Disabled by default - no constant refreshing
  const [useUploadQueue, setUseUploadQueue] = useState(true);
  const [showBulkUploadModal, setShowBulkUploadModal] = useState(false);
  const [uploadSource, setUploadSource] = useState<'browser' | 'server'>('browser');

  // Document type configurations
  const documentTypes = [
    { value: 'pdf', label: 'PDF Document', icon: FileText, extensions: ['.pdf'] },
    { value: 'doc', label: 'Word Document', icon: File, extensions: ['.doc', '.docx'] },
    { value: 'xls', label: 'Excel Spreadsheet', icon: FileSpreadsheet, extensions: ['.xls', '.xlsx'] },
    { value: 'ppt', label: 'PowerPoint Presentation', icon: Presentation, extensions: ['.ppt', '.pptx'] },
    { value: 'txt', label: 'Text Document', icon: FileCode, extensions: ['.txt', '.rtf'] },
    { value: 'SSB_KPR', label: 'SSB/KPR File', icon: FileText, extensions: ['.mhtml', '.html'] },
  ];

  // Initialize enabled file types after documentTypes is defined
  const [enabledFileTypes, setEnabledFileTypes] = useState<Set<string>>(new Set(documentTypes.map(t => t.value)));
  const [selectedFolder, setSelectedFolder] = useState('');
  const [bulkFiles, setBulkFiles] = useState<any[]>([]);
  const [bulkFileMetadata, setBulkFileMetadata] = useState<any[]>([]);
  const [bulkProcessing, setBulkProcessing] = useState(false);
  const [filteredOutFiles, setFilteredOutFiles] = useState<any[]>([]);
  const [jobMonitoring, setJobMonitoring] = useState(false);
  const [importStatus, setImportStatus] = useState<any>(null);
  const [bulkApplyProductKey, setBulkApplyProductKey] = useState(0);
  const [bulkApplyContentTypeKey, setBulkApplyContentTypeKey] = useState(0);
  const [bulkResults, setBulkResults] = useState<any>(null);
  const [progressInterval, setProgressInterval] = useState<NodeJS.Timeout | null>(null);
  const [showUploadProgress, setShowUploadProgress] = useState(false);
  const [uploadQueue, setUploadQueue] = useState<any[]>([]);

  // Product categories
  const productCategories = [
    { value: '', label: 'Select Product' },
    { value: 'openlab_cds', label: 'OpenLab CDS' },
    { value: 'openlab_ecm', label: 'OpenLab ECM' },
    { value: 'openlab_eln', label: 'OpenLab ELN' },
    { value: 'openlab_server', label: 'OpenLab Server' },
    { value: 'masshunter_workstation', label: 'MassHunter Workstation' },
    { value: 'masshunter_quantitative', label: 'MassHunter Quantitative' },
    { value: 'masshunter_qualitative', label: 'MassHunter Qualitative' },
    { value: 'masshunter_bioconfirm', label: 'MassHunter BioConfirm' },
    { value: 'masshunter_metabolomics', label: 'MassHunter Metabolomics' },
    { value: 'vnmrj_current', label: 'VNMRJ Current' },
    { value: 'vnmrj_legacy', label: 'VNMRJ Legacy' },
    { value: 'vnmr_legacy', label: 'VNMR Legacy' },
  ];

  // Content types
  const contentTypes = [
    { value: '', label: 'Select Document Type' },
    { value: 'installation_guide', label: 'Installation Guide' },
    { value: 'user_manual', label: 'User Manual' },
    { value: 'configuration_guide', label: 'Configuration Guide' },
    { value: 'troubleshooting_guide', label: 'Troubleshooting Guide' },
    { value: 'maintenance_procedure', label: 'Maintenance Procedure' },
    { value: 'calibration_procedure', label: 'Calibration Procedure' },
    { value: 'best_practice_guide', label: 'Best Practice Guide' },
    { value: 'video_tutorial', label: 'Video Tutorial' },
    { value: 'webinar_recording', label: 'Webinar Recording' },
    { value: 'ssb_kpr', label: 'SSB/KPR' },
  ];

  // Load documents on component mount
  useEffect(() => {
    // If defaultDocType is set, trigger search with that filter
    if (defaultDocType && defaultDocType !== 'all') {
      setSearchParams(prev => ({ ...prev, document_type: defaultDocType }));
      // Load with the filter immediately
      apiClient.searchDocuments('', 'both', defaultDocType)
        .then(response => {
          setDocuments(response.results || []);
          setError(null);
        })
        .catch(err => {
          setError(t('failedToLoadDocuments'));
          console.error('Error loading documents:', err);
        });
    } else {
      loadDocuments();
    }
  }, [defaultDocType]);

  // Debug: Check authentication status (non-blocking)
  useEffect(() => {
    const token = localStorage.getItem('anylab_token');
    console.log('Auth token exists:', !!token);
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
      setError(t('failedToLoadDocuments'));
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

  // NEW: Render processing status badge
  const renderStatusBadge = (status?: any) => {
    if (!status) return null;
    const statusValue: string | undefined = typeof status === 'string' ? status : status?.status;
    if (!statusValue) return null;
    const base = 'px-2 py-0.5 text-xs rounded-full';
    const map: Record<string, string> = {
      ready: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
      pending: 'bg-yellow-100 text-yellow-800',
      metadata_extracting: 'bg-teal-100 text-teal-800',
      chunking: 'bg-emerald-100 text-emerald-800',
      embedding: 'bg-lime-100 text-lime-800',
    };
    const cls = map[statusValue] || 'bg-gray-100 text-gray-800';
    const label = String(statusValue).replace('_', ' ');
    return (
      <span className={`${base} ${cls}`} title={t('processingStatus') + ': ' + label}>
        {label}
      </span>
    );
  };

  // NEW: Render truncation warning badge
  const renderTruncationWarning = (status?: any) => {
    if (!status || typeof status !== 'object') return null;
    const isTruncated = status.is_truncated;
    const coverage = status.processing_coverage;
    
    if (!isTruncated) return null;
    
    return (
      <span 
        className="px-2 py-0.5 text-xs rounded-full bg-orange-100 text-orange-800 flex items-center gap-1"
        title={t('documentTruncatedWarning', { coverage: coverage?.toFixed(1) })}
      >
        <span>⚠️</span>
        <span>{t('truncated')} ({coverage?.toFixed(0)}%)</span>
      </span>
    );
  };

  // Auto-poll documents list while any are processing (only when enabled)
  // Use ref to access latest documents without causing effect re-runs
  const documentsRef = useRef(documents);
  useEffect(() => {
    documentsRef.current = documents;
  }, [documents]);

  useEffect(() => {
    if (!autoRefreshEnabled) return;
    
    // Check if there are any active processing documents using ref (always current)
    const hasActive = documentsRef.current.some(d => {
      const ps: any = (d as any).processing_status;
      const sVal: string | undefined = typeof ps === 'string' ? ps : ps?.status;
      return sVal && sVal !== 'ready' && sVal !== 'failed';
    });
    
    if (!hasActive) return;
    
    // Only refresh every 5 seconds (reduced frequency) and only when there are active documents
    const interval = setInterval(() => {
      // Check current documents state for active processing (using ref for latest data)
      const stillHasActive = documentsRef.current.some(d => {
        const ps: any = (d as any).processing_status;
        const sVal: string | undefined = typeof ps === 'string' ? ps : ps?.status;
        return sVal && sVal !== 'ready' && sVal !== 'failed';
      });
      if (stillHasActive) {
        loadDocuments();
      }
    }, 5000); // Increased to 5 seconds to reduce refresh frequency
    
    return () => clearInterval(interval);
  }, [autoRefreshEnabled]); // Only re-run when autoRefreshEnabled changes, not when documents change

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    if (files.length === 0) return;

    // NEW: File count and size limits
    const MAX_FILES = 50;
    const MAX_TOTAL_SIZE_MB = 500; // 500 MB total
    
    if (files.length > MAX_FILES) {
      setError(t('tooManyFilesSelected', { max: MAX_FILES }));
      return;
    }

    const totalSizeMB = files.reduce((sum, file) => sum + file.size, 0) / (1024 * 1024);
    if (totalSizeMB > MAX_TOTAL_SIZE_MB) {
      setError(t('totalFileSizeTooLarge', { size: totalSizeMB.toFixed(2), max: MAX_TOTAL_SIZE_MB }));
      return;
    }

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
      setError(t('invalidFileTypes', { files: invalidFiles.join(', ') }));
    }

    if (validFiles.length > 0) {
      setSelectedFiles(validFiles);
      
      // NEW: Initialize individual metadata for each file
      const metadata = validFiles.map(file => {
        const extension = '.' + file.name.split('.').pop()?.toLowerCase();
        const selectedType = documentTypes.find(t => 
          t.extensions.includes(extension)
        ) || documentTypes[0];
        
        const baseTitle = file.name.replace(/\.[^/.]+$/, ''); // Remove extension
        
        return {
          file,
          title: baseTitle,
          description: '',
          document_type: selectedType.value,
          product_category: uploadForm.product_category || '',
          content_type: uploadForm.content_type || '',
          version: uploadForm.version || ''
        };
      });
      
      setFileMetadata(metadata);
      
      // Set document type based on first file for form defaults
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
  // NEW: Validate file metadata before upload
  const validateFileMetadata = (): boolean => {
    for (const meta of fileMetadata) {
      if (!meta.title.trim()) {
        setError(t('titleRequiredForFile', { filename: meta.file.name }));
        return false;
      }
      // Product category and content type are optional - auto-detection will handle them
    }
    return true;
  };

  // Simplified upload - always uses unified queue
  const handleUpload = async () => {
    if (fileMetadata.length === 0 && selectedFiles.length === 0) {
      setError(t('pleaseSelectAtLeastOneFile'));
      return;
    }

    // Initialize metadata if needed
    let metadataToUse: typeof fileMetadata = fileMetadata;
    if (fileMetadata.length === 0 && selectedFiles.length > 0) {
      metadataToUse = selectedFiles.map(file => {
        const extension = '.' + file.name.split('.').pop()?.toLowerCase();
        const selectedType = documentTypes.find(t => 
          t.extensions.includes(extension)
        ) || documentTypes[0];
        
        return {
          file,
          title: uploadForm.title.trim() || file.name.replace(/\.[^/.]+$/, ''),
          description: uploadForm.description,
          document_type: uploadForm.document_type,
          product_category: uploadForm.product_category,
          content_type: uploadForm.content_type,
          version: uploadForm.version
        };
      });
      setFileMetadata(metadataToUse);
    }

    const finalMetadata = fileMetadata.length > 0 ? fileMetadata : metadataToUse;
    
    if (!finalMetadata || finalMetadata.length === 0) {
      setError(t('noFilesToUpload'));
      return;
    }
    
    // Validate metadata
    for (const meta of finalMetadata) {
      if (!meta.title.trim()) {
        setError(t('titleRequiredForFile', { filename: meta.file.name }));
        return;
      }
    }

    setError(null);
    setIsUploading(true);
    
    try {
      // Create job using unified upload queue
      const formData = new FormData();
      formData.append('job_type', 'file');
      formData.append('source', 'document_manager_upload');
      formData.append('priority', '5');
      
      // Add all files
      finalMetadata.forEach((meta) => {
        formData.append('files', meta.file);
      });
      
      // Add metadata as JSON
      formData.append('metadata', JSON.stringify({
        files: finalMetadata.map(meta => ({
          name: meta.file.name,
          title: meta.title,
          description: meta.description,
          document_type: meta.document_type,
          product_category: meta.product_category,
          content_type: meta.content_type,
          version: meta.version
        }))
      }));
      
      const response = await apiClient.post('/ai/upload/queue/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      const job = (response as any).data?.data || (response as any).data;
      setSuccess(
        `Files queued successfully! Job ID: ${job.job_id?.substring(0, 8)}... ` +
        `Files will be processed in the background. You can continue adding more files.`
      );
      setShowFileSelectionModal(false);
      setSelectedFiles([]);
      setFileMetadata([]);
      
      // Reload documents after a delay (files will appear after processing)
      setTimeout(() => {
        loadDocuments();
      }, 3000);
    } catch (err: any) {
      console.error('Upload error:', err);
      setError(err.response?.data?.message || err.message || 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleSearch = async () => {
    setLoading(true);
    try {
      let results: DocumentFile[] = [];
      
      // If there's a search query, perform search
      if (searchParams.query.trim()) {
        const response = await apiClient.searchDocuments(
          searchParams.query, 
          searchParams.search_type, 
          searchParams.document_type
        );
        results = response.results || [];
      } else {
        // Otherwise, load all documents
        const response = await apiClient.getDocuments();
        results = response.documents || [];
      }
      
      // Apply advanced filters
      let filteredResults = results;
      
      if (advancedFilters.product_category) {
        filteredResults = filteredResults.filter(doc => 
          doc.product_category === advancedFilters.product_category
        );
      }
      
      if (advancedFilters.content_type) {
        filteredResults = filteredResults.filter(doc => 
          doc.content_type === advancedFilters.content_type
        );
      }
      
      if (advancedFilters.processing_status) {
        // Note: This requires the backend to return processing_status
        // For now, we'll skip this filter if not available
        // filteredResults = filteredResults.filter(doc => 
        //   doc.processing_status === advancedFilters.processing_status
        // );
      }
      
      if (advancedFilters.date_from) {
        const fromDate = new Date(advancedFilters.date_from);
        filteredResults = filteredResults.filter(doc => {
          const docDate = new Date(doc.uploaded_date);
          return docDate >= fromDate;
        });
      }
      
      if (advancedFilters.date_to) {
        const toDate = new Date(advancedFilters.date_to);
        filteredResults = filteredResults.filter(doc => {
          const docDate = new Date(doc.uploaded_date);
          return docDate <= toDate;
        });
      }
      
      if (advancedFilters.file_size_min) {
        const minSizeMB = parseFloat(advancedFilters.file_size_min);
        filteredResults = filteredResults.filter(doc => {
          const sizeMB = parseFloat(doc.file_size_mb);
          return sizeMB >= minSizeMB;
        });
      }
      
      if (advancedFilters.file_size_max) {
        const maxSizeMB = parseFloat(advancedFilters.file_size_max);
        filteredResults = filteredResults.filter(doc => {
          const sizeMB = parseFloat(doc.file_size_mb);
          return sizeMB <= maxSizeMB;
        });
      }
      
      // Sort results
      filteredResults.sort((a, b) => {
        const aVal = getFieldValue(a, advancedFilters.sort_by);
        const bVal = getFieldValue(b, advancedFilters.sort_by);
        
        if (advancedFilters.sort_order === 'asc') {
          return aVal > bVal ? 1 : -1;
        } else {
          return aVal < bVal ? 1 : -1;
        }
      });
      
      setDocuments(filteredResults);
      setError(null);
    } catch (err) {
      setError(t('failedToSearchDocuments'));
      console.error('Error searching documents:', err);
    } finally {
      setLoading(false);
    }
  };

  // Helper function to get field value for sorting
  const getFieldValue = (doc: DocumentFile, field: string): any => {
    switch (field) {
      case 'uploaded_at':
      case 'uploaded_date':
        return new Date(doc.uploaded_date).getTime();
      case 'title':
        return doc.title.toLowerCase();
      case 'filename':
        return doc.filename.toLowerCase();
      case 'file_size':
        return parseFloat(doc.file_size_mb);
      case 'page_count':
        return doc.page_count || 0;
      default:
        return '';
    }
  };

  const handleDelete = async (docId: number) => {
    if (!window.confirm(t('confirmDeleteDocument'))) {
      return;
    }

    try {
      await apiClient.deleteDocument(docId);
      setSuccess(t('documentDeletedSuccessfully'));
      loadDocuments();
    } catch (err: any) {
      setError(err.message || t('failedToDeleteDocument'));
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
      setError(t('failedToDownloadDocument'));
    }
  };

  const handleView = (doc: DocumentFile) => {
    // For all document types, use the embedded viewer
    if (onOpenInViewer && doc.file_url) {
      // Determine document type for viewer
      let docType: 'pdf'|'docx'|'txt'|'xls'|'xlsx'|'ppt'|'pptx'|'html' = 'pdf';
      const type = doc.document_type || '';
      if (type === 'doc' || type === 'docx') docType = 'docx';
      else if (type === 'xls') docType = 'xls';
      else if (type === 'xlsx') docType = 'xlsx';
      else if (type === 'ppt') docType = 'ppt';
      else if (type === 'pptx') docType = 'pptx';
      else if (type === 'txt') docType = 'txt';
      else if (type === 'SSB_KPR') docType = 'html'; // Treat SSB_KPR as HTML for iframe rendering
      else docType = 'pdf';
      
      // Open in the embedded DocumentViewer component
      onOpenInViewer({
        id: String(doc.id),
        title: doc.title,
        url: doc.file_url,
        type: docType,
      });
    } else if (doc.document_type === 'pdf' && doc.file_url) {
      // Fallback: Open PDF in new tab if file_url is available
      window.open(doc.file_url, '_blank');
    } else {
      // For other document types without file_url, show error
      setError(t('documentUrlNotAvailable'));
    }
  };

  const formatFileSize = (size: string) => {
    return size;
  };

  const handleEditMetadata = (doc: DocumentFile) => {
    // Populate edit form with existing metadata
    setSelectedDocument(doc);
    setEditMetadata({
      product_category: doc.metadata?.product_category || doc.product_category || '',
      content_type: doc.metadata?.content_type || doc.content_type || '',
      version: doc.metadata?.version || ''
    });
    setShowEditModal(true);
  };

  const handleSaveMetadata = async () => {
    if (!selectedDocument) return;

    try {
      await apiClient.updateDocumentMetadata(selectedDocument.id, {
        product_category: editMetadata.product_category,
        content_type: editMetadata.content_type,
        version: editMetadata.version
      });
      
      setSuccess(t('metadataUpdatedSuccessfully'));
      setShowEditModal(false);
      setSelectedDocument(null);
      loadDocuments();
    } catch (err: any) {
      setError(err.message || t('failedToUpdateMetadata'));
    }
  };

  const handleExtractMetadata = async () => {
    const confirmed = window.confirm(
      t('extractMetadataConfirmation')
    );
    
    if (!confirmed) return;

    setExtracting(true);
    setError(null);

    try {
      const result = await apiClient.extractDocumentsMetadata();
      
      setSuccess(
        t('metadataExtractedSuccessfully', { 
          updated: result.updated_count, 
          skipped: result.skipped_count 
        })
      );
      
      // Reload documents to show updated data
      loadDocuments();
    } catch (err: any) {
      setError(err.message || t('failedToExtractMetadata'));
    } finally {
      setExtracting(false);
    }
  };

  // Expose methods via ref for parent component
  useImperativeHandle(ref, () => ({
    handleExtractMetadata,
    openUploadModal: () => setShowFileSelectionModal(true),
  }));

  // Handle folder scan
  const handleScanFolder = async () => {
    if (!selectedFolder.trim()) {
      setError(t('pleaseEnterFolderPath'));
      return;
    }

    setBulkProcessing(true);
    setError(null);
    try {
      const response = await apiClient.post('/ai/process/bulk/scan-folder/', {
        folder_path: selectedFolder,
        auto_upload: false,
        priority: 5
      });
      
      const data = (response as any).data;
      if (data?.success && data?.files) {
        setBulkFiles(data.files);
        setSuccess(t('foundFilesInFolder', { count: data.files.length }));
      } else {
        setError(t('noFilesFoundInFolder'));
      }
    } catch (err: any) {
      setError(err.response?.data?.error || err.message || t('failedToScanFolder'));
    } finally {
      setBulkProcessing(false);
    }
  };

  // Handle bulk import from server
  const handleBulkImport = async () => {
    if (bulkFiles.length === 0) {
      setError(t('pleaseSelectFilesToImport'));
      return;
    }

    setBulkProcessing(true);
    setError(null);
    try {
      const filesToImport = bulkFiles.map(f => ({
        file_path: f.file_path || f.path,
        filename: f.name || f.filename
      }));

      const response = await apiClient.bulkImportFiles(filesToImport);
      const result = response as any;
      
      if (result.success) {
        setSuccess(t('bulkImportSuccess', { count: result.successful || 0 }));
        setBulkFiles([]);
        setSelectedFolder('');
        loadDocuments();
      } else {
        setError(result.error || t('bulkImportFailed'));
      }
    } catch (err: any) {
      setError(err.response?.data?.error || err.message || t('bulkImportFailed'));
    } finally {
      setBulkProcessing(false);
    }
  };

  // Handle bulk import from browser
  const handleBulkImportFromBrowser = async () => {
    if (bulkFileMetadata.length === 0 && selectedFiles.length === 0) {
      setError(t('pleaseSelectFilesToImport'));
      return;
    }

    setBulkProcessing(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('job_type', 'file');
      formData.append('source', 'file_upload');
      formData.append('priority', '5');

      // Use metadata if available, otherwise use selected files
      const filesToUpload = bulkFileMetadata.length > 0 
        ? bulkFileMetadata.map(m => m.file)
        : selectedFiles;

      filesToUpload.forEach((file, index) => {
        formData.append('files', file);
        if (bulkFileMetadata[index]) {
          const meta = bulkFileMetadata[index];
          formData.append(`metadata_${index}`, JSON.stringify({
            title: meta.title,
            description: meta.description,
            document_type: meta.document_type,
            product_category: meta.product_category,
            content_type: meta.content_type,
            version: meta.version
          }));
        }
      });

      const response = await apiClient.post('/ai/upload/queue/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setSuccess(t('filesQueuedSuccessfully'));
      setShowBulkUploadModal(false);
      setSelectedFiles([]);
      setBulkFileMetadata([]);
      loadDocuments();
    } catch (err: any) {
      setError(err.response?.data?.error || err.message || t('uploadFailed'));
    } finally {
      setBulkProcessing(false);
    }
  };

  console.log('Rendering DocumentManager with extract button visible. extracting state:', extracting);

  return (
    <div className="p-6 bg-white rounded-lg shadow-sm">

      {/* Search Bar */}
      <div className="mb-6 p-4 bg-gray-50 rounded-lg">
        <div className="flex gap-4 items-end">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('searchDocuments')}
            </label>
            <input
              type="text"
              value={searchParams.query}
              onChange={(e) => setSearchParams(prev => ({ ...prev, query: e.target.value }))}
              placeholder={t('searchByTitleFilenameDescription')}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('documentType')}
            </label>
            <select
              value={searchParams.document_type}
              onChange={(e) => setSearchParams(prev => ({ ...prev, document_type: e.target.value }))}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="all">{t('allTypes')}</option>
              <option value="SSB_KPR">SSB/KPR</option>
              {documentTypes.map(type => (
                <option key={type.value} value={type.value}>{type.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('searchType')}
            </label>
            <select
              value={searchParams.search_type}
              onChange={(e) => setSearchParams(prev => ({ ...prev, search_type: e.target.value as any }))}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="both">{t('titleAndContent')}</option>
              <option value="title">{t('titleOnly')}</option>
              <option value="content">{t('contentOnly')}</option>
            </select>
          </div>
          <button
            onClick={handleSearch}
            className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
          >
            <Search size={20} />
            {t('search')}
          </button>
          <button
            onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
            className="bg-teal-600 hover:bg-teal-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
          >
            <Filter size={20} />
            {showAdvancedFilters ? t('hideFilters') : t('advancedFilters')}
            {showAdvancedFilters ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
        </div>
      </div>

      {/* NEW: Advanced Filters Section */}
      {showAdvancedFilters && (
        <div className="mb-6 p-4 bg-teal-50 rounded-lg border border-teal-200">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {/* Product Category Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('productCategory')}
              </label>
              <select
                value={advancedFilters.product_category}
                onChange={(e) => setAdvancedFilters(prev => ({ ...prev, product_category: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm"
              >
                <option value="">{t('allProducts')}</option>
                {productCategories.filter(cat => cat.value).map(category => (
                  <option key={category.value} value={category.value}>{category.label}</option>
                ))}
              </select>
            </div>

            {/* Content Type Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('contentType')}
              </label>
              <select
                value={advancedFilters.content_type}
                onChange={(e) => setAdvancedFilters(prev => ({ ...prev, content_type: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm"
              >
                <option value="">{t('allTypes')}</option>
                {contentTypes.map(type => (
                  <option key={type.value} value={type.value}>{type.label}</option>
                ))}
              </select>
            </div>

            {/* Processing Status Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('processingStatus')}
              </label>
              <select
                value={advancedFilters.processing_status}
                onChange={(e) => setAdvancedFilters(prev => ({ ...prev, processing_status: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm"
              >
                <option value="">{t('allStatus')}</option>
                <option value="ready">{t('ready')}</option>
                <option value="pending">{t('pending')}</option>
                <option value="metadata_extracting">{t('extractingMetadata')}</option>
                <option value="chunking">{t('chunking')}</option>
                <option value="embedding">{t('embedding')}</option>
                <option value="failed">{t('failed')}</option>
              </select>
            </div>

            {/* Sort By */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('sortBy')}
              </label>
              <select
                value={advancedFilters.sort_by}
                onChange={(e) => setAdvancedFilters(prev => ({ ...prev, sort_by: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm"
              >
                <option value="uploaded_at">{t('uploadDate')}</option>
                <option value="title">{t('title')}</option>
                <option value="filename">{t('filename')}</option>
                <option value="file_size">{t('fileSize')}</option>
                <option value="page_count">{t('pageCount')}</option>
              </select>
            </div>

            {/* Sort Order */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('order')}
              </label>
              <select
                value={advancedFilters.sort_order}
                onChange={(e) => setAdvancedFilters(prev => ({ ...prev, sort_order: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm"
              >
                <option value="desc">{t('descending')}</option>
                <option value="asc">{t('ascending')}</option>
              </select>
            </div>

            {/* Date From */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('fromDate')}
              </label>
              <input
                type="date"
                value={advancedFilters.date_from}
                onChange={(e) => setAdvancedFilters(prev => ({ ...prev, date_from: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm"
              />
            </div>

            {/* Date To */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('toDate')}
              </label>
              <input
                type="date"
                value={advancedFilters.date_to}
                onChange={(e) => setAdvancedFilters(prev => ({ ...prev, date_to: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm"
              />
            </div>

            {/* File Size Min */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('minSizeMB')}
              </label>
              <input
                type="number"
                value={advancedFilters.file_size_min}
                onChange={(e) => setAdvancedFilters(prev => ({ ...prev, file_size_min: e.target.value }))}
                placeholder="0"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm"
              />
            </div>

            {/* File Size Max */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('maxSizeMB')}
              </label>
              <input
                type="number"
                value={advancedFilters.file_size_max}
                onChange={(e) => setAdvancedFilters(prev => ({ ...prev, file_size_max: e.target.value }))}
                placeholder={t('unlimited')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm"
              />
            </div>
          </div>

          {/* Filter Actions */}
          <div className="flex gap-3 mt-4 pt-4 border-t border-teal-200">
            <button
              onClick={() => {
                setAdvancedFilters({
                  product_category: '',
                  content_type: '',
                  processing_status: '',
                  uploaded_by: '',
                  date_from: '',
                  date_to: '',
                  file_size_min: '',
                  file_size_max: '',
                  sort_by: 'uploaded_at',
                  sort_order: 'desc'
                });
                handleSearch();
              }}
              className="px-4 py-2 text-teal-700 border border-teal-300 rounded-lg hover:bg-teal-100 transition-colors text-sm font-medium"
            >
              {t('clearFilters')}
            </button>
            <button
              onClick={handleSearch}
              className="px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition-colors text-sm font-medium"
            >
              {t('applyFilters')}
            </button>
          </div>
        </div>
      )}

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
      <div 
        className="space-y-4 max-h-[600px] overflow-y-auto pr-2" 
        style={{
          scrollbarWidth: 'thin',
          scrollbarColor: '#cbd5e1 #f1f5f9'
        }}
      >
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-2 text-gray-600">{t('loadingDocuments')}</p>
          </div>
        ) : documents.length === 0 ? (
          <div className="text-center py-8">
            <FileText size={48} className="mx-auto text-gray-400 mb-4" />
            <p className="text-gray-600">{t('noDocumentsFound')}</p>
            <p className="text-gray-500 text-sm">{t('uploadFirstDocument')}</p>
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
                        <IconComponent size={20} className="text-emerald-600" />
                        <h3 className="text-lg font-semibold text-gray-900">{doc.title}</h3>
                        <span className="px-2 py-1 bg-emerald-100 text-emerald-800 text-xs rounded-full">
                          {documentTypes.find(t => t.value === doc.document_type)?.label || doc.document_type}
                        </span>
                        {renderStatusBadge((doc as any).processing_status)}
                        {renderTruncationWarning((doc as any).processing_status)}
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600 mb-3">
                        <div className="flex items-center gap-1">
                          <HardDrive size={16} />
                          <span>{formatFileSize(doc.file_size_mb)}</span>
                        </div>
                        {doc.page_count !== undefined && doc.page_count !== null && doc.page_count > 0 && (
                          <div className="flex items-center gap-1">
                            <FileText size={16} />
                            <span>{doc.page_count} {t('pages')}</span>
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
                      <button
                        onClick={() => handleView(doc)}
                        className="p-2 text-emerald-600 hover:bg-emerald-50 rounded-lg transition-colors"
                        title={t('viewDocument')}
                      >
                        <Eye size={18} />
                      </button>
                      {(() => {
                        const ps: any = (doc as any).processing_status;
                        const sVal: string | undefined = typeof ps === 'string' ? ps : ps?.status;
                        const ufId: number | undefined = (doc as any).uploaded_file_id;
                        if (ufId && sVal === 'failed') {
                          return (
                            <button
                              onClick={async () => {
                                try {
                                  await apiClient.retryFileProcessing(ufId);
                                  setSuccess(t('retryScheduled'));
                                  loadDocuments();
                                } catch (e: any) {
                                  setError(e?.message || t('failedToRetry'));
                                }
                              }}
                              className="p-2 text-orange-600 hover:bg-orange-50 rounded-lg transition-colors"
                              title={t('retryProcessing')}
                            >
                              <Wand2 size={18} />
                            </button>
                          );
                        }
                        return null;
                      })()}
                      <button
                        onClick={() => handleDownload(doc)}
                        className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                        title={t('downloadDocument')}
                      >
                        <Download size={18} />
                      </button>
                      <button
                        onClick={() => handleEditMetadata(doc)}
                        className="p-2 text-lime-600 hover:bg-lime-50 rounded-lg transition-colors"
                        title={t('editMetadata')}
                      >
                        <Edit size={18} />
                      </button>
                      <button
                        onClick={() => handleDelete(doc.id)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        title={t('deleteDocument')}
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

      {/* File Selection Modal */}
      <FileSelectionModal
        isOpen={showFileSelectionModal}
        onClose={() => setShowFileSelectionModal(false)}
        onQueued={() => {
          setSuccess(t('filesQueuedSuccessfully') || 'Files queued successfully! Check Upload Queue for status.');
          if (autoRefreshEnabled) {
            setTimeout(() => loadDocuments(), 2000);
          }
        }}
      />

      {/* Old Upload Modal - REMOVED: Replaced by FileSelectionModal */}
      {false && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-6xl mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">{t('uploadDocument')}{fileMetadata.length > 1 ? ` (${fileMetadata.length} ${t('files')})` : ''}</h3>
              <button
                onClick={() => {
                  setShowFileSelectionModal(false);
                  setSelectedFiles([]);
                  setFileMetadata([]);
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <X size={20} />
              </button>
            </div>

            <div className="space-y-4">
              {/* File Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('documentFilesMultipleSelection')}
                </label>
                <input
                  type="file"
                  multiple
                  accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.rtf,.mhtml,.html"
                  onChange={handleFileSelect}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
                {selectedFiles.length > 0 && (
                  <div className="mt-2">
                    <p className="text-sm text-gray-600 mb-2">
                      {t('selectedFilesTotalSize', { 
                        count: selectedFiles.length, 
                        size: (selectedFiles.reduce((sum, f) => sum + f.size, 0) / 1024 / 1024).toFixed(2) 
                      })}
                    </p>
                  </div>
                )}
              </div>

              {/* NEW: Metadata Table for Multiple Files */}
              {fileMetadata.length > 0 && (
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <label className="block text-sm font-medium text-gray-700">
                      {t('fileMetadata')} {fileMetadata.length > 1 && `(${t('editEachFileIndividually')})`}
                    </label>
                    {fileMetadata.length > 1 && (
                      <div className="flex gap-2">
                        <select
                          key={applyProductKey}
                          onChange={(e) => {
                            if (e.target.value) {
                              setFileMetadata(prev => prev.map(m => ({ ...m, product_category: e.target.value })));
                              // Reset dropdown by changing key
                              setApplyProductKey(prev => prev + 1);
                            }
                          }}
                          className="text-xs px-2 py-1 bg-emerald-100 text-emerald-700 rounded hover:bg-emerald-200 border border-emerald-300 focus:outline-none cursor-pointer"
                          defaultValue=""
                        >
                          <option value="">{t('applyProductToAll')}</option>
                          {productCategories.filter(cat => cat.value).map(category => (
                            <option key={category.value} value={category.value}>{category.label}</option>
                          ))}
                        </select>
                        <select
                          key={applyContentTypeKey}
                          onChange={(e) => {
                            if (e.target.value) {
                              setFileMetadata(prev => prev.map(m => ({ ...m, content_type: e.target.value })));
                              // Reset dropdown by changing key
                              setApplyContentTypeKey(prev => prev + 1);
                            }
                          }}
                          className="text-xs px-2 py-1 bg-emerald-100 text-emerald-700 rounded hover:bg-emerald-200 border border-emerald-300 focus:outline-none cursor-pointer"
                          defaultValue=""
                        >
                          <option value="">{t('applyContentTypeToAll')}</option>
                          {contentTypes.filter(type => type.value).map(type => (
                            <option key={type.value} value={type.value}>{type.label}</option>
                          ))}
                        </select>
                      </div>
                    )}
                  </div>
                  
                  <div className="border border-gray-300 rounded-lg overflow-hidden">
                    <div className="overflow-x-auto max-h-[400px] overflow-y-auto">
                      <table className="w-full text-sm">
                        <thead className="bg-gray-50 sticky top-0">
                          <tr>
                            <th className="px-3 py-2 text-left font-medium text-gray-700 border-b">{t('filename')}</th>
                            <th className="px-3 py-2 text-left font-medium text-gray-700 border-b">{t('title')} *</th>
                            <th className="px-3 py-2 text-left font-medium text-gray-700 border-b">{t('description')}</th>
                            <th className="px-3 py-2 text-left font-medium text-gray-700 border-b">{t('product')}</th>
                            <th className="px-3 py-2 text-left font-medium text-gray-700 border-b">{t('contentType')}</th>
                            <th className="px-3 py-2 text-left font-medium text-gray-700 border-b">{t('version')}</th>
                            <th className="px-3 py-2 text-left font-medium text-gray-700 border-b">{t('size')}</th>
                          </tr>
                        </thead>
                        <tbody>
                          {fileMetadata.map((meta, index) => (
                            <tr key={index} className="border-b hover:bg-gray-50">
                              <td className="px-3 py-2 text-gray-700">
                                <div className="max-w-xs truncate" title={meta.file.name}>
                                  {meta.file.name}
                                </div>
                              </td>
                              <td className="px-3 py-2">
                                <input
                                  type="text"
                                  value={meta.title}
                                  onChange={(e) => {
                                    const newMetadata = [...fileMetadata];
                                    newMetadata[index].title = e.target.value;
                                    setFileMetadata(newMetadata);
                                  }}
                                  className="w-full px-2 py-1 border border-gray-300 rounded text-xs focus:ring-1 focus:ring-primary-500"
                                  placeholder={t('enterTitle')}
                                />
                              </td>
                              <td className="px-3 py-2">
                                <input
                                  type="text"
                                  value={meta.description}
                                  onChange={(e) => {
                                    const newMetadata = [...fileMetadata];
                                    newMetadata[index].description = e.target.value;
                                    setFileMetadata(newMetadata);
                                  }}
                                  className="w-full px-2 py-1 border border-gray-300 rounded text-xs focus:ring-1 focus:ring-primary-500"
                                  placeholder={t('optional')}
                                />
                              </td>
                              <td className="px-3 py-2">
                                <select
                                  value={meta.product_category}
                                  onChange={(e) => {
                                    const newMetadata = [...fileMetadata];
                                    newMetadata[index].product_category = e.target.value;
                                    setFileMetadata(newMetadata);
                                  }}
                                  className="w-full px-2 py-1 border border-gray-300 rounded text-xs focus:ring-1 focus:ring-primary-500"
                                >
                                  {productCategories.map(cat => (
                                    <option key={cat.value} value={cat.value}>{cat.label}</option>
                                  ))}
                                </select>
                              </td>
                              <td className="px-3 py-2">
                                <select
                                  value={meta.content_type}
                                  onChange={(e) => {
                                    const newMetadata = [...fileMetadata];
                                    newMetadata[index].content_type = e.target.value;
                                    setFileMetadata(newMetadata);
                                  }}
                                  className="w-full px-2 py-1 border border-gray-300 rounded text-xs focus:ring-1 focus:ring-primary-500"
                                >
                                  {contentTypes.map(type => (
                                    <option key={type.value} value={type.value}>{type.label}</option>
                                  ))}
                                </select>
                              </td>
                              <td className="px-3 py-2">
                                <input
                                  type="text"
                                  value={meta.version}
                                  onChange={(e) => {
                                    const newMetadata = [...fileMetadata];
                                    newMetadata[index].version = e.target.value;
                                    setFileMetadata(newMetadata);
                                  }}
                                  className="w-full px-2 py-1 border border-gray-300 rounded text-xs focus:ring-1 focus:ring-primary-500"
                                  placeholder={t('versionExample')}
                                />
                              </td>
                              <td className="px-3 py-2 text-gray-600 text-xs">
                                {(meta.file.size / 1024 / 1024).toFixed(2)} MB
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {/* Single File Form (fallback for single file) */}
              {fileMetadata.length === 0 && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Title *
                    </label>
                    <input
                      type="text"
                      value={uploadForm.title}
                      onChange={(e) => setUploadForm(prev => ({ ...prev, title: e.target.value }))}
                      placeholder="Enter document title"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
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
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Product Category <span className="text-gray-500 text-xs">(optional - will be auto-detected)</span>
                    </label>
                    <select
                      value={uploadForm.product_category}
                      onChange={(e) => setUploadForm(prev => ({ ...prev, product_category: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    >
                      {productCategories.map(category => (
                        <option key={category.value} value={category.value}>{category.label}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Content Type <span className="text-gray-500 text-xs">(optional - will be auto-detected)</span>
                    </label>
                    <select
                      value={uploadForm.content_type}
                      onChange={(e) => setUploadForm(prev => ({ ...prev, content_type: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    >
                      {contentTypes.map(type => (
                        <option key={type.value} value={type.value}>{type.label}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Version (optional)
                    </label>
                    <input
                      type="text"
                      value={uploadForm.version}
                      onChange={(e) => setUploadForm(prev => ({ ...prev, version: e.target.value }))}
                      placeholder="e.g., 3.2.1"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    />
                  </div>
                </>
              )}

              <div className="flex gap-3 pt-4 border-t">
                <button
                  onClick={() => {
                    setShowFileSelectionModal(false);
                    setSelectedFiles([]);
                    setFileMetadata([]);
                  }}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleUpload}
                  disabled={isUploading || fileMetadata.length === 0}
                  className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isUploading ? t('uploading') : t('uploadFiles', { count: fileMetadata.length })}
                </button>
              </div>
              
              {/* Option to use unified upload queue */}
              <div className="mt-4 pt-4 border-t border-gray-200">
                <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={useUploadQueue}
                    onChange={(e) => setUseUploadQueue(e.target.checked)}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span>Use unified upload queue (recommended for multiple files - provides better progress tracking and control)</span>
                </label>
                {useUploadQueue && (
                  <p className="text-xs text-gray-500 mt-1 ml-6">
                    Files will be processed through the upload queue. Check the Upload Queue page to monitor progress.
                  </p>
                )}
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
                  <p>{t('documentViewerNotAvailable')}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Edit Metadata Modal */}
      {showEditModal && selectedDocument && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">{t('editMetadata')}</h3>
              <button
                onClick={() => setShowEditModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X size={20} />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('productCategory')} <span className="text-gray-500 text-xs">({t('optional')})</span>
                </label>
                <select
                  value={editMetadata.product_category}
                  onChange={(e) => setEditMetadata(prev => ({ ...prev, product_category: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  {productCategories.map(category => (
                    <option key={category.value} value={category.value}>{category.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('contentType')} <span className="text-gray-500 text-xs">({t('optional')})</span>
                </label>
                <select
                  value={editMetadata.content_type}
                  onChange={(e) => setEditMetadata(prev => ({ ...prev, content_type: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  {contentTypes.map(type => (
                    <option key={type.value} value={type.value}>{type.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('version')}
                </label>
                <input
                  type="text"
                  value={editMetadata.version}
                  onChange={(e) => setEditMetadata(prev => ({ ...prev, version: e.target.value }))}
                  placeholder={t('versionExample')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  onClick={() => setShowEditModal(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  {t('cancel')}
                </button>
                <button
                  onClick={handleSaveMetadata}
                  className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                >
                  {t('save')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Bulk Upload Modal - REMOVED: Use UnifiedUploadQueue instead */}
      {false && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">{t('bulkImportFromFolder')}</h3>
              <button
                onClick={() => setShowBulkUploadModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X size={20} />
              </button>
            </div>

            <div className="space-y-4">
              {/* Toggle between Browser and Server methods */}
              <div className="flex gap-2 mb-4 border-b">
                <button
                  onClick={() => setUploadSource('browser')}
                  className={`flex-1 px-4 py-2 rounded-t-lg ${
                    uploadSource === 'browser'
                      ? 'bg-green-100 text-green-700 font-semibold'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  } transition-colors`}
                >
                  🌐 {t('selectFromBrowser')}
                </button>
                <button
                  onClick={() => setUploadSource('server')}
                  className={`flex-1 px-4 py-2 rounded-t-lg ${
                    uploadSource === 'server'
                      ? 'bg-green-100 text-green-700 font-semibold'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  } transition-colors`}
                >
                  💾 {t('serverFolderPath')}
                </button>
              </div>

              {/* File Type Filter Selection */}
              {uploadSource === 'browser' && (
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    📄 {t('selectFileTypesToInclude')}
                  </label>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                    {documentTypes.map((docType) => {
                      const IconComponent = docType.icon;
                      const isEnabled = enabledFileTypes.has(docType.value);
                      return (
                        <button
                          key={docType.value}
                          onClick={() => {
                            const newSet = new Set(enabledFileTypes);
                            if (isEnabled) {
                              newSet.delete(docType.value);
                            } else {
                              newSet.add(docType.value);
                            }
                            setEnabledFileTypes(newSet);
                              // Re-filter files if already selected
                              if (selectedFiles.length > 0) {
                                handleFileSelect({ target: { files: selectedFiles } } as any);
                              }
                          }}
                          className={`flex items-center gap-2 px-3 py-2 rounded-lg border-2 transition-all ${
                            isEnabled
                              ? 'bg-emerald-50 border-blue-500 text-emerald-700'
                              : 'bg-white border-gray-300 text-gray-600 hover:bg-gray-50'
                          }`}
                        >
                          <IconComponent size={16} />
                          <span className="text-xs font-medium">{docType.label}</span>
                        </button>
                      );
                    })}
                    {/* HTML/MHTML toggle */}
                    <button
                      onClick={() => {
                        const newSet = new Set(enabledFileTypes);
                        const hasHtml = enabledFileTypes.has('mhtml');
                        if (hasHtml) {
                          newSet.delete('mhtml');
                        } else {
                          newSet.add('mhtml');
                        }
                        setEnabledFileTypes(newSet);
                        if (selectedFiles.length > 0) {
                          handleFileSelect({ target: { files: selectedFiles } } as any);
                        }
                      }}
                      className={`flex items-center gap-2 px-3 py-2 rounded-lg border-2 transition-all ${
                        enabledFileTypes.has('mhtml')
                          ? 'bg-emerald-50 border-blue-500 text-emerald-700'
                          : 'bg-white border-gray-300 text-gray-600 hover:bg-gray-50'
                      }`}
                    >
                      <FileCode size={16} />
                      <span className="text-xs font-medium">HTML/MHTML</span>
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    {t('onlySelectedTypesIncluded')}
                  </p>
                </div>
              )}

              {/* Browser Folder Selection */}
              {uploadSource === 'browser' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {t('selectFolderFromComputer')}
                  </label>
                  <input
                    type="file"
                    {...({ webkitdirectory: '' } as any)}
                    multiple
                    onChange={handleFileSelect}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    {t('chooseFolderToUpload')}
                  </p>
                </div>
              )}

              {/* Server Folder Path (existing method) */}
              {uploadSource === 'server' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {t('serverFolderPath')}
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={selectedFolder}
                      onChange={(e) => setSelectedFolder(e.target.value)}
                      placeholder={t('serverFolderPathExample')}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    />
                    <button
                      onClick={handleScanFolder}
                      disabled={bulkProcessing}
                      className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors disabled:opacity-50"
                    >
                      <FolderOpen size={20} />
                      {bulkProcessing ? t('scanning') : t('scanFolder')}
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {t('enterServerFolderPath')}
                  </p>
                </div>
              )}

              {/* NEW: Real-time Status Display */}
              {jobMonitoring && importStatus && (
                <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4">
                  <h4 className="font-semibold mb-2 flex items-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-primary-600 border-t-transparent"></div>
                    {t('processingStatus')}
                  </h4>
                  <div className="grid grid-cols-4 gap-4 text-sm">
                    <div>
                      <div className="text-gray-600">{t('pending')}</div>
                      <div className="text-gray-800 font-bold">{importStatus.statistics?.pending || 0}</div>
                    </div>
                    <div>
                      <div className="text-emerald-600">{t('processing')}</div>
                      <div className="text-emerald-800 font-bold">
                        {(importStatus.statistics?.metadata_extracting || 0) + 
                         (importStatus.statistics?.chunking || 0) + 
                         (importStatus.statistics?.embedding || 0)}
                      </div>
                    </div>
                    <div>
                      <div className="text-green-600">{t('ready')}</div>
                      <div className="text-green-800 font-bold">{importStatus.statistics?.ready || 0}</div>
                    </div>
                    <div>
                      <div className="text-red-600">{t('failed')}</div>
                      <div className="text-red-800 font-bold">{importStatus.statistics?.failed || 0}</div>
                    </div>
                  </div>
                </div>
              )}

              {/* NEW: Metadata Table for Bulk Import (Browser Folder) */}
              {uploadSource === 'browser' && bulkFileMetadata.length > 0 && (
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <label className="block text-sm font-medium text-gray-700">
                      {t('fileMetadata')} {bulkFileMetadata.length > 1 && `(${t('editEachFileIndividually')})`}
                    </label>
                    {bulkFileMetadata.length > 1 && (
                      <div className="flex gap-2">
                        <select
                          key={bulkApplyProductKey}
                          onChange={(e) => {
                            if (e.target.value) {
                              setBulkFileMetadata(prev => prev.map(m => ({ ...m, product_category: e.target.value })));
                              setBulkApplyProductKey(prev => prev + 1);
                            }
                          }}
                          className="text-xs px-2 py-1 bg-emerald-100 text-emerald-700 rounded hover:bg-emerald-200 border border-emerald-300 focus:outline-none cursor-pointer"
                          defaultValue=""
                        >
                          <option value="">{t('applyProductToAll')}</option>
                          {productCategories.filter(cat => cat.value).map(category => (
                            <option key={category.value} value={category.value}>{category.label}</option>
                          ))}
                        </select>
                        <select
                          key={bulkApplyContentTypeKey}
                          onChange={(e) => {
                            if (e.target.value) {
                              setBulkFileMetadata(prev => prev.map(m => ({ ...m, content_type: e.target.value })));
                              setBulkApplyContentTypeKey(prev => prev + 1);
                            }
                          }}
                          className="text-xs px-2 py-1 bg-emerald-100 text-emerald-700 rounded hover:bg-emerald-200 border border-emerald-300 focus:outline-none cursor-pointer"
                          defaultValue=""
                        >
                          <option value="">Apply Content Type to All</option>
                          {contentTypes.filter(type => type.value).map(type => (
                            <option key={type.value} value={type.value}>{type.label}</option>
                          ))}
                        </select>
                      </div>
                    )}
                  </div>
                  
                  <div className="border border-gray-300 rounded-lg overflow-hidden">
                    <div className="overflow-x-auto max-h-[400px] overflow-y-auto">
                      <table className="w-full text-sm">
                        <thead className="bg-gray-50 sticky top-0">
                          <tr>
                            <th className="px-3 py-2 text-left font-medium text-gray-700 border-b">{t('filename')}</th>
                            <th className="px-3 py-2 text-left font-medium text-gray-700 border-b">{t('title')} *</th>
                            <th className="px-3 py-2 text-left font-medium text-gray-700 border-b">{t('description')}</th>
                            <th className="px-3 py-2 text-left font-medium text-gray-700 border-b">{t('product')}</th>
                            <th className="px-3 py-2 text-left font-medium text-gray-700 border-b">{t('contentType')}</th>
                            <th className="px-3 py-2 text-left font-medium text-gray-700 border-b">{t('version')}</th>
                            <th className="px-3 py-2 text-left font-medium text-gray-700 border-b">{t('size')}</th>
                          </tr>
                        </thead>
                        <tbody>
                          {bulkFileMetadata.map((meta, index) => (
                            <tr key={index} className="border-b hover:bg-gray-50">
                              <td className="px-3 py-2 text-gray-700">
                                <div className="max-w-xs truncate" title={meta.file.name}>
                                  {meta.file.name}
                                </div>
                              </td>
                              <td className="px-3 py-2">
                                <input
                                  type="text"
                                  value={meta.title}
                                  onChange={(e) => {
                                    const newMetadata = [...bulkFileMetadata];
                                    newMetadata[index].title = e.target.value;
                                    setBulkFileMetadata(newMetadata);
                                  }}
                                  className="w-full px-2 py-1 border border-gray-300 rounded text-xs focus:ring-1 focus:ring-primary-500"
                                  placeholder={t('enterTitle')}
                                />
                              </td>
                              <td className="px-3 py-2">
                                <input
                                  type="text"
                                  value={meta.description}
                                  onChange={(e) => {
                                    const newMetadata = [...bulkFileMetadata];
                                    newMetadata[index].description = e.target.value;
                                    setBulkFileMetadata(newMetadata);
                                  }}
                                  className="w-full px-2 py-1 border border-gray-300 rounded text-xs focus:ring-1 focus:ring-primary-500"
                                  placeholder={t('optional')}
                                />
                              </td>
                              <td className="px-3 py-2">
                                <select
                                  value={meta.product_category}
                                  onChange={(e) => {
                                    const newMetadata = [...bulkFileMetadata];
                                    newMetadata[index].product_category = e.target.value;
                                    setBulkFileMetadata(newMetadata);
                                  }}
                                  className="w-full px-2 py-1 border border-gray-300 rounded text-xs focus:ring-1 focus:ring-primary-500"
                                >
                                  {productCategories.map(cat => (
                                    <option key={cat.value} value={cat.value}>{cat.label}</option>
                                  ))}
                                </select>
                              </td>
                              <td className="px-3 py-2">
                                <select
                                  value={meta.content_type}
                                  onChange={(e) => {
                                    const newMetadata = [...bulkFileMetadata];
                                    newMetadata[index].content_type = e.target.value;
                                    setBulkFileMetadata(newMetadata);
                                  }}
                                  className="w-full px-2 py-1 border border-gray-300 rounded text-xs focus:ring-1 focus:ring-primary-500"
                                >
                                  {contentTypes.map(type => (
                                    <option key={type.value} value={type.value}>{type.label}</option>
                                  ))}
                                </select>
                              </td>
                              <td className="px-3 py-2">
                                <input
                                  type="text"
                                  value={meta.version}
                                  onChange={(e) => {
                                    const newMetadata = [...bulkFileMetadata];
                                    newMetadata[index].version = e.target.value;
                                    setBulkFileMetadata(newMetadata);
                                  }}
                                  className="w-full px-2 py-1 border border-gray-300 rounded text-xs focus:ring-1 focus:ring-primary-500"
                                  placeholder={t('versionExample')}
                                />
                              </td>
                              <td className="px-3 py-2 text-gray-600 text-xs">
                                {(meta.file.size / 1024 / 1024).toFixed(2)} MB
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {/* File List with Status Indicators (for server-side import) */}
              {uploadSource === 'server' && bulkFiles.length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Files ({bulkFiles.length})
                  </label>
                  <div className="border border-gray-300 rounded-lg max-h-60 overflow-y-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50 sticky top-0">
                        <tr>
                          <th className="px-3 py-2 text-left font-medium text-gray-700">{t('status')}</th>
                          <th className="px-3 py-2 text-left font-medium text-gray-700">{t('filename')}</th>
                          <th className="px-3 py-2 text-left font-medium text-gray-700">{t('size')}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {bulkFiles.map((file, idx) => {
                          // Find this file in importStatus if monitoring
                          const fileStatus = jobMonitoring && importStatus?.files 
                            ? importStatus.files.find((f: any) => f.filename === file.filename)
                            : null;
                          
                          const getStatusBadge = () => {
                            if (!fileStatus) {
                              return <span className="text-gray-500 text-xs">⏳ {t('pending')}</span>;
                            }
                            
                            const status = fileStatus.processing_status;
                            const isReady = fileStatus.is_ready;
                            
                            if (isReady) {
                              return <span className="text-green-600 text-xs">✓ {t('ready')}</span>;
                            }
                            if (status === 'failed') {
                              return <span className="text-red-600 text-xs">✗ {t('failed')}</span>;
                            }
                            if (status === 'metadata_extracting') {
                              return <span className="text-emerald-600 text-xs">📄 {t('metadata')}</span>;
                            }
                            if (status === 'chunking') {
                              return <span className="text-emerald-600 text-xs">✂️ {t('chunking')}</span>;
                            }
                            if (status === 'embedding') {
                              return <span className="text-emerald-600 text-xs">🔢 {t('embedding')}</span>;
                            }
                            return <span className="text-yellow-600 text-xs">⏳ {t('waiting')}</span>;
                          };
                          
                          return (
                            <tr key={idx} className="border-t border-gray-200">
                              <td className="px-3 py-2">{getStatusBadge()}</td>
                              <td className="px-3 py-2">{file.filename}</td>
                              <td className="px-3 py-2 text-gray-600">
                                {(file.size / 1024 / 1024).toFixed(2)} MB
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Show Filtered Out Files */}
              {uploadSource === 'browser' && filteredOutFiles.length > 0 && (
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-sm font-medium text-gray-700">
                      {t('filesFilteredOutTitle', { count: filteredOutFiles.length })}
                    </label>
                    <button
                      onClick={() => setFilteredOutFiles([])}
                      className="text-xs text-gray-500 hover:text-gray-700"
                    >
                      {t('hide')}
                    </button>
                  </div>
                  <div className="border border-orange-200 rounded-lg max-h-40 overflow-y-auto bg-orange-50">
                    <div className="p-2 space-y-1">
                      {filteredOutFiles.map((file, idx) => {
                        const ext = file.name.split('.').pop()?.toLowerCase() || '';
                        return (
                          <div key={idx} className="text-xs text-orange-700 flex items-center gap-2">
                            <span className="w-2 h-2 bg-orange-400 rounded-full"></span>
                            <span>{file.name}</span>
                            <span className="text-orange-500">(.{ext} not enabled)</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              )}

              {/* Enhanced Results with Error Reporting */}
              {bulkResults && (
                <div className="bg-gray-50 rounded-lg p-4 space-y-4">
                  <h4 className="font-semibold mb-2">{t('importResults')}</h4>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <div className="text-gray-600">{t('successful')}</div>
                      <div className="text-green-600 font-bold">{bulkResults.successful}</div>
                    </div>
                    <div>
                      <div className="text-gray-600">{t('failed')}</div>
                      <div className="text-red-600 font-bold">{bulkResults.failed}</div>
                    </div>
                    <div>
                      <div className="text-gray-600">{t('skipped')}</div>
                      <div className="text-yellow-600 font-bold">{bulkResults.skipped}</div>
                    </div>
                  </div>

                  {/* Show failed files with errors */}
                  {bulkResults.details && bulkResults.details.length > 0 && (
                    <div className="mt-4">
                      <h5 className="font-semibold text-sm mb-2">Failed Files:</h5>
                      <div className="space-y-2 max-h-40 overflow-y-auto">
                        {bulkResults.details
                          .filter((detail: any) => detail.status === 'failed')
                          .map((detail: any, idx: number) => (
                            <div key={idx} className="bg-red-50 border border-red-200 rounded p-2 text-xs">
                              <div className="font-medium text-red-900">{detail.filename}</div>
                              <div className="text-red-700 mt-1">{detail.error}</div>
                            </div>
                          ))}
                      </div>
                    </div>
                  )}

                  {/* Show skipped files */}
                  {bulkResults.details && bulkResults.details.length > 0 && (
                    <div className="mt-4">
                      <h5 className="font-semibold text-sm mb-2">Skipped Files (Duplicates):</h5>
                      <div className="space-y-2 max-h-40 overflow-y-auto">
                        {bulkResults.details
                          .filter((detail: any) => detail.status === 'skipped')
                          .map((detail: any, idx: number) => (
                            <div key={idx} className="bg-yellow-50 border border-yellow-200 rounded p-2 text-xs">
                              <div className="font-medium text-yellow-900">{detail.filename}</div>
                              <div className="text-yellow-700 mt-1">{detail.error}</div>
                              {detail.existing_file_id && (
                                <div className="text-yellow-600 mt-1">
                                  Already exists (ID: {detail.existing_file_id})
                                </div>
                              )}
                            </div>
                          ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              <div className="flex gap-3 pt-4">
                <button
                  onClick={() => {
                    // Stop monitoring if running
                    if (progressInterval) {
                      clearInterval(progressInterval);
                      setProgressInterval(null);
                    }
                    setJobMonitoring(false);
                    setShowBulkUploadModal(false);
                    // Reset state
                    setBulkFiles([]);
                    setBulkResults(null);
                    setImportStatus(null);
                    setSelectedFolder('');
                    setSelectedFiles([]);
                    setUploadSource('browser');
                    setFilteredOutFiles([]);
                    setBulkFileMetadata([]);
                    setEnabledFileTypes(new Set(['pdf', 'doc', 'docx', 'txt', 'xls', 'xlsx', 'ppt', 'pptx', 'html', 'mhtml']));
                  }}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  {t('close')}
                </button>
                {!jobMonitoring && (
                  <button
                    onClick={uploadSource === 'browser' ? handleBulkImportFromBrowser : handleBulkImport}
                    disabled={bulkProcessing || (uploadSource === 'browser' && bulkFileMetadata.length === 0 && selectedFiles.length === 0) || (uploadSource === 'server' && bulkFiles.length === 0)}
                    className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {bulkProcessing 
                      ? t('importingFiles', { count: uploadSource === 'browser' ? bulkFileMetadata.length : bulkFiles.length }) 
                      : t('importFiles', { count: uploadSource === 'browser' ? bulkFileMetadata.length : bulkFiles.length })}
                  </button>
                )}
                {jobMonitoring && (
                  <button
                    onClick={() => {
                      // Stop monitoring but keep modal open
                      if (progressInterval) {
                        clearInterval(progressInterval);
                        setProgressInterval(null);
                      }
                      setJobMonitoring(false);
                    }}
                    className="flex-1 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
                  >
                    {t('stopMonitoring')}
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* NEW: Background Upload Progress Panel */}
      {showUploadProgress && uploadQueue.length > 0 && (
        <div className="fixed bottom-4 right-4 bg-white rounded-lg shadow-2xl border border-gray-300 z-50 w-96 max-h-[600px] flex flex-col">
          <div className="flex justify-between items-center p-4 border-b bg-emerald-50">
            <div className="flex items-center gap-2">
              <div className={`animate-spin rounded-full h-4 w-4 border-2 border-primary-600 border-t-transparent ${!isUploading ? 'hidden' : ''}`}></div>
              <h3 className="font-semibold text-gray-900">
                {t('uploadProgress')} ({uploadQueue.filter(q => q.status === 'completed').length}/{uploadQueue.length})
              </h3>
            </div>
            <button
              onClick={() => {
                if (!isUploading) {
                  setShowUploadProgress(false);
                  setUploadQueue([]);
                }
              }}
              className="text-gray-400 hover:text-gray-600"
              disabled={isUploading}
            >
              <X size={18} />
            </button>
          </div>
          
          <div className="overflow-y-auto flex-1 p-4">
            <div className="space-y-2">
              {uploadQueue.map((item) => {
                const getStatusColor = () => {
                  switch (item.status) {
                    case 'queued': return 'text-gray-500';
                    case 'uploading': return 'text-emerald-600';
                    case 'processing': return 'text-yellow-600';
                    case 'completed': return 'text-green-600';
                    case 'failed': return 'text-red-600';
                    default: return 'text-gray-500';
                  }
                };

                const getStatusIcon = () => {
                  switch (item.status) {
                    case 'queued': return '⏳';
                    case 'uploading': return '⬆️';
                    case 'processing': return '⚙️';
                    case 'completed': return '✓';
                    case 'failed': return '✗';
                    default: return '⏳';
                  }
                };

                return (
                  <div
                    key={item.id}
                    className="border border-gray-200 rounded-lg p-3 hover:bg-gray-50"
                  >
                    <div className="flex items-start justify-between mb-1">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className={getStatusColor()}>{getStatusIcon()}</span>
                          <span className="text-sm font-medium text-gray-900 truncate" title={item.file.name}>
                            {item.file.name}
                          </span>
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          {(item.file.size / 1024 / 1024).toFixed(2)} MB
                        </div>
                      </div>
                      <span className={`text-xs font-medium ${getStatusColor()}`}>
                        {item.status === 'queued' ? t('queued') :
                         item.status === 'uploading' ? t('uploading') :
                         item.status === 'processing' ? t('processing') :
                         item.status === 'completed' ? t('completed') :
                         item.status === 'failed' ? t('failed') : item.status}
                      </span>
                    </div>
                    
                    {/* Progress bar */}
                    <div className="mt-2">
                      <div className="w-full bg-gray-200 rounded-full h-1.5">
                        <div
                          className={`h-1.5 rounded-full transition-all ${
                            item.status === 'completed' ? 'bg-green-500' :
                            item.status === 'failed' ? 'bg-red-500' :
                            item.status === 'processing' ? 'bg-yellow-500' :
                            'bg-emerald-500'
                          }`}
                          style={{ width: `${item.progress}%` }}
                        ></div>
                      </div>
                    </div>

                    {/* Error message */}
                    {item.error && (
                      <div className="mt-2 text-xs text-red-600 bg-red-50 p-2 rounded">
                        {item.error}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Summary */}
          <div className="border-t p-4 bg-gray-50">
            <div className="grid grid-cols-3 gap-2 text-xs">
              <div>
                <div className="text-gray-600">{t('queued')}</div>
                <div className="font-semibold text-gray-700">
                  {uploadQueue.filter(q => q.status === 'queued').length}
                </div>
              </div>
              <div>
                <div className="text-emerald-600">{t('inProgress')}</div>
                <div className="font-semibold text-emerald-700">
                  {uploadQueue.filter(q => q.status === 'uploading' || q.status === 'processing').length}
                </div>
              </div>
              <div>
                <div className="text-green-600">{t('completed')}</div>
                <div className="font-semibold text-green-700">
                  {uploadQueue.filter(q => q.status === 'completed').length}
                </div>
              </div>
            </div>
            {uploadQueue.some(q => q.status === 'failed') && (
              <div className="mt-2 text-xs text-red-600">
                {t('failed')}: {uploadQueue.filter(q => q.status === 'failed').length}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
});

DocumentManager.displayName = 'DocumentManager';

export default DocumentManager;
