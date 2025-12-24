"""
Django management command to reprocess existing documents with improved GraphRAG

This command rebuilds the knowledge graph for existing documents using the
enhanced entity extraction (LLM-based concepts, importance scoring, etc.)
"""

from django.core.management.base import BaseCommand
from django.db.models import Q
from ai_assistant.models import UploadedFile, DocumentChunk
from ai_assistant.service_classes.graph_builder import GraphBuilder
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Reprocess existing documents with improved GraphRAG entity extraction and importance scoring'

    def add_arguments(self, parser):
        parser.add_argument(
            '--document-id',
            type=int,
            help='Reprocess only a specific document ID',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=5,
            help='Number of documents to process per batch (default: 5, lower for LLM processing)',
        )
        parser.add_argument(
            '--status',
            type=str,
            default='ready',
            help='Only process documents with this status (default: ready). Use "any" to process all documents with chunks.',
        )
        parser.add_argument(
            '--any-status',
            action='store_true',
            help='Process documents with any status as long as they have chunks',
        )
        parser.add_argument(
            '--clear-graph',
            action='store_true',
            help='Clear existing graph data before reprocessing',
        )
        parser.add_argument(
            '--skip-llm',
            action='store_true',
            help='Skip LLM-based extraction (faster but less comprehensive)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without actually doing it',
        )

    def handle(self, *args, **options):
        document_id = options.get('document_id')
        batch_size = options.get('batch_size', 5)
        status = options.get('status', 'ready')
        any_status = options.get('any_status', False)
        clear_graph = options.get('clear_graph', False)
        skip_llm = options.get('skip_llm', False)
        dry_run = options.get('dry_run', False)

        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('GraphRAG Reprocessing with Improvements'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('')
        self.stdout.write('Improvements being applied:')
        self.stdout.write('  ✅ LLM-based concept extraction (unless --skip-llm)')
        self.stdout.write('  ✅ Importance scoring for chunks')
        self.stdout.write('  ✅ Enhanced entity types: CONCEPT, KEY_TERM, IMPORTANT_INFO, KEY_POINT')
        self.stdout.write('  ✅ Better query processing with semantic understanding')
        self.stdout.write('')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
            self.stdout.write('')

        # Initialize graph builder
        graph_builder = GraphBuilder()
        
        # Disable LLM extraction if requested
        if skip_llm:
            graph_builder.entity_extractor.use_llm_extraction = False
            self.stdout.write(self.style.WARNING('LLM extraction disabled (faster processing)'))
            self.stdout.write('')

        # Clear existing graph data if requested
        if clear_graph:
            if dry_run:
                self.stdout.write(self.style.WARNING('[DRY RUN] Would clear all existing graph data'))
            else:
                self.stdout.write(self.style.WARNING('Clearing existing graph data...'))
                try:
                    from ai_assistant.service_classes.neo4j_service import get_neo4j_service
                    neo4j = get_neo4j_service()
                    clear_query = "MATCH (n) DETACH DELETE n"
                    neo4j.execute_query(clear_query)
                    self.stdout.write(self.style.SUCCESS('  ✅ Existing graph data cleared'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ❌ Error clearing graph: {e}'))
                    return
            self.stdout.write('')

        # Get documents to process
        from django.db.models import Q, Exists, OuterRef
        from ai_assistant.models import DocumentChunk, DocumentFile
        
        if document_id:
            documents = UploadedFile.objects.filter(id=document_id)
        else:
            # First, try to find documents via DocumentFile -> UploadedFile relationship
            # Many documents are stored in DocumentFile but linked to UploadedFile
            doc_files_with_uploaded = DocumentFile.objects.exclude(uploaded_file__isnull=True)
            
            # Get UploadedFile IDs from DocumentFile
            uploaded_file_ids_from_docfiles = doc_files_with_uploaded.values_list('uploaded_file_id', flat=True).distinct()
            
            if any_status or status == 'any':
                # Process any document that has chunks, regardless of status
                # Include both direct UploadedFiles and those linked from DocumentFile
                documents = UploadedFile.objects.filter(
                    Q(Exists(DocumentChunk.objects.filter(uploaded_file=OuterRef('pk')))) |
                    Q(id__in=uploaded_file_ids_from_docfiles)
                ).order_by('id')
            else:
                # Process documents with specific status that have chunks
                documents = UploadedFile.objects.filter(
                    Q(processing_status=status) | 
                    Q(processing_status='ready') |
                    Q(id__in=uploaded_file_ids_from_docfiles)
                ).filter(
                    # Either chunks_created is True, OR document has actual chunks, OR linked from DocumentFile
                    Q(chunks_created=True) | 
                    Exists(DocumentChunk.objects.filter(uploaded_file=OuterRef('pk'))) |
                    Q(id__in=uploaded_file_ids_from_docfiles)
                ).distinct().order_by('id')
        
        total_docs = documents.count()
        self.stdout.write(f'Found {total_docs} document(s) to reprocess')
        
        if total_docs == 0:
            self.stdout.write(self.style.WARNING('No documents found to process'))
            self.stdout.write('')
            
            # Show what documents exist
            all_ready = UploadedFile.objects.filter(processing_status='ready').count()
            all_with_chunks = UploadedFile.objects.filter(chunks_created=True).count()
            all_with_actual_chunks = UploadedFile.objects.filter(
                id__in=DocumentChunk.objects.values_list('uploaded_file_id', flat=True).distinct()
            ).count()
            
            self.stdout.write(f'Debug info:')
            self.stdout.write(f'  - Documents with status "ready": {all_ready}')
            self.stdout.write(f'  - Documents with chunks_created=True: {all_with_chunks}')
            self.stdout.write(f'  - Documents with actual chunks: {all_with_actual_chunks}')
            self.stdout.write('')
            self.stdout.write('Tips:')
            self.stdout.write('  - Check document status: python manage.py check_pdf_status')
            self.stdout.write('  - Process specific document: --document-id <ID>')
            self.stdout.write('  - Check processing status in admin interface')
            self.stdout.write('  - If documents show as ready but not found, try: --status ready')
            return

        if dry_run:
            self.stdout.write('')
            self.stdout.write('Documents that would be processed:')
            for doc in documents[:10]:  # Show first 10
                chunk_count = DocumentChunk.objects.filter(uploaded_file=doc).count()
                self.stdout.write(f'  - ID {doc.id}: {doc.filename} ({chunk_count} chunks)')
            if total_docs > 10:
                self.stdout.write(f'  ... and {total_docs - 10} more')
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('Dry run complete. Run without --dry-run to process.'))
            return

        # Process in batches
        processed = 0
        successful = 0
        failed = 0
        total_entities = 0
        total_relationships = 0

        self.stdout.write('')
        self.stdout.write('Starting reprocessing...')
        self.stdout.write('')

        for i in range(0, total_docs, batch_size):
            batch = documents[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_docs + batch_size - 1) // batch_size
            
            self.stdout.write(f'Batch {batch_num}/{total_batches} ({len(batch)} documents)')
            self.stdout.write('-' * 70)
            
            for uploaded_file in batch:
                try:
                    self.stdout.write(f'Processing: {uploaded_file.filename} (ID: {uploaded_file.id})...')
                    
                    # Get chunks for this document
                    chunks = DocumentChunk.objects.filter(uploaded_file=uploaded_file)
                    chunk_count = chunks.count()
                    
                    if chunk_count == 0:
                        self.stdout.write(
                            self.style.WARNING(f'  ⚠️  No chunks found for {uploaded_file.filename}')
                        )
                        failed += 1
                        processed += 1
                        continue
                    
                    self.stdout.write(f'  Found {chunk_count} chunks')
                    
                    # Clear existing graph data for this document
                    try:
                        from ai_assistant.service_classes.neo4j_service import get_neo4j_service
                        neo4j = get_neo4j_service()
                        clear_doc_query = """
                        MATCH (d:Document {id: $doc_id})-[r]-()
                        DELETE r, d
                        """
                        neo4j.execute_query(clear_doc_query, {'doc_id': str(uploaded_file.id)})
                        self.stdout.write('  Cleared existing graph data for this document')
                    except Exception as e:
                        logger.warning(f"Could not clear existing graph for doc {uploaded_file.id}: {e}")
                    
                    # Build graph with improved extraction
                    self.stdout.write('  Extracting entities (this may take a moment with LLM)...')
                    result = graph_builder.build_graph_from_document(uploaded_file, list(chunks))
                    
                    if result.get('success'):
                        entity_count = result.get('entities_extracted', 0)
                        relationship_count = result.get('relationships_created', 0)
                        total_entities += entity_count
                        total_relationships += relationship_count
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✅ Success: {entity_count} entities extracted, '
                                f'{relationship_count} relationships created'
                            )
                        )
                        
                        # Show improvement indicators
                        if entity_count > 10:
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
                    self.stdout.write('')
                    
                except Exception as e:
                    logger.error(f"Error processing document {uploaded_file.id}: {e}", exc_info=True)
                    self.stdout.write(
                        self.style.ERROR(f'  ❌ Error: {str(e)}')
                    )
                    failed += 1
                    processed += 1
                    self.stdout.write('')

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('Reprocessing Summary'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(f'  Total documents: {total_docs}')
        self.stdout.write(f'  Processed: {processed}')
        self.stdout.write(self.style.SUCCESS(f'  Successful: {successful}'))
        self.stdout.write(self.style.ERROR(f'  Failed: {failed}'))
        self.stdout.write('')
        self.stdout.write(f'  Total entities extracted: {total_entities}')
        self.stdout.write(f'  Total relationships created: {total_relationships}')
        self.stdout.write('')
        
        # Get final graph statistics
        try:
            stats = graph_builder.get_graph_statistics()
            self.stdout.write(self.style.SUCCESS('Final Graph Statistics:'))
            self.stdout.write(f'  Total nodes: {stats.get("total_nodes", 0)}')
            self.stdout.write(f'  Total relationships: {stats.get("total_relationships", 0)}')
            self.stdout.write('')
        except Exception as e:
            logger.warning(f"Could not get graph statistics: {e}")
        
        self.stdout.write(self.style.SUCCESS('✅ Reprocessing complete!'))
        self.stdout.write('')
        self.stdout.write('Next steps:')
        self.stdout.write('  - Test queries to see improved results')
        self.stdout.write('  - Check graph visualization in admin interface')
        self.stdout.write('  - Monitor query performance improvements')

