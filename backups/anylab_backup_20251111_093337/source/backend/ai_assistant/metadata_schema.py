"""
Dual-Mode Metadata Schema for AnyLab Document Management System

This module defines comprehensive metadata schemas for both General Agilent Products
and Lab Informatics Focus modes, enabling intelligent content organization and filtering.
"""

from typing import Dict, List, Optional, Union, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import json


class OrganizationMode(Enum):
    """Organization mode enumeration"""
    GENERAL = "general"
    LAB_INFORMATICS = "lab-informatics"


class DocumentType(Enum):
    """Document type enumeration"""
    # General Agilent Products
    USER_MANUAL = "user_manual"
    TECHNICAL_SPECIFICATION = "technical_specification"
    INSTALLATION_GUIDE = "installation_guide"
    MAINTENANCE_GUIDE = "maintenance_guide"
    PRODUCT_CATALOG = "product_catalog"
    APPLICATION_NOTE = "application_note"
    WHITE_PAPER = "white_paper"
    
    # Lab Informatics specific
    SSB_KPR = "ssb_kpr"  # Software Status Bulletin - Known Problem Report
    TROUBLESHOOTING_GUIDE = "troubleshooting_guide"
    MAINTENANCE_PROCEDURE = "maintenance_procedure"
    CALIBRATION_PROCEDURE = "calibration_procedure"
    CONFIGURATION_GUIDE = "configuration_guide"
    BEST_PRACTICE_GUIDE = "best_practice_guide"
    COMMUNITY_SOLUTION = "community_solution"
    VIDEO_TUTORIAL = "video_tutorial"
    WEBINAR_RECORDING = "webinar_recording"


