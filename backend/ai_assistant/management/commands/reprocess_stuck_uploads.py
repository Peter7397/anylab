from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from ai_assistant.models import UploadedFile
from ai_assistant.tasks import process_file_automatically


class Command(BaseCommand):
    help = 'Re-queue processing for stuck/failed uploads older than a threshold'

    def add_arguments(self, parser):
        parser.add_argument('--older-than', type=str, default='10m', help='Threshold (e.g., 10m, 2h)')
        parser.add_argument('--limit', type=int, default=50, help='Max files to re-queue')

    def handle(self, *args, **options):
        threshold = options['older_than']
        limit = options['limit']

        delta = self._parse_delta(threshold)
        cutoff = timezone.now() - delta

        qs = UploadedFile.objects.filter(
            processing_status__in=['pending', 'failed'],
            uploaded_at__lt=cutoff
        ).order_by('-uploaded_at')[:limit]

        count = 0
        for uf in qs:
            uf.processing_status = 'pending'
            uf.processing_error = ''
            uf.metadata_extracted = False
            uf.chunks_created = False
            uf.embeddings_created = False
            uf.chunk_count = 0
            uf.embedding_count = 0
            uf.save()
            process_file_automatically.delay(uf.id)
            count += 1

        self.stdout.write(self.style.SUCCESS(f'Re-queued {count} upload(s) older than {threshold}'))

    def _parse_delta(self, s: str) -> timedelta:
        s = s.strip().lower()
        if s.endswith('m'):
            return timedelta(minutes=int(s[:-1]))
        if s.endswith('h'):
            return timedelta(hours=int(s[:-1]))
        if s.endswith('d'):
            return timedelta(days=int(s[:-1]))
        # default minutes
        return timedelta(minutes=int(s))








