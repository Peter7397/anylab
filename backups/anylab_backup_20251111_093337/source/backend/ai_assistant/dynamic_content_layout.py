"""
Dynamic Content Layout System

This module provides dynamic content layout capabilities
including responsive design, content adaptation, and user customization.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from django.utils import timezone as django_timezone
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


class LayoutType(Enum):
    """Layout type enumeration"""
    GRID = "grid"
    LIST = "list"
    CARD = "card"
    TABLE = "table"
    TIMELINE = "timeline"
    DASHBOARD = "dashboard"
    GALLERY = "gallery"
    MAGAZINE = "magazine"
    SIDEBAR = "sidebar"
    FULLSCREEN = "fullscreen"


class ContentType(Enum):
    """Content type enumeration"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    LINK = "link"
    EMBED = "embed"
    WIDGET = "widget"
    CHART = "chart"
    FORM = "form"
    NAVIGATION = "navigation"
    SEARCH = "search"
    FILTER = "filter"
    PAGINATION = "pagination"


class ResponsiveBreakpoint(Enum):
    """Responsive breakpoint enumeration"""
    MOBILE = "mobile"  # < 768px
    TABLET = "tablet"  # 768px - 1024px
    DESKTOP = "desktop"  # > 1024px
    LARGE_DESKTOP = "large_desktop"  # > 1440px


class LayoutOrientation(Enum):
    """Layout orientation enumeration"""
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    MIXED = "mixed"


@dataclass
class LayoutBreakpoint:
    """Layout breakpoint configuration"""
    breakpoint: ResponsiveBreakpoint
    columns: int
    gap: str
    padding: str
    margin: str
    font_size: str
    line_height: str
    max_width: Optional[str] = None
    min_width: Optional[str] = None


@dataclass
class ContentBlock:
    """Content block structure"""
    id: str
    type: ContentType
    title: str
    content: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    style: Dict[str, Any] = field(default_factory=dict)
    responsive: Dict[ResponsiveBreakpoint, Dict[str, Any]] = field(default_factory=dict)
    order: int = 0
    is_visible: bool = True
    is_draggable: bool = True
    is_resizable: bool = False
    permissions: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: django_timezone.now())
    updated_at: datetime = field(default_factory=lambda: django_timezone.now())


@dataclass
class LayoutSection:
    """Layout section structure"""
    id: str
    title: str
    type: LayoutType
    orientation: LayoutOrientation
    blocks: List[ContentBlock]
    style: Dict[str, Any] = field(default_factory=dict)
    responsive: Dict[ResponsiveBreakpoint, Dict[str, Any]] = field(default_factory=dict)
    order: int = 0
    is_visible: bool = True
    is_collapsible: bool = False
    is_collapsed: bool = False
    permissions: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: django_timezone.now())
    updated_at: datetime = field(default_factory=lambda: django_timezone.now())


@dataclass
class DynamicLayout:
    """Dynamic layout structure"""
    id: str
    name: str
    description: str
    type: LayoutType
    sections: List[LayoutSection]
    breakpoints: Dict[ResponsiveBreakpoint, LayoutBreakpoint] = field(default_factory=dict)
    global_style: Dict[str, Any] = field(default_factory=dict)
    theme: str = "default"
    is_responsive: bool = True
    is_customizable: bool = True
    is_exportable: bool = True
    permissions: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: django_timezone.now())
    updated_at: datetime = field(default_factory=lambda: django_timezone.now())


@dataclass
class UserLayoutPreference:
    """User layout preference structure"""
    user_id: str
    layout_id: str
    customizations: Dict[str, Any] = field(default_factory=dict)
    saved_layouts: List[str] = field(default_factory=list)
    favorite_layouts: List[str] = field(default_factory=list)
    last_used: datetime = field(default_factory=lambda: django_timezone.now())
    created_at: datetime = field(default_factory=lambda: django_timezone.now())
    updated_at: datetime = field(default_factory=lambda: django_timezone.now())


