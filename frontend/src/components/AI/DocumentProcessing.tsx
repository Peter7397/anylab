import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Upload, FileVideo, Image, CheckCircle, AlertCircle, X, Download, Eye } from 'lucide-react';
import { apiClient } from '../../services/api';

interface ProcessedFile {
  id: string;
  title: string;
  filename: string;
  type: 'video' | 'image';
  status: 'processing' | 'completed' | 'error';
  metadata?: any;
  created_at: string;
}

const DocumentProcessing: React.FC = () => {
  const { t } = useTranslation('documents');
  const [activeTab, setActiveTab] = useState<'video' | 'image'>('video');
  const [files, setFiles] = useState<ProcessedFile[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      if (!title) {
        setTitle(e.target.files[0].name);
      }
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError(t('pleaseSelectFile'));
      return;
    }

    setUploading(true);
    setError(null);
    
    try {
      let result;
      if (activeTab === 'video') {
        result = await apiClient.processVideo(selectedFile, title || undefined, description || undefined);
        
        // Add to files list
        const newFile: ProcessedFile = {
          id: result.data.document_id || Date.now().toString(),
          title: result.data.title || title,
          filename: selectedFile.name,
          type: 'video',
          status: 'completed',
          metadata: result.data.metadata,
          created_at: new Date().toISOString(),
        };
        setFiles([newFile, ...files]);
      } else {
        result = await apiClient.processImage(selectedFile, title || undefined, description || undefined);
        
        // Add to files list
        const newFile: ProcessedFile = {
          id: result.data.document_id || Date.now().toString(),
          title: result.data.title || title,
          filename: selectedFile.name,
          type: 'image',
          status: 'completed',
          metadata: result.data.metadata,
          created_at: new Date().toISOString(),
        };
        setFiles([newFile, ...files]);
      }

      // Reset form
      setSelectedFile(null);
      setTitle('');
      setDescription('');
      const fileInput = document.getElementById('file-input') as HTMLInputElement;
      if (fileInput) fileInput.value = '';
      
    } catch (err: any) {
      setError(err?.message || t('failedToProcessFile'));
      console.error('Upload error:', err);
    } finally {
      setUploading(false);
    }
  };

  const handleRemove = (id: string) => {
    setFiles(files.filter(f => f.id !== id));
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return `0 ${t('bytes')}`;
    const k = 1024;
    const sizes = [t('bytes'), t('kb'), t('mb'), t('gb')];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('documentProcessing')}</h1>
          <p className="text-gray-600">{t('processVideosAndImagesForAIAnalysis')}</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab('video')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'video'
                ? 'border-blue-500 text-emerald-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <FileVideo className="inline mr-2" size={16} />
            {t('videoProcessing')}
          </button>
          <button
            onClick={() => setActiveTab('image')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'image'
                ? 'border-blue-500 text-emerald-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Image className="inline mr-2" size={16} />
            {t('imageOcr')}
          </button>
        </nav>
      </div>

      {/* Upload Section */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          {activeTab === 'video' ? t('uploadVideoForTranscriptExtraction') : t('uploadImageForOcrProcessing')}
        </h3>

        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-3 flex items-start">
            <AlertCircle className="text-red-600 mt-0.5 mr-3" size={20} />
            <div className="flex-1">
              <p className="text-sm font-medium text-red-800">{t('error')}</p>
              <p className="text-sm text-red-600">{error}</p>
            </div>
            <button onClick={() => setError(null)}>
              <X size={16} className="text-red-600" />
            </button>
          </div>
        )}

        <div className="space-y-4">
          {/* File Upload */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {activeTab === 'video' ? t('selectVideoFile') : t('selectImageFile')}
            </label>
            <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-lg hover:border-gray-400 transition-colors">
              <div className="space-y-1 text-center">
                {selectedFile ? (
                  <div className="text-sm text-gray-600">
                    <p className="font-medium">{selectedFile.name}</p>
                    <p className="text-gray-500">{formatFileSize(selectedFile.size)}</p>
                    <button
                      onClick={() => setSelectedFile(null)}
                      className="mt-2 text-sm text-red-600 hover:text-red-800"
                    >
                      {t('remove')}
                    </button>
                  </div>
                ) : (
                  <>
                    <Upload className="mx-auto h-12 w-12 text-gray-400" />
                    <div className="flex text-sm text-gray-600">
                      <label
                        htmlFor="file-input"
                        className="relative cursor-pointer bg-white rounded-md font-medium text-emerald-600 hover:text-blue-500 focus-within:outline-none"
                      >
                        <span>{t('uploadAFile')}</span>
                        <input
                          id="file-input"
                          type="file"
                          className="sr-only"
                          accept={activeTab === 'video' ? 'video/*' : 'image/*'}
                          onChange={handleFileSelect}
                        />
                      </label>
                      <p className="pl-1">{t('orDragAndDrop')}</p>
                    </div>
                    <p className="text-xs text-gray-500">
                      {activeTab === 'video' ? t('videoFileFormats') : t('imageFileFormats')}
                    </p>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Title Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('title')} ({t('optional')})
            </label>
            <input
              type="text"
              className="input-field"
              placeholder={activeTab === 'video' ? t('enterVideoTitle') : t('enterImageTitle')}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>

          {/* Description Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('description')} ({t('optional')})
            </label>
            <textarea
              className="input-field"
              rows={3}
              placeholder={activeTab === 'video' ? t('enterVideoDescription') : t('enterImageDescription')}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          {/* Upload Button */}
          <button
            onClick={handleUpload}
            disabled={!selectedFile || uploading}
            className="btn-primary w-full"
          >
            {uploading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                {t('processing')}
              </>
            ) : (
              <>
                <Upload size={16} className="mr-2" />
                {activeTab === 'video' ? t('processVideo') : t('processImage')}
              </>
            )}
          </button>
        </div>
      </div>

      {/* Results Section */}
      {files.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('processedFiles')}</h3>
          <div className="space-y-4">
            {files
              .filter(f => f.type === activeTab)
              .map((file) => (
                <div
                  key={file.id}
                  className="border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center">
                        <div className={`p-2 rounded-lg ${
                          file.type === 'video' ? 'bg-emerald-100' : 'bg-lime-100'
                        }`}>
                          {file.type === 'video' ? (
                            <FileVideo className={`${file.type === 'video' ? 'text-emerald-600' : 'text-lime-600'}`} size={20} />
                          ) : (
                            <Image className="text-lime-600" size={20} />
                          )}
                        </div>
                        <div className="ml-4">
                          <p className="text-sm font-medium text-gray-900">{file.title}</p>
                          <p className="text-xs text-gray-500">{file.filename}</p>
                          <p className="text-xs text-gray-400 mt-1">
                            {new Date(file.created_at).toLocaleString()}
                          </p>
                        </div>
                      </div>

                      {/* Metadata */}
                      {file.metadata && (
                        <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-gray-600">
                          {file.type === 'video' ? (
                            <>
                              {file.metadata.duration && (
                                <div>{t('duration')}: {parseFloat(file.metadata.duration).toFixed(2)}s</div>
                              )}
                              {file.metadata.language && (
                                <div>{t('language')}: {file.metadata.language}</div>
                              )}
                              {file.metadata.word_count && (
                                <div>{t('words')}: {file.metadata.word_count}</div>
                              )}
                              {file.metadata.confidence && (
                                <div>{t('confidence')}: {(file.metadata.confidence * 100).toFixed(1)}%</div>
                              )}
                            </>
                          ) : (
                            <>
                              {file.metadata.dimensions && (
                                <div>{t('dimensions')}: {file.metadata.dimensions}</div>
                              )}
                              {file.metadata.word_count && (
                                <div>{t('words')}: {file.metadata.word_count}</div>
                              )}
                              {file.metadata.confidence && (
                                <div>{t('confidence')}: {(file.metadata.confidence * 100).toFixed(1)}%</div>
                              )}
                              {file.metadata.language && (
                                <div>{t('language')}: {file.metadata.language}</div>
                              )}
                            </>
                          )}
                        </div>
                      )}
                    </div>

                    <div className="flex items-center space-x-2">
                      {file.status === 'completed' && (
                        <CheckCircle className="text-green-600" size={20} />
                      )}
                      <button
                        onClick={() => handleRemove(file.id)}
                        className="text-gray-400 hover:text-red-600"
                      >
                        <X size={16} />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}

      {files.filter(f => f.type === activeTab).length === 0 && (
        <div className="card text-center py-12">
          <p className="text-gray-500">
            {activeTab === 'video' ? t('noVideoFilesProcessedYet') : t('noImageFilesProcessedYet')}
          </p>
        </div>
      )}
    </div>
  );
};

export default DocumentProcessing;

