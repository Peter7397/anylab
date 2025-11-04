"""
Website Management Views

This module provides API endpoints for managing external website sources
that are processed and integrated into the RAG system.
"""

import logging
from django.utils import timezone
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

from ..models import WebsiteSource
from ..serializers import WebsiteSourceSerializer, WebsiteSourceCreateSerializer
from ..website_processor import website_processor
from .base_views import BaseViewMixin

logger = logging.getLogger(__name__)


class WebsitePagination(PageNumberPagination):
    """Pagination for website list"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_website(request):
    """Add a new website source for processing"""
    try:
        BaseViewMixin.log_request(request, 'add_website')
        
        # Validate required fields
        required_fields = ['url']
        validation_error = BaseViewMixin.validate_required_fields(request.data, required_fields)
        if validation_error:
            return Response({'error': validation_error}, status=status.HTTP_400_BAD_REQUEST)
        
        # Use create serializer for validation
        serializer = WebsiteSourceCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            website_source = serializer.save()
            
            # Trigger processing via Celery task
            from .tasks import process_website_automatically
            process_website_automatically.delay(website_source.id)
            
            # Return full website data
            full_serializer = WebsiteSourceSerializer(website_source, context={'request': request})
            
            BaseViewMixin.log_response({'message': 'Website added successfully'}, 'add_website')
            return Response({
                'message': 'Website added successfully',
                'website': full_serializer.data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'add_website')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_websites(request):
    """List all website sources with optional filtering"""
    try:
        BaseViewMixin.log_request(request, 'list_websites')
        
        # Get query parameters
        status_filter = request.GET.get('status', 'all')
        domain_filter = request.GET.get('domain', '')
        search_query = request.GET.get('search', '')
        
        # Build queryset
        queryset = WebsiteSource.objects.all()
        
        # Apply filters
        if status_filter != 'all':
            queryset = queryset.filter(processing_status=status_filter)
        
        if domain_filter:
            queryset = queryset.filter(domain__icontains=domain_filter)
        
        if search_query:
            queryset = queryset.filter(
                Q(url__icontains=search_query) |
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Order by creation date (newest first)
        queryset = queryset.order_by('-created_at')
        
        # Paginate results
        paginator = WebsitePagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = WebsiteSourceSerializer(page, many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)
        
        # If no pagination
        serializer = WebsiteSourceSerializer(queryset, many=True, context={'request': request})
        
        BaseViewMixin.log_response({'count': len(serializer.data)}, 'list_websites')
        return Response({
            'websites': serializer.data,
            'count': len(serializer.data)
        })
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'list_websites')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_website_status(request, website_id):
    """Get processing status for a specific website"""
    try:
        BaseViewMixin.log_request(request, 'get_website_status')
        
        website_source = WebsiteSource.objects.get(id=website_id)
        serializer = WebsiteSourceSerializer(website_source, context={'request': request})
        
        BaseViewMixin.log_response({'status': website_source.processing_status}, 'get_website_status')
        return Response({
            'website': serializer.data,
            'status': website_source.processing_status,
            'is_ready': website_source.is_ready_for_search(),
            'progress_percentage': website_source.get_processing_progress()
        })
        
    except WebsiteSource.DoesNotExist:
        return Response({'error': 'Website not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'get_website_status')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refresh_website(request, website_id):
    """Manually refresh website content"""
    try:
        BaseViewMixin.log_request(request, 'refresh_website')
        
        website_source = WebsiteSource.objects.get(id=website_id)
        
        # Trigger refresh processing
        result = website_processor.refresh_website(website_id)
        
        if result['status'] == 'success':
            # Return updated website data
            website_source.refresh_from_db()
            serializer = WebsiteSourceSerializer(website_source, context={'request': request})
            
            BaseViewMixin.log_response({'message': 'Website refreshed successfully'}, 'refresh_website')
            return Response({
                'message': 'Website refreshed successfully',
                'website': serializer.data
            })
        else:
            return Response({
                'error': result.get('error', 'Refresh failed'),
                'details': result
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except WebsiteSource.DoesNotExist:
        return Response({'error': 'Website not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'refresh_website')


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_website(request, website_id):
    """Delete a website source and its associated data"""
    try:
        BaseViewMixin.log_request(request, 'delete_website')
        
        website_source = WebsiteSource.objects.get(id=website_id)
        
        # Delete associated chunks if any
        if website_source.uploaded_file:
            from .models import DocumentChunk
            DocumentChunk.objects.filter(uploaded_file=website_source.uploaded_file).delete()
            logger.info(f"Deleted chunks for UploadedFile {website_source.uploaded_file.id}")
        
        # Delete the website source
        website_source.delete()
        
        BaseViewMixin.log_response({'message': 'Website deleted successfully'}, 'delete_website')
        return Response({'message': 'Website deleted successfully'})
        
    except WebsiteSource.DoesNotExist:
        return Response({'error': 'Website not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'delete_website')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_website_statistics(request):
    """Get statistics about website sources"""
    try:
        BaseViewMixin.log_request(request, 'get_website_statistics')
        
        total_websites = WebsiteSource.objects.count()
        ready_websites = WebsiteSource.objects.filter(processing_status='ready').count()
        processing_websites = WebsiteSource.objects.filter(
            processing_status__in=['pending', 'fetching', 'metadata_extracting', 'chunking', 'embedding']
        ).count()
        failed_websites = WebsiteSource.objects.filter(processing_status='failed').count()
        
        # Get total chunks and embeddings
        total_chunks = sum(WebsiteSource.objects.values_list('chunk_count', flat=True))
        total_embeddings = sum(WebsiteSource.objects.values_list('embedding_count', flat=True))
        
        # Get domain distribution
        from django.db.models import Count
        domain_stats = WebsiteSource.objects.values('domain').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        statistics = {
            'total_websites': total_websites,
            'ready_websites': ready_websites,
            'processing_websites': processing_websites,
            'failed_websites': failed_websites,
            'total_chunks': total_chunks,
            'total_embeddings': total_embeddings,
            'domain_distribution': list(domain_stats),
            'success_rate': round((ready_websites / total_websites * 100) if total_websites > 0 else 0, 2)
        }
        
        BaseViewMixin.log_response({'total_websites': total_websites}, 'get_website_statistics')
        return Response(statistics)
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'get_website_statistics')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def retry_website_processing(request, website_id):
    """Retry processing for a failed website"""
    try:
        BaseViewMixin.log_request(request, 'retry_website_processing')
        
        website_source = WebsiteSource.objects.get(id=website_id)
        
        # Reset processing status
        website_source.processing_status = 'pending'
        website_source.processing_error = None
        website_source.processing_started_at = None
        website_source.processing_completed_at = None
        website_source.save()
        
        # Trigger processing via Celery task
        from .tasks import process_website_automatically
        process_website_automatically.delay(website_source.id)
        
        BaseViewMixin.log_response({'message': 'Website processing retry initiated'}, 'retry_website_processing')
        return Response({'message': 'Website processing retry initiated'})
        
    except WebsiteSource.DoesNotExist:
        return Response({'error': 'Website not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'retry_website_processing')


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_website_settings(request, website_id):
    """Update website settings (refresh interval, auto-refresh, etc.)"""
    try:
        BaseViewMixin.log_request(request, 'update_website_settings')
        
        website_source = WebsiteSource.objects.get(id=website_id)
        
        # Update allowed fields
        allowed_fields = ['title', 'description', 'auto_refresh', 'refresh_interval_days']
        for field in allowed_fields:
            if field in request.data:
                setattr(website_source, field, request.data[field])
        
        website_source.save()
        
        serializer = WebsiteSourceSerializer(website_source, context={'request': request})
        
        BaseViewMixin.log_response({'message': 'Website settings updated'}, 'update_website_settings')
        return Response({
            'message': 'Website settings updated',
            'website': serializer.data
        })
        
    except WebsiteSource.DoesNotExist:
        return Response({'error': 'Website not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'update_website_settings')
