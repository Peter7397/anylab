import React, { useState, useEffect } from 'react';
import { Globe, Plus, Tag, Trash2, Edit, ExternalLink, Copy } from 'lucide-react';
import { apiClient } from '../../services/api';

interface WebLinkItem {
  id: string;
  title: string;
  url: string;
  tags: string[];
  addedAt: string;
}

const UsefulLinksPage: React.FC = () => {
  const [links, setLinks] = useState<WebLinkItem[]>([]);
  const [linkForm, setLinkForm] = useState<{ title: string; url: string; tags: string }>(
    { title: '', url: '', tags: '' }
  );
  const [linkError, setLinkError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadLinks();
  }, []);

  const loadLinks = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.getWeblinks();
      setLinks(response.links.map((item: any) => ({
        id: `${item.id}`,
        title: item.title,
        url: item.url,
        tags: item.tags || [],
        addedAt: (item.created_at || new Date().toISOString()).split('T')[0],
      })));
    } catch (error) {
      console.error('Failed to load links:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const validateUrl = (url: string) => {
    try {
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
      const created = await apiClient.createWeblink({ 
        title: linkForm.title.trim(), 
        url: linkForm.url.trim(), 
        tags 
      });
      
      const newItem: WebLinkItem = {
        id: `${created.id}`,
        title: created.title,
        url: created.url,
        tags: created.tags || [],
        addedAt: (created.created_at || new Date().toISOString()).split('T')[0],
      };
      
      setLinks(prev => [newItem, ...prev]);
      setLinkForm({ title: '', url: '', tags: '' });
    } catch (error) {
      setLinkError('Failed to add link. Please try again.');
    }
  };

  const handleDeleteLink = async (id: string) => {
    try {
      await apiClient.deleteWeblink(parseInt(id));
      setLinks(prev => prev.filter(link => link.id !== id));
    } catch (error) {
      console.error('Failed to delete link:', error);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Globe className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">Useful Links</h1>
              <p className="text-sm text-gray-500">Manage and organize your useful web links</p>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 flex flex-col">
          {/* Add Link Form */}
          <div className="bg-white border-b border-gray-200 p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Add New Link</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
                <input
                  type="text"
                  value={linkForm.title}
                  onChange={(e) => setLinkForm(prev => ({ ...prev, title: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter link title"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">URL</label>
                <input
                  type="url"
                  value={linkForm.url}
                  onChange={(e) => setLinkForm(prev => ({ ...prev, url: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="https://example.com"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tags</label>
                <input
                  type="text"
                  value={linkForm.tags}
                  onChange={(e) => setLinkForm(prev => ({ ...prev, tags: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="tag1, tag2, tag3"
                />
              </div>
            </div>
            {linkError && (
              <p className="mt-2 text-sm text-red-600">{linkError}</p>
            )}
            <button
              onClick={handleAddLink}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors flex items-center space-x-2"
            >
              <Plus className="h-4 w-4" />
              <span>Add Link</span>
            </button>
          </div>

          {/* Links List */}
          <div className="flex-1 overflow-y-auto p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Your Links</h2>
            {isLoading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-2 text-sm text-gray-500">Loading links...</p>
              </div>
            ) : links.length === 0 ? (
              <div className="text-center py-8">
                <Globe className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No links yet</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Add your first useful link above.
                </p>
              </div>
            ) : (
              <div className="grid gap-4">
                {links.map((link) => (
                  <div key={link.id} className="bg-white border border-gray-200 rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="text-lg font-medium text-gray-900">{link.title}</h3>
                        <a
                          href={link.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-700 text-sm flex items-center space-x-1 mt-1"
                        >
                          <span>{link.url}</span>
                          <ExternalLink className="h-3 w-3" />
                        </a>
                        {link.tags.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            {link.tags.map((tag, index) => (
                              <span
                                key={index}
                                className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                              >
                                <Tag className="h-3 w-3 mr-1" />
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}
                        <p className="text-xs text-gray-500 mt-2">Added: {link.addedAt}</p>
                      </div>
                      <div className="flex items-center space-x-2 ml-4">
                        <button
                          onClick={() => copyToClipboard(link.url)}
                          className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                          title="Copy URL"
                        >
                          <Copy className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteLink(link.id)}
                          className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                          title="Delete link"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default UsefulLinksPage;
