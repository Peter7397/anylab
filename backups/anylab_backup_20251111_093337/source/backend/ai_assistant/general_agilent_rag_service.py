"""
General Agilent RAG Service

This module provides a specialized RAG service for General Agilent Products
including product documentation, specifications, and support materials.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from django.utils import timezone as django_timezone
from django.core.cache import cache

logger = logging.getLogger(__name__)


class AgilentProductCategory(Enum):
    """Agilent product category enumeration"""
    ANALYTICAL_INSTRUMENTS = "analytical_instruments"
    LIFE_SCIENCES = "life_sciences"
    DIAGNOSTICS = "diagnostics"
    ELECTRONIC_MEASUREMENT = "electronic_measurement"
    CHEMICAL_ANALYSIS = "chemical_analysis"
    MATERIALS_SCIENCE = "materials_science"
    FOOD_SAFETY = "food_safety"
    ENVIRONMENTAL = "environmental"
    PHARMACEUTICAL = "pharmaceutical"
    PETROCHEMICAL = "petrochemical"
    SEMICONDUCTOR = "semiconductor"
    AUTOMOTIVE = "automotive"
    AEROSPACE = "aerospace"
    TELECOMMUNICATIONS = "telecommunications"
    RESEARCH = "research"


class DocumentType(Enum):
    """Document type enumeration"""
    USER_MANUAL = "user_manual"
    TECHNICAL_SPECIFICATION = "technical_specification"
    APPLICATION_NOTE = "application_note"
    WHITE_PAPER = "white_paper"
    TROUBLESHOOTING_GUIDE = "troubleshooting_guide"
    INSTALLATION_GUIDE = "installation_guide"
    MAINTENANCE_GUIDE = "maintenance_guide"
    CALIBRATION_GUIDE = "calibration_guide"
    SAFETY_DATASHEET = "safety_datasheet"
    CERTIFICATE_OF_ANALYSIS = "certificate_of_analysis"
    SOFTWARE_DOCUMENTATION = "software_documentation"
    API_DOCUMENTATION = "api_documentation"
    TRAINING_MATERIAL = "training_material"
    WEBINAR = "webinar"
    VIDEO_TUTORIAL = "video_tutorial"
    FAQ = "faq"
    RELEASE_NOTES = "release_notes"
    COMPATIBILITY_MATRIX = "compatibility_matrix"


@dataclass
class AgilentProduct:
    """Agilent product structure"""
    id: str
    name: str
    model_number: str
    category: AgilentProductCategory
    description: str
    specifications: Dict[str, Any] = field(default_factory=dict)
    features: List[str] = field(default_factory=list)
    applications: List[str] = field(default_factory=list)
    documents: List[str] = field(default_factory=list)
    support_resources: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: django_timezone.now())
    updated_at: datetime = field(default_factory=lambda: django_timezone.now())


@dataclass
class AgilentDocument:
    """Agilent document structure"""
    id: str
    title: str
    document_type: DocumentType
    product_id: Optional[str] = None
    category: Optional[AgilentProductCategory] = None
    content: str = ""
    summary: str = ""
    keywords: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    file_path: Optional[str] = None
    url: Optional[str] = None
    language: str = "en"
    version: str = "1.0"
    last_updated: datetime = field(default_factory=lambda: django_timezone.now())
    created_at: datetime = field(default_factory=lambda: django_timezone.now())


@dataclass
class AgilentSearchResult:
    """Agilent search result structure"""
    document_id: str
    title: str
    content: str
    relevance_score: float
    document_type: DocumentType
    product_id: Optional[str] = None
    category: Optional[AgilentProductCategory] = None
    highlights: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class GeneralAgilentRAGService:
    """General Agilent RAG Service"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize General Agilent RAG Service"""
        self.config = config or {}
        self.service_enabled = self.config.get('service_enabled', True)
        self.cache_enabled = self.config.get('cache_enabled', True)
        self.max_results = self.config.get('max_results', 10)
        self.similarity_threshold = self.config.get('similarity_threshold', 0.7)
        
        # Initialize components
        self.products = {}
        self.documents = {}
        self.search_index = {}
        self.cache = cache if self.cache_enabled else None
        
        # Initialize service
        self._initialize_service()
        
        logger.info("General Agilent RAG Service initialized")
    
    def _initialize_service(self):
        """Initialize service components"""
        try:
            # Initialize product catalog
            self._initialize_product_catalog()
            
            # Initialize document collection
            self._initialize_document_collection()
            
            # Initialize search index
            self._initialize_search_index()
            
            logger.info("Service components initialized")
            
        except Exception as e:
            logger.error(f"Error initializing service: {e}")
            raise
    
    def _initialize_product_catalog(self):
        """Initialize Agilent product catalog"""
        try:
            # Sample Agilent products
            products = [
                AgilentProduct(
                    id="agilent_1260_infinity_ii",
                    name="1260 Infinity II LC System",
                    model_number="1260 Infinity II",
                    category=AgilentProductCategory.ANALYTICAL_INSTRUMENTS,
                    description="High-performance liquid chromatography system for analytical and preparative applications",
                    specifications={
                        "pressure_limit": "600 bar",
                        "flow_range": "0.001-5.0 mL/min",
                        "temperature_range": "4-85°C",
                        "detection": "UV-Vis, DAD, FLD, RID"
                    },
                    features=[
                        "High-pressure capability",
                        "Modular design",
                        "Advanced detection options",
                        "Intuitive software"
                    ],
                    applications=[
                        "Pharmaceutical analysis",
                        "Food safety testing",
                        "Environmental monitoring",
                        "Research applications"
                    ]
                ),
                AgilentProduct(
                    id="agilent_5977b_gc_ms",
                    name="5977B GC/MSD System",
                    model_number="5977B",
                    category=AgilentProductCategory.ANALYTICAL_INSTRUMENTS,
                    description="Gas chromatography-mass spectrometry system for trace analysis",
                    specifications={
                        "mass_range": "1.2-1050 m/z",
                        "scan_speed": "12,500 u/sec",
                        "sensitivity": "1 pg OFN",
                        "resolution": "Unit mass"
                    },
                    features=[
                        "High sensitivity",
                        "Fast scanning",
                        "Robust design",
                        "Easy maintenance"
                    ],
                    applications=[
                        "Environmental analysis",
                        "Food safety",
                        "Forensic analysis",
                        "Pharmaceutical testing"
                    ]
                ),
                AgilentProduct(
                    id="agilent_7900_icp_ms",
                    name="7900 ICP-MS System",
                    model_number="7900",
                    category=AgilentProductCategory.ANALYTICAL_INSTRUMENTS,
                    description="Inductively coupled plasma mass spectrometry for elemental analysis",
                    specifications={
                        "mass_range": "2-260 amu",
                        "sensitivity": "> 1 billion cps/ppm",
                        "resolution": "0.2-0.8 amu",
                        "detection_limits": "ppt level"
                    },
                    features=[
                        "Ultra-high sensitivity",
                        "Wide mass range",
                        "Low detection limits",
                        "Multi-element capability"
                    ],
                    applications=[
                        "Environmental monitoring",
                        "Food safety testing",
                        "Pharmaceutical analysis",
                        "Materials science"
                    ]
                )
            ]
            
            for product in products:
                self.products[product.id] = product
            
            logger.info(f"Initialized {len(products)} Agilent products")
            
        except Exception as e:
            logger.error(f"Error initializing product catalog: {e}")
    
    def _initialize_document_collection(self):
        """Initialize document collection"""
        try:
            # Sample Agilent documents
            documents = [
                AgilentDocument(
                    id="doc_1260_user_manual",
                    title="1260 Infinity II LC System User Manual",
                    document_type=DocumentType.USER_MANUAL,
                    product_id="agilent_1260_infinity_ii",
                    category=AgilentProductCategory.ANALYTICAL_INSTRUMENTS,
                    content="This manual provides comprehensive instructions for operating the 1260 Infinity II LC System. The system includes pump, autosampler, column oven, and detector modules. Key features include high-pressure capability up to 600 bar, flow range from 0.001 to 5.0 mL/min, and temperature control from 4 to 85°C.",
                    summary="Complete user manual for 1260 Infinity II LC System operation",
                    keywords=["LC", "HPLC", "chromatography", "pump", "autosampler", "detector"],
                    tags=["user_manual", "LC", "HPLC", "1260"]
                ),
                AgilentDocument(
                    id="doc_5977b_troubleshooting",
                    title="5977B GC/MSD Troubleshooting Guide",
                    document_type=DocumentType.TROUBLESHOOTING_GUIDE,
                    product_id="agilent_5977b_gc_ms",
                    category=AgilentProductCategory.ANALYTICAL_INSTRUMENTS,
                    content="This troubleshooting guide covers common issues with the 5977B GC/MSD system. Common problems include vacuum issues, mass calibration problems, and detector sensitivity issues. Solutions include checking vacuum pumps, recalibrating mass axis, and cleaning ion source.",
                    summary="Troubleshooting guide for 5977B GC/MSD system issues",
                    keywords=["GC/MS", "troubleshooting", "vacuum", "calibration", "sensitivity"],
                    tags=["troubleshooting", "GC/MS", "5977B"]
                ),
                AgilentDocument(
                    id="doc_7900_application_note",
                    title="7900 ICP-MS Environmental Analysis Application Note",
                    document_type=DocumentType.APPLICATION_NOTE,
                    product_id="agilent_7900_icp_ms",
                    category=AgilentProductCategory.ANALYTICAL_INSTRUMENTS,
                    content="This application note describes environmental analysis using the 7900 ICP-MS system. Methods include water analysis, soil analysis, and air particulate analysis. Detection limits are in the ppt range for most elements. Sample preparation techniques and method optimization are discussed.",
                    summary="Environmental analysis applications for 7900 ICP-MS",
                    keywords=["ICP-MS", "environmental", "water", "soil", "air", "trace analysis"],
                    tags=["application_note", "ICP-MS", "environmental", "7900"]
                )
            ]
            
            for document in documents:
                self.documents[document.id] = document
            
            logger.info(f"Initialized {len(documents)} Agilent documents")
            
        except Exception as e:
            logger.error(f"Error initializing document collection: {e}")
    
    def _initialize_search_index(self):
        """Initialize search index"""
        try:
            # Create search index from documents
            for doc_id, document in self.documents.items():
                # Index by keywords
                for keyword in document.keywords:
                    if keyword not in self.search_index:
                        self.search_index[keyword] = []
                    self.search_index[keyword].append(doc_id)
                
                # Index by tags
                for tag in document.tags:
                    if tag not in self.search_index:
                        self.search_index[tag] = []
                    self.search_index[tag].append(doc_id)
                
                # Index by product ID
                if document.product_id:
                    if document.product_id not in self.search_index:
                        self.search_index[document.product_id] = []
                    self.search_index[document.product_id].append(doc_id)
            
            logger.info("Search index initialized")
            
        except Exception as e:
            logger.error(f"Error initializing search index: {e}")
    
    def search_documents(self, query: str, filters: Dict[str, Any] = None) -> List[AgilentSearchResult]:
        """Search Agilent documents"""
        try:
            # Check cache first
            if self.cache_enabled:
                cache_key = f"agilent_search_{hash(query)}_{hash(str(filters))}"
                cached_result = self.cache.get(cache_key)
                if cached_result:
                    return cached_result
            
            # Perform search
            results = []
            query_lower = query.lower()
            
            for doc_id, document in self.documents.items():
                # Apply filters
                if filters:
                    if 'product_id' in filters and document.product_id != filters['product_id']:
                        continue
                    if 'category' in filters and document.category != filters['category']:
                        continue
                    if 'document_type' in filters and document.document_type != filters['document_type']:
                        continue
                
                # Calculate relevance score
                relevance_score = self._calculate_relevance_score(query_lower, document)
                
                if relevance_score >= self.similarity_threshold:
                    # Create search result
                    result = AgilentSearchResult(
                        document_id=doc_id,
                        title=document.title,
                        content=document.content,
                        relevance_score=relevance_score,
                        document_type=document.document_type,
                        product_id=document.product_id,
                        category=document.category,
                        highlights=self._generate_highlights(query_lower, document.content),
                        metadata={
                            'summary': document.summary,
                            'keywords': document.keywords,
                            'tags': document.tags,
                            'version': document.version,
                            'last_updated': document.last_updated.isoformat()
                        }
                    )
                    results.append(result)
            
            # Sort by relevance score
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # Limit results
            results = results[:self.max_results]
            
            # Cache results
            if self.cache_enabled:
                self.cache.set(cache_key, results, timeout=3600)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def _calculate_relevance_score(self, query: str, document: AgilentDocument) -> float:
        """Calculate relevance score for a document"""
        try:
            score = 0.0
            
            # Title match (highest weight)
            if query in document.title.lower():
                score += 0.4
            
            # Content match
            content_lower = document.content.lower()
            query_words = query.split()
            content_matches = sum(1 for word in query_words if word in content_lower)
            score += (content_matches / len(query_words)) * 0.3
            
            # Keyword match
            keyword_matches = sum(1 for keyword in document.keywords if keyword.lower() in query)
            if document.keywords:
                score += (keyword_matches / len(document.keywords)) * 0.2
            
            # Tag match
            tag_matches = sum(1 for tag in document.tags if tag.lower() in query)
            if document.tags:
                score += (tag_matches / len(document.tags)) * 0.1
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating relevance score: {e}")
            return 0.0
    
    def _generate_highlights(self, query: str, content: str) -> List[str]:
        """Generate highlights from content"""
        try:
            highlights = []
            query_words = query.split()
            content_lower = content.lower()
            
            # Find sentences containing query words
            sentences = content.split('.')
            for sentence in sentences:
                sentence_lower = sentence.lower()
                if any(word in sentence_lower for word in query_words):
                    highlights.append(sentence.strip())
            
            return highlights[:3]  # Limit to 3 highlights
            
        except Exception as e:
            logger.error(f"Error generating highlights: {e}")
            return []
    
    def get_product_info(self, product_id: str) -> Optional[AgilentProduct]:
        """Get product information"""
        return self.products.get(product_id)
    
    def get_document_info(self, document_id: str) -> Optional[AgilentDocument]:
        """Get document information"""
        return self.documents.get(document_id)
    
    def get_products_by_category(self, category: AgilentProductCategory) -> List[AgilentProduct]:
        """Get products by category"""
        try:
            return [p for p in self.products.values() if p.category == category]
        except Exception as e:
            logger.error(f"Error getting products by category: {e}")
            return []
    
    def get_documents_by_type(self, document_type: DocumentType) -> List[AgilentDocument]:
        """Get documents by type"""
        try:
            return [d for d in self.documents.values() if d.document_type == document_type]
        except Exception as e:
            logger.error(f"Error getting documents by type: {e}")
            return []
    
    def get_documents_by_product(self, product_id: str) -> List[AgilentDocument]:
        """Get documents for a product"""
        try:
            return [d for d in self.documents.values() if d.product_id == product_id]
        except Exception as e:
            logger.error(f"Error getting documents by product: {e}")
            return []
    
    def add_product(self, product_data: Dict[str, Any]) -> AgilentProduct:
        """Add a new product"""
        try:
            product = AgilentProduct(
                id=product_data['id'],
                name=product_data['name'],
                model_number=product_data['model_number'],
                category=AgilentProductCategory(product_data['category']),
                description=product_data['description'],
                specifications=product_data.get('specifications', {}),
                features=product_data.get('features', []),
                applications=product_data.get('applications', [])
            )
            
            self.products[product.id] = product
            
            logger.info(f"Added product: {product.id}")
            return product
            
        except Exception as e:
            logger.error(f"Error adding product: {e}")
            raise
    
    def add_document(self, document_data: Dict[str, Any]) -> AgilentDocument:
        """Add a new document"""
        try:
            document = AgilentDocument(
                id=document_data['id'],
                title=document_data['title'],
                document_type=DocumentType(document_data['document_type']),
                product_id=document_data.get('product_id'),
                category=AgilentProductCategory(document_data['category']) if document_data.get('category') else None,
                content=document_data.get('content', ''),
                summary=document_data.get('summary', ''),
                keywords=document_data.get('keywords', []),
                tags=document_data.get('tags', []),
                file_path=document_data.get('file_path'),
                url=document_data.get('url'),
                language=document_data.get('language', 'en'),
                version=document_data.get('version', '1.0')
            )
            
            self.documents[document.id] = document
            
            # Update search index
            self._update_search_index(document)
            
            logger.info(f"Added document: {document.id}")
            return document
            
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            raise
    
    def _update_search_index(self, document: AgilentDocument):
        """Update search index with new document"""
        try:
            # Index by keywords
            for keyword in document.keywords:
                if keyword not in self.search_index:
                    self.search_index[keyword] = []
                if document.id not in self.search_index[keyword]:
                    self.search_index[keyword].append(document.id)
            
            # Index by tags
            for tag in document.tags:
                if tag not in self.search_index:
                    self.search_index[tag] = []
                if document.id not in self.search_index[tag]:
                    self.search_index[tag].append(document.id)
            
            # Index by product ID
            if document.product_id:
                if document.product_id not in self.search_index:
                    self.search_index[document.product_id] = []
                if document.id not in self.search_index[document.product_id]:
                    self.search_index[document.product_id].append(document.id)
            
        except Exception as e:
            logger.error(f"Error updating search index: {e}")
    
    def get_service_statistics(self) -> Dict[str, Any]:
        """Get service statistics"""
        try:
            stats = {
                'total_products': len(self.products),
                'total_documents': len(self.documents),
                'products_by_category': {},
                'documents_by_type': {},
                'search_index_size': len(self.search_index),
                'cache_enabled': self.cache_enabled,
                'service_enabled': self.service_enabled
            }
            
            # Count products by category
            for product in self.products.values():
                category = product.category.value
                stats['products_by_category'][category] = stats['products_by_category'].get(category, 0) + 1
            
            # Count documents by type
            for document in self.documents.values():
                doc_type = document.document_type.value
                stats['documents_by_type'][doc_type] = stats['documents_by_type'].get(doc_type, 0) + 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting service statistics: {e}")
            return {}
    
    def export_data(self) -> Dict[str, Any]:
        """Export service data"""
        try:
            return {
                'products': [
                    {
                        'id': p.id,
                        'name': p.name,
                        'model_number': p.model_number,
                        'category': p.category.value,
                        'description': p.description,
                        'specifications': p.specifications,
                        'features': p.features,
                        'applications': p.applications,
                        'created_at': p.created_at.isoformat(),
                        'updated_at': p.updated_at.isoformat()
                    }
                    for p in self.products.values()
                ],
                'documents': [
                    {
                        'id': d.id,
                        'title': d.title,
                        'document_type': d.document_type.value,
                        'product_id': d.product_id,
                        'category': d.category.value if d.category else None,
                        'content': d.content,
                        'summary': d.summary,
                        'keywords': d.keywords,
                        'tags': d.tags,
                        'file_path': d.file_path,
                        'url': d.url,
                        'language': d.language,
                        'version': d.version,
                        'last_updated': d.last_updated.isoformat(),
                        'created_at': d.created_at.isoformat()
                    }
                    for d in self.documents.values()
                ],
                'search_index': self.search_index
            }
            
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return {}
    
    def import_data(self, data: Dict[str, Any]):
        """Import service data"""
        try:
            # Import products
            if 'products' in data:
                for product_data in data['products']:
                    product = AgilentProduct(
                        id=product_data['id'],
                        name=product_data['name'],
                        model_number=product_data['model_number'],
                        category=AgilentProductCategory(product_data['category']),
                        description=product_data['description'],
                        specifications=product_data.get('specifications', {}),
                        features=product_data.get('features', []),
                        applications=product_data.get('applications', []),
                        created_at=datetime.fromisoformat(product_data['created_at']),
                        updated_at=datetime.fromisoformat(product_data['updated_at'])
                    )
                    self.products[product.id] = product
            
            # Import documents
            if 'documents' in data:
                for document_data in data['documents']:
                    document = AgilentDocument(
                        id=document_data['id'],
                        title=document_data['title'],
                        document_type=DocumentType(document_data['document_type']),
                        product_id=document_data.get('product_id'),
                        category=AgilentProductCategory(document_data['category']) if document_data.get('category') else None,
                        content=document_data.get('content', ''),
                        summary=document_data.get('summary', ''),
                        keywords=document_data.get('keywords', []),
                        tags=document_data.get('tags', []),
                        file_path=document_data.get('file_path'),
                        url=document_data.get('url'),
                        language=document_data.get('language', 'en'),
                        version=document_data.get('version', '1.0'),
                        last_updated=datetime.fromisoformat(document_data['last_updated']),
                        created_at=datetime.fromisoformat(document_data['created_at'])
                    )
                    self.documents[document.id] = document
            
            # Import search index
            if 'search_index' in data:
                self.search_index = data['search_index']
            
            logger.info("Data imported successfully")
            
        except Exception as e:
            logger.error(f"Error importing data: {e}")
            raise
