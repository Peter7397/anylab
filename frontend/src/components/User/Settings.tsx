import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Settings as SettingsIcon, Save, Bell, Moon, Globe, Shield, Loader, CheckCircle, XCircle } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface UserSettings {
  notifications: {
    email: boolean;
    push: boolean;
    updates: boolean;
  };
  preferences: {
    theme: 'light' | 'dark' | 'auto';
    language: string;
    timezone: string;
  };
  privacy: {
    profileVisibility: 'public' | 'private' | 'team';
    showEmail: boolean;
  };
}

const Settings: React.FC = () => {
  const { t } = useTranslation('common');
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const [settings, setSettings] = useState<UserSettings>({
    notifications: {
      email: true,
      push: true,
      updates: true,
    },
    preferences: {
      theme: 'light',
      language: 'en',
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    },
    privacy: {
      profileVisibility: 'team',
      showEmail: false,
    },
  });

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = () => {
    // Load settings from localStorage
    const savedSettings = localStorage.getItem('user_settings');
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        setSettings(prev => ({ ...prev, ...parsed }));
      } catch (err) {
        console.error('Failed to parse saved settings:', err);
      }
    }

    // Load theme preference
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | 'auto' | null;
    if (savedTheme) {
      setSettings(prev => ({
        ...prev,
        preferences: { ...prev.preferences, theme: savedTheme },
      }));
    }
  };

  const handleNotificationChange = (key: keyof UserSettings['notifications'], value: boolean) => {
    setSettings(prev => ({
      ...prev,
      notifications: { ...prev.notifications, [key]: value },
    }));
  };

  const handlePreferenceChange = (key: keyof UserSettings['preferences'], value: string) => {
    setSettings(prev => ({
      ...prev,
      preferences: { ...prev.preferences, [key]: value },
    }));
  };

  const handlePrivacyChange = (key: keyof UserSettings['privacy'], value: string | boolean) => {
    setSettings(prev => ({
      ...prev,
      privacy: { ...prev.privacy, [key]: value },
    }));
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(false);

    try {
      // Save to localStorage (in a real app, this would be saved to the backend)
      localStorage.setItem('user_settings', JSON.stringify(settings));
      
      // Save theme preference separately
      localStorage.setItem('theme', settings.preferences.theme);

      // Apply theme if needed
      if (settings.preferences.theme === 'dark') {
        document.documentElement.classList.add('dark');
      } else if (settings.preferences.theme === 'light') {
        document.documentElement.classList.remove('dark');
      } else {
        // Auto theme - follow system preference
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        if (prefersDark) {
          document.documentElement.classList.add('dark');
        } else {
          document.documentElement.classList.remove('dark');
        }
      }

      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err: any) {
      setError(err?.message || t('failedToSaveSettings'));
      console.error('Error saving settings:', err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader className="animate-spin text-primary-600" size={32} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('settings')}</h1>
          <p className="text-gray-600">{t('manageAccountSettingsAndPreferences')}</p>
        </div>
      </div>

      {/* Success/Error Messages */}
      {success && (
        <div className="bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-md flex items-center space-x-2">
          <CheckCircle size={20} />
          <span>{t('settingsSavedSuccessfully')}</span>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-md flex items-center space-x-2">
          <XCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* Notifications Section */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center space-x-3 mb-4">
            <Bell className="text-primary-600" size={20} />
            <h2 className="text-lg font-semibold text-gray-900">{t('notifications')}</h2>
          </div>
          <p className="text-sm text-gray-600 mb-4">{t('chooseHowYouWantToBeNotified')}</p>

          <div className="space-y-4">
            <label className="flex items-center justify-between cursor-pointer">
              <div>
                <span className="text-sm font-medium text-gray-700">{t('emailNotifications')}</span>
                <p className="text-xs text-gray-500">{t('receiveNotificationsViaEmail')}</p>
              </div>
              <input
                type="checkbox"
                checked={settings.notifications.email}
                onChange={(e) => handleNotificationChange('email', e.target.checked)}
                className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
              />
            </label>

            <label className="flex items-center justify-between cursor-pointer">
              <div>
                <span className="text-sm font-medium text-gray-700">{t('pushNotifications')}</span>
                <p className="text-xs text-gray-500">{t('receiveBrowserPushNotifications')}</p>
              </div>
              <input
                type="checkbox"
                checked={settings.notifications.push}
                onChange={(e) => handleNotificationChange('push', e.target.checked)}
                className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
              />
            </label>

            <label className="flex items-center justify-between cursor-pointer">
              <div>
                <span className="text-sm font-medium text-gray-700">{t('productUpdates')}</span>
                <p className="text-xs text-gray-500">{t('getNotifiedAboutNewFeaturesAndUpdates')}</p>
              </div>
              <input
                type="checkbox"
                checked={settings.notifications.updates}
                onChange={(e) => handleNotificationChange('updates', e.target.checked)}
                className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
              />
            </label>
          </div>
        </div>

        {/* Preferences Section */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center space-x-3 mb-4">
            <SettingsIcon className="text-primary-600" size={20} />
            <h2 className="text-lg font-semibold text-gray-900">{t('preferences')}</h2>
          </div>
          <p className="text-sm text-gray-600 mb-4">{t('customizeYourExperience')}</p>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Moon className="inline mr-2" size={16} />
                {t('theme')}
              </label>
              <select
                value={settings.preferences.theme}
                onChange={(e) => handlePreferenceChange('theme', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                <option value="light">{t('light')}</option>
                <option value="dark">{t('dark')}</option>
                <option value="auto">{t('autoSystem')}</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Globe className="inline mr-2" size={16} />
                {t('language')}
              </label>
              <select
                value={settings.preferences.language}
                onChange={(e) => handlePreferenceChange('language', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                <option value="en">{t('english')}</option>
                <option value="es">{t('spanish')}</option>
                <option value="fr">{t('french')}</option>
                <option value="de">{t('german')}</option>
                <option value="ja">{t('japanese')}</option>
                <option value="zh">{t('chinese')}</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('timezone')}
              </label>
              <select
                value={settings.preferences.timezone}
                onChange={(e) => handlePreferenceChange('timezone', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                <option value="UTC">UTC</option>
                <option value="America/New_York">Eastern Time (ET)</option>
                <option value="America/Chicago">Central Time (CT)</option>
                <option value="America/Denver">Mountain Time (MT)</option>
                <option value="America/Los_Angeles">Pacific Time (PT)</option>
                <option value="Europe/London">London (GMT)</option>
                <option value="Europe/Paris">Paris (CET)</option>
                <option value="Asia/Tokyo">Tokyo (JST)</option>
                <option value="Asia/Shanghai">Shanghai (CST)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Privacy Section */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center space-x-3 mb-4">
            <Shield className="text-primary-600" size={20} />
            <h2 className="text-lg font-semibold text-gray-900">{t('privacy')}</h2>
          </div>
          <p className="text-sm text-gray-600 mb-4">{t('controlYourPrivacySettings')}</p>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('profileVisibility')}
              </label>
              <select
                value={settings.privacy.profileVisibility}
                onChange={(e) => handlePrivacyChange('profileVisibility', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                <option value="public">{t('publicEveryoneCanSeeYourProfile')}</option>
                <option value="team">{t('teamOnlyTeamMembersCanSeeYourProfile')}</option>
                <option value="private">{t('privateOnlyYouCanSeeYourProfile')}</option>
              </select>
            </div>

            <label className="flex items-center justify-between cursor-pointer">
              <div>
                <span className="text-sm font-medium text-gray-700">{t('showEmailAddress')}</span>
                <p className="text-xs text-gray-500">{t('allowOthersToSeeYourEmailAddress')}</p>
              </div>
              <input
                type="checkbox"
                checked={settings.privacy.showEmail}
                onChange={(e) => handlePrivacyChange('showEmail', e.target.checked)}
                className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
              />
            </label>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-200">
          <button
            type="submit"
            disabled={saving}
            className="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? (
              <>
                <Loader className="animate-spin" size={16} />
                <span>{t('saving')}</span>
              </>
            ) : (
              <>
                <Save size={16} />
                <span>{t('saveSettings')}</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default Settings;

