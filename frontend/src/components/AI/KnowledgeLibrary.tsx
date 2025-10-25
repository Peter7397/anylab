import React, { useMemo, useState } from 'react';
import {
  FileText,
  Globe,
  Share2,
  FolderOpen,
  Plus,
  Tag,
  Trash2,
  Edit,
  ExternalLink,
  Copy,
  Link as LinkIcon,
} from 'lucide-react';
import DocumentManager from './DocumentManager';
import DocumentViewer from './DocumentViewer';
import { apiClient } from '../../services/api';

type KnowledgeTabs = 'viewer' | 'manual' | 'weblinks' | 'sharing' | 'others';

interface WebLinkItem {
  id: string;
  title: string;
  url: string;
  tags: string[];
  addedAt: string;
}

const KnowledgeLibrary: React.FC = () => {
  const [activeTab, setActiveTab] = useState<KnowledgeTabs>('manual');

  // Useful Weblinks state
  const [links, setLinks] = useState<WebLinkItem[]>([]);
  const [linkForm, setLinkForm] = useState<{ title: string; url: string; tags: string }>(
    { title: '', url: '', tags: '' }
  );
  const [linkError, setLinkError] = useState<string | null>(null);

  // Sharing KB state
  const [publicLinkEnabled, setPublicLinkEnabled] = useState(false);
  const [shareToken, setShareToken] = useState<string | null>(null);
  const shareLink = useMemo(
    () => (publicLinkEnabled && shareToken ? `${window.location.origin}/api/ai/share/public/${shareToken}` : ''),
    [publicLinkEnabled, shareToken]
  );
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteMsg, setInviteMsg] = useState<string | null>(null);
  const [viewerTabs, setViewerTabs] = useState<Array<{ id: string; title: string; url: string; type: 'pdf'|'docx'|'txt'|'xls'|'xlsx'|'ppt'|'pptx'; page?: number; query?: string }>>([]);
  const [activeViewerId, setActiveViewerId] = useState<string | null>(null);

  const openInViewer = (args: { id: string; title: string; url: string; type: 'pdf'|'docx'|'txt'|'xls'|'xlsx'|'ppt'|'pptx'; page?: number; query?: string }) => {
    setActiveTab('viewer');
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

  const validateUrl = (url: string) => {
    try {
      // eslint-disable-next-line no-new
      new URL(url);
      return true;
    } catch {
      return false;
    }
  };

  const handleAddLink = async () => {
    setLinkError(null);
    if (!linkForm.title.trim()) {
      setLinkError('Title is required.');
      return;
    }
    if (!validateUrl(linkForm.url)) {
      setLinkError('Please enter a valid URL.');
      return;
    }
    const tags = linkForm.tags
      .split(',')
      .map(t => t.trim())
      .filter(Boolean);
    try {
      const created = await apiClient.createWeblink({ title: linkForm.title.trim(), url: linkForm.url.trim(), tags });
      const newItem: WebLinkItem = {
        id: `${created.id}`,
        title: created.title,
        url: created.url,
        tags: created.tags || [],
        addedAt: (created.created_at || new Date().toISOString()).split('T')[0],
      };
      setLinks(prev => [newItem, ...prev]);
      setLinkForm({ title: '', url: '', tags: '' });
    } catch (e: any) {
      setLinkError(e?.message || 'Failed to add link');
    }
  };

  const handleDeleteLink = async (id: string) => {
    try {
      await apiClient.deleteWeblink(Number(id));
      setLinks(prev => prev.filter(l => l.id !== id));
    } catch (e: any) {
      setInviteMsg(e?.message || 'Delete failed');
      setTimeout(() => setInviteMsg(null), 1500);
    }
  };

  const handleCopy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setInviteMsg('Link copied to clipboard');
      setTimeout(() => setInviteMsg(null), 1500);
    } catch {
      setInviteMsg('Copy failed');
      setTimeout(() => setInviteMsg(null), 1500);
    }
  };

  const exportSharingBundle = () => {
    const bundle = {
      generatedAt: new Date().toISOString(),
      weblinks: links,
      note: 'This is a UI-generated export. Backend persistence/sharing to be wired.',
    };
    const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'knowledge_export.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  // Load initial data when switching to tabs
  React.useEffect(() => {
    const init = async () => {
      if (activeTab === 'weblinks') {
        try {
          const resp = await apiClient.getWeblinks();
          const items: WebLinkItem[] = (resp.links || []).map((l: any) => ({
            id: `${l.id}`,
            title: l.title,
            url: l.url,
            tags: l.tags || [],
            addedAt: (l.created_at || '').split('T')[0] || '',
          }));
          setLinks(items);
        } catch (e) {
          // ignore for now
        }
      }
      if (activeTab === 'sharing') {
        try {
          const s = await apiClient.getShareSettings();
          setPublicLinkEnabled(!!s.enabled);
          setShareToken(s.share_token || null);
        } catch (e) {
          // ignore
        }
      }
    };
    init();
  }, [activeTab]);

  return (
    <div className="p-6 bg-white rounded-lg shadow-sm">
      {/* Sticky header + tabs */}
      <div className="sticky top-0 z-30 bg-white pb-4">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Knowledge Library</h2>
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex flex-wrap gap-6">
            <button
              onClick={() => setActiveTab('viewer')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'viewer'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="inline-flex items-center gap-2">
                <FileText size={16} /> Viewer
              </span>
            </button>
            <button
              onClick={() => setActiveTab('manual')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'manual'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="inline-flex items-center gap-2">
                <FileText size={16} /> Documents
              </span>
            </button>
            <button
              onClick={() => setActiveTab('weblinks')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'weblinks'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="inline-flex items-center gap-2">
                <Globe size={16} /> Useful Weblinks
              </span>
            </button>
            <button
              onClick={() => setActiveTab('sharing')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'sharing'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="inline-flex items-center gap-2">
                <Share2 size={16} /> Sharing Knowledge Base
              </span>
            </button>
            <button
              onClick={() => setActiveTab('others')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'others'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="inline-flex items-center gap-2">
                <FolderOpen size={16} /> Others
              </span>
            </button>
          </nav>
        </div>
      </div>

      {activeTab === 'viewer' && (
        <div className="space-y-4">
          {viewerTabs.length === 0 ? (
            <div className="p-6 text-gray-600 border rounded">No document open. Open from Manuals or Weblinks.</div>
          ) : (
            <div className="border rounded">
              <div className="flex items-center gap-2 px-3 py-2 border-b bg-gray-50 overflow-auto">
                {viewerTabs.map(tab => (
                  <div
                    key={tab.id}
                    className={`flex items-center gap-2 px-2 py-1 rounded cursor-pointer ${activeViewerId === tab.id ? 'bg-white border' : 'hover:bg-white'}`}
                    onClick={() => setActiveViewerId(tab.id)}
                  >
                    <span className="text-sm font-medium truncate max-w-[240px]" title={tab.title}>{tab.title}</span>
                    <button
                      className="text-gray-500 hover:text-gray-700"
                      onClick={(e) => { e.stopPropagation(); closeViewerTab(tab.id); }}
                      aria-label="Close tab"
                    >✕</button>
                  </div>
                ))}
              </div>
              <div className="p-3">
                {viewerTabs.map(tab => (
                  <div key={tab.id} className={activeViewerId === tab.id ? 'block' : 'hidden'}>
                    <DocumentViewer title={tab.title} url={tab.url} docType={tab.type} initialPage={tab.page} initialQuery={tab.query} />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'manual' && (
        <DocumentManager onOpenInViewer={(doc: any) => {
          if (!doc?.file_url) return;
          let docType: 'pdf'|'docx'|'txt'|'xls'|'xlsx'|'ppt'|'pptx' = 'pdf';
          const type = doc.document_type || '';
          if (type === 'doc' || type === 'docx') docType = 'docx';
          else if (type === 'xls') docType = 'xls';
          else if (type === 'xlsx') docType = 'xlsx';
          else if (type === 'ppt') docType = 'ppt';
          else if (type === 'pptx') docType = 'pptx';
          else if (type === 'txt') docType = 'txt';
          else docType = 'pdf';
          openInViewer({ id: `doc-${doc.id}`, title: doc.title || doc.filename, url: doc.file_url, type: docType });
        }} />
      )}

      {activeTab === 'weblinks' && (
        <div>
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <h3 className="text-lg font-semibold text-gray-900 mb-3 inline-flex items-center gap-2">
              <Globe size={18} /> Add a Useful Weblink
            </h3>
            {linkError && (
              <div className="mb-3 text-sm text-red-700 bg-red-50 border border-red-200 rounded p-2">
                {linkError}
              </div>
            )}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
                <input
                  type="text"
                  value={linkForm.title}
                  onChange={(e) => setLinkForm(prev => ({ ...prev, title: e.target.value }))}
                  placeholder="e.g. Troubleshooting Guide"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">URL</label>
                <input
                  type="url"
                  value={linkForm.url}
                  onChange={(e) => setLinkForm(prev => ({ ...prev, url: e.target.value }))}
                  placeholder="https://..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1 inline-flex items-center gap-2">
                  <Tag size={14} /> Tags (comma-separated)
                </label>
                <input
                  type="text"
                  value={linkForm.tags}
                  onChange={(e) => setLinkForm(prev => ({ ...prev, tags: e.target.value }))}
                  placeholder="manual, vendor, sql"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
            <div className="mt-4">
              <button
                onClick={handleAddLink}
                className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
              >
                <Plus size={18} /> Add Link
              </button>
            </div>
          </div>

          <div className="space-y-4">
            {links.length === 0 ? (
              <div className="text-center py-12 text-gray-600">
                <Globe size={40} className="mx-auto mb-3 text-gray-400" />
                No weblinks yet. Add your first link above.
              </div>
            ) : (
              links.map(link => (
                <div key={link.id} className="border border-gray-200 rounded-lg p-4 flex justify-between items-start">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <LinkIcon size={16} className="text-blue-600" />
                      <a href={link.url} target="_blank" rel="noreferrer" className="font-medium text-gray-900 truncate hover:underline">
                        {link.title}
                      </a>
                      <a href={link.url} target="_blank" rel="noreferrer" className="text-gray-500 hover:text-gray-700" title="Open">
                        <ExternalLink size={16} />
                      </a>
                    </div>
                    <p className="text-sm text-gray-600 break-all">{link.url}</p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {link.tags.map(t => (
                        <span key={t} className="px-2 py-0.5 text-xs rounded-full bg-blue-50 text-blue-700 border border-blue-200">{t}</span>
                      ))}
                      <span className="text-xs text-gray-400">Added: {link.addedAt}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 ml-4">
                    <button
                      className="p-2 text-gray-600 hover:bg-gray-50 rounded"
                      title="Edit (coming soon)"
                    >
                      <Edit size={16} />
                    </button>
                    <button
                      onClick={() => handleDeleteLink(link.id)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded"
                      title="Delete"
                    >
                      <Trash2 size={16} />
                    </button>
                    {/\.(pdf|docx?|txt|xlsx?|pptx?)(\?.*)?$/i.test(link.url) && (
                      <button
                        onClick={() => {
                          const ext = link.url.toLowerCase().match(/\.(pdf|docx?|txt|xlsx?|pptx?)(\?.*)?$/);
                          let type: 'pdf'|'docx'|'txt'|'xls'|'xlsx'|'ppt'|'pptx' = 'pdf';
                          if (ext) {
                            const extension = ext[1];
                            if (extension === 'xlsx') type = 'xlsx';
                            else if (extension === 'xls') type = 'xls';
                            else if (extension === 'pptx') type = 'pptx';
                            else if (extension === 'ppt') type = 'ppt';
                            else if (extension === 'docx') type = 'docx';
                            else if (extension === 'doc') type = 'docx';
                            else if (extension === 'txt') type = 'txt';
                            else type = 'pdf';
                          }
                          openInViewer({ id: `link-${link.id}`, title: link.title, url: link.url, type });
                        }}
                        className="p-2 text-blue-600 hover:bg-blue-50 rounded"
                        title="Open in Viewer"
                      >
                        Open
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {activeTab === 'sharing' && (
        <div className="space-y-6">
          <div className="p-4 bg-gray-50 rounded-lg">
            <h3 className="text-lg font-semibold text-gray-900 mb-3 inline-flex items-center gap-2">
              <Share2 size={18} /> Share Settings
            </h3>
            <div className="flex items-center gap-3">
              <label className="inline-flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={publicLinkEnabled}
                  onChange={(e) => setPublicLinkEnabled(e.target.checked)}
                />
                Enable public share link
              </label>
              {publicLinkEnabled && (
                <div className="flex items-center gap-2">
                  <code className="px-2 py-1 bg-white rounded border text-sm break-all">{shareLink}</code>
                  <button onClick={() => handleCopy(shareLink)} className="p-2 text-gray-600 hover:bg-gray-100 rounded" title="Copy link">
                    <Copy size={16} />
                  </button>
                </div>
              )}
            </div>
            {inviteMsg && <p className="text-sm text-green-700 mt-2">{inviteMsg}</p>}
          </div>

          <div className="p-4 bg-gray-50 rounded-lg">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Invite collaborators</h3>
            <div className="flex gap-3 max-w-xl">
              <input
                type="email"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                placeholder="user@example.com"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <button
                onClick={() => {
                  if (!inviteEmail.includes('@')) {
                    setInviteMsg('Please enter a valid email');
                    setTimeout(() => setInviteMsg(null), 1500);
                    return;
                  }
                  setInviteMsg('Invitation sent (demo)');
                  setInviteEmail('');
                  setTimeout(() => setInviteMsg(null), 1500);
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Send Invite
              </button>
            </div>
          </div>

          <div className="p-4 bg-gray-50 rounded-lg">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Export knowledge bundle</h3>
            <p className="text-sm text-gray-600 mb-3">Export weblinks as JSON. Documents are managed in the Manual tab.</p>
            <button
              onClick={exportSharingBundle}
              className="inline-flex items-center gap-2 bg-gray-700 hover:bg-gray-800 text-white px-4 py-2 rounded-lg"
            >
              <Share2 size={16} /> Export JSON
            </button>
          </div>
        </div>
      )}

      {activeTab === 'others' && (
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="border rounded-lg p-4">
            <h4 className="font-semibold mb-1">Website Import (planned)</h4>
            <p className="text-sm text-gray-600 mb-3">Crawl and ingest docs from vendor support sites.</p>
            <button className="px-3 py-2 rounded bg-gray-200 text-gray-500 cursor-not-allowed">Coming soon</button>
          </div>
          <div className="border rounded-lg p-4">
            <h4 className="font-semibold mb-1">Bulk CSV Import (planned)</h4>
            <p className="text-sm text-gray-600 mb-3">Upload metadata to pre-tag manuals and links.</p>
            <button className="px-3 py-2 rounded bg-gray-200 text-gray-500 cursor-not-allowed">Coming soon</button>
          </div>
          <div className="border rounded-lg p-4">
            <h4 className="font-semibold mb-1">Cleanup & Dedup (planned)</h4>
            <p className="text-sm text-gray-600 mb-3">Find duplicates and outdated documents.</p>
            <button className="px-3 py-2 rounded bg-gray-200 text-gray-500 cursor-not-allowed">Coming soon</button>
          </div>
          <div className="border rounded-lg p-4">
            <h4 className="font-semibold mb-1">Categories & Tags (planned)</h4>
            <p className="text-sm text-gray-600 mb-3">Organize knowledge with categories.</p>
            <button className="px-3 py-2 rounded bg-gray-200 text-gray-500 cursor-not-allowed">Coming soon</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default KnowledgeLibrary;