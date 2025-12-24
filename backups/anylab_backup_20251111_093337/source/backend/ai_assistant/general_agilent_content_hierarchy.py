"""
General Agilent Content Hierarchy

This module provides content hierarchy management for General Agilent Products,
including product categorization, content organization, and hierarchical navigation.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from django.utils import timezone as django_timezone
from django.core.cache import cache

logger = logging.getLogger(__name__)


class ProductCategory(Enum):
    """Product category enumeration"""
    ANALYTICAL_INSTRUMENTS = "analytical_instruments"
    LIFE_SCIENCES = "life_sciences"
    DIAGNOSTICS = "diagnostics"
    APPLIED_MARKETS = "applied_markets"
    SOFTWARE = "software"
    SERVICES = "services"
    CONSUMABLES = "consumables"
    SUPPORT = "support"


class ContentType(Enum):
    """Content type enumeration"""
    PRODUCT_INFO = "product_info"
    TECHNICAL_SPEC = "technical_spec"
    USER_GUIDE = "user_guide"
    INSTALLATION_GUIDE = "installation_guide"
    MAINTENANCE_GUIDE = "maintenance_guide"
    TROUBLESHOOTING = "troubleshooting"
    APPLICATION_NOTE = "application_note"
    WHITE_PAPER = "white_paper"
    CASE_STUDY = "case_study"
    WEBINAR = "webinar"
    VIDEO_TUTORIAL = "video_tutorial"
    FAQ = "faq"
    NEWS = "news"
    ANNOUNCEMENT = "announcement"


class ContentPriority(Enum):
    """Content priority enumeration"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class ContentStatus(Enum):
    """Content status enumeration"""
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


@dataclass
class ProductNode:
    """Product node structure"""
    id: str
    name: str
    category: ProductCategory
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)
    content_items: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: django_timezone.now())
    updated_at: datetime = field(default_factory=lambda: django_timezone.now())


@dataclass
class ContentItem:
    """Content item structure"""
    id: str
    title: str
    content_type: ContentType
    product_id: str
    priority: ContentPriority
    status: ContentStatus
    content: str
    summary: str
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: django_timezone.now())
    updated_at: datetime = field(default_factory=lambda: django_timezone.now())


@dataclass
class HierarchyLevel:
    """Hierarchy level structure"""
    level: int
    name: str
    description: str
    max_depth: int
    required_fields: List[str] = field(default_factory=list)
    optional_fields: List[str] = field(default_factory=list)


