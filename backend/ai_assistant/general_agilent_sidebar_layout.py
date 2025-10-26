"""
General Agilent Products Sidebar Layout

This module provides the sidebar layout and navigation structure
for the General Agilent Products mode of the AnyLab application.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from django.utils import timezone as django_timezone

logger = logging.getLogger(__name__)


class NavigationItemType(Enum):
    """Navigation item type enumeration"""
    SECTION = "section"
    SUBSECTION = "subsection"
    LINK = "link"
    DROPDOWN = "dropdown"
    DIVIDER = "divider"
    HEADER = "header"


class ProductCategory(Enum):
    """Product category enumeration"""
    ANALYTICAL_INSTRUMENTS = "analytical_instruments"
    LIFE_SCIENCES = "life_sciences"
    DIAGNOSTICS = "diagnostics"
    APPLIED_MARKETS = "applied_markets"
    SOFTWARE_SERVICES = "software_services"
    CONSUMABLES = "consumables"
    SUPPORT_SERVICES = "support_services"


class ContentType(Enum):
    """Content type enumeration"""
    PRODUCT_INFO = "product_info"
    USER_GUIDE = "user_guide"
    TECHNICAL_SPEC = "technical_spec"
    INSTALLATION = "installation"
    TROUBLESHOOTING = "troubleshooting"
    MAINTENANCE = "maintenance"
    TRAINING = "training"
    SUPPORT = "support"
    DOWNLOADS = "downloads"
    FAQ = "faq"


@dataclass
class NavigationItem:
    """Navigation item structure"""
    id: str
    title: str
    type: NavigationItemType
    icon: Optional[str] = None
    url: Optional[str] = None
    children: List['NavigationItem'] = field(default_factory=list)
    badge: Optional[str] = None
    tooltip: Optional[str] = None
    permissions: List[str] = field(default_factory=list)
    is_active: bool = False
    is_expanded: bool = False
    order: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SidebarSection:
    """Sidebar section structure"""
    id: str
    title: str
    icon: str
    items: List[NavigationItem]
    order: int
    is_collapsible: bool = True
    is_collapsed: bool = False
    permissions: List[str] = field(default_factory=list)


@dataclass
class SidebarLayout:
    """Sidebar layout structure"""
    id: str
    name: str
    description: str
    sections: List[SidebarSection]
    theme: str = "default"
    width: str = "280px"
    is_resizable: bool = True
    show_search: bool = True
    show_user_info: bool = True
    show_notifications: bool = True
    created_at: datetime = field(default_factory=lambda: django_timezone.now())
    updated_at: datetime = field(default_factory=lambda: django_timezone.now())


class GeneralAgilentSidebarLayout:
    """General Agilent Products Sidebar Layout Manager"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize General Agilent sidebar layout"""
        self.config = config or {}
        self.layout_enabled = self.config.get('layout_enabled', True)
        self.dynamic_content_enabled = self.config.get('dynamic_content_enabled', True)
        self.user_preferences_enabled = self.config.get('user_preferences_enabled', True)
        self.analytics_enabled = self.config.get('analytics_enabled', True)
        
        # Layout configuration
        self.default_theme = self.config.get('default_theme', 'agilent-blue')
        self.default_width = self.config.get('default_width', '280px')
        self.collapsible_sections = self.config.get('collapsible_sections', True)
        self.remember_state = self.config.get('remember_state', True)
        
        # Content configuration
        self.show_product_counts = self.config.get('show_product_counts', True)
        self.show_recent_content = self.config.get('show_recent_content', True)
        self.show_popular_content = self.config.get('show_popular_content', True)
        self.max_recent_items = self.config.get('max_recent_items', 5)
        self.max_popular_items = self.config.get('max_popular_items', 5)
        
        # Initialize layout
        self._initialize_layout()
        
        logger.info("General Agilent Sidebar Layout initialized")
    
    def _initialize_layout(self):
        """Initialize the sidebar layout structure"""
        try:
            # Create main layout
            self.layout = SidebarLayout(
                id="general_agilent_sidebar",
                name="General Agilent Products",
                description="Sidebar layout for General Agilent Products navigation",
                sections=[],
                theme=self.default_theme,
                width=self.default_width
            )
            
            # Create sections
            self._create_main_sections()
            
            logger.info("Sidebar layout initialized with sections")
            
        except Exception as e:
            logger.error(f"Error initializing sidebar layout: {e}")
    
    def _create_main_sections(self):
        """Create main sidebar sections"""
        try:
            sections = [
                self._create_dashboard_section(),
                self._create_products_section(),
                self._create_documentation_section(),
                self._create_support_section(),
                self._create_tools_section(),
                self._create_resources_section(),
                self._create_ai_assistant_section(),
                self._create_user_section()
            ]
            
            # Add sections to layout
            self.layout.sections.extend(sections)
            
        except Exception as e:
            logger.error(f"Error creating main sections: {e}")
    
    def _create_dashboard_section(self) -> SidebarSection:
        """Create dashboard section"""
        try:
            items = [
                NavigationItem(
                    id="dashboard_overview",
                    title="Overview",
                    type=NavigationItemType.LINK,
                    icon="dashboard",
                    url="/dashboard",
                    order=1
                ),
                NavigationItem(
                    id="dashboard_analytics",
                    title="Analytics",
                    type=NavigationItemType.LINK,
                    icon="analytics",
                    url="/dashboard/analytics",
                    order=2
                ),
                NavigationItem(
                    id="dashboard_reports",
                    title="Reports",
                    type=NavigationItemType.LINK,
                    icon="report",
                    url="/dashboard/reports",
                    order=3
                )
            ]
            
            return SidebarSection(
                id="dashboard",
                title="Dashboard",
                icon="dashboard",
                items=items,
                order=1,
                is_collapsible=True
            )
            
        except Exception as e:
            logger.error(f"Error creating dashboard section: {e}")
            return SidebarSection(id="dashboard", title="Dashboard", icon="dashboard", items=[], order=1)
    
    def _create_products_section(self) -> SidebarSection:
        """Create products section"""
        try:
            items = [
                NavigationItem(
                    id="products_analytical",
                    title="Analytical Instruments",
                    type=NavigationItemType.DROPDOWN,
                    icon="microscope",
                    order=1,
                    children=[
                        NavigationItem(
                            id="products_gc",
                            title="Gas Chromatography",
                            type=NavigationItemType.LINK,
                            url="/products/gc",
                            order=1
                        ),
                        NavigationItem(
                            id="products_lc",
                            title="Liquid Chromatography",
                            type=NavigationItemType.LINK,
                            url="/products/lc",
                            order=2
                        ),
                        NavigationItem(
                            id="products_ms",
                            title="Mass Spectrometry",
                            type=NavigationItemType.LINK,
                            url="/products/ms",
                            order=3
                        ),
                        NavigationItem(
                            id="products_nmr",
                            title="NMR Spectroscopy",
                            type=NavigationItemType.LINK,
                            url="/products/nmr",
                            order=4
                        ),
                        NavigationItem(
                            id="products_icp",
                            title="ICP-MS/OES",
                            type=NavigationItemType.LINK,
                            url="/products/icp",
                            order=5
                        )
                    ]
                ),
                NavigationItem(
                    id="products_life_sciences",
                    title="Life Sciences",
                    type=NavigationItemType.DROPDOWN,
                    icon="dna",
                    order=2,
                    children=[
                        NavigationItem(
                            id="products_pcr",
                            title="PCR Systems",
                            type=NavigationItemType.LINK,
                            url="/products/pcr",
                            order=1
                        ),
                        NavigationItem(
                            id="products_sequencing",
                            title="Sequencing",
                            type=NavigationItemType.LINK,
                            url="/products/sequencing",
                            order=2
                        ),
                        NavigationItem(
                            id="products_cell_analysis",
                            title="Cell Analysis",
                            type=NavigationItemType.LINK,
                            url="/products/cell-analysis",
                            order=3
                        ),
                        NavigationItem(
                            id="products_protein",
                            title="Protein Analysis",
                            type=NavigationItemType.LINK,
                            url="/products/protein",
                            order=4
                        )
                    ]
                ),
                NavigationItem(
                    id="products_diagnostics",
                    title="Diagnostics",
                    type=NavigationItemType.DROPDOWN,
                    icon="stethoscope",
                    order=3,
                    children=[
                        NavigationItem(
                            id="products_clinical",
                            title="Clinical Diagnostics",
                            type=NavigationItemType.LINK,
                            url="/products/clinical",
                            order=1
                        ),
                        NavigationItem(
                            id="products_molecular",
                            title="Molecular Diagnostics",
                            type=NavigationItemType.LINK,
                            url="/products/molecular",
                            order=2
                        ),
                        NavigationItem(
                            id="products_pathology",
                            title="Pathology",
                            type=NavigationItemType.LINK,
                            url="/products/pathology",
                            order=3
                        )
                    ]
                ),
                NavigationItem(
                    id="products_applied",
                    title="Applied Markets",
                    type=NavigationItemType.DROPDOWN,
                    icon="industry",
                    order=4,
                    children=[
                        NavigationItem(
                            id="products_food",
                            title="Food & Beverage",
                            type=NavigationItemType.LINK,
                            url="/products/food-beverage",
                            order=1
                        ),
                        NavigationItem(
                            id="products_environmental",
                            title="Environmental",
                            type=NavigationItemType.LINK,
                            url="/products/environmental",
                            order=2
                        ),
                        NavigationItem(
                            id="products_pharmaceutical",
                            title="Pharmaceutical",
                            type=NavigationItemType.LINK,
                            url="/products/pharmaceutical",
                            order=3
                        ),
                        NavigationItem(
                            id="products_chemical",
                            title="Chemical",
                            type=NavigationItemType.LINK,
                            url="/products/chemical",
                            order=4
                        )
                    ]
                ),
                NavigationItem(
                    id="products_software",
                    title="Software & Services",
                    type=NavigationItemType.DROPDOWN,
                    icon="software",
                    order=5,
                    children=[
                        NavigationItem(
                            id="products_openlab",
                            title="OpenLab",
                            type=NavigationItemType.LINK,
                            url="/products/openlab",
                            order=1
                        ),
                        NavigationItem(
                            id="products_masshunter",
                            title="MassHunter",
                            type=NavigationItemType.LINK,
                            url="/products/masshunter",
                            order=2
                        ),
                        NavigationItem(
                            id="products_chemstation",
                            title="ChemStation",
                            type=NavigationItemType.LINK,
                            url="/products/chemstation",
                            order=3
                        ),
                        NavigationItem(
                            id="products_vnmrj",
                            title="VnmrJ",
                            type=NavigationItemType.LINK,
                            url="/products/vnmrj",
                            order=4
                        )
                    ]
                )
            ]
            
            return SidebarSection(
                id="products",
                title="Products",
                icon="products",
                items=items,
                order=2,
                is_collapsible=True
            )
            
        except Exception as e:
            logger.error(f"Error creating products section: {e}")
            return SidebarSection(id="products", title="Products", icon="products", items=[], order=2)
    
    def _create_documentation_section(self) -> SidebarSection:
        """Create documentation section"""
        try:
            items = [
                NavigationItem(
                    id="docs_user_guides",
                    title="User Guides",
                    type=NavigationItemType.LINK,
                    icon="book",
                    url="/documentation/user-guides",
                    order=1
                ),
                NavigationItem(
                    id="docs_technical_specs",
                    title="Technical Specifications",
                    type=NavigationItemType.LINK,
                    icon="specifications",
                    url="/documentation/technical-specs",
                    order=2
                ),
                NavigationItem(
                    id="docs_installation",
                    title="Installation Guides",
                    type=NavigationItemType.LINK,
                    icon="install",
                    url="/documentation/installation",
                    order=3
                ),
                NavigationItem(
                    id="docs_troubleshooting",
                    title="Troubleshooting",
                    type=NavigationItemType.LINK,
                    icon="troubleshoot",
                    url="/documentation/troubleshooting",
                    order=4
                ),
                NavigationItem(
                    id="docs_maintenance",
                    title="Maintenance",
                    type=NavigationItemType.LINK,
                    icon="maintenance",
                    url="/documentation/maintenance",
                    order=5
                ),
                NavigationItem(
                    id="docs_training",
                    title="Training Materials",
                    type=NavigationItemType.LINK,
                    icon="training",
                    url="/documentation/training",
                    order=6
                ),
                NavigationItem(
                    id="docs_api",
                    title="API Documentation",
                    type=NavigationItemType.LINK,
                    icon="api",
                    url="/documentation/api",
                    order=7
                ),
                NavigationItem(
                    id="docs_release_notes",
                    title="Release Notes",
                    type=NavigationItemType.LINK,
                    icon="release",
                    url="/documentation/release-notes",
                    order=8
                )
            ]
            
            return SidebarSection(
                id="documentation",
                title="Documentation",
                icon="documentation",
                items=items,
                order=3,
                is_collapsible=True
            )
            
        except Exception as e:
            logger.error(f"Error creating documentation section: {e}")
            return SidebarSection(id="documentation", title="Documentation", icon="documentation", items=[], order=3)
    
    def _create_support_section(self) -> SidebarSection:
        """Create support section"""
        try:
            items = [
                NavigationItem(
                    id="support_contact",
                    title="Contact Support",
                    type=NavigationItemType.LINK,
                    icon="support",
                    url="/support/contact",
                    order=1
                ),
                NavigationItem(
                    id="support_tickets",
                    title="Support Tickets",
                    type=NavigationItemType.LINK,
                    icon="ticket",
                    url="/support/tickets",
                    order=2
                ),
                NavigationItem(
                    id="support_knowledge_base",
                    title="Knowledge Base",
                    type=NavigationItemType.LINK,
                    icon="knowledge",
                    url="/support/knowledge-base",
                    order=3
                ),
                NavigationItem(
                    id="support_forums",
                    title="Community Forums",
                    type=NavigationItemType.LINK,
                    icon="forum",
                    url="/support/forums",
                    order=4
                ),
                NavigationItem(
                    id="support_remote_assistance",
                    title="Remote Assistance",
                    type=NavigationItemType.LINK,
                    icon="remote",
                    url="/support/remote-assistance",
                    order=5
                ),
                NavigationItem(
                    id="support_service_centers",
                    title="Service Centers",
                    type=NavigationItemType.LINK,
                    icon="service-center",
                    url="/support/service-centers",
                    order=6
                ),
                NavigationItem(
                    id="support_warranty",
                    title="Warranty Information",
                    type=NavigationItemType.LINK,
                    icon="warranty",
                    url="/support/warranty",
                    order=7
                )
            ]
            
            return SidebarSection(
                id="support",
                title="Support",
                icon="support",
                items=items,
                order=4,
                is_collapsible=True
            )
            
        except Exception as e:
            logger.error(f"Error creating support section: {e}")
            return SidebarSection(id="support", title="Support", icon="support", items=[], order=4)
    
    def _create_tools_section(self) -> SidebarSection:
        """Create tools section"""
        try:
            items = [
                NavigationItem(
                    id="tools_calculator",
                    title="Calculator Tools",
                    type=NavigationItemType.LINK,
                    icon="calculator",
                    url="/tools/calculator",
                    order=1
                ),
                NavigationItem(
                    id="tools_converter",
                    title="Unit Converter",
                    type=NavigationItemType.LINK,
                    icon="converter",
                    url="/tools/converter",
                    order=2
                ),
                NavigationItem(
                    id="tools_method_development",
                    title="Method Development",
                    type=NavigationItemType.LINK,
                    icon="method",
                    url="/tools/method-development",
                    order=3
                ),
                NavigationItem(
                    id="tools_data_analysis",
                    title="Data Analysis",
                    type=NavigationItemType.LINK,
                    icon="analysis",
                    url="/tools/data-analysis",
                    order=4
                ),
                NavigationItem(
                    id="tools_configuration",
                    title="Configuration Tools",
                    type=NavigationItemType.LINK,
                    icon="config",
                    url="/tools/configuration",
                    order=5
                ),
                NavigationItem(
                    id="tools_diagnostics",
                    title="Diagnostics",
                    type=NavigationItemType.LINK,
                    icon="diagnostics",
                    url="/tools/diagnostics",
                    order=6
                )
            ]
            
            return SidebarSection(
                id="tools",
                title="Tools",
                icon="tools",
                items=items,
                order=5,
                is_collapsible=True
            )
            
        except Exception as e:
            logger.error(f"Error creating tools section: {e}")
            return SidebarSection(id="tools", title="Tools", icon="tools", items=[], order=5)
    
    def _create_resources_section(self) -> SidebarSection:
        """Create resources section"""
        try:
            items = [
                NavigationItem(
                    id="resources_downloads",
                    title="Downloads",
                    type=NavigationItemType.LINK,
                    icon="download",
                    url="/resources/downloads",
                    order=1
                ),
                NavigationItem(
                    id="resources_software_updates",
                    title="Software Updates",
                    type=NavigationItemType.LINK,
                    icon="update",
                    url="/resources/software-updates",
                    order=2
                ),
                NavigationItem(
                    id="resources_drivers",
                    title="Drivers & Firmware",
                    type=NavigationItemType.LINK,
                    icon="driver",
                    url="/resources/drivers",
                    order=3
                ),
                NavigationItem(
                    id="resources_certificates",
                    title="Certificates",
                    type=NavigationItemType.LINK,
                    icon="certificate",
                    url="/resources/certificates",
                    order=4
                ),
                NavigationItem(
                    id="resources_standards",
                    title="Standards & Regulations",
                    type=NavigationItemType.LINK,
                    icon="standards",
                    url="/resources/standards",
                    order=5
                ),
                NavigationItem(
                    id="resources_white_papers",
                    title="White Papers",
                    type=NavigationItemType.LINK,
                    icon="paper",
                    url="/resources/white-papers",
                    order=6
                ),
                NavigationItem(
                    id="resources_case_studies",
                    title="Case Studies",
                    type=NavigationItemType.LINK,
                    icon="case-study",
                    url="/resources/case-studies",
                    order=7
                ),
                NavigationItem(
                    id="resources_webinars",
                    title="Webinars",
                    type=NavigationItemType.LINK,
                    icon="webinar",
                    url="/resources/webinars",
                    order=8
                )
            ]
            
            return SidebarSection(
                id="resources",
                title="Resources",
                icon="resources",
                items=items,
                order=6,
                is_collapsible=True
            )
            
        except Exception as e:
            logger.error(f"Error creating resources section: {e}")
            return SidebarSection(id="resources", title="Resources", icon="resources", items=[], order=6)
    
    def _create_ai_assistant_section(self) -> SidebarSection:
        """Create AI assistant section"""
        try:
            items = [
                NavigationItem(
                    id="ai_chat",
                    title="AI Chat Assistant",
                    type=NavigationItemType.LINK,
                    icon="chat",
                    url="/ai/chat",
                    order=1
                ),
                NavigationItem(
                    id="ai_rag_search",
                    title="RAG Search",
                    type=NavigationItemType.LINK,
                    icon="search",
                    url="/ai/rag-search",
                    order=2
                ),
                NavigationItem(
                    id="ai_advanced_search",
                    title="Advanced Search",
                    type=NavigationItemType.LINK,
                    icon="advanced-search",
                    url="/ai/advanced-search",
                    order=3
                ),
                NavigationItem(
                    id="ai_comprehensive_search",
                    title="Comprehensive Search",
                    type=NavigationItemType.LINK,
                    icon="comprehensive-search",
                    url="/ai/comprehensive-search",
                    order=4
                ),
                NavigationItem(
                    id="ai_document_manager",
                    title="Document Manager",
                    type=NavigationItemType.LINK,
                    icon="document-manager",
                    url="/ai/document-manager",
                    order=5
                ),
                NavigationItem(
                    id="ai_content_analysis",
                    title="Content Analysis",
                    type=NavigationItemType.LINK,
                    icon="analysis",
                    url="/ai/content-analysis",
                    order=6
                )
            ]
            
            return SidebarSection(
                id="ai_assistant",
                title="AI Assistant",
                icon="ai",
                items=items,
                order=7,
                is_collapsible=True
            )
            
        except Exception as e:
            logger.error(f"Error creating AI assistant section: {e}")
            return SidebarSection(id="ai_assistant", title="AI Assistant", icon="ai", items=[], order=7)
    
    def _create_user_section(self) -> SidebarSection:
        """Create user section"""
        try:
            items = [
                NavigationItem(
                    id="user_profile",
                    title="Profile",
                    type=NavigationItemType.LINK,
                    icon="profile",
                    url="/user/profile",
                    order=1
                ),
                NavigationItem(
                    id="user_preferences",
                    title="Preferences",
                    type=NavigationItemType.LINK,
                    icon="preferences",
                    url="/user/preferences",
                    order=2
                ),
                NavigationItem(
                    id="user_history",
                    title="History",
                    type=NavigationItemType.LINK,
                    icon="history",
                    url="/user/history",
                    order=3
                ),
                NavigationItem(
                    id="user_favorites",
                    title="Favorites",
                    type=NavigationItemType.LINK,
                    icon="favorites",
                    url="/user/favorites",
                    order=4
                ),
                NavigationItem(
                    id="user_notifications",
                    title="Notifications",
                    type=NavigationItemType.LINK,
                    icon="notifications",
                    url="/user/notifications",
                    order=5
                ),
                NavigationItem(
                    id="user_settings",
                    title="Settings",
                    type=NavigationItemType.LINK,
                    icon="settings",
                    url="/user/settings",
                    order=6
                )
            ]
            
            return SidebarSection(
                id="user",
                title="User",
                icon="user",
                items=items,
                order=8,
                is_collapsible=True
            )
            
        except Exception as e:
            logger.error(f"Error creating user section: {e}")
            return SidebarSection(id="user", title="User", icon="user", items=[], order=8)
    
    def get_layout(self) -> SidebarLayout:
        """Get the current sidebar layout"""
        return self.layout
    
    def get_section(self, section_id: str) -> Optional[SidebarSection]:
        """Get a specific section by ID"""
        try:
            for section in self.layout.sections:
                if section.id == section_id:
                    return section
            return None
            
        except Exception as e:
            logger.error(f"Error getting section {section_id}: {e}")
            return None
    
    def get_navigation_item(self, item_id: str) -> Optional[NavigationItem]:
        """Get a specific navigation item by ID"""
        try:
            for section in self.layout.sections:
                for item in section.items:
                    if item.id == item_id:
                        return item
                    
                    # Check children
                    for child in item.children:
                        if child.id == item_id:
                            return child
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting navigation item {item_id}: {e}")
            return None
    
    def update_section(self, section_id: str, updates: Dict[str, Any]):
        """Update a section"""
        try:
            section = self.get_section(section_id)
            if section:
                for key, value in updates.items():
                    if hasattr(section, key):
                        setattr(section, key, value)
                
                logger.info(f"Updated section: {section_id}")
            
        except Exception as e:
            logger.error(f"Error updating section {section_id}: {e}")
    
    def update_navigation_item(self, item_id: str, updates: Dict[str, Any]):
        """Update a navigation item"""
        try:
            item = self.get_navigation_item(item_id)
            if item:
                for key, value in updates.items():
                    if hasattr(item, key):
                        setattr(item, key, value)
                
                logger.info(f"Updated navigation item: {item_id}")
            
        except Exception as e:
            logger.error(f"Error updating navigation item {item_id}: {e}")
    
    def add_section(self, section: SidebarSection):
        """Add a new section"""
        try:
            self.layout.sections.append(section)
            # Sort sections by order
            self.layout.sections.sort(key=lambda x: x.order)
            
            logger.info(f"Added section: {section.id}")
            
        except Exception as e:
            logger.error(f"Error adding section: {e}")
    
    def remove_section(self, section_id: str):
        """Remove a section"""
        try:
            self.layout.sections = [s for s in self.layout.sections if s.id != section_id]
            
            logger.info(f"Removed section: {section_id}")
            
        except Exception as e:
            logger.error(f"Error removing section: {e}")
    
    def add_navigation_item(self, section_id: str, item: NavigationItem):
        """Add a navigation item to a section"""
        try:
            section = self.get_section(section_id)
            if section:
                section.items.append(item)
                # Sort items by order
                section.items.sort(key=lambda x: x.order)
                
                logger.info(f"Added navigation item {item.id} to section {section_id}")
            
        except Exception as e:
            logger.error(f"Error adding navigation item: {e}")
    
    def remove_navigation_item(self, item_id: str):
        """Remove a navigation item"""
        try:
            for section in self.layout.sections:
                section.items = [item for item in section.items if item.id != item_id]
                
                # Check children
                for item in section.items:
                    item.children = [child for child in item.children if child.id != item_id]
            
            logger.info(f"Removed navigation item: {item_id}")
            
        except Exception as e:
            logger.error(f"Error removing navigation item: {e}")
    
    def set_active_item(self, item_id: str):
        """Set a navigation item as active"""
        try:
            # Clear all active items
            for section in self.layout.sections:
                for item in section.items:
                    item.is_active = False
                    for child in item.children:
                        child.is_active = False
            
            # Set the specified item as active
            item = self.get_navigation_item(item_id)
            if item:
                item.is_active = True
                
                # Expand parent if it's a child item
                for section in self.layout.sections:
                    for parent_item in section.items:
                        for child in parent_item.children:
                            if child.id == item_id:
                                parent_item.is_expanded = True
                                break
            
            logger.info(f"Set active item: {item_id}")
            
        except Exception as e:
            logger.error(f"Error setting active item: {e}")
    
    def toggle_section_collapse(self, section_id: str):
        """Toggle section collapse state"""
        try:
            section = self.get_section(section_id)
            if section and section.is_collapsible:
                section.is_collapsed = not section.is_collapsed
                
                logger.info(f"Toggled section {section_id} collapse state")
            
        except Exception as e:
            logger.error(f"Error toggling section collapse: {e}")
    
    def toggle_item_expand(self, item_id: str):
        """Toggle item expand state"""
        try:
            item = self.get_navigation_item(item_id)
            if item and item.type == NavigationItemType.DROPDOWN:
                item.is_expanded = not item.is_expanded
                
                logger.info(f"Toggled item {item_id} expand state")
            
        except Exception as e:
            logger.error(f"Error toggling item expand: {e}")
    
    def get_breadcrumb(self, item_id: str) -> List[NavigationItem]:
        """Get breadcrumb path for a navigation item"""
        try:
            breadcrumb = []
            
            # Find the item and build breadcrumb
            for section in self.layout.sections:
                for item in section.items:
                    if item.id == item_id:
                        breadcrumb.append(item)
                        return breadcrumb
                    
                    # Check children
                    for child in item.children:
                        if child.id == item_id:
                            breadcrumb.append(item)
                            breadcrumb.append(child)
                            return breadcrumb
            
            return breadcrumb
            
        except Exception as e:
            logger.error(f"Error getting breadcrumb: {e}")
            return []
    
    def search_navigation(self, query: str) -> List[NavigationItem]:
        """Search navigation items"""
        try:
            results = []
            query_lower = query.lower()
            
            for section in self.layout.sections:
                for item in section.items:
                    # Search in item title
                    if query_lower in item.title.lower():
                        results.append(item)
                    
                    # Search in children
                    for child in item.children:
                        if query_lower in child.title.lower():
                            results.append(child)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching navigation: {e}")
            return []
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences for sidebar layout"""
        try:
            # This would typically fetch from database
            preferences = {
                'collapsed_sections': [],
                'expanded_items': [],
                'favorite_items': [],
                'custom_order': [],
                'theme': self.default_theme,
                'width': self.default_width
            }
            
            return preferences
            
        except Exception as e:
            logger.error(f"Error getting user preferences: {e}")
            return {}
    
    def save_user_preferences(self, user_id: str, preferences: Dict[str, Any]):
        """Save user preferences for sidebar layout"""
        try:
            # This would typically save to database
            logger.info(f"Saved user preferences for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error saving user preferences: {e}")
    
    def apply_user_preferences(self, user_id: str):
        """Apply user preferences to the layout"""
        try:
            preferences = self.get_user_preferences(user_id)
            
            # Apply collapsed sections
            for section_id in preferences.get('collapsed_sections', []):
                section = self.get_section(section_id)
                if section:
                    section.is_collapsed = True
            
            # Apply expanded items
            for item_id in preferences.get('expanded_items', []):
                item = self.get_navigation_item(item_id)
                if item:
                    item.is_expanded = True
            
            # Apply theme
            if 'theme' in preferences:
                self.layout.theme = preferences['theme']
            
            # Apply width
            if 'width' in preferences:
                self.layout.width = preferences['width']
            
            logger.info(f"Applied user preferences for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error applying user preferences: {e}")
    
    def export_layout(self) -> Dict[str, Any]:
        """Export the sidebar layout configuration"""
        try:
            layout_data = {
                'id': self.layout.id,
                'name': self.layout.name,
                'description': self.layout.description,
                'theme': self.layout.theme,
                'width': self.layout.width,
                'is_resizable': self.layout.is_resizable,
                'show_search': self.layout.show_search,
                'show_user_info': self.layout.show_user_info,
                'show_notifications': self.layout.show_notifications,
                'sections': []
            }
            
            for section in self.layout.sections:
                section_data = {
                    'id': section.id,
                    'title': section.title,
                    'icon': section.icon,
                    'order': section.order,
                    'is_collapsible': section.is_collapsible,
                    'is_collapsed': section.is_collapsed,
                    'permissions': section.permissions,
                    'items': []
                }
                
                for item in section.items:
                    item_data = {
                        'id': item.id,
                        'title': item.title,
                        'type': item.type.value,
                        'icon': item.icon,
                        'url': item.url,
                        'badge': item.badge,
                        'tooltip': item.tooltip,
                        'permissions': item.permissions,
                        'is_active': item.is_active,
                        'is_expanded': item.is_expanded,
                        'order': item.order,
                        'metadata': item.metadata,
                        'children': []
                    }
                    
                    for child in item.children:
                        child_data = {
                            'id': child.id,
                            'title': child.title,
                            'type': child.type.value,
                            'icon': child.icon,
                            'url': child.url,
                            'badge': child.badge,
                            'tooltip': child.tooltip,
                            'permissions': child.permissions,
                            'is_active': child.is_active,
                            'is_expanded': child.is_expanded,
                            'order': child.order,
                            'metadata': child.metadata
                        }
                        item_data['children'].append(child_data)
                    
                    section_data['items'].append(item_data)
                
                layout_data['sections'].append(section_data)
            
            return layout_data
            
        except Exception as e:
            logger.error(f"Error exporting layout: {e}")
            return {}
    
    def import_layout(self, layout_data: Dict[str, Any]):
        """Import sidebar layout configuration"""
        try:
            # Update layout properties
            self.layout.name = layout_data.get('name', self.layout.name)
            self.layout.description = layout_data.get('description', self.layout.description)
            self.layout.theme = layout_data.get('theme', self.layout.theme)
            self.layout.width = layout_data.get('width', self.layout.width)
            self.layout.is_resizable = layout_data.get('is_resizable', self.layout.is_resizable)
            self.layout.show_search = layout_data.get('show_search', self.layout.show_search)
            self.layout.show_user_info = layout_data.get('show_user_info', self.layout.show_user_info)
            self.layout.show_notifications = layout_data.get('show_notifications', self.layout.show_notifications)
            
            # Clear existing sections
            self.layout.sections = []
            
            # Import sections
            for section_data in layout_data.get('sections', []):
                section = SidebarSection(
                    id=section_data['id'],
                    title=section_data['title'],
                    icon=section_data['icon'],
                    items=[],
                    order=section_data['order'],
                    is_collapsible=section_data.get('is_collapsible', True),
                    is_collapsed=section_data.get('is_collapsed', False),
                    permissions=section_data.get('permissions', [])
                )
                
                # Import items
                for item_data in section_data.get('items', []):
                    item = NavigationItem(
                        id=item_data['id'],
                        title=item_data['title'],
                        type=NavigationItemType(item_data['type']),
                        icon=item_data.get('icon'),
                        url=item_data.get('url'),
                        badge=item_data.get('badge'),
                        tooltip=item_data.get('tooltip'),
                        permissions=item_data.get('permissions', []),
                        is_active=item_data.get('is_active', False),
                        is_expanded=item_data.get('is_expanded', False),
                        order=item_data.get('order', 0),
                        metadata=item_data.get('metadata', {})
                    )
                    
                    # Import children
                    for child_data in item_data.get('children', []):
                        child = NavigationItem(
                            id=child_data['id'],
                            title=child_data['title'],
                            type=NavigationItemType(child_data['type']),
                            icon=child_data.get('icon'),
                            url=child_data.get('url'),
                            badge=child_data.get('badge'),
                            tooltip=child_data.get('tooltip'),
                            permissions=child_data.get('permissions', []),
                            is_active=child_data.get('is_active', False),
                            is_expanded=child_data.get('is_expanded', False),
                            order=child_data.get('order', 0),
                            metadata=child_data.get('metadata', {})
                        )
                        item.children.append(child)
                    
                    section.items.append(item)
                
                self.layout.sections.append(section)
            
            # Sort sections by order
            self.layout.sections.sort(key=lambda x: x.order)
            
            logger.info("Layout imported successfully")
            
        except Exception as e:
            logger.error(f"Error importing layout: {e}")
    
    def get_layout_statistics(self) -> Dict[str, Any]:
        """Get layout statistics"""
        try:
            stats = {
                'total_sections': len(self.layout.sections),
                'total_items': 0,
                'total_children': 0,
                'active_items': 0,
                'expanded_items': 0,
                'collapsed_sections': 0,
                'sections_by_type': {},
                'items_by_type': {}
            }
            
            for section in self.layout.sections:
                if section.is_collapsed:
                    stats['collapsed_sections'] += 1
                
                stats['total_items'] += len(section.items)
                
                for item in section.items:
                    if item.is_active:
                        stats['active_items'] += 1
                    
                    if item.is_expanded:
                        stats['expanded_items'] += 1
                    
                    stats['total_children'] += len(item.children)
                    
                    # Count by type
                    item_type = item.type.value
                    stats['items_by_type'][item_type] = stats['items_by_type'].get(item_type, 0) + 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting layout statistics: {e}")
            return {}
    
    def validate_layout(self) -> List[str]:
        """Validate the layout configuration"""
        try:
            errors = []
            
            # Check for duplicate IDs
            all_ids = set()
            for section in self.layout.sections:
                if section.id in all_ids:
                    errors.append(f"Duplicate section ID: {section.id}")
                all_ids.add(section.id)
                
                for item in section.items:
                    if item.id in all_ids:
                        errors.append(f"Duplicate item ID: {item.id}")
                    all_ids.add(item.id)
                    
                    for child in item.children:
                        if child.id in all_ids:
                            errors.append(f"Duplicate child ID: {child.id}")
                        all_ids.add(child.id)
            
            # Check for missing required fields
            for section in self.layout.sections:
                if not section.title:
                    errors.append(f"Section {section.id} missing title")
                
                for item in section.items:
                    if not item.title:
                        errors.append(f"Item {item.id} missing title")
                    
                    if item.type == NavigationItemType.LINK and not item.url:
                        errors.append(f"Link item {item.id} missing URL")
            
            return errors
            
        except Exception as e:
            logger.error(f"Error validating layout: {e}")
            return [f"Validation error: {e}"]
    
    def reset_layout(self):
        """Reset layout to default configuration"""
        try:
            self._initialize_layout()
            logger.info("Layout reset to default configuration")
            
        except Exception as e:
            logger.error(f"Error resetting layout: {e}")
    
    def get_mobile_layout(self) -> SidebarLayout:
        """Get mobile-optimized layout"""
        try:
            mobile_layout = SidebarLayout(
                id="general_agilent_mobile_sidebar",
                name="General Agilent Products (Mobile)",
                description="Mobile-optimized sidebar layout",
                sections=[],
                theme=self.default_theme,
                width="100%",
                is_resizable=False,
                show_search=True,
                show_user_info=True,
                show_notifications=True
            )
            
            # Create simplified sections for mobile
            mobile_sections = [
                self._create_mobile_dashboard_section(),
                self._create_mobile_products_section(),
                self._create_mobile_documentation_section(),
                self._create_mobile_support_section(),
                self._create_mobile_ai_section()
            ]
            
            mobile_layout.sections.extend(mobile_sections)
            
            return mobile_layout
            
        except Exception as e:
            logger.error(f"Error creating mobile layout: {e}")
            return self.layout
    
    def _create_mobile_dashboard_section(self) -> SidebarSection:
        """Create mobile dashboard section"""
        return SidebarSection(
            id="mobile_dashboard",
            title="Dashboard",
            icon="dashboard",
            items=[
                NavigationItem(
                    id="mobile_dashboard_overview",
                    title="Overview",
                    type=NavigationItemType.LINK,
                    icon="dashboard",
                    url="/dashboard",
                    order=1
                )
            ],
            order=1,
            is_collapsible=False
        )
    
    def _create_mobile_products_section(self) -> SidebarSection:
        """Create mobile products section"""
        return SidebarSection(
            id="mobile_products",
            title="Products",
            icon="products",
            items=[
                NavigationItem(
                    id="mobile_products_all",
                    title="All Products",
                    type=NavigationItemType.LINK,
                    icon="products",
                    url="/products",
                    order=1
                )
            ],
            order=2,
            is_collapsible=False
        )
    
    def _create_mobile_documentation_section(self) -> SidebarSection:
        """Create mobile documentation section"""
        return SidebarSection(
            id="mobile_documentation",
            title="Documentation",
            icon="documentation",
            items=[
                NavigationItem(
                    id="mobile_docs_all",
                    title="All Documentation",
                    type=NavigationItemType.LINK,
                    icon="documentation",
                    url="/documentation",
                    order=1
                )
            ],
            order=3,
            is_collapsible=False
        )
    
    def _create_mobile_support_section(self) -> SidebarSection:
        """Create mobile support section"""
        return SidebarSection(
            id="mobile_support",
            title="Support",
            icon="support",
            items=[
                NavigationItem(
                    id="mobile_support_contact",
                    title="Contact Support",
                    type=NavigationItemType.LINK,
                    icon="support",
                    url="/support/contact",
                    order=1
                )
            ],
            order=4,
            is_collapsible=False
        )
    
    def _create_mobile_ai_section(self) -> SidebarSection:
        """Create mobile AI section"""
        return SidebarSection(
            id="mobile_ai",
            title="AI Assistant",
            icon="ai",
            items=[
                NavigationItem(
                    id="mobile_ai_chat",
                    title="AI Chat",
                    type=NavigationItemType.LINK,
                    icon="chat",
                    url="/ai/chat",
                    order=1
                )
            ],
            order=5,
            is_collapsible=False
        )