class SeverityLevel(Enum):
    """Severity level for troubleshooting documents"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class ProductCategory(Enum):
    """Product category enumeration"""
    # General Agilent Products
    GAS_CHROMATOGRAPHY = "gas_chromatography"
    LIQUID_CHROMATOGRAPHY = "liquid_chromatography"
    MASS_SPECTROMETRY = "mass_spectrometry"
    NMR_SYSTEMS = "nmr_systems"
    SPECTROSCOPY = "spectroscopy"
    VACUUM_TECHNOLOGIES = "vacuum_technologies"
    LIFE_SCIENCES = "life_sciences"
    DIAGNOSTICS = "diagnostics"
    
    # Lab Informatics specific
    OPENLAB_CDS = "openlab_cds"
    OPENLAB_ECM = "openlab_ecm"
    OPENLAB_ELN = "openlab_eln"
    OPENLAB_SERVER = "openlab_server"
    MASSHUNTER_WORKSTATION = "masshunter_workstation"
    MASSHUNTER_QUANTITATIVE = "masshunter_quantitative"
    MASSHUNTER_QUALITATIVE = "masshunter_qualitative"
    MASSHUNTER_BIO_CONFIRM = "masshunter_bio_confirm"
    MASSHUNTER_METABOLOMICS = "masshunter_metabolomics"
    VNMRJ_CURRENT = "vnmrj_current"
    VNMRJ_LEGACY = "vnmrj_legacy"
    VNMR_LEGACY = "vnmr_legacy"


class ContentCategory(Enum):
    """Content category enumeration"""
    # General categories
    INSTALLATION = "installation"
    CONFIGURATION = "configuration"
    OPERATION = "operation"
    MAINTENANCE = "maintenance"
    TROUBLESHOOTING = "troubleshooting"
    TRAINING = "training"
    REFERENCE = "reference"
    
    # Lab Informatics specific
    DATABASE_ISSUES = "database_issues"
    PERFORMANCE_ISSUES = "performance_issues"
    CONNECTIVITY_ISSUES = "connectivity_issues"
    UI_ISSUES = "ui_issues"
    WORKFLOW_ISSUES = "workflow_issues"
    DRIVER_ISSUES = "driver_issues"
    LICENSING_ISSUES = "licensing_issues"


@dataclass
class GeneralAgilentMetadata:
    """Metadata schema for General Agilent Products mode"""
    
    # Basic document information
    document_id: str
    title: str
    filename: str
    file_type: str
    file_size: int
    
    # Product classification
    product_category: ProductCategory
    
    # Content classification (required fields must come before optional)
    document_type: DocumentType
    content_category: ContentCategory
    
    # Optional fields
    page_count: Optional[int] = None
    language: str = "English"
    version: Optional[str] = None
    last_updated: datetime = field(default_factory=datetime.now)
    created_date: Optional[datetime] = None
    product_line: Optional[str] = None
    model_number: Optional[str] = None
    software_version: Optional[str] = None
    target_audience: List[str] = field(default_factory=list)
    technical_level: str = "intermediate"  # beginner, intermediate, advanced, expert
    
    # Industry and compliance
    industry_application: List[str] = field(default_factory=list)
    compliance_standards: List[str] = field(default_factory=list)
    
    # Content analysis
    keywords: List[str] = field(default_factory=list)
    search_tags: List[str] = field(default_factory=list)
    summary: Optional[str] = None
    
    # Quality metrics
    validation_status: str = "pending"  # pending, validated, rejected
    accuracy_score: float = 0.0
    completeness_score: float = 0.0
    usability_score: float = 0.0
    last_reviewed: Optional[datetime] = None
    reviewer: Optional[str] = None
    
    # Usage analytics
    view_count: int = 0
    download_count: int = 0
    search_hits: int = 0
    user_rating: float = 0.0
    last_accessed: Optional[datetime] = None
    
    # Source information
    source_url: Optional[str] = None
    source_type: str = "manual_upload"  # manual_upload, web_scraping, api_import
    collection_date: Optional[datetime] = None
    
    # Cross-references
    related_documents: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    
    # RAG optimization
    chunking_strategy: str = "semantic"
    embedding_model: str = "bge-m3"
    search_priority: str = "medium"  # low, medium, high, critical


@dataclass
class LabInformaticsMetadata:
    """Metadata schema for Lab Informatics Focus mode"""
    
    # Basic document information
    document_id: str
    title: str
    filename: str
    file_type: str
    file_size: int
    
    # Software platform classification (required fields first)
    software_platform: ProductCategory
    software_version: str
    
    # Content classification (required fields)
    document_type: DocumentType
    content_category: ContentCategory
    
    # Optional basic fields
    page_count: Optional[int] = None
    language: str = "English"
    version: Optional[str] = None
    last_updated: datetime = field(default_factory=datetime.now)
    created_date: Optional[datetime] = None
    software_edition: Optional[str] = None  # Standard, Enterprise, Express
    
    # Problem classification (for troubleshooting documents)
    problem_category: Optional[str] = None
    problem_subcategory: Optional[str] = None
    severity_level: Optional[SeverityLevel] = None
    frequency: Optional[str] = None  # rare, occasional, common, frequent
    urgency: Optional[str] = None  # low, medium, high, critical
    
    # Error information
    error_codes: List[str] = field(default_factory=list)
    error_messages: List[str] = field(default_factory=list)
    kpr_number: Optional[str] = None  # Known Problem Report number
    
    # Solution information
    solution_type: Optional[str] = None  # workaround, fix, best_practice
    difficulty_level: Optional[str] = None  # easy, medium, hard, expert
    estimated_time: Optional[str] = None
    success_rate: Optional[float] = None
    prerequisites: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    rollback_procedure: Optional[str] = None
    
    # Maintenance context
    maintenance_type: Optional[str] = None  # preventive, corrective, predictive
    maintenance_frequency: Optional[str] = None
    preventive_measures: List[str] = field(default_factory=list)
    related_maintenance: List[str] = field(default_factory=list)
    
    target_audience: List[str] = field(default_factory=list)
    skill_level: Optional[str] = None  # beginner, intermediate, advanced
    
    # Compatibility information
    os_support: List[str] = field(default_factory=list)
    database_support: List[str] = field(default_factory=list)
    instrument_support: List[str] = field(default_factory=list)
    legacy_support: List[str] = field(default_factory=list)
    
    # Content analysis
    keywords: List[str] = field(default_factory=list)
    search_tags: List[str] = field(default_factory=list)
    summary: Optional[str] = None
    
    # Quality metrics
    validation_status: str = "pending"  # pending, validated, rejected, community_validated
    accuracy_score: float = 0.0
    completeness_score: float = 0.0
    usability_score: float = 0.0
    last_reviewed: Optional[datetime] = None
    reviewer: Optional[str] = None
    
    # Usage analytics
    view_count: int = 0
    download_count: int = 0
    search_hits: int = 0
    success_count: int = 0
    failure_count: int = 0
    user_rating: float = 0.0
    last_accessed: Optional[datetime] = None
    
    # Source information
    source_url: Optional[str] = None
    source_type: str = "manual_upload"  # manual_upload, web_scraping, ssb_import, community_forum
    collection_date: Optional[datetime] = None
    
    # Cross-references
    related_documents: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    
    # RAG optimization
    chunking_strategy: str = "problem-solution"
    embedding_model: str = "bge-m3"
    search_priority: str = "high"  # low, medium, high, critical


@dataclass
class DualModeMetadata:
    """Unified metadata schema supporting both organization modes"""
    
    # Organization mode
    organization_mode: OrganizationMode
    
    # Common metadata fields
    document_id: str
    title: str
    filename: str
    file_type: str
    file_size: int
    page_count: Optional[int] = None
    language: str = "English"
    version: Optional[str] = None
    last_updated: datetime = field(default_factory=datetime.now)
    created_date: Optional[datetime] = None
    
    # Mode-specific metadata
    general_metadata: Optional[GeneralAgilentMetadata] = None
    lab_informatics_metadata: Optional[LabInformaticsMetadata] = None
    
    # Common fields for both modes
    document_type: DocumentType = DocumentType.USER_MANUAL
    content_category: ContentCategory = ContentCategory.REFERENCE
    keywords: List[str] = field(default_factory=list)
    search_tags: List[str] = field(default_factory=list)
    summary: Optional[str] = None
    
    # Quality metrics
    validation_status: str = "pending"
    accuracy_score: float = 0.0
    completeness_score: float = 0.0
    usability_score: float = 0.0
    last_reviewed: Optional[datetime] = None
    reviewer: Optional[str] = None
    
    # Usage analytics
    view_count: int = 0
    download_count: int = 0
    search_hits: int = 0
    user_rating: float = 0.0
    last_accessed: Optional[datetime] = None
    
    # Source information
    source_url: Optional[str] = None
    source_type: str = "manual_upload"
    collection_date: Optional[datetime] = None
    
    # Cross-references
    related_documents: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    
    # RAG optimization
    chunking_strategy: str = "semantic"
    embedding_model: str = "bge-m3"
    search_priority: str = "medium"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary for JSON serialization"""
        data = {
            'organization_mode': self.organization_mode.value,
            'document_id': self.document_id,
            'title': self.title,
            'filename': self.filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'page_count': self.page_count,
            'language': self.language,
            'version': self.version,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'document_type': self.document_type.value,
            'content_category': self.content_category.value,
            'keywords': self.keywords,
            'search_tags': self.search_tags,
            'summary': self.summary,
            'validation_status': self.validation_status,
            'accuracy_score': self.accuracy_score,
            'completeness_score': self.completeness_score,
            'usability_score': self.usability_score,
            'last_reviewed': self.last_reviewed.isoformat() if self.last_reviewed else None,
            'reviewer': self.reviewer,
            'view_count': self.view_count,
            'download_count': self.download_count,
            'search_hits': self.search_hits,
            'user_rating': self.user_rating,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'source_url': self.source_url,
            'source_type': self.source_type,
            'collection_date': self.collection_date.isoformat() if self.collection_date else None,
            'related_documents': self.related_documents,
            'dependencies': self.dependencies,
            'chunking_strategy': self.chunking_strategy,
            'embedding_model': self.embedding_model,
            'search_priority': self.search_priority,
        }
        
        # Add mode-specific metadata
        if self.general_metadata:
            data['general_metadata'] = {
                'product_category': self.general_metadata.product_category.value,
                'product_line': self.general_metadata.product_line,
                'model_number': self.general_metadata.model_number,
                'software_version': self.general_metadata.software_version,
                'target_audience': self.general_metadata.target_audience,
                'technical_level': self.general_metadata.technical_level,
                'industry_application': self.general_metadata.industry_application,
                'compliance_standards': self.general_metadata.compliance_standards,
            }
        
        if self.lab_informatics_metadata:
            data['lab_informatics_metadata'] = {
                'software_platform': self.lab_informatics_metadata.software_platform.value,
                'software_version': self.lab_informatics_metadata.software_version,
                'software_edition': self.lab_informatics_metadata.software_edition,
                'problem_category': self.lab_informatics_metadata.problem_category,
                'problem_subcategory': self.lab_informatics_metadata.problem_subcategory,
                'severity_level': self.lab_informatics_metadata.severity_level.value if self.lab_informatics_metadata.severity_level else None,
                'frequency': self.lab_informatics_metadata.frequency,
                'urgency': self.lab_informatics_metadata.urgency,
                'error_codes': self.lab_informatics_metadata.error_codes,
                'error_messages': self.lab_informatics_metadata.error_messages,
                'kpr_number': self.lab_informatics_metadata.kpr_number,
                'solution_type': self.lab_informatics_metadata.solution_type,
                'difficulty_level': self.lab_informatics_metadata.difficulty_level,
                'estimated_time': self.lab_informatics_metadata.estimated_time,
                'success_rate': self.lab_informatics_metadata.success_rate,
                'prerequisites': self.lab_informatics_metadata.prerequisites,
                'risks': self.lab_informatics_metadata.risks,
                'rollback_procedure': self.lab_informatics_metadata.rollback_procedure,
                'maintenance_type': self.lab_informatics_metadata.maintenance_type,
                'maintenance_frequency': self.lab_informatics_metadata.maintenance_frequency,
                'preventive_measures': self.lab_informatics_metadata.preventive_measures,
                'related_maintenance': self.lab_informatics_metadata.related_maintenance,
                'target_audience': self.lab_informatics_metadata.target_audience,
                'skill_level': self.lab_informatics_metadata.skill_level,
                'os_support': self.lab_informatics_metadata.os_support,
                'database_support': self.lab_informatics_metadata.database_support,
                'instrument_support': self.lab_informatics_metadata.instrument_support,
                'legacy_support': self.lab_informatics_metadata.legacy_support,
                'success_count': self.lab_informatics_metadata.success_count,
                'failure_count': self.lab_informatics_metadata.failure_count,
            }
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DualModeMetadata':
        """Create metadata from dictionary"""
        # Parse datetime fields
        last_updated = datetime.fromisoformat(data['last_updated']) if data.get('last_updated') else datetime.now()
        created_date = datetime.fromisoformat(data['created_date']) if data.get('created_date') else None
        last_reviewed = datetime.fromisoformat(data['last_reviewed']) if data.get('last_reviewed') else None
        last_accessed = datetime.fromisoformat(data['last_accessed']) if data.get('last_accessed') else None
        collection_date = datetime.fromisoformat(data['collection_date']) if data.get('collection_date') else None
        
        metadata = cls(
            organization_mode=OrganizationMode(data['organization_mode']),
            document_id=data['document_id'],
            title=data['title'],
            filename=data['filename'],
            file_type=data['file_type'],
            file_size=data['file_size'],
            page_count=data.get('page_count'),
            language=data.get('language', 'English'),
            version=data.get('version'),
            last_updated=last_updated,
            created_date=created_date,
            document_type=DocumentType(data['document_type']),
            content_category=ContentCategory(data['content_category']),
            keywords=data.get('keywords', []),
            search_tags=data.get('search_tags', []),
            summary=data.get('summary'),
            validation_status=data.get('validation_status', 'pending'),
            accuracy_score=data.get('accuracy_score', 0.0),
            completeness_score=data.get('completeness_score', 0.0),
            usability_score=data.get('usability_score', 0.0),
            last_reviewed=last_reviewed,
            reviewer=data.get('reviewer'),
            view_count=data.get('view_count', 0),
            download_count=data.get('download_count', 0),
            search_hits=data.get('search_hits', 0),
            user_rating=data.get('user_rating', 0.0),
            last_accessed=last_accessed,
            source_url=data.get('source_url'),
            source_type=data.get('source_type', 'manual_upload'),
            collection_date=collection_date,
            related_documents=data.get('related_documents', []),
            dependencies=data.get('dependencies', []),
            chunking_strategy=data.get('chunking_strategy', 'semantic'),
            embedding_model=data.get('embedding_model', 'bge-m3'),
            search_priority=data.get('search_priority', 'medium'),
        )
        
        # Add mode-specific metadata
        if 'general_metadata' in data and data['general_metadata']:
            general_data = data['general_metadata']
            metadata.general_metadata = GeneralAgilentMetadata(
                document_id=data['document_id'],
                title=data['title'],
                filename=data['filename'],
                file_type=data['file_type'],
                file_size=data['file_size'],
                page_count=data.get('page_count'),
                language=data.get('language', 'English'),
                version=data.get('version'),
                last_updated=last_updated,
                created_date=created_date,
                product_category=ProductCategory(general_data['product_category']),
                product_line=general_data.get('product_line'),
                model_number=general_data.get('model_number'),
                software_version=general_data.get('software_version'),
                document_type=DocumentType(data['document_type']),
                content_category=ContentCategory(data['content_category']),
                target_audience=general_data.get('target_audience', []),
                technical_level=general_data.get('technical_level', 'intermediate'),
                industry_application=general_data.get('industry_application', []),
                compliance_standards=general_data.get('compliance_standards', []),
                keywords=data.get('keywords', []),
                search_tags=data.get('search_tags', []),
                summary=data.get('summary'),
                validation_status=data.get('validation_status', 'pending'),
                accuracy_score=data.get('accuracy_score', 0.0),
                completeness_score=data.get('completeness_score', 0.0),
                usability_score=data.get('usability_score', 0.0),
                last_reviewed=last_reviewed,
                reviewer=data.get('reviewer'),
                view_count=data.get('view_count', 0),
                download_count=data.get('download_count', 0),
                search_hits=data.get('search_hits', 0),
                user_rating=data.get('user_rating', 0.0),
                last_accessed=last_accessed,
                source_url=data.get('source_url'),
                source_type=data.get('source_type', 'manual_upload'),
                collection_date=collection_date,
                related_documents=data.get('related_documents', []),
                dependencies=data.get('dependencies', []),
                chunking_strategy=data.get('chunking_strategy', 'semantic'),
                embedding_model=data.get('embedding_model', 'bge-m3'),
                search_priority=data.get('search_priority', 'medium'),
            )
        
        if 'lab_informatics_metadata' in data and data['lab_informatics_metadata']:
            lab_data = data['lab_informatics_metadata']
            metadata.lab_informatics_metadata = LabInformaticsMetadata(
                document_id=data['document_id'],
                title=data['title'],
                filename=data['filename'],
                file_type=data['file_type'],
                file_size=data['file_size'],
                page_count=data.get('page_count'),
                language=data.get('language', 'English'),
                version=data.get('version'),
                last_updated=last_updated,
                created_date=created_date,
                software_platform=ProductCategory(lab_data['software_platform']),
                software_version=lab_data['software_version'],
                software_edition=lab_data.get('software_edition'),
                problem_category=lab_data.get('problem_category'),
                problem_subcategory=lab_data.get('problem_subcategory'),
                severity_level=SeverityLevel(lab_data['severity_level']) if lab_data.get('severity_level') else None,
                frequency=lab_data.get('frequency'),
                urgency=lab_data.get('urgency'),
                error_codes=lab_data.get('error_codes', []),
                error_messages=lab_data.get('error_messages', []),
                kpr_number=lab_data.get('kpr_number'),
                solution_type=lab_data.get('solution_type'),
                difficulty_level=lab_data.get('difficulty_level'),
                estimated_time=lab_data.get('estimated_time'),
                success_rate=lab_data.get('success_rate'),
                prerequisites=lab_data.get('prerequisites', []),
                risks=lab_data.get('risks', []),
                rollback_procedure=lab_data.get('rollback_procedure'),
                maintenance_type=lab_data.get('maintenance_type'),
                maintenance_frequency=lab_data.get('maintenance_frequency'),
                preventive_measures=lab_data.get('preventive_measures', []),
                related_maintenance=lab_data.get('related_maintenance', []),
                document_type=DocumentType(data['document_type']),
                content_category=ContentCategory(data['content_category']),
                target_audience=lab_data.get('target_audience', []),
                skill_level=lab_data.get('skill_level'),
                os_support=lab_data.get('os_support', []),
                database_support=lab_data.get('database_support', []),
                instrument_support=lab_data.get('instrument_support', []),
                legacy_support=lab_data.get('legacy_support', []),
                keywords=data.get('keywords', []),
                search_tags=data.get('search_tags', []),
                summary=data.get('summary'),
                validation_status=data.get('validation_status', 'pending'),
                accuracy_score=data.get('accuracy_score', 0.0),
                completeness_score=data.get('completeness_score', 0.0),
                usability_score=data.get('usability_score', 0.0),
                last_reviewed=last_reviewed,
                reviewer=data.get('reviewer'),
                view_count=data.get('view_count', 0),
                download_count=data.get('download_count', 0),
                search_hits=data.get('search_hits', 0),
                success_count=lab_data.get('success_count', 0),
                failure_count=lab_data.get('failure_count', 0),
                user_rating=data.get('user_rating', 0.0),
                last_accessed=last_accessed,
                source_url=data.get('source_url'),
                source_type=data.get('source_type', 'manual_upload'),
                collection_date=collection_date,
                related_documents=data.get('related_documents', []),
                dependencies=data.get('dependencies', []),
                chunking_strategy=data.get('chunking_strategy', 'problem-solution'),
                embedding_model=data.get('embedding_model', 'bge-m3'),
                search_priority=data.get('search_priority', 'high'),
            )
        
        return metadata


