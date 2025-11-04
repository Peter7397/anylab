import React, { useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
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
  CheckCircle
} from 'lucide-react';

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  // Check if user is authenticated
  const token = localStorage.getItem(process.env.REACT_APP_JWT_STORAGE_KEY || 'anylab_token');
  const isAuthenticated = !!token;

  useEffect(() => {
    // If authenticated, redirect to dashboard
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  // Show loading state while redirecting authenticated users
  if (isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // Public landing page for unauthenticated users
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <div>
              <h1 className="text-2xl font-bold text-gray-900">AnyLab</h1>
              <span className="text-sm text-gray-500">AI Next to Your Lab</span>
              </div>
            </div>
            <Link
              to="/login"
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              <LogIn className="w-4 h-4" />
              Sign In
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-100 text-blue-700 rounded-full text-sm font-medium mb-6">
            <Sparkles className="w-4 h-4" />
            AI-Powered Laboratory Knowledge Platform
          </div>
          <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
            Centralize, Search, and
            <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent"> Collaborate</span>
          </h1>
          <p className="text-xl md:text-2xl text-gray-600 max-w-3xl mx-auto mb-8">
            Transform your laboratory documentation into an intelligent knowledge base. 
            Upload PDFs, search with AI-powered RAG, and get instant answers from your technical manuals, SOPs, and protocols.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/login"
              className="inline-flex items-center gap-2 px-8 py-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-lg shadow-lg"
            >
              Get Started
              <ArrowRight className="w-5 h-5" />
            </Link>
            <Link
              to="/forum"
              className="inline-flex items-center gap-2 px-8 py-4 bg-white text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium text-lg border border-gray-300"
            >
              Explore Forum
            </Link>
          </div>
        </div>

        {/* Feature Highlights Grid */}
        <div className="grid md:grid-cols-3 gap-6 mb-16">
          <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-8 hover:shadow-xl transition-shadow">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
              <Brain className="w-6 h-6 text-blue-600" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">AI-Powered Search</h3>
            <p className="text-gray-600">
              Advanced RAG with 4 search modes: Basic, Advanced, Comprehensive, and Graph RAG. 
              Get precise answers from your documentation.
            </p>
          </div>
          <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-8 hover:shadow-xl transition-shadow">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
              <Upload className="w-6 h-6 text-green-600" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">Document Management</h3>
            <p className="text-gray-600">
              Intelligent PDF processing with automatic chunking, embedding generation, 
              and vector storage for instant retrieval.
            </p>
          </div>
          <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-8 hover:shadow-xl transition-shadow">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
              <Database className="w-6 h-6 text-purple-600" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">Knowledge Library</h3>
            <p className="text-gray-600">
              Centralized repository for manuals, specs, protocols, and technical documentation 
              with smart categorization.
            </p>
          </div>
        </div>
      </section>

      {/* Main Features Section */}
      <section className="bg-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">Comprehensive Platform Features</h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Everything you need to manage laboratory knowledge and operations in one place
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* AI Assistant */}
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-200">
              <div className="flex items-center gap-3 mb-4">
                <Brain className="w-8 h-8 text-blue-600" />
                <h3 className="text-xl font-bold text-gray-900">AI Assistant</h3>
              </div>
              <p className="text-gray-700 mb-4">
                Chat with your documentation using advanced RAG technology. Get instant, 
                traceable answers from your knowledge base.
              </p>
              <ul className="space-y-2 text-sm text-gray-600">
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  Free AI Chat
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  4 RAG Search Modes
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  Graph RAG Support
                </li>
              </ul>
            </div>

            {/* Document Processing */}
            <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl p-6 border border-green-200">
              <div className="flex items-center gap-3 mb-4">
                <FileText className="w-8 h-8 text-green-600" />
                <h3 className="text-xl font-bold text-gray-900">Document Processing</h3>
              </div>
              <p className="text-gray-700 mb-4">
                Automated PDF processing with intelligent chunking, embedding generation, 
                and vector storage for optimal search performance.
              </p>
              <ul className="space-y-2 text-sm text-gray-600">
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  Auto-Extract Content
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  Smart Chunking
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  Vector Embeddings
                </li>
              </ul>
            </div>

            {/* Knowledge Library */}
            <div className="bg-gradient-to-br from-purple-50 to-violet-50 rounded-xl p-6 border border-purple-200">
              <div className="flex items-center gap-3 mb-4">
                <BookOpen className="w-8 h-8 text-purple-600" />
                <h3 className="text-xl font-bold text-gray-900">Knowledge Library</h3>
              </div>
              <p className="text-gray-700 mb-4">
                Centralized document management with advanced viewer, categorization, 
                and sharing capabilities.
              </p>
              <ul className="space-y-2 text-sm text-gray-600">
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  Document Viewer
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  Library Manager
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  Sharing & Collaboration
                </li>
              </ul>
            </div>

            {/* Troubleshooting */}
            <div className="bg-gradient-to-br from-orange-50 to-amber-50 rounded-xl p-6 border border-orange-200">
              <div className="flex items-center gap-3 mb-4">
                <AlertTriangle className="w-8 h-8 text-orange-600" />
                <h3 className="text-xl font-bold text-gray-900">Troubleshooting AI</h3>
              </div>
              <p className="text-gray-700 mb-4">
                AI-powered troubleshooting assistance using your documentation, 
                logs, and knowledge base for rapid problem resolution.
              </p>
              <ul className="space-y-2 text-sm text-gray-600">
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  Log Analysis
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  System Overview
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  Diagnostic Tools
                </li>
              </ul>
            </div>

            {/* Lab Informatics */}
            <div className="bg-gradient-to-br from-indigo-50 to-blue-50 rounded-xl p-6 border border-indigo-200">
              <div className="flex items-center gap-3 mb-4">
                <Database className="w-8 h-8 text-indigo-600" />
                <h3 className="text-xl font-bold text-gray-900">Lab Informatics</h3>
              </div>
              <p className="text-gray-700 mb-4">
                Specialized support for laboratory software suites with product-specific 
                documentation and knowledge bases.
              </p>
              <ul className="space-y-2 text-sm text-gray-600">
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  Product Manuals
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  SSB Database
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  Help Portal
                </li>
              </ul>
            </div>

            {/* Community Forum */}
            <div className="bg-gradient-to-br from-pink-50 to-rose-50 rounded-xl p-6 border border-pink-200">
              <div className="flex items-center gap-3 mb-4">
                <MessageSquare className="w-8 h-8 text-pink-600" />
                <h3 className="text-xl font-bold text-gray-900">Community Forum</h3>
              </div>
              <p className="text-gray-700 mb-4">
                Collaborate with your team, share knowledge, ask questions, and build 
                a collective knowledge base.
              </p>
              <ul className="space-y-2 text-sm text-gray-600">
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  Discussion Threads
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  Knowledge Sharing
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  Team Collaboration
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Technology Stack */}
      <section className="bg-gray-50 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">Powered by Advanced Technology</h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Built with cutting-edge AI and modern web technologies
            </p>
          </div>
          <div className="grid md:grid-cols-4 gap-6">
            <div className="bg-white rounded-lg p-6 text-center border border-gray-200">
              <Zap className="w-10 h-10 text-yellow-500 mx-auto mb-3" />
              <h4 className="font-semibold text-gray-900 mb-2">Ollama LLM</h4>
              <p className="text-sm text-gray-600">Qwen 2.5-7B Model</p>
            </div>
            <div className="bg-white rounded-lg p-6 text-center border border-gray-200">
              <Layers className="w-10 h-10 text-blue-500 mx-auto mb-3" />
              <h4 className="font-semibold text-gray-900 mb-2">pgvector</h4>
              <p className="text-sm text-gray-600">Vector Database</p>
            </div>
            <div className="bg-white rounded-lg p-6 text-center border border-gray-200">
              <Network className="w-10 h-10 text-purple-500 mx-auto mb-3" />
              <h4 className="font-semibold text-gray-900 mb-2">Hybrid Search</h4>
              <p className="text-sm text-gray-600">BM25 + Vector</p>
            </div>
            <div className="bg-white rounded-lg p-6 text-center border border-gray-200">
              <Shield className="w-10 h-10 text-green-500 mx-auto mb-3" />
              <h4 className="font-semibold text-gray-900 mb-2">Secure & Private</h4>
              <p className="text-sm text-gray-600">On-Premise Deployment</p>
            </div>
          </div>
        </div>
      </section>

        {/* CTA Section */}
      <section className="bg-gradient-to-r from-blue-600 to-indigo-600 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-4xl font-bold text-white mb-4">
            Ready to Transform Your Lab Knowledge Management?
          </h2>
          <p className="text-xl text-blue-100 mb-8 max-w-2xl mx-auto">
            Join teams who are already using AI to streamline documentation search, 
            improve troubleshooting, and enhance collaboration.
          </p>
          <Link
            to="/login"
            className="inline-flex items-center gap-2 px-8 py-4 bg-white text-blue-600 rounded-lg hover:bg-gray-50 transition-colors font-medium text-lg shadow-lg"
          >
            Get Started Free
            <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <Brain className="w-6 h-6 text-blue-400" />
                <span className="text-white font-bold text-lg">AnyLab</span>
              </div>
              <p className="text-sm">
                AI-powered laboratory knowledge management platform
              </p>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">Features</h4>
              <ul className="space-y-2 text-sm">
                <li><Link to="/forum" className="hover:text-white transition-colors">AI Assistant</Link></li>
                <li><Link to="/forum" className="hover:text-white transition-colors">Document Management</Link></li>
                <li><Link to="/forum" className="hover:text-white transition-colors">Knowledge Library</Link></li>
                <li><Link to="/forum" className="hover:text-white transition-colors">Troubleshooting</Link></li>
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
              <h4 className="text-white font-semibold mb-4">Get Started</h4>
              <Link
                to="/login"
                className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
              >
                Sign In
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
          <div className="mt-8 pt-8 border-t border-gray-800 text-center text-sm">
            <p>&copy; 2024 AnyLab. AI Next to Your Lab.</p>
        </div>
      </div>
      </footer>
    </div>
  );
};

export default HomePage;
