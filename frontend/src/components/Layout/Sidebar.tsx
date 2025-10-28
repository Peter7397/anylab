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
        Download,
        FlaskConical,
        Cpu,
        ToggleLeft,
        ToggleRight
} from 'lucide-react';

interface SidebarProps {
        collapsed: boolean;
        onToggle: () => void;
}

type OrganizationMode = 'general' | 'lab-informatics';

const generalAgilentNavigation = [
        {
                name: 'Dashboard',
                href: '/',
                icon: Home,
        },
        {
                name: 'Knowledge Library',
                href: '/ai/knowledge',
                icon: Library,
                children: [
                        { name: 'Library Manager', href: '/ai/knowledge/manager', icon: FolderOpen },
                        { name: 'Product Manuals', href: '/ai/knowledge/manuals', icon: FileText },
                        { name: 'Technical Specs', href: '/ai/knowledge/specs', icon: FileText },
                        { name: 'Community Solutions', href: '/ai/knowledge/community', icon: Users },
                        { name: 'Document Viewer', href: '/ai/knowledge/viewer', icon: FileText },
                ],
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
                        { name: 'Troubleshooting AI', href: '/ai/troubleshooting', icon: AlertTriangle },
                ],
        },
        {
                name: 'Gas Chromatography',
                href: '/products/gc',
                icon: FlaskConical,
                children: [
                        { name: 'GC Systems', href: '/products/gc/systems', icon: FlaskConical },
                        { name: 'GC Columns', href: '/products/gc/columns', icon: FlaskConical },
                        { name: 'GC Accessories', href: '/products/gc/accessories', icon: FlaskConical },
                        { name: 'GC Software', href: '/products/gc/software', icon: Code },
                ],
        },
        {
                name: 'Liquid Chromatography',
                href: '/products/lc',
                icon: FlaskConical,
                children: [
                        { name: 'LC Systems', href: '/products/lc/systems', icon: FlaskConical },
                        { name: 'LC Columns', href: '/products/lc/columns', icon: FlaskConical },
                        { name: 'LC Accessories', href: '/products/lc/accessories', icon: FlaskConical },
                        { name: 'LC Software', href: '/products/lc/software', icon: Code },
                ],
        },
        {
                name: 'Mass Spectrometry',
                href: '/products/ms',
                icon: Cpu,
                children: [
                        { name: 'MS Systems', href: '/products/ms/systems', icon: Cpu },
                        { name: 'MS Software', href: '/products/ms/software', icon: Code },
                        { name: 'MS Accessories', href: '/products/ms/accessories', icon: Cpu },
                ],
        },
        {
                name: 'NMR Systems',
                href: '/products/nmr',
                icon: Cpu,
                children: [
                        { name: 'NMR Systems', href: '/products/nmr/systems', icon: Cpu },
                        { name: 'NMR Software', href: '/products/nmr/software', icon: Code },
                        { name: 'NMR Accessories', href: '/products/nmr/accessories', icon: Cpu },
                ],
        },
        {
                name: 'Spectroscopy',
                href: '/products/spectroscopy',
                icon: Cpu,
                children: [
                        { name: 'UV-Vis', href: '/products/spectroscopy/uv-vis', icon: Cpu },
                        { name: 'IR', href: '/products/spectroscopy/ir', icon: Cpu },
                        { name: 'Fluorescence', href: '/products/spectroscopy/fluorescence', icon: Cpu },
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
];

const labInformaticsNavigation = [
        {
                name: 'Dashboard',
                href: '/',
                icon: Home,
        },
        {
                name: 'Knowledge Library',
                href: '/ai/knowledge',
                icon: Library,
                children: [
                        { name: 'Library Manager', href: '/ai/knowledge/manager', icon: FolderOpen },
                        { name: 'SSB Database', href: '/ai/knowledge/ssb', icon: Database },
                        { name: 'Help Portal', href: '/ai/knowledge/help-portal', icon: Globe },
                        { name: 'Community Solutions', href: '/ai/knowledge/community', icon: Users },
                        { name: 'Document Viewer', href: '/ai/knowledge/viewer', icon: FileText },
                ],
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
                        { name: 'Troubleshooting AI', href: '/ai/troubleshooting', icon: AlertTriangle },
                ],
        },
        {
                name: 'OpenLab Software Suite',
                href: '/lab-informatics/openlab',
                icon: Code,
                children: [
                        { name: 'OpenLab CDS', href: '/lab-informatics/openlab/cds', icon: Code },
                        { name: 'OpenLab ECM', href: '/lab-informatics/openlab/ecm', icon: Database },
                        { name: 'OpenLab ELN', href: '/lab-informatics/openlab/eln', icon: FileText },
                        { name: 'OpenLab Server', href: '/lab-informatics/openlab/server', icon: Server },
                ],
        },
        {
                name: 'MassHunter Suite',
                href: '/lab-informatics/masshunter',
                icon: Cpu,
                children: [
                        { name: 'MassHunter Workstation', href: '/lab-informatics/masshunter/workstation', icon: Cpu },
                        { name: 'MassHunter Quantitative', href: '/lab-informatics/masshunter/quantitative', icon: BarChart3 },
                        { name: 'MassHunter Qualitative', href: '/lab-informatics/masshunter/qualitative', icon: Search },
                        { name: 'MassHunter BioConfirm', href: '/lab-informatics/masshunter/bioconfirm', icon: Brain },
                        { name: 'MassHunter Metabolomics', href: '/lab-informatics/masshunter/metabolomics', icon: Activity },
                ],
        },
        {
                name: 'VNMRJ Software',
                href: '/lab-informatics/vnmrj',
                icon: Cpu,
                children: [
                        { name: 'VNMRJ Current', href: '/lab-informatics/vnmrj/current', icon: Cpu },
                        { name: 'VNMRJ Legacy', href: '/lab-informatics/vnmrj/legacy', icon: Cpu },
                        { name: 'VNMR Legacy', href: '/lab-informatics/vnmrj/vnmr-legacy', icon: Cpu },
                ],
        },
        {
                name: 'Troubleshooting',
                href: '/troubleshooting/overview',
                icon: AlertTriangle,
                children: [
                        { name: 'Critical Issues', href: '/troubleshooting/critical', icon: AlertTriangle },
                        { name: 'Common Issues', href: '/troubleshooting/common', icon: Monitor },
                        { name: 'Error Codes', href: '/troubleshooting/error-codes', icon: FileSearch },
                        { name: 'KPR Database', href: '/troubleshooting/kpr', icon: Database },
                        { name: 'Solution Finder', href: '/troubleshooting/solutions', icon: Search },
                ],
        },
        {
                name: 'Administration',
                href: '/admin/users',
                icon: Settings,
                children: [
                        { name: 'Users & Roles', href: '/admin/users', icon: Users },
                        { name: 'Licenses', href: '/admin/licenses', icon: Key },
                        { name: 'System Settings', href: '/admin/system', icon: Settings },
                ],
        },
];

