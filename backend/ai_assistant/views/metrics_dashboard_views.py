"""
Metrics Dashboard API Views

Provides API endpoints for dashboard metrics including:
- Processing success rates
- Processing times
- File counts
- Error rates
- System performance metrics
"""

import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone
from datetime import timedelta
from ai_assistant.models import UploadedFile, DocumentChunk, QueryHistory
import psutil

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_processing_metrics(request):
    """
    Get processing metrics for dashboard.
    
    Query parameters:
    - hours: Time window in hours (default: 24)
    - include_system: Include system metrics (default: true)
    """
    try:
        hours = int(request.query_params.get('hours', 24))
        include_system = request.query_params.get('include_system', 'true').lower() == 'true'
        
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        # Processing statistics
        total_files = UploadedFile.objects.filter(uploaded_at__gte=cutoff_time).count()
        processed_files = UploadedFile.objects.filter(
            uploaded_at__gte=cutoff_time,
            processing_status='ready'
        ).count()
        failed_files = UploadedFile.objects.filter(
            uploaded_at__gte=cutoff_time,
            processing_status__in=['failed', 'corrupted']
        ).count()
        pending_files = UploadedFile.objects.filter(
            uploaded_at__gte=cutoff_time,
            processing_status='pending'
        ).count()
        
        # Calculate success rate
        success_rate = (processed_files / total_files * 100) if total_files > 0 else 0
        failure_rate = (failed_files / total_files * 100) if total_files > 0 else 0
        
        # Processing time statistics
        completed_files = UploadedFile.objects.filter(
            uploaded_at__gte=cutoff_time,
            processing_status='ready',
            processing_completed_at__isnull=False,
            processing_started_at__isnull=False
        )
        
        processing_times = []
        for file in completed_files:
            if file.processing_started_at and file.processing_completed_at:
                duration = (file.processing_completed_at - file.processing_started_at).total_seconds()
                processing_times.append(duration)
        
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        min_processing_time = min(processing_times) if processing_times else 0
        max_processing_time = max(processing_times) if processing_times else 0
        
        # File size statistics
        file_size_stats = UploadedFile.objects.filter(
            uploaded_at__gte=cutoff_time
        ).aggregate(
            total_size=Sum('file_size'),
            avg_size=Avg('file_size'),
            count=Count('id')
        )
        
        # Chunk and embedding statistics
        chunks_count = DocumentChunk.objects.filter(
            uploaded_file__uploaded_at__gte=cutoff_time
        ).count()
        
        embeddings_count = DocumentChunk.objects.filter(
            uploaded_file__uploaded_at__gte=cutoff_time
        ).exclude(embedding__isnull=True).exclude(embedding='[]').count()
        
        # Error breakdown
        error_breakdown = UploadedFile.objects.filter(
            uploaded_at__gte=cutoff_time,
            processing_error__isnull=False
        ).values('processing_status').annotate(
            count=Count('id')
        )
        
        metrics = {
            'time_window_hours': hours,
            'timestamp': timezone.now().isoformat(),
            'processing': {
                'total_files': total_files,
                'processed_files': processed_files,
                'failed_files': failed_files,
                'pending_files': pending_files,
                'success_rate': round(success_rate, 2),
                'failure_rate': round(failure_rate, 2),
            },
            'processing_time': {
                'average_seconds': round(avg_processing_time, 2),
                'min_seconds': round(min_processing_time, 2),
                'max_seconds': round(max_processing_time, 2),
                'samples': len(processing_times),
            },
            'file_sizes': {
                'total_bytes': file_size_stats['total_size'] or 0,
                'total_mb': round((file_size_stats['total_size'] or 0) / (1024 * 1024), 2),
                'average_bytes': round(file_size_stats['avg_size'] or 0, 2),
                'average_mb': round((file_size_stats['avg_size'] or 0) / (1024 * 1024), 2),
            },
            'content': {
                'total_chunks': chunks_count,
                'total_embeddings': embeddings_count,
                'chunks_per_file': round(chunks_count / total_files, 2) if total_files > 0 else 0,
            },
            'errors': {
                'breakdown': list(error_breakdown),
                'total_errors': failed_files,
            },
        }
        
        # System metrics (optional)
        if include_system:
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                metrics['system'] = {
                    'cpu_percent': round(cpu_percent, 2),
                    'memory': {
                        'percent': round(memory.percent, 2),
                        'used_gb': round(memory.used / (1024 ** 3), 2),
                        'total_gb': round(memory.total / (1024 ** 3), 2),
                    },
                    'disk': {
                        'percent': round(disk.percent, 2),
                        'used_gb': round(disk.used / (1024 ** 3), 2),
                        'total_gb': round(disk.total / (1024 ** 3), 2),
                    },
                }
            except Exception as e:
                logger.warning(f"Failed to get system metrics: {e}")
                metrics['system'] = {'error': 'Unable to retrieve system metrics'}
        
        return Response(metrics, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting processing metrics: {e}", exc_info=True)
        return Response(
            {'error': 'Failed to retrieve metrics', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_processing_timeline(request):
    """
    Get processing metrics over time for timeline visualization.
    
    Query parameters:
    - hours: Time window in hours (default: 24)
    - interval: Aggregation interval in hours (default: 1)
    """
    try:
        hours = int(request.query_params.get('hours', 24))
        interval_hours = int(request.query_params.get('interval', 1))
        
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        # Generate time buckets
        timeline = []
        current_time = cutoff_time
        
        while current_time < timezone.now():
            bucket_end = current_time + timedelta(hours=interval_hours)
            
            # Count files in this time bucket
            bucket_files = UploadedFile.objects.filter(
                uploaded_at__gte=current_time,
                uploaded_at__lt=bucket_end
            )
            
            total = bucket_files.count()
            processed = bucket_files.filter(processing_status='ready').count()
            failed = bucket_files.filter(processing_status__in=['failed', 'corrupted']).count()
            pending = bucket_files.filter(processing_status='pending').count()
            
            timeline.append({
                'timestamp': current_time.isoformat(),
                'time_bucket': f"{current_time.strftime('%Y-%m-%d %H:%M')} - {bucket_end.strftime('%H:%M')}",
                'total_files': total,
                'processed_files': processed,
                'failed_files': failed,
                'pending_files': pending,
                'success_rate': round((processed / total * 100) if total > 0 else 0, 2),
            })
            
            current_time = bucket_end
        
        return Response({
            'time_window_hours': hours,
            'interval_hours': interval_hours,
            'timeline': timeline,
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting processing timeline: {e}", exc_info=True)
        return Response(
            {'error': 'Failed to retrieve timeline', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_error_summary(request):
    """
    Get error summary for dashboard.
    
    Query parameters:
    - hours: Time window in hours (default: 24)
    - limit: Maximum number of error samples to return (default: 20)
    """
    try:
        hours = int(request.query_params.get('hours', 24))
        limit = int(request.query_params.get('limit', 20))
        
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        # Get files with errors
        error_files = UploadedFile.objects.filter(
            uploaded_at__gte=cutoff_time,
            processing_error__isnull=False
        ).exclude(processing_status='ready').order_by('-uploaded_at')[:limit]
        
        # Error type breakdown
        error_types = {}
        for file in error_files:
            error_type = file.processing_status
            if error_type not in error_types:
                error_types[error_type] = {
                    'count': 0,
                    'samples': [],
                }
            error_types[error_type]['count'] += 1
            if len(error_types[error_type]['samples']) < 5:
                error_types[error_type]['samples'].append({
                    'filename': file.filename,
                    'error': file.processing_error[:200],  # Truncate long errors
                    'timestamp': file.uploaded_at.isoformat(),
                })
        
        return Response({
            'time_window_hours': hours,
            'error_breakdown': error_types,
            'total_errors': sum(et['count'] for et in error_types.values()),
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting error summary: {e}", exc_info=True)
        return Response(
            {'error': 'Failed to retrieve error summary', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

