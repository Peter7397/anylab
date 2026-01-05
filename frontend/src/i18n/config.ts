import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// Import translation files
import commonZh from '../locales/zh-CN/common.json';
import commonEn from '../locales/en-US/common.json';
import sidebarZh from '../locales/zh-CN/sidebar.json';
import sidebarEn from '../locales/en-US/sidebar.json';
import dashboardZh from '../locales/zh-CN/dashboard.json';
import dashboardEn from '../locales/en-US/dashboard.json';
import authZh from '../locales/zh-CN/auth.json';
import authEn from '../locales/en-US/auth.json';
import aiZh from '../locales/zh-CN/ai.json';
import aiEn from '../locales/en-US/ai.json';
import adminZh from '../locales/zh-CN/admin.json';
import adminEn from '../locales/en-US/admin.json';
import forumZh from '../locales/zh-CN/forum.json';
import forumEn from '../locales/en-US/forum.json';
import documentsZh from '../locales/zh-CN/documents.json';
import documentsEn from '../locales/en-US/documents.json';
import errorsZh from '../locales/zh-CN/errors.json';
import errorsEn from '../locales/en-US/errors.json';
import validationZh from '../locales/zh-CN/validation.json';
import validationEn from '../locales/en-US/validation.json';

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      'zh-CN': {
        common: commonZh,
        sidebar: sidebarZh,
        dashboard: dashboardZh,
        auth: authZh,
        ai: aiZh,
        admin: adminZh,
        forum: forumZh,
        documents: documentsZh,
        errors: errorsZh,
        validation: validationZh,
      },
      'en-US': {
        common: commonEn,
        sidebar: sidebarEn,
        dashboard: dashboardEn,
        auth: authEn,
        ai: aiEn,
        admin: adminEn,
        forum: forumEn,
        documents: documentsEn,
        errors: errorsEn,
        validation: validationEn,
      },
    },
fallbackLng: 'zh-CN',  // Default to Chinese if no language is set
    defaultNS: 'common',
    ns: [
      'common',
      'sidebar',
      'dashboard',
      'auth',
      'ai',
      'admin',
      'forum',
      'documents',
      'errors',
      'validation',
    ],
    interpolation: {
      escapeValue: false, // React already escapes
    },
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
      lookupLocalStorage: 'anylab_language',
    },
  });

export default i18n;

