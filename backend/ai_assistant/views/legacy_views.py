"""
Legacy Views Module

This module contains legacy views for backward compatibility
including PDF documents, web links, and knowledge sharing.
"""

import logging
from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from ..models import PDFDocument, WebLink, KnowledgeShare, QueryHistory, UploadedFile, DocumentFile, DocumentChunk
from ..serializers import PDFDocumentSerializer, WebLinkSerializer, KnowledgeShareSerializer, QueryHistorySerializer
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Count, Q
from .base_views import (
    BaseViewMixin, success_response, error_response, bad_request_response,
    internal_error_response
)

logger = logging.getLogger(__name__)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def pdf_documents(request):
    """Legacy PDF documents endpoint"""
    try:
        BaseViewMixin.log_request(request, 'pdf_documents')
        
        if request.method == 'GET':
            # Get all PDF documents
            pdfs = PDFDocument.objects.all()
            serializer = PDFDocumentSerializer(pdfs, many=True, context={'request': request})
            
            BaseViewMixin.log_response({'pdfs': serializer.data}, 'pdf_documents')
            return success_response("PDF documents retrieved successfully", {'pdfs': serializer.data})
        
        elif request.method == 'POST':
            # Create new PDF document
            serializer = PDFDocumentSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                
                BaseViewMixin.log_response(serializer.data, 'pdf_documents')
                return success_response("PDF document created successfully", serializer.data)
            else:
                return bad_request_response(f"Validation error: {serializer.errors}")
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'pdf_documents')


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def web_links(request):
    """Legacy web links endpoint"""
    try:
        BaseViewMixin.log_request(request, 'web_links')
        
        if request.method == 'GET':
            # Get all web links
            links = WebLink.objects.all()
            serializer = WebLinkSerializer(links, many=True)
            
            BaseViewMixin.log_response({'links': serializer.data}, 'web_links')
            return success_response("Web links retrieved successfully", {'links': serializer.data})
        
        elif request.method == 'POST':
            # Create new web link
            serializer = WebLinkSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                
                BaseViewMixin.log_response(serializer.data, 'web_links')
                return success_response("Web link created successfully", serializer.data)
            else:
                return bad_request_response(f"Validation error: {serializer.errors}")
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'web_links')


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def knowledge_share(request):
    """Legacy knowledge sharing endpoint"""
    try:
        BaseViewMixin.log_request(request, 'knowledge_share')
        
        if request.method == 'GET':
            # Get all knowledge shares
            shares = KnowledgeShare.objects.all()
            serializer = KnowledgeShareSerializer(shares, many=True)
            
            BaseViewMixin.log_response({'shares': serializer.data}, 'knowledge_share')
            return success_response("Knowledge shares retrieved successfully", {'shares': serializer.data})
        
        elif request.method == 'POST':
            # Create new knowledge share
            serializer = KnowledgeShareSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                
                BaseViewMixin.log_response(serializer.data, 'knowledge_share')
                return success_response("Knowledge share created successfully", serializer.data)
            else:
                return bad_request_response(f"Validation error: {serializer.errors}")
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'knowledge_share')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_query_history(request):
    """Get query history for the authenticated user"""
    try:
        BaseViewMixin.log_request(request, 'get_query_history')
        
        # Get pagination parameters
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 50))
        
        # Get user's query history
        history = QueryHistory.objects.filter(user=request.user).order_by('-created_at')
        
        # Pagination
        start = (page - 1) * page_size
        end = start + page_size
        history_page = history[start:end]
        
        serializer = QueryHistorySerializer(history_page, many=True)
        
        return success_response(
            "Query history retrieved successfully",
            {
                'history': serializer.data,
                'total': history.count(),
                'page': page,
                'page_size': page_size
            }
        )
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'get_query_history')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_index_info(request):
    """Get index information and statistics"""
    try:
        BaseViewMixin.log_request(request, 'get_index_info')
        
        # Get statistics
        total_documents = DocumentFile.objects.count()
        total_chunks = DocumentChunk.objects.count()
        total_uploaded_files = UploadedFile.objects.count()
        
        # Get document type distribution
        doc_type_dist = DocumentFile.objects.values('document_type').annotate(count=Count('id'))
        
        # Get recent uploads
        recent_uploads = UploadedFile.objects.order_by('-uploaded_at')[:5]
        
        info = {
            'total_documents': total_documents,
            'total_chunks': total_chunks,
            'total_uploaded_files': total_uploaded_files,
            'document_type_distribution': list(doc_type_dist),
            'recent_uploads': [
                {
                    'filename': f.filename,
                    'file_size': f.file_size,
                    'page_count': f.page_count,
                    'uploaded_at': f.uploaded_at
                }
                for f in recent_uploads
            ]
        }
        
        return success_response("Index information retrieved successfully", info)
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'get_index_info')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_uploaded_files(request):
    """List all uploaded files with pagination"""
    try:
        BaseViewMixin.log_request(request, 'list_uploaded_files')
        
        # Get pagination parameters
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 50))
        
        # Get uploaded files
        files = UploadedFile.objects.all().order_by('-uploaded_at')
        
        # Pagination
        start = (page - 1) * page_size
        end = start + page_size
        files_page = files[start:end]
        
        file_data = [
            {
                'id': f.id,
                'filename': f.filename,
                'file_size': f.file_size,
                'page_count': f.page_count,
                'uploaded_at': f.uploaded_at,
                'intro': f.intro
            }
            for f in files_page
        ]
        
        return success_response(
            "Uploaded files retrieved successfully",
            {
                'files': file_data,
                'total': files.count(),
                'page': page,
                'page_size': page_size
            }
        )
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'list_uploaded_files')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_performance_stats(request):
    """Get performance statistics for the system"""
    try:
        BaseViewMixin.log_request(request, 'get_performance_stats')
        
        # Get cache stats
        cache_stats = cache.get('performance_stats', {})
        
        # Get database stats
        db_stats = {
            'total_documents': DocumentFile.objects.count(),
            'total_chunks': DocumentChunk.objects.count(),
            'total_history': QueryHistory.objects.count(),
            'total_files': UploadedFile.objects.count()
        }
        
        # Get recent performance metrics (if available)
        recent_queries = QueryHistory.objects.filter(
            created_at__gte=timezone.now() - timezone.timedelta(hours=24)
        ).count()
        
        stats = {
            'cache': cache_stats,
            'database': db_stats,
            'recent_queries_24h': recent_queries,
            'timestamp': timezone.now()
        }
        
        return success_response("Performance statistics retrieved successfully", stats)
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'get_performance_stats')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_search_analytics(request):
    """Get search analytics and statistics"""
    try:
        BaseViewMixin.log_request(request, 'get_search_analytics')
        
        # Get query type distribution
        query_types = QueryHistory.objects.values('query_type').annotate(count=Count('id'))
        
        # Get recent searches (last 7 days)
        recent_searches = QueryHistory.objects.filter(
            created_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).count()
        
        # Get top queries (most common searches)
        top_queries = QueryHistory.objects.values('query').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Get average response time (if cached)
        avg_response_time = cache.get('avg_response_time', 0.0)
        
        analytics = {
            'query_type_distribution': list(query_types),
            'recent_searches_7d': recent_searches,
            'top_queries': list(top_queries),
            'average_response_time': avg_response_time,
            'timestamp': timezone.now()
        }
        
        return success_response("Search analytics retrieved successfully", analytics)
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'get_search_analytics')
