import React, { useState, useEffect, useCallback } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
        Settings,
        MessageSquare,
        MessageCircle,
        Sparkles,
        ChevronLeft,
        ChevronRight,
        AlertTriangle,
        Home,
        Code,
        Search,
        Brain,
        Library,
        Network,
        Users,
        Key,
        FileText,
        Globe,
        Shield,
        FolderOpen,
        ChevronDown,
        ChevronRight as ChevronRightIcon,
        Layers,
        Upload,
        X,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { apiClient } from '../../services/api';
import TrimmedImage from '../ui/TrimmedImage';
import { useTranslation } from 'react-i18next';

interface SidebarProps {
        collapsed: boolean;
        onToggle: () => void;
        mobileOpen?: boolean;
        isMobile?: boolean;
        onMobileClose?: () => void;
}

// Navigation structure with translation keys - flattened (no nested children for AI tools and Library management)
const getNavigation = (t: (key: string) => string) => [
        {
                name: t('about'),
                href: '/',
                icon: Globe,
        },
        {
                name: t('dashboard'),
                href: '/dashboard',
                icon: Home,
        },
        // Library Management items (moved to top level)
        {
                name: t('libraryManager'),
                href: '/ai/knowledge/manager',
                icon: FolderOpen,
        },
        {
                name: t('uploadQueue') || 'Upload Queue',
                href: '/ai/knowledge/upload',
                icon: Upload,
        },
        // AI Tools items (moved to top level)
        {
                name: t('freeAiChat'),
                href: '/ai/chat',
                icon: MessageSquare,
        },
        {
                name: t('basicRag'),
                href: '/ai/basic-rag',
                icon: Search,
        },
        {
                name: t('advancedRag'),
                href: '/ai/rag',
                icon: Brain,
        },
        {
                name: t('comprehensiveRag'),
                href: '/ai/comprehensive-rag',
                icon: Layers,
        },
        {
                name: t('graphRag'),
                href: '/ai/graph-rag',
                icon: Network,
        },
        {
                name: t('troubleshootingAi'),
                href: '/ai/troubleshooting',
                icon: AlertTriangle,
        },
        {
                name: t('forum'),
                href: '/forum',
                icon: MessageCircle,
        },
        {
                name: t('administration'),
                href: '/admin/users',
                icon: Settings,
                children: [
                        { name: t('usersRoles'), href: '/admin/users', icon: Users },
                        { name: t('licenses'), href: '/admin/licenses', icon: Key },
                        { name: t('systemSettings'), href: '/admin/system', icon: Settings },
                        { name: t('djangoAdmin'), href: '/admin/', icon: Shield, external: true },
                ],
        },
];

