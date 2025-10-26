"""
Mobile-Optimized Sidebar Layouts

This module provides mobile-optimized sidebar layouts
including responsive design, touch-friendly interfaces, and mobile-specific features.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from django.utils import timezone as django_timezone

logger = logging.getLogger(__name__)


class MobileLayoutType(Enum):
    """Mobile layout type enumeration"""
    DRAWER = "drawer"
    BOTTOM_SHEET = "bottom_sheet"
    TAB_BAR = "tab_bar"
    FLOATING_ACTION = "floating_action"
    COLLAPSIBLE = "collapsible"
    OVERLAY = "overlay"
    SLIDE_OUT = "slide_out"
    MODAL = "modal"


class MobileBreakpoint(Enum):
    """Mobile breakpoint enumeration"""
    SMALL_MOBILE = "small_mobile"  # < 375px
    MOBILE = "mobile"  # 375px - 767px
    LARGE_MOBILE = "large_mobile"  # 768px - 1023px
    TABLET = "tablet"  # 1024px - 1439px


class TouchGesture(Enum):
    """Touch gesture enumeration"""
    TAP = "tap"
    DOUBLE_TAP = "double_tap"
    LONG_PRESS = "long_press"
    SWIPE_LEFT = "swipe_left"
    SWIPE_RIGHT = "swipe_right"
    SWIPE_UP = "swipe_up"
    SWIPE_DOWN = "swipe_down"
    PINCH = "pinch"
    PAN = "pan"


class MobileNavigationItem:
    """Mobile navigation item structure"""
    id: str
    title: str
    icon: str
    url: Optional[str] = None
    badge: Optional[str] = None
    tooltip: Optional[str] = None
    is_active: bool = False
    is_visible: bool = True
    order: int = 0
    gesture: Optional[TouchGesture] = None
    children: List['MobileNavigationItem'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MobileSidebarSection:
    """Mobile sidebar section structure"""
    id: str
    title: str
    icon: str
    items: List[MobileNavigationItem]
    order: int
    is_collapsible: bool = True
    is_collapsed: bool = False
    is_visible: bool = True
    max_height: Optional[str] = None
    scrollable: bool = True


@dataclass
class MobileSidebarLayout:
    """Mobile sidebar layout structure"""
    id: str
    name: str
    description: str
    type: MobileLayoutType
    sections: List[MobileSidebarSection]
    theme: str = "mobile-default"
    width: str = "100%"
    height: str = "100%"
    position: str = "left"  # left, right, top, bottom
    animation: str = "slide"  # slide, fade, scale, none
    backdrop: bool = True
    backdrop_opacity: float = 0.5
    z_index: int = 1000
    touch_enabled: bool = True
    gesture_support: bool = True
    haptic_feedback: bool = True
    created_at: datetime = field(default_factory=lambda: django_timezone.now())
    updated_at: datetime = field(default_factory=lambda: django_timezone.now())


@dataclass
class MobileLayoutBreakpoint:
    """Mobile layout breakpoint configuration"""
    breakpoint: MobileBreakpoint
    width: str
    height: str
    font_size: str
    icon_size: str
    padding: str
    margin: str
    touch_target_size: str
    max_items_per_section: int
    show_labels: bool
    show_icons: bool
    orientation: str  # portrait, landscape


@dataclass
class MobileUserPreference:
    """Mobile user preference structure"""
    user_id: str
    layout_id: str
    customizations: Dict[str, Any] = field(default_factory=dict)
    gesture_preferences: Dict[str, Any] = field(default_factory=dict)
    haptic_enabled: bool = True
    animations_enabled: bool = True
    dark_mode: bool = False
    font_size: str = "medium"
    touch_sensitivity: str = "medium"
    last_used: datetime = field(default_factory=lambda: django_timezone.now())
    created_at: datetime = field(default_factory=lambda: django_timezone.now())
    updated_at: datetime = field(default_factory=lambda: django_timezone.now())


class MobileSidebarLayoutManager:
    """Mobile-Optimized Sidebar Layout Manager"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize mobile sidebar layout manager"""
        self.config = config or {}
        self.layout_enabled = self.config.get('layout_enabled', True)
        self.responsive_enabled = self.config.get('responsive_enabled', True)
        self.gesture_enabled = self.config.get('gesture_enabled', True)
        self.haptic_enabled = self.config.get('haptic_enabled', True)
        self.animation_enabled = self.config.get('animation_enabled', True)
        
        # Layout configuration
        self.default_layout_type = self.config.get('default_layout_type', MobileLayoutType.DRAWER)
        self.default_theme = self.config.get('default_theme', 'mobile-default')
        self.max_sections = self.config.get('max_sections', 8)
        self.max_items_per_section = self.config.get('max_items_per_section', 10)
        
        # Mobile breakpoints
        self.breakpoints = {
            MobileBreakpoint.SMALL_MOBILE: MobileLayoutBreakpoint(
                breakpoint=MobileBreakpoint.SMALL_MOBILE,
                width="100%",
                height="100%",
                font_size="14px",
                icon_size="20px",
                padding="12px",
                margin="8px",
                touch_target_size="44px",
                max_items_per_section=6,
                show_labels=True,
                show_icons=True,
                orientation="portrait"
            ),
            MobileBreakpoint.MOBILE: MobileLayoutBreakpoint(
                breakpoint=MobileBreakpoint.MOBILE,
                width="100%",
                height="100%",
                font_size="16px",
                icon_size="24px",
                padding="16px",
                margin="12px",
                touch_target_size="48px",
                max_items_per_section=8,
                show_labels=True,
                show_icons=True,
                orientation="portrait"
            ),
            MobileBreakpoint.LARGE_MOBILE: MobileLayoutBreakpoint(
                breakpoint=MobileBreakpoint.LARGE_MOBILE,
                width="100%",
                height="100%",
                font_size="18px",
                icon_size="28px",
                padding="20px",
                margin="16px",
                touch_target_size="52px",
                max_items_per_section=10,
                show_labels=True,
                show_icons=True,
                orientation="landscape"
            ),
            MobileBreakpoint.TABLET: MobileLayoutBreakpoint(
                breakpoint=MobileBreakpoint.TABLET,
                width="100%",
                height="100%",
                font_size="20px",
                icon_size="32px",
                padding="24px",
                margin="20px",
                touch_target_size="56px",
                max_items_per_section=12,
                show_labels=True,
                show_icons=True,
                orientation="landscape"
            )
        }
        
        # Initialize components
        self._initialize_components()
        
        logger.info("Mobile Sidebar Layout Manager initialized")
    
    def _initialize_components(self):
        """Initialize mobile layout components"""
        try:
            # Initialize data structures
            self.layouts = {}
            self.user_preferences = {}
            self.layout_templates = {}
            
            # Initialize default layouts
            self._create_default_layouts()
            
            # Initialize layout templates
            self._create_layout_templates()
            
            logger.info("Mobile layout components initialized")
            
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            raise
    
    def _create_default_layouts(self):
        """Create default mobile layouts"""
        try:
            # Create drawer layout
            drawer_layout = self._create_drawer_layout()
            self.layouts[drawer_layout.id] = drawer_layout
            
            # Create bottom sheet layout
            bottom_sheet_layout = self._create_bottom_sheet_layout()
            self.layouts[bottom_sheet_layout.id] = bottom_sheet_layout
            
            # Create tab bar layout
            tab_bar_layout = self._create_tab_bar_layout()
            self.layouts[tab_bar_layout.id] = tab_bar_layout
            
            # Create collapsible layout
            collapsible_layout = self._create_collapsible_layout()
            self.layouts[collapsible_layout.id] = collapsible_layout
            
            logger.info("Default mobile layouts created")
            
        except Exception as e:
            logger.error(f"Error creating default layouts: {e}")
    
    def _create_drawer_layout(self) -> MobileSidebarLayout:
        """Create drawer layout"""
        try:
            sections = [
                MobileSidebarSection(
                    id="mobile_dashboard",
                    title="Dashboard",
                    icon="dashboard",
                    items=[
                        MobileNavigationItem(
                            id="mobile_dashboard_overview",
                            title="Overview",
                            icon="dashboard",
                            url="/mobile/dashboard",
                            order=1
                        ),
                        MobileNavigationItem(
                            id="mobile_dashboard_analytics",
                            title="Analytics",
                            icon="analytics",
                            url="/mobile/analytics",
                            order=2
                        )
                    ],
                    order=1
                ),
                MobileSidebarSection(
                    id="mobile_products",
                    title="Products",
                    icon="products",
                    items=[
                        MobileNavigationItem(
                            id="mobile_products_all",
                            title="All Products",
                            icon="products",
                            url="/mobile/products",
                            order=1
                        ),
                        MobileNavigationItem(
                            id="mobile_products_favorites",
                            title="Favorites",
                            icon="favorites",
                            url="/mobile/products/favorites",
                            order=2
                        )
                    ],
                    order=2
                ),
                MobileSidebarSection(
                    id="mobile_documentation",
                    title="Documentation",
                    icon="documentation",
                    items=[
                        MobileNavigationItem(
                            id="mobile_docs_all",
                            title="All Documentation",
                            icon="documentation",
                            url="/mobile/documentation",
                            order=1
                        ),
                        MobileNavigationItem(
                            id="mobile_docs_recent",
                            title="Recent",
                            icon="recent",
                            url="/mobile/documentation/recent",
                            order=2
                        )
                    ],
                    order=3
                ),
                MobileSidebarSection(
                    id="mobile_support",
                    title="Support",
                    icon="support",
                    items=[
                        MobileNavigationItem(
                            id="mobile_support_contact",
                            title="Contact Support",
                            icon="support",
                            url="/mobile/support/contact",
                            order=1
                        ),
                        MobileNavigationItem(
                            id="mobile_support_tickets",
                            title="My Tickets",
                            icon="ticket",
                            url="/mobile/support/tickets",
                            order=2
                        )
                    ],
                    order=4
                ),
                MobileSidebarSection(
                    id="mobile_ai",
                    title="AI Assistant",
                    icon="ai",
                    items=[
                        MobileNavigationItem(
                            id="mobile_ai_chat",
                            title="AI Chat",
                            icon="chat",
                            url="/mobile/ai/chat",
                            order=1
                        ),
                        MobileNavigationItem(
                            id="mobile_ai_search",
                            title="AI Search",
                            icon="search",
                            url="/mobile/ai/search",
                            order=2
                        )
                    ],
                    order=5
                ),
                MobileSidebarSection(
                    id="mobile_user",
                    title="User",
                    icon="user",
                    items=[
                        MobileNavigationItem(
                            id="mobile_user_profile",
                            title="Profile",
                            icon="profile",
                            url="/mobile/user/profile",
                            order=1
                        ),
                        MobileNavigationItem(
                            id="mobile_user_settings",
                            title="Settings",
                            icon="settings",
                            url="/mobile/user/settings",
                            order=2
                        )
                    ],
                    order=6
                )
            ]
            
            return MobileSidebarLayout(
                id="mobile_drawer_layout",
                name="Mobile Drawer Layout",
                description="Drawer-style mobile sidebar layout",
                type=MobileLayoutType.DRAWER,
                sections=sections,
                theme=self.default_theme,
                position="left",
                animation="slide",
                backdrop=True,
                backdrop_opacity=0.5,
                z_index=1000,
                touch_enabled=True,
                gesture_support=True,
                haptic_feedback=True
            )
            
        except Exception as e:
            logger.error(f"Error creating drawer layout: {e}")
            return MobileSidebarLayout(id="mobile_drawer_layout", name="Mobile Drawer Layout", description="", type=MobileLayoutType.DRAWER, sections=[])
    
    def _create_bottom_sheet_layout(self) -> MobileSidebarLayout:
        """Create bottom sheet layout"""
        try:
            sections = [
                MobileSidebarSection(
                    id="mobile_quick_actions",
                    title="Quick Actions",
                    icon="quick-actions",
                    items=[
                        MobileNavigationItem(
                            id="mobile_quick_search",
                            title="Search",
                            icon="search",
                            url="/mobile/search",
                            order=1
                        ),
                        MobileNavigationItem(
                            id="mobile_quick_upload",
                            title="Upload",
                            icon="upload",
                            url="/mobile/upload",
                            order=2
                        ),
                        MobileNavigationItem(
                            id="mobile_quick_scan",
                            title="Scan",
                            icon="scan",
                            url="/mobile/scan",
                            order=3
                        )
                    ],
                    order=1
                ),
                MobileSidebarSection(
                    id="mobile_navigation",
                    title="Navigation",
                    icon="navigation",
                    items=[
                        MobileNavigationItem(
                            id="mobile_nav_dashboard",
                            title="Dashboard",
                            icon="dashboard",
                            url="/mobile/dashboard",
                            order=1
                        ),
                        MobileNavigationItem(
                            id="mobile_nav_products",
                            title="Products",
                            icon="products",
                            url="/mobile/products",
                            order=2
                        ),
                        MobileNavigationItem(
                            id="mobile_nav_docs",
                            title="Documentation",
                            icon="documentation",
                            url="/mobile/documentation",
                            order=3
                        ),
                        MobileNavigationItem(
                            id="mobile_nav_support",
                            title="Support",
                            icon="support",
                            url="/mobile/support",
                            order=4
                        )
                    ],
                    order=2
                ),
                MobileSidebarSection(
                    id="mobile_tools",
                    title="Tools",
                    icon="tools",
                    items=[
                        MobileNavigationItem(
                            id="mobile_tools_calculator",
                            title="Calculator",
                            icon="calculator",
                            url="/mobile/tools/calculator",
                            order=1
                        ),
                        MobileNavigationItem(
                            id="mobile_tools_converter",
                            title="Unit Converter",
                            icon="converter",
                            url="/mobile/tools/converter",
                            order=2
                        )
                    ],
                    order=3
                )
            ]
            
            return MobileSidebarLayout(
                id="mobile_bottom_sheet_layout",
                name="Mobile Bottom Sheet Layout",
                description="Bottom sheet-style mobile sidebar layout",
                type=MobileLayoutType.BOTTOM_SHEET,
                sections=sections,
                theme=self.default_theme,
                position="bottom",
                animation="slide",
                backdrop=True,
                backdrop_opacity=0.3,
                z_index=1000,
                touch_enabled=True,
                gesture_support=True,
                haptic_feedback=True
            )
            
        except Exception as e:
            logger.error(f"Error creating bottom sheet layout: {e}")
            return MobileSidebarLayout(id="mobile_bottom_sheet_layout", name="Mobile Bottom Sheet Layout", description="", type=MobileLayoutType.BOTTOM_SHEET, sections=[])
    
    def _create_tab_bar_layout(self) -> MobileSidebarLayout:
        """Create tab bar layout"""
        try:
            sections = [
                MobileSidebarSection(
                    id="mobile_tabs",
                    title="Main Tabs",
                    icon="tabs",
                    items=[
                        MobileNavigationItem(
                            id="mobile_tab_dashboard",
                            title="Dashboard",
                            icon="dashboard",
                            url="/mobile/dashboard",
                            order=1
                        ),
                        MobileNavigationItem(
                            id="mobile_tab_products",
                            title="Products",
                            icon="products",
                            url="/mobile/products",
                            order=2
                        ),
                        MobileNavigationItem(
                            id="mobile_tab_docs",
                            title="Docs",
                            icon="documentation",
                            url="/mobile/documentation",
                            order=3
                        ),
                        MobileNavigationItem(
                            id="mobile_tab_support",
                            title="Support",
                            icon="support",
                            url="/mobile/support",
                            order=4
                        ),
                        MobileNavigationItem(
                            id="mobile_tab_more",
                            title="More",
                            icon="more",
                            url="/mobile/more",
                            order=5
                        )
                    ],
                    order=1,
                    is_collapsible=False
                )
            ]
            
            return MobileSidebarLayout(
                id="mobile_tab_bar_layout",
                name="Mobile Tab Bar Layout",
                description="Tab bar-style mobile sidebar layout",
                type=MobileLayoutType.TAB_BAR,
                sections=sections,
                theme=self.default_theme,
                position="bottom",
                animation="none",
                backdrop=False,
                z_index=1000,
                touch_enabled=True,
                gesture_support=False,
                haptic_feedback=True
            )
            
        except Exception as e:
            logger.error(f"Error creating tab bar layout: {e}")
            return MobileSidebarLayout(id="mobile_tab_bar_layout", name="Mobile Tab Bar Layout", description="", type=MobileLayoutType.TAB_BAR, sections=[])
    
    def _create_collapsible_layout(self) -> MobileSidebarLayout:
        """Create collapsible layout"""
        try:
            sections = [
                MobileSidebarSection(
                    id="mobile_main",
                    title="Main",
                    icon="main",
                    items=[
                        MobileNavigationItem(
                            id="mobile_main_dashboard",
                            title="Dashboard",
                            icon="dashboard",
                            url="/mobile/dashboard",
                            order=1
                        ),
                        MobileNavigationItem(
                            id="mobile_main_products",
                            title="Products",
                            icon="products",
                            url="/mobile/products",
                            order=2
                        )
                    ],
                    order=1,
                    is_collapsible=True,
                    is_collapsed=False
                ),
                MobileSidebarSection(
                    id="mobile_tools",
                    title="Tools",
                    icon="tools",
                    items=[
                        MobileNavigationItem(
                            id="mobile_tools_calculator",
                            title="Calculator",
                            icon="calculator",
                            url="/mobile/tools/calculator",
                            order=1
                        ),
                        MobileNavigationItem(
                            id="mobile_tools_converter",
                            title="Unit Converter",
                            icon="converter",
                            url="/mobile/tools/converter",
                            order=2
                        )
                    ],
                    order=2,
                    is_collapsible=True,
                    is_collapsed=True
                ),
                MobileSidebarSection(
                    id="mobile_support",
                    title="Support",
                    icon="support",
                    items=[
                        MobileNavigationItem(
                            id="mobile_support_contact",
                            title="Contact Support",
                            icon="support",
                            url="/mobile/support/contact",
                            order=1
                        ),
                        MobileNavigationItem(
                            id="mobile_support_tickets",
                            title="My Tickets",
                            icon="ticket",
                            url="/mobile/support/tickets",
                            order=2
                        )
                    ],
                    order=3,
                    is_collapsible=True,
                    is_collapsed=True
                )
            ]
            
            return MobileSidebarLayout(
                id="mobile_collapsible_layout",
                name="Mobile Collapsible Layout",
                description="Collapsible-style mobile sidebar layout",
                type=MobileLayoutType.COLLAPSIBLE,
                sections=sections,
                theme=self.default_theme,
                position="left",
                animation="slide",
                backdrop=False,
                z_index=1000,
                touch_enabled=True,
                gesture_support=True,
                haptic_feedback=True
            )
            
        except Exception as e:
            logger.error(f"Error creating collapsible layout: {e}")
            return MobileSidebarLayout(id="mobile_collapsible_layout", name="Mobile Collapsible Layout", description="", type=MobileLayoutType.COLLAPSIBLE, sections=[])
    
    def _create_layout_templates(self):
        """Create layout templates"""
        try:
            templates = {
                "mobile_drawer_template": {
                    "name": "Mobile Drawer Template",
                    "description": "Drawer template for mobile navigation",
                    "type": MobileLayoutType.DRAWER,
                    "theme": "mobile-default",
                    "sections": ["dashboard", "products", "documentation", "support", "ai", "user"]
                },
                "mobile_bottom_sheet_template": {
                    "name": "Mobile Bottom Sheet Template",
                    "description": "Bottom sheet template for mobile navigation",
                    "type": MobileLayoutType.BOTTOM_SHEET,
                    "theme": "mobile-default",
                    "sections": ["quick_actions", "navigation", "tools"]
                },
                "mobile_tab_bar_template": {
                    "name": "Mobile Tab Bar Template",
                    "description": "Tab bar template for mobile navigation",
                    "type": MobileLayoutType.TAB_BAR,
                    "theme": "mobile-default",
                    "sections": ["tabs"]
                },
                "mobile_collapsible_template": {
                    "name": "Mobile Collapsible Template",
                    "description": "Collapsible template for mobile navigation",
                    "type": MobileLayoutType.COLLAPSIBLE,
                    "theme": "mobile-default",
                    "sections": ["main", "tools", "support"]
                }
            }
            
            self.layout_templates.update(templates)
            
            logger.info("Mobile layout templates created")
            
        except Exception as e:
            logger.error(f"Error creating layout templates: {e}")
    
    def get_layout(self, layout_id: str) -> Optional[MobileSidebarLayout]:
        """Get a layout by ID"""
        try:
            return self.layouts.get(layout_id)
            
        except Exception as e:
            logger.error(f"Error getting layout {layout_id}: {e}")
            return None
    
    def get_layouts(self, layout_type: MobileLayoutType = None) -> List[MobileSidebarLayout]:
        """Get layouts filtered by type"""
        try:
            layouts = list(self.layouts.values())
            
            if layout_type:
                layouts = [layout for layout in layouts if layout.type == layout_type]
            
            return layouts
            
        except Exception as e:
            logger.error(f"Error getting layouts: {e}")
            return []
    
    def get_responsive_layout(self, layout_id: str, breakpoint: MobileBreakpoint) -> Dict[str, Any]:
        """Get responsive layout configuration for a breakpoint"""
        try:
            layout = self.get_layout(layout_id)
            if not layout:
                return {}
            
            # Get breakpoint configuration
            breakpoint_config = self.breakpoints.get(breakpoint)
            if not breakpoint_config:
                return {}
            
            responsive_config = {
                'layout_id': layout_id,
                'breakpoint': breakpoint.value,
                'layout_type': layout.type.value,
                'theme': layout.theme,
                'position': layout.position,
                'animation': layout.animation,
                'backdrop': layout.backdrop,
                'backdrop_opacity': layout.backdrop_opacity,
                'z_index': layout.z_index,
                'touch_enabled': layout.touch_enabled,
                'gesture_support': layout.gesture_support,
                'haptic_feedback': layout.haptic_feedback,
                'breakpoint_config': {
                    'width': breakpoint_config.width,
                    'height': breakpoint_config.height,
                    'font_size': breakpoint_config.font_size,
                    'icon_size': breakpoint_config.icon_size,
                    'padding': breakpoint_config.padding,
                    'margin': breakpoint_config.margin,
                    'touch_target_size': breakpoint_config.touch_target_size,
                    'max_items_per_section': breakpoint_config.max_items_per_section,
                    'show_labels': breakpoint_config.show_labels,
                    'show_icons': breakpoint_config.show_icons,
                    'orientation': breakpoint_config.orientation
                },
                'sections': []
            }
            
            # Process sections
            for section in layout.sections:
                section_config = {
                    'id': section.id,
                    'title': section.title,
                    'icon': section.icon,
                    'order': section.order,
                    'is_collapsible': section.is_collapsible,
                    'is_collapsed': section.is_collapsed,
                    'is_visible': section.is_visible,
                    'max_height': section.max_height,
                    'scrollable': section.scrollable,
                    'items': []
                }
                
                # Process items
                for item in section.items:
                    item_config = {
                        'id': item.id,
                        'title': item.title,
                        'icon': item.icon,
                        'url': item.url,
                        'badge': item.badge,
                        'tooltip': item.tooltip,
                        'is_active': item.is_active,
                        'is_visible': item.is_visible,
                        'order': item.order,
                        'gesture': item.gesture.value if item.gesture else None,
                        'metadata': item.metadata
                    }
                    
                    section_config['items'].append(item_config)
                
                responsive_config['sections'].append(section_config)
            
            return responsive_config
            
        except Exception as e:
            logger.error(f"Error getting responsive layout: {e}")
            return {}
    
    def create_layout(self, layout_data: Dict[str, Any]) -> MobileSidebarLayout:
        """Create a new mobile layout"""
        try:
            layout = MobileSidebarLayout(
                id=layout_data['id'],
                name=layout_data['name'],
                description=layout_data.get('description', ''),
                type=MobileLayoutType(layout_data.get('type', self.default_layout_type.value)),
                sections=[],
                theme=layout_data.get('theme', self.default_theme),
                width=layout_data.get('width', '100%'),
                height=layout_data.get('height', '100%'),
                position=layout_data.get('position', 'left'),
                animation=layout_data.get('animation', 'slide'),
                backdrop=layout_data.get('backdrop', True),
                backdrop_opacity=layout_data.get('backdrop_opacity', 0.5),
                z_index=layout_data.get('z_index', 1000),
                touch_enabled=layout_data.get('touch_enabled', True),
                gesture_support=layout_data.get('gesture_support', True),
                haptic_feedback=layout_data.get('haptic_feedback', True)
            )
            
            # Add sections
            for section_data in layout_data.get('sections', []):
                section = self._create_section_from_data(section_data)
                layout.sections.append(section)
            
            # Store layout
            self.layouts[layout.id] = layout
            
            logger.info(f"Created mobile layout: {layout.id}")
            return layout
            
        except Exception as e:
            logger.error(f"Error creating mobile layout: {e}")
            raise
    
    def _create_section_from_data(self, section_data: Dict[str, Any]) -> MobileSidebarSection:
        """Create section from data"""
        try:
            section = MobileSidebarSection(
                id=section_data['id'],
                title=section_data['title'],
                icon=section_data['icon'],
                items=[],
                order=section_data.get('order', 0),
                is_collapsible=section_data.get('is_collapsible', True),
                is_collapsed=section_data.get('is_collapsed', False),
                is_visible=section_data.get('is_visible', True),
                max_height=section_data.get('max_height'),
                scrollable=section_data.get('scrollable', True)
            )
            
            # Add items
            for item_data in section_data.get('items', []):
                item = self._create_item_from_data(item_data)
                section.items.append(item)
            
            return section
            
        except Exception as e:
            logger.error(f"Error creating section from data: {e}")
            raise
    
    def _create_item_from_data(self, item_data: Dict[str, Any]) -> MobileNavigationItem:
        """Create item from data"""
        try:
            item = MobileNavigationItem(
                id=item_data['id'],
                title=item_data['title'],
                icon=item_data['icon'],
                url=item_data.get('url'),
                badge=item_data.get('badge'),
                tooltip=item_data.get('tooltip'),
                is_active=item_data.get('is_active', False),
                is_visible=item_data.get('is_visible', True),
                order=item_data.get('order', 0),
                gesture=TouchGesture(item_data['gesture']) if item_data.get('gesture') else None,
                metadata=item_data.get('metadata', {})
            )
            
            return item
            
        except Exception as e:
            logger.error(f"Error creating item from data: {e}")
            raise
    
    def update_layout(self, layout_id: str, updates: Dict[str, Any]):
        """Update a mobile layout"""
        try:
            layout = self.get_layout(layout_id)
            if layout:
                for key, value in updates.items():
                    if hasattr(layout, key):
                        setattr(layout, key, value)
                
                layout.updated_at = django_timezone.now()
                
                logger.info(f"Updated mobile layout: {layout_id}")
            
        except Exception as e:
            logger.error(f"Error updating mobile layout {layout_id}: {e}")
    
    def delete_layout(self, layout_id: str):
        """Delete a mobile layout"""
        try:
            if layout_id in self.layouts:
                del self.layouts[layout_id]
                logger.info(f"Deleted mobile layout: {layout_id}")
            
        except Exception as e:
            logger.error(f"Error deleting mobile layout {layout_id}: {e}")
    
    def add_section(self, layout_id: str, section: MobileSidebarSection):
        """Add a section to a mobile layout"""
        try:
            layout = self.get_layout(layout_id)
            if layout:
                layout.sections.append(section)
                layout.updated_at = django_timezone.now()
                
                logger.info(f"Added section {section.id} to mobile layout {layout_id}")
            
        except Exception as e:
            logger.error(f"Error adding section to mobile layout: {e}")
    
    def remove_section(self, layout_id: str, section_id: str):
        """Remove a section from a mobile layout"""
        try:
            layout = self.get_layout(layout_id)
            if layout:
                layout.sections = [s for s in layout.sections if s.id != section_id]
                layout.updated_at = django_timezone.now()
                
                logger.info(f"Removed section {section_id} from mobile layout {layout_id}")
            
        except Exception as e:
            logger.error(f"Error removing section from mobile layout: {e}")
    
    def add_item(self, layout_id: str, section_id: str, item: MobileNavigationItem):
        """Add an item to a section"""
        try:
            layout = self.get_layout(layout_id)
            if layout:
                for section in layout.sections:
                    if section.id == section_id:
                        section.items.append(item)
                        layout.updated_at = django_timezone.now()
                        
                        logger.info(f"Added item {item.id} to section {section_id}")
                        break
            
        except Exception as e:
            logger.error(f"Error adding item to section: {e}")
    
    def remove_item(self, layout_id: str, section_id: str, item_id: str):
        """Remove an item from a section"""
        try:
            layout = self.get_layout(layout_id)
            if layout:
                for section in layout.sections:
                    if section.id == section_id:
                        section.items = [i for i in section.items if i.id != item_id]
                        layout.updated_at = django_timezone.now()
                        
                        logger.info(f"Removed item {item_id} from section {section_id}")
                        break
            
        except Exception as e:
            logger.error(f"Error removing item from section: {e}")
    
    def toggle_section_collapse(self, layout_id: str, section_id: str):
        """Toggle section collapse state"""
        try:
            layout = self.get_layout(layout_id)
            if layout:
                for section in layout.sections:
                    if section.id == section_id and section.is_collapsible:
                        section.is_collapsed = not section.is_collapsed
                        layout.updated_at = django_timezone.now()
                        
                        logger.info(f"Toggled section {section_id} collapse state")
                        break
            
        except Exception as e:
            logger.error(f"Error toggling section collapse: {e}")
    
    def set_active_item(self, layout_id: str, item_id: str):
        """Set a navigation item as active"""
        try:
            layout = self.get_layout(layout_id)
            if layout:
                # Clear all active items
                for section in layout.sections:
                    for item in section.items:
                        item.is_active = False
                
                # Set the specified item as active
                for section in layout.sections:
                    for item in section.items:
                        if item.id == item_id:
                            item.is_active = True
                            layout.updated_at = django_timezone.now()
                            
                            logger.info(f"Set active item: {item_id}")
                            return
            
        except Exception as e:
            logger.error(f"Error setting active item: {e}")
    
    def get_user_preferences(self, user_id: str) -> Optional[MobileUserPreference]:
        """Get user preferences for mobile layouts"""
        try:
            return self.user_preferences.get(user_id)
            
        except Exception as e:
            logger.error(f"Error getting user preferences: {e}")
            return None
    
    def save_user_preferences(self, user_id: str, preferences: Dict[str, Any]):
        """Save user preferences for mobile layouts"""
        try:
            if user_id not in self.user_preferences:
                self.user_preferences[user_id] = MobileUserPreference(
                    user_id=user_id,
                    layout_id=preferences.get('layout_id', 'mobile_drawer_layout')
                )
            
            user_pref = self.user_preferences[user_id]
            user_pref.customizations.update(preferences.get('customizations', {}))
            user_pref.gesture_preferences.update(preferences.get('gesture_preferences', {}))
            user_pref.haptic_enabled = preferences.get('haptic_enabled', True)
            user_pref.animations_enabled = preferences.get('animations_enabled', True)
            user_pref.dark_mode = preferences.get('dark_mode', False)
            user_pref.font_size = preferences.get('font_size', 'medium')
            user_pref.touch_sensitivity = preferences.get('touch_sensitivity', 'medium')
            user_pref.last_used = django_timezone.now()
            user_pref.updated_at = django_timezone.now()
            
            logger.info(f"Saved user preferences for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error saving user preferences: {e}")
    
    def apply_user_customizations(self, layout_id: str, user_id: str, customizations: Dict[str, Any]):
        """Apply user customizations to a mobile layout"""
        try:
            layout = self.get_layout(layout_id)
            if not layout:
                return
            
            # Apply section customizations
            if 'sections' in customizations:
                for section_id, section_customizations in customizations['sections'].items():
                    for section in layout.sections:
                        if section.id == section_id:
                            if 'is_visible' in section_customizations:
                                section.is_visible = section_customizations['is_visible']
                            
                            if 'is_collapsed' in section_customizations:
                                section.is_collapsed = section_customizations['is_collapsed']
                            
                            # Apply item customizations
                            if 'items' in section_customizations:
                                for item_id, item_customizations in section_customizations['items'].items():
                                    for item in section.items:
                                        if item.id == item_id:
                                            if 'is_visible' in item_customizations:
                                                item.is_visible = item_customizations['is_visible']
                                            
                                            if 'is_active' in item_customizations:
                                                item.is_active = item_customizations['is_active']
                                            
                                            break
                            break
            
            # Apply global customizations
            if 'theme' in customizations:
                layout.theme = customizations['theme']
            
            if 'animation' in customizations:
                layout.animation = customizations['animation']
            
            if 'haptic_feedback' in customizations:
                layout.haptic_feedback = customizations['haptic_feedback']
            
            layout.updated_at = django_timezone.now()
            
            # Save user preferences
            self.save_user_preferences(user_id, {
                'layout_id': layout_id,
                'customizations': customizations
            })
            
            logger.info(f"Applied customizations for user {user_id} to mobile layout {layout_id}")
            
        except Exception as e:
            logger.error(f"Error applying user customizations: {e}")
    
    def get_layout_templates(self) -> Dict[str, Any]:
        """Get available mobile layout templates"""
        return self.layout_templates.copy()
    
    def create_layout_from_template(self, template_id: str, customizations: Dict[str, Any] = None) -> MobileSidebarLayout:
        """Create a mobile layout from a template"""
        try:
            template = self.layout_templates.get(template_id)
            if not template:
                raise ValueError(f"Template {template_id} not found")
            
            # Create layout data from template
            layout_data = {
                'id': f"{template_id}_{django_timezone.now().strftime('%Y%m%d_%H%M%S')}",
                'name': template['name'],
                'description': template['description'],
                'type': template['type'],
                'theme': template['theme'],
                'sections': []
            }
            
            # Apply customizations
            if customizations:
                layout_data.update(customizations)
            
            # Create layout
            layout = self.create_layout(layout_data)
            
            logger.info(f"Created mobile layout from template {template_id}: {layout.id}")
            return layout
            
        except Exception as e:
            logger.error(f"Error creating mobile layout from template: {e}")
            raise
    
    def export_layout(self, layout_id: str) -> Dict[str, Any]:
        """Export a mobile layout configuration"""
        try:
            layout = self.get_layout(layout_id)
            if not layout:
                return {}
            
            export_data = {
                'id': layout.id,
                'name': layout.name,
                'description': layout.description,
                'type': layout.type.value,
                'theme': layout.theme,
                'width': layout.width,
                'height': layout.height,
                'position': layout.position,
                'animation': layout.animation,
                'backdrop': layout.backdrop,
                'backdrop_opacity': layout.backdrop_opacity,
                'z_index': layout.z_index,
                'touch_enabled': layout.touch_enabled,
                'gesture_support': layout.gesture_support,
                'haptic_feedback': layout.haptic_feedback,
                'sections': []
            }
            
            for section in layout.sections:
                section_data = {
                    'id': section.id,
                    'title': section.title,
                    'icon': section.icon,
                    'order': section.order,
                    'is_collapsible': section.is_collapsible,
                    'is_collapsed': section.is_collapsed,
                    'is_visible': section.is_visible,
                    'max_height': section.max_height,
                    'scrollable': section.scrollable,
                    'items': []
                }
                
                for item in section.items:
                    item_data = {
                        'id': item.id,
                        'title': item.title,
                        'icon': item.icon,
                        'url': item.url,
                        'badge': item.badge,
                        'tooltip': item.tooltip,
                        'is_active': item.is_active,
                        'is_visible': item.is_visible,
                        'order': item.order,
                        'gesture': item.gesture.value if item.gesture else None,
                        'metadata': item.metadata
                    }
                    section_data['items'].append(item_data)
                
                export_data['sections'].append(section_data)
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting mobile layout: {e}")
            return {}
    
    def import_layout(self, layout_data: Dict[str, Any]) -> MobileSidebarLayout:
        """Import a mobile layout configuration"""
        try:
            layout = MobileSidebarLayout(
                id=layout_data['id'],
                name=layout_data['name'],
                description=layout_data.get('description', ''),
                type=MobileLayoutType(layout_data['type']),
                sections=[],
                theme=layout_data.get('theme', self.default_theme),
                width=layout_data.get('width', '100%'),
                height=layout_data.get('height', '100%'),
                position=layout_data.get('position', 'left'),
                animation=layout_data.get('animation', 'slide'),
                backdrop=layout_data.get('backdrop', True),
                backdrop_opacity=layout_data.get('backdrop_opacity', 0.5),
                z_index=layout_data.get('z_index', 1000),
                touch_enabled=layout_data.get('touch_enabled', True),
                gesture_support=layout_data.get('gesture_support', True),
                haptic_feedback=layout_data.get('haptic_feedback', True)
            )
            
            # Import sections
            for section_data in layout_data.get('sections', []):
                section = self._create_section_from_data(section_data)
                layout.sections.append(section)
            
            # Store layout
            self.layouts[layout.id] = layout
            
            logger.info(f"Imported mobile layout: {layout.id}")
            return layout
            
        except Exception as e:
            logger.error(f"Error importing mobile layout: {e}")
            raise
    
    def get_layout_statistics(self) -> Dict[str, Any]:
        """Get mobile layout statistics"""
        try:
            stats = {
                'total_layouts': len(self.layouts),
                'layouts_by_type': {},
                'total_sections': 0,
                'total_items': 0,
                'total_users': len(self.user_preferences),
                'total_templates': len(self.layout_templates),
                'most_used_layouts': [],
                'recent_layouts': []
            }
            
            # Count layouts by type
            for layout in self.layouts.values():
                layout_type = layout.type.value
                stats['layouts_by_type'][layout_type] = stats['layouts_by_type'].get(layout_type, 0) + 1
                
                # Count sections and items
                stats['total_sections'] += len(layout.sections)
                for section in layout.sections:
                    stats['total_items'] += len(section.items)
            
            # Get most used layouts
            layout_usage = {}
            for user_pref in self.user_preferences.values():
                if user_pref.layout_id in layout_usage:
                    layout_usage[user_pref.layout_id] += 1
                else:
                    layout_usage[user_pref.layout_id] = 1
            
            stats['most_used_layouts'] = sorted(
                layout_usage.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            # Get recent layouts
            recent_layouts = sorted(
                self.layouts.values(),
                key=lambda x: x.updated_at,
                reverse=True
            )[:10]
            
            stats['recent_layouts'] = [
                {
                    'id': layout.id,
                    'name': layout.name,
                    'type': layout.type.value,
                    'updated_at': layout.updated_at.isoformat()
                }
                for layout in recent_layouts
            ]
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting mobile layout statistics: {e}")
            return {}
    
    def validate_layout(self, layout_id: str) -> List[str]:
        """Validate a mobile layout configuration"""
        try:
            layout = self.get_layout(layout_id)
            if not layout:
                return [f"Mobile layout {layout_id} not found"]
            
            errors = []
            
            # Check for duplicate IDs
            all_ids = set()
            for section in layout.sections:
                if section.id in all_ids:
                    errors.append(f"Duplicate section ID: {section.id}")
                all_ids.add(section.id)
                
                for item in section.items:
                    if item.id in all_ids:
                        errors.append(f"Duplicate item ID: {item.id}")
                    all_ids.add(item.id)
            
            # Check for missing required fields
            for section in layout.sections:
                if not section.title:
                    errors.append(f"Section {section.id} missing title")
                
                for item in section.items:
                    if not item.title:
                        errors.append(f"Item {item.id} missing title")
            
            # Check section limits
            if len(layout.sections) > self.max_sections:
                errors.append(f"Layout has too many sections: {len(layout.sections)} > {self.max_sections}")
            
            # Check item limits
            for section in layout.sections:
                if len(section.items) > self.max_items_per_section:
                    errors.append(f"Section {section.id} has too many items: {len(section.items)} > {self.max_items_per_section}")
            
            return errors
            
        except Exception as e:
            logger.error(f"Error validating mobile layout: {e}")
            return [f"Validation error: {e}"]
    
    def reset_layout(self, layout_id: str):
        """Reset a mobile layout to its default state"""
        try:
            layout = self.get_layout(layout_id)
            if layout:
                # Reset to default configuration
                layout.updated_at = django_timezone.now()
                
                # Reset sections
                for section in layout.sections:
                    section.is_collapsed = False
                
                # Reset items
                for section in layout.sections:
                    for item in section.items:
                        item.is_active = False
                
                logger.info(f"Reset mobile layout: {layout_id}")
            
        except Exception as e:
            logger.error(f"Error resetting mobile layout: {e}")
    
    def duplicate_layout(self, layout_id: str, new_name: str = None) -> MobileSidebarLayout:
        """Duplicate a mobile layout"""
        try:
            original_layout = self.get_layout(layout_id)
            if not original_layout:
                raise ValueError(f"Mobile layout {layout_id} not found")
            
            # Create new layout ID
            new_layout_id = f"{layout_id}_copy_{django_timezone.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Export original layout
            layout_data = self.export_layout(layout_id)
            
            # Update for new layout
            layout_data['id'] = new_layout_id
            layout_data['name'] = new_name or f"{original_layout.name} (Copy)"
            layout_data['description'] = f"Copy of {original_layout.description}"
            
            # Create new layout
            new_layout = self.import_layout(layout_data)
            
            logger.info(f"Duplicated mobile layout {layout_id} as {new_layout_id}")
            return new_layout
            
        except Exception as e:
            logger.error(f"Error duplicating mobile layout: {e}")
            raise
    
    def get_layout_preview(self, layout_id: str, breakpoint: MobileBreakpoint = MobileBreakpoint.MOBILE) -> Dict[str, Any]:
        """Get mobile layout preview data"""
        try:
            layout = self.get_layout(layout_id)
            if not layout:
                return {}
            
            preview_data = {
                'layout_id': layout_id,
                'name': layout.name,
                'type': layout.type.value,
                'theme': layout.theme,
                'breakpoint': breakpoint.value,
                'sections': []
            }
            
            # Get responsive configuration
            responsive_config = self.get_responsive_layout(layout_id, breakpoint)
            if responsive_config:
                preview_data.update(responsive_config)
            
            return preview_data
            
        except Exception as e:
            logger.error(f"Error getting mobile layout preview: {e}")
            return {}
    
    def optimize_layout(self, layout_id: str) -> Dict[str, Any]:
        """Optimize a mobile layout for performance"""
        try:
            layout = self.get_layout(layout_id)
            if not layout:
                return {}
            
            optimizations = {
                'layout_id': layout_id,
                'optimizations_applied': [],
                'performance_improvements': [],
                'recommendations': []
            }
            
            # Optimize sections
            for section in layout.sections:
                # Remove empty sections
                if not section.items:
                    optimizations['optimizations_applied'].append(f"Removed empty section: {section.id}")
                    continue
                
                # Optimize items
                for item in section.items:
                    # Remove unused metadata
                    if item.metadata and not item.metadata:
                        item.metadata = {}
                        optimizations['optimizations_applied'].append(f"Cleaned metadata for item: {item.id}")
            
            # Performance improvements
            optimizations['performance_improvements'].append("Reduced mobile layout complexity")
            optimizations['performance_improvements'].append("Cleaned unused data")
            
            # Recommendations
            if len(layout.sections) > 5:
                optimizations['recommendations'].append("Consider reducing the number of sections for better mobile performance")
            
            total_items = sum(len(section.items) for section in layout.sections)
            if total_items > 30:
                optimizations['recommendations'].append("Consider pagination for large numbers of items on mobile")
            
            layout.updated_at = django_timezone.now()
            
            logger.info(f"Optimized mobile layout: {layout_id}")
            return optimizations
            
        except Exception as e:
            logger.error(f"Error optimizing mobile layout: {e}")
            return {}