class GeneralAgilentContentHierarchy:
    """General Agilent Content Hierarchy System"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize content hierarchy system"""
        self.config = config or {}
        self.hierarchy_enabled = self.config.get('hierarchy_enabled', True)
        self.auto_categorization = self.config.get('auto_categorization', True)
        self.content_validation = self.config.get('content_validation', True)
        self.cache_enabled = self.config.get('cache_enabled', True)
        self.max_depth = self.config.get('max_depth', 5)
        
        # Initialize components
        self.product_nodes = {}
        self.content_items = {}
        self.hierarchy_levels = {}
        self.cache = cache if self.cache_enabled else None
        
        # Initialize hierarchy
        self._initialize_hierarchy()
        
        logger.info("General Agilent Content Hierarchy initialized")
    
    def _initialize_hierarchy(self):
        """Initialize content hierarchy"""
        try:
            # Define hierarchy levels
            self.hierarchy_levels = {
                1: HierarchyLevel(
                    level=1,
                    name="Product Category",
                    description="Top-level product categories",
                    max_depth=1,
                    required_fields=["name", "category"],
                    optional_fields=["description", "icon"]
                ),
                2: HierarchyLevel(
                    level=2,
                    name="Product Family",
                    description="Product families within categories",
                    max_depth=2,
                    required_fields=["name", "family_type"],
                    optional_fields=["description", "specifications"]
                ),
                3: HierarchyLevel(
                    level=3,
                    name="Product Series",
                    description="Product series within families",
                    max_depth=3,
                    required_fields=["name", "series_type"],
                    optional_fields=["description", "model_range"]
                ),
                4: HierarchyLevel(
                    level=4,
                    name="Product Model",
                    description="Specific product models",
                    max_depth=4,
                    required_fields=["name", "model_number"],
                    optional_fields=["description", "specifications", "pricing"]
                ),
                5: HierarchyLevel(
                    level=5,
                    name="Product Variant",
                    description="Product variants and configurations",
                    max_depth=5,
                    required_fields=["name", "variant_type"],
                    optional_fields=["description", "configuration_options"]
                )
            }
            
            # Create root categories
            self._create_root_categories()
            
            logger.info("Content hierarchy initialized")
            
        except Exception as e:
            logger.error(f"Error initializing hierarchy: {e}")
            raise
    
    def _create_root_categories(self):
        """Create root product categories"""
        try:
            categories = [
                ("analytical_instruments", "Analytical Instruments", ProductCategory.ANALYTICAL_INSTRUMENTS),
                ("life_sciences", "Life Sciences", ProductCategory.LIFE_SCIENCES),
                ("diagnostics", "Diagnostics", ProductCategory.DIAGNOSTICS),
                ("applied_markets", "Applied Markets", ProductCategory.APPLIED_MARKETS),
                ("software", "Software", ProductCategory.SOFTWARE),
                ("services", "Services", ProductCategory.SERVICES),
                ("consumables", "Consumables", ProductCategory.CONSUMABLES),
                ("support", "Support", ProductCategory.SUPPORT)
            ]
            
            for category_id, name, category in categories:
                node = ProductNode(
                    id=category_id,
                    name=name,
                    category=category,
                    metadata={
                        "level": 1,
                        "description": f"Root category for {name}",
                        "icon": f"category_{category_id}",
                        "sort_order": len(self.product_nodes)
                    }
                )
                self.product_nodes[category_id] = node
            
            logger.info(f"Created {len(categories)} root categories")
            
        except Exception as e:
            logger.error(f"Error creating root categories: {e}")
            raise
    
    def add_product_node(self, node_id: str, name: str, category: ProductCategory,
                        parent_id: Optional[str] = None, metadata: Dict[str, Any] = None) -> ProductNode:
        """Add a product node to the hierarchy"""
        try:
            # Validate parent
            if parent_id and parent_id not in self.product_nodes:
                raise ValueError(f"Parent node {parent_id} not found")
            
            # Check depth
            if parent_id:
                parent_level = self.product_nodes[parent_id].metadata.get("level", 1)
                if parent_level >= self.max_depth:
                    raise ValueError(f"Maximum hierarchy depth ({self.max_depth}) exceeded")
            
            # Create node
            node = ProductNode(
                id=node_id,
                name=name,
                category=category,
                parent_id=parent_id,
                metadata=metadata or {}
            )
            
            # Set level
            if parent_id:
                node.metadata["level"] = self.product_nodes[parent_id].metadata.get("level", 1) + 1
            else:
                node.metadata["level"] = 1
            
            # Add to hierarchy
            self.product_nodes[node_id] = node
            
            # Update parent
            if parent_id:
                self.product_nodes[parent_id].children.append(node_id)
            
            logger.info(f"Added product node: {node_id}")
            return node
            
        except Exception as e:
            logger.error(f"Error adding product node: {e}")
            raise
    
    def get_product_node(self, node_id: str) -> Optional[ProductNode]:
        """Get a product node by ID"""
        return self.product_nodes.get(node_id)
    
    def get_product_children(self, node_id: str) -> List[ProductNode]:
        """Get children of a product node"""
        try:
            node = self.product_nodes.get(node_id)
            if not node:
                return []
            
            children = []
            for child_id in node.children:
                child = self.product_nodes.get(child_id)
                if child:
                    children.append(child)
            
            return children
            
        except Exception as e:
            logger.error(f"Error getting product children: {e}")
            return []
    
    def get_product_ancestors(self, node_id: str) -> List[ProductNode]:
        """Get ancestors of a product node"""
        try:
            ancestors = []
            current_id = node_id
            
            while current_id:
                node = self.product_nodes.get(current_id)
                if not node or not node.parent_id:
                    break
                
                parent = self.product_nodes.get(node.parent_id)
                if parent:
                    ancestors.append(parent)
                    current_id = parent.id
                else:
                    break
            
            return ancestors
            
        except Exception as e:
            logger.error(f"Error getting product ancestors: {e}")
            return []
    
    def get_product_descendants(self, node_id: str) -> List[ProductNode]:
        """Get all descendants of a product node"""
        try:
            descendants = []
            node = self.product_nodes.get(node_id)
            if not node:
                return descendants
            
            # Recursively collect descendants
            def collect_descendants(current_node):
                for child_id in current_node.children:
                    child = self.product_nodes.get(child_id)
                    if child:
                        descendants.append(child)
                        collect_descendants(child)
            
            collect_descendants(node)
            return descendants
            
        except Exception as e:
            logger.error(f"Error getting product descendants: {e}")
            return []
    
    def add_content_item(self, item_id: str, title: str, content_type: ContentType,
                        product_id: str, priority: ContentPriority = ContentPriority.MEDIUM,
                        status: ContentStatus = ContentStatus.DRAFT, content: str = "",
                        summary: str = "", tags: List[str] = None,
                        metadata: Dict[str, Any] = None) -> ContentItem:
        """Add a content item"""
        try:
            # Validate product exists
            if product_id not in self.product_nodes:
                raise ValueError(f"Product node {product_id} not found")
            
            # Create content item
            item = ContentItem(
                id=item_id,
                title=title,
                content_type=content_type,
                product_id=product_id,
                priority=priority,
                status=status,
                content=content,
                summary=summary,
                tags=tags or [],
                metadata=metadata or {}
            )
            
            # Add to content items
            self.content_items[item_id] = item
            
            # Add to product node
            self.product_nodes[product_id].content_items.append(item_id)
            
            logger.info(f"Added content item: {item_id}")
            return item
            
        except Exception as e:
            logger.error(f"Error adding content item: {e}")
            raise
    
    def get_content_item(self, item_id: str) -> Optional[ContentItem]:
        """Get a content item by ID"""
        return self.content_items.get(item_id)
    
    def get_content_by_product(self, product_id: str, content_type: ContentType = None,
                             status: ContentStatus = None) -> List[ContentItem]:
        """Get content items for a product"""
        try:
            items = []
            
            for item_id in self.product_nodes[product_id].content_items:
                item = self.content_items.get(item_id)
                if not item:
                    continue
                
                # Filter by content type
                if content_type and item.content_type != content_type:
                    continue
                
                # Filter by status
                if status and item.status != status:
                    continue
                
                items.append(item)
            
            return items
            
        except Exception as e:
            logger.error(f"Error getting content by product: {e}")
            return []
    
    def get_content_by_category(self, category: ProductCategory, content_type: ContentType = None,
                               status: ContentStatus = None) -> List[ContentItem]:
        """Get content items for a category"""
        try:
            items = []
            
            # Get all products in category
            for node in self.product_nodes.values():
                if node.category == category:
                    # Get content for this product
                    product_items = self.get_content_by_product(node.id, content_type, status)
                    items.extend(product_items)
            
            return items
            
        except Exception as e:
            logger.error(f"Error getting content by category: {e}")
            return []
    
    def search_content(self, query: str, category: ProductCategory = None,
                      content_type: ContentType = None, status: ContentStatus = None,
                      tags: List[str] = None) -> List[ContentItem]:
        """Search content items"""
        try:
            results = []
            query_lower = query.lower()
            
            for item in self.content_items.values():
                # Filter by category
                if category:
                    product = self.product_nodes.get(item.product_id)
                    if not product or product.category != category:
                        continue
                
                # Filter by content type
                if content_type and item.content_type != content_type:
                    continue
                
                # Filter by status
                if status and item.status != status:
                    continue
                
                # Filter by tags
                if tags:
                    if not any(tag in item.tags for tag in tags):
                        continue
                
                # Search in title, content, and summary
                if (query_lower in item.title.lower() or
                    query_lower in item.content.lower() or
                    query_lower in item.summary.lower()):
                    results.append(item)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching content: {e}")
            return []
    
    def get_hierarchy_breadcrumb(self, node_id: str) -> List[ProductNode]:
        """Get breadcrumb trail for a node"""
        try:
            breadcrumb = []
            current_id = node_id
            
            while current_id:
                node = self.product_nodes.get(current_id)
                if not node:
                    break
                
                breadcrumb.insert(0, node)
                current_id = node.parent_id
            
            return breadcrumb
            
        except Exception as e:
            logger.error(f"Error getting hierarchy breadcrumb: {e}")
            return []
    
    def get_hierarchy_tree(self, root_id: str = None) -> Dict[str, Any]:
        """Get hierarchy tree structure"""
        try:
            if root_id:
                root = self.product_nodes.get(root_id)
                if not root:
                    return {}
                return self._build_tree_structure(root)
            else:
                # Build tree for all root nodes
                tree = {}
                for node in self.product_nodes.values():
                    if not node.parent_id:  # Root node
                        tree[node.id] = self._build_tree_structure(node)
                return tree
            
        except Exception as e:
            logger.error(f"Error getting hierarchy tree: {e}")
            return {}
    
    def _build_tree_structure(self, node: ProductNode) -> Dict[str, Any]:
        """Build tree structure for a node"""
        try:
            tree = {
                "id": node.id,
                "name": node.name,
                "category": node.category.value,
                "level": node.metadata.get("level", 1),
                "metadata": node.metadata,
                "content_count": len(node.content_items),
                "children": []
            }
            
            # Add children
            for child_id in node.children:
                child = self.product_nodes.get(child_id)
                if child:
                    child_tree = self._build_tree_structure(child)
                    tree["children"].append(child_tree)
            
            return tree
            
        except Exception as e:
            logger.error(f"Error building tree structure: {e}")
            return {}
    
    def validate_hierarchy(self) -> Dict[str, Any]:
        """Validate hierarchy integrity"""
        try:
            validation_results = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "statistics": {
                    "total_nodes": len(self.product_nodes),
                    "total_content": len(self.content_items),
                    "orphaned_content": 0,
                    "circular_references": 0,
                    "depth_violations": 0
                }
            }
            
            # Check for orphaned content
            for item in self.content_items.values():
                if item.product_id not in self.product_nodes:
                    validation_results["errors"].append(f"Content item {item.id} references non-existent product {item.product_id}")
                    validation_results["statistics"]["orphaned_content"] += 1
            
            # Check for circular references
            for node_id, node in self.product_nodes.items():
                if self._has_circular_reference(node_id):
                    validation_results["errors"].append(f"Circular reference detected for node {node_id}")
                    validation_results["statistics"]["circular_references"] += 1
            
            # Check depth violations
            for node in self.product_nodes.values():
                level = node.metadata.get("level", 1)
                if level > self.max_depth:
                    validation_results["warnings"].append(f"Node {node.id} exceeds maximum depth")
                    validation_results["statistics"]["depth_violations"] += 1
            
            # Set valid flag
            if validation_results["errors"]:
                validation_results["valid"] = False
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating hierarchy: {e}")
            return {"valid": False, "errors": [str(e)], "warnings": [], "statistics": {}}
    
    def _has_circular_reference(self, node_id: str, visited: set = None) -> bool:
        """Check for circular references"""
        try:
            if visited is None:
                visited = set()
            
            if node_id in visited:
                return True
            
            visited.add(node_id)
            node = self.product_nodes.get(node_id)
            if not node:
                return False
            
            for child_id in node.children:
                if self._has_circular_reference(child_id, visited.copy()):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking circular reference: {e}")
            return False
    
    def get_hierarchy_statistics(self) -> Dict[str, Any]:
        """Get hierarchy statistics"""
        try:
            stats = {
                "total_nodes": len(self.product_nodes),
                "total_content": len(self.content_items),
                "nodes_by_level": {},
                "content_by_type": {},
                "content_by_status": {},
                "content_by_priority": {},
                "nodes_by_category": {},
                "average_content_per_node": 0,
                "max_depth": 0,
                "hierarchy_enabled": self.hierarchy_enabled,
                "auto_categorization": self.auto_categorization,
                "content_validation": self.content_validation
            }
            
            # Count nodes by level
            for node in self.product_nodes.values():
                level = node.metadata.get("level", 1)
                stats["nodes_by_level"][level] = stats["nodes_by_level"].get(level, 0) + 1
                stats["max_depth"] = max(stats["max_depth"], level)
            
            # Count content by type
            for item in self.content_items.values():
                content_type = item.content_type.value
                stats["content_by_type"][content_type] = stats["content_by_type"].get(content_type, 0) + 1
                
                status = item.status.value
                stats["content_by_status"][status] = stats["content_by_status"].get(status, 0) + 1
                
                priority = item.priority.value
                stats["content_by_priority"][priority] = stats["content_by_priority"].get(priority, 0) + 1
            
            # Count nodes by category
            for node in self.product_nodes.values():
                category = node.category.value
                stats["nodes_by_category"][category] = stats["nodes_by_category"].get(category, 0) + 1
            
            # Calculate average content per node
            if stats["total_nodes"] > 0:
                stats["average_content_per_node"] = stats["total_content"] / stats["total_nodes"]
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting hierarchy statistics: {e}")
            return {}
    
    def export_hierarchy(self) -> Dict[str, Any]:
        """Export hierarchy data"""
        try:
            return {
                "nodes": [
                    {
                        "id": node.id,
                        "name": node.name,
                        "category": node.category.value,
                        "parent_id": node.parent_id,
                        "children": node.children,
                        "content_items": node.content_items,
                        "metadata": node.metadata,
                        "created_at": node.created_at.isoformat(),
                        "updated_at": node.updated_at.isoformat()
                    }
                    for node in self.product_nodes.values()
                ],
                "content": [
                    {
                        "id": item.id,
                        "title": item.title,
                        "content_type": item.content_type.value,
                        "product_id": item.product_id,
                        "priority": item.priority.value,
                        "status": item.status.value,
                        "content": item.content,
                        "summary": item.summary,
                        "tags": item.tags,
                        "metadata": item.metadata,
                        "created_at": item.created_at.isoformat(),
                        "updated_at": item.updated_at.isoformat()
                    }
                    for item in self.content_items.values()
                ],
                "hierarchy_levels": [
                    {
                        "level": level.level,
                        "name": level.name,
                        "description": level.description,
                        "max_depth": level.max_depth,
                        "required_fields": level.required_fields,
                        "optional_fields": level.optional_fields
                    }
                    for level in self.hierarchy_levels.values()
                ]
            }
            
        except Exception as e:
            logger.error(f"Error exporting hierarchy: {e}")
            return {}
    
    def import_hierarchy(self, data: Dict[str, Any]):
        """Import hierarchy data"""
        try:
            # Import nodes
            if "nodes" in data:
                for node_data in data["nodes"]:
                    node = ProductNode(
                        id=node_data["id"],
                        name=node_data["name"],
                        category=ProductCategory(node_data["category"]),
                        parent_id=node_data.get("parent_id"),
                        children=node_data.get("children", []),
                        content_items=node_data.get("content_items", []),
                        metadata=node_data.get("metadata", {}),
                        created_at=datetime.fromisoformat(node_data["created_at"]),
                        updated_at=datetime.fromisoformat(node_data["updated_at"])
                    )
                    self.product_nodes[node.id] = node
            
            # Import content
            if "content" in data:
                for content_data in data["content"]:
                    item = ContentItem(
                        id=content_data["id"],
                        title=content_data["title"],
                        content_type=ContentType(content_data["content_type"]),
                        product_id=content_data["product_id"],
                        priority=ContentPriority(content_data["priority"]),
                        status=ContentStatus(content_data["status"]),
                        content=content_data["content"],
                        summary=content_data["summary"],
                        tags=content_data.get("tags", []),
                        metadata=content_data.get("metadata", {}),
                        created_at=datetime.fromisoformat(content_data["created_at"]),
                        updated_at=datetime.fromisoformat(content_data["updated_at"])
                    )
                    self.content_items[item.id] = item
            
            # Import hierarchy levels
            if "hierarchy_levels" in data:
                for level_data in data["hierarchy_levels"]:
                    level = HierarchyLevel(
                        level=level_data["level"],
                        name=level_data["name"],
                        description=level_data["description"],
                        max_depth=level_data["max_depth"],
                        required_fields=level_data.get("required_fields", []),
                        optional_fields=level_data.get("optional_fields", [])
                    )
                    self.hierarchy_levels[level.level] = level
            
            logger.info("Hierarchy data imported successfully")
            
        except Exception as e:
            logger.error(f"Error importing hierarchy: {e}")
            raise
