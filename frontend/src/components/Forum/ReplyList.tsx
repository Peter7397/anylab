import React, { useState, useEffect } from 'react';
import { Heart, Reply, MoreVertical } from 'lucide-react';
import { apiClient } from '../../services/api';
import ReplyEditor from './ReplyEditor';

interface ReplyData {
  id: number;
  content: string;
  author: {
    id: number;
    username: string;
    first_name?: string;
    last_name?: string;
    avatar?: string;
  };
  parent_reply?: number;
  quoted_reply?: ReplyData;
  child_replies?: ReplyData[];
  attachments?: Array<{
    id: number;
    filename: string;
    file_url: string;
  }>;
  like_count: number;
  is_liked: boolean;
  mention_count?: number;
  created_at: string;
  updated_at: string;
}

interface ReplyListProps {
  postId: number;
}

const ReplyList: React.FC<ReplyListProps> = ({ postId }) => {
  const [replies, setReplies] = useState<ReplyData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [replyingTo, setReplyingTo] = useState<number | null>(null);
  const [quotedReply, setQuotedReply] = useState<ReplyData | null>(null);

  useEffect(() => {
    loadReplies();
  }, [postId]);

  const loadReplies = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.getForumPostReplies(postId);
      if (data.results) {
        setReplies(data.results);
      } else if (Array.isArray(data)) {
        setReplies(data);
      } else {
        setReplies(data.replies || []);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load replies');
      console.error('Failed to load replies:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleLike = async (replyId: number) => {
    try {
      const result = await apiClient.likeForumReply(replyId);
      // Update local state
      const updateReply = (reply: ReplyData): ReplyData => {
        if (reply.id === replyId) {
          return { ...reply, is_liked: result.liked, like_count: result.like_count };
        }
        if (reply.child_replies) {
          return {
            ...reply,
            child_replies: reply.child_replies.map(updateReply),
          };
        }
        return reply;
      };
      setReplies(replies.map(updateReply));
    } catch (err: any) {
      console.error('Failed to like reply:', err);
    }
  };

  const handleReplySuccess = () => {
    setReplyingTo(null);
    setQuotedReply(null);
    loadReplies();
  };

  const handleQuote = (reply: ReplyData) => {
    setQuotedReply(reply);
    setReplyingTo(reply.parent_reply || null);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return '刚刚';
    if (minutes < 60) return `${minutes}分钟前`;
    if (hours < 24) return `${hours}小时前`;
    if (days < 7) return `${days}天前`;
    return date.toLocaleDateString('zh-CN');
  };

  const renderReply = (reply: ReplyData, level: number = 0): React.ReactNode => {
    return (
      <div key={reply.id} className={`${level > 0 ? 'ml-8 mt-4' : ''}`}>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          {/* Reply Header */}
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-2">
              <span className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-sm">
                {reply.author.username[0].toUpperCase()}
              </span>
              <div>
                <span className="font-medium text-gray-900">{reply.author.username}</span>
                <span className="text-xs text-gray-500 ml-2">{formatDate(reply.created_at)}</span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => handleLike(reply.id)}
                className={`flex items-center gap-1 text-sm hover:text-red-600 transition-colors ${
                  reply.is_liked ? 'text-red-600' : 'text-gray-500'
                }`}
              >
                <Heart className={`w-4 h-4 ${reply.is_liked ? 'fill-current' : ''}`} />
                {reply.like_count}
              </button>
              <button
                onClick={() => handleQuote(reply)}
                className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
              >
                <Reply className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Quoted Reply */}
          {reply.quoted_reply && (
            <div className="mb-3 p-3 bg-gray-50 border-l-4 border-blue-500 rounded">
              <div className="text-xs text-gray-500 mb-1">
                {reply.quoted_reply.author.username} 说:
              </div>
              <div className="text-sm text-gray-700 line-clamp-3">
                {reply.quoted_reply.content}
              </div>
            </div>
          )}

          {/* Reply Content */}
          <div className="whitespace-pre-wrap text-gray-800 mb-3">{reply.content}</div>

          {/* Attachments */}
          {reply.attachments && reply.attachments.length > 0 && (
            <div className="mb-3">
              {reply.attachments.map(attachment => (
                <a
                  key={attachment.id}
                  href={attachment.file_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-block mr-2 px-2 py-1 bg-gray-100 rounded text-sm text-gray-700 hover:bg-gray-200"
                >
                  {attachment.filename}
                </a>
              ))}
            </div>
          )}

          {/* Reply Button */}
          {level < 3 && (
            <button
              onClick={() => setReplyingTo(reply.id)}
              className="text-sm text-blue-600 hover:text-blue-700"
            >
              回复
            </button>
          )}
        </div>

        {/* Reply Editor */}
        {replyingTo === reply.id && (
          <div className="ml-4 mt-4">
            <ReplyEditor
              postId={postId}
              parentReplyId={reply.id}
              quotedReplyId={quotedReply?.id}
              onSuccess={handleReplySuccess}
              onCancel={() => {
                setReplyingTo(null);
                setQuotedReply(null);
              }}
            />
          </div>
        )}

        {/* Child Replies */}
        {reply.child_replies && reply.child_replies.length > 0 && (
          <div className="mt-4">
            {reply.child_replies.map(childReply => renderReply(childReply, level + 1))}
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
        <p className="mt-2 text-gray-600 text-sm">加载回复中...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error}</p>
      </div>
    );
  }

  if (replies.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>暂无回复</p>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-900 mb-4">
        回复 ({replies.length})
      </h2>
      <div className="space-y-4">
        {replies.map(reply => renderReply(reply))}
      </div>
    </div>
  );
};

export default ReplyList;

