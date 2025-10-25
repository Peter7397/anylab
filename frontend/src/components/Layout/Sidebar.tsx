import React, { useState, useEffect, useCallback } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
        Settings,
        MessageSquare,
        Wrench,
        ChevronLeft,
        ChevronRight,
        Monitor,
        AlertTriangle,
        Database,
        Home,
        Code,
        Search,
        Brain,
        Library,
        Activity,
        Network,
        Bell,
        Server,
        BarChart3,
        Zap,
        Users,
        Key,
        Calendar,
        FileText,
        Globe,
        Shield,
        FileSearch,
        FolderOpen,
        Share2,
        ChevronDown,
        ChevronRight as ChevronRightIcon,
        Download
} from 'lucide-react';

interface SidebarProps {
        collapsed: boolean;
        onToggle: () => void;
}

const navigation = [
        {
                name: 'Dashboard',
                href: '/',
                icon: Home,
        },
        {
                name: 'AI Assistant',
                href: '/ai/chat',
                icon: MessageSquare,
                children: [
                        { name: 'Free AI Chat', href: '/ai/chat', icon: MessageSquare },
                        { name: 'Basic RAG', href: '/ai/basic-rag', icon: Search },
                        { name: 'Advanced RAG', href: '/ai/rag', icon: Search },
                        { name: 'Comprehensive RAG', href: '/ai/comprehensive-rag', icon: Brain },
                ],
        },
        {
                name: 'Knowledge Library',
                href: '/ai/knowledge',
                icon: Library,
                children: [
                        { name: 'Document Viewer', href: '/ai/knowledge/viewer', icon: FileText },
                        { name: 'Document Manager', href: '/ai/knowledge/manager', icon: FolderOpen },
                        { name: 'Useful Links', href: '/ai/knowledge/links', icon: Globe },
                        { name: 'Sharing & Collaboration', href: '/ai/knowledge/sharing', icon: Share2 },
                ],
        },
        {
                name: 'System Monitoring',
                href: '/monitoring/enhanced',
                icon: Monitor,
                children: [
                        { name: 'Enhanced Dashboard', href: '/monitoring/enhanced', icon: BarChart3 },
                        { name: 'SysMon Agents', href: '/monitoring/sysmon-agents', icon: Monitor },
                        { name: 'Agent Deployment', href: '/monitoring/deployment', icon: Download },
                        { name: 'System Details', href: '/monitoring/system-detail', icon: Server },
                        { name: 'Performance', href: '/monitoring/performance', icon: Activity },
                        { name: 'Resources', href: '/monitoring/resources', icon: Zap },
                        { name: 'Network', href: '/monitoring/network', icon: Network },
                        { name: 'Processes', href: '/monitoring/processes', icon: Activity },
                        { name: 'Alerts', href: '/monitoring/alerts', icon: Bell },
                        { name: 'Events', href: '/monitoring/events', icon: FileSearch },
                ],
        },
        {
                name: 'Database Monitoring',
                href: '/database-monitoring/dashboard',
                icon: Database,
                children: [
                        { name: 'Dashboard', href: '/database-monitoring/dashboard', icon: BarChart3 },
                        { name: 'Databases', href: '/database-monitoring/databases', icon: Database },
                        { name: 'Performance', href: '/database-monitoring/performance', icon: Zap },
                        { name: 'Queries', href: '/database-monitoring/queries', icon: FileSearch },
                        { name: 'Connections', href: '/database-monitoring/connections', icon: Network },
                        { name: 'Tables', href: '/database-monitoring/tables', icon: FileText },
                        { name: 'Indexes', href: '/database-monitoring/indexes', icon: Shield },
                        { name: 'Backups', href: '/database-monitoring/backups', icon: Shield },
                        { name: 'Alerts', href: '/database-monitoring/alerts', icon: Bell },
                ],
        },
        {
                name: 'AppMon Monitoring',
                href: '/appmon/enhanced-dashboard',
                icon: Code,
                children: [
                        { name: 'Enhanced Dashboard', href: '/appmon/enhanced-dashboard', icon: BarChart3 },
                        { name: 'AppMon Agents', href: '/appmon/agents', icon: Monitor },
                        { name: 'File Monitoring', href: '/appmon/file-monitoring', icon: FileSearch },
                        { name: 'Performance Analytics', href: '/appmon/performance-analytics', icon: Activity },
                        { name: 'Alert Management', href: '/appmon/alerts', icon: Bell },
                ],
        },
        {
                name: 'Maintenance',
                href: '/maintenance/calendar',
                icon: Wrench,
                children: [
                        { name: 'Calendar', href: '/maintenance/calendar', icon: Calendar },
                        { name: 'SQL Health', href: '/maintenance/sql-health', icon: Database },
                ],
        },
        {
                name: 'Administration',
                href: '/admin/users',
                icon: Settings,
                children: [
                        { name: 'Users & Roles', href: '/admin/users', icon: Users },
                        { name: 'Licenses', href: '/admin/licenses', icon: Key },
                ],
        },
        {
                name: 'Troubleshooting',
                href: '/troubleshooting/overview',
                icon: AlertTriangle,
                children: [
                        { name: 'System Overview', href: '/troubleshooting/overview', icon: Monitor },
                        { name: 'Log Collection', href: '/troubleshooting/logs', icon: FileSearch },
                ],
        },
];

