import React, { useState, useEffect } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import { AIMode } from '../../types';
import { useAuth } from '../../context/AuthContext';

const Layout: React.FC = () => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [aiMode, setAiMode] = useState<AIMode>('performance');
  const location = useLocation();
  const navigate = useNavigate();
  const { error: authError } = useAuth();

  // Detect mobile screen size
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768); // md breakpoint
      // On mobile, sidebar should be closed by default
      if (window.innerWidth < 768) {
        setSidebarCollapsed(true);
      }
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Close mobile sidebar when route changes
  useEffect(() => {
    if (isMobile) {
      setMobileSidebarOpen(false);
    }
  }, [location.pathname, isMobile]);

  // Check authentication and load AI mode on component mount
  // Forum routes can be accessed without authentication (public viewing)
  useEffect(() => {
    const token = localStorage.getItem('anylab_token');
    
    // Public routes that don't require authentication
    // Public routes: / (homepage), /forum and /forum/post/:id (viewing posts)
    // Authenticated forum routes: /forum/new and /forum/post/:id/edit (editing)
    const isPublicRoute = location.pathname === '/' ||
                          location.pathname === '/forum' || 
                          /^\/forum\/post\/\d+$/.test(location.pathname);
    
    // All non-public routes inside Layout require authentication
    if (!isPublicRoute && !token) {
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
        // Store the model that was set
        if (response.ollama_model) {
          localStorage.setItem('ollama_model', response.ollama_model);
        }
        console.log(`AI Mode switched to: ${mode}`, response.message);
        // Optionally show success notification
        if (response.ollama_model) {
          console.log(`Ollama model set to: ${response.ollama_model}`);
        }
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
      {/* Mobile backdrop overlay */}
      {isMobile && mobileSidebarOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setMobileSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <Sidebar 
        collapsed={sidebarCollapsed} 
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        mobileOpen={mobileSidebarOpen}
        isMobile={isMobile}
        onMobileClose={() => setMobileSidebarOpen(false)}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar */}
        <TopBar 
          aiMode={aiMode}
          onAIModeChange={handleAIModeChange}
          onQuickAction={handleQuickAction}
          onMobileMenuToggle={() => setMobileSidebarOpen(!mobileSidebarOpen)}
          isMobile={isMobile}
        />

        {/* Breadcrumbs */}
        <div className="bg-white border-b border-gray-200 px-3 sm:px-6 py-2 sm:py-3">
          <nav className="flex overflow-x-auto" aria-label="Breadcrumb">
            <ol className="flex items-center space-x-1 sm:space-x-2 min-w-max">
              {breadcrumbs.map((breadcrumb, index) => (
                <li key={breadcrumb.href} className="flex items-center">
                  {index > 0 && (
                    <svg
                      className="flex-shrink-0 h-3 w-3 sm:h-4 sm:w-4 text-gray-400 mx-1 sm:mx-2"
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
                  <span className={`text-xs sm:text-sm whitespace-nowrap ${
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
        <main className="flex-1 overflow-auto p-3 sm:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout; 