const Sidebar: React.FC<SidebarProps> = ({ collapsed, onToggle }) => {
        const location = useLocation();
        const [expandedItems, setExpandedItems] = useState<string[]>([]);
        const [organizationMode, setOrganizationMode] = useState<OrganizationMode>(() => {
                const saved = localStorage.getItem('anylab_organization_mode');
                return (saved as OrganizationMode) || 'general';
        });

        // Save mode preference to localStorage
        useEffect(() => {
                localStorage.setItem('anylab_organization_mode', organizationMode);
        }, [organizationMode]);

        const toggleOrganizationMode = () => {
                setOrganizationMode(prev => prev === 'general' ? 'lab-informatics' : 'general');
        };

        const navigation = organizationMode === 'general' ? generalAgilentNavigation : labInformaticsNavigation;

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
                                                <h1 className="text-xl font-bold text-gray-900">AnyLab</h1>
                                                <p className="text-xs text-gray-500">AI eNlighteN Your Lab</p>
                                        </div>
                                )}
                                <button
                                        onClick={onToggle}
                                        className="p-1 rounded-md hover:bg-gray-100 transition-colors"
                                >
                                        {collapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
                                </button>
                        </div>

                        {/* Mode Toggle */}
                        {!collapsed && (
                                <div className="p-4 border-b border-gray-200">
                                        <div className="flex items-center justify-between">
                                                <div className="flex flex-col">
                                                        <span className="text-sm font-medium text-gray-700">
                                                                Organization Mode
                                                        </span>
                                                        <span className="text-xs text-gray-500">
                                                                {organizationMode === 'general' ? 'General Agilent Products' : 'Lab Informatics Focus'}
                                                        </span>
                                                </div>
                                                <button
                                                        onClick={toggleOrganizationMode}
                                                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                                                                organizationMode === 'lab-informatics' 
                                                                        ? 'bg-blue-600' 
                                                                        : 'bg-gray-200'
                                                        }`}
                                                >
                                                        <span
                                                                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                                                                        organizationMode === 'lab-informatics' 
                                                                                ? 'translate-x-6' 
                                                                                : 'translate-x-1'
                                                                }`}
                                                        />
                                                </button>
                                        </div>
                                </div>
                        )}

                        {/* Collapsed Mode Toggle */}
                        {collapsed && (
                                <div className="p-2 border-b border-gray-200">
                                        <button
                                                onClick={toggleOrganizationMode}
                                                className="w-full p-2 rounded-md hover:bg-gray-100 transition-colors flex items-center justify-center"
                                                title={organizationMode === 'general' ? 'Switch to Lab Informatics' : 'Switch to General Agilent'}
                                        >
                                                {organizationMode === 'general' ? (
                                                        <FlaskConical size={20} className="text-gray-600" />
                                                ) : (
                                                        <Code size={20} className="text-blue-600" />
                                                )}
                                        </button>
                                </div>
                        )}

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