"""
Content Service Module

This module provides service layer for content filtering and management
operations including document filtering, metadata management, and analytics.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from django.utils import timezone

from .base_service import BaseService
from ..models import DocumentFile
from ..content_filtering import DynamicContentFilter, FilterPresetManager, SearchContext, OrganizationMode, FilterCriteria, SortOrder

logger = logging.getLogger(__name__)


class ContentService(BaseService):
    """Service for content operations"""
    
    def __init__(self):
        super().__init__()
        self.filter_engine = DynamicContentFilter()
        self.preset_manager = FilterPresetManager()
    
    def filter_documents(self, search_query: str, organization_mode: str, 
                       filters_data: List[Dict[str, Any]], sort_order: str,
                       page: int = 1, page_size: int = 20, 
                       user_preferences: Dict[str, Any] = None,
                       **kwargs) -> Dict[str, Any]:
        """Filter documents based on search query, organization mode, and dynamic criteria"""
        try:
            self.log_operation('filter_documents', {
                'query_length': len(search_query),
                'organization_mode': organization_mode,
                'filters_count': len(filters_data),
                'page': page,
                'page_size': page_size
            })
            
            # Convert filters to FilterCriteria objects
            filters = []
            for filter_data in filters_data:
                filters.append(FilterCriteria(
                    field=filter_data.get('field'),
                    operator=filter_data.get('operator'),
                    value=filter_data.get('value')
                ))
            
            # Create search context
            context = SearchContext(
                organization_mode=OrganizationMode(organization_mode),
                user_role=kwargs.get('user_role', 'user'),
                user_preferences=user_preferences or {},
                search_history=kwargs.get('search_history', []),
                current_page=kwargs.get('current_page'),
                session_id=kwargs.get('session_id'),
                device_type=kwargs.get('device_type', 'desktop')
            )
            
            # Filter documents
            result = self.filter_engine.filter_documents(
                search_query=search_query,
                organization_mode=OrganizationMode(organization_mode),
                filters=filters,
                sort_order=SortOrder(sort_order),
                page=page,
                page_size=page_size,
                context=context
            )
            
            return self.success_response("Documents filtered successfully", result)
            
        except Exception as e:
            self.log_error('filter_documents', e)
            return self.error_response('Failed to filter documents')
    
    def get_filter_suggestions(self, organization_mode: str) -> Dict[str, Any]:
        """Get dynamic filter suggestions based on organization mode"""
        try:
            self.log_operation('get_filter_suggestions', {'organization_mode': organization_mode})
            
            # Get filter suggestions
            suggestions = self.filter_engine.get_filter_suggestions(OrganizationMode(organization_mode))
            
            return self.success_response("Filter suggestions retrieved successfully", suggestions)
            
        except Exception as e:
            self.log_error('get_filter_suggestions', e)
            return self.error_response('Failed to get filter suggestions')
    
    def save_filter_preset(self, preset_name: str, preset_data: Dict[str, Any], 
                          user_id: int) -> Dict[str, Any]:
        """Save a filter preset for future use"""
        try:
            self.log_operation('save_filter_preset', {
                'preset_name': preset_name,
                'user_id': user_id
            })
            
            if not preset_name:
                return self.error_response('Preset name is required')
            
            # Save preset
            preset_id = self.preset_manager.save_preset(
                name=preset_name,
                preset_data=preset_data,
                user_id=user_id
            )
            
            result = {
                'preset_id': preset_id,
                'name': preset_name,
                'preset_data': preset_data
            }
            
            return self.success_response("Filter preset saved successfully", result)
            
        except Exception as e:
            self.log_error('save_filter_preset', e)
            return self.error_response('Failed to save filter preset')
    
    def load_filter_preset(self, preset_id: str = None, preset_name: str = None, 
                          user_id: int = None) -> Dict[str, Any]:
        """Load a saved filter preset"""
        try:
            self.log_operation('load_filter_preset', {
                'preset_id': preset_id,
                'preset_name': preset_name,
                'user_id': user_id
            })
            
            if not preset_id and not preset_name:
                return self.error_response('Either preset_id or preset_name is required')
            
            # Load preset
            preset_data = self.preset_manager.load_preset(
                preset_id=preset_id,
                preset_name=preset_name,
                user_id=user_id
            )
            
            if not preset_data:
                return self.error_response("Preset not found")
            
            return self.success_response("Filter preset loaded successfully", preset_data)
            
        except Exception as e:
            self.log_error('load_filter_preset', e)
            return self.error_response('Failed to load filter preset')
    
    def list_filter_presets(self, user_id: int) -> Dict[str, Any]:
        """List all saved filter presets for the user"""
        try:
            self.log_operation('list_filter_presets', {'user_id': user_id})
            
            # List presets
            presets = self.preset_manager.list_presets(user_id=user_id)
            
            return self.success_response("Filter presets retrieved successfully", {
                'presets': presets
            })
            
        except Exception as e:
            self.log_error('list_filter_presets', e)
            return self.error_response('Failed to list filter presets')
    
    def get_document_metadata(self, document_id: int) -> Dict[str, Any]:
        """Get metadata for a specific document"""
        try:
            self.log_operation('get_document_metadata', {'document_id': document_id})
            
            if not document_id:
                return self.error_response('Document ID is required')
            
            # Get document
            try:
                document = DocumentFile.objects.get(id=document_id)
            except DocumentFile.DoesNotExist:
                return self.error_response("Document not found")
            
            # Parse metadata
            metadata = json.loads(document.metadata) if document.metadata else {}
            
            result = {
                'document_id': document.id,
                'title': document.title,
                'description': document.description,
                'document_type': document.document_type,
                'created_at': document.created_at.isoformat() if document.created_at else None,
                'updated_at': document.updated_at.isoformat() if document.updated_at else None,
                'metadata': metadata
            }
            
            return self.success_response("Document metadata retrieved successfully", result)
            
        except Exception as e:
            self.log_error('get_document_metadata', e)
            return self.error_response('Failed to get document metadata')
    
    def update_document_metadata(self, document_id: int, 
                                metadata_updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update metadata for a specific document"""
        try:
            self.log_operation('update_document_metadata', {
                'document_id': document_id,
                'updates_count': len(metadata_updates)
            })
            
            if not document_id:
                return self.error_response('Document ID is required')
            
            # Get document
            try:
                document = DocumentFile.objects.get(id=document_id)
            except DocumentFile.DoesNotExist:
                return self.error_response("Document not found")
            
            # Update metadata
            current_metadata = json.loads(document.metadata) if document.metadata else {}
            current_metadata.update(metadata_updates)
            document.metadata = json.dumps(current_metadata)
            document.save()
            
            result = {
                'document_id': document.id,
                'updated_metadata': current_metadata
            }
            
            return self.success_response("Document metadata updated successfully", result)
            
        except Exception as e:
            self.log_error('update_document_metadata', e)
            return self.error_response('Failed to update document metadata')
    
    def get_filter_analytics(self, organization_mode: str) -> Dict[str, Any]:
        """Get analytics for content filtering"""
        try:
            self.log_operation('get_filter_analytics', {'organization_mode': organization_mode})
            
            # Get analytics
            analytics = self.filter_engine.get_filter_analytics(OrganizationMode(organization_mode))
            
            return self.success_response("Filter analytics retrieved successfully", analytics)
            
        except Exception as e:
            self.log_error('get_filter_analytics', e)
            return self.error_response('Failed to get filter analytics')