const Sidebar: React.FC<SidebarProps> = ({ collapsed, onToggle, mobileOpen = false, isMobile = false, onMobileClose }) => {
        const location = useLocation();
        const { permissions, user, loading } = useAuth();
        const { t } = useTranslation('sidebar');
        const [expandedItems, setExpandedItems] = useState<string[]>([]);

        const navigation = getNavigation(t);

        // Debug logging (remove in production)
        useEffect(() => {
                if (!loading) {
                        console.log('Sidebar - User:', user);
                        console.log('Sidebar - User is_staff:', user?.is_staff);
                        console.log('Sidebar - User is_superuser:', user?.is_superuser);
                        console.log('Sidebar - Permissions:', permissions);
                        console.log('Sidebar - Loading:', loading);
                        // Check if items would be shown
                        const testItems = navigation.map(item => ({
                                name: item.name,
                                href: item.href,
                                isAllowed: isAllowed(item.href),
                                feature: routeFeatureMap(item.href)
                        }));
                        console.log('Sidebar - Navigation items visibility:', testItems);
                }
        }, [user, permissions, loading]);

        const routeFeatureMap = (href: string): string | null => {
                if (href.startsWith('/admin/')) return 'admin';
                // Only specific AI routes require ai.rag
                const aiRagRoutes = [
                        '/ai/chat',
                        '/ai/basic-rag',
                        '/ai/rag',
                        '/ai/comprehensive-rag',
                        '/ai/graph-rag',
                ];
                if (aiRagRoutes.includes(href)) return 'ai.rag';
                // Knowledge routes require knowledge.view
                if (href.startsWith('/ai/knowledge')) return 'knowledge.view';
                if (href.startsWith('/ai/troubleshooting')) return 'knowledge.view';
                // Product manuals and lab-informatics trees also require knowledge.view
                if (href.startsWith('/products/')) return 'knowledge.view';
                if (href.startsWith('/lab-informatics/')) return 'knowledge.view';
                if (href.startsWith('/troubleshooting/')) return 'knowledge.view';
                return null;
        };

        const isAllowed = (href: string): boolean => {
                const feature = routeFeatureMap(href);
                // During loading, show all items to prevent flicker
                if (loading) return true;
                // Routes without feature requirements are always allowed
                if (!feature) return true;
                // Superusers and staff have access to all features
                // Check both direct properties and nested user object
                const isStaff = !!(user?.is_staff || (user as any)?.user?.is_staff);
                const isSuperuser = !!(user?.is_superuser || (user as any)?.user?.is_superuser);
                if (isSuperuser || isStaff) {
                        console.log(`Sidebar - Allowing ${href} because user is staff (${isStaff}) or superuser (${isSuperuser})`);
                        return true;
                }
                // Check permissions for non-staff users
                const hasPermission = !!permissions?.features?.[feature];
                console.log(`Sidebar - Checking ${href} (feature: ${feature}): ${hasPermission ? 'ALLOWED' : 'DENIED'}`);
                return hasPermission;
        };

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
                        const item = navigation.find(item => item.name === itemName);
                        return item?.children ? hasActiveChild(item.children) : false;
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
                <>
                        {/* Mobile overlay backdrop is handled in Layout */}
                        <div className={`
                                bg-white border-r border-gray-200 flex flex-col transition-all duration-300
                                ${isMobile 
                                        ? `fixed inset-y-0 left-0 z-50 transform ${mobileOpen ? 'translate-x-0' : '-translate-x-full'} w-64`
                                        : `relative ${collapsed ? 'w-16' : 'w-64'}`
                                }
                        `}>
                                {/* Header */}
                                <div className="flex items-center justify-between p-3 sm:p-4 border-b border-gray-200">
                                        {collapsed && !isMobile ? (
                                                <div className="flex items-center justify-center w-full">
                                                        <TrimmedImage
                                                                src={`${process.env.PUBLIC_URL || ''}/ai-logo-192.png`}
                                                                fallbackSrc={`${process.env.PUBLIC_URL || ''}/ai-logo-512.png`}
                                                                alt="AnyLab"
                                                                className="w-10 h-10 sm:w-12 sm:h-12"
                                                        />
                                                </div>
                                        ) : (
                                                <div className="flex items-center flex-1">
                                                        <TrimmedImage
                                                                src={`${process.env.PUBLIC_URL || ''}/ai-logo-512.png`}
                                                                fallbackSrc={`${process.env.PUBLIC_URL || ''}/ai-logo-192.png`}
                                                                alt="AnyLab"
                                                                className="w-12 h-12 sm:w-16 sm:h-16 mr-2 sm:mr-3 flex-shrink-0"
                                                        />
                                                        <div className="min-w-0">
                                                                <h1 className="text-lg sm:text-xl font-bold text-gray-900 truncate">AnyLab</h1>
                                                                <p className="text-xs text-gray-500 hidden sm:block">{t('slogan')}</p>
                                                        </div>
                                                </div>
                                        )}
                                        <div className="flex items-center gap-2">
                                                {isMobile && onMobileClose && (
                                                        <button
                                                                onClick={onMobileClose}
                                                                className="p-1 rounded-md hover:bg-gray-100 text-gray-700 transition-colors lg:hidden"
                                                                aria-label="Close menu"
                                                        >
                                                                <X size={20} />
                                                        </button>
                                                )}
                                                {!isMobile && (
                                                        <button
                                                                onClick={onToggle}
                                                                className="p-1 rounded-md hover:bg-primary-50 text-primary-700 transition-colors hidden lg:block"
                                                        >
                                                                {collapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
                                                        </button>
                                                )}
                                        </div>
                                </div>

                        {/* Navigation */}
                        <nav className="flex-1 p-2 sm:p-4 space-y-1 sm:space-y-2 overflow-y-auto">
                                {navigation.map((item) => {
                                        // During loading, show all items
                                        if (loading) {
                                                const Icon = item.icon;
                                                // Show parent with all children during loading
                                                return (
                                                        <div key={item.name} className="space-y-1">
                                                                {item.children ? (
                                                                        <div className="sidebar-item">
                                                                                <Icon size={20} className="mr-3" />
                                                                                {!collapsed && <span className="flex-1">{item.name}</span>}
                                                                        </div>
                                                                ) : (
                                                                        <Link to={item.href} className="sidebar-item">
                                                                                <Icon size={20} className="mr-3" />
                                                                                {!collapsed && <span className="flex-1">{item.name}</span>}
                                                                        </Link>
                                                                )}
                                                        </div>
                                                );
                                        }
                                        
                                        // If parent has no children and is not allowed, skip
                                        if (!item.children && !isAllowed(item.href)) {
                                                return null;
                                        }
                                        const Icon = item.icon;
                                        const allowedChildren = item.children ? item.children.filter((child: any) => isAllowed(child.href)) : [];
                                        // If parent has children but none are allowed, hide the entire section
                                        if (item.children && allowedChildren.length === 0) {
                                                return null;
                                        }
                                        const isParentActive = item.children ? hasActiveChild(item.children) : isActive(item.href);

                                        const expanded = isExpanded(item.name);

                                        return (
                                                <div key={item.name} className="space-y-1">
                                                        {item.children ? (
                                                                // Only Administration has children now
                                                                <button
                                                                        onClick={() => toggleExpanded(item.name)}
                                                                        className={`sidebar-item w-full text-left cursor-pointer ${isParentActive ? 'sidebar-item-active border border-primary-200 bg-primary-50 text-primary-800' : 'sidebar-item-inactive'}`}
                                                                        type="button"
                                                                >
                                                                        <Icon size={20} className={`mr-3 ${isParentActive ? 'text-primary-700' : ''}`} />
                                                                        {!collapsed && (
                                                                                <>
                                                                                        <span className="flex-1">{item.name}</span>
                                                                                        {expanded ? <ChevronDown size={16} /> : <ChevronRightIcon size={16} />}
                                                                                </>
                                                                        )}
                                                                </button>
                                                        ) : (
                                                                isAllowed(item.href) ? (
                                                                <Link
                                                                        to={item.href}
                                                                        onClick={() => isMobile && onMobileClose?.()}
                                                                        className={`sidebar-item ${isActive(item.href || '') ? 'sidebar-item-active border border-primary-200 bg-primary-50 text-primary-800' : 'sidebar-item-inactive'}`}
                                                                >
                                                                        <Icon size={20} className={`mr-2 sm:mr-3 flex-shrink-0 ${isActive(item.href || '') ? 'text-primary-700' : ''}`} />
                                                                        {(!collapsed || isMobile) && <span className="flex-1 truncate">{item.name}</span>}
                                                                </Link>
                                                                ) : null
                                                        )}

                                                        {!collapsed && item.children && expanded && (
                                                                <div className="ml-8 space-y-1">
                                                                        {allowedChildren.map((child: any) => {
                                                                                const ChildIcon = child.icon;
                                                                                // Handle external links (like Django admin)
                                                                                if (child.external) {
                                                                                        return (
                                                                                                <a
                                                                                                        key={child.name}
                                                                                                        href={child.href}
                                                                                                        target="_blank"
                                                                                                        rel="noopener noreferrer"
                                                                                                        className={`sidebar-item sidebar-item-inactive hover:bg-gray-50`}
                                                                                                >
                                                                                                        <ChildIcon size={18} className="mr-3" />
                                                                                                        <span className="flex-1">{child.name}</span>
                                                                                                        <Globe size={14} className="text-gray-400" />
                                                                                                </a>
                                                                                        );
                                                                                }
                                                                                return (
                                                                                        <Link
                                                                                                key={child.name}
                                                                                                to={child.href}
                                                                                                onClick={() => isMobile && onMobileClose?.()}
                                                                                                className={`sidebar-item ${isActive(child.href) ? 'sidebar-item-active border border-primary-200 bg-primary-50 text-primary-800' : 'sidebar-item-inactive'}`}
                                                                                        >
                                                                                                <ChildIcon size={16} className={`mr-2 flex-shrink-0 ${isActive(child.href) ? 'text-primary-700' : ''}`} />
                                                                                                <span className="truncate">{child.name}</span>
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
        </>
        );
};

export default Sidebar; 