const Sidebar: React.FC<SidebarProps> = ({ collapsed, onToggle }) => {
        const location = useLocation();
        const [expandedItems, setExpandedItems] = useState<string[]>([]);

        const isActive = useCallback((href: string) => {
                return location.pathname === href;
        }, [location.pathname]);

        const hasActiveChild = useCallback((children: any[]) => {
                return children.some(child => isActive(child.href));
        }, [isActive]);

        const toggleExpanded = (itemName: string) => {
                setExpandedItems(prev => {
                        // If the clicked item is already expanded, close it
                        if (prev.includes(itemName)) {
                                return prev.filter(name => name !== itemName);
                        }
                        // If clicking on a different item, close all others and expand this one
                        return [itemName];
                });
        };

        const isExpanded = (itemName: string) => {
                // If the item is manually expanded, show it
                if (expandedItems.includes(itemName)) {
                        return true;
                }

                // If no item is manually expanded, show the item with active child
                if (expandedItems.length === 0) {
                        return hasActiveChild(navigation.find(item => item.name === itemName)?.children || []);
                }

                // If some item is manually expanded, only show that item
                return false;
        };

        // Auto-expand the item with active child only if no item is manually expanded
        useEffect(() => {
                const activeItem = navigation.find(item => 
                        item.children && hasActiveChild(item.children)
                );
                if (activeItem && expandedItems.length === 0) {
                        setExpandedItems([activeItem.name]);
                }
        }, [location.pathname, expandedItems, hasActiveChild]);

        return (
                <div className={`bg-white border-r border-gray-200 flex flex-col transition-all duration-300 ${
                        collapsed ? 'w-16' : 'w-64'
                }`}>
                        {/* Header */}
                        <div className="flex items-center justify-between p-4 border-b border-gray-200">
                                {!collapsed && (
                                        <div>
                                                <h1 className="text-xl font-bold text-gray-900">OnLab</h1>
                                                <p className="text-xs text-gray-500">One AI solution for every lab</p>
                                        </div>
                                )}
                                <button
                                        onClick={onToggle}
                                        className="p-1 rounded-md hover:bg-gray-100 transition-colors"
                                >
                                        {collapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
                                </button>
                        </div>

                        {/* Navigation */}
                        <nav className="flex-1 p-4 space-y-2">
                                {navigation.map((item) => {
                                        const Icon = item.icon;
                                        const isParentActive = item.children ? hasActiveChild(item.children) : isActive(item.href);

                                        const expanded = isExpanded(item.name);

                                        return (
                                                <div key={item.name} className="space-y-1">
                                                        {item.children ? (
                                                                <button
                                                                        onClick={() => toggleExpanded(item.name)}
                                                                        className={`sidebar-item w-full text-left cursor-pointer ${isParentActive ? 'sidebar-item-active' : 'sidebar-item-inactive'}`}
                                                                        type="button"
                                                                >
                                                                        <Icon size={20} className="mr-3" />
                                                                        {!collapsed && (
                                                                                <>
                                                                                        <span className="flex-1">{item.name}</span>
                                                                                        {expanded ? <ChevronDown size={16} /> : <ChevronRightIcon size={16} />}
                                                                                </>
                                                                        )}
                                                                </button>
                                                        ) : (
                                                                <Link
                                                                        to={item.href}
                                                                        className={`sidebar-item ${isActive(item.href || '') ? 'sidebar-item-active' : 'sidebar-item-inactive'}`}
                                                                >
                                                                        <Icon size={20} className="mr-3" />
                                                                        {!collapsed && <span>{item.name}</span>}
                                                                </Link>
                                                        )}

                                                        {!collapsed && item.children && expanded && (
                                                                <div className="ml-8 space-y-1">
                                                                        {item.children.map((child) => {
                                                                                const ChildIcon = child.icon;
                                                                                return (
                                                                                        <Link
                                                                                                key={child.name}
                                                                                                to={child.href}
                                                                                                className={`sidebar-item ${isActive(child.href) ? 'sidebar-item-active' : 'sidebar-item-inactive'}`}
                                                                                        >
                                                                                                <ChildIcon size={16} className="mr-2" />
                                                                                                {child.name}
                                                                                        </Link>
                                                                                );
                                                                        })}
                                                                </div>
                                                        )}
                                                </div>
                                        );
                                })}
                        </nav>
                </div>
        );
};

export default Sidebar; 