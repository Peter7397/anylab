"""
Dynamic Content Filtering Architecture for AnyLab Document Management System

This module provides intelligent content filtering capabilities that adapt to both
General Agilent Products and Lab Informatics Focus modes, ensuring optimal
content discovery and RAG performance.
"""

from typing import Dict, List, Optional, Union, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import logging
from django.conf import settings
from django.core.cache import cache
from django.db.models import Q, F, Count, Avg, Max, Min
from django.utils import timezone

from .metadata_schema import (
    OrganizationMode, DocumentType, ProductCategory, 
    ContentCategory, SeverityLevel, DualModeMetadata
)
from .models import DocumentFile, DocumentChunk, UploadedFile

logger = logging.getLogger(__name__)


class FilterType(Enum):
    """Filter type enumeration"""
    TEXT_SEARCH = "text_search"
    CATEGORY_FILTER = "category_filter"
    DATE_RANGE = "date_range"
    FILE_TYPE = "file_type"
    PRODUCT_FILTER = "product_filter"
    SEVERITY_FILTER = "severity_filter"
    QUALITY_FILTER = "quality_filter"
    USAGE_FILTER = "usage_filter"
    SOURCE_FILTER = "source_filter"
    TAG_FILTER = "tag_filter"
    CUSTOM_FILTER = "custom_filter"


class SortOrder(Enum):
    """Sort order enumeration"""
    RELEVANCE = "relevance"
    DATE_NEWEST = "date_newest"
    DATE_OLDEST = "date_oldest"
    POPULARITY = "popularity"
    QUALITY_SCORE = "quality_score"
    ALPHABETICAL = "alphabetical"
    FILE_SIZE = "file_size"
    PAGE_COUNT = "page_count"


@dataclass
class FilterCriteria:
    """Filter criteria configuration"""
    filter_type: FilterType
    field_name: str
    operator: str  # equals, contains, starts_with, ends_with, greater_than, less_than, in, not_in
    value: Any
    weight: float = 1.0  # For relevance scoring
    required: bool = False  # Must match for inclusion


@dataclass
class SearchContext:
    """Search context for intelligent filtering"""
    organization_mode: OrganizationMode
    user_role: Optional[str] = None
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    search_history: List[str] = field(default_factory=list)
    current_page: str = ""
    session_id: Optional[str] = None
    device_type: str = "desktop"  # desktop, mobile, tablet


@dataclass
class FilterResult:
    """Filter result with metadata"""
    document_id: str
    relevance_score: float
    match_reasons: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    snippet: Optional[str] = None


