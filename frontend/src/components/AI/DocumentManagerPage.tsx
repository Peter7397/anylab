import React from 'react';
import { FolderOpen } from 'lucide-react';
import DocumentManager from './DocumentManager';

const DocumentManagerPage: React.FC = () => {
  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <FolderOpen className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">Document Manager</h1>
              <p className="text-sm text-gray-500">Upload, organize, and manage your knowledge base documents</p>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 flex overflow-hidden">
        <DocumentManager />
      </div>
    </div>
  );
};

export default DocumentManagerPage;
