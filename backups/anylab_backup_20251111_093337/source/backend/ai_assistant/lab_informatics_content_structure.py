"""
Lab Informatics Content Structure

This module provides specialized content structure for Lab Informatics products,
including OpenLab, ChemStation, MassHunter, and other informatics solutions.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from django.utils import timezone as django_timezone
from django.core.cache import cache

logger = logging.getLogger(__name__)


class LabInformaticsProduct(Enum):
    """Lab Informatics product enumeration"""
    OPENLAB = "openlab"
    CHEMSTATION = "chemstation"
    MASSHUNTER = "masshunter"
    AGILENT_1290 = "agilent_1290"
    AGILENT_1260 = "agilent_1260"
    AGILENT_1220 = "agilent_1220"
    AGILENT_1100 = "agilent_1100"
    AGILENT_1200 = "agilent_1200"
    AGILENT_6000 = "agilent_6000"
    AGILENT_7000 = "agilent_7000"
    AGILENT_8000 = "agilent_8000"
    AGILENT_9000 = "agilent_9000"


class InformaticsContentType(Enum):
    """Informatics content type enumeration"""
    METHOD_DEVELOPMENT = "method_development"
    DATA_ANALYSIS = "data_analysis"
    SYSTEM_ADMINISTRATION = "system_administration"
    TROUBLESHOOTING = "troubleshooting"
    MAINTENANCE = "maintenance"
    CALIBRATION = "calibration"
    VALIDATION = "validation"
    COMPLIANCE = "compliance"
    TRAINING = "training"
    BEST_PRACTICES = "best_practices"
    WORKFLOW = "workflow"
    INTEGRATION = "integration"


class ContentComplexity(Enum):
    """Content complexity enumeration"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class InformaticsNode:
    """Informatics node structure"""
    id: str
    name: str
    product: LabInformaticsProduct
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)
    content_items: List[str] = field(default_factory=list)
    complexity: ContentComplexity = ContentComplexity.INTERMEDIATE
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: django_timezone.now())
    updated_at: datetime = field(default_factory=lambda: django_timezone.now())


@dataclass
class InformaticsContent:
    """Informatics content structure"""
    id: str
    title: str
    content_type: InformaticsContentType
    product_id: str
    complexity: ContentComplexity
    content: str
    summary: str
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: django_timezone.now())
    updated_at: datetime = field(default_factory=lambda: django_timezone.now())


