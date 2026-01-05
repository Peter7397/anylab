import React, { useState, useEffect } from 'react';
import { Upload, FolderOpen, Globe, X, Play, Pause, Trash2, CheckCircle, AlertCircle, Clock, Eye, Info, RefreshCw, File, ChevronRight, ChevronLeft, Folder, ArrowUp } from 'lucide-react';
import { apiClient } from '../../services/api';
import { calculateFileHashes, isValidHash } from '../../utils/fileHash';

interface SourceFile {
  name: string;

  size?: number;




  type?: string;
  path?: string;
  is_temp?: boolean;
  upload_status?: 'pending' | 'uploading' | 'uploaded' | 'failed' | 'skipped';
  processing_status?: 'pending' | 'processing' | 'chunking' | 'embedding' | 'metadata_extracting' | 'ready' | 'failed' | 'no_text_available' | 'skipped';
  uploaded_file_id?: number;
  upload_error?: string;
  processing_error?: string;
  uploaded_at?: string;
  processed_at?: string;
  retry_count?: number;
  chunk_count?: number;
  embedding_count?: number;
}

interface FileStats {


  uploading: number;
  uploaded: number;
  upload_failed: number;
  pending_processing: number;
  processing: number;
  ready: number;
  processing_failed: number;
}

interface UploadJob {
  job_id: string;
  job_type: 'file' | 'folder' | 'webpage';
  status: string;
  total_items: number;
  completed_items: number;
  failed_items: number;
  progress_percentage: number;
  paused: boolean;
  cancelled: boolean;
  source_path: string;
  created_at: string;
  error_message?: string;
  file_errors?: Record<string, string>;
  source_files?: SourceFile[];
  file_stats?: FileStats;
  // Legacy support
  processing_stages?: any[];
}

