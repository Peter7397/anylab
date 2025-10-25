import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import Dashboard from './components/Dashboard/Dashboard';
import Login from './components/Auth/Login';
import UsersRoles from './components/Administration/UsersRoles';
import License from './components/Administration/License';
import MonitoringDashboard from './components/Monitoring/MonitoringDashboard';
import SystemList from './components/Monitoring/SystemList';
import AlertList from './components/Monitoring/AlertList';
import EventLogViewer from './components/Monitoring/EventLogViewer';
import SystemPerformance from './components/Monitoring/SystemPerformance';
import SystemResources from './components/Monitoring/SystemResources';
import SystemNetwork from './components/Monitoring/SystemNetwork';
import SystemProcesses from './components/Monitoring/SystemProcesses';
import SystemMetrics from './components/Monitoring/SystemMetrics';
import ClientAgentDeployer from './components/Monitoring/ClientAgentDeployer';
import SysMonAgents from './components/Monitoring/SysMonAgents';
import AppMonAgents from './components/Monitoring/AppMonAgents';
import AppMonAlerts from './components/Monitoring/AppMonAlerts';
import DatabaseMonitoringDashboard from './components/Monitoring/DatabaseMonitoringDashboard';
import DatabaseList from './components/Monitoring/DatabaseList';
import DatabaseAlerts from './components/Monitoring/DatabaseAlerts';

import AppMonEnhancedDashboard from './components/Monitoring/AppMonEnhancedDashboard';
import AppMonFileMonitoring from './components/Monitoring/AppMonFileMonitoring';
import AppMonPerformanceAnalytics from './components/Monitoring/AppMonPerformanceAnalytics';
import ApplicationAlerts from './components/Monitoring/ApplicationAlerts';
import ChatAssistant from './components/AI/ChatAssistant';
import KnowledgeLibrary from './components/AI/KnowledgeLibrary';
import DocumentViewerPage from './components/AI/DocumentViewerPage';
import DocumentManagerPage from './components/AI/DocumentManagerPage';
import UsefulLinksPage from './components/AI/UsefulLinksPage';
import SharingCollaborationPage from './components/AI/SharingCollaborationPage';
import RagSearch from './components/AI/RagSearch';
import ComprehensiveRagSearch from './components/AI/ComprehensiveRagSearch';
import BasicRagSearch from './components/AI/BasicRagSearch';
import MaintenanceCalendar from './components/Maintenance/MaintenanceCalendar';
import SQLHealth from './components/Maintenance/SQLHealth';
import SystemOverview from './components/Troubleshooting/SystemOverview';
import LogCollection from './components/Troubleshooting/LogCollection';
import PlaceholderComponent from './components/Monitoring/PlaceholderComponent';

// Enhanced System Monitoring Components
import EnhancedSystemMonitoring from './components/Monitoring/EnhancedSystemMonitoring';
import SystemDetailView from './components/Monitoring/SystemDetailView';
import SysMonDeployment from './components/Monitoring/SysMonDeployment';

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

                                        {/* Knowledge Library */}
                                        <Route path="/ai/knowledge" element={<KnowledgeLibrary />} />
                                        <Route path="/ai/knowledge/viewer" element={<DocumentViewerPage />} />
                                        <Route path="/ai/knowledge/manager" element={<DocumentManagerPage />} />
                                        <Route path="/ai/knowledge/links" element={<UsefulLinksPage />} />
                                        <Route path="/ai/knowledge/sharing" element={<SharingCollaborationPage />} />

                                        {/* Enhanced System Monitoring */}
                                        <Route path="/monitoring/enhanced" element={<EnhancedSystemMonitoring />} />
                                        <Route path="/monitoring/system-detail/:hostname" element={<SystemDetailView />} />
                                        <Route path="/monitoring/deployment" element={<SysMonDeployment />} />
                                        
                                        {/* Legacy System Monitoring */}
                                        <Route path="/monitoring/dashboard" element={<MonitoringDashboard />} />
                                        <Route path="/monitoring/systems" element={<SystemList />} />
                                        <Route path="/monitoring/sysmon-agents" element={<SysMonAgents />} />
                                        <Route path="/monitoring/performance" element={<SystemPerformance />} />
                                        <Route path="/monitoring/resources" element={<SystemResources />} />
                                        <Route path="/monitoring/network" element={<SystemNetwork />} />
                                        <Route path="/monitoring/processes" element={<SystemProcesses />} />
                                        <Route path="/monitoring/alerts" element={<AlertList />} />
                                        <Route path="/monitoring/events" element={<EventLogViewer />} />
                                        <Route path="/monitoring/metrics" element={<SystemMetrics />} />
                                        <Route path="/monitoring/deploy-agent" element={<ClientAgentDeployer />} />

                                        {/* Database Monitoring */}
                                        <Route path="/database-monitoring/dashboard" element={<DatabaseMonitoringDashboard />} />
                                        <Route path="/database-monitoring/databases" element={<DatabaseList />} />
                                        <Route path="/database-monitoring/performance" element={<PlaceholderComponent title="Database Performance" description="Database performance monitoring and optimization tools." />} />
                                        <Route path="/database-monitoring/queries" element={<PlaceholderComponent title="Database Queries" description="Monitor and analyze database query performance." />} />
                                        <Route path="/database-monitoring/connections" element={<PlaceholderComponent title="Database Connections" description="Track active database connections and connection pools." />} />
                                        <Route path="/database-monitoring/tables" element={<PlaceholderComponent title="Database Tables" description="Monitor table sizes, indexes, and performance metrics." />} />
                                        <Route path="/database-monitoring/indexes" element={<PlaceholderComponent title="Database Indexes" description="Analyze index usage and performance." />} />
                                        <Route path="/database-monitoring/backups" element={<PlaceholderComponent title="Database Backups" description="Monitor backup status and schedules." />} />
                                        <Route path="/database-monitoring/alerts" element={<DatabaseAlerts />} />

                                        {/* AppMon Monitoring */}
                                        <Route path="/appmon/enhanced-dashboard" element={<AppMonEnhancedDashboard />} />
                                        <Route path="/appmon/agents" element={<AppMonAgents />} />
                                        <Route path="/appmon/file-monitoring" element={<AppMonFileMonitoring />} />
                                        <Route path="/appmon/performance-analytics" element={<AppMonPerformanceAnalytics />} />
                                        <Route path="/appmon/alerts" element={<ApplicationAlerts />} />

                                        {/* Maintenance */}
                                        <Route path="/maintenance/calendar" element={<MaintenanceCalendar />} />
                                        <Route path="/maintenance/sql-health" element={<SQLHealth />} />

                                        {/* Administration */}
                                        <Route path="/admin/users" element={<UsersRoles />} />
                                        <Route path="/admin/licenses" element={<License />} />

                                        {/* Troubleshooting */}
                                        <Route path="/troubleshooting/overview" element={<SystemOverview />} />
                                        <Route path="/troubleshooting/logs" element={<LogCollection />} />

                                        {/* Default route */}
                                        <Route path="*" element={<Dashboard />} />
                                </Route>
                        </Routes>
                </Router>
        );
}

export default App;
