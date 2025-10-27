import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import Dashboard from './components/Dashboard/Dashboard';
import Login from './components/Auth/Login';
import UsersRoles from './components/Administration/UsersRoles';
import License from './components/Administration/License';
import Analytics from './components/Administration/Analytics';
import ChatAssistant from './components/AI/ChatAssistant';
import KnowledgeLibrary from './components/AI/KnowledgeLibrary';
import DocumentViewerPage from './components/AI/DocumentViewerPage';
import DocumentManagerPage from './components/AI/DocumentManagerPage';
import UsefulLinksPage from './components/AI/UsefulLinksPage';
import SharingCollaborationPage from './components/AI/SharingCollaborationPage';
import RagSearch from './components/AI/RagSearch';
import ComprehensiveRagSearch from './components/AI/ComprehensiveRagSearch';
import BasicRagSearch from './components/AI/BasicRagSearch';
import TroubleshootingAI from './components/AI/TroubleshootingAI';
import DocumentProcessing from './components/AI/DocumentProcessing';
import ScraperManagement from './components/Scrapers/ScraperManagement';
import SSBDatabase from './components/AI/SSBDatabase';
import SystemOverview from './components/Troubleshooting/SystemOverview';
import LogCollection from './components/Troubleshooting/LogCollection';
import ProductDocumentGrid from './components/Products/ProductDocumentGrid';

function App() {
        return (
                <Router>
                        <Routes>
                                {/* Public */}
                                <Route path="/login" element={<Login />} />

                                {/* App Shell */}
                                <Route element={<Layout />}>
                                        {/* Dashboard */}
                                        <Route path="/" element={<Dashboard />} />

                                {/* AI Assistant */}
                                <Route path="/ai/chat" element={<ChatAssistant />} />
                                <Route path="/ai/basic-rag" element={<BasicRagSearch />} />
                                <Route path="/ai/rag" element={<RagSearch />} />
                                <Route path="/ai/comprehensive-rag" element={<ComprehensiveRagSearch />} />
                                <Route path="/ai/troubleshooting" element={<TroubleshootingAI />} />
                                <Route path="/ai/processing" element={<DocumentProcessing />} />

                        {/* Knowledge Library */}
                        <Route path="/ai/knowledge" element={<KnowledgeLibrary />} />
                        <Route path="/ai/knowledge/viewer" element={<DocumentViewerPage />} />
                        <Route path="/ai/knowledge/manager" element={<DocumentManagerPage />} />
                        <Route path="/ai/knowledge/ssb" element={<SSBDatabase />} />
                        <Route path="/ai/knowledge/links" element={<UsefulLinksPage />} />
                        <Route path="/ai/knowledge/sharing" element={<SharingCollaborationPage />} />

                                {/* Troubleshooting */}
                                <Route path="/troubleshooting/overview" element={<SystemOverview />} />
                                <Route path="/troubleshooting/logs" element={<LogCollection />} />

                                {/* Scrapers */}
                                <Route path="/scrapers" element={<ScraperManagement />} />

                        {/* Administration */}
                        <Route path="/admin/users" element={<UsersRoles />} />
                        <Route path="/admin/analytics" element={<Analytics />} />
                        <Route path="/admin/licenses" element={<License />} />

                                        {/* Product Documentation */}
                                <Route path="/lab-informatics/:suite/:product" element={<ProductDocumentGrid />} />

                                        {/* Default route */}
                                        <Route path="*" element={<Dashboard />} />
                                </Route>
                        </Routes>
                </Router>
        );
}

export default App;
