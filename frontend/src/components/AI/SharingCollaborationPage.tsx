import React, { useState, useMemo } from 'react';
import { Share2, Copy, Mail, Users, Globe, Lock } from 'lucide-react';

const SharingCollaborationPage: React.FC = () => {
  const [publicLinkEnabled, setPublicLinkEnabled] = useState(false);
  const [shareToken, setShareToken] = useState<string | null>(null);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteMsg, setInviteMsg] = useState<string | null>(null);

  const shareLink = useMemo(
    () => (publicLinkEnabled && shareToken ? `${window.location.origin}/api/ai/share/public/${shareToken}` : ''),
    [publicLinkEnabled, shareToken]
  );

  const generateShareToken = () => {
    const token = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
    setShareToken(token);
    setPublicLinkEnabled(true);
  };

  const copyShareLink = () => {
    if (shareLink) {
      navigator.clipboard.writeText(shareLink);
    }
  };

  const handleInvite = () => {
    if (!inviteEmail.trim()) {
      setInviteMsg('Please enter an email address.');
      return;
    }
    // Here you would typically send an invitation email
    setInviteMsg('Invitation sent successfully!');
    setInviteEmail('');
    setTimeout(() => setInviteMsg(null), 3000);
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Share2 className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">Sharing & Collaboration</h1>
              <p className="text-sm text-gray-500">Share your knowledge base and collaborate with others</p>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 flex flex-col">
          {/* Public Sharing */}
          <div className="bg-white border-b border-gray-200 p-6">
            <div className="flex items-center space-x-2 mb-4">
              <Globe className="h-5 w-5 text-blue-600" />
              <h2 className="text-lg font-medium text-gray-900">Public Sharing</h2>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              Create a public link to share your knowledge base with anyone. They can view and search your documents without needing an account.
            </p>
            
            {!publicLinkEnabled ? (
              <button
                onClick={generateShareToken}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors flex items-center space-x-2"
              >
                <Share2 className="h-4 w-4" />
                <span>Generate Public Link</span>
              </button>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center space-x-2">
                  <div className="flex-1">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Public Share Link</label>
                    <div className="flex">
                      <input
                        type="text"
                        value={shareLink}
                        readOnly
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-l-md bg-gray-50 text-sm"
                      />
                      <button
                        onClick={copyShareLink}
                        className="px-4 py-2 bg-gray-600 text-white rounded-r-md hover:bg-gray-700 transition-colors flex items-center space-x-2"
                      >
                        <Copy className="h-4 w-4" />
                        <span>Copy</span>
                      </button>
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <button
                    onClick={() => setPublicLinkEnabled(false)}
                    className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
                  >
                    Disable Public Link
                  </button>
                  <span className="text-sm text-gray-500">
                    Anyone with this link can access your knowledge base
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Team Collaboration */}
          <div className="bg-white border-b border-gray-200 p-6">
            <div className="flex items-center space-x-2 mb-4">
              <Users className="h-5 w-5 text-blue-600" />
              <h2 className="text-lg font-medium text-gray-900">Team Collaboration</h2>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              Invite team members to collaborate on your knowledge base. They'll get access to view, search, and contribute to your documents.
            </p>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Invite by Email</label>
                <div className="flex space-x-2">
                  <input
                    type="email"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    placeholder="colleague@company.com"
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <button
                    onClick={handleInvite}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors flex items-center space-x-2"
                  >
                    <Mail className="h-4 w-4" />
                    <span>Send Invite</span>
                  </button>
                </div>
                {inviteMsg && (
                  <p className={`mt-2 text-sm ${inviteMsg.includes('successfully') ? 'text-green-600' : 'text-red-600'}`}>
                    {inviteMsg}
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Access Control */}
          <div className="bg-white p-6">
            <div className="flex items-center space-x-2 mb-4">
              <Lock className="h-5 w-5 text-blue-600" />
              <h2 className="text-lg font-medium text-gray-900">Access Control</h2>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              Manage who has access to your knowledge base and what they can do.
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="border border-gray-200 rounded-lg p-4">
                <h3 className="font-medium text-gray-900 mb-2">Current Members</h3>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">You (Owner)</span>
                    <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">Owner</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">No team members yet</span>
                    <span className="text-xs text-gray-400">Invite members to get started</span>
                  </div>
                </div>
              </div>
              
              <div className="border border-gray-200 rounded-lg p-4">
                <h3 className="font-medium text-gray-900 mb-2">Permissions</h3>
                <div className="space-y-2 text-sm text-gray-600">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span>View and search documents</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span>Upload new documents</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                    <span>Edit document metadata</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                    <span>Delete documents (Owner only)</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SharingCollaborationPage;