const UnifiedUploadQueue: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'file' | 'folder' | 'webpage'>('file');
  const [jobs, setJobs] = useState<UploadJob[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [selectedFolderFiles, setSelectedFolderFiles] = useState<File[]>([]);
  const [selectedFolderName, setSelectedFolderName] = useState<string>('');
  const [webpageUrl, setWebpageUrl] = useState('');
  const [polling, setPolling] = useState(true);
  const [selectedJob, setSelectedJob] = useState<UploadJob | null>(null);
  const [jobDetail, setJobDetail] = useState<any>(null);
  const [queueStats, setQueueStats] = useState<any>(null);
  const [expandedJobs, setExpandedJobs] = useState<Set<string>>(new Set()); // Track expanded jobs for file list
  
  // Folder scan confirmation dialog state
  const [showFolderConfirmDialog, setShowFolderConfirmDialog] = useState(false);
  const [scannedFiles, setScannedFiles] = useState<any[]>([]);
  const [scannedFolderPath, setScannedFolderPath] = useState<string>('');
  const [scannedTotalSize, setScannedTotalSize] = useState<number>(0);
  
  // Webpage discovery state
  const [discoveryConfig, setDiscoveryConfig] = useState({
    maxDepth: 2,
    sameDomainOnly: true,
    fileTypeFilters: [] as string[],
    maxFileSizeMB: 20,
  });
  const [discoveryInProgress, setDiscoveryInProgress] = useState(false);
  const [discoveredFiles, setDiscoveredFiles] = useState<any[]>([]);
  const [selectedFileUrls, setSelectedFileUrls] = useState<Set<string>>(new Set());
  const [showDiscoveryProgress, setShowDiscoveryProgress] = useState(false);
  const [showFilePreview, setShowFilePreview] = useState(false);
  const [discoveryProgress, setDiscoveryProgress] = useState({
    pagesCrawled: 0,
    filesFound: 0,
    status: '',
  });
  
  // User-friendly improvements
  const [notification, setNotification] = useState<{type: 'success' | 'error' | 'info', message: string} | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>('active'); // 'active', 'all', 'queued', 'processing', 'completed', 'failed'
  const [showCompletedJobs, setShowCompletedJobs] = useState<boolean>(false); // Toggle to show/hide completed jobs
  const [sortBy, setSortBy] = useState<'date' | 'progress' | 'name'>('date');
  const [searchQuery, setSearchQuery] = useState('');
  
  // Hash calculation state
  const [hashCalculationProgress, setHashCalculationProgress] = useState<{
    inProgress: boolean;
    currentFile: number;
    totalFiles: number;
    currentFileProgress: number;
    canCancel: boolean;
  }>({
    inProgress: false,
    currentFile: 0,
    totalFiles: 0,
    currentFileProgress: 0,
    canCancel: false,
  });
  const [hashCalculationCancelled, setHashCalculationCancelled] = useState(false);
  
  // Helper function to show notifications
  const showNotification = (type: 'success' | 'error' | 'info', message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 5000);
  };
  
  // Format time ago
  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffSecs < 60) return 'just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    return date.toLocaleDateString();
  };
  
  // Format file size
  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'Unknown size';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
  };
  
  // Estimate time remaining
  const estimateTimeRemaining = (job: UploadJob) => {
    if (job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled') {
      return null;
    }
    
    const completed = job.completed_items || 0;
    const total = job.total_items || 1;
    const remaining = total - completed;
    
    if (completed === 0 || remaining === 0) return null;
    
    // Estimate based on average time per file (rough estimate: 30 seconds per file)
    const avgTimePerFile = 30; // seconds
    const estimatedSeconds = remaining * avgTimePerFile;
    
    if (estimatedSeconds < 60) return `~${estimatedSeconds}s remaining`;
    if (estimatedSeconds < 3600) return `~${Math.floor(estimatedSeconds / 60)}m remaining`;
    return `~${Math.floor(estimatedSeconds / 3600)}h remaining`;
  };

  const fetchQueue = async () => {
    try {
      // Request active jobs only by default (excludes completed jobs)
      const response = await apiClient.get('/ai/upload/queue/?active_only=true');
      const data = (response as any).data;
      
      // Response structure: { message, timestamp, stats: {...}, jobs: [...] }
      // The queue_data from get_queue_status is merged into the response
      let jobsList: UploadJob[] = [];
      if (data?.jobs && Array.isArray(data.jobs)) {
        jobsList = data.jobs;
      } else if (data?.data?.jobs) {
        jobsList = data.data.jobs;
      } else {
        console.warn('Unexpected queue response structure:', data);
      }
      
      // Apply filtering and sorting
      let filteredJobs = jobsList;
      
      // Apply status filter - Default to 'active' (exclude completed/cancelled)
      if (filterStatus === 'active') {
        // Show only active jobs: queued, uploading, processing, paused, failed (needs attention)
        filteredJobs = filteredJobs.filter(job => {
          const activeStatuses = ['queued', 'uploading', 'processing', 'paused', 'failed'];
          
          // If job status is in active statuses, include it
          if (activeStatuses.includes(job.status)) {
            return true;
          }
          
          // If job is marked completed but has failures, include it (needs attention)
          if (job.status === 'completed' && job.failed_items > 0) {
            return true;
          }
          
          // Check if all files are ready/completed/skipped - if so, exclude from active jobs
          if (job.source_files && job.source_files.length > 0) {
            const allFilesComplete = job.source_files.every((file: SourceFile) => {
              // File is skipped (duplicate) - not active
              const isSkipped = file.upload_status === 'skipped' || file.processing_status === 'skipped';
              if (isSkipped) {
                return true; // Skipped files are considered complete (no action needed)
              }
              
              // File is ready if it has processing_status === 'ready' or is completed
              const isReady = file.processing_status === 'ready' && file.uploaded_file_id;
              // Also check if file is uploaded and not pending processing
              const isUploaded = file.upload_status === 'uploaded' || file.uploaded_file_id;
              const isNotProcessing = !file.processing_status || 
                file.processing_status === 'ready' || 
                file.processing_status === 'failed' ||
                file.processing_status === 'no_text_available';
              
              // File is complete if: ready OR (uploaded and not processing and not pending)
              return isReady || (isUploaded && isNotProcessing && file.processing_status !== 'pending');
            });
            
            // If all files are complete (ready/skipped), exclude from active jobs
            if (allFilesComplete) {
              return false;
            }
          }
          
          // For jobs marked as completed, check if they really are (all files ready)
          if (job.status === 'completed') {
            // If no source_files info, trust the status
            if (!job.source_files || job.source_files.length === 0) {
              return false; // Exclude completed jobs without file info
            }
            
            // Check if all files are actually ready or skipped
            const allFilesComplete = job.source_files.every((file: SourceFile) => {
              // File is skipped (duplicate) - not active
              const isSkipped = file.upload_status === 'skipped' || file.processing_status === 'skipped';
              if (isSkipped) {
                return true; // Skipped files are considered complete
              }
              
              const isReady = file.processing_status === 'ready' && file.uploaded_file_id;
              const isUploaded = file.upload_status === 'uploaded' || file.uploaded_file_id;
              const isNotProcessing = !file.processing_status || 
                file.processing_status === 'ready' || 
                file.processing_status === 'failed';
              return isReady || (isUploaded && isNotProcessing && file.processing_status !== 'pending');
            });
            
            // Exclude if all files are complete (ready or skipped)
            return !allFilesComplete;
          }
          
          // Exclude other completed/cancelled jobs
          return false;
        });
      } else if (filterStatus !== 'all') {
        filteredJobs = filteredJobs.filter(job => {
          if (filterStatus === 'queued') return job.status === 'queued';
          if (filterStatus === 'processing') return job.status === 'processing' || job.status === 'uploading';
          if (filterStatus === 'completed') return job.status === 'completed';
          if (filterStatus === 'failed') return job.status === 'failed';
          return true;
        });
      }
      
      // Additional filter: Hide completed jobs if showCompletedJobs is false (even when filterStatus is 'all')
      if (!showCompletedJobs && filterStatus === 'all') {
        filteredJobs = filteredJobs.filter(job => {
          // Only hide fully completed jobs with no failures
          if (job.status === 'completed' && job.failed_items === 0) {
            return false;
          }
          return true;
        });
      }
      
      // Apply search query
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        filteredJobs = filteredJobs.filter(job => 
          job.source_path.toLowerCase().includes(query) ||
          job.job_id.toLowerCase().includes(query) ||
          job.source_files?.some((f: SourceFile) => f.name.toLowerCase().includes(query))
        );
      }
      
      // Apply sorting
      filteredJobs.sort((a, b) => {
        if (sortBy === 'date') {
          const dateA = new Date(a.created_at).getTime();
          const dateB = new Date(b.created_at).getTime();
          return dateB - dateA; // DESC order (newest first)
        } else if (sortBy === 'progress') {
          const progressA = a.progress_percentage || 0;
          const progressB = b.progress_percentage || 0;
          return progressB - progressA; // DESC order (most progress first)
        } else if (sortBy === 'name') {
          return a.source_path.localeCompare(b.source_path);
        }
        return 0;
      });
      
      setJobs(filteredJobs);
    } catch (error: any) {
      console.error('Error fetching queue:', error);
      if (error.response?.status === 401) {
        console.error('Authentication failed - user may need to log in again');
      }
    }
  };

  const fetchQueueStats = async () => {
    try {
      const response = await apiClient.getQueueStats();
      const data = (response as any).data;
      setQueueStats(data);
    } catch (error: any) {
      console.error('Error fetching queue stats:', error);
    }
  };

  // Poll for queue updates
  useEffect(() => {
    if (!polling) return;
    
    fetchQueue();
    fetchQueueStats();

    const interval = setInterval(() => {
      fetchQueue();
      fetchQueueStats();
    }, 3000); // Poll every 3 seconds
    return () => clearInterval(interval);
  }, [polling]);

  const handleRetryProcessing = async (uploadedFileId: number) => {
    try {
      await apiClient.retryFileProcessing(uploadedFileId);
      // Refresh queue after retry
      setTimeout(() => fetchQueue(), 1000);
    } catch (error: any) {
      console.error('Error retrying processing:', error);
      alert(error.response?.data?.error || error.message || 'Failed to retry processing');
    }
  };

  const handleDeleteFile = async (uploadedFileId: number, filename: string) => {
    if (!confirm(`Delete "${filename}"?\n\nThis will permanently delete:\n- The file record\n- All chunks and embeddings\n- The physical file\n\nThis action cannot be undone.`)) {
      return;
    }
    
    try {
      await apiClient.deleteUploadedFile(uploadedFileId);
      showNotification('success', 'File deleted successfully');
      // Refresh queue after deletion
      setTimeout(() => fetchQueue(), 1000);
    } catch (error: any) {
      console.error('Error deleting file:', error);
      showNotification('error', error.response?.data?.error || error.message || 'Failed to delete file');
    }
  };

  const handleRetryAllFailed = async () => {
    // Find all failed files in current jobs
    const failedFiles: Array<{fileId: number, filename: string}> = [];
    jobs.forEach(job => {
      // Check new source_files structure first
      if (job.source_files) {
        job.source_files.forEach((file: SourceFile) => {
          if ((file.processing_status === 'failed' || file.upload_status === 'failed') && file.uploaded_file_id) {
            failedFiles.push({
              fileId: file.uploaded_file_id,
              filename: file.name
            });
          }
        });
      }
      // Legacy support for processing_stages
      if (job.processing_stages) {
        job.processing_stages.forEach((stage: any) => {
          if (stage.processing_status === 'failed' && stage.uploaded_file_id) {
            failedFiles.push({
              fileId: stage.uploaded_file_id,
              filename: stage.filename
            });
          }
        });
      }
    });

    if (failedFiles.length === 0) {
      alert('No failed files found to retry');
      return;
    }

    if (!confirm(`Retry processing for ${failedFiles.length} failed file(s)?`)) {
      return;
    }

    try {
      let successCount = 0;
      let errorCount = 0;
      
      for (const file of failedFiles) {
        try {
          await apiClient.retryFileProcessing(file.fileId);
          successCount++;
        } catch (error: any) {
          console.error(`Error retrying file ${file.fileId}:`, error);
          errorCount++;
        }
      }

      if (successCount > 0) {
        showNotification('success', `Retry initiated for ${successCount} file(s). ${errorCount > 0 ? `${errorCount} file(s) failed to retry.` : ''}`);
      } else {
        showNotification('error', 'Failed to retry files. Please check the console for details.');
      }
      // Refresh queue after retry
      setTimeout(() => fetchQueue(), 1000);
    } catch (error: any) {
      console.error('Error retrying failed files:', error);
      showNotification('error', 'Failed to retry some files. Please check the console for details.');
    }
  };

  const handleRetryFileUpload = async (jobId: string, filename: string) => {
    try {
      // Retry by resuming the job (which will retry failed files)
      await apiClient.post(`/ai/upload/queue/${jobId}/resume/`);
      showNotification('success', 'Job resumed successfully');
      // Refresh queue after retry
      setTimeout(() => fetchQueue(), 1000);
    } catch (error: any) {
      console.error('Error retrying file upload:', error);
      showNotification('error', error.response?.data?.error || error.message || 'Failed to retry file upload');
    }
  };

  const handleRemoveFileFromJob = async (jobId: string, filename: string) => {
    if (!confirm(`Remove "${filename}" from this job? This will not delete the file if it was already uploaded.`)) {
      return;
    }
    
    try {
      // Get current job to update source_files
      const response = await apiClient.get(`/ai/upload/queue/${jobId}/`);
      const jobData = (response as any).data?.data;
      
      if (jobData && jobData.source_files) {
        // Remove file from source_files
        const updatedFiles = jobData.source_files.filter((f: any) => 
          f.name !== filename && f.filename !== filename && f.path !== filename
        );
        
        // Update job via API
        await apiClient.post(`/ai/upload/queue/${jobId}/update/`, {
          source_files: updatedFiles,
          total_items: updatedFiles.length
        });
        
        // Refresh queue
        setTimeout(() => fetchQueue(), 1000);
      }
    } catch (error: any) {
      console.error('Error removing file from job:', error);
      alert(error.response?.data?.error || error.message || 'Failed to remove file from job');
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setSelectedFiles(Array.from(e.target.files));
    }
  };

  const handleFolderSelectFromHost = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const files = Array.from(e.target.files);
      setSelectedFolderFiles(files);
      // Get folder name from the first file's path
      const firstFile = files[0];
      const path = (firstFile as any).webkitRelativePath || firstFile.name;
      const folderName = path.split('/')[0];
      setSelectedFolderName(folderName);
    }
  };

  const handleFileUpload = async () => {
    if (selectedFiles.length === 0) return;

    setLoading(true);
    setHashCalculationCancelled(false);
    
    try {
      // Step 1: Calculate hashes for all files
      setHashCalculationProgress({
        inProgress: true,
        currentFile: 0,
        totalFiles: selectedFiles.length,
        currentFileProgress: 0,
        canCancel: true,
      });

      const fileHashes = await calculateFileHashes(
        selectedFiles,
        (fileIndex, progress) => {
          // Update progress for individual file
          setHashCalculationProgress(prev => ({
            ...prev,
            currentFile: fileIndex + 1,
            currentFileProgress: progress,
          }));
        },
        (completed, total) => {
          // Update overall progress
          setHashCalculationProgress(prev => ({
            ...prev,
            currentFile: completed,
            totalFiles: total,
          }));
        },
        () => hashCalculationCancelled // Cancellation check
      );

      // Check if calculation was cancelled
      if (hashCalculationCancelled) {
        setLoading(false);
        setHashCalculationProgress({
          inProgress: false,
          currentFile: 0,
          totalFiles: 0,
          currentFileProgress: 0,
          canCancel: false,
        });
        return;
      }

      // Step 2: Prepare file metadata (no file content)
      const filesMetadata = fileHashes.map(({ file, hash }) => ({
        name: file.name,
        size: file.size,
        hash: hash,
        type: file.type || 'application/octet-stream',
      }));

      // Step 3: Send metadata to API (JSON, not FormData)
      const response = await apiClient.post('/ai/upload/queue/', {
        job_type: 'file',
        source: 'file_upload',
        files: filesMetadata,
      });

      const jobData = (response as any).data?.data || (response as any).data;
      const jobId = jobData.job_id;
      
      // Step 4: Upload file content for non-duplicate files (background, non-blocking)
      // OPTIMIZATION: Batch uploads (5-10 files per request) for 2-3x faster upload
      const BATCH_SIZE = 8; // Upload 8 files per batch request
      const batches: Array<Array<{file: File, hash: string}>> = [];
      
      // Group files into batches
      for (let i = 0; i < fileHashes.length; i += BATCH_SIZE) {
        batches.push(fileHashes.slice(i, i + BATCH_SIZE));
      }
      
      // Upload each batch
      const uploadPromises = batches.map(async (batch, batchIndex) => {
        try {
          const formData = new FormData();
          
          // Add all files in this batch to FormData
          batch.forEach(({ file }) => {
            formData.append('files[]', file); // Use 'files[]' for array format
          });
          
          // Upload batch to batch endpoint
          await apiClient.post(
            `/ai/upload/queue/${jobId}/upload-files/`,
            formData,
            {
              headers: { 'Content-Type': 'multipart/form-data' }
            }
          );
          
          console.debug(`Batch ${batchIndex + 1}/${batches.length} uploaded successfully (${batch.length} files)`);
        } catch (error: any) {
          console.error(`Error uploading batch ${batchIndex + 1}:`, error);
          // If batch fails, fall back to individual uploads for this batch
          const fallbackPromises = batch.map(async ({ file }) => {
            try {
              const fallbackFormData = new FormData();
              fallbackFormData.append('file', file);
              await apiClient.post(
                `/ai/upload/queue/${jobId}/upload-file/?filename=${encodeURIComponent(file.name)}`,
                fallbackFormData,
                { headers: { 'Content-Type': 'multipart/form-data' } }
              );
            } catch (fallbackError: any) {
              console.error(`Error uploading file ${file.name} (fallback):`, fallbackError);
            }
          });
          await Promise.all(fallbackPromises);
        }
      });
      
      // Start batch uploads in background (don't await - non-blocking)
      Promise.all(uploadPromises).catch(err => {
        console.error('Error uploading file batches:', err);
        // Background upload failed, but job is created - processing task will handle
      });
      
      setSelectedFiles([]);
      setLoading(false);
      setHashCalculationProgress({
        inProgress: false,
        currentFile: 0,
        totalFiles: 0,
        currentFileProgress: 0,
        canCancel: false,
      });
      
      // Job queued immediately - user can continue adding more jobs
      const newFiles = jobData.new_files || selectedFiles.length;
      const duplicates = jobData.duplicates || 0;
      showNotification('success', 
        `Job queued successfully! ${newFiles} new file(s), ${duplicates} duplicate(s) skipped. ` +
        `Files will be processed in the background. You can continue adding more jobs.`
      );
      
      // Auto-refresh queue after a short delay (job may take a few seconds to appear in PostgreSQL)
      setTimeout(() => fetchQueue(), 2000);
    } catch (error: any) {
      console.error('Upload error:', error);
      
      // Check if it's a hash calculation error
      if (error.message && error.message.includes('hash')) {
        showNotification('error', `Hash calculation failed: ${error.message}. Please try again.`);
      } else {
        showNotification('error', error.response?.data?.message || 'Upload failed. Please try again.');
      }
      
      setLoading(false);
      setHashCalculationProgress({
        inProgress: false,
        currentFile: 0,
        totalFiles: 0,
        currentFileProgress: 0,
        canCancel: false,
      });
    }
  };

  const handleCancelHashCalculation = () => {
    setHashCalculationCancelled(true);
    setHashCalculationProgress({
      inProgress: false,
      currentFile: 0,
      totalFiles: 0,
      currentFileProgress: 0,
      canCancel: false,
    });
    setLoading(false);
    showNotification('info', 'Hash calculation cancelled');
  };

  const handleFolderScan = async () => {
    // Only support client-side folder picker (browser/host machine)
    if (selectedFolderFiles.length === 0) {
      showNotification('info', 'Please select a folder from your computer first');
      return;
    }

    // Show confirmation dialog with file list
    setScannedFiles(selectedFolderFiles.map((file, idx) => ({
      name: file.name,
      size: file.size,
      type: file.type,
      index: idx
    })));
    setScannedTotalSize(selectedFolderFiles.reduce((sum, f) => sum + f.size, 0));
    setScannedFolderPath(selectedFolderName || 'Selected Folder');
    setShowFolderConfirmDialog(true);
  };

  const handleConfirmFolderUpload = async () => {
    setLoading(true);
    setHashCalculationCancelled(false);
    setShowFolderConfirmDialog(false);
    
    try {
      // Only support client-side folder picker (browser/host machine)
      if (selectedFolderFiles.length === 0) {
        showNotification('info', 'No files selected');
        setLoading(false);
        return;
      }

      // Step 1: Calculate hashes for all files (same as file upload)
      setHashCalculationProgress({
        inProgress: true,
        currentFile: 0,
        totalFiles: selectedFolderFiles.length,
        currentFileProgress: 0,
        canCancel: true,
      });

      const fileHashes = await calculateFileHashes(
        selectedFolderFiles,
        (fileIndex, progress) => {
          setHashCalculationProgress(prev => ({
            ...prev,
            currentFile: fileIndex + 1,
            currentFileProgress: progress,
          }));
        },
        (completed, total) => {
          setHashCalculationProgress(prev => ({
            ...prev,
            currentFile: completed,
            totalFiles: total,
          }));
        },
        () => hashCalculationCancelled
      );

      // Check if calculation was cancelled
      if (hashCalculationCancelled) {
        setLoading(false);
        setHashCalculationProgress({
          inProgress: false,
          currentFile: 0,
          totalFiles: 0,
          currentFileProgress: 0,
          canCancel: false,
        });
        return;
      }

      // Step 2: Prepare file metadata (no file content)
      const filesMetadata = fileHashes.map(({ file, hash }) => ({
        name: file.name,
        size: file.size,
        hash: hash,
        type: file.type || 'application/octet-stream',
      }));

      // Step 3: Send metadata to API (JSON, not FormData)
      const response = await apiClient.post('/ai/upload/queue/', {
        job_type: 'file',
        source: 'folder_upload',
        files: filesMetadata,
      });

      const jobData = (response as any).data?.data || (response as any).data;
      const jobId = jobData.job_id;
      
      // Step 4: Upload file content for non-duplicate files (background, non-blocking)
      // OPTIMIZATION: Batch uploads (5-10 files per request) for 2-3x faster upload
      const BATCH_SIZE = 8; // Upload 8 files per batch request
      const batches: Array<Array<{file: File, hash: string}>> = [];
      
      // Group files into batches
      for (let i = 0; i < fileHashes.length; i += BATCH_SIZE) {
        batches.push(fileHashes.slice(i, i + BATCH_SIZE));
      }
      
      // Upload each batch
      const uploadPromises = batches.map(async (batch, batchIndex) => {
        try {
          const formData = new FormData();
          
          // Add all files in this batch to FormData
          batch.forEach(({ file }) => {
            formData.append('files[]', file); // Use 'files[]' for array format
          });
          
          // Upload batch to batch endpoint
          await apiClient.post(
            `/ai/upload/queue/${jobId}/upload-files/`,
            formData,
            {
              headers: { 'Content-Type': 'multipart/form-data' }
            }
          );
          
          console.debug(`Batch ${batchIndex + 1}/${batches.length} uploaded successfully (${batch.length} files)`);
        } catch (error: any) {
          console.error(`Error uploading batch ${batchIndex + 1}:`, error);
          // If batch fails, fall back to individual uploads for this batch
          const fallbackPromises = batch.map(async ({ file }) => {
            try {
              const fallbackFormData = new FormData();
              fallbackFormData.append('file', file);
              await apiClient.post(
                `/ai/upload/queue/${jobId}/upload-file/?filename=${encodeURIComponent(file.name)}`,
                fallbackFormData,
                { headers: { 'Content-Type': 'multipart/form-data' } }
              );
            } catch (fallbackError: any) {
              console.error(`Error uploading file ${file.name} (fallback):`, fallbackError);
            }
          });
          await Promise.all(fallbackPromises);
        }
      });
      
      // Start batch uploads in background (don't await - non-blocking)
      Promise.all(uploadPromises).catch(err => {
        console.error('Error uploading file batches:', err);
      });
      
      setSelectedFolderFiles([]);
      setSelectedFolderName('');
      setScannedFiles([]);
      setScannedFolderPath('');
      setScannedTotalSize(0);
      setLoading(false);
      setHashCalculationProgress({
        inProgress: false,
        currentFile: 0,
        totalFiles: 0,
        currentFileProgress: 0,
        canCancel: false,
      });
      
      // Job queued immediately - user can continue adding more jobs
      const newFiles = jobData.new_files || selectedFolderFiles.length;
      const duplicates = jobData.duplicates || 0;
      showNotification('success', 
        `Job queued successfully! ${newFiles} new file(s), ${duplicates} duplicate(s) skipped. ` +
        `Files will be processed in the background. You can continue adding more folders.`
      );
      
      // Refresh queue after a short delay
      setTimeout(() => fetchQueue(), 2000);
    } catch (error: any) {
      console.error('Folder upload error:', error);
      
      // Check if it's a hash calculation error
      if (error.message && error.message.includes('hash')) {
        showNotification('error', `Hash calculation failed: ${error.message}. Please try again.`);
      } else {
        showNotification('error', error.response?.data?.message || 'Folder upload failed');
      }
      
      setLoading(false);
      setHashCalculationProgress({
        inProgress: false,
        currentFile: 0,
        totalFiles: 0,
        currentFileProgress: 0,
        canCancel: false,
      });
    }
  };

  const handleCancelFolderUpload = () => {
    setShowFolderConfirmDialog(false);
    setScannedFiles([]);
    setScannedFolderPath('');
    setScannedTotalSize(0);
    // Don't clear selectedFolderFiles - user might want to try again
  };


  const handleWebpageDownload = async () => {
    if (!webpageUrl.trim()) {
      alert('Please enter a webpage URL');
      return;
    }

    // Start discovery process
    setDiscoveryInProgress(true);
    setShowDiscoveryProgress(true);
    setDiscoveryProgress({ pagesCrawled: 0, filesFound: 0, status: 'Starting discovery...' });

    try {
      const result = await apiClient.discoverWebpageFiles({
        url: webpageUrl,
        max_depth: discoveryConfig.maxDepth,
        same_domain_only: discoveryConfig.sameDomainOnly,
        file_type_filters: discoveryConfig.fileTypeFilters,
        max_file_size_mb: discoveryConfig.maxFileSizeMB,
      });

      setDiscoveredFiles(result.discovered_files || []);
      setDiscoveryProgress({
        pagesCrawled: result.total_pages_crawled || 0,
        filesFound: result.total_files_after_filter || 0,
        status: 'Discovery completed',
      });
      
      setShowDiscoveryProgress(false);
      setShowFilePreview(true);
      setDiscoveryInProgress(false);
      showNotification('success', `Found ${result.total_files_after_filter || 0} file(s) from ${result.total_pages_crawled || 0} page(s)`);
    } catch (error: any) {
      console.error('Webpage discovery error:', error);
      showNotification('error', error.response?.data?.message || error.message || 'Webpage discovery failed');
      setDiscoveryInProgress(false);
      setShowDiscoveryProgress(false);
    }
  };

  const handleQueueSelectedFiles = async () => {
    if (selectedFileUrls.size === 0) {
      showNotification('error', 'Please select at least one file to queue');
      return;
    }

    const filesToQueue = discoveredFiles.filter(f => selectedFileUrls.has(f.url));
    
    setLoading(true);
    try {
      await apiClient.queueWebpageFiles(filesToQueue, webpageUrl);
      
      setWebpageUrl('');
      setDiscoveredFiles([]);
      setSelectedFileUrls(new Set());
      setShowFilePreview(false);
      setLoading(false);
      
      showNotification('success', `Successfully queued ${filesToQueue.length} file(s) from webpage`);
      // Refresh queue
      fetchQueue();
    } catch (error: any) {
      console.error('Queue files error:', error);
      showNotification('error', error.response?.data?.message || error.message || 'Failed to queue files');
      setLoading(false);
    }
  };

  const handlePause = async (jobId: string) => {
    try {
      await apiClient.post(`/ai/upload/queue/${jobId}/pause/`);
      showNotification('info', 'Job paused successfully');
      // Refresh queue after pause
      setTimeout(() => fetchQueue(), 500);
    } catch (error: any) {
      console.error('Pause error:', error);
      showNotification('error', error.response?.data?.error || error.message || 'Failed to pause job');
    }
  };

  const handleResume = async (jobId: string) => {
    try {
      await apiClient.post(`/ai/upload/queue/${jobId}/resume/`);
      showNotification('success', 'Job resumed successfully');
      // Refresh queue after resume
      setTimeout(() => fetchQueue(), 500);
    } catch (error: any) {
      console.error('Resume error:', error);
      showNotification('error', error.response?.data?.error || error.message || 'Failed to resume job');
    }
  };

  // Cancel removed - use handleDeleteJob instead

  const handleRetryJob = async (jobId: string) => {
    if (!confirm('Retry this job? This will reset the job status and attempt to process it again.')) return;
    
    try {
      await apiClient.post(`/ai/upload/queue/${jobId}/retry/`);
      showNotification('success', 'Job retried successfully');
      // Refresh queue after retry
      setTimeout(() => fetchQueue(), 500);
    } catch (error: any) {
      console.error('Retry error:', error);
      showNotification('error', error.response?.data?.error || error.message || 'Failed to retry job');
    }
  };

  const handleDeleteJob = async (jobId: string) => {
    if (!confirm(
      '⚠️ PERMANENT DELETE ⚠️\n\n' +
      'This will permanently delete:\n' +
      '• The upload job\n' +
      '• All uploaded files\n' +
      '• All chunks and embeddings\n' +
      '• All document records\n' +
      '• Physical files\n\n' +
      'This action CANNOT be undone!\n\n' +
      'After deletion, you can upload the same files again.\n\n' +
      'Are you absolutely sure?'
    )) return;
    
    try {
      // Use DELETE method to permanently delete the job and all data
      const response = await apiClient.delete(`/ai/upload/queue/${jobId}/delete/`);
      const data = (response as any).data?.data || (response as any).data;
      
      const message = data?.deleted_files 
        ? `Job deleted successfully. Removed ${data.deleted_files} file(s), ${data.deleted_chunks || 0} chunk(s), ${data.deleted_document_files || 0} document record(s).`
        : 'Job and all associated data deleted successfully.';
      
      showNotification('success', message);
      // Refresh queue after delete
      setTimeout(() => fetchQueue(), 500);
    } catch (error: any) {
      console.error('Delete job error:', error);
      showNotification('error', error.response?.data?.error || error.message || 'Failed to delete job');
    }
  };

  const handleViewDetails = async (job: UploadJob) => {
    setSelectedJob(job);
    try {
      const response = await apiClient.get(`/ai/upload/queue/${job.job_id}/`);
      const data = (response as any).data;
      if (data?.data) {
        setJobDetail(data.data);
      }
    } catch (error) {
      console.error('Error fetching job details:', error);
    }
  };

  const getStatusDisplay = (job: UploadJob) => {
    // More accurate status display - check if files are still processing
    if (job.cancelled) {
      return { text: 'Cancelled', color: 'bg-gray-100 text-gray-600', icon: <X className="w-4 h-4 text-gray-500" /> };
    }
    
    // Check if job is "completed" but files are still processing
    let hasProcessingFiles = false;
    let processingCount = 0;
    
    if (job.source_files) {
      // Only count files that are actually processing, not those that are ready/completed
      hasProcessingFiles = job.source_files.some(
        (file: SourceFile) => file.uploaded_file_id && file.processing_status && 
        ['pending', 'processing', 'metadata_extracting', 'chunking', 'embedding'].includes(file.processing_status) &&
        file.processing_status !== 'ready'
      );
      processingCount = job.source_files.filter(
        (file: SourceFile) => file.uploaded_file_id && file.processing_status && 
        ['pending', 'processing', 'metadata_extracting', 'chunking', 'embedding'].includes(file.processing_status) &&
        file.processing_status !== 'ready'
      ).length;
    } else if (job.processing_stages) {
      // Legacy support
      hasProcessingFiles = job.processing_stages.some(
        (stage: any) => stage.processing_status && 
        ['pending', 'metadata_extracting', 'chunking', 'embedding'].includes(stage.processing_status)
      );
      processingCount = job.processing_stages.filter(
        (s: any) => s.processing_status && ['pending', 'metadata_extracting', 'chunking', 'embedding'].includes(s.processing_status)
      ).length;
    }
    
    if (job.status === 'completed' || job.status === 'partially_completed') {
      // If files are still processing, show "Processing Files" instead of "Completed"
      if (hasProcessingFiles) {
        return { 
          text: `Processing Files (${processingCount} remaining)`, 
          color: 'bg-blue-100 text-blue-700', 
          icon: <Clock className="w-4 h-4 text-blue-500 animate-pulse" /> 
        };
      }
      
      if (job.status === 'partially_completed') {
        return { 
          text: 'Partially Completed', 
          color: 'bg-yellow-100 text-yellow-700', 
          icon: <AlertCircle className="w-4 h-4 text-yellow-500" /> 
        };
      }
      
      if (job.failed_items > 0 && job.completed_items > 0) {
        return { text: `Completed (${job.completed_items} success, ${job.failed_items} failed)`, color: 'bg-yellow-100 text-yellow-700', icon: <AlertCircle className="w-4 h-4 text-yellow-500" /> };
      } else if (job.failed_items > 0) {
        return { text: 'Failed', color: 'bg-red-100 text-red-700', icon: <AlertCircle className="w-4 h-4 text-red-500" /> };
      } else {
        return { text: 'Completed', color: 'bg-green-100 text-green-700', icon: <CheckCircle className="w-4 h-4 text-green-500" /> };
      }
    }
    if (job.status === 'failed') {
      return { text: 'Failed', color: 'bg-red-100 text-red-700', icon: <AlertCircle className="w-4 h-4 text-red-500" /> };
    }
    if (job.paused) {
      return { text: 'Paused', color: 'bg-yellow-100 text-yellow-700', icon: <Pause className="w-4 h-4 text-yellow-500" /> };
    }
    if (job.status === 'processing') {
      return { text: 'Processing...', color: 'bg-blue-100 text-blue-700', icon: <Clock className="w-4 h-4 text-blue-500 animate-pulse" /> };
    }
    if (job.status === 'uploading') {
      return { text: 'Uploading...', color: 'bg-blue-100 text-blue-700', icon: <Upload className="w-4 h-4 text-blue-500 animate-pulse" /> };
    }
    // Default: queued
    return { text: 'Queued', color: 'bg-gray-100 text-gray-700', icon: <Clock className="w-4 h-4 text-gray-500" /> };
  };

  const getStatusIcon = (job: UploadJob) => {
    return getStatusDisplay(job).icon;
  };

  const getStatusColor = (job: UploadJob) => {
    return getStatusDisplay(job).color;
  };

  // Filtered and sorted jobs (already applied in fetchQueue)
  const filteredJobs = jobs; // Jobs are already filtered in fetchQueue
  
  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Notification Toast */}
      {notification && (
        <div className={`fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg flex items-center gap-3 animate-in slide-in-from-top-5 ${
          notification.type === 'success' ? 'bg-green-50 border border-green-200 text-green-800' :
          notification.type === 'error' ? 'bg-red-50 border border-red-200 text-red-800' :
          'bg-blue-50 border border-blue-200 text-blue-800'
        }`}>
          {notification.type === 'success' && <CheckCircle className="w-5 h-5" />}
          {notification.type === 'error' && <AlertCircle className="w-5 h-5" />}
          {notification.type === 'info' && <Info className="w-5 h-5" />}
          <span className="font-medium">{notification.message}</span>
          <button
            onClick={() => setNotification(null)}
            className="ml-2 hover:opacity-70"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}
      
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Upload Queue</h1>
          <p className="text-sm text-gray-600 mt-1">
            Manage your file uploads and track processing status
          </p>
        </div>
      </div>

      {/* Processing Health Dashboard */}
      {queueStats && (
        <div className="bg-white rounded-lg shadow mb-6 p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Info className="w-5 h-5 text-blue-600" />
            Processing Health Status
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* File Processing Status */}
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-600 mb-1">File Processing</div>
              <div className="text-2xl font-bold text-gray-900">{queueStats.file_processing?.ready || 0}</div>
              <div className="text-xs text-gray-500">of {queueStats.file_processing?.total_files || 0} ready</div>
              <div className="mt-2">
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-green-600 h-2 rounded-full transition-all"
                    style={{ width: `${queueStats.file_processing?.ready_percentage || 0}%` }}
                  />
                </div>
                <div className="text-xs text-gray-600 mt-1">{queueStats.file_processing?.ready_percentage || 0}% ready</div>
              </div>
            </div>

            {/* Pending Files */}
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-600 mb-1">Process Pending</div>
              <div className="text-2xl font-bold text-yellow-600">{queueStats.file_processing?.pending || 0}</div>
              <div className="text-xs text-gray-500">
                {queueStats.file_processing?.stuck_pending || 0} stuck (&gt;5min)
              </div>
              {queueStats.file_processing?.processing > 0 && (
                <div className="text-xs text-blue-600 mt-1">
                  {queueStats.file_processing.processing} currently processing
                </div>
              )}
            </div>

            {/* Embedding Status */}
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-600 mb-1">Embeddings</div>
              <div className="text-2xl font-bold text-green-600">
                {queueStats.embedding_status?.embedding_completion_percentage || 0}%
              </div>
              <div className="text-xs text-gray-500">
                {queueStats.embedding_status?.chunks_with_embeddings || 0} / {queueStats.embedding_status?.total_chunks || 0} chunks
              </div>
              {queueStats.embedding_status?.chunks_without_embeddings > 0 && (
                <div className="text-xs text-red-600 mt-1">
                  {queueStats.embedding_status.chunks_without_embeddings} without embeddings
                </div>
              )}
            </div>

            {/* System Resources */}
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-600 mb-1">System Resources</div>
              <div className="text-xs text-gray-500 mb-2">
                CPU: {queueStats.system_resources?.cpu_percent?.toFixed(1) || 0}% | 
                Memory: {queueStats.system_resources?.memory_percent?.toFixed(1) || 0}%
              </div>
              <div className={`text-xs px-2 py-1 rounded ${
                queueStats.system_resources?.resources_ok 
                  ? 'bg-green-100 text-green-700' 
                  : 'bg-yellow-100 text-yellow-700'
              }`}>
                {queueStats.system_resources?.resources_ok ? '✓ Healthy' : '⚠ High Usage'}
              </div>
            </div>
          </div>

          {/* Stuck Jobs Alert */}
          {(queueStats.stuck_jobs?.warning_count > 0 || queueStats.stuck_jobs?.critical_count > 0) && (
            <div className={`mt-4 p-4 rounded-lg ${
              queueStats.stuck_jobs.critical_count > 0 
                ? 'bg-red-50 border border-red-200' 
                : 'bg-yellow-50 border border-yellow-200'
            }`}>
              <div className="flex items-center gap-2 mb-2">
                <AlertCircle className={`w-5 h-5 ${
                  queueStats.stuck_jobs.critical_count > 0 ? 'text-red-600' : 'text-yellow-600'
                }`} />
                <h3 className={`font-semibold ${
                  queueStats.stuck_jobs.critical_count > 0 ? 'text-red-800' : 'text-yellow-800'
                }`}>
                  {queueStats.stuck_jobs.critical_count > 0 ? 'Critical: Stuck Jobs Detected' : 'Warning: Jobs Taking Longer Than Expected'}
                </h3>
              </div>
              {queueStats.stuck_jobs.critical_count > 0 && (
                <div className="text-sm text-red-700 mb-2">
                  {queueStats.stuck_jobs.critical_count} job(s) queued for over 2 hours
                </div>
              )}
              {queueStats.stuck_jobs.warning_count > 0 && (
                <div className="text-sm text-yellow-700 mb-2">
                  {queueStats.stuck_jobs.warning_count} job(s) queued for over 30 minutes
                </div>
              )}
              {queueStats.stuck_jobs.critical_jobs && queueStats.stuck_jobs.critical_jobs.length > 0 && (
                <div className="mt-2 text-xs">
                  <div className="font-medium text-red-800 mb-1">Critical Jobs:</div>
                  {queueStats.stuck_jobs.critical_jobs.map((job: any, idx: number) => (
                    <div key={idx} className="text-red-700 mb-1">
                      • {job.job_type}: {job.age_hours}h old - {job.source_path}
                    </div>
                  ))}
                </div>
              )}
              {queueStats.stuck_jobs.warning_jobs && queueStats.stuck_jobs.warning_jobs.length > 0 && (
                <div className="mt-2 text-xs">
                  <div className="font-medium text-yellow-800 mb-1">Warning Jobs:</div>
                  {queueStats.stuck_jobs.warning_jobs.map((job: any, idx: number) => (
                    <div key={idx} className="text-yellow-700 mb-1">
                      • {job.job_type}: {job.age_minutes}min old - {job.source_path}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Upload Tabs */}
      <div className="bg-white rounded-lg shadow mb-6">
        <div className="border-b border-gray-200">
          <nav className="flex -mb-px">
            {(['file', 'folder', 'webpage'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-6 py-3 text-sm font-medium border-b-2 ${
                  activeTab === tab
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab === 'file' && <><Upload className="w-4 h-4 inline mr-2" />Files</>}
                {tab === 'folder' && <><FolderOpen className="w-4 h-4 inline mr-2" />Folder</>}
                {tab === 'webpage' && <><Globe className="w-4 h-4 inline mr-2" />Webpage</>}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {/* File Upload */}
          {activeTab === 'file' && (
            <div>
              <input
                type="file"
                multiple
                onChange={handleFileSelect}
                className="mb-4 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              />
              {selectedFiles.length > 0 && (
                <div className="mb-4 text-sm text-gray-600">
                  {selectedFiles.length} file(s) selected
                </div>
              )}
              {/* Hash Calculation Progress */}
              {hashCalculationProgress.inProgress && (
                <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <RefreshCw className="w-4 h-4 text-blue-600 animate-spin" />
                      <span className="text-sm font-medium text-blue-800">
                        Calculating hash... {hashCalculationProgress.currentFile}/{hashCalculationProgress.totalFiles} files
                      </span>
                    </div>
                    {hashCalculationProgress.canCancel && (
                      <button
                        onClick={handleCancelHashCalculation}
                        className="text-xs text-blue-600 hover:text-blue-800 underline"
                      >
                        Cancel
                      </button>
                    )}
                  </div>
                  <div className="w-full bg-blue-200 rounded-full h-2 mb-1">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{
                        width: `${(hashCalculationProgress.currentFile / hashCalculationProgress.totalFiles) * 100}%`
                      }}
                    />
                  </div>
                  {hashCalculationProgress.currentFile > 0 && (
                    <div className="text-xs text-blue-600">
                      File {hashCalculationProgress.currentFile}: {hashCalculationProgress.currentFileProgress}%
                    </div>
                  )}
                </div>
              )}
              
              <button
                onClick={handleFileUpload}
                disabled={loading || selectedFiles.length === 0 || hashCalculationProgress.inProgress}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {hashCalculationProgress.inProgress 
                  ? `Calculating hash... ${hashCalculationProgress.currentFile}/${hashCalculationProgress.totalFiles}`
                  : loading 
                    ? 'Submitting...' 
                    : 'Submit'}
              </button>
            </div>
          )}

          {/* Folder Upload */}
          {activeTab === 'folder' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Folder from Your Computer
                </label>
                <input
                  type="file"
                  {...({ webkitdirectory: '' } as any)}
                  multiple
                  onChange={handleFolderSelectFromHost}
                  className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                />
                <p className="mt-2 text-xs text-gray-500">
                  Select a folder from your local computer. All supported files in the folder will be uploaded.
                </p>
              </div>

              {selectedFolderFiles.length > 0 && (
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <div className="text-sm font-medium text-blue-900 mb-1">
                        <FolderOpen className="w-4 h-4 inline mr-1" />
                        {selectedFolderName}
                      </div>
                      <div className="text-xs text-blue-700">
                        {selectedFolderFiles.length} file(s) ready to upload
                      </div>
                    </div>
                    <button
                      onClick={() => {
                        setSelectedFolderFiles([]);
                        setSelectedFolderName('');
                      }}
                      className="text-blue-600 hover:text-blue-800"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                  <button
                    onClick={handleFolderScan}
                    disabled={loading}
                    className="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
                  >
                    {loading ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        Scanning...
                      </>
                    ) : (
                      <>
                        <FolderOpen className="w-4 h-4" />
                        Scan Folder
                      </>
                    )}
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Webpage Download */}
          {activeTab === 'webpage' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Webpage URL
                </label>
                <input
                  type="url"
                  value={webpageUrl}
                  onChange={(e) => setWebpageUrl(e.target.value)}
                  placeholder="https://example.com/page"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Crawl Depth (0-5)
                  </label>
                  <select
                    value={discoveryConfig.maxDepth}
                    onChange={(e) => setDiscoveryConfig({ ...discoveryConfig, maxDepth: parseInt(e.target.value) })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    {[0, 1, 2, 3, 4, 5].map(d => (
                      <option key={d} value={d}>{d} {d === 0 ? '(current page only)' : d === 1 ? 'level' : 'levels'}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Max File Size (MB)
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={discoveryConfig.maxFileSizeMB}
                    onChange={(e) => setDiscoveryConfig({ ...discoveryConfig, maxFileSizeMB: parseInt(e.target.value) || 0 })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="sameDomainOnly"
                  checked={discoveryConfig.sameDomainOnly}
                  onChange={(e) => setDiscoveryConfig({ ...discoveryConfig, sameDomainOnly: e.target.checked })}
                  className="mr-2"
                />
                <label htmlFor="sameDomainOnly" className="text-sm text-gray-700">
                  Same domain only
                </label>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  File Type Filters (leave empty for all types)
                </label>
                <div className="flex flex-wrap gap-2">
                  {['pdf', 'doc', 'xls', 'ppt', 'txt', 'csv', 'zip', 'image'].map(type => (
                    <label key={type} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={discoveryConfig.fileTypeFilters.includes(type)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setDiscoveryConfig({
                              ...discoveryConfig,
                              fileTypeFilters: [...discoveryConfig.fileTypeFilters, type]
                            });
                          } else {
                            setDiscoveryConfig({
                              ...discoveryConfig,
                              fileTypeFilters: discoveryConfig.fileTypeFilters.filter(t => t !== type)
                            });
                          }
                        }}
                        className="mr-1"
                      />
                      <span className="text-sm text-gray-700">{type.toUpperCase()}</span>
                    </label>
                  ))}
                </div>
              </div>

              <button
                onClick={handleWebpageDownload}
                disabled={discoveryInProgress || !webpageUrl.trim()}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {discoveryInProgress ? 'Discovering Files...' : 'Discover Files from Webpage'}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Queue List */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-4 border-b border-gray-200">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-4">
            <h2 className="text-lg font-semibold">Active Jobs ({filteredJobs.length})</h2>
            
            {/* Filters and Search */}
            <div className="flex flex-wrap gap-2 items-center">
              {/* Search */}
              <input
                type="text"
                placeholder="Search jobs..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              
              {/* Status Filter */}
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="active">Active Jobs</option>
                <option value="all">All Jobs</option>
                <option value="queued">Queued</option>
                <option value="processing">Processing</option>
                <option value="completed">Completed</option>
                <option value="failed">Failed</option>
              </select>
              
              {/* Sort */}
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as 'date' | 'progress' | 'name')}
                className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="date">Sort by Date</option>
                <option value="progress">Sort by Progress</option>
                <option value="name">Sort by Name</option>
              </select>
            </div>
          </div>
          
          <div className="flex gap-2">
            {/* Retry All Failed Button - only show if there are failed files */}
            {jobs.some(job => 
              job.processing_stages?.some(stage => 
                stage.processing_status === 'failed' && stage.uploaded_file_id
              )
            ) && (
              <button
                onClick={handleRetryAllFailed}
                className="flex items-center gap-1 px-3 py-1 text-sm bg-yellow-600 text-white hover:bg-yellow-700 rounded"
                title="Retry all failed files"
              >
                <RefreshCw className="w-4 h-4" />
                Retry All Failed
              </button>
            )}
            <button
              onClick={fetchQueue}
              className="flex items-center gap-1 px-3 py-1 text-sm text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded"
              title="Refresh queue"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
            <button
              onClick={() => setPolling(!polling)}
              className="text-sm text-blue-600 hover:text-blue-700"
            >
              {polling ? 'Pause Updates' : 'Resume Updates'}
            </button>
          </div>
        </div>

        <div className="divide-y divide-gray-200">
          {filteredJobs.length === 0 ? (
            <div className="p-12 text-center">
              <div className="text-gray-400 mb-2">
                {searchQuery || filterStatus !== 'all' ? (
                  <>
                    <Info className="w-12 h-12 mx-auto mb-3" />
                    <p className="text-lg font-medium text-gray-600">No jobs match your filters</p>
                    <p className="text-sm text-gray-500 mt-1">Try adjusting your search or filter criteria</p>
                    <button
                      onClick={() => {
                        setSearchQuery('');
                        setFilterStatus('all');
                      }}
                      className="mt-4 px-4 py-2 text-sm text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors"
                    >
                      Clear Filters
                    </button>
                  </>
                ) : (
                  <>
                    <Upload className="w-12 h-12 mx-auto mb-3" />
                    <p className="text-lg font-medium text-gray-600">No active jobs</p>
                    <p className="text-sm text-gray-500 mt-1">Upload files to get started</p>
                  </>
                )}
              </div>
            </div>
          ) : (
            filteredJobs.map((job) => (
              <div key={job.job_id} className="p-4 hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      {getStatusIcon(job)}
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(job)}`}>
                        {getStatusDisplay(job).text}
                      </span>
                      <span className="text-sm text-gray-600">
                        {job.job_type === 'file' && <Upload className="w-4 h-4 inline mr-1" />}
                        {job.job_type === 'folder' && <FolderOpen className="w-4 h-4 inline mr-1" />}
                        {job.job_type === 'webpage' && <Globe className="w-4 h-4 inline mr-1" />}
                        {job.job_type}
                      </span>
                    </div>
                    <div className="flex items-center justify-between mb-2">
                      <div className="text-sm text-gray-700 truncate flex-1" title={job.source_path}>
                        {job.source_path}
                      </div>
                      <div className="text-xs text-gray-500 ml-2 flex-shrink-0">
                        {formatTimeAgo(job.created_at)}
                      </div>
                    </div>
                    
                    {/* Enhanced Progress Bar */}
                    <div className="mb-2">
                      <div className="w-full bg-gray-200 rounded-full h-2.5 mb-1">
                        <div
                          className={`h-2.5 rounded-full transition-all duration-300 ${
                            job.status === 'failed' ? 'bg-red-600' :
                            job.status === 'completed' ? 'bg-green-600' :
                            'bg-blue-600'
                          }`}
                          style={{ 
                            width: `${Math.max(0, Math.min(100, job.progress_percentage || 
                              (job.total_items > 0 ? 
                                Math.round(((job.completed_items || 0) + (job.failed_items || 0)) / job.total_items * 100) : 
                                0
                              )
                            ))}%` 
                          }}
                        />
                      </div>
                      <div className="flex items-center justify-between text-xs text-gray-600">
                        <div className="space-x-2">
                          <span>Progress: {(job.completed_items || 0) + (job.failed_items || 0)}/{job.total_items || 0} files</span>
                          {job.completed_items > 0 && <span className="text-green-600">✓ {job.completed_items} success</span>}
                          {job.failed_items > 0 && <span className="text-red-600">✗ {job.failed_items} failed</span>}
                          {(job.completed_items || 0) + (job.failed_items || 0) < (job.total_items || 0) && (
                            <span className="text-blue-600">⏳ {(job.total_items || 0) - (job.completed_items || 0) - (job.failed_items || 0)} remaining</span>
                          )}
                        </div>
                        {estimateTimeRemaining(job) && (
                          <span className="text-blue-600 font-medium">{estimateTimeRemaining(job)}</span>
                        )}
                      </div>
                    </div>
                    
                    {/* Per-File Status Display - Enhanced with Upload and Processing Status */}
                    {job.source_files && job.source_files.length > 0 && (
                      <div className="mt-3 space-y-2">
                        <div className="text-xs font-semibold text-gray-700 mb-1 flex items-center justify-between">
                          <button
                            onClick={() => {
                              const newExpanded = new Set(expandedJobs);
                              if (newExpanded.has(job.job_id)) {
                                newExpanded.delete(job.job_id);
                              } else {
                                newExpanded.add(job.job_id);
                              }
                              setExpandedJobs(newExpanded);
                            }}
                            className="flex items-center gap-1 hover:text-blue-600 transition-colors"
                          >
                            {expandedJobs.has(job.job_id) ? (
                              <ChevronRight className="w-3 h-3 rotate-90" />
                            ) : (
                              <ChevronRight className="w-3 h-3" />
                            )}
                            <span>Files ({job.source_files.length}):</span>
                          </button>
                          {job.file_stats && (
                            <span className="text-xs text-gray-500">
                              {job.file_stats.ready} ready • {job.file_stats.processing} processing • {job.file_stats.upload_failed + job.file_stats.processing_failed} failed
                            </span>
                          )}
                        </div>
                        {expandedJobs.has(job.job_id) && job.source_files.map((file: SourceFile, idx: number) => {
                          const fileError = job.file_errors?.[file.name];
                          const uploadError = file.upload_error || (file.upload_status === 'failed' ? fileError : null);
                          const processingError = file.processing_error;
                          const hasError = uploadError || processingError;
                          const uploadFailed = file.upload_status === 'failed';
                          const processingFailed = file.processing_status === 'failed';
                          const isUploaded = file.upload_status === 'uploaded' || file.uploaded_file_id;
                          const isReady = file.processing_status === 'ready';
                          const isCompleted = isReady && file.uploaded_file_id; // File is completed if it's ready and has an uploaded_file_id
                          const isProcessing = file.processing_status && ['processing', 'chunking', 'embedding', 'metadata_extracting'].includes(file.processing_status);
                          const isPendingUpload = (file.upload_status === 'pending' || !file.upload_status) && !isUploaded;
                          const isPendingProcessing = (file.processing_status === 'pending' || !file.processing_status) && !isCompleted && !isProcessing;
                          const canRetry = (uploadFailed || processingFailed) && file.uploaded_file_id && !isCompleted;
                          const canRetryUpload = uploadFailed && !file.uploaded_file_id;
                          
                          return (
                            <div 
                              key={idx} 
                              className={`text-sm p-3 rounded-lg border ${
                                uploadFailed || processingFailed
                                  ? 'bg-red-50 border-red-200' 
                                  : isCompleted
                                  ? 'bg-green-50 border-green-200'
                                  : isProcessing
                                  ? 'bg-blue-50 border-blue-200'
                                  : 'bg-gray-50 border-gray-200'
                              }`}
                            >
                              <div className="flex items-start justify-between gap-2">
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-2 mb-2">
                                    <File className="w-4 h-4 text-gray-500 flex-shrink-0" />
                                    <span className="font-medium text-gray-900 truncate" title={file.name}>
                                      {file.name}
                                    </span>
                                    {file.size && (
                                      <span className="text-xs text-gray-500">
                                        ({formatFileSize(file.size)})
                                      </span>
                                    )}
                                  </div>
                                  
                                  {/* Upload Status Badge */}
                                  <div className="flex items-center gap-2 mb-1">
                                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                                      (file.upload_status === 'uploaded' || file.uploaded_file_id) ? 'bg-green-100 text-green-800 border border-green-300' :
                                      file.upload_status === 'uploading' ? 'bg-blue-100 text-blue-800 border border-blue-300 animate-pulse' :
                                      file.upload_status === 'failed' ? 'bg-red-100 text-red-800 border border-red-300' :
                                      'bg-gray-100 text-gray-800 border border-gray-300'
                                    }`}>
                                      {(file.upload_status === 'uploaded' || file.uploaded_file_id) && '✓ Uploaded'}
                                      {file.upload_status === 'uploading' && '⬆️ Uploading...'}
                                      {file.upload_status === 'failed' && '✗ Upload Failed'}
                                      {isPendingUpload && '⏳ Upload Pending'}
                                    </span>
                                    
                                    {/* Processing Status Badge */}
                                    {isUploaded && (
                                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                                        file.processing_status === 'ready' ? 'bg-green-100 text-green-800 border border-green-300' :
                                        file.processing_status === 'failed' ? 'bg-red-100 text-red-800 border border-red-300' :
                                        file.processing_status === 'no_text_available' ? 'bg-yellow-100 text-yellow-800 border border-yellow-300' :
                                        file.processing_status === 'embedding' ? 'bg-blue-100 text-blue-800 border border-blue-300 animate-pulse' :
                                        file.processing_status === 'chunking' ? 'bg-yellow-100 text-yellow-800 border border-yellow-300 animate-pulse' :
                                        file.processing_status === 'metadata_extracting' ? 'bg-purple-100 text-purple-800 border border-purple-300 animate-pulse' :
                                        file.processing_status === 'processing' ? 'bg-blue-100 text-blue-800 border border-blue-300 animate-pulse' :
                                        'bg-gray-100 text-gray-800 border border-gray-300'
                                      }`}>
                                        {file.processing_status === 'ready' && '✓ Completed'}
                                        {file.processing_status === 'failed' && '✗ Processing Failed'}
                                        {file.processing_status === 'no_text_available' && '⚠ No Text Available'}
                                        {file.processing_status === 'embedding' && '🔄 Embedding...'}
                                        {file.processing_status === 'chunking' && '✂️ Chunking...'}
                                        {file.processing_status === 'metadata_extracting' && '📄 Extracting Metadata...'}
                                        {file.processing_status === 'processing' && '⚙️ Processing...'}
                                        {isPendingProcessing && '⏳ Process Pending'}
                                      </span>
                                    )}
                                    
                                    {file.uploaded_file_id && (
                                      <span className="text-xs text-gray-500">
                                        ID: {file.uploaded_file_id}
                                      </span>
                                    )}
                                    {file.retry_count && file.retry_count > 0 && (
                                      <span className="text-xs text-orange-600">
                                        Retry: {file.retry_count}
                                      </span>
                                    )}
                                  </div>

                                  {/* Processing Progress Details */}
                                  {isUploaded && isProcessing && (
                                    <div className="mt-2 flex items-center gap-3 text-xs">
                                      {file.chunk_count !== undefined && (
                                        <div className="flex items-center gap-1">
                                          <span className="text-green-600 font-medium">✓ Chunks ({file.chunk_count})</span>
                                        </div>
                                      )}
                                      {file.embedding_count !== undefined && (
                                        <div className="flex items-center gap-1">
                                          <span className="text-green-600 font-medium">✓ Embeddings ({file.embedding_count})</span>
                                        </div>
                                      )}
                                    </div>
                                  )}

                                  {/* Upload Error */}
                                  {uploadError && (
                                    <div className="mt-2 p-2 bg-red-100 border border-red-300 rounded text-xs">
                                      <div className="font-semibold text-red-800 mb-1 flex items-center gap-1">
                                        <AlertCircle className="w-3 h-3" />
                                        Upload Error:
                                      </div>
                                      <div className="text-red-700 whitespace-pre-wrap break-words">
                                        {uploadError}
                                      </div>
                                    </div>
                                  )}

                                  {/* Processing Error */}
                                  {processingError && (
                                    <div className="mt-2 p-2 bg-red-100 border border-red-300 rounded text-xs">
                                      <div className="font-semibold text-red-800 mb-1 flex items-center gap-1">
                                        <AlertCircle className="w-3 h-3" />
                                        Processing Error:
                                      </div>
                                      <div className="text-red-700 whitespace-pre-wrap break-words">
                                        {processingError}
                                      </div>
                                    </div>
                                  )}

                                  {/* Success Message */}
                                  {isReady && (
                                    <div className="mt-2 text-xs text-green-700 flex items-center gap-1">
                                      <CheckCircle className="w-3 h-3" />
                                      File is ready for search
                                      {file.chunk_count !== undefined && ` (${file.chunk_count} chunks, ${file.embedding_count || 0} embeddings)`}
                                    </div>
                                  )}

                                  {/* No Text Available Message */}
                                  {file.processing_status === 'no_text_available' && (
                                    <div className="mt-2 text-xs text-yellow-700 flex items-center gap-1">
                                      <AlertCircle className="w-3 h-3" />
                                      No extractable text found. OCR is disabled.
                                    </div>
                                  )}
                                </div>

                                {/* Action Buttons */}
                                <div className="flex items-center gap-1 flex-shrink-0">
                                  {canRetry && (
                                    <button
                                      onClick={() => {
                                        if (file.uploaded_file_id) {
                                          handleRetryProcessing(file.uploaded_file_id);
                                        }
                                      }}
                                      className="p-1.5 text-blue-600 hover:bg-blue-100 rounded transition-colors"
                                      title="Retry processing"
                                    >
                                      <RefreshCw className="w-4 h-4" />
                                    </button>
                                  )}
                                  {canRetryUpload && (
                                    <button
                                      onClick={() => handleRetryFileUpload(job.job_id, file.name)}
                                      className="p-1.5 text-blue-600 hover:bg-blue-100 rounded transition-colors"
                                      title="Retry upload"
                                    >
                                      <RefreshCw className="w-4 h-4" />
                                    </button>
                                  )}
                                  {file.uploaded_file_id && (processingFailed || uploadFailed) && (
                                    <button
                                      onClick={() => handleDeleteFile(file.uploaded_file_id!, file.name)}
                                      className="p-1.5 text-red-600 hover:bg-red-100 rounded transition-colors"
                                      title="Delete file permanently"
                                    >
                                      <Trash2 className="w-4 h-4" />
                                    </button>
                                  )}
                                  {(isPendingUpload || uploadFailed) && !file.uploaded_file_id && (
                                    <button
                                      onClick={() => handleRemoveFileFromJob(job.job_id, file.name)}
                                      className="p-1.5 text-orange-600 hover:bg-orange-100 rounded transition-colors"
                                      title="Remove from queue"
                                    >
                                      <X className="w-4 h-4" />
                                    </button>
                                  )}
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                    
                    {/* Legacy Processing Stages Support */}
                    {!job.source_files && job.processing_stages && job.processing_stages.length > 0 && (
                      <div className="mt-3 space-y-2">
                        <div className="text-xs font-semibold text-gray-700 mb-1">
                          Files ({job.processing_stages.length}):
                        </div>
                        {job.processing_stages.map((stage: any, idx: number) => {
                          const fileError = job.file_errors?.[stage.filename];
                          const hasError = stage.processing_error || fileError;
                          const isFailed = stage.processing_status === 'failed' || hasError;
                          const isPending = stage.processing_status === 'pending' && !stage.uploaded_file_id;
                          const canRetry = (isFailed || isPending) && (stage.uploaded_file_id || !isPending);
                          
                          return (
                            <div 
                              key={idx} 
                              className={`text-sm p-3 rounded-lg border ${
                                isFailed 
                                  ? 'bg-red-50 border-red-200' 
                                  : stage.processing_status === 'ready' 
                                  ? 'bg-green-50 border-green-200'
                                  : 'bg-gray-50 border-gray-200'
                              }`}
                            >
                              <div className="flex items-start justify-between gap-2">
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-2 mb-1">
                                    <File className="w-4 h-4 text-gray-500 flex-shrink-0" />
                                    <span className="font-medium text-gray-900 truncate" title={stage.filename}>
                                      {stage.filename}
                                    </span>
                                  </div>
                                  
                                  <div className="flex items-center gap-2 mb-2">
                                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                                      stage.processing_status === 'ready' ? 'bg-green-100 text-green-800 border border-green-300' :
                                      stage.processing_status === 'failed' ? 'bg-red-100 text-red-800 border border-red-300' :
                                      'bg-gray-100 text-gray-800 border border-gray-300'
                                    }`}>
                                      {stage.processing_status === 'ready' && '✓ Ready'}
                                      {stage.processing_status === 'failed' && '✗ Failed'}
                                      {stage.processing_status === 'pending' && '⏳ Pending'}
                                    </span>
                                  </div>

                                  {hasError && (
                                    <div className="mt-2 p-2 bg-red-100 border border-red-300 rounded text-xs">
                                      <div className="text-red-700">{fileError || stage.processing_error}</div>
                                    </div>
                                  )}
                                </div>

                                <div className="flex items-center gap-1 flex-shrink-0">
                                  {canRetry && stage.uploaded_file_id && (
                                    <button
                                      onClick={() => handleRetryProcessing(stage.uploaded_file_id)}
                                      className="p-1.5 text-blue-600 hover:bg-blue-100 rounded transition-colors"
                                      title="Retry processing"
                                    >
                                      <RefreshCw className="w-4 h-4" />
                                    </button>
                                  )}
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                    
                    {job.error_message && (
                      <div className="text-xs text-red-600 mt-1">{job.error_message}</div>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleViewDetails(job)}
                      className="p-2 text-gray-600 hover:bg-gray-50 rounded"
                      title="View Details"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                    {/* Job control buttons */}
                    <div className="flex gap-1">
                      {/* Pause/Resume - only for active jobs */}
                      {job.status !== 'completed' && !job.cancelled && (
                        <>
                          {job.paused ? (
                            <button
                              onClick={() => handleResume(job.job_id)}
                              className="p-2 text-green-600 hover:bg-green-50 rounded transition-colors"
                              title="Resume Job"
                            >
                              <Play className="w-4 h-4" />
                            </button>
                          ) : (
                            <button
                              onClick={() => handlePause(job.job_id)}
                              className="p-2 text-yellow-600 hover:bg-yellow-50 rounded transition-colors"
                              title="Pause Job"
                            >
                              <Pause className="w-4 h-4" />
                            </button>
                          )}
                        </>
                      )}
                      
                      {/* Retry button - for stuck, failed, or queued jobs with no progress */}
                      {(job.status === 'queued' || job.status === 'failed' || (job.status === 'completed' && job.failed_items > 0)) && (
                        <button
                          onClick={() => handleRetryJob(job.job_id)}
                          className="p-2 text-blue-600 hover:bg-blue-50 rounded transition-colors"
                          title="Retry Job"
                        >
                          <RefreshCw className="w-4 h-4" />
                        </button>
                      )}
                      
                      {/* Delete button - always available, deletes everything */}
                      <button
                        onClick={() => handleDeleteJob(job.job_id)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded transition-colors"
                        title="Delete Job and All Files (Permanent - allows re-upload)"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Job Detail Modal */}
      {selectedJob && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => setSelectedJob(null)}>
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full m-4 max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="p-6 border-b border-gray-200 flex justify-between items-center">
              <h2 className="text-xl font-semibold">Job Details</h2>
              <button
                onClick={() => setSelectedJob(null)}
                className="p-2 hover:bg-gray-100 rounded"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="p-6">
              {jobDetail ? (
                <>
                  <div className="grid grid-cols-2 gap-4 mb-6">
                    <div>
                      <label className="text-sm font-medium text-gray-500">Job ID</label>
                      <div className="text-sm text-gray-900">{jobDetail.job_id}</div>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">Type</label>
                      <div className="text-sm text-gray-900 capitalize">{jobDetail.job_type}</div>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">Status</label>
                      <div className={`text-sm font-medium ${getStatusColor(selectedJob)} inline-block px-2 py-1 rounded`}>
                        {jobDetail.status}
                      </div>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">Source</label>
                      <div className="text-sm text-gray-900 break-all">{jobDetail.source_path}</div>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">Created</label>
                      <div className="text-sm text-gray-900">
                        {new Date(jobDetail.created_at).toLocaleString()}
                      </div>
                    </div>
                  </div>

                  <div className="mb-6">
                    <label className="text-sm font-medium text-gray-500 mb-2 block">Progress</label>
                    <div className="w-full bg-gray-200 rounded-full h-4 mb-2">
                      <div
                        className="bg-blue-600 h-4 rounded-full transition-all"
                        style={{ width: `${jobDetail.progress_percentage || 0}%` }}
                      />
                    </div>
                    <div className="text-sm text-gray-600">
                      {jobDetail.completed_items || 0} / {jobDetail.total_items || 0} completed
                      {jobDetail.failed_items > 0 && ` • ${jobDetail.failed_items} failed`}
                    </div>
                  </div>

                  {jobDetail.source_files && jobDetail.source_files.length > 0 && (
                    <div className="mb-6">
                      <label className="text-sm font-medium text-gray-500 mb-2 block">
                        Documents ({jobDetail.source_files.length})
                      </label>
                      <div className="max-h-96 overflow-y-auto border border-gray-200 rounded divide-y divide-gray-100">
                        {jobDetail.source_files.map((file: any, index: number) => {
                          const fileName = file.name || file.path || `File ${index + 1}`;
                          const fileError = jobDetail.file_errors?.[fileName];
                          
                          // Check actual file processing status - if ready, it's completed
                          const isFullyProcessed = file.processing_status === 'ready' && file.uploaded_file_id;
                          const isUploaded = file.upload_status === 'uploaded' || file.uploaded_file_id;
                          const isProcessing = file.processing_status && 
                            ['processing', 'metadata_extracting', 'chunking', 'embedding'].includes(file.processing_status);
                          const isFailed = !!fileError || file.processing_status === 'failed' || file.upload_status === 'failed';
                          
                          // File is completed if: fully processed (ready) OR uploaded and no processing needed
                          const isCompleted = isFullyProcessed || (isUploaded && !isProcessing && !isFailed && file.processing_status !== 'pending');
                          const isPending = !isCompleted && !isFailed && !isProcessing;

                          const getFileStatusIcon = () => {
                            if (isCompleted) return <CheckCircle className="w-4 h-4 text-green-500" />;
                            if (isFailed) return <AlertCircle className="w-4 h-4 text-red-500" />;
                            if (isProcessing) return <Clock className="w-4 h-4 text-blue-500 animate-pulse" />;
                            return <Clock className="w-4 h-4 text-gray-400" />;
                          };

                          const getFileStatusText = () => {
                            if (isCompleted) return 'Completed';
                            if (isFailed) return 'Failed';
                            if (isProcessing) return 'Processing...';
                            // Distinguish between upload pending and process pending
                            if (!isUploaded) return 'Upload Pending';
                            if (isUploaded && (file.processing_status === 'pending' || !file.processing_status)) return 'Process Pending';
                            return 'Pending';
                          };

                          return (
                            <div key={index} className="p-3 hover:bg-gray-50 transition-colors">
                              <div className="flex items-start justify-between gap-3">
                                <div className="flex items-start gap-2 flex-1 min-w-0">
                                  {getFileStatusIcon()}
                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2">
                                      <File className="w-4 h-4 text-gray-400 flex-shrink-0" />
                                      <span className="text-sm font-medium text-gray-900 truncate" title={fileName}>
                                        {fileName}
                                      </span>
                                    </div>
                                    <div className="flex items-center gap-2 mt-1">
                                      <span className={`text-xs px-2 py-0.5 rounded ${
                                        isCompleted ? 'bg-green-100 text-green-700' :
                                        isFailed ? 'bg-red-100 text-red-700' :
                                        isProcessing ? 'bg-blue-100 text-blue-700' :
                                        'bg-gray-100 text-gray-600'
                                      }`}>
                                        {getFileStatusText()}
                                      </span>
                                      {file.size && (
                                        <span className="text-xs text-gray-500">
                                          {(file.size / 1024 / 1024).toFixed(2)} MB
                                        </span>
                                      )}
                                    </div>
                                    {fileError && (
                                      <div className="text-xs text-red-600 mt-1 bg-red-50 p-2 rounded">
                                        <strong>Error:</strong> {fileError}
                                      </div>
                                    )}
                                  </div>
                                </div>
                                <div className="flex gap-1 flex-shrink-0">
                                  {isFailed && (
                                    <button
                                      onClick={async () => {
                                        if (confirm(`Retry upload for "${fileName}"?`)) {
                                          try {
                                            // Retry by resuming the job (which will retry failed files)
                                            await apiClient.post(`/ai/upload/queue/${jobDetail.job_id}/resume/`);
                                            // Refresh job details
                                            handleViewDetails(selectedJob!);
                                          } catch (error) {
                                            console.error('Retry error:', error);
                                            alert('Failed to retry file upload');
                                          }
                                        }
                                      }}
                                      className="p-1.5 text-blue-600 hover:bg-blue-50 rounded transition-colors"
                                      title="Retry"
                                    >
                                      <RefreshCw className="w-4 h-4" />
                                    </button>
                                  )}
                                  {(isPending || isProcessing) && (
                                    <button
                                      onClick={async () => {
                                        if (confirm(`Cancel upload for "${fileName}"?`)) {
                                          try {
                                            // Note: Individual file cancel would require backend support
                                            // For now, we'll cancel the entire job if it's the only file
                                            if (jobDetail.total_items === 1) {
                                              await apiClient.post(`/ai/upload/queue/${jobDetail.job_id}/cancel/`);
                                              setSelectedJob(null);
                                            } else {
                                              alert('Individual file cancellation is not yet supported. Please cancel the entire job if needed.');
                                            }
                                          } catch (error) {
                                            console.error('Cancel error:', error);
                                            alert('Failed to cancel file upload');
                                          }
                                        }
                                      }}
                                      className="p-1.5 text-red-600 hover:bg-red-50 rounded transition-colors"
                                      title="Cancel"
                                    >
                                      <X className="w-4 h-4" />
                                    </button>
                                  )}
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {jobDetail.error_message && (
                    <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded">
                      <div className="text-sm font-medium text-red-800 mb-1">Job Error</div>
                      <div className="text-sm text-red-700">{jobDetail.error_message}</div>
                    </div>
                  )}

                  {jobDetail.metadata && Object.keys(jobDetail.metadata).length > 0 && (
                    <div>
                      <label className="text-sm font-medium text-gray-500 mb-2 block">Metadata</label>
                      <pre className="text-xs bg-gray-50 p-3 rounded border border-gray-200 overflow-x-auto">
                        {JSON.stringify(jobDetail.metadata, null, 2)}
                      </pre>
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center py-8 text-gray-500">Loading job details...</div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Folder Browser Modal */}

      {/* Discovery Progress Modal */}
      {showDiscoveryProgress && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4 p-6">
            <h3 className="text-lg font-semibold mb-4">Discovering Files...</h3>
            <div className="mb-4">
              <div className="w-full bg-gray-200 rounded-full h-2.5 mb-2">
                <div
                  className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
                  style={{
                    width: discoveryProgress.pagesCrawled > 0
                      ? `${Math.min((discoveryProgress.pagesCrawled / 50) * 100, 100)}%`
                      : '10%'
                  }}
                />
              </div>
              <div className="text-sm text-gray-600">
                <div>{discoveryProgress.status}</div>
                <div className="mt-1">
                  Pages crawled: {discoveryProgress.pagesCrawled} | Files found: {discoveryProgress.filesFound}
                </div>
              </div>
            </div>
            <button
              onClick={() => {
                setShowDiscoveryProgress(false);
                setDiscoveryInProgress(false);
              }}
              className="w-full px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* File Preview Modal */}
      {showFilePreview && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl mx-4 max-h-[80vh] flex flex-col">
            <div className="p-4 border-b border-gray-200 flex justify-between items-center">
              <h3 className="text-lg font-semibold">
                Discovered Files ({discoveredFiles.length})
              </h3>
              <button
                onClick={() => {
                  setShowFilePreview(false);
                  setSelectedFileUrls(new Set());
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4">
              {discoveredFiles.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  No files found. Try adjusting your filters or crawl depth.
                </div>
              ) : (
                <div className="space-y-2">
                  <div className="flex items-center justify-between mb-4 pb-2 border-b">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={selectedFileUrls.size === discoveredFiles.length && discoveredFiles.length > 0}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedFileUrls(new Set(discoveredFiles.map(f => f.url)));
                          } else {
                            setSelectedFileUrls(new Set());
                          }
                        }}
                        className="mr-2"
                      />
                      <span className="text-sm font-medium text-gray-700">
                        Select All ({selectedFileUrls.size} selected)
                      </span>
                    </label>
                  </div>

                  <div className="space-y-1">
                    {discoveredFiles.map((file, index) => (
                      <div
                        key={index}
                        className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50"
                      >
                        <input
                          type="checkbox"
                          checked={selectedFileUrls.has(file.url)}
                          onChange={(e) => {
                            const newSelected = new Set(selectedFileUrls);
                            if (e.target.checked) {
                              newSelected.add(file.url);
                            } else {
                              newSelected.delete(file.url);
                            }
                            setSelectedFileUrls(newSelected);
                          }}
                          className="mr-3"
                        />
                        <File className="w-5 h-5 text-gray-400 mr-3" />
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium text-gray-900 truncate">
                            {file.name}
                          </div>
                          <div className="text-xs text-gray-500 mt-1">
                            <span className="inline-block px-2 py-0.5 bg-blue-100 text-blue-700 rounded mr-2">
                              {file.type.toUpperCase()}
                            </span>
                            {file.size_mb && (
                              <span className="mr-2">{file.size_mb} MB</span>
                            )}
                            <a
                              href={file.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:text-blue-700 underline"
                              onClick={(e) => e.stopPropagation()}
                            >
                              View source
                            </a>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="p-4 border-t border-gray-200 flex justify-between items-center">
              <div className="text-sm text-gray-600">
                {selectedFileUrls.size} file(s) selected
                {selectedFileUrls.size > 0 && (
                  <span className="ml-2">
                    ({discoveredFiles.filter(f => selectedFileUrls.has(f.url)).reduce((sum, f) => sum + (f.size_mb || 0), 0).toFixed(2)} MB total)
                  </span>
                )}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    setShowFilePreview(false);
                    setSelectedFileUrls(new Set());
                  }}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleQueueSelectedFiles}
                  disabled={selectedFileUrls.size === 0 || loading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Submitting...' : 'Submit'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Folder Upload Confirmation Dialog */}
      {showFolderConfirmDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-3xl mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <FolderOpen className="w-5 h-5" />
                Confirm Folder Submission
              </h3>
              <button
                onClick={handleCancelFolderUpload}
                className="text-gray-400 hover:text-gray-600 transition-colors"
                disabled={loading}
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="mb-4">
              <div className="text-sm text-gray-600 mb-2">
                <strong>Folder:</strong> {scannedFolderPath}
              </div>
              <div className="text-sm text-gray-600 mb-4">
                <strong>Files Found:</strong> {scannedFiles.length} file(s) • 
                <strong> Total Size:</strong> {(scannedTotalSize / (1024 * 1024)).toFixed(2)} MB
              </div>
            </div>

            <div className="mb-4 border border-gray-200 rounded-lg max-h-96 overflow-y-auto">
              <div className="divide-y divide-gray-200">
                {scannedFiles.slice(0, 100).map((file, index) => (
                  <div key={index} className="p-3 flex items-center justify-between hover:bg-gray-50">
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <File className="w-4 h-4 text-gray-400 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate" title={file.name || file.file_path}>
                          {file.name || file.filename || file.file_path}
                        </p>
                        <p className="text-xs text-gray-500">
                          {(file.size || file.file_size || 0) > 0 
                            ? `${((file.size || file.file_size) / 1024).toFixed(2)} KB`
                            : 'Size unknown'}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
                {scannedFiles.length > 100 && (
                  <div className="p-3 text-sm text-gray-500 text-center">
                    ... and {scannedFiles.length - 100} more file(s)
                  </div>
                )}
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t">
              <button
                onClick={handleCancelFolderUpload}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                disabled={loading}
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmFolderUpload}
                disabled={loading}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                    Submitting...
                  </>
                ) : (
                  <>
                    <ArrowUp className="w-4 h-4" />
                    Submit
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UnifiedUploadQueue;

