from django.core.management.base import BaseCommand
from django.db import transaction
from ai_assistant.models import DocumentChunk
from ai_assistant.rag_service import EnhancedRAGService

class Command(BaseCommand):
    help = "Batch-generate embeddings for chunks with NULL embedding using BGE-M3 via Ollama"

    def add_arguments(self, parser):
        parser.add_argument('--batch-size', type=int, default=50, help='Batch size per API call')
        parser.add_argument('--limit', type=int, default=5000, help='Max chunks to process')

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        remaining = options['limit']

        rag = EnhancedRAGService()

        processed = 0
        self.stdout.write(self.style.NOTICE(f"Embedding up to {remaining} chunks (batch={batch_size})"))

        while remaining > 0:
            slice_qs = list(DocumentChunk.objects.filter(embedding__isnull=True).order_by('id')[:min(batch_size, remaining)])
            if not slice_qs:
                break
            texts = [c.content or '' for c in slice_qs]
            embeddings = rag.get_embeddings_from_ollama_batch(texts)
            with transaction.atomic():
                for c, emb in zip(slice_qs, embeddings):
                    c.embedding = emb
                    c.save(update_fields=['embedding'])
                    processed += 1
            remaining -= len(slice_qs)
            self.stdout.write(f"Embedded {processed}")

        self.stdout.write(self.style.SUCCESS(f"Done. Embedded {processed} chunks"))
