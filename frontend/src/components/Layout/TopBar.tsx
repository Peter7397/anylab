import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
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
import { useAuth } from '../../context/AuthContext';
import LanguageSwitcher from './LanguageSwitcher';

interface TopBarProps {
  aiMode: AIMode;
  onAIModeChange: (mode: AIMode) => void;
  onQuickAction: (action: string) => void;
}

const TopBar: React.FC<TopBarProps> = ({ aiMode, onAIModeChange, onQuickAction }) => {
  const { t } = useTranslation('common');
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showAIModeMenu, setShowAIModeMenu] = useState(false);
  const [recommendedModels, setRecommendedModels] = useState<{ performance?: string; lightweight?: string }>({});
  const navigate = useNavigate();
  const { clearAuth, user } = useAuth();
  
  // Load recommended models on mount
  useEffect(() => {
    const loadModels = async () => {
      try {
        const { apiClient } = await import('../../services/api');
        const settings = await apiClient.getSystemSettings();
        if (settings?.rag?.recommended_models) {
          setRecommendedModels(settings.rag.recommended_models);
        }
      } catch (error) {
        console.error('Failed to load recommended models:', error);
      }
    };
    loadModels();
  }, []);
  
  // Get display name for user
  const displayName = user 
    ? (user.first_name && user.last_name 
        ? `${user.first_name} ${user.last_name}` 
        : user.username)
    : 'User';

  const handleLogout = () => {
    // Clear auth state (tokens, permissions, user) using AuthContext
    clearAuth();
    // Redirect to login
    navigate('/login', { replace: true });
  };

  const quickActions = [
    { nameKey: 'scraperManager', icon: Radar, action: 'scan' },
    { nameKey: 'refresh', icon: RefreshCw, action: 'refresh' },
    { nameKey: 'analytics', icon: FileText, action: 'report' },
    { nameKey: 'libraryManager', icon: Sparkles, action: 'analyze' },
  ];

  const aiModes = [
    { 
      value: 'performance' as AIMode, 
      labelKey: 'performanceMode', 
      descriptionKey: 'fullPrecisionModelsForMaximumAccuracy',
      requirements: 'Mac Mini M3 32GB or PC with 16-24GB GPU'
    },
    { 
      value: 'lightweight' as AIMode, 
      labelKey: 'lightweightMode', 
      descriptionKey: 'quantizedModelsForLowResourceUsage',
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
                key={action.nameKey}
                onClick={() => onQuickAction(action.action)}
                className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors"
              >
                <Icon size={16} />
                <span>{t(action.nameKey)}</span>
              </button>
            );
          })}
        </div>

        {/* Persistent AI Assistant Button */}
        <div className="flex items-center">
          <button
            onClick={() => navigate('/ai/chat')}
            className="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors"
            title={t('openAiAssistant')}
          >
            {t('aiAssistant')}
          </button>
        </div>

        {/* Language Switcher, AI Mode Toggle and User Menu */}
        <div className="flex items-center space-x-4">
          {/* Language Switcher */}
          <LanguageSwitcher />
          
          {/* AI Mode Toggle */}
          <div className="relative">
            <button
              onClick={() => setShowAIModeMenu(!showAIModeMenu)}
              className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors"
              title={t('aiModeSwitchDescription')}
            >
              <Sparkles size={16} />
              <span>
                {t('aiMode')}: {aiMode === 'performance' ? t('performanceMode') : t('lightweightMode')}
                {(() => {
                  const storedModel = localStorage.getItem('ollama_model');
                  if (storedModel) {
                    return <span className="text-xs text-gray-500 ml-1">({storedModel})</span>;
                  }
                  return null;
                })()}
              </span>
              <ChevronDown size={16} />
            </button>

            {showAIModeMenu && (
              <div className="absolute right-0 mt-2 w-80 bg-white rounded-md shadow-lg border border-gray-200 z-50">
                <div className="p-4">
                  <h3 className="text-sm font-medium text-gray-900 mb-1">{t('aiModeSelection')}</h3>
                  <p className="text-xs text-gray-500 mb-3">{t('chooseBetweenPerformanceAndLightweight')}</p>
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
                            {t(mode.labelKey)}
                          </span>
                          {aiMode === mode.value && (
                            <div className="w-2 h-2 bg-primary-500 rounded-full"></div>
                          )}
                        </div>
                        <p className="text-xs text-gray-600 mb-1">{t(mode.descriptionKey)}</p>
                        <p className="text-xs text-gray-500">Requirements: {mode.requirements}</p>
                        {recommendedModels[mode.value] && (
                          <p className="text-xs text-primary-600 mt-1 font-medium">
                            Model: {recommendedModels[mode.value]}
                          </p>
                        )}
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
              <span>{displayName}</span>
              <ChevronDown size={16} />
            </button>

            {showUserMenu && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg border border-gray-200 z-50">
                <div className="py-1">
                  <button 
                    onClick={() => {
                      setShowUserMenu(false);
                      navigate('/profile');
                    }}
                    className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                  >
                    <User size={16} className="mr-3" />
                    {t('profile')}
                  </button>
                  <button 
                    onClick={() => {
                      setShowUserMenu(false);
                      navigate('/settings');
                    }}
                    className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                  >
                    <Settings size={16} className="mr-3" />
                    {t('settings')}
                  </button>
                  <hr className="my-1" />
                  <button 
                    onClick={handleLogout}
                    className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                  >
                    <LogOut size={16} className="mr-3" />
                    {t('logout')}
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