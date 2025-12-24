import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './i18n/config'; // Initialize i18n
import Layout from './components/Layout/Layout';
import Dashboard from './components/Dashboard/Dashboard';
import Login from './components/Auth/Login';
import UsersRoles from './components/Administration/UsersRoles';
import License from './components/Administration/License';
import Analytics from './components/Administration/Analytics';
import SystemSettings from './components/Administration/SystemSettings';
import ChatAssistant from './components/AI/ChatAssistant';
import KnowledgeLibrary from './components/AI/KnowledgeLibrary';
import DocumentViewerPage from './components/AI/DocumentViewerPage';
import DocumentManagerPage from './components/AI/DocumentManagerPage';
import UsefulLinksPage from './components/AI/UsefulLinksPage';
import SharingCollaborationPage from './components/AI/SharingCollaborationPage';
import RagSearch from './components/AI/RagSearch';
import ComprehensiveRagSearch from './components/AI/ComprehensiveRagSearch';
import GraphRagSearch from './components/AI/GraphRagSearch';
import BasicRagSearch from './components/AI/BasicRagSearch';
import TroubleshootingAI from './components/AI/TroubleshootingAI';
import DocumentProcessing from './components/AI/DocumentProcessing';
import ScraperManagement from './components/Scrapers/ScraperManagement';
import SSBDatabase from './components/AI/SSBDatabase';
import SystemOverview from './components/Troubleshooting/SystemOverview';
import LogCollection from './components/Troubleshooting/LogCollection';
import ProductDocumentGrid from './components/Products/ProductDocumentGrid';
import HelpPortal from './components/AI/HelpPortal';
import Forum from './components/Forum/Forum';
import ForumPost from './components/Forum/ForumPost';
import PostEditor from './components/Forum/PostEditor';
import HomePage from './components/Home/HomePage';
import Profile from './components/User/Profile';
import Settings from './components/User/Settings';
import { AuthProvider } from './context/AuthContext';
import RequireFeature from './components/Auth/RequireFeature';

function App() {
        return (
                <AuthProvider>
                <Router>
                        <Routes>
                                {/* Public Routes */}
                                <Route path="/login" element={<Login />} />
                                
                                {/* Public Homepage */}
                                <Route path="/" element={<HomePage />} />
                                
                                {/* App Shell - Layout with Sidebar (some routes require auth, forum is public) */}
                                <Route element={<Layout />}>
                                        {/* Public Forum Routes (in Layout so they have sidebar) */}
                                        <Route path="/forum" element={<Forum />} />
                                        <Route path="/forum/post/:id" element={<ForumPost />} />
                                        {/* Dashboard (redirects from / to /dashboard if authenticated) */}
                                        <Route path="/dashboard" element={<Dashboard />} />

                                        {/* User Profile and Settings */}
                                        <Route path="/profile" element={<Profile />} />
                                        <Route path="/settings" element={<Settings />} />

                                {/* AI Assistant (requires ai.rag) */}
                                <Route path="/ai/chat" element={<RequireFeature feature="ai.rag"><ChatAssistant /></RequireFeature>} />
                                <Route path="/ai/basic-rag" element={<RequireFeature feature="ai.rag"><BasicRagSearch /></RequireFeature>} />
                                <Route path="/ai/rag" element={<RequireFeature feature="ai.rag"><RagSearch /></RequireFeature>} />
                                <Route path="/ai/comprehensive-rag" element={<RequireFeature feature="ai.rag"><ComprehensiveRagSearch /></RequireFeature>} />
                                <Route path="/ai/graph-rag" element={<RequireFeature feature="ai.rag"><GraphRagSearch /></RequireFeature>} />
                                <Route path="/ai/troubleshooting" element={<RequireFeature feature="knowledge.view"><TroubleshootingAI /></RequireFeature>} />
                                <Route path="/ai/processing" element={<RequireFeature feature="knowledge.view"><DocumentProcessing /></RequireFeature>} />

                        {/* Knowledge Library (requires knowledge.view) */}
                        <Route path="/ai/knowledge" element={<RequireFeature feature="knowledge.view"><KnowledgeLibrary /></RequireFeature>} />
                        <Route path="/ai/knowledge/viewer" element={<RequireFeature feature="knowledge.view"><DocumentViewerPage /></RequireFeature>} />
                        <Route path="/ai/viewer" element={<RequireFeature feature="knowledge.view"><DocumentViewerPage /></RequireFeature>} />
                        <Route path="/ai/knowledge/manager" element={<RequireFeature feature="knowledge.view"><DocumentManagerPage /></RequireFeature>} />
                        <Route path="/ai/knowledge/ssb" element={<RequireFeature feature="knowledge.view"><SSBDatabase /></RequireFeature>} />
                        <Route path="/ai/knowledge/help-portal" element={<RequireFeature feature="knowledge.view"><HelpPortal /></RequireFeature>} />
                        <Route path="/ai/knowledge/links" element={<RequireFeature feature="knowledge.view"><UsefulLinksPage /></RequireFeature>} />
                        <Route path="/ai/knowledge/sharing" element={<RequireFeature feature="knowledge.view"><SharingCollaborationPage /></RequireFeature>} />

                                {/* Troubleshooting (requires knowledge.view) */}
                                <Route path="/troubleshooting/overview" element={<RequireFeature feature="knowledge.view"><SystemOverview /></RequireFeature>} />
                                <Route path="/troubleshooting/logs" element={<RequireFeature feature="knowledge.view"><LogCollection /></RequireFeature>} />

                                {/* Scrapers (requires knowledge.view) */}
                                <Route path="/scrapers" element={<RequireFeature feature="knowledge.view"><ScraperManagement /></RequireFeature>} />

                        {/* Administration (requires admin) */}
                        <Route path="/admin/users" element={<RequireFeature feature="admin"><UsersRoles /></RequireFeature>} />
                        <Route path="/admin/analytics" element={<RequireFeature feature="admin"><Analytics /></RequireFeature>} />
                        <Route path="/admin/licenses" element={<RequireFeature feature="admin"><License /></RequireFeature>} />
                        <Route path="/admin/system" element={<RequireFeature feature="admin"><SystemSettings /></RequireFeature>} />

                                        {/* Product Documentation */}
                                <Route path="/lab-informatics/:suite/:product" element={<RequireFeature feature="knowledge.view"><ProductDocumentGrid /></RequireFeature>} />

                                        {/* Forum (authenticated routes) */}
                                <Route path="/forum/new" element={<PostEditor />} />
                                <Route path="/forum/post/:id/edit" element={<PostEditor />} />

                                        {/* Default route */}
                                        <Route path="*" element={<Dashboard />} />
                                </Route>
                        </Routes>
                </Router>
                </AuthProvider>
        );
}

export default App;
