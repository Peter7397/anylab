import React from 'react';
import DocumentManager from './DocumentManager';
import DocumentViewer from './DocumentViewer';

const SSBDatabase: React.FC = () => {
  const [showViewer, setShowViewer] = React.useState(false);
  const [viewerProps, setViewerProps] = React.useState<{ title: string; url: string; docType: any } | null>(null);

  const handleOpenInViewer = (args: { id: string; title: string; url: string; type: 'pdf'|'docx'|'txt'|'xls'|'xlsx'|'ppt'|'pptx'|'html' }) => {
    setViewerProps({
      title: args.title,
      url: args.url,
      docType: args.type
    });
    setShowViewer(true);
  };

  const handleCloseViewer = () => {
    setShowViewer(false);
    setViewerProps(null);
  };

  if (showViewer && viewerProps) {
    return (
      <div className="p-6 bg-white rounded-lg shadow-sm">
        <button
          onClick={handleCloseViewer}
          className="mb-4 px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-md text-sm font-medium"
        >
          ← Back to SSB Database
        </button>
        <DocumentViewer
          title={viewerProps.title}
          url={viewerProps.url}
          docType={viewerProps.docType}
        />
      </div>
    );
  }

  // Use Document Manager with SSB_KPR filter - much simpler and reuses mature UI
  return <DocumentManager defaultDocType="SSB_KPR" onOpenInViewer={handleOpenInViewer} />;
};

export default SSBDatabase;