class DynamicContentFilter:
    """Main content filtering engine"""
    
    def __init__(self):
        self.cache_timeout = 300  # 5 minutes
        self.max_results = 1000
        self.default_page_size = 20
        
    def filter_documents(self,
                        search_query: Optional[str] = None,
                        organization_mode: OrganizationMode = OrganizationMode.GENERAL,
                        filters: Optional[List[FilterCriteria]] = None,
                        sort_order: SortOrder = SortOrder.RELEVANCE,
                        page: int = 1,
                        page_size: Optional[int] = None,
                        context: Optional[SearchContext] = None) -> Dict[str, Any]:
        """
        Main filtering method that adapts to organization mode and user context
        """
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(
                search_query, organization_mode, filters, sort_order, page, page_size, context
            )
            
            # Check cache first
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.info(f"Returning cached filter results for key: {cache_key}")
                return cached_result
            
            # Build base queryset
            queryset = self._build_base_queryset(organization_mode)
            
            # Apply text search if provided
            if search_query:
                queryset = self._apply_text_search(queryset, search_query, organization_mode)
            
            # Apply filters
            if filters:
                queryset = self._apply_filters(queryset, filters, organization_mode)
            
            # Apply context-based filtering
            if context:
                queryset = self._apply_context_filtering(queryset, context)
            
            # Calculate relevance scores
            results = self._calculate_relevance_scores(
                queryset, search_query, organization_mode, context
            )
            
            # Sort results
            results = self._sort_results(results, sort_order)
            
            # Paginate results
            page_size = page_size or self.default_page_size
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            
            paginated_results = results[start_idx:end_idx]
            
            # Build response
            response = {
                'results': paginated_results,
                'total_count': len(results),
                'page': page,
                'page_size': page_size,
                'total_pages': (len(results) + page_size - 1) // page_size,
                'organization_mode': organization_mode.value,
                'applied_filters': [f.__dict__ for f in filters] if filters else [],
                'sort_order': sort_order.value,
                'search_query': search_query,
                'context': context.__dict__ if context else None,
                'generated_at': timezone.now().isoformat()
            }
            
            # Cache results
            cache.set(cache_key, response, self.cache_timeout)
            
            logger.info(f"Filtered {len(results)} documents for mode: {organization_mode.value}")
            return response
            
        except Exception as e:
            logger.error(f"Error in filter_documents: {e}")
            return {
                'results': [],
                'total_count': 0,
                'page': page,
                'page_size': page_size or self.default_page_size,
                'total_pages': 0,
                'organization_mode': organization_mode.value,
                'error': str(e),
                'generated_at': timezone.now().isoformat()
            }
    
    def _build_base_queryset(self, organization_mode: OrganizationMode):
        """Build base queryset based on organization mode"""
        if organization_mode == OrganizationMode.GENERAL:
            # For General Agilent Products, focus on product documentation
            return DocumentFile.objects.filter(
                document_type__in=[
                    DocumentType.USER_MANUAL.value,
                    DocumentType.TECHNICAL_SPECIFICATION.value,
                    DocumentType.INSTALLATION_GUIDE.value,
                    DocumentType.MAINTENANCE_GUIDE.value,
                    DocumentType.PRODUCT_CATALOG.value,
                    DocumentType.APPLICATION_NOTE.value,
                    DocumentType.WHITE_PAPER.value
                ]
            ).select_related('uploaded_by').prefetch_related('chunks')
        
        elif organization_mode == OrganizationMode.LAB_INFORMATICS:
            # For Lab Informatics, focus on software documentation and troubleshooting
            return DocumentFile.objects.filter(
                document_type__in=[
                    DocumentType.SSB_KPR.value,
                    DocumentType.TROUBLESHOOTING_GUIDE.value,
                    DocumentType.MAINTENANCE_PROCEDURE.value,
                    DocumentType.CALIBRATION_PROCEDURE.value,
                    DocumentType.CONFIGURATION_GUIDE.value,
                    DocumentType.BEST_PRACTICE_GUIDE.value,
                    DocumentType.COMMUNITY_SOLUTION.value,
                    DocumentType.VIDEO_TUTORIAL.value,
                    DocumentType.WEBINAR_RECORDING.value
                ]
            ).select_related('uploaded_by').prefetch_related('chunks')
        
        return DocumentFile.objects.all().select_related('uploaded_by').prefetch_related('chunks')
    
    def _apply_text_search(self, queryset, search_query: str, organization_mode: OrganizationMode):
        """Apply intelligent text search based on organization mode"""
        search_terms = search_query.lower().split()
        
        # Build search conditions
        search_conditions = Q()
        
        for term in search_terms:
            # Search in title, description, and content
            term_conditions = (
                Q(title__icontains=term) |
                Q(description__icontains=term) |
                Q(filename__icontains=term)
            )
            
            # Add mode-specific search fields
            if organization_mode == OrganizationMode.GENERAL:
                # Search in product-related fields
                term_conditions |= (
                    Q(document_type__icontains=term) |
                    Q(metadata__icontains=term)
                )
            elif organization_mode == OrganizationMode.LAB_INFORMATICS:
                # Search in software-related fields
                term_conditions |= (
                    Q(document_type__icontains=term) |
                    Q(metadata__icontains=term)
                )
            
            search_conditions &= term_conditions
        
        return queryset.filter(search_conditions)
    
    def _apply_filters(self, queryset, filters: List[FilterCriteria], organization_mode: OrganizationMode):
        """Apply filter criteria to queryset"""
        filter_conditions = Q()
        
        for filter_criteria in filters:
            field_name = filter_criteria.field_name
            operator = filter_criteria.operator
            value = filter_criteria.value
            
            # Build filter condition based on operator
            if operator == "equals":
                condition = Q(**{f"{field_name}": value})
            elif operator == "contains":
                condition = Q(**{f"{field_name}__icontains": value})
            elif operator == "starts_with":
                condition = Q(**{f"{field_name}__istartswith": value})
            elif operator == "ends_with":
                condition = Q(**{f"{field_name}__iendswith": value})
            elif operator == "greater_than":
                condition = Q(**{f"{field_name}__gt": value})
            elif operator == "less_than":
                condition = Q(**{f"{field_name}__lt": value})
            elif operator == "in":
                condition = Q(**{f"{field_name}__in": value})
            elif operator == "not_in":
                condition = ~Q(**{f"{field_name}__in": value})
            else:
                logger.warning(f"Unknown operator: {operator}")
                continue
            
            if filter_criteria.required:
                filter_conditions &= condition
            else:
                filter_conditions |= condition
        
        return queryset.filter(filter_conditions)
    
    def _apply_context_filtering(self, queryset, context: SearchContext):
        """Apply context-based filtering for personalized results"""
        context_conditions = Q()
        
        # User role-based filtering
        if context.user_role:
            if context.user_role == "admin":
                # Admins see all documents
                pass
            elif context.user_role == "expert":
                # Experts see high-quality documents
                context_conditions |= Q(metadata__contains='"quality_score": {"$gte": 0.8}')
            elif context.user_role == "beginner":
                # Beginners see basic documentation
                context_conditions |= Q(
                    document_type__in=[
                        DocumentType.USER_MANUAL.value,
                        DocumentType.INSTALLATION_GUIDE.value
                    ]
                )
        
        # User preferences
        if context.user_preferences:
            preferred_types = context.user_preferences.get('document_types', [])
            if preferred_types:
                context_conditions |= Q(document_type__in=preferred_types)
        
        # Search history relevance
        if context.search_history:
            # Boost documents that match previous search terms
            history_conditions = Q()
            for term in context.search_history[-5:]:  # Last 5 searches
                history_conditions |= Q(title__icontains=term)
            context_conditions |= history_conditions
        
        return queryset.filter(context_conditions)
    
    def _calculate_relevance_scores(self, queryset, search_query: Optional[str], 
                                   organization_mode: OrganizationMode, 
                                   context: Optional[SearchContext]) -> List[FilterResult]:
        """Calculate relevance scores for documents"""
        results = []
        
        for document in queryset:
            relevance_score = 0.0
            match_reasons = []
            
            # Base relevance from document metadata
            if hasattr(document, 'metadata') and document.metadata:
                try:
                    metadata = json.loads(document.metadata) if isinstance(document.metadata, str) else document.metadata
                    
                    # Quality score contribution
                    quality_score = metadata.get('quality_score', 0.5)
                    relevance_score += quality_score * 0.3
                    
                    # Usage score contribution
                    view_count = metadata.get('view_count', 0)
                    download_count = metadata.get('download_count', 0)
                    usage_score = min((view_count + download_count * 2) / 100, 1.0)
                    relevance_score += usage_score * 0.2
                    
                    # User rating contribution
                    user_rating = metadata.get('user_rating', 0.0)
                    relevance_score += user_rating * 0.2
                    
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # Search query relevance
            if search_query:
                search_terms = search_query.lower().split()
                title_matches = sum(1 for term in search_terms if term in document.title.lower())
                filename_matches = sum(1 for term in search_terms if term in document.filename.lower())
                
                query_relevance = (title_matches * 2 + filename_matches) / len(search_terms)
                relevance_score += query_relevance * 0.3
                
                if title_matches > 0:
                    match_reasons.append(f"Title matches {title_matches} search terms")
                if filename_matches > 0:
                    match_reasons.append(f"Filename matches {filename_matches} search terms")
            
            # Organization mode relevance
            if organization_mode == OrganizationMode.GENERAL:
                if document.document_type in [
                    DocumentType.USER_MANUAL.value,
                    DocumentType.TECHNICAL_SPECIFICATION.value,
                    DocumentType.PRODUCT_CATALOG.value
                ]:
                    relevance_score += 0.1
                    match_reasons.append("Product documentation")
            
            elif organization_mode == OrganizationMode.LAB_INFORMATICS:
                if document.document_type in [
                    DocumentType.SSB_KPR.value,
                    DocumentType.TROUBLESHOOTING_GUIDE.value,
                    DocumentType.CONFIGURATION_GUIDE.value
                ]:
                    relevance_score += 0.1
                    match_reasons.append("Software documentation")
            
            # Context relevance
            if context:
                if context.user_role == "expert" and document.document_type in [
                    DocumentType.TECHNICAL_SPECIFICATION.value,
                    DocumentType.BEST_PRACTICE_GUIDE.value
                ]:
                    relevance_score += 0.1
                    match_reasons.append("Expert-level content")
                
                if context.current_page and document.document_type in context.current_page:
                    relevance_score += 0.05
                    match_reasons.append("Context-relevant")
            
            # Normalize score
            relevance_score = min(relevance_score, 1.0)
            
            # Build metadata
            metadata = {
                'title': document.title,
                'filename': document.filename,
                'document_type': document.document_type,
                'file_size': document.file_size,
                'page_count': document.page_count,
                'created_at': document.created_at.isoformat() if document.created_at else None,
                'updated_at': document.updated_at.isoformat() if document.updated_at else None,
            }
            
            # Add mode-specific metadata
            if hasattr(document, 'metadata') and document.metadata:
                try:
                    doc_metadata = json.loads(document.metadata) if isinstance(document.metadata, str) else document.metadata
                    metadata.update(doc_metadata)
                except (json.JSONDecodeError, TypeError):
                    pass
            
            results.append(FilterResult(
                document_id=str(document.id),
                relevance_score=relevance_score,
                match_reasons=match_reasons,
                metadata=metadata,
                snippet=self._generate_snippet(document, search_query)
            ))
        
        return results
    
    def _sort_results(self, results: List[FilterResult], sort_order: SortOrder) -> List[FilterResult]:
        """Sort results based on sort order"""
        if sort_order == SortOrder.RELEVANCE:
            return sorted(results, key=lambda x: x.relevance_score, reverse=True)
        elif sort_order == SortOrder.DATE_NEWEST:
            return sorted(results, key=lambda x: x.metadata.get('updated_at', ''), reverse=True)
        elif sort_order == SortOrder.DATE_OLDEST:
            return sorted(results, key=lambda x: x.metadata.get('updated_at', ''))
        elif sort_order == SortOrder.POPULARITY:
            return sorted(results, key=lambda x: x.metadata.get('view_count', 0), reverse=True)
        elif sort_order == SortOrder.QUALITY_SCORE:
            return sorted(results, key=lambda x: x.metadata.get('quality_score', 0), reverse=True)
        elif sort_order == SortOrder.ALPHABETICAL:
            return sorted(results, key=lambda x: x.metadata.get('title', '').lower())
        elif sort_order == SortOrder.FILE_SIZE:
            return sorted(results, key=lambda x: x.metadata.get('file_size', 0), reverse=True)
        elif sort_order == SortOrder.PAGE_COUNT:
            return sorted(results, key=lambda x: x.metadata.get('page_count', 0), reverse=True)
        
        return results
    
    def _generate_snippet(self, document, search_query: Optional[str]) -> Optional[str]:
        """Generate a snippet for the document"""
        if not search_query:
            return document.description[:200] if document.description else None
        
        # Simple snippet generation - in a real implementation, this would be more sophisticated
        search_terms = search_query.lower().split()
        text_to_search = f"{document.title} {document.description or ''}".lower()
        
        for term in search_terms:
            if term in text_to_search:
                # Find the position of the term and extract surrounding text
                pos = text_to_search.find(term)
                start = max(0, pos - 50)
                end = min(len(text_to_search), pos + len(term) + 50)
                return text_to_search[start:end] + "..."
        
        return document.description[:200] if document.description else None
    
    def _generate_cache_key(self, search_query: Optional[str], organization_mode: OrganizationMode,
                           filters: Optional[List[FilterCriteria]], sort_order: SortOrder,
                           page: int, page_size: Optional[int], context: Optional[SearchContext]) -> str:
        """Generate cache key for filtering results"""
        key_parts = [
            f"filter_{organization_mode.value}",
            f"query_{search_query or 'none'}",
            f"sort_{sort_order.value}",
            f"page_{page}",
            f"size_{page_size or self.default_page_size}"
        ]
        
        if filters:
            filter_str = "_".join([f"{f.filter_type.value}_{f.field_name}_{f.operator}_{str(f.value)}" for f in filters])
            key_parts.append(f"filters_{filter_str}")
        
        if context:
            context_str = f"role_{context.user_role or 'none'}_session_{context.session_id or 'none'}"
            key_parts.append(f"context_{context_str}")
        
        return "_".join(key_parts)
    
    def get_filter_suggestions(self, organization_mode: OrganizationMode, 
                              partial_query: str = "") -> Dict[str, List[str]]:
        """Get filter suggestions based on organization mode and partial query"""
        suggestions = {
            'document_types': [],
            'product_categories': [],
            'tags': [],
            'recent_searches': []
        }
        
        try:
            # Get document type suggestions
            if organization_mode == OrganizationMode.GENERAL:
                suggestions['document_types'] = [
                    DocumentType.USER_MANUAL.value,
                    DocumentType.TECHNICAL_SPECIFICATION.value,
                    DocumentType.INSTALLATION_GUIDE.value,
                    DocumentType.MAINTENANCE_GUIDE.value,
                    DocumentType.PRODUCT_CATALOG.value,
                    DocumentType.APPLICATION_NOTE.value
                ]
            else:
                suggestions['document_types'] = [
                    DocumentType.SSB_KPR.value,
                    DocumentType.TROUBLESHOOTING_GUIDE.value,
                    DocumentType.MAINTENANCE_PROCEDURE.value,
                    DocumentType.CONFIGURATION_GUIDE.value,
                    DocumentType.BEST_PRACTICE_GUIDE.value,
                    DocumentType.COMMUNITY_SOLUTION.value
                ]
            
            # Get product category suggestions
            if organization_mode == OrganizationMode.GENERAL:
                suggestions['product_categories'] = [
                    ProductCategory.GAS_CHROMATOGRAPHY.value,
                    ProductCategory.LIQUID_CHROMATOGRAPHY.value,
                    ProductCategory.MASS_SPECTROMETRY.value,
                    ProductCategory.NMR_SYSTEMS.value,
                    ProductCategory.SPECTROSCOPY.value
                ]
            else:
                suggestions['product_categories'] = [
                    ProductCategory.OPENLAB_CDS.value,
                    ProductCategory.OPENLAB_ECM.value,
                    ProductCategory.OPENLAB_ELN.value,
                    ProductCategory.MASSHUNTER_WORKSTATION.value,
                    ProductCategory.MASSHUNTER_QUANTITATIVE.value,
                    ProductCategory.VNMRJ_CURRENT.value
                ]
            
            # Get recent searches from cache
            recent_searches = cache.get(f"recent_searches_{organization_mode.value}", [])
            suggestions['recent_searches'] = recent_searches[-10:]  # Last 10 searches
            
        except Exception as e:
            logger.error(f"Error getting filter suggestions: {e}")
        
        return suggestions
    
    def update_search_history(self, search_query: str, organization_mode: OrganizationMode):
        """Update search history for suggestions"""
        try:
            cache_key = f"recent_searches_{organization_mode.value}"
            recent_searches = cache.get(cache_key, [])
            
            # Add new search if not already present
            if search_query not in recent_searches:
                recent_searches.append(search_query)
                # Keep only last 20 searches
                recent_searches = recent_searches[-20:]
                cache.set(cache_key, recent_searches, 86400)  # 24 hours
            
        except Exception as e:
            logger.error(f"Error updating search history: {e}")


