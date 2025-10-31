from django.core.management.base import BaseCommand
from ai_assistant.models import UploadedFile, DocumentChunk
from ai_assistant.enhanced_chunking import semantic_chunker

class Command(BaseCommand):
    help = "Re-chunk all processed documents to add glossary micro-chunks (non-destructive)"

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=100000, help='Limit number of files to process')
        parser.add_argument('--dry-run', action='store_true', help='Do not write changes')

    def handle(self, *args, **options):
        limit = options['limit']
        dry_run = options['dry_run']

        files = UploadedFile.objects.filter(chunks_created=True).order_by('-uploaded_at')[:limit]
        created = 0
        self.stdout.write(self.style.NOTICE(f"Processing {files.count()} files (limit={limit})"))

        for uf in files:
            # Load existing chunks per page_number
            chunks = DocumentChunk.objects.filter(uploaded_file=uf).order_by('page_number', 'chunk_index')
            # Build page_texts by concatenating chunks per page
            pages = {}
            for ch in chunks:
                pages.setdefault(ch.page_number or 1, []).append(ch.content)
            for page_num, parts in pages.items():
                text = "\n".join(parts)
                micro = semantic_chunker.extract_glossary_microchunks(text, page_number=page_num)
                for m in micro:
                    if not dry_run:
                        DocumentChunk.objects.create(
                            uploaded_file=uf,
                            content=m.content,
                            embedding=None,  # embedding will be generated lazily on next embedding job
                            page_number=m.page_number,
                            chunk_index=999999  # place at end; retrieval doesn’t rely on order
                        )
                    created += 1
        self.stdout.write(self.style.SUCCESS(f"Added {created} glossary micro-chunks"))
