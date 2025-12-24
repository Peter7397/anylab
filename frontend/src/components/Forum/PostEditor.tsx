import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router-dom';
import { X, Paperclip, Send, Tag, Image as ImageIcon } from 'lucide-react';
import { apiClient } from '../../services/api';

interface PostEditorProps {
  postId?: number; // If provided, edit mode
}

const PostEditor: React.FC<PostEditorProps> = () => {
  const { t } = useTranslation('forum');
  const navigate = useNavigate();
  const { id } = useParams<{ id?: string }>();
  const postId = id ? parseInt(id) : undefined;
  const isEditMode = !!postId;

  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [category, setCategory] = useState<number | null>(null);
  const [selectedTags, setSelectedTags] = useState<number[]>([]);
  const [isPublicVisible, setIsPublicVisible] = useState(false);
  const [allowPublicReply, setAllowPublicReply] = useState(false);
  const [attachments, setAttachments] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [categories, setCategories] = useState<any[]>([]);
  const [tags, setTags] = useState<any[]>([]);
  const [tagSearchQuery, setTagSearchQuery] = useState('');

  useEffect(() => {
    loadCategories();
    loadTags();
    if (isEditMode && postId) {
      loadPost();
    }
  }, [postId, isEditMode]);

  const loadCategories = async () => {
    try {
      const data = await apiClient.getForumCategories();
      setCategories(Array.isArray(data) ? data : data.results || []);
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  };

  const loadTags = async () => {
    try {
      const data = await apiClient.getForumTags(tagSearchQuery || undefined);
      setTags(Array.isArray(data) ? data : data.results || []);
    } catch (err) {
      console.error('Failed to load tags:', err);
    }
  };

  const loadPost = async () => {
    if (!postId) return;
    try {
      const data = await apiClient.getForumPost(postId);
      setTitle(data.title);
      setContent(data.content);
      setCategory(data.category?.id || null);
      setSelectedTags(data.tags?.map((t: any) => t.id) || []);
      setIsPublicVisible(data.is_public_visible || false);
      setAllowPublicReply(data.allow_public_reply || false);
    } catch (err: any) {
      setError(err.message || t('failedToLoadPost'));
    }
  };

  useEffect(() => {
    if (tagSearchQuery !== undefined) {
      const timer = setTimeout(() => {
        loadTags();
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [tagSearchQuery]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setError(t('pleaseEnterTitle'));
      return;
    }
    if (!content.trim()) {
      setError(t('pleaseEnterContent'));
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const postData: any = {
        title: title.trim(),
        content: content.trim(),
        tag_ids: selectedTags,
        is_public_visible: isPublicVisible,
        allow_public_reply: allowPublicReply,
      };

      if (category) {
        postData.category = category;
      }

      if (isEditMode && postId) {
        await apiClient.updateForumPost(postId, postData);
      } else {
        await apiClient.createForumPost(postData);
      }

      // Upload attachments if any
      if (attachments.length > 0) {
        const newPostId = isEditMode ? postId : undefined; // Would need to get from create response
        for (const file of attachments) {
          await apiClient.uploadForumAttachment(file, newPostId);
        }
      }

      navigate('/forum');
    } catch (err: any) {
      setError(err.message || t('publishFailed'));
      console.error('Failed to save post:', err);
    } finally {
      setUploading(false);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      setAttachments([...attachments, ...files]);
    }
  };

  const removeAttachment = (index: number) => {
    setAttachments(attachments.filter((_, i) => i !== index));
  };

  const toggleTag = (tagId: number) => {
    if (selectedTags.includes(tagId)) {
      setSelectedTags(selectedTags.filter(id => id !== tagId));
    } else {
      setSelectedTags([...selectedTags, tagId]);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          {isEditMode ? t('editPost') : t('createNewPost')}
        </h1>

        <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          {/* Error Message */}
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
              {error}
            </div>
          )}

          {/* Title */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('title')} *
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder={t('enterPostTitle')}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={uploading}
              required
            />
          </div>

          {/* Category */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('category')}
            </label>
            <select
              value={category || ''}
              onChange={(e) => setCategory(e.target.value ? parseInt(e.target.value) : null)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={uploading}
            >
              <option value="">{t('selectCategory')}</option>
              {categories.map(cat => (
                <option key={cat.id} value={cat.id}>{cat.name}</option>
              ))}
            </select>
          </div>

          {/* Tags */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('tags')}
            </label>
            <div className="flex flex-wrap gap-2 mb-2">
              {tags.filter(tag => selectedTags.includes(tag.id)).map(tag => (
                <span
                  key={tag.id}
                  onClick={() => toggleTag(tag.id)}
                  className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm cursor-pointer"
                  style={{ backgroundColor: tag.color + '20', color: tag.color }}
                >
                  {tag.name}
                  <X className="w-3 h-3" />
                </span>
              ))}
            </div>
            <input
              type="text"
              value={tagSearchQuery}
              onChange={(e) => setTagSearchQuery(e.target.value)}
              placeholder={t('searchTags')}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={uploading}
            />
            {tagSearchQuery && (
              <div className="mt-2 flex flex-wrap gap-2">
                {tags.filter(tag => !selectedTags.includes(tag.id)).slice(0, 10).map(tag => (
                  <span
                    key={tag.id}
                    onClick={() => toggleTag(tag.id)}
                    className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm cursor-pointer hover:opacity-80"
                    style={{ backgroundColor: tag.color + '20', color: tag.color }}
                  >
                    {tag.name}
                    <span className="text-xs">+</span>
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Content */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('content')} *
            </label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder={t('enterPostContent')}
              className="w-full min-h-[300px] px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-y"
              disabled={uploading}
              required
            />
            <p className="mt-1 text-xs text-gray-500">
              {t('mentionUserHint')}
            </p>
          </div>

          {/* Attachments */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('attachments')}
            </label>
            {attachments.length > 0 && (
              <div className="mb-2 flex flex-wrap gap-2">
                {attachments.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center gap-2 px-3 py-1 bg-gray-100 rounded text-sm"
                  >
                    <span className="text-gray-700">{file.name}</span>
                    <button
                      type="button"
                      onClick={() => removeAttachment(index)}
                      className="text-gray-400 hover:text-red-600"
                      disabled={uploading}
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
            <label className="cursor-pointer inline-flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-600 hover:text-gray-800 transition-colors">
              <Paperclip className="w-4 h-4" />
              <span>{t('addAttachment')}</span>
              <input
                type="file"
                multiple
                onChange={handleFileSelect}
                className="hidden"
                disabled={uploading}
              />
            </label>
          </div>

          {/* Options */}
          <div className="mb-6 space-y-2">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={isPublicVisible}
                onChange={(e) => setIsPublicVisible(e.target.checked)}
                disabled={uploading}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">{t('publicVisible')}</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={allowPublicReply}
                onChange={(e) => setAllowPublicReply(e.target.checked)}
                disabled={uploading}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">{t('allowPublicReply')}</span>
            </label>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-4">
            <button
              type="button"
              onClick={() => navigate('/forum')}
              className="px-6 py-2 text-gray-600 hover:text-gray-800 transition-colors"
              disabled={uploading}
            >
              {t('cancel')}
            </button>
            <button
              type="submit"
              disabled={uploading || !title.trim() || !content.trim()}
              className="inline-flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send className="w-4 h-4" />
              {uploading ? t('publishing') : isEditMode ? t('save') : t('publish')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default PostEditor;