class LabInformaticsContentStructure:
    """Lab Informatics Content Structure System"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize content structure system"""
        self.config = config or {}
        self.structure_enabled = self.config.get('structure_enabled', True)
        self.auto_categorization = self.config.get('auto_categorization', True)
        self.content_validation = self.config.get('content_validation', True)
        self.cache_enabled = self.config.get('cache_enabled', True)
        
        # Initialize components
        self.informatics_nodes = {}
        self.informatics_content = {}
        self.cache = cache if self.cache_enabled else None
        
        # Initialize structure
        self._initialize_structure()
        
        logger.info("Lab Informatics Content Structure initialized")
    
    def _initialize_structure(self):
        """Initialize content structure"""
        try:
            # Create product nodes
            self._create_product_nodes()
            
            logger.info("Content structure initialized")
            
        except Exception as e:
            logger.error(f"Error initializing structure: {e}")
            raise
    
    def _create_product_nodes(self):
        """Create product nodes"""
        try:
            products = [
                ("openlab", "OpenLab", LabInformaticsProduct.OPENLAB),
                ("chemstation", "ChemStation", LabInformaticsProduct.CHEMSTATION),
                ("masshunter", "MassHunter", LabInformaticsProduct.MASSHUNTER),
                ("agilent_1290", "Agilent 1290", LabInformaticsProduct.AGILENT_1290),
                ("agilent_1260", "Agilent 1260", LabInformaticsProduct.AGILENT_1260),
                ("agilent_1220", "Agilent 1220", LabInformaticsProduct.AGILENT_1220),
                ("agilent_1100", "Agilent 1100", LabInformaticsProduct.AGILENT_1100),
                ("agilent_1200", "Agilent 1200", LabInformaticsProduct.AGILENT_1200),
                ("agilent_6000", "Agilent 6000", LabInformaticsProduct.AGILENT_6000),
                ("agilent_7000", "Agilent 7000", LabInformaticsProduct.AGILENT_7000),
                ("agilent_8000", "Agilent 8000", LabInformaticsProduct.AGILENT_8000),
                ("agilent_9000", "Agilent 9000", LabInformaticsProduct.AGILENT_9000)
            ]
            
            for product_id, name, product in products:
                node = InformaticsNode(
                    id=product_id,
                    name=name,
                    product=product,
                    metadata={
                        "level": 1,
                        "description": f"Root node for {name}",
                        "icon": f"product_{product_id}",
                        "sort_order": len(self.informatics_nodes)
                    }
                )
                self.informatics_nodes[product_id] = node
            
            logger.info(f"Created {len(products)} product nodes")
            
        except Exception as e:
            logger.error(f"Error creating product nodes: {e}")
            raise
    
    def add_informatics_node(self, node_id: str, name: str, product: LabInformaticsProduct,
                            parent_id: Optional[str] = None, complexity: ContentComplexity = ContentComplexity.INTERMEDIATE,
                            metadata: Dict[str, Any] = None) -> InformaticsNode:
        """Add an informatics node"""
        try:
            # Validate parent
            if parent_id and parent_id not in self.informatics_nodes:
                raise ValueError(f"Parent node {parent_id} not found")
            
            # Create node
            node = InformaticsNode(
                id=node_id,
                name=name,
                product=product,
                parent_id=parent_id,
                complexity=complexity,
                metadata=metadata or {}
            )
            
            # Add to structure
            self.informatics_nodes[node_id] = node
            
            # Update parent
            if parent_id:
                self.informatics_nodes[parent_id].children.append(node_id)
            
            logger.info(f"Added informatics node: {node_id}")
            return node
            
        except Exception as e:
            logger.error(f"Error adding informatics node: {e}")
            raise
    
    def add_informatics_content(self, content_id: str, title: str, content_type: InformaticsContentType,
                               product_id: str, complexity: ContentComplexity = ContentComplexity.INTERMEDIATE,
                               content: str = "", summary: str = "", tags: List[str] = None,
                               metadata: Dict[str, Any] = None) -> InformaticsContent:
        """Add informatics content"""
        try:
            # Validate product exists
            if product_id not in self.informatics_nodes:
                raise ValueError(f"Product node {product_id} not found")
            
            # Create content
            item = InformaticsContent(
                id=content_id,
                title=title,
                content_type=content_type,
                product_id=product_id,
                complexity=complexity,
                content=content,
                summary=summary,
                tags=tags or [],
                metadata=metadata or {}
            )
            
            # Add to content
            self.informatics_content[content_id] = item
            
            # Add to product node
            self.informatics_nodes[product_id].content_items.append(content_id)
            
            logger.info(f"Added informatics content: {content_id}")
            return item
            
        except Exception as e:
            logger.error(f"Error adding informatics content: {e}")
            raise
    
    def get_informatics_node(self, node_id: str) -> Optional[InformaticsNode]:
        """Get an informatics node by ID"""
        return self.informatics_nodes.get(node_id)
    
    def get_informatics_content(self, content_id: str) -> Optional[InformaticsContent]:
        """Get informatics content by ID"""
        return self.informatics_content.get(content_id)
    
    def get_content_by_product(self, product_id: str, content_type: InformaticsContentType = None,
                             complexity: ContentComplexity = None) -> List[InformaticsContent]:
        """Get content for a product"""
        try:
            items = []
            
            for content_id in self.informatics_nodes[product_id].content_items:
                item = self.informatics_content.get(content_id)
                if not item:
                    continue
                
                # Filter by content type
                if content_type and item.content_type != content_type:
                    continue
                
                # Filter by complexity
                if complexity and item.complexity != complexity:
                    continue
                
                items.append(item)
            
            return items
            
        except Exception as e:
            logger.error(f"Error getting content by product: {e}")
            return []
    
    def search_informatics_content(self, query: str, product: LabInformaticsProduct = None,
                                  content_type: InformaticsContentType = None,
                                  complexity: ContentComplexity = None,
                                  tags: List[str] = None) -> List[InformaticsContent]:
        """Search informatics content"""
        try:
            results = []
            query_lower = query.lower()
            
            for item in self.informatics_content.values():
                # Filter by product
                if product:
                    node = self.informatics_nodes.get(item.product_id)
                    if not node or node.product != product:
                        continue
                
                # Filter by content type
                if content_type and item.content_type != content_type:
                    continue
                
                # Filter by complexity
                if complexity and item.complexity != complexity:
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
            logger.error(f"Error searching informatics content: {e}")
            return []
    
    def get_structure_statistics(self) -> Dict[str, Any]:
        """Get structure statistics"""
        try:
            stats = {
                "total_nodes": len(self.informatics_nodes),
                "total_content": len(self.informatics_content),
                "nodes_by_product": {},
                "content_by_type": {},
                "content_by_complexity": {},
                "average_content_per_node": 0,
                "structure_enabled": self.structure_enabled,
                "auto_categorization": self.auto_categorization,
                "content_validation": self.content_validation
            }
            
            # Count nodes by product
            for node in self.informatics_nodes.values():
                product = node.product.value
                stats["nodes_by_product"][product] = stats["nodes_by_product"].get(product, 0) + 1
            
            # Count content by type
            for item in self.informatics_content.values():
                content_type = item.content_type.value
                stats["content_by_type"][content_type] = stats["content_by_type"].get(content_type, 0) + 1
                
                complexity = item.complexity.value
                stats["content_by_complexity"][complexity] = stats["content_by_complexity"].get(complexity, 0) + 1
            
            # Calculate average content per node
            if stats["total_nodes"] > 0:
                stats["average_content_per_node"] = stats["total_content"] / stats["total_nodes"]
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting structure statistics: {e}")
            return {}
    
    def export_structure(self) -> Dict[str, Any]:
        """Export structure data"""
        try:
            return {
                "nodes": [
                    {
                        "id": node.id,
                        "name": node.name,
                        "product": node.product.value,
                        "parent_id": node.parent_id,
                        "children": node.children,
                        "content_items": node.content_items,
                        "complexity": node.complexity.value,
                        "metadata": node.metadata,
                        "created_at": node.created_at.isoformat(),
                        "updated_at": node.updated_at.isoformat()
                    }
                    for node in self.informatics_nodes.values()
                ],
                "content": [
                    {
                        "id": item.id,
                        "title": item.title,
                        "content_type": item.content_type.value,
                        "product_id": item.product_id,
                        "complexity": item.complexity.value,
                        "content": item.content,
                        "summary": item.summary,
                        "tags": item.tags,
                        "metadata": item.metadata,
                        "created_at": item.created_at.isoformat(),
                        "updated_at": item.updated_at.isoformat()
                    }
                    for item in self.informatics_content.values()
                ]
            }
            
        except Exception as e:
            logger.error(f"Error exporting structure: {e}")
            return {}
    
    def import_structure(self, data: Dict[str, Any]):
        """Import structure data"""
        try:
            # Import nodes
            if "nodes" in data:
                for node_data in data["nodes"]:
                    node = InformaticsNode(
                        id=node_data["id"],
                        name=node_data["name"],
                        product=LabInformaticsProduct(node_data["product"]),
                        parent_id=node_data.get("parent_id"),
                        children=node_data.get("children", []),
                        content_items=node_data.get("content_items", []),
                        complexity=ContentComplexity(node_data["complexity"]),
                        metadata=node_data.get("metadata", {}),
                        created_at=datetime.fromisoformat(node_data["created_at"]),
                        updated_at=datetime.fromisoformat(node_data["updated_at"])
                    )
                    self.informatics_nodes[node.id] = node
            
            # Import content
            if "content" in data:
                for content_data in data["content"]:
                    item = InformaticsContent(
                        id=content_data["id"],
                        title=content_data["title"],
                        content_type=InformaticsContentType(content_data["content_type"]),
                        product_id=content_data["product_id"],
                        complexity=ContentComplexity(content_data["complexity"]),
                        content=content_data["content"],
                        summary=content_data["summary"],
                        tags=content_data.get("tags", []),
                        metadata=content_data.get("metadata", {}),
                        created_at=datetime.fromisoformat(content_data["created_at"]),
                        updated_at=datetime.fromisoformat(content_data["updated_at"])
                    )
                    self.informatics_content[item.id] = item
            
            logger.info("Structure data imported successfully")
            
        except Exception as e:
            logger.error(f"Error importing structure: {e}")
            raise
