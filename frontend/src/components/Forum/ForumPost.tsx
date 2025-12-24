import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { 
  Heart, 
  MessageSquare, 
  Eye, 
  Edit, 
  Trash2,
  Pin,
  Star,
  Reply,
  MoreVertical
} from 'lucide-react';
import { apiClient } from '../../services/api';
import ReplyList from './ReplyList';
import ReplyEditor from './ReplyEditor';

interface ForumPostData {
  id: number;
  title: string;
  content: string;
  author: {
    id: number;
    username: string;
    first_name?: string;
    last_name?: string;
    avatar?: string;
  };
  category?: {
    id: number;
    name: string;
  };
  tags?: Array<{
    id: number;
    name: string;
    color: string;
  }>;
  status: string;
  is_pinned: boolean;
  is_featured: boolean;
  is_public_visible: boolean;
  allow_public_reply: boolean;
  view_count: number;
  like_count: number;
  reply_count: number;
  attachments?: Array<{
    id: number;
    filename: string;
    file_url: string;
    file_size: number;
  }>;
  is_liked: boolean;
  created_at: string;
  updated_at: string;
}

const ForumPost: React.FC = () => {
  const { t } = useTranslation('forum');
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [post, setPost] = useState<ForumPostData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showReplyEditor, setShowReplyEditor] = useState(false);
  const [isAuthor, setIsAuthor] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    if (id) {
      loadPost();
      checkPermissions();
    }
  }, [id]);

  const checkPermissions = () => {
    // Check if user is author or admin
    // This would typically come from auth context
    const token = localStorage.getItem('anylab_token');
    if (token) {
      try {
        // Decode JWT to check user info (simplified)
        // In real implementation, use auth context
        setIsAuthor(false); // Will be set after post loads
        setIsAdmin(false); // Will be set from auth context
      } catch (err) {
        console.error('Failed to check permissions:', err);
      }
    }
  };

  const loadPost = async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.getForumPost(parseInt(id));
      setPost(data);
      // Check if current user is author
      // In real implementation, get from auth context
      const currentUserId = getCurrentUserId();
      if (currentUserId && data.author.id === currentUserId) {
        setIsAuthor(true);
      }
    } catch (err: any) {
      setError(err.message || t('failedToLoadPost'));
      console.error('Failed to load post:', err);
    } finally {
      setLoading(false);
    }
  };

  const getCurrentUserId = (): number | null => {
    // This should come from auth context
    // Simplified for now
    return null;
  };

  const handleLike = async () => {
    if (!post) return;
    try {
      const result = await apiClient.likeForumPost(post.id);
      setPost({
        ...post,
        is_liked: result.liked,
        like_count: result.like_count,
      });
    } catch (err: any) {
      console.error('Failed to like post:', err);
    }
  };

  const handleDelete = async () => {
    if (!post || !window.confirm(t('confirmDeletePost'))) return;
    try {
      await apiClient.deleteForumPost(post.id);
      navigate('/forum');
    } catch (err: any) {
      console.error('Failed to delete post:', err);
      alert(t('deleteFailed') + ': ' + (err.message || t('unknownError')));
    }
  };

  const handleReplySuccess = () => {
    setShowReplyEditor(false);
    loadPost(); // Reload to get updated reply count
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return `0 ${t('bytes')}`;
    const k = 1024;
    const sizes = [t('bytes'), t('kb'), t('mb'), t('gb')];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">{t('loading')}</p>
        </div>
      </div>
    );
  }

  if (error || !post) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600">{error || t('postNotFound')}</p>
          <Link to="/forum" className="mt-4 text-blue-600 hover:underline">
            {t('backToForum')}
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Back Button */}
        <Link
          to="/forum"
          className="inline-flex items-center text-blue-600 hover:text-blue-700 mb-6"
        >
          ← {t('backToForum')}
        </Link>

        {/* Post Card */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
          <div className="p-6">
            {/* Header */}
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  {post.is_pinned && (
                    <Pin className="w-5 h-5 text-yellow-500" />
                  )}
                  {post.is_featured && (
                    <Star className="w-5 h-5 text-orange-500" />
                  )}
                  <h1 className="text-2xl font-bold text-gray-900">{post.title}</h1>
                </div>
                <div className="flex items-center gap-4 text-sm text-gray-500">
                  <span className="flex items-center gap-2">
                    <span className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
                      {post.author.username[0].toUpperCase()}
                    </span>
                    {post.author.username}
                  </span>
                  {post.category && (
                    <span className="px-2 py-1 bg-gray-100 rounded text-gray-600">
                      {post.category.name}
                    </span>
                  )}
                  <span>{formatDate(post.created_at)}</span>
                </div>
              </div>
              {(isAuthor || isAdmin) && (
                <div className="flex items-center gap-2">
                  <Link
                    to={`/forum/post/${post.id}/edit`}
                    className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
                  >
                    <Edit className="w-5 h-5" />
                  </Link>
                  <button
                    onClick={handleDelete}
                    className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              )}
            </div>

            {/* Tags */}
            {post.tags && post.tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-4">
                {post.tags.map(tag => (
                  <span
                    key={tag.id}
                    className="px-2 py-1 text-xs rounded"
                    style={{ backgroundColor: tag.color + '20', color: tag.color }}
                  >
                    {tag.name}
                  </span>
                ))}
              </div>
            )}

            {/* Content */}
            <div className="prose max-w-none mb-6">
              <div className="whitespace-pre-wrap text-gray-800">{post.content}</div>
            </div>

            {/* Attachments */}
            {post.attachments && post.attachments.length > 0 && (
              <div className="mb-6 pt-6 border-t border-gray-200">
                <h3 className="text-sm font-semibold text-gray-700 mb-2">{t('attachments')}</h3>
                <div className="space-y-2">
                  {post.attachments.map(attachment => (
                    <a
                      key={attachment.id}
                      href={attachment.file_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 p-2 bg-gray-50 rounded hover:bg-gray-100 transition-colors"
                    >
                      <span className="text-sm text-gray-700">{attachment.filename}</span>
                      <span className="text-xs text-gray-500 ml-auto">
                        {formatFileSize(attachment.file_size)}
                      </span>
                    </a>
                  ))}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex items-center justify-between pt-4 border-t border-gray-200">
              <div className="flex items-center gap-6">
                <button
                  onClick={handleLike}
                  className={`flex items-center gap-2 hover:text-red-600 transition-colors ${
                    post.is_liked ? 'text-red-600' : 'text-gray-500'
                  }`}
                >
                  <Heart className={`w-5 h-5 ${post.is_liked ? 'fill-current' : ''}`} />
                  <span>{post.like_count}</span>
                </button>
                <span className="flex items-center gap-2 text-gray-500">
                  <MessageSquare className="w-5 h-5" />
                  <span>{post.reply_count}</span>
                </span>
                <span className="flex items-center gap-2 text-gray-500">
                  <Eye className="w-5 h-5" />
                  <span>{post.view_count}</span>
                </span>
              </div>
              <button
                onClick={() => setShowReplyEditor(!showReplyEditor)}
                className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Reply className="w-4 h-4" />
                {t('reply')}
              </button>
            </div>
          </div>
        </div>

        {/* Reply Editor */}
        {showReplyEditor && (
          <div className="mb-6">
            <ReplyEditor
              postId={post.id}
              onSuccess={handleReplySuccess}
              onCancel={() => setShowReplyEditor(false)}
            />
          </div>
        )}

        {/* Replies */}
        <ReplyList postId={post.id} />
      </div>
    </div>
  );
};

export default ForumPost;

