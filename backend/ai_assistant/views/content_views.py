"""
Content Views Module

This module contains all content filtering and management related views
including document filtering, metadata management, and analytics.
"""

import logging
import json
from django.core.cache import cache
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from ..models import DocumentFile
from ..content_filtering import DynamicContentFilter, FilterPresetManager, SearchContext, OrganizationMode, FilterCriteria, SortOrder
from .base_views import (
    BaseViewMixin, success_response, error_response, bad_request_response,
    internal_error_response
)

logger = logging.getLogger(__name__)

# Initialize filter engine and preset manager
filter_engine = DynamicContentFilter()
preset_manager = FilterPresetManager()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def filter_documents(request):
    """Filter documents based on search query, organization mode, and dynamic criteria"""
    try:
        BaseViewMixin.log_request(request, 'filter_documents')
        
        # Get request parameters
        search_query = request.data.get('query', '').strip()
        organization_mode = request.data.get('organization_mode', 'general')
        filters_data = request.data.get('filters', [])
        sort_order = request.data.get('sort_order', 'relevance')
        page = int(request.data.get('page', 1))
        page_size = int(request.data.get('page_size', 20))
        
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
            user_role=getattr(request.user, 'role', 'user') if hasattr(request.user, 'role') else 'user',
            user_preferences=request.data.get('user_preferences', {}),
            search_history=request.data.get('search_history', []),
            current_page=request.data.get('current_page'),
            session_id=request.data.get('session_id'),
            device_type=request.data.get('device_type', 'desktop')
        )
        
        # Filter documents
        result = filter_engine.filter_documents(
            search_query=search_query,
            organization_mode=OrganizationMode(organization_mode),
            filters=filters,
            sort_order=SortOrder(sort_order),
            page=page,
            page_size=page_size,
            context=context
        )
        
        BaseViewMixin.log_response(result, 'filter_documents')
        return success_response("Documents filtered successfully", result)
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'filter_documents')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_filter_suggestions(request):
    """Get dynamic filter suggestions based on organization mode"""
    try:
        BaseViewMixin.log_request(request, 'get_filter_suggestions')
        
        organization_mode = request.GET.get('organization_mode', 'general')
        
        # Get filter suggestions
        suggestions = filter_engine.get_filter_suggestions(OrganizationMode(organization_mode))
        
        BaseViewMixin.log_response(suggestions, 'get_filter_suggestions')
        return success_response("Filter suggestions retrieved successfully", suggestions)
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'get_filter_suggestions')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_filter_preset(request):
    """Save a filter preset for future use"""
    try:
        BaseViewMixin.log_request(request, 'save_filter_preset')
        
        preset_name = request.data.get('name')
        preset_data = request.data.get('preset_data', {})
        
        if not preset_name:
            return bad_request_response('Preset name is required')
        
        # Save preset
        preset_id = preset_manager.save_preset(
            name=preset_name,
            preset_data=preset_data,
            user_id=request.user.id
        )
        
        result = {
            'preset_id': preset_id,
            'name': preset_name,
            'preset_data': preset_data
        }
        
        BaseViewMixin.log_response(result, 'save_filter_preset')
        return success_response("Filter preset saved successfully", result)
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'save_filter_preset')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def load_filter_preset(request):
    """Load a saved filter preset"""
    try:
        BaseViewMixin.log_request(request, 'load_filter_preset')
        
        preset_id = request.GET.get('preset_id')
        preset_name = request.GET.get('preset_name')
        
        if not preset_id and not preset_name:
            return bad_request_response('Either preset_id or preset_name is required')
        
        # Load preset
        preset_data = preset_manager.load_preset(
            preset_id=preset_id,
            preset_name=preset_name,
            user_id=request.user.id
        )
        
        if not preset_data:
            return error_response("Preset not found", status.HTTP_404_NOT_FOUND)
        
        BaseViewMixin.log_response(preset_data, 'load_filter_preset')
        return success_response("Filter preset loaded successfully", preset_data)
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'load_filter_preset')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_filter_presets(request):
    """List all saved filter presets for the user"""
    try:
        BaseViewMixin.log_request(request, 'list_filter_presets')
        
        # List presets
        presets = preset_manager.list_presets(user_id=request.user.id)
        
        BaseViewMixin.log_response(presets, 'list_filter_presets')
        return success_response("Filter presets retrieved successfully", {'presets': presets})
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'list_filter_presets')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_document_metadata(request):
    """Get metadata for a specific document"""
    try:
        BaseViewMixin.log_request(request, 'get_document_metadata')
        
        document_id = request.GET.get('document_id')
        if not document_id:
            return bad_request_response('Document ID is required')
        
        # Get document
        try:
            document = DocumentFile.objects.get(id=document_id)
        except DocumentFile.DoesNotExist:
            return error_response("Document not found", status.HTTP_404_NOT_FOUND)
        
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
        
        BaseViewMixin.log_response(result, 'get_document_metadata')
        return success_response("Document metadata retrieved successfully", result)
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'get_document_metadata')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_document_metadata(request):
    """Update metadata for a specific document"""
    try:
        BaseViewMixin.log_request(request, 'update_document_metadata')
        
        document_id = request.data.get('document_id')
        metadata_updates = request.data.get('metadata_updates', {})
        
        if not document_id:
            return bad_request_response('Document ID is required')
        
        # Get document
        try:
            document = DocumentFile.objects.get(id=document_id)
        except DocumentFile.DoesNotExist:
            return error_response("Document not found", status.HTTP_404_NOT_FOUND)
        
        # Update metadata
        current_metadata = json.loads(document.metadata) if document.metadata else {}
        current_metadata.update(metadata_updates)
        document.metadata = json.dumps(current_metadata)
        document.save()
        
        result = {
            'document_id': document.id,
            'updated_metadata': current_metadata
        }
        
        BaseViewMixin.log_response(result, 'update_document_metadata')
        return success_response("Document metadata updated successfully", result)
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'update_document_metadata')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_filter_analytics(request):
    """Get analytics for content filtering"""
    try:
        BaseViewMixin.log_request(request, 'get_filter_analytics')
        
        organization_mode = request.GET.get('organization_mode', 'general')
        
        # Get analytics
        analytics = filter_engine.get_filter_analytics(OrganizationMode(organization_mode))
        
        BaseViewMixin.log_response(analytics, 'get_filter_analytics')
        return success_response("Filter analytics retrieved successfully", analytics)
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'get_filter_analytics')
