"""
Product Views Module

This module contains views for fetching and managing documents by product category.
"""

import logging
import json
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from ..models import DocumentFile
from ..serializers import DocumentSerializer
from .base_views import (
    BaseViewMixin, success_response, error_response, bad_request_response
)

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_product_documents(request, product_category):
    """Get documents by product category with grouping and versioning"""
    try:
        BaseViewMixin.log_request(request, 'get_product_documents')
        
        # Get filter parameters
        show_latest_only = request.GET.get('latest_only', 'false').lower() == 'true'
        
        # Query documents with matching product category
        # Use proper JSON field lookup (Django auto-converts)
        documents = DocumentFile.objects.filter(
            metadata__product_category=product_category
        ).order_by('-uploaded_at')
        
        # Parse metadata and group documents
        grouped_docs = {}
        
        for doc in documents:
            try:
                metadata = json.loads(doc.metadata) if isinstance(doc.metadata, str) else doc.metadata
                content_type = metadata.get('content_type') or 'other'  # Treat empty string as None, then default to 'other'
                if not content_type or content_type.strip() == '':
                    content_type = 'other'
                
                # If showing latest only, filter by version
                if show_latest_only and metadata.get('version'):
                    # Get all documents with same content type for version comparison
                    documents_with_same_type = DocumentFile.objects.filter(
                        metadata__product_category=product_category,
                        metadata__content_type=content_type
                    )
                    
                    # Check if this is the latest version
                    is_latest = _is_latest_version(
                        documents_with_same_type,
                        metadata.get('version')
                    )
                    if not is_latest:
                        continue
                
                if content_type not in grouped_docs:
                    grouped_docs[content_type] = []
                
                grouped_docs[content_type].append({
                    'id': doc.id,
                    'title': doc.title,
                    'filename': doc.filename,
                    'version': metadata.get('version', 'N/A'),
                    'is_latest': True,  # TODO: Implement proper latest check
                    'file_size': doc.file_size,
                    'uploaded_at': doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                    'document_type': doc.document_type,
                    'metadata': metadata,
                    'download_url': f"/api/ai/documents/{doc.id}/download/",
                    'view_url': f"/api/ai/pdf/{doc.id}/view/?page=1" if doc.document_type == 'pdf' else None
                })
                
            except json.JSONDecodeError:
                logger.warning(f"Invalid metadata for document {doc.id}")
                continue
        
        # Sort groups by document count and within groups by version
        result_groups = []
        for content_type, docs in grouped_docs.items():
            # Sort documents by version (latest first)
            docs.sort(key=lambda x: _parse_version(x['version']), reverse=True)
            
            result_groups.append({
                'document_type': content_type,
                'display_name': _get_display_name(content_type),
                'total_count': len(docs),
                'documents': docs
            })
        
        # Sort groups by total_count (descending)
        result_groups.sort(key=lambda x: x['total_count'], reverse=True)
        
        result = {
            'product': product_category,
            'total_documents': sum(group['total_count'] for group in result_groups),
            'groups': result_groups
        }
        
        BaseViewMixin.log_response(result, 'get_product_documents')
        return success_response("Documents retrieved successfully", result)
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'get_product_documents')


def _is_latest_version(documents, current_version):
    """Check if current_version is the latest among all versions"""
    try:
        versions = []
        for doc in documents:
            metadata = json.loads(doc.metadata) if isinstance(doc.metadata, str) else doc.metadata
            version = metadata.get('version')
            if version:
                versions.append(_parse_version(version))
        
        if not versions:
            return True
        
        current_parsed = _parse_version(current_version)
        return current_parsed == max(versions)
        
    except Exception:
        return True


def _parse_version(version_str):
    """Parse version string to comparable tuple (e.g., '3.2.1' -> (3, 2, 1))"""
    if not version_str or version_str == 'N/A':
        return (0, 0, 0)
    
    try:
        parts = version_str.split('.')
        return tuple(int(part) for part in parts if part.isdigit())
    except (ValueError, AttributeError):
        return (0, 0, 0)


def _get_display_name(content_type):
    """Get display name for content type"""
    display_names = {
        'installation_guide': 'Installation & Setup',
        'user_manual': 'User Manuals',
        'configuration_guide': 'Configuration Guides',
        'troubleshooting_guide': 'Troubleshooting Guides',
        'maintenance_procedure': 'Maintenance Procedures',
        'calibration_procedure': 'Calibration Procedures',
        'best_practice_guide': 'Best Practice Guides',
        'video_tutorial': 'Video Tutorials',
        'webinar_recording': 'Webinar Recordings',
        'ssb_kpr': 'SSB/KPR',
        'other': 'Other Documents'
    }
    return display_names.get(content_type, content_type.replace('_', ' ').title())

