import React, { useState, useEffect } from 'react';
import { ChevronDown, ChevronRight, FileText, Download, Eye, Star } from 'lucide-react';
import { apiClient } from '../../services/api';
import { useParams, useNavigate } from 'react-router-dom';

interface ProductDocument {
  id: number;
  title: string;
  filename: string;
  version: string;
  is_latest: boolean;
  file_size: number;
  uploaded_at: string | null;
  document_type: string;
  metadata: any;
  download_url: string;
  view_url: string | null;
}

interface DocumentGroup {
  document_type: string;
  display_name: string;
  total_count: number;
  documents: ProductDocument[];
}

interface ProductDocumentsResponse {
  product: string;
  total_documents: number;
  groups: DocumentGroup[];
}

const ProductDocumentGrid: React.FC = () => {
  const { suite, product } = useParams<{ suite: string; product: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<ProductDocumentsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());
  const [showLatestOnly, setShowLatestOnly] = useState(true);

  useEffect(() => {
    loadDocuments();
  }, [product, showLatestOnly]);

  // Map URL slug to full product category code
  const getProductCategory = (productSlug: string): string => {
    const categoryMap: { [key: string]: string } = {
      'cds': 'openlab_cds',
      'ecm': 'openlab_ecm',
      'eln': 'openlab_eln',
      'server': 'openlab_server',
      'workstation': 'masshunter_workstation',
      'quantitative': 'masshunter_quantitative',
      'qualitative': 'masshunter_qualitative',
      'bioconfirm': 'masshunter_bioconfirm',
      'metabolomics': 'masshunter_metabolomics',
      'current': 'vnmrj_current',
      'legacy': 'vnmrj_legacy'
    };
    return categoryMap[productSlug] || productSlug;
  };

  const loadDocuments = async () => {
    if (!product) return;

    setLoading(true);
    setError(null);

    try {
      const productCategory = getProductCategory(product);
      const response = await apiClient.getProductDocuments(productCategory, { latestOnly: showLatestOnly });
      setData(response);
      
      // Expand first section by default
      if (response.groups.length > 0) {
        setExpandedSections(new Set([response.groups[0].document_type]));
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const toggleSection = (documentType: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(documentType)) {
        newSet.delete(documentType);
      } else {
        newSet.add(documentType);
      }
      return newSet;
    });
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const getProductName = (productSlug: string): string => {
    const names: { [key: string]: string } = {
      'cds': 'OpenLab CDS',
      'ecm': 'OpenLab ECM',
      'eln': 'OpenLab ELN',
      'server': 'OpenLab Server',
      'workstation': 'MassHunter Workstation',
      'quantitative': 'MassHunter Quantitative',
      'qualitative': 'MassHunter Qualitative',
      'bioconfirm': 'MassHunter BioConfirm',
      'metabolomics': 'MassHunter Metabolomics',
      'current': 'VNMRJ Current',
      'legacy': 'VNMRJ Legacy'
    };
    return names[productSlug] || productSlug;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading documents...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
        </div>
      </div>
    );
  }

  if (!data || data.groups.length === 0) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <FileText size={64} className="mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No documents found</h3>
          <p className="text-gray-600">No documents are available for this product yet.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{getProductName(product || '')}</h1>
            <p className="text-gray-600 mt-1">{data.total_documents} documents available</p>
          </div>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={showLatestOnly}
              onChange={(e) => setShowLatestOnly(e.target.checked)}
              className="rounded"
            />
            <span className="text-sm text-gray-700">Show latest versions only</span>
          </label>
        </div>
      </div>

      {/* Document Groups */}
      <div className="space-y-4">
        {data.groups.map((group) => (
          <div
            key={group.document_type}
            className="border border-gray-200 rounded-lg overflow-hidden"
          >
            {/* Group Header */}
            <button
              onClick={() => toggleSection(group.document_type)}
              className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
            >
              <div className="flex items-center gap-3">
                {expandedSections.has(group.document_type) ? (
                  <ChevronDown size={20} className="text-gray-600" />
                ) : (
                  <ChevronRight size={20} className="text-gray-600" />
                )}
                <h3 className="text-lg font-semibold text-gray-900">
                  {group.display_name}
                </h3>
                <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                  {group.total_count} documents
                </span>
              </div>
            </button>

            {/* Group Content */}
            {expandedSections.has(group.document_type) && (
              <div className="p-4 bg-white">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {group.documents.slice(0, showLatestOnly ? 5 : group.documents.length).map((doc) => (
                    <div
                      key={doc.id}
                      className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <FileText size={18} className="text-blue-600" />
                            <span className="text-xs font-medium text-gray-500">{doc.version}</span>
                            {doc.is_latest && (
                              <span className="px-2 py-0.5 bg-green-100 text-green-800 text-xs rounded-full flex items-center gap-1">
                                <Star size={12} className="fill-current" />
                                Latest
                              </span>
                            )}
                          </div>
                          <h4 className="font-semibold text-gray-900 text-sm">{doc.title}</h4>
                        </div>
                      </div>

                      <div className="text-xs text-gray-600 mb-3">
                        <div>{formatFileSize(doc.file_size)}</div>
                        {doc.uploaded_at && (
                          <div>{new Date(doc.uploaded_at).toLocaleDateString()}</div>
                        )}
                      </div>

                      <div className="flex gap-2">
                        {doc.view_url && (
                          <button
                            onClick={() => window.open(doc.view_url!, '_blank')}
                            className="flex-1 px-3 py-1.5 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 transition-colors flex items-center justify-center gap-1"
                          >
                            <Eye size={14} />
                            View
                          </button>
                        )}
                        <button
                          onClick={() => window.open(doc.download_url, '_blank')}
                          className="flex-1 px-3 py-1.5 bg-gray-100 text-gray-700 text-xs rounded hover:bg-gray-200 transition-colors flex items-center justify-center gap-1"
                        >
                          <Download size={14} />
                          Download
                        </button>
                      </div>
                    </div>
                  ))}
                </div>

                {group.documents.length > 5 && showLatestOnly && (
                  <button
                    onClick={() => setShowLatestOnly(false)}
                    className="mt-4 w-full py-2 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                  >
                    Show all {group.total_count} documents
                  </button>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ProductDocumentGrid;

