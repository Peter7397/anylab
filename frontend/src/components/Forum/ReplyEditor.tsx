import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { X, Paperclip, Send } from 'lucide-react';
import { apiClient } from '../../services/api';

interface ReplyEditorProps {
  postId: number;
  parentReplyId?: number;
  quotedReplyId?: number;
  onSuccess?: () => void;
  onCancel?: () => void;
}

const ReplyEditor: React.FC<ReplyEditorProps> = ({
  postId,
  parentReplyId,
  quotedReplyId,
  onSuccess,
  onCancel,
}) => {
  const { t } = useTranslation('forum');
  const [content, setContent] = useState('');
  const [attachments, setAttachments] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim()) {
      setError(t('pleaseEnterReplyContent'));
      return;
    }

    setUploading(true);
    setError(null);

    try {
      // Upload attachments first if any
      const attachmentIds: number[] = [];
      if (attachments.length > 0) {
        for (const file of attachments) {
          const attachment = await apiClient.uploadForumAttachment(file, postId, undefined);
          if (attachment.id) {
            attachmentIds.push(attachment.id);
          }
        }
      }

      // Create reply
      await apiClient.createForumReply({
        content,
        post: postId,
        parent_reply: parentReplyId,
        quoted_reply: quotedReplyId,
      });

      // Reset form
      setContent('');
      setAttachments([]);
      
      if (onSuccess) {
        onSuccess();
      }
    } catch (err: any) {
      setError(err.message || t('publishReplyFailed'));
      console.error('Failed to create reply:', err);
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

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <form onSubmit={handleSubmit}>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder={t('enterYourReply')}
          className="w-full min-h-[120px] p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
          disabled={uploading}
        />

        {/* Attachments Preview */}
        {attachments.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-2">
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
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mt-2 text-sm text-red-600">{error}</div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-between mt-4">
          <div className="flex items-center gap-2">
            <label className="cursor-pointer inline-flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:text-gray-800 transition-colors">
              <Paperclip className="w-4 h-4" />
              <span>{t('attachment')}</span>
              <input
                type="file"
                multiple
                onChange={handleFileSelect}
                className="hidden"
                disabled={uploading}
              />
            </label>
          </div>
          <div className="flex items-center gap-2">
            {onCancel && (
              <button
                type="button"
                onClick={onCancel}
                className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
                disabled={uploading}
              >
                {t('cancel')}
              </button>
            )}
            <button
              type="submit"
              disabled={uploading || !content.trim()}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send className="w-4 h-4" />
              {uploading ? t('publishing') : t('publish')}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};

export default ReplyEditor;

