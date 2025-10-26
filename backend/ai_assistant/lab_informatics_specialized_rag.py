"""
Lab Informatics Specialized RAG Service

This module provides a specialized RAG service for Lab Informatics products
including OpenLab, MassHunter, and other laboratory software solutions.
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
    MASSHUNTER = "masshunter"
    CHEMSTATION = "chemstation"
    EZCHROM = "ezchrom"
    AGILENT_METHOD_SCOUT = "agilent_method_scout"
    AGILENT_CONNECT = "agilent_connect"
    AGILENT_INFINITYLAB = "agilent_infinitylab"
    AGILENT_CROSSLAB = "agilent_crosslab"
    AGILENT_VEE = "agilent_vee"
    AGILENT_BENCHTOP = "agilent_benchtop"
    AGILENT_OPENLAB_CDS = "agilent_openlab_cds"
    AGILENT_OPENLAB_ELN = "agilent_openlab_eln"
    AGILENT_OPENLAB_LIMS = "agilent_openlab_lims"
    AGILENT_OPENLAB_PCS = "agilent_openlab_pcs"
    AGILENT_OPENLAB_SHARED_RESOURCES = "agilent_openlab_shared_resources"


class LabInformaticsDocumentType(Enum):
    """Lab Informatics document type enumeration"""
    USER_GUIDE = "user_guide"
    ADMINISTRATOR_GUIDE = "administrator_guide"
    INSTALLATION_GUIDE = "installation_guide"
    CONFIGURATION_GUIDE = "configuration_guide"
    TROUBLESHOOTING_GUIDE = "troubleshooting_guide"
    API_DOCUMENTATION = "api_documentation"
    SDK_DOCUMENTATION = "sdk_documentation"
    TRAINING_MATERIAL = "training_material"
    BEST_PRACTICES = "best_practices"
    WORKFLOW_GUIDE = "workflow_guide"
    INTEGRATION_GUIDE = "integration_guide"
    SECURITY_GUIDE = "security_guide"
    BACKUP_RECOVERY_GUIDE = "backup_recovery_guide"
    PERFORMANCE_TUNING_GUIDE = "performance_tuning_guide"
    RELEASE_NOTES = "release_notes"
    KNOWN_ISSUES = "known_issues"
    FAQ = "faq"
    VIDEO_TUTORIAL = "video_tutorial"
    WEBINAR = "webinar"
    WHITE_PAPER = "white_paper"


class LabInformaticsCategory(Enum):
    """Lab Informatics category enumeration"""
    DATA_MANAGEMENT = "data_management"
    WORKFLOW_AUTOMATION = "workflow_automation"
    INTEGRATION = "integration"
    SECURITY = "security"
    BACKUP_RECOVERY = "backup_recovery"
    PERFORMANCE = "performance"
    INSTALLATION = "installation"
    CONFIGURATION = "configuration"
    TROUBLESHOOTING = "troubleshooting"
    TRAINING = "training"
    API_SDK = "api_sdk"
    BEST_PRACTICES = "best_practices"


@dataclass
class LabInformaticsProductInfo:
    """Lab Informatics product information structure"""
    id: str
    name: str
    product_type: LabInformaticsProduct
    version: str
    description: str
    features: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    system_requirements: Dict[str, Any] = field(default_factory=dict)
    supported_platforms: List[str] = field(default_factory=list)
    integration_options: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: django_timezone.now())
    updated_at: datetime = field(default_factory=lambda: django_timezone.now())


@dataclass
class LabInformaticsDocument:
    """Lab Informatics document structure"""
    id: str
    title: str
    document_type: LabInformaticsDocumentType
    product_id: Optional[str] = None
    category: Optional[LabInformaticsCategory] = None
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
class LabInformaticsSearchResult:
    """Lab Informatics search result structure"""
    document_id: str
    title: str
    content: str
    relevance_score: float
    document_type: LabInformaticsDocumentType
    product_id: Optional[str] = None
    category: Optional[LabInformaticsCategory] = None
    highlights: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class LabInformaticsSpecializedRAGService:
    """Lab Informatics Specialized RAG Service"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize Lab Informatics Specialized RAG Service"""
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
        
        logger.info("Lab Informatics Specialized RAG Service initialized")
    
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
        """Initialize Lab Informatics product catalog"""
        try:
            # Sample Lab Informatics products
            products = [
                LabInformaticsProductInfo(
                    id="openlab_cds",
                    name="OpenLab CDS",
                    product_type=LabInformaticsProduct.OPENLAB,
                    version="2.6",
                    description="Comprehensive chromatography data system for analytical laboratories",
                    features=[
                        "Method development and validation",
                        "Data acquisition and processing",
                        "Compliance and reporting",
                        "Multi-vendor instrument support"
                    ],
                    capabilities=[
                        "LC/GC data analysis",
                        "Method transfer",
                        "Quality control",
                        "Regulatory compliance"
                    ],
                    system_requirements={
                        "os": "Windows 10/11, Linux",
                        "ram": "8GB minimum",
                        "storage": "100GB minimum",
                        "processor": "Intel i5 or equivalent"
                    },
                    supported_platforms=["Windows", "Linux"],
                    integration_options=["REST API", "Web Services", "Database"]
                ),
                LabInformaticsProductInfo(
                    id="masshunter_workstation",
                    name="MassHunter Workstation",
                    product_type=LabInformaticsProduct.MASSHUNTER,
                    version="10.1",
                    description="Mass spectrometry data analysis software",
                    features=[
                        "Qualitative and quantitative analysis",
                        "Method development",
                        "Data processing",
                        "Reporting and visualization"
                    ],
                    capabilities=[
                        "GC/MS data analysis",
                        "LC/MS data analysis",
                        "Metabolomics analysis",
                        "Proteomics analysis"
                    ],
                    system_requirements={
                        "os": "Windows 10/11",
                        "ram": "16GB minimum",
                        "storage": "200GB minimum",
                        "processor": "Intel i7 or equivalent"
                    },
                    supported_platforms=["Windows"],
                    integration_options=["REST API", "Database", "File System"]
                ),
                LabInformaticsProductInfo(
                    id="openlab_eln",
                    name="OpenLab ELN",
                    product_type=LabInformaticsProduct.OPENLAB,
                    version="2.6",
                    description="Electronic laboratory notebook for research and development",
                    features=[
                        "Experiment documentation",
                        "Data capture",
                        "Collaboration tools",
                        "Compliance features"
                    ],
                    capabilities=[
                        "Experiment planning",
                        "Data recording",
                        "Result analysis",
                        "Report generation"
                    ],
                    system_requirements={
                        "os": "Windows 10/11, Linux",
                        "ram": "8GB minimum",
                        "storage": "50GB minimum",
                        "processor": "Intel i5 or equivalent"
                    },
                    supported_platforms=["Windows", "Linux"],
                    integration_options=["REST API", "Web Services", "Database"]
                )
            ]
            
            for product in products:
                self.products[product.id] = product
            
            logger.info(f"Initialized {len(products)} Lab Informatics products")
            
        except Exception as e:
            logger.error(f"Error initializing product catalog: {e}")
    
    def _initialize_document_collection(self):
        """Initialize document collection"""
        try:
            # Sample Lab Informatics documents
            documents = [
                LabInformaticsDocument(
                    id="doc_openlab_cds_user_guide",
                    title="OpenLab CDS User Guide",
                    document_type=LabInformaticsDocumentType.USER_GUIDE,
                    product_id="openlab_cds",
                    category=LabInformaticsCategory.DATA_MANAGEMENT,
                    content="This user guide provides comprehensive instructions for using OpenLab CDS. The system includes data acquisition, processing, and reporting capabilities. Key features include method development, data analysis, and compliance reporting. The software supports multiple instrument types and provides integration with laboratory information systems.",
                    summary="Complete user guide for OpenLab CDS operation",
                    keywords=["OpenLab", "CDS", "chromatography", "data", "analysis"],
                    tags=["user_guide", "OpenLab", "CDS", "chromatography"]
                ),
                LabInformaticsDocument(
                    id="doc_masshunter_troubleshooting",
                    title="MassHunter Troubleshooting Guide",
                    document_type=LabInformaticsDocumentType.TROUBLESHOOTING_GUIDE,
                    product_id="masshunter_workstation",
                    category=LabInformaticsCategory.TROUBLESHOOTING,
                    content="This troubleshooting guide covers common issues with MassHunter Workstation. Common problems include data acquisition issues, analysis errors, and performance problems. Solutions include checking instrument connections, recalibrating mass axis, and optimizing system performance.",
                    summary="Troubleshooting guide for MassHunter Workstation",
                    keywords=["MassHunter", "troubleshooting", "mass spectrometry", "analysis"],
                    tags=["troubleshooting", "MassHunter", "mass spectrometry"]
                ),
                LabInformaticsDocument(
                    id="doc_openlab_eln_best_practices",
                    title="OpenLab ELN Best Practices",
                    document_type=LabInformaticsDocumentType.BEST_PRACTICES,
                    product_id="openlab_eln",
                    category=LabInformaticsCategory.BEST_PRACTICES,
                    content="This document outlines best practices for using OpenLab ELN effectively. Topics include experiment design, data organization, collaboration workflows, and compliance requirements. Recommendations cover data integrity, security, and regulatory compliance.",
                    summary="Best practices for OpenLab ELN usage",
                    keywords=["OpenLab", "ELN", "best practices", "experiment", "compliance"],
                    tags=["best_practices", "OpenLab", "ELN", "experiment"]
                )
            ]
            
            for document in documents:
                self.documents[document.id] = document
            
            logger.info(f"Initialized {len(documents)} Lab Informatics documents")
            
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
    
    def search_documents(self, query: str, filters: Dict[str, Any] = None) -> List[LabInformaticsSearchResult]:
        """Search Lab Informatics documents"""
        try:
            # Check cache first
            if self.cache_enabled:
                cache_key = f"lab_informatics_search_{hash(query)}_{hash(str(filters))}"
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
                    result = LabInformaticsSearchResult(
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
    
    def _calculate_relevance_score(self, query: str, document: LabInformaticsDocument) -> float:
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
    
    def get_product_info(self, product_id: str) -> Optional[LabInformaticsProductInfo]:
        """Get product information"""
        return self.products.get(product_id)
    
    def get_document_info(self, document_id: str) -> Optional[LabInformaticsDocument]:
        """Get document information"""
        return self.documents.get(document_id)
    
    def get_products_by_type(self, product_type: LabInformaticsProduct) -> List[LabInformaticsProductInfo]:
        """Get products by type"""
        try:
            return [p for p in self.products.values() if p.product_type == product_type]
        except Exception as e:
            logger.error(f"Error getting products by type: {e}")
            return []
    
    def get_documents_by_type(self, document_type: LabInformaticsDocumentType) -> List[LabInformaticsDocument]:
        """Get documents by type"""
        try:
            return [d for d in self.documents.values() if d.document_type == document_type]
        except Exception as e:
            logger.error(f"Error getting documents by type: {e}")
            return []
    
    def get_documents_by_product(self, product_id: str) -> List[LabInformaticsDocument]:
        """Get documents for a product"""
        try:
            return [d for d in self.documents.values() if d.product_id == product_id]
        except Exception as e:
            logger.error(f"Error getting documents by product: {e}")
            return []
    
    def get_documents_by_category(self, category: LabInformaticsCategory) -> List[LabInformaticsDocument]:
        """Get documents by category"""
        try:
            return [d for d in self.documents.values() if d.category == category]
        except Exception as e:
            logger.error(f"Error getting documents by category: {e}")
            return []
    
    def add_product(self, product_data: Dict[str, Any]) -> LabInformaticsProductInfo:
        """Add a new product"""
        try:
            product = LabInformaticsProductInfo(
                id=product_data['id'],
                name=product_data['name'],
                product_type=LabInformaticsProduct(product_data['product_type']),
                version=product_data['version'],
                description=product_data['description'],
                features=product_data.get('features', []),
                capabilities=product_data.get('capabilities', []),
                system_requirements=product_data.get('system_requirements', {}),
                supported_platforms=product_data.get('supported_platforms', []),
                integration_options=product_data.get('integration_options', [])
            )
            
            self.products[product.id] = product
            
            logger.info(f"Added product: {product.id}")
            return product
            
        except Exception as e:
            logger.error(f"Error adding product: {e}")
            raise
    
    def add_document(self, document_data: Dict[str, Any]) -> LabInformaticsDocument:
        """Add a new document"""
        try:
            document = LabInformaticsDocument(
                id=document_data['id'],
                title=document_data['title'],
                document_type=LabInformaticsDocumentType(document_data['document_type']),
                product_id=document_data.get('product_id'),
                category=LabInformaticsCategory(document_data['category']) if document_data.get('category') else None,
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
    
    def _update_search_index(self, document: LabInformaticsDocument):
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
                'products_by_type': {},
                'documents_by_type': {},
                'documents_by_category': {},
                'search_index_size': len(self.search_index),
                'cache_enabled': self.cache_enabled,
                'service_enabled': self.service_enabled
            }
            
            # Count products by type
            for product in self.products.values():
                product_type = product.product_type.value
                stats['products_by_type'][product_type] = stats['products_by_type'].get(product_type, 0) + 1
            
            # Count documents by type
            for document in self.documents.values():
                doc_type = document.document_type.value
                stats['documents_by_type'][doc_type] = stats['documents_by_type'].get(doc_type, 0) + 1
            
            # Count documents by category
            for document in self.documents.values():
                if document.category:
                    category = document.category.value
                    stats['documents_by_category'][category] = stats['documents_by_category'].get(category, 0) + 1
            
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
                        'product_type': p.product_type.value,
                        'version': p.version,
                        'description': p.description,
                        'features': p.features,
                        'capabilities': p.capabilities,
                        'system_requirements': p.system_requirements,
                        'supported_platforms': p.supported_platforms,
                        'integration_options': p.integration_options,
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
                    product = LabInformaticsProductInfo(
                        id=product_data['id'],
                        name=product_data['name'],
                        product_type=LabInformaticsProduct(product_data['product_type']),
                        version=product_data['version'],
                        description=product_data['description'],
                        features=product_data.get('features', []),
                        capabilities=product_data.get('capabilities', []),
                        system_requirements=product_data.get('system_requirements', {}),
                        supported_platforms=product_data.get('supported_platforms', []),
                        integration_options=product_data.get('integration_options', []),
                        created_at=datetime.fromisoformat(product_data['created_at']),
                        updated_at=datetime.fromisoformat(product_data['updated_at'])
                    )
                    self.products[product.id] = product
            
            # Import documents
            if 'documents' in data:
                for document_data in data['documents']:
                    document = LabInformaticsDocument(
                        id=document_data['id'],
                        title=document_data['title'],
                        document_type=LabInformaticsDocumentType(document_data['document_type']),
                        product_id=document_data.get('product_id'),
                        category=LabInformaticsCategory(document_data['category']) if document_data.get('category') else None,
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
