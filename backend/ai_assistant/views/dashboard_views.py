"""
Dashboard Views

Provides aggregated statistics for the main dashboard.
"""

import logging
from datetime import timedelta

from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import DocumentFile, DocumentChunk, UploadedFile, QueryHistory

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Return high-level dashboard statistics and recent activity."""
    try:
        now = timezone.now()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)

        # Documents
        total_docs = DocumentFile.objects.count()
        today_docs = DocumentFile.objects.filter(uploaded_at__gte=day_ago).count()
        week_docs = DocumentFile.objects.filter(uploaded_at__gte=week_ago).count()

        # Chunks
        total_chunks = DocumentChunk.objects.count()
        chunks_with_embeddings = DocumentChunk.objects.exclude(embedding__isnull=True).count()
        pending_chunks = max(0, total_chunks - chunks_with_embeddings)

        # RAG Queries
        total_queries = QueryHistory.objects.count()
        today_queries = QueryHistory.objects.filter(created_at__gte=day_ago).count()

        # Simple latency placeholder (use recorded metrics if available later)
        avg_latency_ms = 0

        # Processing queue
        pending = UploadedFile.objects.filter(processing_status='pending').count()
        processing = UploadedFile.objects.filter(processing_status__in=['metadata_extracting', 'chunking', 'embedding']).count()
        failed = UploadedFile.objects.filter(processing_status='failed').count()

        # Recent uploads
        recent_uploads_qs = (
            DocumentFile.objects.order_by('-uploaded_at')
            .values('id', 'title', 'filename', 'document_type', 'uploaded_at', 'file_size')[:10]
        )
        recent_uploads = [
            {
                'id': u['id'],
                'title': u['title'],
                'filename': u['filename'],
                'document_type': u['document_type'],
                'uploaded_at': u['uploaded_at'],
                'file_size': u['file_size'],
            }
            for u in recent_uploads_qs
        ]

        # Recent queries
        recent_queries_qs = (
            QueryHistory.objects.order_by('-created_at')
            .values('id', 'query', 'query_type', 'created_at')[:10]
        )
        recent_queries = [
            {
                'id': q['id'],
                'query': q['query'][:200],
                'query_type': q['query_type'],
                'created_at': q['created_at'],
            }
            for q in recent_queries_qs
        ]

        data = {
            'documents': {
                'total': total_docs,
                'today': today_docs,
                'last_7_days': week_docs,
            },
            'chunks': {
                'total': total_chunks,
                'with_embeddings': chunks_with_embeddings,
                'pending': pending_chunks,
            },
            'rag_queries': {
                'total': total_queries,
                'today': today_queries,
                'avg_response_time_ms': avg_latency_ms,
            },
            'processing_queue': {
                'pending': pending,
                'processing': processing,
                'failed': failed,
            },
            'recent_uploads': recent_uploads,
            'recent_queries': recent_queries,
        }

        return Response(data)
    except Exception as e:
        logger.exception("Error building dashboard stats")
        return Response({'error': 'Failed to load dashboard stats'}, status=500)