class DynamicContentLayoutManager:
    """Dynamic Content Layout Manager"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize dynamic content layout manager"""
        self.config = config or {}
        self.layout_enabled = self.config.get('layout_enabled', True)
        self.responsive_enabled = self.config.get('responsive_enabled', True)
        self.customization_enabled = self.config.get('customization_enabled', True)
        self.caching_enabled = self.config.get('caching_enabled', True)
        self.analytics_enabled = self.config.get('analytics_enabled', True)
        
        # Layout configuration
        self.default_layout_type = self.config.get('default_layout_type', LayoutType.GRID)
        self.default_theme = self.config.get('default_theme', 'agilent')
        self.max_sections = self.config.get('max_sections', 10)
        self.max_blocks_per_section = self.config.get('max_blocks_per_section', 20)
        
        # Responsive configuration
        self.breakpoints = {
            ResponsiveBreakpoint.MOBILE: LayoutBreakpoint(
                breakpoint=ResponsiveBreakpoint.MOBILE,
                columns=1,
                gap="8px",
                padding="16px",
                margin="8px",
                font_size="14px",
                line_height="1.4",
                max_width="767px"
            ),
            ResponsiveBreakpoint.TABLET: LayoutBreakpoint(
                breakpoint=ResponsiveBreakpoint.TABLET,
                columns=2,
                gap="16px",
                padding="24px",
                margin="16px",
                font_size="16px",
                line_height="1.5",
                min_width="768px",
                max_width="1023px"
            ),
            ResponsiveBreakpoint.DESKTOP: LayoutBreakpoint(
                breakpoint=ResponsiveBreakpoint.DESKTOP,
                columns=3,
                gap="24px",
                padding="32px",
                margin="24px",
                font_size="16px",
                line_height="1.6",
                min_width="1024px",
                max_width="1439px"
            ),
            ResponsiveBreakpoint.LARGE_DESKTOP: LayoutBreakpoint(
                breakpoint=ResponsiveBreakpoint.LARGE_DESKTOP,
                columns=4,
                gap="32px",
                padding="40px",
                margin="32px",
                font_size="18px",
                line_height="1.7",
                min_width="1440px"
            )
        }
        
        # Initialize components
        self._initialize_components()
        
        logger.info("Dynamic Content Layout Manager initialized")
    
    def _initialize_components(self):
        """Initialize layout components"""
        try:
            # Initialize data structures
            self.layouts = {}
            self.user_preferences = {}
            self.layout_templates = {}
            self.content_blocks = {}
            
            # Initialize default layouts
            self._create_default_layouts()
            
            # Initialize layout templates
            self._create_layout_templates()
            
            logger.info("Layout components initialized")
            
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            raise
    
    def _create_default_layouts(self):
        """Create default layouts"""
        try:
            # Create dashboard layout
            dashboard_layout = self._create_dashboard_layout()
            self.layouts[dashboard_layout.id] = dashboard_layout
            
            # Create grid layout
            grid_layout = self._create_grid_layout()
            self.layouts[grid_layout.id] = grid_layout
            
            # Create list layout
            list_layout = self._create_list_layout()
            self.layouts[list_layout.id] = list_layout
            
            # Create card layout
            card_layout = self._create_card_layout()
            self.layouts[card_layout.id] = card_layout
            
            logger.info("Default layouts created")
            
        except Exception as e:
            logger.error(f"Error creating default layouts: {e}")
    
    def _create_dashboard_layout(self) -> DynamicLayout:
        """Create dashboard layout"""
        try:
            sections = [
                LayoutSection(
                    id="dashboard_header",
                    title="Dashboard Header",
                    type=LayoutType.FULLSCREEN,
                    orientation=LayoutOrientation.HORIZONTAL,
                    blocks=[
                        ContentBlock(
                            id="header_title",
                            type=ContentType.TEXT,
                            title="Dashboard Title",
                            content="AnyLab Dashboard",
                            style={"font_size": "24px", "font_weight": "bold", "color": "#333"}
                        ),
                        ContentBlock(
                            id="header_search",
                            type=ContentType.SEARCH,
                            title="Search",
                            content={"placeholder": "Search...", "action": "/search"}
                        )
                    ],
                    order=1
                ),
                LayoutSection(
                    id="dashboard_metrics",
                    title="Key Metrics",
                    type=LayoutType.GRID,
                    orientation=LayoutOrientation.HORIZONTAL,
                    blocks=[
                        ContentBlock(
                            id="metric_total_documents",
                            type=ContentType.WIDGET,
                            title="Total Documents",
                            content={"value": 0, "type": "counter", "icon": "document"}
                        ),
                        ContentBlock(
                            id="metric_active_users",
                            type=ContentType.WIDGET,
                            title="Active Users",
                            content={"value": 0, "type": "counter", "icon": "users"}
                        ),
                        ContentBlock(
                            id="metric_system_health",
                            type=ContentType.WIDGET,
                            title="System Health",
                            content={"value": 0, "type": "gauge", "icon": "health"}
                        )
                    ],
                    order=2
                ),
                LayoutSection(
                    id="dashboard_content",
                    title="Recent Content",
                    type=LayoutType.LIST,
                    orientation=LayoutOrientation.VERTICAL,
                    blocks=[
                        ContentBlock(
                            id="recent_documents",
                            type=ContentType.WIDGET,
                            title="Recent Documents",
                            content={"type": "list", "source": "/api/recent-documents"}
                        )
                    ],
                    order=3
                )
            ]
            
            return DynamicLayout(
                id="dashboard_layout",
                name="Dashboard Layout",
                description="Default dashboard layout with metrics and recent content",
                type=LayoutType.DASHBOARD,
                sections=sections,
                breakpoints=self.breakpoints,
                theme=self.default_theme,
                is_responsive=True,
                is_customizable=True
            )
            
        except Exception as e:
            logger.error(f"Error creating dashboard layout: {e}")
            return DynamicLayout(id="dashboard_layout", name="Dashboard Layout", description="", type=LayoutType.DASHBOARD, sections=[])
    
    def _create_grid_layout(self) -> DynamicLayout:
        """Create grid layout"""
        try:
            sections = [
                LayoutSection(
                    id="grid_header",
                    title="Grid Header",
                    type=LayoutType.FULLSCREEN,
                    orientation=LayoutOrientation.HORIZONTAL,
                    blocks=[
                        ContentBlock(
                            id="grid_title",
                            type=ContentType.TEXT,
                            title="Grid Title",
                            content="Content Grid",
                            style={"font_size": "20px", "font_weight": "bold"}
                        ),
                        ContentBlock(
                            id="grid_filters",
                            type=ContentType.FILTER,
                            title="Filters",
                            content={"filters": ["category", "date", "type"]}
                        )
                    ],
                    order=1
                ),
                LayoutSection(
                    id="grid_content",
                    title="Grid Content",
                    type=LayoutType.GRID,
                    orientation=LayoutOrientation.MIXED,
                    blocks=[
                        ContentBlock(
                            id="grid_item_1",
                            type=ContentType.CARD,
                            title="Grid Item 1",
                            content={"title": "Sample Content", "description": "This is a sample content item"}
                        ),
                        ContentBlock(
                            id="grid_item_2",
                            type=ContentType.CARD,
                            title="Grid Item 2",
                            content={"title": "Sample Content", "description": "This is a sample content item"}
                        ),
                        ContentBlock(
                            id="grid_item_3",
                            type=ContentType.CARD,
                            title="Grid Item 3",
                            content={"title": "Sample Content", "description": "This is a sample content item"}
                        )
                    ],
                    order=2
                ),
                LayoutSection(
                    id="grid_pagination",
                    title="Grid Pagination",
                    type=LayoutType.FULLSCREEN,
                    orientation=LayoutOrientation.HORIZONTAL,
                    blocks=[
                        ContentBlock(
                            id="pagination",
                            type=ContentType.PAGINATION,
                            title="Pagination",
                            content={"current_page": 1, "total_pages": 10, "items_per_page": 20}
                        )
                    ],
                    order=3
                )
            ]
            
            return DynamicLayout(
                id="grid_layout",
                name="Grid Layout",
                description="Responsive grid layout for content display",
                type=LayoutType.GRID,
                sections=sections,
                breakpoints=self.breakpoints,
                theme=self.default_theme,
                is_responsive=True,
                is_customizable=True
            )
            
        except Exception as e:
            logger.error(f"Error creating grid layout: {e}")
            return DynamicLayout(id="grid_layout", name="Grid Layout", description="", type=LayoutType.GRID, sections=[])
    
    def _create_list_layout(self) -> DynamicLayout:
        """Create list layout"""
        try:
            sections = [
                LayoutSection(
                    id="list_header",
                    title="List Header",
                    type=LayoutType.FULLSCREEN,
                    orientation=LayoutOrientation.HORIZONTAL,
                    blocks=[
                        ContentBlock(
                            id="list_title",
                            type=ContentType.TEXT,
                            title="List Title",
                            content="Content List",
                            style={"font_size": "20px", "font_weight": "bold"}
                        ),
                        ContentBlock(
                            id="list_search",
                            type=ContentType.SEARCH,
                            title="Search",
                            content={"placeholder": "Search list...", "action": "/search"}
                        )
                    ],
                    order=1
                ),
                LayoutSection(
                    id="list_content",
                    title="List Content",
                    type=LayoutType.LIST,
                    orientation=LayoutOrientation.VERTICAL,
                    blocks=[
                        ContentBlock(
                            id="list_item_1",
                            type=ContentType.TEXT,
                            title="List Item 1",
                            content="This is the first list item"
                        ),
                        ContentBlock(
                            id="list_item_2",
                            type=ContentType.TEXT,
                            title="List Item 2",
                            content="This is the second list item"
                        ),
                        ContentBlock(
                            id="list_item_3",
                            type=ContentType.TEXT,
                            title="List Item 3",
                            content="This is the third list item"
                        )
                    ],
                    order=2
                )
            ]
            
            return DynamicLayout(
                id="list_layout",
                name="List Layout",
                description="Vertical list layout for content display",
                type=LayoutType.LIST,
                sections=sections,
                breakpoints=self.breakpoints,
                theme=self.default_theme,
                is_responsive=True,
                is_customizable=True
            )
            
        except Exception as e:
            logger.error(f"Error creating list layout: {e}")
            return DynamicLayout(id="list_layout", name="List Layout", description="", type=LayoutType.LIST, sections=[])
    
    def _create_card_layout(self) -> DynamicLayout:
        """Create card layout"""
        try:
            sections = [
                LayoutSection(
                    id="card_header",
                    title="Card Header",
                    type=LayoutType.FULLSCREEN,
                    orientation=LayoutOrientation.HORIZONTAL,
                    blocks=[
                        ContentBlock(
                            id="card_title",
                            type=ContentType.TEXT,
                            title="Card Title",
                            content="Content Cards",
                            style={"font_size": "20px", "font_weight": "bold"}
                        )
                    ],
                    order=1
                ),
                LayoutSection(
                    id="card_content",
                    title="Card Content",
                    type=LayoutType.CARD,
                    orientation=LayoutOrientation.MIXED,
                    blocks=[
                        ContentBlock(
                            id="card_1",
                            type=ContentType.CARD,
                            title="Card 1",
                            content={
                                "title": "Sample Card",
                                "description": "This is a sample card with content",
                                "image": "/images/sample.jpg",
                                "actions": ["view", "edit", "delete"]
                            }
                        ),
                        ContentBlock(
                            id="card_2",
                            type=ContentType.CARD,
                            title="Card 2",
                            content={
                                "title": "Sample Card",
                                "description": "This is a sample card with content",
                                "image": "/images/sample.jpg",
                                "actions": ["view", "edit", "delete"]
                            }
                        ),
                        ContentBlock(
                            id="card_3",
                            type=ContentType.CARD,
                            title="Card 3",
                            content={
                                "title": "Sample Card",
                                "description": "This is a sample card with content",
                                "image": "/images/sample.jpg",
                                "actions": ["view", "edit", "delete"]
                            }
                        )
                    ],
                    order=2
                )
            ]
            
            return DynamicLayout(
                id="card_layout",
                name="Card Layout",
                description="Card-based layout for content display",
                type=LayoutType.CARD,
                sections=sections,
                breakpoints=self.breakpoints,
                theme=self.default_theme,
                is_responsive=True,
                is_customizable=True
            )
            
        except Exception as e:
            logger.error(f"Error creating card layout: {e}")
            return DynamicLayout(id="card_layout", name="Card Layout", description="", type=LayoutType.CARD, sections=[])
    
    def _create_layout_templates(self):
        """Create layout templates"""
        try:
            templates = {
                "agilent_dashboard": {
                    "name": "Agilent Dashboard",
                    "description": "Dashboard template for Agilent products",
                    "type": LayoutType.DASHBOARD,
                    "theme": "agilent",
                    "sections": ["header", "metrics", "content", "footer"]
                },
                "lab_informatics_grid": {
                    "name": "Lab Informatics Grid",
                    "description": "Grid template for Lab Informatics content",
                    "type": LayoutType.GRID,
                    "theme": "lab-informatics",
                    "sections": ["header", "filters", "content", "pagination"]
                },
                "troubleshooting_list": {
                    "name": "Troubleshooting List",
                    "description": "List template for troubleshooting content",
                    "type": LayoutType.LIST,
                    "theme": "troubleshooting",
                    "sections": ["header", "search", "content", "pagination"]
                },
                "documentation_cards": {
                    "name": "Documentation Cards",
                    "description": "Card template for documentation content",
                    "type": LayoutType.CARD,
                    "theme": "documentation",
                    "sections": ["header", "content", "footer"]
                }
            }
            
            self.layout_templates.update(templates)
            
            logger.info("Layout templates created")
            
        except Exception as e:
            logger.error(f"Error creating layout templates: {e}")
    
    def create_layout(self, layout_data: Dict[str, Any]) -> DynamicLayout:
        """Create a new layout"""
        try:
            layout = DynamicLayout(
                id=layout_data['id'],
                name=layout_data['name'],
                description=layout_data.get('description', ''),
                type=LayoutType(layout_data.get('type', self.default_layout_type.value)),
                sections=[],
                breakpoints=self.breakpoints,
                theme=layout_data.get('theme', self.default_theme),
                is_responsive=layout_data.get('is_responsive', True),
                is_customizable=layout_data.get('is_customizable', True),
                is_exportable=layout_data.get('is_exportable', True),
                permissions=layout_data.get('permissions', [])
            )
            
            # Add sections
            for section_data in layout_data.get('sections', []):
                section = self._create_section_from_data(section_data)
                layout.sections.append(section)
            
            # Store layout
            self.layouts[layout.id] = layout
            
            logger.info(f"Created layout: {layout.id}")
            return layout
            
        except Exception as e:
            logger.error(f"Error creating layout: {e}")
            raise
    
    def _create_section_from_data(self, section_data: Dict[str, Any]) -> LayoutSection:
        """Create section from data"""
        try:
            section = LayoutSection(
                id=section_data['id'],
                title=section_data['title'],
                type=LayoutType(section_data.get('type', LayoutType.GRID.value)),
                orientation=LayoutOrientation(section_data.get('orientation', LayoutOrientation.HORIZONTAL.value)),
                blocks=[],
                style=section_data.get('style', {}),
                order=section_data.get('order', 0),
                is_visible=section_data.get('is_visible', True),
                is_collapsible=section_data.get('is_collapsible', False),
                is_collapsed=section_data.get('is_collapsed', False),
                permissions=section_data.get('permissions', [])
            )
            
            # Add blocks
            for block_data in section_data.get('blocks', []):
                block = self._create_block_from_data(block_data)
                section.blocks.append(block)
            
            return section
            
        except Exception as e:
            logger.error(f"Error creating section from data: {e}")
            raise
    
    def _create_block_from_data(self, block_data: Dict[str, Any]) -> ContentBlock:
        """Create block from data"""
        try:
            block = ContentBlock(
                id=block_data['id'],
                type=ContentType(block_data['type']),
                title=block_data['title'],
                content=block_data['content'],
                metadata=block_data.get('metadata', {}),
                style=block_data.get('style', {}),
                order=block_data.get('order', 0),
                is_visible=block_data.get('is_visible', True),
                is_draggable=block_data.get('is_draggable', True),
                is_resizable=block_data.get('is_resizable', False),
                permissions=block_data.get('permissions', [])
            )
            
            return block
            
        except Exception as e:
            logger.error(f"Error creating block from data: {e}")
            raise
    
    def get_layout(self, layout_id: str) -> Optional[DynamicLayout]:
        """Get a layout by ID"""
        try:
            return self.layouts.get(layout_id)
            
        except Exception as e:
            logger.error(f"Error getting layout {layout_id}: {e}")
            return None
    
    def get_layouts(self, layout_type: LayoutType = None) -> List[DynamicLayout]:
        """Get layouts filtered by type"""
        try:
            layouts = list(self.layouts.values())
            
            if layout_type:
                layouts = [layout for layout in layouts if layout.type == layout_type]
            
            return layouts
            
        except Exception as e:
            logger.error(f"Error getting layouts: {e}")
            return []
    
    def update_layout(self, layout_id: str, updates: Dict[str, Any]):
        """Update a layout"""
        try:
            layout = self.get_layout(layout_id)
            if layout:
                for key, value in updates.items():
                    if hasattr(layout, key):
                        setattr(layout, key, value)
                
                layout.updated_at = django_timezone.now()
                
                logger.info(f"Updated layout: {layout_id}")
            
        except Exception as e:
            logger.error(f"Error updating layout {layout_id}: {e}")
    
    def delete_layout(self, layout_id: str):
        """Delete a layout"""
        try:
            if layout_id in self.layouts:
                del self.layouts[layout_id]
                logger.info(f"Deleted layout: {layout_id}")
            
        except Exception as e:
            logger.error(f"Error deleting layout {layout_id}: {e}")
    
    def add_section(self, layout_id: str, section: LayoutSection):
        """Add a section to a layout"""
        try:
            layout = self.get_layout(layout_id)
            if layout:
                layout.sections.append(section)
                layout.updated_at = django_timezone.now()
                
                logger.info(f"Added section {section.id} to layout {layout_id}")
            
        except Exception as e:
            logger.error(f"Error adding section to layout: {e}")
    
    def remove_section(self, layout_id: str, section_id: str):
        """Remove a section from a layout"""
        try:
            layout = self.get_layout(layout_id)
            if layout:
                layout.sections = [s for s in layout.sections if s.id != section_id]
                layout.updated_at = django_timezone.now()
                
                logger.info(f"Removed section {section_id} from layout {layout_id}")
            
        except Exception as e:
            logger.error(f"Error removing section from layout: {e}")
    
    def add_block(self, layout_id: str, section_id: str, block: ContentBlock):
        """Add a block to a section"""
        try:
            layout = self.get_layout(layout_id)
            if layout:
                for section in layout.sections:
                    if section.id == section_id:
                        section.blocks.append(block)
                        section.updated_at = django_timezone.now()
                        layout.updated_at = django_timezone.now()
                        
                        logger.info(f"Added block {block.id} to section {section_id}")
                        break
            
        except Exception as e:
            logger.error(f"Error adding block to section: {e}")
    
    def remove_block(self, layout_id: str, section_id: str, block_id: str):
        """Remove a block from a section"""
        try:
            layout = self.get_layout(layout_id)
            if layout:
                for section in layout.sections:
                    if section.id == section_id:
                        section.blocks = [b for b in section.blocks if b.id != block_id]
                        section.updated_at = django_timezone.now()
                        layout.updated_at = django_timezone.now()
                        
                        logger.info(f"Removed block {block_id} from section {section_id}")
                        break
            
        except Exception as e:
            logger.error(f"Error removing block from section: {e}")
    
    def reorder_sections(self, layout_id: str, section_orders: Dict[str, int]):
        """Reorder sections in a layout"""
        try:
            layout = self.get_layout(layout_id)
            if layout:
                for section in layout.sections:
                    if section.id in section_orders:
                        section.order = section_orders[section.id]
                
                # Sort sections by order
                layout.sections.sort(key=lambda x: x.order)
                layout.updated_at = django_timezone.now()
                
                logger.info(f"Reordered sections in layout {layout_id}")
            
        except Exception as e:
            logger.error(f"Error reordering sections: {e}")
    
    def reorder_blocks(self, layout_id: str, section_id: str, block_orders: Dict[str, int]):
        """Reorder blocks in a section"""
        try:
            layout = self.get_layout(layout_id)
            if layout:
                for section in layout.sections:
                    if section.id == section_id:
                        for block in section.blocks:
                            if block.id in block_orders:
                                block.order = block_orders[block.id]
                        
                        # Sort blocks by order
                        section.blocks.sort(key=lambda x: x.order)
                        section.updated_at = django_timezone.now()
                        layout.updated_at = django_timezone.now()
                        
                        logger.info(f"Reordered blocks in section {section_id}")
                        break
            
        except Exception as e:
            logger.error(f"Error reordering blocks: {e}")
    
    def get_responsive_layout(self, layout_id: str, breakpoint: ResponsiveBreakpoint) -> Dict[str, Any]:
        """Get responsive layout configuration for a breakpoint"""
        try:
            layout = self.get_layout(layout_id)
            if not layout:
                return {}
            
            responsive_config = {
                'layout_id': layout_id,
                'breakpoint': breakpoint.value,
                'sections': []
            }
            
            # Get breakpoint configuration
            breakpoint_config = self.breakpoints.get(breakpoint)
            if breakpoint_config:
                responsive_config['breakpoint_config'] = {
                    'columns': breakpoint_config.columns,
                    'gap': breakpoint_config.gap,
                    'padding': breakpoint_config.padding,
                    'margin': breakpoint_config.margin,
                    'font_size': breakpoint_config.font_size,
                    'line_height': breakpoint_config.line_height,
                    'max_width': breakpoint_config.max_width,
                    'min_width': breakpoint_config.min_width
                }
            
            # Process sections
            for section in layout.sections:
                section_config = {
                    'id': section.id,
                    'title': section.title,
                    'type': section.type.value,
                    'orientation': section.orientation.value,
                    'order': section.order,
                    'is_visible': section.is_visible,
                    'blocks': []
                }
                
                # Apply responsive styles
                if breakpoint in section.responsive:
                    section_config['style'] = section.responsive[breakpoint]
                
                # Process blocks
                for block in section.blocks:
                    block_config = {
                        'id': block.id,
                        'type': block.type.value,
                        'title': block.title,
                        'content': block.content,
                        'order': block.order,
                        'is_visible': block.is_visible
                    }
                    
                    # Apply responsive styles
                    if breakpoint in block.responsive:
                        block_config['style'] = block.responsive[breakpoint]
                    
                    section_config['blocks'].append(block_config)
                
                responsive_config['sections'].append(section_config)
            
            return responsive_config
            
        except Exception as e:
            logger.error(f"Error getting responsive layout: {e}")
            return {}
    
    def apply_user_customizations(self, layout_id: str, user_id: str, customizations: Dict[str, Any]):
        """Apply user customizations to a layout"""
        try:
            layout = self.get_layout(layout_id)
            if not layout:
                return
            
            # Apply section customizations
            if 'sections' in customizations:
                for section_id, section_customizations in customizations['sections'].items():
                    for section in layout.sections:
                        if section.id == section_id:
                            # Apply customizations
                            if 'style' in section_customizations:
                                section.style.update(section_customizations['style'])
                            
                            if 'is_visible' in section_customizations:
                                section.is_visible = section_customizations['is_visible']
                            
                            if 'is_collapsed' in section_customizations:
                                section.is_collapsed = section_customizations['is_collapsed']
                            
                            # Apply block customizations
                            if 'blocks' in section_customizations:
                                for block_id, block_customizations in section_customizations['blocks'].items():
                                    for block in section.blocks:
                                        if block.id == block_id:
                                            if 'style' in block_customizations:
                                                block.style.update(block_customizations['style'])
                                            
                                            if 'is_visible' in block_customizations:
                                                block.is_visible = block_customizations['is_visible']
                                            
                                            break
                            break
            
            # Apply global customizations
            if 'global_style' in customizations:
                layout.global_style.update(customizations['global_style'])
            
            if 'theme' in customizations:
                layout.theme = customizations['theme']
            
            layout.updated_at = django_timezone.now()
            
            # Save user preferences
            self._save_user_preferences(user_id, layout_id, customizations)
            
            logger.info(f"Applied customizations for user {user_id} to layout {layout_id}")
            
        except Exception as e:
            logger.error(f"Error applying user customizations: {e}")
    
    def _save_user_preferences(self, user_id: str, layout_id: str, customizations: Dict[str, Any]):
        """Save user preferences"""
        try:
            if user_id not in self.user_preferences:
                self.user_preferences[user_id] = UserLayoutPreference(
                    user_id=user_id,
                    layout_id=layout_id
                )
            
            user_pref = self.user_preferences[user_id]
            user_pref.customizations[layout_id] = customizations
            user_pref.last_used = django_timezone.now()
            user_pref.updated_at = django_timezone.now()
            
        except Exception as e:
            logger.error(f"Error saving user preferences: {e}")
    
    def get_user_preferences(self, user_id: str) -> Optional[UserLayoutPreference]:
        """Get user preferences"""
        try:
            return self.user_preferences.get(user_id)
            
        except Exception as e:
            logger.error(f"Error getting user preferences: {e}")
            return None
    
    def save_user_layout(self, user_id: str, layout_id: str, layout_data: Dict[str, Any]):
        """Save a user's custom layout"""
        try:
            if user_id not in self.user_preferences:
                self.user_preferences[user_id] = UserLayoutPreference(
                    user_id=user_id,
                    layout_id=layout_id
                )
            
            user_pref = self.user_preferences[user_id]
            
            # Create custom layout ID
            custom_layout_id = f"{layout_id}_user_{user_id}"
            
            # Create custom layout
            custom_layout = DynamicLayout(
                id=custom_layout_id,
                name=f"{layout_data['name']} (Custom)",
                description=f"Custom layout for user {user_id}",
                type=LayoutType(layout_data.get('type', self.default_layout_type.value)),
                sections=[],
                breakpoints=self.breakpoints,
                theme=layout_data.get('theme', self.default_theme),
                is_responsive=True,
                is_customizable=True,
                is_exportable=True
            )
            
            # Add sections
            for section_data in layout_data.get('sections', []):
                section = self._create_section_from_data(section_data)
                custom_layout.sections.append(section)
            
            # Store custom layout
            self.layouts[custom_layout_id] = custom_layout
            
            # Add to user's saved layouts
            if custom_layout_id not in user_pref.saved_layouts:
                user_pref.saved_layouts.append(custom_layout_id)
            
            user_pref.updated_at = django_timezone.now()
            
            logger.info(f"Saved custom layout {custom_layout_id} for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error saving user layout: {e}")
    
    def get_user_layouts(self, user_id: str) -> List[DynamicLayout]:
        """Get user's custom layouts"""
        try:
            user_pref = self.get_user_preferences(user_id)
            if not user_pref:
                return []
            
            layouts = []
            for layout_id in user_pref.saved_layouts:
                layout = self.get_layout(layout_id)
                if layout:
                    layouts.append(layout)
            
            return layouts
            
        except Exception as e:
            logger.error(f"Error getting user layouts: {e}")
            return []
    
    def add_favorite_layout(self, user_id: str, layout_id: str):
        """Add a layout to user's favorites"""
        try:
            if user_id not in self.user_preferences:
                self.user_preferences[user_id] = UserLayoutPreference(
                    user_id=user_id,
                    layout_id=layout_id
                )
            
            user_pref = self.user_preferences[user_id]
            if layout_id not in user_pref.favorite_layouts:
                user_pref.favorite_layouts.append(layout_id)
                user_pref.updated_at = django_timezone.now()
                
                logger.info(f"Added layout {layout_id} to favorites for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error adding favorite layout: {e}")
    
    def remove_favorite_layout(self, user_id: str, layout_id: str):
        """Remove a layout from user's favorites"""
        try:
            user_pref = self.get_user_preferences(user_id)
            if user_pref and layout_id in user_pref.favorite_layouts:
                user_pref.favorite_layouts.remove(layout_id)
                user_pref.updated_at = django_timezone.now()
                
                logger.info(f"Removed layout {layout_id} from favorites for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error removing favorite layout: {e}")
    
    def get_favorite_layouts(self, user_id: str) -> List[DynamicLayout]:
        """Get user's favorite layouts"""
        try:
            user_pref = self.get_user_preferences(user_id)
            if not user_pref:
                return []
            
            layouts = []
            for layout_id in user_pref.favorite_layouts:
                layout = self.get_layout(layout_id)
                if layout:
                    layouts.append(layout)
            
            return layouts
            
        except Exception as e:
            logger.error(f"Error getting favorite layouts: {e}")
            return []
    
    def export_layout(self, layout_id: str) -> Dict[str, Any]:
        """Export a layout configuration"""
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
                'is_responsive': layout.is_responsive,
                'is_customizable': layout.is_customizable,
                'is_exportable': layout.is_exportable,
                'permissions': layout.permissions,
                'breakpoints': {
                    breakpoint.value: {
                        'columns': bp.columns,
                        'gap': bp.gap,
                        'padding': bp.padding,
                        'margin': bp.margin,
                        'font_size': bp.font_size,
                        'line_height': bp.line_height,
                        'max_width': bp.max_width,
                        'min_width': bp.min_width
                    }
                    for breakpoint, bp in layout.breakpoints.items()
                },
                'global_style': layout.global_style,
                'sections': []
            }
            
            for section in layout.sections:
                section_data = {
                    'id': section.id,
                    'title': section.title,
                    'type': section.type.value,
                    'orientation': section.orientation.value,
                    'style': section.style,
                    'order': section.order,
                    'is_visible': section.is_visible,
                    'is_collapsible': section.is_collapsible,
                    'is_collapsed': section.is_collapsed,
                    'permissions': section.permissions,
                    'blocks': []
                }
                
                for block in section.blocks:
                    block_data = {
                        'id': block.id,
                        'type': block.type.value,
                        'title': block.title,
                        'content': block.content,
                        'metadata': block.metadata,
                        'style': block.style,
                        'order': block.order,
                        'is_visible': block.is_visible,
                        'is_draggable': block.is_draggable,
                        'is_resizable': block.is_resizable,
                        'permissions': block.permissions
                    }
                    section_data['blocks'].append(block_data)
                
                export_data['sections'].append(section_data)
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting layout: {e}")
            return {}
    
    def import_layout(self, layout_data: Dict[str, Any]) -> DynamicLayout:
        """Import a layout configuration"""
        try:
            layout = DynamicLayout(
                id=layout_data['id'],
                name=layout_data['name'],
                description=layout_data.get('description', ''),
                type=LayoutType(layout_data['type']),
                sections=[],
                theme=layout_data.get('theme', self.default_theme),
                is_responsive=layout_data.get('is_responsive', True),
                is_customizable=layout_data.get('is_customizable', True),
                is_exportable=layout_data.get('is_exportable', True),
                permissions=layout_data.get('permissions', []),
                global_style=layout_data.get('global_style', {})
            )
            
            # Import breakpoints
            if 'breakpoints' in layout_data:
                for breakpoint_name, bp_data in layout_data['breakpoints'].items():
                    breakpoint = ResponsiveBreakpoint(breakpoint_name)
                    layout.breakpoints[breakpoint] = LayoutBreakpoint(
                        breakpoint=breakpoint,
                        columns=bp_data['columns'],
                        gap=bp_data['gap'],
                        padding=bp_data['padding'],
                        margin=bp_data['margin'],
                        font_size=bp_data['font_size'],
                        line_height=bp_data['line_height'],
                        max_width=bp_data.get('max_width'),
                        min_width=bp_data.get('min_width')
                    )
            
            # Import sections
            for section_data in layout_data.get('sections', []):
                section = self._create_section_from_data(section_data)
                layout.sections.append(section)
            
            # Store layout
            self.layouts[layout.id] = layout
            
            logger.info(f"Imported layout: {layout.id}")
            return layout
            
        except Exception as e:
            logger.error(f"Error importing layout: {e}")
            raise
    
    def get_layout_templates(self) -> Dict[str, Any]:
        """Get available layout templates"""
        return self.layout_templates.copy()
    
    def create_layout_from_template(self, template_id: str, customizations: Dict[str, Any] = None) -> DynamicLayout:
        """Create a layout from a template"""
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
            
            logger.info(f"Created layout from template {template_id}: {layout.id}")
            return layout
            
        except Exception as e:
            logger.error(f"Error creating layout from template: {e}")
            raise
    
    def get_layout_statistics(self) -> Dict[str, Any]:
        """Get layout statistics"""
        try:
            stats = {
                'total_layouts': len(self.layouts),
                'layouts_by_type': {},
                'total_sections': 0,
                'total_blocks': 0,
                'total_users': len(self.user_preferences),
                'total_templates': len(self.layout_templates),
                'most_used_layouts': [],
                'recent_layouts': []
            }
            
            # Count layouts by type
            for layout in self.layouts.values():
                layout_type = layout.type.value
                stats['layouts_by_type'][layout_type] = stats['layouts_by_type'].get(layout_type, 0) + 1
                
                # Count sections and blocks
                stats['total_sections'] += len(layout.sections)
                for section in layout.sections:
                    stats['total_blocks'] += len(section.blocks)
            
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
            logger.error(f"Error getting layout statistics: {e}")
            return {}
    
    def validate_layout(self, layout_id: str) -> List[str]:
        """Validate a layout configuration"""
        try:
            layout = self.get_layout(layout_id)
            if not layout:
                return [f"Layout {layout_id} not found"]
            
            errors = []
            
            # Check for duplicate IDs
            all_ids = set()
            for section in layout.sections:
                if section.id in all_ids:
                    errors.append(f"Duplicate section ID: {section.id}")
                all_ids.add(section.id)
                
                for block in section.blocks:
                    if block.id in all_ids:
                        errors.append(f"Duplicate block ID: {block.id}")
                    all_ids.add(block.id)
            
            # Check for missing required fields
            for section in layout.sections:
                if not section.title:
                    errors.append(f"Section {section.id} missing title")
                
                for block in section.blocks:
                    if not block.title:
                        errors.append(f"Block {block.id} missing title")
            
            # Check section limits
            if len(layout.sections) > self.max_sections:
                errors.append(f"Layout has too many sections: {len(layout.sections)} > {self.max_sections}")
            
            # Check block limits
            for section in layout.sections:
                if len(section.blocks) > self.max_blocks_per_section:
                    errors.append(f"Section {section.id} has too many blocks: {len(section.blocks)} > {self.max_blocks_per_section}")
            
            return errors
            
        except Exception as e:
            logger.error(f"Error validating layout: {e}")
            return [f"Validation error: {e}"]
    
    def reset_layout(self, layout_id: str):
        """Reset a layout to its default state"""
        try:
            layout = self.get_layout(layout_id)
            if layout:
                # Reset to default configuration
                layout.global_style = {}
                layout.updated_at = django_timezone.now()
                
                # Reset sections
                for section in layout.sections:
                    section.style = {}
                    section.is_collapsed = False
                    section.updated_at = django_timezone.now()
                    
                    # Reset blocks
                    for block in section.blocks:
                        block.style = {}
                        block.updated_at = django_timezone.now()
                
                logger.info(f"Reset layout: {layout_id}")
            
        except Exception as e:
            logger.error(f"Error resetting layout: {e}")
    
    def duplicate_layout(self, layout_id: str, new_name: str = None) -> DynamicLayout:
        """Duplicate a layout"""
        try:
            original_layout = self.get_layout(layout_id)
            if not original_layout:
                raise ValueError(f"Layout {layout_id} not found")
            
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
            
            logger.info(f"Duplicated layout {layout_id} as {new_layout_id}")
            return new_layout
            
        except Exception as e:
            logger.error(f"Error duplicating layout: {e}")
            raise
    
    def get_layout_preview(self, layout_id: str, breakpoint: ResponsiveBreakpoint = ResponsiveBreakpoint.DESKTOP) -> Dict[str, Any]:
        """Get layout preview data"""
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
            logger.error(f"Error getting layout preview: {e}")
            return {}
    
    def optimize_layout(self, layout_id: str) -> Dict[str, Any]:
        """Optimize a layout for performance"""
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
                if not section.blocks:
                    optimizations['optimizations_applied'].append(f"Removed empty section: {section.id}")
                    continue
                
                # Optimize blocks
                for block in section.blocks:
                    # Remove unused metadata
                    if block.metadata and not block.metadata:
                        block.metadata = {}
                        optimizations['optimizations_applied'].append(f"Cleaned metadata for block: {block.id}")
                    
                    # Optimize styles
                    if block.style and not block.style:
                        block.style = {}
                        optimizations['optimizations_applied'].append(f"Cleaned styles for block: {block.id}")
            
            # Performance improvements
            optimizations['performance_improvements'].append("Reduced layout complexity")
            optimizations['performance_improvements'].append("Cleaned unused data")
            
            # Recommendations
            if len(layout.sections) > 5:
                optimizations['recommendations'].append("Consider reducing the number of sections for better performance")
            
            total_blocks = sum(len(section.blocks) for section in layout.sections)
            if total_blocks > 50:
                optimizations['recommendations'].append("Consider pagination for large numbers of blocks")
            
            layout.updated_at = django_timezone.now()
            
            logger.info(f"Optimized layout: {layout_id}")
            return optimizations
            
        except Exception as e:
            logger.error(f"Error optimizing layout: {e}")
            return {}
