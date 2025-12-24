import React from 'react';
import { useTranslation } from 'react-i18next';
import { Globe } from 'lucide-react';

const LanguageSwitcher: React.FC = () => {
  const { i18n } = useTranslation();

  const changeLanguage = (lng: string) => {
    i18n.changeLanguage(lng);
    localStorage.setItem('anylab_language', lng);
  };

  return (
    <div className="relative inline-block">
      <select
        value={i18n.language || 'zh-CN'}
        onChange={(e) => changeLanguage(e.target.value)}
        className="appearance-none bg-white border border-gray-300 rounded-md px-3 py-1.5 pr-8 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 cursor-pointer"
        aria-label="Select language"
      >
        <option value="zh-CN">简体中文</option>
        <option value="en-US">English</option>
      </select>
      <Globe 
        size={16} 
        className="absolute right-2 top-1/2 transform -translate-y-1/2 pointer-events-none text-gray-500"
      />
    </div>
  );
};

export default LanguageSwitcher;

