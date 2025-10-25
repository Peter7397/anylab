import React, { useState } from 'react';
import { FileText, X } from 'lucide-react';
import DocumentViewer from './DocumentViewer';

interface ViewerTab {
  id: string;
  title: string;
  url: string;
  type: 'pdf'|'docx'|'txt'|'xls'|'xlsx'|'ppt'|'pptx';
  page?: number;
  query?: string;
}

const DocumentViewerPage: React.FC = () => {
  const [viewerTabs, setViewerTabs] = useState<ViewerTab[]>([]);
  const [activeViewerId, setActiveViewerId] = useState<string | null>(null);

  const openInViewer = (args: ViewerTab) => {
    setActiveViewerId(args.id);
    setViewerTabs(prev => {
      if (prev.find(t => t.id === args.id)) return prev.map(t => t.id === args.id ? { ...t, ...args } : t);
      return [...prev, args];
    });
  };

  const closeViewerTab = (id: string) => {
    setViewerTabs(prev => prev.filter(t => t.id !== id));
    if (activeViewerId === id) {
      const next = viewerTabs.find(t => t.id !== id);
      setActiveViewerId(next ? next.id : null);
    }
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <FileText className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">Document Viewer</h1>
              <p className="text-sm text-gray-500">View and analyze your uploaded documents</p>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Document Viewer */}
        <div className="flex-1 flex flex-col">
          {viewerTabs.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <FileText className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No documents open</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Open a document from the Document Manager to view it here.
                </p>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col">
              {/* Tab Bar */}
              <div className="bg-white border-b border-gray-200 px-4">
                <div className="flex space-x-1 overflow-x-auto">
                  {viewerTabs.map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveViewerId(tab.id)}
                      className={`flex items-center space-x-2 px-3 py-2 text-sm font-medium rounded-t-lg border-b-2 transition-colors ${
                        activeViewerId === tab.id
                          ? 'border-blue-500 text-blue-600 bg-blue-50'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      <FileText className="h-4 w-4" />
                      <span className="truncate max-w-32">{tab.title}</span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          closeViewerTab(tab.id);
                        }}
                        className="ml-1 p-0.5 rounded hover:bg-gray-200"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </button>
                  ))}
                </div>
              </div>

              {/* Document Content */}
              <div className="flex-1">
                {activeViewerId && (
                  <DocumentViewer
                    key={activeViewerId}
                    title={viewerTabs.find(t => t.id === activeViewerId)?.title || 'Document'}
                    url={viewerTabs.find(t => t.id === activeViewerId)?.url || ''}
                    docType={viewerTabs.find(t => t.id === activeViewerId)?.type || 'pdf'}
                    initialPage={viewerTabs.find(t => t.id === activeViewerId)?.page}
                    initialQuery={viewerTabs.find(t => t.id === activeViewerId)?.query}
                  />
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DocumentViewerPage;
