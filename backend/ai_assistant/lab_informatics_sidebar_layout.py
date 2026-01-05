"""
Lab Informatics Focus Sidebar Layout

This module provides the sidebar layout and navigation structure
for the Lab Informatics Focus mode of the AnyLab application.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from django.utils import timezone as django_timezone

# Import from refactored modules
from .lab_informatics import (
    LabInformaticsProduct,
    LabInformaticsCategory,
    TroubleshootingCategory,
    TroubleshootingItem,
    LabInformaticsNavigationItem,
    LabInformaticsSidebarSection,
    LabInformaticsSidebarLayout,
)
# Import section builders
from .lab_informatics.section_builders import (
    _create_dashboard_section,
    _create_lab_informatics_products_section,
    _create_troubleshooting_section,
    _create_data_management_section,
    _create_workflow_automation_section,
    _create_compliance_section,
    _create_integration_section,
    _create_analytics_section,
    _create_collaboration_section,
    _create_infrastructure_section,
    _create_security_section,
    _create_support_section,
    _create_ai_assistant_section,
    _create_user_section,
    _create_mobile_dashboard_section,
    _create_mobile_products_section,
    _create_mobile_troubleshooting_section,
    _create_mobile_ai_section,
)

logger = logging.getLogger(__name__)


class LabInformaticsSidebarLayoutManager:
    """Lab Informatics Focus Sidebar Layout Manager"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize Lab Informatics sidebar layout"""
        self.config = config or {}
        self.layout_enabled = self.config.get('layout_enabled', True)
        self.troubleshooting_enabled = self.config.get('troubleshooting_enabled', True)
        self.dynamic_content_enabled = self.config.get('dynamic_content_enabled', True)
        self.user_preferences_enabled = self.config.get('user_preferences_enabled', True)
        self.analytics_enabled = self.config.get('analytics_enabled', True)
        
        # Layout configuration
        self.default_theme = self.config.get('default_theme', 'lab-informatics')
        self.default_width = self.config.get('default_width', '320px')
        self.collapsible_sections = self.config.get('collapsible_sections', True)
        self.remember_state = self.config.get('remember_state', True)
        
        # Troubleshooting configuration
        self.show_troubleshooting_counts = self.config.get('show_troubleshooting_counts', True)
        self.show_featured_troubleshooting = self.config.get('show_featured_troubleshooting', True)
        self.max_troubleshooting_items = self.config.get('max_troubleshooting_items', 10)
        
        # Content configuration
        self.show_product_counts = self.config.get('show_product_counts', True)
        self.show_recent_content = self.config.get('show_recent_content', True)
        self.show_popular_content = self.config.get('show_popular_content', True)
        self.max_recent_items = self.config.get('max_recent_items', 5)
        self.max_popular_items = self.config.get('max_popular_items', 5)
        
        # Initialize layout
        self._initialize_layout()
        
        logger.info("Lab Informatics Sidebar Layout initialized")
    
    def _initialize_layout(self):
        """Initialize the sidebar layout structure"""
        try:
            # Create main layout
            self.layout = LabInformaticsSidebarLayout(
                id="lab_informatics_sidebar",
                name="Lab Informatics Focus",
                description="Sidebar layout for Lab Informatics Focus navigation",
                sections=[],
                theme=self.default_theme,
                width=self.default_width
            )
            
            # Create sections
            self._create_main_sections()
            
            logger.info("Lab Informatics sidebar layout initialized with sections")
            
        except Exception as e:
            logger.error(f"Error initializing sidebar layout: {e}")
    
    def _create_main_sections(self):
        """Create main sidebar sections"""
        try:
            sections = [
                _create_dashboard_section(),
                _create_lab_informatics_products_section(),
                _create_troubleshooting_section(),
                _create_data_management_section(),
                _create_workflow_automation_section(),
                _create_compliance_section(),
                _create_integration_section(),
                _create_analytics_section(),
                _create_collaboration_section(),
                _create_infrastructure_section(),
                _create_security_section(),
                _create_support_section(),
                _create_ai_assistant_section(),
                _create_user_section()
            ]
            
            # Add sections to layout
            self.layout.sections.extend(sections)
            
        except Exception as e:
            logger.error(f"Error creating main sections: {e}")
    
    def get_layout(self) -> LabInformaticsSidebarLayout:
        """Get the current sidebar layout"""
        return self.layout
    
    def get_section(self, section_id: str) -> Optional[LabInformaticsSidebarSection]:
        """Get a specific section by ID"""
        try:
            for section in self.layout.sections:
                if section.id == section_id:
                    return section
            return None
            
        except Exception as e:
            logger.error(f"Error getting section {section_id}: {e}")
            return None
    
    def get_navigation_item(self, item_id: str) -> Optional[LabInformaticsNavigationItem]:
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
    
    def get_troubleshooting_items(self, category: TroubleshootingCategory = None, product: LabInformaticsProduct = None) -> List[TroubleshootingItem]:
        """Get troubleshooting items filtered by category and product"""
        try:
            items = []
            
            for section in self.layout.sections:
                for item in section.items:
                    for troubleshooting_item in item.troubleshooting_items:
                        if category and troubleshooting_item.category != category:
                            continue
                        if product and product not in troubleshooting_item.related_products:
                            continue
                        items.append(troubleshooting_item)
            
            return items
            
        except Exception as e:
            logger.error(f"Error getting troubleshooting items: {e}")
            return []
    
    def get_featured_troubleshooting_items(self, limit: int = 5) -> List[TroubleshootingItem]:
        """Get featured troubleshooting items"""
        try:
            items = []
            
            for section in self.layout.sections:
                for item in section.items:
                    for troubleshooting_item in item.troubleshooting_items:
                        if troubleshooting_item.is_featured:
                            items.append(troubleshooting_item)
            
            # Sort by view count and limit
            items.sort(key=lambda x: x.view_count, reverse=True)
            return items[:limit]
            
        except Exception as e:
            logger.error(f"Error getting featured troubleshooting items: {e}")
            return []
    
    def search_troubleshooting(self, query: str) -> List[TroubleshootingItem]:
        """Search troubleshooting items"""
        try:
            results = []
            query_lower = query.lower()
            
            for section in self.layout.sections:
                for item in section.items:
                    for troubleshooting_item in item.troubleshooting_items:
                        # Search in title, description, solution, and tags
                        if (query_lower in troubleshooting_item.title.lower() or
                            query_lower in troubleshooting_item.description.lower() or
                            query_lower in troubleshooting_item.solution.lower() or
                            any(query_lower in tag.lower() for tag in troubleshooting_item.tags)):
                            results.append(troubleshooting_item)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching troubleshooting: {e}")
            return []
    
    def get_product_troubleshooting(self, product: LabInformaticsProduct) -> List[TroubleshootingItem]:
        """Get troubleshooting items for a specific product"""
        try:
            items = []
            
            for section in self.layout.sections:
                for item in section.items:
                    for troubleshooting_item in item.troubleshooting_items:
                        if product in troubleshooting_item.related_products:
                            items.append(troubleshooting_item)
            
            return items
            
        except Exception as e:
            logger.error(f"Error getting product troubleshooting: {e}")
            return []
    
    def get_category_troubleshooting(self, category: TroubleshootingCategory) -> List[TroubleshootingItem]:
        """Get troubleshooting items for a specific category"""
        try:
            items = []
            
            for section in self.layout.sections:
                for item in section.items:
                    for troubleshooting_item in item.troubleshooting_items:
                        if troubleshooting_item.category == category:
                            items.append(troubleshooting_item)
            
            return items
            
        except Exception as e:
            logger.error(f"Error getting category troubleshooting: {e}")
            return []
    
    def add_troubleshooting_item(self, item: TroubleshootingItem, section_id: str, navigation_item_id: str):
        """Add a troubleshooting item to a navigation item"""
        try:
            navigation_item = self.get_navigation_item(navigation_item_id)
            if navigation_item:
                navigation_item.troubleshooting_items.append(item)
                logger.info(f"Added troubleshooting item {item.id} to {navigation_item_id}")
            
        except Exception as e:
            logger.error(f"Error adding troubleshooting item: {e}")
    
    def update_troubleshooting_item(self, item_id: str, updates: Dict[str, Any]):
        """Update a troubleshooting item"""
        try:
            for section in self.layout.sections:
                for item in section.items:
                    for troubleshooting_item in item.troubleshooting_items:
                        if troubleshooting_item.id == item_id:
                            for key, value in updates.items():
                                if hasattr(troubleshooting_item, key):
                                    setattr(troubleshooting_item, key, value)
                            
                            logger.info(f"Updated troubleshooting item: {item_id}")
                            return
            
        except Exception as e:
            logger.error(f"Error updating troubleshooting item: {e}")
    
    def remove_troubleshooting_item(self, item_id: str):
        """Remove a troubleshooting item"""
        try:
            for section in self.layout.sections:
                for item in section.items:
                    item.troubleshooting_items = [
                        troubleshooting_item for troubleshooting_item in item.troubleshooting_items
                        if troubleshooting_item.id != item_id
                    ]
            
            logger.info(f"Removed troubleshooting item: {item_id}")
            
        except Exception as e:
            logger.error(f"Error removing troubleshooting item: {e}")
    
    def increment_troubleshooting_view_count(self, item_id: str):
        """Increment view count for a troubleshooting item"""
        try:
            for section in self.layout.sections:
                for item in section.items:
                    for troubleshooting_item in item.troubleshooting_items:
                        if troubleshooting_item.id == item_id:
                            troubleshooting_item.view_count += 1
                            logger.info(f"Incremented view count for troubleshooting item: {item_id}")
                            return
            
        except Exception as e:
            logger.error(f"Error incrementing view count: {e}")
    
    def get_troubleshooting_statistics(self) -> Dict[str, Any]:
        """Get troubleshooting statistics"""
        try:
            stats = {
                'total_items': 0,
                'items_by_category': {},
                'items_by_product': {},
                'items_by_severity': {},
                'featured_items': 0,
                'total_views': 0,
                'most_viewed': []
            }
            
            for section in self.layout.sections:
                for item in section.items:
                    for troubleshooting_item in item.troubleshooting_items:
                        stats['total_items'] += 1
                        
                        # Count by category
                        category = troubleshooting_item.category.value
                        stats['items_by_category'][category] = stats['items_by_category'].get(category, 0) + 1
                        
                        # Count by product
                        for product in troubleshooting_item.related_products:
                            product_name = product.value
                            stats['items_by_product'][product_name] = stats['items_by_product'].get(product_name, 0) + 1
                        
                        # Count by severity
                        severity = troubleshooting_item.severity
                        stats['items_by_severity'][severity] = stats['items_by_severity'].get(severity, 0) + 1
                        
                        # Count featured items
                        if troubleshooting_item.is_featured:
                            stats['featured_items'] += 1
                        
                        # Count total views
                        stats['total_views'] += troubleshooting_item.view_count
                        
                        # Track most viewed
                        stats['most_viewed'].append({
                            'id': troubleshooting_item.id,
                            'title': troubleshooting_item.title,
                            'views': troubleshooting_item.view_count
                        })
            
            # Sort most viewed by view count
            stats['most_viewed'].sort(key=lambda x: x['views'], reverse=True)
            stats['most_viewed'] = stats['most_viewed'][:10]  # Top 10
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting troubleshooting statistics: {e}")
            return {}
    
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
                'show_troubleshooting': self.layout.show_troubleshooting,
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
                    'category': section.category.value if section.category else None,
                    'items': []
                }
                
                for item in section.items:
                    item_data = {
                        'id': item.id,
                        'title': item.title,
                        'type': item.type,
                        'icon': item.icon,
                        'url': item.url,
                        'badge': item.badge,
                        'tooltip': item.tooltip,
                        'permissions': item.permissions,
                        'is_active': item.is_active,
                        'is_expanded': item.is_expanded,
                        'order': item.order,
                        'metadata': item.metadata,
                        'related_products': [product.value for product in item.related_products],
                        'troubleshooting_items': [
                            {
                                'id': troubleshooting_item.id,
                                'title': troubleshooting_item.title,
                                'category': troubleshooting_item.category.value,
                                'severity': troubleshooting_item.severity,
                                'description': troubleshooting_item.description,
                                'solution': troubleshooting_item.solution,
                                'related_products': [product.value for product in troubleshooting_item.related_products],
                                'tags': troubleshooting_item.tags,
                                'url': troubleshooting_item.url,
                                'is_featured': troubleshooting_item.is_featured,
                                'view_count': troubleshooting_item.view_count,
                                'last_updated': troubleshooting_item.last_updated.isoformat()
                            }
                            for troubleshooting_item in item.troubleshooting_items
                        ],
                        'children': []
                    }
                    
                    for child in item.children:
                        child_data = {
                            'id': child.id,
                            'title': child.title,
                            'type': child.type,
                            'icon': child.icon,
                            'url': child.url,
                            'badge': child.badge,
                            'tooltip': child.tooltip,
                            'permissions': child.permissions,
                            'is_active': child.is_active,
                            'is_expanded': child.is_expanded,
                            'order': child.order,
                            'metadata': child.metadata,
                            'related_products': [product.value for product in child.related_products]
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
            self.layout.show_troubleshooting = layout_data.get('show_troubleshooting', self.layout.show_troubleshooting)
            
            # Clear existing sections
            self.layout.sections = []
            
            # Import sections
            for section_data in layout_data.get('sections', []):
                section = LabInformaticsSidebarSection(
                    id=section_data['id'],
                    title=section_data['title'],
                    icon=section_data['icon'],
                    items=[],
                    order=section_data['order'],
                    is_collapsible=section_data.get('is_collapsible', True),
                    is_collapsed=section_data.get('is_collapsed', False),
                    permissions=section_data.get('permissions', []),
                    category=LabInformaticsCategory(section_data['category']) if section_data.get('category') else None
                )
                
                # Import items
                for item_data in section_data.get('items', []):
                    item = LabInformaticsNavigationItem(
                        id=item_data['id'],
                        title=item_data['title'],
                        type=item_data['type'],
                        icon=item_data.get('icon'),
                        url=item_data.get('url'),
                        badge=item_data.get('badge'),
                        tooltip=item_data.get('tooltip'),
                        permissions=item_data.get('permissions', []),
                        is_active=item_data.get('is_active', False),
                        is_expanded=item_data.get('is_expanded', False),
                        order=item_data.get('order', 0),
                        metadata=item_data.get('metadata', {}),
                        related_products=[LabInformaticsProduct(product) for product in item_data.get('related_products', [])]
                    )
                    
                    # Import troubleshooting items
                    for troubleshooting_data in item_data.get('troubleshooting_items', []):
                        troubleshooting_item = TroubleshootingItem(
                            id=troubleshooting_data['id'],
                            title=troubleshooting_data['title'],
                            category=TroubleshootingCategory(troubleshooting_data['category']),
                            severity=troubleshooting_data['severity'],
                            description=troubleshooting_data['description'],
                            solution=troubleshooting_data['solution'],
                            related_products=[LabInformaticsProduct(product) for product in troubleshooting_data['related_products']],
                            tags=troubleshooting_data['tags'],
                            url=troubleshooting_data.get('url'),
                            is_featured=troubleshooting_data.get('is_featured', False),
                            view_count=troubleshooting_data.get('view_count', 0),
                            last_updated=datetime.fromisoformat(troubleshooting_data['last_updated'])
                        )
                        item.troubleshooting_items.append(troubleshooting_item)
                    
                    # Import children
                    for child_data in item_data.get('children', []):
                        child = LabInformaticsNavigationItem(
                            id=child_data['id'],
                            title=child_data['title'],
                            type=child_data['type'],
                            icon=child_data.get('icon'),
                            url=child_data.get('url'),
                            badge=child_data.get('badge'),
                            tooltip=child_data.get('tooltip'),
                            permissions=child_data.get('permissions', []),
                            is_active=child_data.get('is_active', False),
                            is_expanded=child_data.get('is_expanded', False),
                            order=child_data.get('order', 0),
                            metadata=child_data.get('metadata', {}),
                            related_products=[LabInformaticsProduct(product) for product in child_data.get('related_products', [])]
                        )
                        item.children.append(child)
                    
                    section.items.append(item)
                
                self.layout.sections.append(section)
            
            # Sort sections by order
            self.layout.sections.sort(key=lambda x: x.order)
            
            logger.info("Lab Informatics layout imported successfully")
            
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
                'total_troubleshooting_items': 0,
                'featured_troubleshooting_items': 0,
                'sections_by_category': {},
                'items_by_type': {},
                'troubleshooting_by_category': {},
                'troubleshooting_by_product': {}
            }
            
            for section in self.layout.sections:
                if section.is_collapsed:
                    stats['collapsed_sections'] += 1
                
                stats['total_items'] += len(section.items)
                
                # Count by category
                if section.category:
                    category = section.category.value
                    stats['sections_by_category'][category] = stats['sections_by_category'].get(category, 0) + 1
                
                for item in section.items:
                    if item.is_active:
                        stats['active_items'] += 1
                    
                    if item.is_expanded:
                        stats['expanded_items'] += 1
                    
                    stats['total_children'] += len(item.children)
                    
                    # Count by type
                    item_type = item.type
                    stats['items_by_type'][item_type] = stats['items_by_type'].get(item_type, 0) + 1
                    
                    # Count troubleshooting items
                    stats['total_troubleshooting_items'] += len(item.troubleshooting_items)
                    
                    for troubleshooting_item in item.troubleshooting_items:
                        if troubleshooting_item.is_featured:
                            stats['featured_troubleshooting_items'] += 1
                        
                        # Count by category
                        category = troubleshooting_item.category.value
                        stats['troubleshooting_by_category'][category] = stats['troubleshooting_by_category'].get(category, 0) + 1
                        
                        # Count by product
                        for product in troubleshooting_item.related_products:
                            product_name = product.value
                            stats['troubleshooting_by_product'][product_name] = stats['troubleshooting_by_product'].get(product_name, 0) + 1
            
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
                    
                    for troubleshooting_item in item.troubleshooting_items:
                        if troubleshooting_item.id in all_ids:
                            errors.append(f"Duplicate troubleshooting item ID: {troubleshooting_item.id}")
                        all_ids.add(troubleshooting_item.id)
            
            # Check for missing required fields
            for section in self.layout.sections:
                if not section.title:
                    errors.append(f"Section {section.id} missing title")
                
                for item in section.items:
                    if not item.title:
                        errors.append(f"Item {item.id} missing title")
                    
                    if item.type == "link" and not item.url:
                        errors.append(f"Link item {item.id} missing URL")
            
            return errors
            
        except Exception as e:
            logger.error(f"Error validating layout: {e}")
            return [f"Validation error: {e}"]
    
    def reset_layout(self):
        """Reset layout to default configuration"""
        try:
            self._initialize_layout()
            logger.info("Lab Informatics layout reset to default configuration")
            
        except Exception as e:
            logger.error(f"Error resetting layout: {e}")
    
    def get_mobile_layout(self) -> LabInformaticsSidebarLayout:
        """Get mobile-optimized layout"""
        try:
            mobile_layout = LabInformaticsSidebarLayout(
                id="lab_informatics_mobile_sidebar",
                name="Lab Informatics Focus (Mobile)",
                description="Mobile-optimized sidebar layout for Lab Informatics",
                sections=[],
                theme=self.default_theme,
                width="100%",
                is_resizable=False,
                show_search=True,
                show_user_info=True,
                show_notifications=True,
                show_troubleshooting=True
            )
            
            # Create simplified sections for mobile
            mobile_sections = [
                self._create_mobile_dashboard_section(),
                self._create_mobile_products_section(),
                self._create_mobile_troubleshooting_section(),
                self._create_mobile_ai_section()
            ]
            
            mobile_layout.sections.extend(mobile_sections)
            
            return mobile_layout
            
        except Exception as e:
            logger.error(f"Error creating mobile layout: {e}")
            return self.layout
    
    def _create_mobile_dashboard_section(self) -> LabInformaticsSidebarSection:
        """Create mobile dashboard section"""
        return LabInformaticsSidebarSection(
            id="mobile_dashboard",
            title="Dashboard",
            icon="dashboard",
            items=[
                LabInformaticsNavigationItem(
                    id="mobile_dashboard_overview",
                    title="Overview",
                    type="link",
                    icon="dashboard",
                    url="/lab-informatics/dashboard",
                    order=1
                )
            ],
            order=1,
            is_collapsible=False
        )
    
    def _create_mobile_products_section(self) -> LabInformaticsSidebarSection:
        """Create mobile products section"""
        return LabInformaticsSidebarSection(
            id="mobile_products",
            title="Products",
            icon="lab-informatics",
            items=[
                LabInformaticsNavigationItem(
                    id="mobile_products_all",
                    title="All Products",
                    type="link",
                    icon="lab-informatics",
                    url="/lab-informatics/products",
                    order=1
                )
            ],
            order=2,
            is_collapsible=False
        )
    
    def _create_mobile_troubleshooting_section(self) -> LabInformaticsSidebarSection:
        """Create mobile troubleshooting section"""
        return LabInformaticsSidebarSection(
            id="mobile_troubleshooting",
            title="Troubleshooting",
            icon="troubleshoot",
            items=[
                LabInformaticsNavigationItem(
                    id="mobile_troubleshooting_all",
                    title="All Issues",
                    type="link",
                    icon="troubleshoot",
                    url="/lab-informatics/troubleshooting",
                    order=1
                )
            ],
            order=3,
            is_collapsible=False
        )
    
    def _create_mobile_ai_section(self) -> LabInformaticsSidebarSection:
        """Create mobile AI section"""
        return LabInformaticsSidebarSection(
            id="mobile_ai",
            title="AI Assistant",
            icon="ai",
            items=[
                LabInformaticsNavigationItem(
                    id="mobile_ai_chat",
                    title="AI Chat",
                    type="link",
                    icon="chat",
                    url="/lab-informatics/ai/chat",
                    order=1
                )
            ],
            order=4,
            is_collapsible=False
        )