class MetadataManager:
    """Manager class for handling dual-mode metadata operations"""
    
    def __init__(self):
        self.metadata_cache: Dict[str, DualModeMetadata] = {}
    
    def create_metadata(self, 
                       organization_mode: OrganizationMode,
                       document_id: str,
                       title: str,
                       filename: str,
                       file_type: str,
                       file_size: int,
                       **kwargs) -> DualModeMetadata:
        """Create metadata for a document"""
        
        metadata = DualModeMetadata(
            organization_mode=organization_mode,
            document_id=document_id,
            title=title,
            filename=filename,
            file_type=file_type,
            file_size=file_size,
            **kwargs
        )
        
        # Add mode-specific metadata
        if organization_mode == OrganizationMode.GENERAL:
            metadata.general_metadata = GeneralAgilentMetadata(
                document_id=document_id,
                title=title,
                filename=filename,
                file_type=file_type,
                file_size=file_size,
                **kwargs
            )
        elif organization_mode == OrganizationMode.LAB_INFORMATICS:
            metadata.lab_informatics_metadata = LabInformaticsMetadata(
                document_id=document_id,
                title=title,
                filename=filename,
                file_type=file_type,
                file_size=file_size,
                **kwargs
            )
        
        self.metadata_cache[document_id] = metadata
        return metadata
    
    def get_metadata(self, document_id: str) -> Optional[DualModeMetadata]:
        """Get metadata by document ID"""
        return self.metadata_cache.get(document_id)
    
    def update_metadata(self, document_id: str, updates: Dict[str, Any]) -> bool:
        """Update metadata for a document"""
        if document_id not in self.metadata_cache:
            return False
        
        metadata = self.metadata_cache[document_id]
        
        # Update common fields
        for key, value in updates.items():
            if hasattr(metadata, key):
                setattr(metadata, key, value)
        
        # Update mode-specific metadata
        if metadata.organization_mode == OrganizationMode.GENERAL and metadata.general_metadata:
            for key, value in updates.items():
                if hasattr(metadata.general_metadata, key):
                    setattr(metadata.general_metadata, key, value)
        
        elif metadata.organization_mode == OrganizationMode.LAB_INFORMATICS and metadata.lab_informatics_metadata:
            for key, value in updates.items():
                if hasattr(metadata.lab_informatics_metadata, key):
                    setattr(metadata.lab_informatics_metadata, key, value)
        
        return True
    
    def delete_metadata(self, document_id: str) -> bool:
        """Delete metadata for a document"""
        if document_id in self.metadata_cache:
            del self.metadata_cache[document_id]
            return True
        return False
    
    def search_metadata(self, 
                       organization_mode: Optional[OrganizationMode] = None,
                       filters: Optional[Dict[str, Any]] = None) -> List[DualModeMetadata]:
        """Search metadata with filters"""
        results = []
        
        for metadata in self.metadata_cache.values():
            # Filter by organization mode
            if organization_mode and metadata.organization_mode != organization_mode:
                continue
            
            # Apply additional filters
            if filters:
                match = True
                for key, value in filters.items():
                    if hasattr(metadata, key):
                        if getattr(metadata, key) != value:
                            match = False
                            break
                    elif metadata.general_metadata and hasattr(metadata.general_metadata, key):
                        if getattr(metadata.general_metadata, key) != value:
                            match = False
                            break
                    elif metadata.lab_informatics_metadata and hasattr(metadata.lab_informatics_metadata, key):
                        if getattr(metadata.lab_informatics_metadata, key) != value:
                            match = False
                            break
                
                if not match:
                    continue
            
            results.append(metadata)
        
        return results
    
    def export_metadata(self, file_path: str) -> bool:
        """Export all metadata to JSON file"""
        try:
            data = {
                'metadata': [metadata.to_dict() for metadata in self.metadata_cache.values()],
                'export_date': datetime.now().isoformat(),
                'total_documents': len(self.metadata_cache)
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error exporting metadata: {e}")
            return False
    
    def import_metadata(self, file_path: str) -> bool:
        """Import metadata from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for metadata_dict in data.get('metadata', []):
                metadata = DualModeMetadata.from_dict(metadata_dict)
                self.metadata_cache[metadata.document_id] = metadata
            
            return True
        except Exception as e:
            print(f"Error importing metadata: {e}")
            return False


# Example usage and testing
if __name__ == "__main__":
    # Create metadata manager
    manager = MetadataManager()
    
    # Create General Agilent metadata
    general_metadata = manager.create_metadata(
        organization_mode=OrganizationMode.GENERAL,
        document_id="AGL-GC-001",
        title="7890B GC System User Manual",
        filename="7890B_GC_User_Manual.pdf",
        file_type="PDF",
        file_size=1024000,
        product_category=ProductCategory.GAS_CHROMATOGRAPHY,
        document_type=DocumentType.USER_MANUAL,
        content_category=ContentCategory.OPERATION,
        keywords=["GC", "7890B", "Gas Chromatography", "User Manual"],
        search_tags=["gc", "7890b", "manual", "operation"]
    )
    
    # Create Lab Informatics metadata
    lab_metadata = manager.create_metadata(
        organization_mode=OrganizationMode.LAB_INFORMATICS,
        document_id="SSB-OLCDS-001",
        title="OpenLab CDS Database Connection Issues",
        filename="SSB_M84xx_KPR1476890N.html",
        file_type="HTML",
        file_size=51200,
        software_platform=ProductCategory.OPENLAB_CDS,
        software_version="2.8",
        document_type=DocumentType.SSB_KPR,
        content_category=ContentCategory.TROUBLESHOOTING,
        severity_level=SeverityLevel.HIGH,
        kpr_number="1476890N",
        keywords=["OpenLab", "CDS", "Database", "Connection", "Troubleshooting"],
        search_tags=["openlab", "cds", "database", "connection", "troubleshooting"]
    )
    
    # Search metadata
    general_results = manager.search_metadata(OrganizationMode.GENERAL)
    lab_results = manager.search_metadata(OrganizationMode.LAB_INFORMATICS)
    
    print(f"Found {len(general_results)} General Agilent documents")
    print(f"Found {len(lab_results)} Lab Informatics documents")
    
    # Export metadata
    manager.export_metadata("metadata_export.json")
    print("Metadata exported successfully")
