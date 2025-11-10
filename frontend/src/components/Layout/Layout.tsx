import React, { useState, useEffect } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import { AIMode } from '../../types';
import { useAuth } from '../../context/AuthContext';

const Layout: React.FC = () => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [aiMode, setAiMode] = useState<AIMode>('performance');
  const location = useLocation();
  const navigate = useNavigate();
  const { error: authError } = useAuth();

  // Check authentication and load AI mode on component mount
  // Forum routes can be accessed without authentication (public viewing)
  useEffect(() => {
    const token = localStorage.getItem('anylab_token');
    
    // Forum routes are public - don't require authentication
    // Public forum routes: /forum and /forum/post/:id (viewing posts)
    // Authenticated forum routes: /forum/new and /forum/post/:id/edit (editing)
    const isPublicForumRoute = location.pathname === '/forum' || 
                                /^\/forum\/post\/\d+$/.test(location.pathname);
    
    // All non-public-forum routes inside Layout require authentication
    if (!isPublicForumRoute && !token) {
      console.log('No auth token found, redirecting to login');
      navigate('/login', { replace: true });
      return;
    }
    
    // Load AI mode preference (only for authenticated users)
    if (token) {
      const savedMode = localStorage.getItem('ai_mode') as AIMode;
      if (savedMode && (savedMode === 'performance' || savedMode === 'lightweight')) {
        setAiMode(savedMode);
      }
    }
  }, [navigate, location.pathname]);

  const handleQuickAction = (action: string) => {
    switch (action) {
      case 'scan':
        navigate('/scrapers');
        break;
      case 'refresh':
        window.location.reload();
        break;
      case 'report':
        // Navigate to analytics or generate report
        navigate('/admin/analytics');
        break;
      case 'analyze':
        // Navigate to Library Manager landing page
        navigate('/ai/knowledge/manager');
        break;
      default:
        console.log('Quick action:', action);
    }
  };

  const handleAIModeChange = async (mode: AIMode) => {
    try {
      // Call backend API to switch mode
      const { apiClient } = await import('../../services/api');
      const response = await apiClient.switchAIMode(mode);
      
      if (response.success) {
        setAiMode(mode);
        // Store AI mode preference
        localStorage.setItem('ai_mode', mode);
        console.log(`AI Mode switched to: ${mode}`, response.message);
      } else {
        console.error('Failed to switch AI mode:', response.error);
        // Optionally show error notification to user
      }
    } catch (error: any) {
      console.error('Error switching AI mode:', error);
      // Fallback: still update local state even if backend call fails
      setAiMode(mode);
      localStorage.setItem('ai_mode', mode);
    }
  };

  // Generate breadcrumbs from current path
  const generateBreadcrumbs = () => {
    const pathSegments = location.pathname.split('/').filter(Boolean);
    const breadcrumbs = [{ name: 'Dashboard', href: '/' }];
    
    let currentPath = '';
    pathSegments.forEach((segment, index) => {
      currentPath += `/${segment}`;
      const name = segment.charAt(0).toUpperCase() + segment.slice(1).replace(/-/g, ' ');
      breadcrumbs.push({ name, href: currentPath });
    });
    
    return breadcrumbs;
  };

  const breadcrumbs = generateBreadcrumbs();

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <Sidebar 
        collapsed={sidebarCollapsed} 
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)} 
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar */}
        <TopBar 
          aiMode={aiMode}
          onAIModeChange={handleAIModeChange}
          onQuickAction={handleQuickAction}
        />

        {/* Breadcrumbs */}
        <div className="bg-white border-b border-gray-200 px-6 py-3">
          <nav className="flex" aria-label="Breadcrumb">
            <ol className="flex items-center space-x-2">
              {breadcrumbs.map((breadcrumb, index) => (
                <li key={breadcrumb.href} className="flex items-center">
                  {index > 0 && (
                    <svg
                      className="flex-shrink-0 h-4 w-4 text-gray-400 mx-2"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  )}
                  <span className={`text-sm ${
                    index === breadcrumbs.length - 1
                      ? 'text-gray-900 font-medium'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}>
                    {breadcrumb.name}
                  </span>
                </li>
              ))}
            </ol>
          </nav>
        </div>

        {/* Auth Error Banner */}
        {authError && (
          <div className="bg-red-50 border-b border-red-200 px-6 py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <svg className="w-5 h-5 text-red-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <p className="text-sm text-red-800">{authError}</p>
              </div>
              <button
                onClick={() => navigate('/login')}
                className="text-sm text-red-600 hover:text-red-800 font-medium underline"
              >
                Go to Login
              </button>
            </div>
          </div>
        )}

        {/* Page Content */}
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout; 