import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Radar, 
  RefreshCw, 
  FileText, 
  Sparkles, 
  User, 
  Settings, 
  LogOut,
  ChevronDown
} from 'lucide-react';
import { AIMode } from '../../types';

interface TopBarProps {
  aiMode: AIMode;
  onAIModeChange: (mode: AIMode) => void;
  onQuickAction: (action: string) => void;
}

const TopBar: React.FC<TopBarProps> = ({ aiMode, onAIModeChange, onQuickAction }) => {
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showAIModeMenu, setShowAIModeMenu] = useState(false);
  const navigate = useNavigate();

  const handleLogout = () => {
    // Clear auth tokens
    localStorage.removeItem(process.env.REACT_APP_JWT_STORAGE_KEY || 'anylab_token');
    localStorage.removeItem(process.env.REACT_APP_REFRESH_TOKEN_KEY || 'anylab_refresh_token');
    // Redirect to login
    navigate('/login', { replace: true });
  };

  const quickActions = [
    { name: 'Scan', icon: Radar, action: 'scan' },
    { name: 'Refresh', icon: RefreshCw, action: 'refresh' },
    { name: 'Generate Report', icon: FileText, action: 'report' },
    { name: 'AI Analyze', icon: Sparkles, action: 'analyze' },
  ];

  const aiModes = [
    { 
      value: 'performance' as AIMode, 
      label: 'Performance Mode', 
      description: 'Full-precision models for maximum accuracy',
      requirements: 'Mac Mini M3 32GB or PC with 16-24GB GPU'
    },
    { 
      value: 'lightweight' as AIMode, 
      label: 'Lightweight Mode', 
      description: 'Quantized models for low resource usage',
      requirements: 'Mac Mini M2/M3 16GB or low-spec PCs'
    },
  ];

  return (
    <div className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        {/* Quick Action Buttons */}
        <div className="flex items-center space-x-3">
          {quickActions.map((action) => {
            const Icon = action.icon;
            return (
              <button
                key={action.name}
                onClick={() => onQuickAction(action.action)}
                className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors"
              >
                <Icon size={16} />
                <span>{action.name}</span>
              </button>
            );
          })}
        </div>

        {/* AI Mode Toggle and User Menu */}
        <div className="flex items-center space-x-4">
          {/* AI Mode Toggle */}
          <div className="relative">
            <button
              onClick={() => setShowAIModeMenu(!showAIModeMenu)}
              className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors"
            >
              <Sparkles size={16} />
              <span>{aiMode === 'performance' ? 'Performance' : 'Lightweight'}</span>
              <ChevronDown size={16} />
            </button>

            {showAIModeMenu && (
              <div className="absolute right-0 mt-2 w-80 bg-white rounded-md shadow-lg border border-gray-200 z-50">
                <div className="p-4">
                  <h3 className="text-sm font-medium text-gray-900 mb-3">AI Mode Selection</h3>
                  <div className="space-y-3">
                    {aiModes.map((mode) => (
                      <div
                        key={mode.value}
                        className={`p-3 rounded-md border cursor-pointer transition-colors ${
                          aiMode === mode.value
                            ? 'border-primary-500 bg-primary-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                        onClick={() => {
                          onAIModeChange(mode.value);
                          setShowAIModeMenu(false);
                        }}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-gray-900">
                            {mode.label}
                          </span>
                          {aiMode === mode.value && (
                            <div className="w-2 h-2 bg-primary-500 rounded-full"></div>
                          )}
                        </div>
                        <p className="text-xs text-gray-600 mb-1">{mode.description}</p>
                        <p className="text-xs text-gray-500">Requirements: {mode.requirements}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* User Menu */}
          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors"
            >
              <User size={16} />
              <span>Admin User</span>
              <ChevronDown size={16} />
            </button>

            {showUserMenu && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg border border-gray-200 z-50">
                <div className="py-1">
                  <button className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors">
                    <User size={16} className="mr-3" />
                    Profile
                  </button>
                  <button className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors">
                    <Settings size={16} className="mr-3" />
                    Settings
                  </button>
                  <hr className="my-1" />
                  <button 
                    onClick={handleLogout}
                    className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                  >
                    <LogOut size={16} className="mr-3" />
                    Logout
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Click outside to close menus */}
      {(showUserMenu || showAIModeMenu) && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => {
            setShowUserMenu(false);
            setShowAIModeMenu(false);
          }}
        />
      )}
    </div>
  );
};

export default TopBar; 