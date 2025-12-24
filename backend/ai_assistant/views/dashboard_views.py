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
from ..service_classes.neo4j_service import get_neo4j_service
from .base_views import forbidden_response

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Return high-level dashboard statistics and recent activity."""
    try:
        user = request.user
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

        # RAG Queries scoped to current user
        user_queries = QueryHistory.objects.filter(user=user)
        total_queries = user_queries.count()
        today_queries = user_queries.filter(created_at__gte=day_ago).count()

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
            user_queries.order_by('-created_at')
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

        # GraphRAG statistics
        try:
            neo4j = get_neo4j_service()
            graph_stats = neo4j.get_graph_stats()
            
            # Entity embedding coverage
            entity_stats_query = """
            MATCH (e:Entity)
            RETURN 
                count(e) AS total_entities,
                count(e.embedding) AS entities_with_embeddings,
                count(CASE WHEN e.embedding IS NULL THEN 1 END) AS entities_without_embeddings
            """
            entity_stats_result = neo4j.execute_query(entity_stats_query)
            entity_stats = entity_stats_result[0] if entity_stats_result else {}
            
            # GraphRAG query statistics
            user_graph_queries = user_queries.filter(query_type='graph_rag')
            graph_rag_queries_total = user_graph_queries.count()
            graph_rag_queries_today = user_graph_queries.filter(
                created_at__gte=day_ago
            ).count()
            
            # Recent GraphRAG queries
            recent_graph_queries_qs = (
                user_graph_queries
                .order_by('-created_at')
                .values('id', 'query', 'created_at')[:5]
            )
            recent_graph_queries = [
                {
                    'id': q['id'],
                    'query': q['query'][:200],
                    'created_at': q['created_at'],
                }
                for q in recent_graph_queries_qs
            ]
            
            # Entity type breakdown
            entity_type_stats = graph_stats.get('entity_types', {})
            
            # Calculate embedding coverage percentage
            total_ent = entity_stats.get('total_entities', 0)
            with_emb = entity_stats.get('entities_with_embeddings', 0)
            coverage_pct = (with_emb / total_ent * 100) if total_ent > 0 else 0
            
            graphrag_stats = {
                'entities': {
                    'total': total_ent,
                    'with_embeddings': with_emb,
                    'without_embeddings': entity_stats.get('entities_without_embeddings', 0),
                    'coverage_percentage': round(coverage_pct, 1),
                },
                'queries': {
                    'total': graph_rag_queries_total,
                    'today': graph_rag_queries_today,
                },
                'graph': {
                    'total_nodes': sum(node['count'] for node in graph_stats.get('nodes', [])),
                    'total_relationships': sum(rel['count'] for rel in graph_stats.get('relationships', [])),
                    'documents_in_graph': next((node['count'] for node in graph_stats.get('nodes', []) if node.get('label') == 'Document'), 0),
                },
                'entity_types': entity_type_stats,
                'recent_queries': recent_graph_queries,
            }
        except Exception as e:
            logger.warning(f"Could not fetch GraphRAG stats: {e}")
            graphrag_stats = {
                'entities': {'total': 0, 'with_embeddings': 0, 'without_embeddings': 0, 'coverage_percentage': 0},
                'queries': {'total': 0, 'today': 0},
                'graph': {'total_nodes': 0, 'total_relationships': 0, 'documents_in_graph': 0},
                'entity_types': {},
                'recent_queries': [],
            }

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
            'graphrag': graphrag_stats,
            'recent_uploads': recent_uploads,
            'recent_queries': recent_queries,
        }

        return Response(data)
    except Exception as e:
        logger.exception("Error building dashboard stats")
        return Response({'error': 'Failed to load dashboard stats'}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats_global(request):
    """Admin-only: Return global dashboard statistics and recent activity."""
    try:
        if not request.user.is_staff:
            return forbidden_response("Admin access required")
        
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

        # RAG Queries (global)
        total_queries = QueryHistory.objects.count()
        today_queries = QueryHistory.objects.filter(created_at__gte=day_ago).count()

        # Simple latency placeholder
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

        # Recent queries (global)
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

        # GraphRAG statistics (global)
        try:
            neo4j = get_neo4j_service()
            graph_stats = neo4j.get_graph_stats()
            
            entity_stats_query = """
            MATCH (e:Entity)
            RETURN 
                count(e) AS total_entities,
                count(e.embedding) AS entities_with_embeddings,
                count(CASE WHEN e.embedding IS NULL THEN 1 END) AS entities_without_embeddings
            """
            entity_stats_result = neo4j.execute_query(entity_stats_query)
            entity_stats = entity_stats_result[0] if entity_stats_result else {}
            
            graph_rag_queries_total = QueryHistory.objects.filter(query_type='graph_rag').count()
            graph_rag_queries_today = QueryHistory.objects.filter(
                query_type='graph_rag',
                created_at__gte=day_ago
            ).count()
            
            recent_graph_queries_qs = (
                QueryHistory.objects.filter(query_type='graph_rag')
                .order_by('-created_at')
                .values('id', 'query', 'created_at')[:5]
            )
            recent_graph_queries = [
                {
                    'id': q['id'],
                    'query': q['query'][:200],
                    'created_at': q['created_at'],
                }
                for q in recent_graph_queries_qs
            ]
            
            entity_type_stats = graph_stats.get('entity_types', {})
            total_ent = entity_stats.get('total_entities', 0)
            with_emb = entity_stats.get('entities_with_embeddings', 0)
            coverage_pct = (with_emb / total_ent * 100) if total_ent > 0 else 0
            
            graphrag_stats = {
                'entities': {
                    'total': total_ent,
                    'with_embeddings': with_emb,
                    'without_embeddings': entity_stats.get('entities_without_embeddings', 0),
                    'coverage_percentage': round(coverage_pct, 1),
                },
                'queries': {
                    'total': graph_rag_queries_total,
                    'today': graph_rag_queries_today,
                    'recent': recent_graph_queries,
                },
                'entity_types': entity_type_stats
            }
        except Exception as e:
            logger.warning(f"GraphRAG stats unavailable (global): {e}")
            graphrag_stats = {
                'entities': {'total': 0, 'with_embeddings': 0, 'without_embeddings': 0, 'coverage_percentage': 0},
                'queries': {'total': 0, 'today': 0, 'recent': []},
                'entity_types': {}
            }

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
            'graphrag': graphrag_stats,
            'recent_uploads': recent_uploads,
            'recent_queries': recent_queries,
        }

        return Response(data)
    except Exception as e:
        logger.exception("Error building global dashboard stats")
        return Response({'error': 'Failed to load global dashboard stats'}, status=500)
