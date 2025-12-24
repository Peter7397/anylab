import React, { useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { 
  LogIn, 
  Brain, 
  BookOpen, 
  Search, 
  FileText, 
  Database, 
  Sparkles,
  Layers,
  Network,
  AlertTriangle,
  Upload,
  Zap,
  Shield,
  Users,
  MessageSquare,
  BarChart3,
  Settings,
  ArrowRight,
  CheckCircle,
  Globe,
  Webhook
} from 'lucide-react';
import LanguageSwitcher from '../Layout/LanguageSwitcher';

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation('common');
  // Check if user is authenticated
  const token = localStorage.getItem(process.env.REACT_APP_JWT_STORAGE_KEY || 'anylab_token');
  const isAuthenticated = !!token;

  // Public landing page for unauthenticated users
  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-primary-600 to-teal-600 rounded-lg flex items-center justify-center">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">AnyLab</h1>
                <span className="text-sm text-gray-500">{t('homepage.tagline')}</span>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <LanguageSwitcher />
              {isAuthenticated ? (
                <Link
                  to="/dashboard"
                  className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium"
                >
                  <ArrowRight className="w-4 h-4 rotate-180" />
                  {t('dashboard')}
                </Link>
              ) : (
                <Link
                  to="/login"
                  className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium"
                >
                  <LogIn className="w-4 h-4" />
                  {t('homepage.signIn')}
                </Link>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary-100 text-primary-700 rounded-full text-sm font-medium mb-6">
            <Sparkles className="w-4 h-4" />
            {t('homepage.heroSubtitle')}
          </div>
          <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
            {t('homepage.heroTitle')}
            <span className="bg-gradient-to-r from-primary-600 to-teal-600 bg-clip-text text-transparent"> {t('homepage.heroTitleHighlight')}</span>
          </h1>
          <p className="text-xl md:text-2xl text-gray-600 max-w-3xl mx-auto mb-8">
            {t('homepage.heroDescription')}
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            {isAuthenticated ? (
              <>
                <Link
                  to="/dashboard"
                  className="inline-flex items-center gap-2 px-8 py-4 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium text-lg shadow-lg"
                >
                  {t('dashboard')}
                  <ArrowRight className="w-5 h-5" />
                </Link>
                <Link
                  to="/ai/chat"
                  className="inline-flex items-center gap-2 px-8 py-4 bg-white text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium text-lg border border-gray-300"
                >
                  {t('aiAssistant')}
                  <ArrowRight className="w-5 h-5" />
                </Link>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  className="inline-flex items-center gap-2 px-8 py-4 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium text-lg shadow-lg"
                >
                  {t('homepage.getStarted')}
                  <ArrowRight className="w-5 h-5" />
                </Link>
                <Link
                  to="/forum"
                  className="inline-flex items-center gap-2 px-8 py-4 bg-white text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium text-lg border border-gray-300"
                >
                  {t('homepage.exploreForum')}
                </Link>
              </>
            )}
          </div>
        </div>
      </section>

      {/* Main Features Section */}
      <section className="bg-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">{t('homepage.featuresTitle')}</h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              {t('homepage.featuresSubtitle')}
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* AI Assistant */}
            <div className="bg-gradient-to-br from-emerald-50 to-teal-50 rounded-xl p-6 border border-emerald-200">
              <div className="flex items-center gap-3 mb-4">
                <Brain className="w-8 h-8 text-emerald-600" />
                <h3 className="text-xl font-bold text-gray-900">{t('homepage.features.aiAssistant.title')}</h3>
              </div>
              <p className="text-gray-700 mb-4">
                {t('homepage.features.aiAssistant.description')}
              </p>
              <ul className="space-y-2 text-sm text-gray-600">
                {(t('homepage.features.aiAssistant.items', { returnObjects: true }) as string[]).map((item: string, index: number) => (
                  <li key={index} className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-green-600" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>

            {/* Document Processing */}
            <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl p-6 border border-green-200">
              <div className="flex items-center gap-3 mb-4">
                <FileText className="w-8 h-8 text-green-600" />
                <h3 className="text-xl font-bold text-gray-900">{t('homepage.features.documentProcessing.title')}</h3>
              </div>
              <p className="text-gray-700 mb-4">
                {t('homepage.features.documentProcessing.description')}
              </p>
              <ul className="space-y-2 text-sm text-gray-600">
                {(t('homepage.features.documentProcessing.items', { returnObjects: true }) as string[]).map((item: string, index: number) => (
                  <li key={index} className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-green-600" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>

            {/* Knowledge Library */}
            <div className="bg-gradient-to-br from-lime-50 to-emerald-50 rounded-xl p-6 border border-lime-200">
              <div className="flex items-center gap-3 mb-4">
                <BookOpen className="w-8 h-8 text-lime-600" />
                <h3 className="text-xl font-bold text-gray-900">{t('homepage.features.knowledgeLibrary.title')}</h3>
              </div>
              <p className="text-gray-700 mb-4">
                {t('homepage.features.knowledgeLibrary.description')}
              </p>
              <ul className="space-y-2 text-sm text-gray-600">
                {(t('homepage.features.knowledgeLibrary.items', { returnObjects: true }) as string[]).map((item: string, index: number) => (
                  <li key={index} className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-green-600" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>

            {/* Troubleshooting */}
            <div className="bg-gradient-to-br from-orange-50 to-amber-50 rounded-xl p-6 border border-orange-200">
              <div className="flex items-center gap-3 mb-4">
                <AlertTriangle className="w-8 h-8 text-orange-600" />
                <h3 className="text-xl font-bold text-gray-900">{t('homepage.features.troubleshooting.title')}</h3>
              </div>
              <p className="text-gray-700 mb-4">
                {t('homepage.features.troubleshooting.description')}
              </p>
              <ul className="space-y-2 text-sm text-gray-600">
                {(t('homepage.features.troubleshooting.items', { returnObjects: true }) as string[]).map((item: string, index: number) => (
                  <li key={index} className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-green-600" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>

            {/* Lab Informatics */}
            <div className="bg-gradient-to-br from-teal-50 to-emerald-50 rounded-xl p-6 border border-teal-200">
              <div className="flex items-center gap-3 mb-4">
                <Database className="w-8 h-8 text-teal-600" />
                <h3 className="text-xl font-bold text-gray-900">{t('homepage.features.labInformatics.title')}</h3>
              </div>
              <p className="text-gray-700 mb-4">
                {t('homepage.features.labInformatics.description')}
              </p>
              <ul className="space-y-2 text-sm text-gray-600">
                {(t('homepage.features.labInformatics.items', { returnObjects: true }) as string[]).map((item: string, index: number) => (
                  <li key={index} className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-green-600" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>

            {/* Community Forum */}
            <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl p-6 border border-green-200">
              <div className="flex items-center gap-3 mb-4">
                <MessageSquare className="w-8 h-8 text-green-600" />
                <h3 className="text-xl font-bold text-gray-900">{t('homepage.features.communityForum.title')}</h3>
              </div>
              <p className="text-gray-700 mb-4">
                {t('homepage.features.communityForum.description')}
              </p>
              <ul className="space-y-2 text-sm text-gray-600">
                {(t('homepage.features.communityForum.items', { returnObjects: true }) as string[]).map((item: string, index: number) => (
                  <li key={index} className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-green-600" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>

            {/* Scraper Management */}
            <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-xl p-6 border border-blue-200">
              <div className="flex items-center gap-3 mb-4">
                <Webhook className="w-8 h-8 text-blue-600" />
                <h3 className="text-xl font-bold text-gray-900">{t('homepage.features.scraperManagement.title')}</h3>
              </div>
              <p className="text-gray-700 mb-4">
                {t('homepage.features.scraperManagement.description')}
              </p>
              <ul className="space-y-2 text-sm text-gray-600">
                {(t('homepage.features.scraperManagement.items', { returnObjects: true }) as string[]).map((item: string, index: number) => (
                  <li key={index} className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-green-600" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>

            {/* Analytics */}
            <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-6 border border-purple-200">
              <div className="flex items-center gap-3 mb-4">
                <BarChart3 className="w-8 h-8 text-purple-600" />
                <h3 className="text-xl font-bold text-gray-900">{t('homepage.features.analytics.title')}</h3>
              </div>
              <p className="text-gray-700 mb-4">
                {t('homepage.features.analytics.description')}
              </p>
              <ul className="space-y-2 text-sm text-gray-600">
                {(t('homepage.features.analytics.items', { returnObjects: true }) as string[]).map((item: string, index: number) => (
                  <li key={index} className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-green-600" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>

            {/* Administration */}
            <div className="bg-gradient-to-br from-indigo-50 to-blue-50 rounded-xl p-6 border border-indigo-200">
              <div className="flex items-center gap-3 mb-4">
                <Settings className="w-8 h-8 text-indigo-600" />
                <h3 className="text-xl font-bold text-gray-900">{t('homepage.features.administration.title')}</h3>
              </div>
              <p className="text-gray-700 mb-4">
                {t('homepage.features.administration.description')}
              </p>
              <ul className="space-y-2 text-sm text-gray-600">
                {(t('homepage.features.administration.items', { returnObjects: true }) as string[]).map((item: string, index: number) => (
                  <li key={index} className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-green-600" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Technology Stack */}
      <section className="bg-gray-50 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">{t('homepage.techTitle')}</h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              {t('homepage.techSubtitle')}
            </p>
          </div>
          <div className="grid md:grid-cols-4 gap-6">
            <div className="bg-white rounded-lg p-6 text-center border border-gray-200">
              <Zap className="w-10 h-10 text-yellow-500 mx-auto mb-3" />
              <h4 className="font-semibold text-gray-900 mb-2">{t('homepage.tech.ollama')}</h4>
              <p className="text-sm text-gray-600">{t('homepage.tech.ollamaDesc')}</p>
            </div>
            <div className="bg-white rounded-lg p-6 text-center border border-gray-200">
              <Layers className="w-10 h-10 text-primary-500 mx-auto mb-3" />
              <h4 className="font-semibold text-gray-900 mb-2">{t('homepage.tech.pgvector')}</h4>
              <p className="text-sm text-gray-600">{t('homepage.tech.pgvectorDesc')}</p>
            </div>
            <div className="bg-white rounded-lg p-6 text-center border border-gray-200">
              <Network className="w-10 h-10 text-lime-500 mx-auto mb-3" />
              <h4 className="font-semibold text-gray-900 mb-2">{t('homepage.tech.hybridSearch')}</h4>
              <p className="text-sm text-gray-600">{t('homepage.tech.hybridSearchDesc')}</p>
            </div>
            <div className="bg-white rounded-lg p-6 text-center border border-gray-200">
              <Shield className="w-10 h-10 text-green-500 mx-auto mb-3" />
              <h4 className="font-semibold text-gray-900 mb-2">{t('homepage.tech.secure')}</h4>
              <p className="text-sm text-gray-600">{t('homepage.tech.secureDesc')}</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-gradient-to-r from-primary-600 to-teal-600 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-4xl font-bold text-white mb-4">
            {t('homepage.ctaTitle')}
          </h2>
          <p className="text-xl text-emerald-100 mb-8 max-w-2xl mx-auto">
            {t('homepage.ctaDescription')}
          </p>
          {isAuthenticated ? (
            <Link
              to="/dashboard"
              className="inline-flex items-center gap-2 px-8 py-4 bg-white text-primary-600 rounded-lg hover:bg-gray-50 transition-colors font-medium text-lg shadow-lg"
            >
              {t('dashboard')}
              <ArrowRight className="w-5 h-5" />
            </Link>
          ) : (
            <Link
              to="/login"
              className="inline-flex items-center gap-2 px-8 py-4 bg-white text-primary-600 rounded-lg hover:bg-gray-50 transition-colors font-medium text-lg shadow-lg"
            >
              {t('homepage.ctaButton')}
              <ArrowRight className="w-5 h-5" />
            </Link>
          )}
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <Brain className="w-6 h-6 text-emerald-400" />
                <span className="text-white font-bold text-lg">AnyLab</span>
              </div>
              <p className="text-sm">
                {t('homepage.footerTagline')}
              </p>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">{t('homepage.featuresTitle')}</h4>
              <ul className="space-y-2 text-sm">
                <li><Link to="/forum" className="hover:text-white transition-colors">{t('homepage.features.aiAssistant.title')}</Link></li>
                <li><Link to="/forum" className="hover:text-white transition-colors">{t('homepage.features.documentProcessing.title')}</Link></li>
                <li><Link to="/forum" className="hover:text-white transition-colors">{t('homepage.features.knowledgeLibrary.title')}</Link></li>
                <li><Link to="/forum" className="hover:text-white transition-colors">{t('homepage.features.troubleshooting.title')}</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">Resources</h4>
              <ul className="space-y-2 text-sm">
                <li><Link to="/forum" className="hover:text-white transition-colors">Forum</Link></li>
                <li><Link to="/forum" className="hover:text-white transition-colors">Documentation</Link></li>
                <li><Link to="/forum" className="hover:text-white transition-colors">Support</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">{isAuthenticated ? t('dashboard') : t('homepage.getStarted')}</h4>
              {isAuthenticated ? (
                <Link
                  to="/dashboard"
                  className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors text-sm font-medium"
                >
                  {t('dashboard')}
                  <ArrowRight className="w-4 h-4" />
                </Link>
              ) : (
                <Link
                  to="/login"
                  className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors text-sm font-medium"
                >
                  {t('homepage.signIn')}
                  <ArrowRight className="w-4 h-4" />
                </Link>
              )}
            </div>
          </div>
          <div className="mt-8 pt-8 border-t border-gray-800 text-center text-sm">
            <p>{t('homepage.footerCopyright')}</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default HomePage;
