import logging
from django.core.management.base import BaseCommand
from ai_assistant.models import DocumentChunk
from ai_assistant.rag_service import EnhancedRAGService

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Add embeddings to existing document chunks for better search functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reprocessing even if embeddings already exist',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without actually doing it',
        )
        parser.add_argument(
            '--chunk-id',
            type=int,
            help='Process only a specific chunk ID',
        )

    def handle(self, *args, **options):
        force = options['force']
        dry_run = options['dry_run']
        chunk_id = options['chunk_id']
        
        self.stdout.write(
            self.style.SUCCESS('Starting embedding generation...')
        )
        
        # Initialize RAG service
        rag_service = EnhancedRAGService()
        
        # Get chunks that need embeddings
        chunks_query = DocumentChunk.objects.all()
        if chunk_id:
            chunks_query = chunks_query.filter(id=chunk_id)
        
        if not force:
            chunks_query = chunks_query.filter(embedding__isnull=True)
        
        chunks = list(chunks_query)
        
        self.stdout.write(f"Found {len(chunks)} chunks to process")
        
        if dry_run:
            self.stdout.write("DRY RUN - No embeddings will be generated")
            for chunk in chunks[:10]:  # Show first 10
                self.stdout.write(f"  - {chunk.uploaded_file.filename if chunk.uploaded_file else 'Unknown'} - Page {chunk.page_number}")
            if len(chunks) > 10:
                self.stdout.write(f"  ... and {len(chunks) - 10} more")
            return
        
        processed_count = 0
        error_count = 0
        
        for chunk in chunks:
            try:
                self.stdout.write(f"Processing chunk {chunk.id}: {chunk.uploaded_file.filename if chunk.uploaded_file else 'Unknown'} - Page {chunk.page_number}")
                
                # Generate embedding
                embedding = rag_service.get_embedding_from_ollama(chunk.content)
                
                # Update chunk
                chunk.embedding = embedding
                chunk.save()
                
                processed_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ Successfully processed")
                )
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"  ✗ Error processing chunk {chunk.id}: {str(e)}")
                )
                logger.error(f"Error processing chunk {chunk.id}: {e}")
        
        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write(
            self.style.SUCCESS(f"Embedding generation complete!")
        )
        self.stdout.write(f"  Processed: {processed_count}")
        self.stdout.write(f"  Errors: {error_count}")
        self.stdout.write(f"  Total: {len(chunks)}")