class FilterPresetManager:
    """Manager for saved filter presets"""
    
    def __init__(self):
        self.cache_timeout = 3600  # 1 hour
    
    def save_preset(self, preset_name: str, filters: List[FilterCriteria], 
                   organization_mode: OrganizationMode, user_id: Optional[str] = None) -> bool:
        """Save a filter preset"""
        try:
            preset_data = {
                'name': preset_name,
                'filters': [f.__dict__ for f in filters],
                'organization_mode': organization_mode.value,
                'created_at': timezone.now().isoformat(),
                'user_id': user_id
            }
            
            cache_key = f"filter_preset_{preset_name}_{organization_mode.value}_{user_id or 'global'}"
            cache.set(cache_key, preset_data, self.cache_timeout)
            
            # Also save to user's preset list
            if user_id:
                user_presets_key = f"user_presets_{user_id}_{organization_mode.value}"
                user_presets = cache.get(user_presets_key, [])
                if preset_name not in user_presets:
                    user_presets.append(preset_name)
                    cache.set(user_presets_key, user_presets, self.cache_timeout)
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving filter preset: {e}")
            return False
    
    def load_preset(self, preset_name: str, organization_mode: OrganizationMode, 
                   user_id: Optional[str] = None) -> Optional[List[FilterCriteria]]:
        """Load a filter preset"""
        try:
            cache_key = f"filter_preset_{preset_name}_{organization_mode.value}_{user_id or 'global'}"
            preset_data = cache.get(cache_key)
            
            if preset_data:
                filters = []
                for filter_dict in preset_data['filters']:
                    filters.append(FilterCriteria(**filter_dict))
                return filters
            
            return None
            
        except Exception as e:
            logger.error(f"Error loading filter preset: {e}")
            return None
    
    def list_presets(self, organization_mode: OrganizationMode, user_id: Optional[str] = None) -> List[str]:
        """List available presets"""
        try:
            if user_id:
                user_presets_key = f"user_presets_{user_id}_{organization_mode.value}"
                return cache.get(user_presets_key, [])
            else:
                # Return global presets
                return [
                    "Recent Documents",
                    "High Quality Documents",
                    "Troubleshooting Guides",
                    "User Manuals",
                    "Technical Specifications"
                ]
                
        except Exception as e:
            logger.error(f"Error listing presets: {e}")
            return []


