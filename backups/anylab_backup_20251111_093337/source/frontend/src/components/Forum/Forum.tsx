import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  MessageSquare, 
  Heart, 
  Eye, 
  Plus, 
  Search,
  Pin,
  Star,
  Filter,
  X
} from 'lucide-react';
import { apiClient } from '../../services/api';

interface ForumCategory {
  id: number;
  name: string;
  description?: string;
  icon?: string;
  post_count?: number;
}

interface ForumTag {
  id: number;
  name: string;
  color: string;
}

interface ForumPost {
  id: number;
  title: string;
  author: {
    id: number;
    username: string;
    first_name?: string;
    last_name?: string;
    avatar?: string;
  };
  category?: ForumCategory;
  tags?: ForumTag[];
  status: string;
  is_pinned: boolean;
  is_featured: boolean;
  is_public_visible: boolean;
  view_count: number;
  like_count: number;
  reply_count: number;
  last_reply_at?: string;
  last_reply_author?: {
    id: number;
    username: string;
  };
  is_liked: boolean;
  created_at: string;
  updated_at: string;
}

const Forum: React.FC = () => {
  const [posts, setPosts] = useState<ForumPost[]>([]);
  const [categories, setCategories] = useState<ForumCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null);
  const [selectedTag, setSelectedTag] = useState<number | null>(null);
  const [filterPinned, setFilterPinned] = useState<boolean | null>(null);
  const [filterFeatured, setFilterFeatured] = useState<boolean | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    loadCategories();
    loadPosts();
  }, [selectedCategory, selectedTag, filterPinned, filterFeatured, currentPage]);

  const loadCategories = async () => {
    try {
      const data = await apiClient.getForumCategories();
      setCategories(Array.isArray(data) ? data : data.results || []);
    } catch (err: any) {
      console.error('Failed to load categories:', err);
    }
  };

  const loadPosts = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: any = {
        page: currentPage,
        page_size: 20,
        status: 'published',
      };
      
      if (searchQuery.trim()) {
        params.search = searchQuery.trim();
      }
      if (selectedCategory) {
        params.category = selectedCategory;
      }
      if (selectedTag) {
        params.tag = selectedTag;
      }
      if (filterPinned !== null) {
        params.pinned = filterPinned;
      }
      if (filterFeatured !== null) {
        params.featured = filterFeatured;
      }

      const data = await apiClient.getForumPosts(params);
      
      if (data.results) {
        setPosts(data.results);
        if (data.count && data.page_size) {
          setTotalPages(Math.ceil(data.count / data.page_size));
        }
      } else if (Array.isArray(data)) {
        setPosts(data);
      } else {
        setPosts(data.posts || []);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load posts');
      console.error('Failed to load posts:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    setCurrentPage(1);
    loadPosts();
  };

  const handleLike = async (postId: number) => {
    try {
      const result = await apiClient.likeForumPost(postId);
      // Update local state
      setPosts(posts.map(post => 
        post.id === postId 
          ? { ...post, is_liked: result.liked, like_count: result.like_count }
          : post
      ));
    } catch (err: any) {
      console.error('Failed to like post:', err);
    }
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

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-3xl font-bold text-gray-900">论坛</h1>
            <Link
              to="/forum/new"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Plus className="w-5 h-5 mr-2" />
              发帖
            </Link>
          </div>

          {/* Search and Filters */}
          <div className="flex flex-col sm:flex-row gap-4 mb-6">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="搜索帖子..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <button
              onClick={handleSearch}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              搜索
            </button>
          </div>

          {/* Category and Filter Chips */}
          <div className="flex flex-wrap gap-2 mb-4">
            <button
              onClick={() => {
                setSelectedCategory(null);
                setSelectedTag(null);
                setFilterPinned(null);
                setFilterFeatured(null);
                setCurrentPage(1);
              }}
              className={`px-3 py-1 rounded-full text-sm ${
                !selectedCategory && !selectedTag && filterPinned === null && filterFeatured === null
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              全部
            </button>
            {categories.map(cat => (
              <button
                key={cat.id}
                onClick={() => {
                  setSelectedCategory(cat.id);
                  setCurrentPage(1);
                }}
                className={`px-3 py-1 rounded-full text-sm ${
                  selectedCategory === cat.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                {cat.name}
              </button>
            ))}
            <button
              onClick={() => {
                setFilterPinned(filterPinned === null ? true : null);
                setCurrentPage(1);
              }}
              className={`px-3 py-1 rounded-full text-sm flex items-center gap-1 ${
                filterPinned === true
                  ? 'bg-yellow-500 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              <Pin className="w-4 h-4" />
              置顶
            </button>
            <button
              onClick={() => {
                setFilterFeatured(filterFeatured === null ? true : null);
                setCurrentPage(1);
              }}
              className={`px-3 py-1 rounded-full text-sm flex items-center gap-1 ${
                filterFeatured === true
                  ? 'bg-orange-500 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              <Star className="w-4 h-4" />
              精华
            </button>
          </div>
        </div>

        {/* Posts List */}
        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-gray-600">加载中...</p>
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">{error}</p>
          </div>
        ) : posts.length === 0 ? (
          <div className="text-center py-12">
            <MessageSquare className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">暂无帖子</p>
          </div>
        ) : (
          <>
            <div className="space-y-4">
              {posts.map(post => (
                <div
                  key={post.id}
                  className={`bg-white rounded-lg shadow-sm border ${
                    post.is_pinned ? 'border-yellow-400 border-l-4' : 'border-gray-200'
                  } hover:shadow-md transition-shadow`}
                >
                  <div className="p-6">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          {post.is_pinned && (
                            <Pin className="w-4 h-4 text-yellow-500" />
                          )}
                          {post.is_featured && (
                            <Star className="w-4 h-4 text-orange-500" />
                          )}
                          <Link
                            to={`/forum/post/${post.id}`}
                            className="text-xl font-semibold text-gray-900 hover:text-blue-600 transition-colors"
                          >
                            {post.title}
                          </Link>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-gray-500">
                          <span className="flex items-center gap-1">
                            <span className="w-6 h-6 rounded-full bg-gray-200 flex items-center justify-center">
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
                    </div>

                    {post.tags && post.tags.length > 0 && (
                      <div className="flex flex-wrap gap-2 mb-3">
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

                    <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-100">
                      <div className="flex items-center gap-6 text-sm text-gray-500">
                        <button
                          onClick={() => handleLike(post.id)}
                          className={`flex items-center gap-1 hover:text-red-600 transition-colors ${
                            post.is_liked ? 'text-red-600' : ''
                          }`}
                        >
                          <Heart className={`w-4 h-4 ${post.is_liked ? 'fill-current' : ''}`} />
                          {post.like_count}
                        </button>
                        <span className="flex items-center gap-1">
                          <MessageSquare className="w-4 h-4" />
                          {post.reply_count}
                        </span>
                        <span className="flex items-center gap-1">
                          <Eye className="w-4 h-4" />
                          {post.view_count}
                        </span>
                      </div>
                      {post.last_reply_author && (
                        <span className="text-xs text-gray-500">
                          最后回复: {post.last_reply_author.username} {formatDate(post.last_reply_at!)}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex justify-center items-center gap-2 mt-8">
                <button
                  onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                  className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                >
                  上一页
                </button>
                <span className="px-4 py-2 text-gray-700">
                  第 {currentPage} 页，共 {totalPages} 页
                </span>
                <button
                  onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                  disabled={currentPage === totalPages}
                  className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                >
                  下一页
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default Forum;

