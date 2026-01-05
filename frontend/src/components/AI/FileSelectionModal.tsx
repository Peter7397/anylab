import React, { useState } from 'react';
import { X, Upload, File, ExternalLink } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../../services/api';

interface FileSelectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onQueued: () => void;
}

const FileSelectionModal: React.FC<FileSelectionModalProps> = ({ isOpen, onClose, onQueued }) => {
  const { t } = useTranslation('ai');
  const navigate = useNavigate();
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isQueuing, setIsQueuing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showQueueLink, setShowQueueLink] = useState(false);

  if (!isOpen) return null;

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      const files = Array.from(event.target.files);
      setSelectedFiles(files);
      setError(null);
    }
  };

  const handleQueueFiles = async () => {
    if (selectedFiles.length === 0) {
      setError(t('pleaseSelectFilesToUpload') || 'Please select files to upload');
      return;
    }

    setIsQueuing(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('job_type', 'file');
      formData.append('source', 'file_upload');
      formData.append('priority', '5');

      selectedFiles.forEach((file) => {
        formData.append('files', file);
      });

      const response = await apiClient.post('/ai/upload/queue/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      // Success - job queued immediately in Redis, user can continue
      const jobData = (response as any).data?.data || (response as any).data;
      setSelectedFiles([]);
      setShowQueueLink(true);
      onQueued();
      
      // Close modal immediately - user can continue adding more jobs
      // Job is already queued and will process in background
      onClose();
      
      // Optionally navigate to upload queue (non-blocking)
      setTimeout(() => {
        navigate('/ai/knowledge/upload');
      }, 500);
    } catch (err: any) {
      console.error('Queue error:', err);
      setError(err.response?.data?.error || err.message || t('failedToQueueFiles') || 'Failed to queue files');
    } finally {
      setIsQueuing(false);
    }
  };

  const handleRemoveFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Upload size={20} />
            {t('selectFilesToUpload') || 'Select Files to Upload'}
          </h3>
          <button
            onClick={() => {
              setShowQueueLink(false);
              onClose();
            }}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            disabled={isQueuing}
          >
            <X size={20} />
          </button>
        </div>

        <div className="space-y-4">
          {/* File Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('documentFilesMultipleSelection') || 'Select Documents (Multiple Selection)'}
            </label>
            <input
              type="file"
              multiple
              accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.rtf,.mhtml,.html"
              onChange={handleFileSelect}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              disabled={isQueuing}
            />
            <p className="mt-1 text-xs text-gray-500">
              {t('supportedFormats') || 'Supported formats: PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, TXT, RTF, MHTML, HTML'}
            </p>
          </div>

          {/* Selected Files List */}
          {selectedFiles.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('selectedFiles') || 'Selected Files'} ({selectedFiles.length})
              </label>
              <div className="border border-gray-300 rounded-lg max-h-64 overflow-y-auto">
                <div className="divide-y divide-gray-200">
                  {selectedFiles.map((file, index) => (
                    <div key={index} className="p-3 flex items-center justify-between hover:bg-gray-50">
                      <div className="flex items-center gap-3 flex-1 min-w-0">
                        <File size={16} className="text-gray-400 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate" title={file.name}>
                            {file.name}
                          </p>
                          <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                        </div>
                      </div>
                      <button
                        onClick={() => handleRemoveFile(index)}
                        className="text-red-500 hover:text-red-700 ml-2 flex-shrink-0"
                        disabled={isQueuing}
                        title={t('remove') || 'Remove'}
                      >
                        <X size={16} />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
              <div className="mt-2 text-sm text-gray-600">
                {t('totalSize') || 'Total size'}: {formatFileSize(selectedFiles.reduce((sum, f) => sum + f.size, 0))}
              </div>
            </div>
          )}

          {/* Success Message with Queue Link */}
          {showQueueLink && !error && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
              <p className="text-sm text-green-700 mb-2">
                ✓ Files queued successfully! Redirecting to Upload Queue...
              </p>
              <button
                onClick={() => {
                  onClose();
                  navigate('/ai/knowledge/upload');
                }}
                className="text-sm text-green-700 hover:text-green-800 underline flex items-center gap-1"
              >
                Go to Upload Queue <ExternalLink size={14} />
              </button>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <button
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              disabled={isQueuing}
            >
              {t('cancel') || 'Cancel'}
            </button>
            <button
              onClick={handleQueueFiles}
              disabled={isQueuing || selectedFiles.length === 0}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {isQueuing ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                  {t('queuing') || 'Queuing...'}
                </>
              ) : (
                <>
                  <Upload size={16} />
                  {t('queueFiles') || 'Queue Files'}
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FileSelectionModal;