# Example usage and testing
if __name__ == "__main__":
    # Create filter engine
    filter_engine = DynamicContentFilter()
    preset_manager = FilterPresetManager()
    
    # Example search context
    context = SearchContext(
        organization_mode=OrganizationMode.LAB_INFORMATICS,
        user_role="expert",
        user_preferences={"document_types": ["SSB_KPR", "TROUBLESHOOTING_GUIDE"]},
        search_history=["OpenLab CDS", "database connection"],
        current_page="/troubleshooting",
        session_id="session_123"
    )
    
    # Example filters
    filters = [
        FilterCriteria(
            filter_type=FilterType.DOCUMENT_TYPE,
            field_name="document_type",
            operator="in",
            value=["SSB_KPR", "TROUBLESHOOTING_GUIDE"],
            weight=1.0,
            required=True
        ),
        FilterCriteria(
            filter_type=FilterType.QUALITY_FILTER,
            field_name="quality_score",
            operator="greater_than",
            value=0.7,
            weight=0.8
        )
    ]
    
    # Perform search
    results = filter_engine.filter_documents(
        search_query="OpenLab CDS database connection",
        organization_mode=OrganizationMode.LAB_INFORMATICS,
        filters=filters,
        sort_order=SortOrder.RELEVANCE,
        page=1,
        page_size=10,
        context=context
    )
    
    print(f"Found {results['total_count']} documents")
    print(f"Results: {len(results['results'])}")
    
    # Get filter suggestions
    suggestions = filter_engine.get_filter_suggestions(OrganizationMode.LAB_INFORMATICS)
    print(f"Suggestions: {suggestions}")
    
    # Save filter preset
    preset_manager.save_preset(
        "OpenLab Troubleshooting",
        filters,
        OrganizationMode.LAB_INFORMATICS,
        "user_123"
    )
    
    print("Filter preset saved successfully")
