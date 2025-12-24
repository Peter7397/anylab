"""
Django management command to build Neo4j graph from existing documents
"""

from django.core.management.base import BaseCommand
from django.db.models import Q
from ai_assistant.models import UploadedFile, DocumentChunk
from ai_assistant.services.graph_builder import GraphBuilder
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Build Neo4j knowledge graph from existing documents'

    def add_arguments(self, parser):
        parser.add_argument(
            '--document-id',
            type=int,
            help='Process only a specific document ID',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Number of documents to process per batch (default: 10)',
        )
        parser.add_argument(
            '--status',
            type=str,
            default='ready',
            help='Only process documents with this status (default: ready)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Rebuild graph even if document already has graph data (clears existing graph data)',
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing graph data before rebuilding (use with --force)',
        )

    def handle(self, *args, **options):
        document_id = options.get('document_id')
        batch_size = options.get('batch_size', 10)
        status = options.get('status', 'ready')
        force = options.get('force', False)

        self.stdout.write(self.style.SUCCESS('Starting graph construction with improved entity extraction...'))
        self.stdout.write('  - LLM-based concept extraction: Enabled')
        self.stdout.write('  - Importance scoring: Enabled')
        self.stdout.write('  - Enhanced entity types: CONCEPT, KEY_TERM, IMPORTANT_INFO, etc.')

        # Initialize graph builder
        graph_builder = GraphBuilder()
        
        # Clear existing graph data if requested
        clear_existing = options.get('clear_existing', False)
        if clear_existing:
            self.stdout.write(self.style.WARNING('Clearing existing graph data...'))
            try:
                from ai_assistant.services.neo4j_service import get_neo4j_service
                neo4j = get_neo4j_service()
                # Clear all graph data
                clear_query = "MATCH (n) DETACH DELETE n"
                neo4j.execute_query(clear_query)
                self.stdout.write(self.style.SUCCESS('  ✅ Existing graph data cleared'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ❌ Error clearing graph: {e}'))
                if not force:
                    return

        # Get documents to process
        if document_id:
            documents = UploadedFile.objects.filter(id=document_id)
        else:
            # Process documents that are ready for search
            documents = UploadedFile.objects.filter(
                processing_status=status,
                chunks_created=True
            )
        
        total_docs = documents.count()
        self.stdout.write(f'Found {total_docs} document(s) to process')

        if total_docs == 0:
            self.stdout.write(self.style.WARNING('No documents found to process'))
            return

        # Process in batches
        processed = 0
        successful = 0
        failed = 0

        for i in range(0, total_docs, batch_size):
            batch = documents[i:i + batch_size]
            
            for uploaded_file in batch:
                try:
                    self.stdout.write(f'Processing: {uploaded_file.filename} (ID: {uploaded_file.id})...')
                    
                    # Get chunks for this document
                    chunks = DocumentChunk.objects.filter(uploaded_file=uploaded_file)
                    
                    if not chunks.exists():
                        self.stdout.write(
                            self.style.WARNING(f'  ⚠️  No chunks found for {uploaded_file.filename}')
                        )
                        failed += 1
                        continue
                    
                    # Clear existing graph data for this document if force is enabled
                    if force:
                        try:
                            from ai_assistant.services.neo4j_service import get_neo4j_service
                            neo4j = get_neo4j_service()
                            clear_doc_query = "MATCH (d:Document {id: $doc_id})-[r]-() DELETE r, d"
                            neo4j.execute_query(clear_doc_query, {'doc_id': str(uploaded_file.id)})
                        except Exception as e:
                            logger.warning(f"Could not clear existing graph for doc {uploaded_file.id}: {e}")
                    
                    # Build graph with improved extraction
                    result = graph_builder.build_graph_from_document(uploaded_file, list(chunks))
                    
                    if result.get('success'):
                        entity_count = result.get('entities_extracted', 0)
                        relationship_count = result.get('relationships_created', 0)
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✅ Success: {entity_count} entities extracted, '
                                f'{relationship_count} relationships created'
                            )
                        )
                        # Show entity type breakdown if available
                        if entity_count > 0:
                            self.stdout.write(
                                f'     (Includes concepts, key terms, and important information)'
                            )
                        successful += 1
                    else:
                        self.stdout.write(
                            self.style.ERROR(f'  ❌ Failed: {result.get("error", "Unknown error")}')
                        )
                        failed += 1
                    
                    processed += 1
                    
                except Exception as e:
                    logger.error(f"Error processing document {uploaded_file.id}: {e}", exc_info=True)
                    self.stdout.write(
                        self.style.ERROR(f'  ❌ Error: {str(e)}')
                    )
                    failed += 1
                    processed += 1

        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 50))
        self.stdout.write(self.style.SUCCESS('Graph Construction Summary:'))
        self.stdout.write(f'  Total documents: {total_docs}')
        self.stdout.write(f'  Processed: {processed}')
        self.stdout.write(self.style.SUCCESS(f'  Successful: {successful}'))
        self.stdout.write(self.style.ERROR(f'  Failed: {failed}'))
        
        # Get final graph statistics
        stats = graph_builder.get_graph_statistics()
        self.stdout.write(self.style.SUCCESS('\nGraph Statistics:'))
        self.stdout.write(f'  Total nodes: {stats["total_nodes"]}')
        self.stdout.write(f'  Total relationships: {stats["total_relationships"]}')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Graph construction complete!'))

