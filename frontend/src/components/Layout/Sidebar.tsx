import React, { useState, useEffect, useCallback } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
        Settings,
        MessageSquare,
        MessageCircle,
        Sparkles,
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
        BookText,
        FileType2,
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
        Beaker,
        Atom,
        Scan,
        Layers,
        ToggleLeft,
        ToggleRight
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { apiClient } from '../../services/api';
import TrimmedImage from '../ui/TrimmedImage';
import { useTranslation } from 'react-i18next';

interface SidebarProps {
        collapsed: boolean;
        onToggle: () => void;
}

type OrganizationMode = 'general' | 'lab-informatics';

// Navigation structure with translation keys
const getGeneralAgilentNavigation = (t: (key: string) => string) => [
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
        {
                name: t('knowledgeLibrary'),
                href: '/ai/knowledge',
                icon: Library,
                children: [
                        { name: t('libraryManager'), href: '/ai/knowledge/manager', icon: FolderOpen },
                        { name: t('productManuals'), href: '/ai/knowledge/manuals', icon: BookText },
                        { name: t('technicalSpecs'), href: '/ai/knowledge/specs', icon: FileType2 },
                        { name: t('communitySolutions'), href: '/ai/knowledge/community', icon: Users },
                        { name: t('documentViewer'), href: '/ai/knowledge/viewer', icon: FileText },
                ],
        },
        {
                name: t('aiAssistant'),
                href: '/ai/chat',
                icon: Sparkles,
                children: [
                        { name: t('freeAiChat'), href: '/ai/chat', icon: MessageSquare },
                        { name: t('basicRag'), href: '/ai/basic-rag', icon: Search },
                        { name: t('advancedRag'), href: '/ai/rag', icon: Brain },
                        { name: t('comprehensiveRag'), href: '/ai/comprehensive-rag', icon: Layers },
                        { name: t('graphRag'), href: '/ai/graph-rag', icon: Network },
                        { name: t('troubleshootingAi'), href: '/ai/troubleshooting', icon: AlertTriangle },
                ],
        },
        {
                name: t('forum'),
                href: '/forum',
                icon: MessageCircle,
        },
        {
                name: t('gasChromatography'),
                href: '/products/gc',
                icon: FlaskConical,
                children: [
                        { name: t('gcSystems'), href: '/products/gc/systems', icon: FlaskConical },
                        { name: t('gcColumns'), href: '/products/gc/columns', icon: FlaskConical },
                        { name: t('gcAccessories'), href: '/products/gc/accessories', icon: FlaskConical },
                        { name: t('gcSoftware'), href: '/products/gc/software', icon: Code },
                ],
        },
        {
                name: t('liquidChromatography'),
                href: '/products/lc',
                icon: Beaker,
                children: [
                        { name: t('lcSystems'), href: '/products/lc/systems', icon: Beaker },
                        { name: t('lcColumns'), href: '/products/lc/columns', icon: Beaker },
                        { name: t('lcAccessories'), href: '/products/lc/accessories', icon: Beaker },
                        { name: t('lcSoftware'), href: '/products/lc/software', icon: Code },
                ],
        },
        {
                name: t('massSpectrometry'),
                href: '/products/ms',
                icon: Activity,
                children: [
                        { name: t('msSystems'), href: '/products/ms/systems', icon: Activity },
                        { name: t('msSoftware'), href: '/products/ms/software', icon: Code },
                        { name: t('msAccessories'), href: '/products/ms/accessories', icon: Activity },
                ],
        },
        {
                name: t('nmrSystems'),
                href: '/products/nmr',
                icon: Atom,
                children: [
                        { name: t('nmrSystems'), href: '/products/nmr/systems', icon: Atom },
                        { name: t('nmrSoftware'), href: '/products/nmr/software', icon: Code },
                        { name: t('nmrAccessories'), href: '/products/nmr/accessories', icon: Atom },
                ],
        },
        {
                name: t('spectroscopy'),
                href: '/products/spectroscopy',
                icon: Scan,
                children: [
                        { name: t('uvVis'), href: '/products/spectroscopy/uv-vis', icon: Scan },
                        { name: t('ir'), href: '/products/spectroscopy/ir', icon: Scan },
                        { name: t('fluorescence'), href: '/products/spectroscopy/fluorescence', icon: Scan },
                ],
        },
        {
                name: t('administration'),
                href: '/admin/users',
                icon: Settings,
                children: [
                        { name: t('usersRoles'), href: '/admin/users', icon: Users },
                        { name: t('licenses'), href: '/admin/licenses', icon: Key },
                        { name: t('djangoAdmin'), href: '/admin/', icon: Shield, external: true },
                ],
        },
];

