import React, { useState, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { FolderOpen, Upload, Wand2 } from 'lucide-react';
import DocumentManager, { DocumentManagerRef } from './DocumentManager';

const DocumentManagerPage: React.FC = () => {
  const { t } = useTranslation(['documents', 'ai']);
  const [extracting, setExtracting] = useState(false);
  const documentManagerRef = useRef<DocumentManagerRef>(null);

  const handleExtractClick = async () => {
    if (documentManagerRef.current) {
      setExtracting(true);
      try {
        await documentManagerRef.current.handleExtractMetadata();
      } finally {
        setExtracting(false);
      }
    }
  };

  const handleUploadClick = () => {
    if (documentManagerRef.current) {
      documentManagerRef.current.openUploadModal();
    }
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header - Unified with action buttons */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <FolderOpen className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">{t('libraryManager')}</h1>
              <p className="text-sm text-gray-500">{t('uploadOrganizeAndManageKnowledgeBaseDocuments')}</p>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleExtractClick}
              disabled={extracting}
              className="bg-lime-600 hover:bg-lime-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title={t('ai:autoExtractMetadataTitle') || 'Automatically extract product/content/version from existing documents'}
            >
              <Wand2 size={20} />
              {extracting ? (t('ai:extracting') || 'Extracting...') : (t('ai:autoExtractMetadata') || 'Auto-Extract Metadata')}
            </button>
            <button
              onClick={handleUploadClick}
              className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
            >
              <Upload size={20} />
              {t('uploadDocument')}
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 flex overflow-hidden">
        <DocumentManager ref={documentManagerRef} />
      </div>
    </div>
  );
};

export default DocumentManagerPage;
