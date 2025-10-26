"""
Analytics Views Module

This module contains all analytics related views including
user behavior tracking, contribution analytics, and performance metrics.
"""

import logging
from django.db.models import Count, Avg, Max, Min, Q, F, Sum
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from datetime import datetime, timedelta

from ..models import DocumentFile, UploadedFile, QueryHistory, UserRole
from ..contribution_analytics_system import ContributionAnalyticsSystem
from ..user_behavior_tracking import UserBehaviorTracking
from .base_views import (
    BaseViewMixin, success_response, error_response
)

logger = logging.getLogger(__name__)

# Initialize analytics systems
contribution_analytics = ContributionAnalyticsSystem()
behavior_tracking = UserBehaviorTracking()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_statistics(request):
    """Get user statistics and activity metrics"""
    try:
        BaseViewMixin.log_request(request, 'get_user_statistics')
        
        user = request.user
        
        # Document upload stats
        documents_uploaded = DocumentFile.objects.filter(uploaded_by=user).count()
        total_file_size = DocumentFile.objects.filter(uploaded_by=user).aggregate(
            total=Sum('file_size')
        )['total'] or 0
        
        # Query history stats
        queries_count = QueryHistory.objects.filter(user=user).count()
        recent_queries = QueryHistory.objects.filter(user=user).order_by('-created_at')[:5]
        
        # Contributions by type
        contribution_stats = {
            'total_documents': documents_uploaded,
            'total_queries': queries_count,
            'total_file_size': total_file_size,
            'recent_documents': DocumentFile.objects.filter(uploaded_by=user).order_by('-uploaded_at')[:5].count(),
        }
        
        result = {
            'user_id': user.id,
            'username': user.username,
            'statistics': contribution_stats,
            'recent_activity': {
                'queries': [
                    {
                        'query': q.query[:100],
                        'type': q.query_type,
                        'created_at': q.created_at
                    } for q in recent_queries
                ]
            }
        }
        
        BaseViewMixin.log_response(result, 'get_user_statistics')
        return success_response("User statistics retrieved successfully", result)
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'get_user_statistics')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_contribution_analytics(request):
    """Get contribution analytics for current user"""
    try:
        BaseViewMixin.log_request(request, 'get_contribution_analytics')
        
        user = request.user
        
        # Get contribution patterns
        documents = DocumentFile.objects.filter(uploaded_by=user)
        
        # Contributions by type
        docs_by_type = documents.values('document_type').annotate(
            count=Count('id')
        )
        
        # Contributions by date
        docs_by_date = documents.extra(
            select={'date': 'DATE(uploaded_at)'}
        ).values('date').annotate(
            count=Count('id')
        ).order_by('-date')[:30]  # Last 30 days
        
        result = {
            'total_contributions': documents.count(),
            'by_type': list(docs_by_type),
            'by_date': list(docs_by_date),
            'latest_contribution': documents.order_by('-uploaded_at').first().uploaded_at if documents.exists() else None
        }
        
        BaseViewMixin.log_response(result, 'get_contribution_analytics')
        return success_response("Contribution analytics retrieved successfully", result)
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'get_contribution_analytics')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_performance_analytics(request):
    """Get performance analytics for RAG operations"""
    try:
        BaseViewMixin.log_request(request, 'get_performance_analytics')
        
        # Get query statistics
        queries = QueryHistory.objects.all()
        
        # Performance metrics
        recent_queries = queries.order_by('-created_at')[:100]
        
        avg_sources_count = recent_queries.aggregate(
            avg=Avg('length')
        )['avg'] or 0
        
        queries_by_type = queries.values('query_type').annotate(
            count=Count('id')
        )
        
        # Time-based metrics
        one_day_ago = timezone.now() - timedelta(days=1)
        seven_days_ago = timezone.now() - timedelta(days=7)
        
        recent_count = queries.filter(created_at__gte=one_day_ago).count()
        weekly_count = queries.filter(created_at__gte=seven_days_ago).count()
        
        result = {
            'total_queries': queries.count(),
            'recent_queries': recent_count,
            'weekly_queries': weekly_count,
            'by_type': list(queries_by_type),
            'avg_sources_per_query': round(avg_sources_count, 2)
        }
        
        BaseViewMixin.log_response(result, 'get_performance_analytics')
        return success_response("Performance analytics retrieved successfully", result)
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'get_performance_analytics')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_document_analytics(request):
    """Get document analytics"""
    try:
        BaseViewMixin.log_request(request, 'get_document_analytics')
        
        documents = DocumentFile.objects.all()
        
        # Documents by type
        docs_by_type = documents.values('document_type').annotate(
            count=Count('id')
        )
        
        # Total size by type
        total_size = documents.aggregate(
            total=Sum('file_size')
        )['total'] or 0
        
        # Recent uploads
        recent_uploads = documents.order_by('-uploaded_at')[:10]
        
        result = {
            'total_documents': documents.count(),
            'by_type': list(docs_by_type),
            'total_size': total_size,
            'recent_uploads': [
                {
                    'id': doc.id,
                    'title': doc.title,
                    'type': doc.document_type,
                    'uploaded_at': doc.uploaded_at,
                    'size': doc.file_size
                } for doc in recent_uploads
            ]
        }
        
        BaseViewMixin.log_response(result, 'get_document_analytics')
        return success_response("Document analytics retrieved successfully", result)
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'get_document_analytics')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_behavior_stats(request):
    """Get user behavior statistics"""
    try:
        BaseViewMixin.log_request(request, 'get_user_behavior_stats')
        
        user = request.user
        
        # Get query history
        queries = QueryHistory.objects.filter(user=user)
        
        # Query patterns
        queries_by_type = queries.values('query_type').annotate(
            count=Count('id')
        )
        
        # Recent activity
        one_day_ago = timezone.now() - timedelta(days=1)
        recent_queries = queries.filter(created_at__gte=one_day_ago).count()
        
        result = {
            'total_queries': queries.count(),
            'recent_queries': recent_queries,
            'by_type': list(queries_by_type),
            'avg_query_length': round(
                sum(len(q.query) for q in queries) / queries.count() if queries.exists() else 0, 
                2
            )
        }
        
        BaseViewMixin.log_response(result, 'get_user_behavior_stats')
        return success_response("User behavior stats retrieved successfully", result)
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'get_user_behavior_stats')

