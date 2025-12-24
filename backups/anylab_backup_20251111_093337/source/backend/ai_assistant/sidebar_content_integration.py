"""
Sidebar and Content Integration

This module provides integration between sidebar navigation and content display,
including dynamic content loading, context-aware navigation, and seamless user experience.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from django.utils import timezone as django_timezone
from django.core.cache import cache

logger = logging.getLogger(__name__)


class NavigationMode(Enum):
    """Navigation mode enumeration"""
    GENERAL_AGILENT = "general_agilent"
    LAB_INFORMATICS = "lab_informatics"
    TROUBLESHOOTING = "troubleshooting"
    CUSTOM = "custom"


class ContentView(Enum):
    """Content view enumeration"""
    LIST = "list"
    GRID = "grid"
    DETAIL = "detail"
    COMPARISON = "comparison"
    SEARCH = "search"
    FILTERED = "filtered"


class IntegrationType(Enum):
    """Integration type enumeration"""
    NAVIGATION = "navigation"
    CONTENT_LOADING = "content_loading"
    SEARCH_INTEGRATION = "search_integration"
    FILTER_INTEGRATION = "filter_integration"
    CONTEXT_SWITCHING = "context_switching"
    USER_PREFERENCES = "user_preferences"


@dataclass
class SidebarItem:
    """Sidebar item structure"""
    id: str
    title: str
    icon: str
    path: str
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)
    content_type: str = "default"
    metadata: Dict[str, Any] = field(default_factory=dict)
    order: int = 0
    visible: bool = True
    created_at: datetime = field(default_factory=lambda: django_timezone.now())
    updated_at: datetime = field(default_factory=lambda: django_timezone.now())


@dataclass
class ContentContext:
    """Content context structure"""
    id: str
    navigation_mode: NavigationMode
    content_view: ContentView
    current_path: str
    breadcrumb: List[str] = field(default_factory=list)
    filters: Dict[str, Any] = field(default_factory=dict)
    search_query: Optional[str] = None
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: django_timezone.now())
    updated_at: datetime = field(default_factory=lambda: django_timezone.now())


@dataclass
class IntegrationRule:
    """Integration rule structure"""
    id: str
    name: str
    integration_type: IntegrationType
    conditions: Dict[str, Any] = field(default_factory=dict)
    actions: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: django_timezone.now())
    updated_at: datetime = field(default_factory=lambda: django_timezone.now())


class SidebarContentIntegration:
    """Sidebar and Content Integration System"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize integration system"""
        self.config = config or {}
        self.integration_enabled = self.config.get('integration_enabled', True)
        self.dynamic_loading = self.config.get('dynamic_loading', True)
        self.context_awareness = self.config.get('context_awareness', True)
        self.cache_enabled = self.config.get('cache_enabled', True)
        
        # Initialize components
        self.sidebar_items = {}
        self.content_contexts = {}
        self.integration_rules = {}
        self.cache = cache if self.cache_enabled else None
        
        # Initialize integration system
        self._initialize_integration_system()
        
        logger.info("Sidebar and Content Integration initialized")
    
    def _initialize_integration_system(self):
        """Initialize integration system components"""
        try:
            # Initialize sidebar structures
            self._initialize_sidebar_structures()
            
            # Initialize integration rules
            self._initialize_integration_rules()
            
            # Initialize content contexts
            self._initialize_content_contexts()
            
            logger.info("Integration system components initialized")
            
        except Exception as e:
            logger.error(f"Error initializing integration system: {e}")
            raise
    
    def _initialize_sidebar_structures(self):
        """Initialize sidebar structures"""
        try:
            # General Agilent Products sidebar
            general_items = [
                {
                    "id": "general_analytical",
                    "title": "Analytical Instruments",
                    "icon": "analytical",
                    "path": "/general/analytical",
                    "content_type": "product_category"
                },
                {
                    "id": "general_life_sciences",
                    "title": "Life Sciences",
                    "icon": "life_sciences",
                    "path": "/general/life-sciences",
                    "content_type": "product_category"
                },
                {
                    "id": "general_diagnostics",
                    "title": "Diagnostics",
                    "icon": "diagnostics",
                    "path": "/general/diagnostics",
                    "content_type": "product_category"
                },
                {
                    "id": "general_applied",
                    "title": "Applied Markets",
                    "icon": "applied",
                    "path": "/general/applied",
                    "content_type": "product_category"
                },
                {
                    "id": "general_software",
                    "title": "Software",
                    "icon": "software",
                    "path": "/general/software",
                    "content_type": "product_category"
                },
                {
                    "id": "general_services",
                    "title": "Services",
                    "icon": "services",
                    "path": "/general/services",
                    "content_type": "product_category"
                }
            ]
            
            # Lab Informatics Focus sidebar
            lab_informatics_items = [
                {
                    "id": "lab_openlab",
                    "title": "OpenLab",
                    "icon": "openlab",
                    "path": "/lab-informatics/openlab",
                    "content_type": "product"
                },
                {
                    "id": "lab_chemstation",
                    "title": "ChemStation",
                    "icon": "chemstation",
                    "path": "/lab-informatics/chemstation",
                    "content_type": "product"
                },
                {
                    "id": "lab_masshunter",
                    "title": "MassHunter",
                    "icon": "masshunter",
                    "path": "/lab-informatics/masshunter",
                    "content_type": "product"
                },
                {
                    "id": "lab_troubleshooting",
                    "title": "Troubleshooting",
                    "icon": "troubleshooting",
                    "path": "/lab-informatics/troubleshooting",
                    "content_type": "troubleshooting"
                },
                {
                    "id": "lab_methods",
                    "title": "Method Development",
                    "icon": "methods",
                    "path": "/lab-informatics/methods",
                    "content_type": "methods"
                },
                {
                    "id": "lab_data_analysis",
                    "title": "Data Analysis",
                    "icon": "data_analysis",
                    "path": "/lab-informatics/data-analysis",
                    "content_type": "data_analysis"
                }
            ]
            
            # Create sidebar items
            for item_data in general_items + lab_informatics_items:
                item = SidebarItem(**item_data)
                self.sidebar_items[item.id] = item
            
            logger.info(f"Initialized {len(self.sidebar_items)} sidebar items")
            
        except Exception as e:
            logger.error(f"Error initializing sidebar structures: {e}")
            raise
    
    def _initialize_integration_rules(self):
        """Initialize integration rules"""
        try:
            rules = [
                {
                    "id": "navigation_mode_switch",
                    "name": "Navigation Mode Switch",
                    "integration_type": IntegrationType.NAVIGATION,
                    "conditions": {"navigation_mode": "general_agilent"},
                    "actions": {"show_sidebar": "general_agilent", "load_content": "general_agilent"},
                    "priority": 1
                },
                {
                    "id": "lab_informatics_mode",
                    "name": "Lab Informatics Mode",
                    "integration_type": IntegrationType.NAVIGATION,
                    "conditions": {"navigation_mode": "lab_informatics"},
                    "actions": {"show_sidebar": "lab_informatics", "load_content": "lab_informatics"},
                    "priority": 1
                },
                {
                    "id": "troubleshooting_mode",
                    "name": "Troubleshooting Mode",
                    "integration_type": IntegrationType.NAVIGATION,
                    "conditions": {"navigation_mode": "troubleshooting"},
                    "actions": {"show_sidebar": "troubleshooting", "load_content": "troubleshooting"},
                    "priority": 1
                },
                {
                    "id": "content_search_integration",
                    "name": "Content Search Integration",
                    "integration_type": IntegrationType.SEARCH_INTEGRATION,
                    "conditions": {"search_query": "not_empty"},
                    "actions": {"filter_content": True, "highlight_results": True},
                    "priority": 2
                },
                {
                    "id": "filter_integration",
                    "name": "Filter Integration",
                    "integration_type": IntegrationType.FILTER_INTEGRATION,
                    "conditions": {"filters": "not_empty"},
                    "actions": {"apply_filters": True, "update_sidebar": True},
                    "priority": 2
                }
            ]
            
            for rule_data in rules:
                rule = IntegrationRule(**rule_data)
                self.integration_rules[rule.id] = rule
            
            logger.info(f"Initialized {len(self.integration_rules)} integration rules")
            
        except Exception as e:
            logger.error(f"Error initializing integration rules: {e}")
            raise
    
    def _initialize_content_contexts(self):
        """Initialize content contexts"""
        try:
            contexts = [
                {
                    "id": "general_agilent_context",
                    "navigation_mode": NavigationMode.GENERAL_AGILENT,
                    "content_view": ContentView.LIST,
                    "current_path": "/general",
                    "breadcrumb": ["General Agilent Products"],
                    "user_preferences": {"view_mode": "list", "sort_by": "name"}
                },
                {
                    "id": "lab_informatics_context",
                    "navigation_mode": NavigationMode.LAB_INFORMATICS,
                    "content_view": ContentView.LIST,
                    "current_path": "/lab-informatics",
                    "breadcrumb": ["Lab Informatics Focus"],
                    "user_preferences": {"view_mode": "list", "sort_by": "relevance"}
                },
                {
                    "id": "troubleshooting_context",
                    "navigation_mode": NavigationMode.TROUBLESHOOTING,
                    "content_view": ContentView.SEARCH,
                    "current_path": "/troubleshooting",
                    "breadcrumb": ["Troubleshooting"],
                    "user_preferences": {"view_mode": "search", "sort_by": "relevance"}
                }
            ]
            
            for context_data in contexts:
                context = ContentContext(**context_data)
                self.content_contexts[context.id] = context
            
            logger.info(f"Initialized {len(self.content_contexts)} content contexts")
            
        except Exception as e:
            logger.error(f"Error initializing content contexts: {e}")
            raise
    
    def switch_navigation_mode(self, mode: NavigationMode, user_id: str = None) -> ContentContext:
        """Switch navigation mode"""
        try:
            # Get or create context for mode
            context_id = f"{mode.value}_context"
            context = self.content_contexts.get(context_id)
            
            if not context:
                context = ContentContext(
                    id=context_id,
                    navigation_mode=mode,
                    content_view=ContentView.LIST,
                    current_path=f"/{mode.value}",
                    breadcrumb=[mode.value.replace("_", " ").title()]
                )
                self.content_contexts[context_id] = context
            
            # Apply integration rules
            self._apply_integration_rules(context)
            
            # Update context
            context.updated_at = django_timezone.now()
            
            logger.info(f"Switched to navigation mode: {mode.value}")
            return context
            
        except Exception as e:
            logger.error(f"Error switching navigation mode: {e}")
            raise
    
    def get_sidebar_items(self, navigation_mode: NavigationMode) -> List[SidebarItem]:
        """Get sidebar items for navigation mode"""
        try:
            items = []
            
            # Filter items based on navigation mode
            for item in self.sidebar_items.values():
                if not item.visible:
                    continue
                
                # Check if item belongs to this navigation mode
                if self._item_belongs_to_mode(item, navigation_mode):
                    items.append(item)
            
            # Sort by order
            items.sort(key=lambda x: x.order)
            
            return items
            
        except Exception as e:
            logger.error(f"Error getting sidebar items: {e}")
            return []
    
    def _item_belongs_to_mode(self, item: SidebarItem, mode: NavigationMode) -> bool:
        """Check if item belongs to navigation mode"""
        try:
            if mode == NavigationMode.GENERAL_AGILENT:
                return item.path.startswith("/general")
            elif mode == NavigationMode.LAB_INFORMATICS:
                return item.path.startswith("/lab-informatics")
            elif mode == NavigationMode.TROUBLESHOOTING:
                return item.path.startswith("/troubleshooting")
            else:
                return True
                
        except Exception as e:
            logger.error(f"Error checking item mode: {e}")
            return False
    
    def load_content(self, path: str, navigation_mode: NavigationMode, 
                    filters: Dict[str, Any] = None, search_query: str = None) -> Dict[str, Any]:
        """Load content for a path"""
        try:
            # Check cache first
            if self.cache_enabled:
                cache_key = f"content_{path}_{navigation_mode.value}_{hash(str(filters))}_{hash(search_query or '')}"
                cached_content = self.cache.get(cache_key)
                if cached_content:
                    return cached_content
            
            # Get content based on path and mode
            content = self._get_content_for_path(path, navigation_mode, filters, search_query)
            
            # Apply integration rules
            content = self._apply_content_integration_rules(content, navigation_mode, filters, search_query)
            
            # Cache content
            if self.cache_enabled:
                self.cache.set(cache_key, content, timeout=3600)
            
            return content
            
        except Exception as e:
            logger.error(f"Error loading content: {e}")
            return {}
    
    def _get_content_for_path(self, path: str, navigation_mode: NavigationMode,
                             filters: Dict[str, Any] = None, search_query: str = None) -> Dict[str, Any]:
        """Get content for a specific path"""
        try:
            content = {
                "path": path,
                "navigation_mode": navigation_mode.value,
                "content_type": "default",
                "items": [],
                "metadata": {},
                "breadcrumb": [],
                "filters": filters or {},
                "search_query": search_query
            }
            
            # Mock content based on path
            if path.startswith("/general"):
                content["content_type"] = "general_agilent"
                content["items"] = self._get_general_agilent_content(path, filters, search_query)
                content["breadcrumb"] = ["General Agilent Products"] + path.split("/")[2:]
            elif path.startswith("/lab-informatics"):
                content["content_type"] = "lab_informatics"
                content["items"] = self._get_lab_informatics_content(path, filters, search_query)
                content["breadcrumb"] = ["Lab Informatics Focus"] + path.split("/")[2:]
            elif path.startswith("/troubleshooting"):
                content["content_type"] = "troubleshooting"
                content["items"] = self._get_troubleshooting_content(path, filters, search_query)
                content["breadcrumb"] = ["Troubleshooting"] + path.split("/")[2:]
            
            return content
            
        except Exception as e:
            logger.error(f"Error getting content for path: {e}")
            return {}
    
    def _get_general_agilent_content(self, path: str, filters: Dict[str, Any] = None, search_query: str = None) -> List[Dict[str, Any]]:
        """Get General Agilent content"""
        try:
            # Mock General Agilent content
            items = [
                {
                    "id": "analytical_instruments",
                    "title": "Analytical Instruments",
                    "description": "High-performance analytical instruments for laboratory analysis",
                    "type": "product_category",
                    "path": "/general/analytical",
                    "metadata": {"product_count": 25, "category": "analytical"}
                },
                {
                    "id": "life_sciences",
                    "title": "Life Sciences",
                    "description": "Solutions for life sciences research and development",
                    "type": "product_category",
                    "path": "/general/life-sciences",
                    "metadata": {"product_count": 18, "category": "life_sciences"}
                },
                {
                    "id": "diagnostics",
                    "title": "Diagnostics",
                    "description": "Diagnostic solutions for healthcare and clinical applications",
                    "type": "product_category",
                    "path": "/general/diagnostics",
                    "metadata": {"product_count": 12, "category": "diagnostics"}
                }
            ]
            
            # Apply filters
            if filters:
                items = self._apply_filters(items, filters)
            
            # Apply search
            if search_query:
                items = self._apply_search(items, search_query)
            
            return items
            
        except Exception as e:
            logger.error(f"Error getting General Agilent content: {e}")
            return []
    
    def _get_lab_informatics_content(self, path: str, filters: Dict[str, Any] = None, search_query: str = None) -> List[Dict[str, Any]]:
        """Get Lab Informatics content"""
        try:
            # Mock Lab Informatics content
            items = [
                {
                    "id": "openlab",
                    "title": "OpenLab",
                    "description": "Comprehensive laboratory data management and analysis platform",
                    "type": "product",
                    "path": "/lab-informatics/openlab",
                    "metadata": {"version": "2.8", "category": "software"}
                },
                {
                    "id": "chemstation",
                    "title": "ChemStation",
                    "description": "Chromatography data system for analytical instruments",
                    "type": "product",
                    "path": "/lab-informatics/chemstation",
                    "metadata": {"version": "B.04.03", "category": "software"}
                },
                {
                    "id": "masshunter",
                    "title": "MassHunter",
                    "description": "Mass spectrometry data analysis software",
                    "type": "product",
                    "path": "/lab-informatics/masshunter",
                    "metadata": {"version": "10.0", "category": "software"}
                }
            ]
            
            # Apply filters
            if filters:
                items = self._apply_filters(items, filters)
            
            # Apply search
            if search_query:
                items = self._apply_search(items, search_query)
            
            return items
            
        except Exception as e:
            logger.error(f"Error getting Lab Informatics content: {e}")
            return []
    
    def _get_troubleshooting_content(self, path: str, filters: Dict[str, Any] = None, search_query: str = None) -> List[Dict[str, Any]]:
        """Get troubleshooting content"""
        try:
            # Mock troubleshooting content
            items = [
                {
                    "id": "common_issues",
                    "title": "Common Issues",
                    "description": "Frequently encountered problems and solutions",
                    "type": "troubleshooting",
                    "path": "/troubleshooting/common",
                    "metadata": {"issue_count": 45, "category": "general"}
                },
                {
                    "id": "error_codes",
                    "title": "Error Codes",
                    "description": "Error code reference and resolution guides",
                    "type": "troubleshooting",
                    "path": "/troubleshooting/error-codes",
                    "metadata": {"error_count": 120, "category": "errors"}
                },
                {
                    "id": "maintenance",
                    "title": "Maintenance",
                    "description": "Preventive maintenance and calibration procedures",
                    "type": "troubleshooting",
                    "path": "/troubleshooting/maintenance",
                    "metadata": {"procedure_count": 30, "category": "maintenance"}
                }
            ]
            
            # Apply filters
            if filters:
                items = self._apply_filters(items, filters)
            
            # Apply search
            if search_query:
                items = self._apply_search(items, search_query)
            
            return items
            
        except Exception as e:
            logger.error(f"Error getting troubleshooting content: {e}")
            return []
    
    def _apply_filters(self, items: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply filters to items"""
        try:
            filtered_items = items
            
            for filter_key, filter_value in filters.items():
                if filter_key == "category":
                    filtered_items = [item for item in filtered_items if item.get("metadata", {}).get("category") == filter_value]
                elif filter_key == "type":
                    filtered_items = [item for item in filtered_items if item.get("type") == filter_value]
                elif filter_key == "version":
                    filtered_items = [item for item in filtered_items if item.get("metadata", {}).get("version") == filter_value]
            
            return filtered_items
            
        except Exception as e:
            logger.error(f"Error applying filters: {e}")
            return items
    
    def _apply_search(self, items: List[Dict[str, Any]], search_query: str) -> List[Dict[str, Any]]:
        """Apply search to items"""
        try:
            search_lower = search_query.lower()
            search_results = []
            
            for item in items:
                # Search in title and description
                if (search_lower in item.get("title", "").lower() or
                    search_lower in item.get("description", "").lower()):
                    search_results.append(item)
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error applying search: {e}")
            return items
    
    def _apply_integration_rules(self, context: ContentContext):
        """Apply integration rules to context"""
        try:
            for rule in self.integration_rules.values():
                if not rule.enabled:
                    continue
                
                # Check conditions
                if self._check_rule_conditions(rule, context):
                    # Apply actions
                    self._apply_rule_actions(rule, context)
            
        except Exception as e:
            logger.error(f"Error applying integration rules: {e}")
    
    def _apply_content_integration_rules(self, content: Dict[str, Any], navigation_mode: NavigationMode,
                                       filters: Dict[str, Any] = None, search_query: str = None) -> Dict[str, Any]:
        """Apply content integration rules"""
        try:
            # Apply rules based on content type
            if content.get("content_type") == "general_agilent":
                content["sidebar_items"] = self.get_sidebar_items(NavigationMode.GENERAL_AGILENT)
            elif content.get("content_type") == "lab_informatics":
                content["sidebar_items"] = self.get_sidebar_items(NavigationMode.LAB_INFORMATICS)
            elif content.get("content_type") == "troubleshooting":
                content["sidebar_items"] = self.get_sidebar_items(NavigationMode.TROUBLESHOOTING)
            
            # Add integration metadata
            content["integration"] = {
                "navigation_mode": navigation_mode.value,
                "filters_applied": bool(filters),
                "search_applied": bool(search_query),
                "sidebar_updated": True
            }
            
            return content
            
        except Exception as e:
            logger.error(f"Error applying content integration rules: {e}")
            return content
    
    def _check_rule_conditions(self, rule: IntegrationRule, context: ContentContext) -> bool:
        """Check if rule conditions are met"""
        try:
            conditions = rule.conditions
            
            # Check navigation mode
            if "navigation_mode" in conditions:
                if context.navigation_mode.value != conditions["navigation_mode"]:
                    return False
            
            # Check content view
            if "content_view" in conditions:
                if context.content_view.value != conditions["content_view"]:
                    return False
            
            # Check path
            if "path" in conditions:
                if not context.current_path.startswith(conditions["path"]):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking rule conditions: {e}")
            return False
    
    def _apply_rule_actions(self, rule: IntegrationRule, context: ContentContext):
        """Apply rule actions to context"""
        try:
            actions = rule.actions
            
            # Apply sidebar actions
            if "show_sidebar" in actions:
                context.metadata["sidebar"] = actions["show_sidebar"]
            
            # Apply content loading actions
            if "load_content" in actions:
                context.metadata["content_loader"] = actions["load_content"]
            
            # Apply filter actions
            if "apply_filters" in actions:
                context.metadata["filters_enabled"] = actions["apply_filters"]
            
            # Apply search actions
            if "highlight_results" in actions:
                context.metadata["search_highlighting"] = actions["highlight_results"]
            
        except Exception as e:
            logger.error(f"Error applying rule actions: {e}")
    
    def get_content_context(self, context_id: str) -> Optional[ContentContext]:
        """Get a content context by ID"""
        return self.content_contexts.get(context_id)
    
    def get_sidebar_item(self, item_id: str) -> Optional[SidebarItem]:
        """Get a sidebar item by ID"""
        return self.sidebar_items.get(item_id)
    
    def get_integration_rule(self, rule_id: str) -> Optional[IntegrationRule]:
        """Get an integration rule by ID"""
        return self.integration_rules.get(rule_id)
    
    def get_integration_statistics(self) -> Dict[str, Any]:
        """Get integration statistics"""
        try:
            stats = {
                "total_sidebar_items": len(self.sidebar_items),
                "total_content_contexts": len(self.content_contexts),
                "total_integration_rules": len(self.integration_rules),
                "sidebar_items_by_mode": {},
                "integration_rules_by_type": {},
                "contexts_by_mode": {},
                "integration_enabled": self.integration_enabled,
                "dynamic_loading": self.dynamic_loading,
                "context_awareness": self.context_awareness
            }
            
            # Count sidebar items by mode
            for item in self.sidebar_items.values():
                if item.path.startswith("/general"):
                    stats["sidebar_items_by_mode"]["general_agilent"] = stats["sidebar_items_by_mode"].get("general_agilent", 0) + 1
                elif item.path.startswith("/lab-informatics"):
                    stats["sidebar_items_by_mode"]["lab_informatics"] = stats["sidebar_items_by_mode"].get("lab_informatics", 0) + 1
                elif item.path.startswith("/troubleshooting"):
                    stats["sidebar_items_by_mode"]["troubleshooting"] = stats["sidebar_items_by_mode"].get("troubleshooting", 0) + 1
            
            # Count integration rules by type
            for rule in self.integration_rules.values():
                rule_type = rule.integration_type.value
                stats["integration_rules_by_type"][rule_type] = stats["integration_rules_by_type"].get(rule_type, 0) + 1
            
            # Count contexts by mode
            for context in self.content_contexts.values():
                mode = context.navigation_mode.value
                stats["contexts_by_mode"][mode] = stats["contexts_by_mode"].get(mode, 0) + 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting integration statistics: {e}")
            return {}
    
    def export_integration_data(self) -> Dict[str, Any]:
        """Export integration data"""
        try:
            return {
                "sidebar_items": [
                    {
                        "id": item.id,
                        "title": item.title,
                        "icon": item.icon,
                        "path": item.path,
                        "parent_id": item.parent_id,
                        "children": item.children,
                        "content_type": item.content_type,
                        "metadata": item.metadata,
                        "order": item.order,
                        "visible": item.visible,
                        "created_at": item.created_at.isoformat(),
                        "updated_at": item.updated_at.isoformat()
                    }
                    for item in self.sidebar_items.values()
                ],
                "content_contexts": [
                    {
                        "id": context.id,
                        "navigation_mode": context.navigation_mode.value,
                        "content_view": context.content_view.value,
                        "current_path": context.current_path,
                        "breadcrumb": context.breadcrumb,
                        "filters": context.filters,
                        "search_query": context.search_query,
                        "user_preferences": context.user_preferences,
                        "metadata": context.metadata,
                        "created_at": context.created_at.isoformat(),
                        "updated_at": context.updated_at.isoformat()
                    }
                    for context in self.content_contexts.values()
                ],
                "integration_rules": [
                    {
                        "id": rule.id,
                        "name": rule.name,
                        "integration_type": rule.integration_type.value,
                        "conditions": rule.conditions,
                        "actions": rule.actions,
                        "priority": rule.priority,
                        "enabled": rule.enabled,
                        "metadata": rule.metadata,
                        "created_at": rule.created_at.isoformat(),
                        "updated_at": rule.updated_at.isoformat()
                    }
                    for rule in self.integration_rules.values()
                ]
            }
            
        except Exception as e:
            logger.error(f"Error exporting integration data: {e}")
            return {}
    
    def import_integration_data(self, data: Dict[str, Any]):
        """Import integration data"""
        try:
            # Import sidebar items
            if "sidebar_items" in data:
                for item_data in data["sidebar_items"]:
                    item = SidebarItem(
                        id=item_data["id"],
                        title=item_data["title"],
                        icon=item_data["icon"],
                        path=item_data["path"],
                        parent_id=item_data.get("parent_id"),
                        children=item_data.get("children", []),
                        content_type=item_data.get("content_type", "default"),
                        metadata=item_data.get("metadata", {}),
                        order=item_data.get("order", 0),
                        visible=item_data.get("visible", True),
                        created_at=datetime.fromisoformat(item_data["created_at"]),
                        updated_at=datetime.fromisoformat(item_data["updated_at"])
                    )
                    self.sidebar_items[item.id] = item
            
            # Import content contexts
            if "content_contexts" in data:
                for context_data in data["content_contexts"]:
                    context = ContentContext(
                        id=context_data["id"],
                        navigation_mode=NavigationMode(context_data["navigation_mode"]),
                        content_view=ContentView(context_data["content_view"]),
                        current_path=context_data["current_path"],
                        breadcrumb=context_data.get("breadcrumb", []),
                        filters=context_data.get("filters", {}),
                        search_query=context_data.get("search_query"),
                        user_preferences=context_data.get("user_preferences", {}),
                        metadata=context_data.get("metadata", {}),
                        created_at=datetime.fromisoformat(context_data["created_at"]),
                        updated_at=datetime.fromisoformat(context_data["updated_at"])
                    )
                    self.content_contexts[context.id] = context
            
            # Import integration rules
            if "integration_rules" in data:
                for rule_data in data["integration_rules"]:
                    rule = IntegrationRule(
                        id=rule_data["id"],
                        name=rule_data["name"],
                        integration_type=IntegrationType(rule_data["integration_type"]),
                        conditions=rule_data.get("conditions", {}),
                        actions=rule_data.get("actions", {}),
                        priority=rule_data.get("priority", 0),
                        enabled=rule_data.get("enabled", True),
                        metadata=rule_data.get("metadata", {}),
                        created_at=datetime.fromisoformat(rule_data["created_at"]),
                        updated_at=datetime.fromisoformat(rule_data["updated_at"])
                    )
                    self.integration_rules[rule.id] = rule
            
            logger.info("Integration data imported successfully")
            
        except Exception as e:
            logger.error(f"Error importing integration data: {e}")
            raise