const getLabInformaticsNavigation = (t: (key: string) => string) => [
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
        {
                name: t('knowledgeLibrary'),
                href: '/ai/knowledge',
                icon: Library,
                children: [
                        { name: t('libraryManager'), href: '/ai/knowledge/manager', icon: FolderOpen },
                        { name: t('ssbDatabase'), href: '/ai/knowledge/ssb', icon: Database },
                        { name: t('helpPortal'), href: '/ai/knowledge/help-portal', icon: Globe },
                        { name: t('communitySolutions'), href: '/ai/knowledge/community', icon: Users },
                        { name: t('documentViewer'), href: '/ai/knowledge/viewer', icon: FileText },
                ],
        },
        {
                name: t('aiAssistant'),
                href: '/ai/chat',
                icon: Sparkles,
                children: [
                        { name: t('freeAiChat'), href: '/ai/chat', icon: MessageSquare },
                        { name: t('basicRag'), href: '/ai/basic-rag', icon: Search },
                        { name: t('advancedRag'), href: '/ai/rag', icon: Brain },
                        { name: t('comprehensiveRag'), href: '/ai/comprehensive-rag', icon: Layers },
                        { name: t('graphRag'), href: '/ai/graph-rag', icon: Network },
                        { name: t('troubleshootingAi'), href: '/ai/troubleshooting', icon: AlertTriangle },
                ],
        },
        {
                name: t('forum'),
                href: '/forum',
                icon: MessageCircle,
        },
        {
                name: t('openlabSoftwareSuite'),
                href: '/lab-informatics/openlab',
                icon: Code,
                children: [
                        { name: t('openlabCds'), href: '/lab-informatics/openlab/cds', icon: Code },
                        { name: t('openlabEcm'), href: '/lab-informatics/openlab/ecm', icon: Database },
                        { name: t('openlabEln'), href: '/lab-informatics/openlab/eln', icon: FileText },
                        { name: t('openlabServer'), href: '/lab-informatics/openlab/server', icon: Server },
                ],
        },
        {
                name: t('masshunterSuite'),
                href: '/lab-informatics/masshunter',
                icon: Cpu,
                children: [
                        { name: t('masshunterWorkstation'), href: '/lab-informatics/masshunter/workstation', icon: Cpu },
                        { name: t('masshunterQuantitative'), href: '/lab-informatics/masshunter/quantitative', icon: BarChart3 },
                        { name: t('masshunterQualitative'), href: '/lab-informatics/masshunter/qualitative', icon: Search },
                        { name: t('masshunterBioconfirm'), href: '/lab-informatics/masshunter/bioconfirm', icon: Brain },
                        { name: t('masshunterMetabolomics'), href: '/lab-informatics/masshunter/metabolomics', icon: Activity },
                ],
        },
        {
                name: t('vnmrjSoftware'),
                href: '/lab-informatics/vnmrj',
                icon: Cpu,
                children: [
                        { name: t('vnmrjCurrent'), href: '/lab-informatics/vnmrj/current', icon: Cpu },
                        { name: t('vnmrjLegacy'), href: '/lab-informatics/vnmrj/legacy', icon: Cpu },
                        { name: t('vnmrLegacy'), href: '/lab-informatics/vnmrj/vnmr-legacy', icon: Cpu },
                ],
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

const Sidebar: React.FC<SidebarProps> = ({ collapsed, onToggle }) => {
        const location = useLocation();
        const { permissions, user, loading } = useAuth();
        const { t } = useTranslation('sidebar');
        const [expandedItems, setExpandedItems] = useState<string[]>([]);
        const [organizationMode, setOrganizationMode] = useState<OrganizationMode>(() => {
                const saved = localStorage.getItem('anylab_organization_mode');
                return (saved as OrganizationMode) || 'general';
        });

        const [availableCategories, setAvailableCategories] = useState<Set<string>>(new Set());
        const [discoveredCategories, setDiscoveredCategories] = useState<string[]>([]);

        // Load available product categories once authenticated
        useEffect(() => {
                const loadAvailable = async () => {
                        if (loading) return;
                        try {
                                const data = await apiClient.getAvailableProducts();
                                const cats = new Set<string>((data.products || []).map((p: any) => String(p.product_category).toLowerCase()));
                                setAvailableCategories(cats);

                                // Track categories not present in static navigation (for lab-informatics mode)
                                const knownCats = new Set<string>([
                                        'openlab','masshunter','vnmrj','gc','lc','ms','nmr','spectroscopy'
                                ]);
                                const discovered: string[] = [];
                                cats.forEach(c => { if (!knownCats.has(c)) discovered.push(c); });
                                setDiscoveredCategories(discovered.sort());
                        } catch (e) {
                                // Ignore errors; sidebar will show defaults
                        }
                };
                loadAvailable();
        }, [loading]);

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

        // Save mode preference to localStorage
        useEffect(() => {
                localStorage.setItem('anylab_organization_mode', organizationMode);
        }, [organizationMode]);

        const toggleOrganizationMode = () => {
                setOrganizationMode(prev => prev === 'general' ? 'lab-informatics' : 'general');
        };

        // Helper: extract top-level category from href
        const extractCategory = (href: string): { domain: 'lab'|'prod'|null; category: string|null } => {
                if (href.startsWith('/lab-informatics/')) {
                        const parts = href.split('/').filter(Boolean);
                        return { domain: 'lab', category: parts[1] || null };
                }
                if (href.startsWith('/products/')) {
                        const parts = href.split('/').filter(Boolean);
                        return { domain: 'prod', category: parts[1] || null };
                }
                return { domain: null, category: null };
        };

        const baseNavigation = organizationMode === 'general' ? getGeneralAgilentNavigation(t) : getLabInformaticsNavigation(t);

        // Map backend product_category to route /lab-informatics/:suite/:product
        const categoryToRoute = (category: string): string => {
                const c = (category || '').toLowerCase();
                // Known mappings
                const map: Record<string, [string, string]> = {
                        'openlab_cds': ['openlab','cds'],
                        'openlab_ecm': ['openlab','ecm'],
                        'openlab_eln': ['openlab','eln'],
                        'openlab_server': ['openlab','server'],
                        'masshunter_workstation': ['masshunter','workstation'],
                        'masshunter_quantitative': ['masshunter','quantitative'],
                        'masshunter_qualitative': ['masshunter','qualitative'],
                        'masshunter_bioconfirm': ['masshunter','bioconfirm'],
                        'masshunter_metabolomics': ['masshunter','metabolomics'],
                        'vnmrj_current': ['vnmrj','current'],
                        'vnmrj_legacy': ['vnmrj','legacy'],
                };
                if (map[c]) {
                        const [suite, product] = map[c];
                        return `/lab-informatics/${suite}/${product}`;
                }
                // Fallback: split at first underscore
                const idx = c.indexOf('_');
                if (idx > 0) {
                        const suite = c.slice(0, idx);
                        const product = c.slice(idx + 1);
                        return `/lab-informatics/${suite}/${product}`;
                }
                // Last resort: direct under lab-informatics
                return `/lab-informatics/${c}/general`;
        };

        // Filter out items with no available content based on category presence
        const navigation = baseNavigation
                .map((item: any) => {
                        const { category } = extractCategory(item.href);
                        // If item maps to a category, hide when not available (unless no availability loaded yet)
                        if (category && availableCategories.size > 0) {
                                const present = availableCategories.has(category.toLowerCase());
                                if (!present) {
                                        return null;
                                }
                        }
                        return item;
                })
                .filter(Boolean) as any[];

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
                                {collapsed ? (
                                        <div className="flex items-center justify-center w-full">
                                                <TrimmedImage
                                                        src={`${process.env.PUBLIC_URL || ''}/ai-logo-192.png`}
                                                        fallbackSrc={`${process.env.PUBLIC_URL || ''}/ai-logo-512.png`}
                                                        alt="AnyLab"
                                                        className="w-12 h-12"
                                                />
                                        </div>
                                ) : (
                                        <div className="flex items-center">
                                                <TrimmedImage
                                                        src={`${process.env.PUBLIC_URL || ''}/ai-logo-512.png`}
                                                        fallbackSrc={`${process.env.PUBLIC_URL || ''}/ai-logo-192.png`}
                                                        alt="AnyLab"
                                                        className="w-16 h-16 mr-3"
                                                />
                                                <div>
                                                        <h1 className="text-xl font-bold text-gray-900">AnyLab</h1>
                                                        <p className="text-xs text-gray-500">{t('slogan')}</p>
                                                </div>
                                        </div>
                                )}
                                <button
                                        onClick={onToggle}
                                        className="p-1 rounded-md hover:bg-primary-50 text-primary-700 transition-colors"
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
                                                                {t('organizationMode')}
                                                        </span>
                                                        <span className="text-xs text-gray-500">
                                                                {organizationMode === 'general' ? t('generalAgilentProducts') : t('labInformaticsFocus')}
                                                        </span>
                                                </div>
                                                <button
                                                        onClick={toggleOrganizationMode}
                                                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                                                                organizationMode === 'lab-informatics' 
                                                                        ? 'bg-primary-600' 
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
                                                className="w-full p-2 rounded-md hover:bg-primary-50 text-primary-700 transition-colors flex items-center justify-center"
                                                title={organizationMode === 'general' ? t('labInformaticsFocus') : t('generalAgilentProducts')}
                                        >
                                                {organizationMode === 'general' ? (
                                                        <FlaskConical size={20} className="text-primary-600" />
                                                ) : (
                                                        <Code size={20} className="text-primary-600" />
                                                )}
                                        </button>
                                </div>
                        )}

                        {/* Navigation */}
                        <nav className="flex-1 p-4 space-y-2">
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
                                                                <button
                                                                        onClick={() => toggleExpanded(item.name)}
                                                                        className={`sidebar-item w-full text-left cursor-pointer ${isParentActive ? 'sidebar-item-active border border-primary-200 bg-primary-50 text-primary-800' : 'sidebar-item-inactive'} ${item.name === t('knowledgeLibrary') ? 'flex-col items-start py-3' : ''}`}
                                                                        type="button"
                                                                >
                                                                        {item.name === t('knowledgeLibrary') ? (
                                                                                <>
                                                                                        <div className="flex items-center w-full mb-1">
                                                                                                <Icon size={20} className={`mr-3 ${isParentActive ? 'text-primary-700' : ''}`} />
                                                                                                {!collapsed && (expanded ? <ChevronDown size={16} /> : <ChevronRightIcon size={16} />)}
                                                                                        </div>
                                                                                        {!collapsed && <span className="block w-full">{item.name}</span>}
                                                                                </>
                                                                        ) : (
                                                                                <>
                                                                                        <Icon size={20} className={`mr-3 ${isParentActive ? 'text-primary-700' : ''}`} />
                                                                                        {!collapsed && (
                                                                                                <>
                                                                                                        <span className="flex-1">{item.name}</span>
                                                                                                        {expanded ? <ChevronDown size={16} /> : <ChevronRightIcon size={16} />}
                                                                                                </>
                                                                                        )}
                                                                                </>
                                                                        )}
                                                                </button>
                                                        ) : (
                                                                isAllowed(item.href) ? (
                                                                <Link
                                                                        to={item.href}
                                                                        className={`sidebar-item ${isActive(item.href || '') ? 'sidebar-item-active border border-primary-200 bg-primary-50 text-primary-800' : 'sidebar-item-inactive'}`}
                                                                >
                                                                        <Icon size={20} className={`mr-3 ${isActive(item.href || '') ? 'text-primary-700' : ''}`} />
                                                                        {!collapsed && <span className="flex-1">{item.name}</span>}
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
                                                                                                className={`sidebar-item ${isActive(child.href) ? 'sidebar-item-active border border-primary-200 bg-primary-50 text-primary-800' : 'sidebar-item-inactive'}`}
                                                                                        >
                                                                                                <ChildIcon size={16} className={`mr-2 ${isActive(child.href) ? 'text-primary-700' : ''}`} />
                                                                                                {child.name}
                                                                                        </Link>
                                                                                );
                                                                        })}
                                                                </div>
                                                        )}
                                                </div>
                                        );
                                })}

                                {/* Discovered products (not in static lists) */}
                                {!collapsed && discoveredCategories.length > 0 && organizationMode === 'lab-informatics' && (
                                        <div className="mt-4">
                                                <div className="px-2 py-1 text-xs font-semibold text-gray-500 uppercase tracking-wide">{t('discoveredProducts')}</div>
                                                <div className="mt-2 space-y-1 ml-0">
                                                        {discoveredCategories.map((cat) => (
                                                                <Link key={cat} to={categoryToRoute(cat)}
                                                                        className={`sidebar-item sidebar-item-inactive`}>
                                                                        <Code size={18} className="mr-3" />
                                                                        <span className="flex-1">{cat.replace(/-/g,' ').toUpperCase()}</span>
                                                                </Link>
                                                        ))}
                                                </div>
                                        </div>
                                )}
                        </nav>
                </div>
        );
};

export default Sidebar; 