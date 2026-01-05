"""
Management command to validate file processing results and send alerts if needed.

Usage:
    python manage.py validate_processing
    python manage.py validate_processing --check-embeddings
    python manage.py validate_processing --check-chunks
"""

from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from ai_assistant.models import UploadedFile, DocumentChunk
from ai_assistant.utils.alerting import alert_manager
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Validate file processing results and check for issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-embeddings',
            action='store_true',
            help='Check embedding generation'
        )
        parser.add_argument(
            '--check-chunks',
            action='store_true',
            help='Check chunk generation'
        )
        parser.add_argument(
            '--recent-hours',
            type=int,
            default=24,
            help='Check files processed in last N hours (default: 24)'
        )

    def handle(self, *args, **options):
        check_embeddings = options.get('check_embeddings', True)
        check_chunks = options.get('check_chunks', True)
        recent_hours = options.get('recent_hours', 24)

        cutoff_time = timezone.now() - timedelta(hours=recent_hours)

        self.stdout.write(f'\n{"="*60}')
        self.stdout.write('FILE PROCESSING VALIDATION')
        self.stdout.write(f'{"="*60}')
        self.stdout.write(f'Checking files processed in last {recent_hours} hours\n')

        # Overall statistics
        total_files = UploadedFile.objects.filter(uploaded_at__gte=cutoff_time).count()
        processed_files = UploadedFile.objects.filter(
            uploaded_at__gte=cutoff_time,
            processing_status='ready'
        ).count()
        failed_files = UploadedFile.objects.filter(
            uploaded_at__gte=cutoff_time,
            processing_status='failed'
        ).count()
        pending_files = UploadedFile.objects.filter(
            uploaded_at__gte=cutoff_time,
            processing_status='pending'
        ).count()
        corrupted_files = UploadedFile.objects.filter(
            uploaded_at__gte=cutoff_time,
            processing_status='corrupted'
        ).count()

        self.stdout.write(f'\nOverall Statistics:')
        self.stdout.write(f'  Total files: {total_files}')
        self.stdout.write(f'  Processed (ready): {processed_files}')
        self.stdout.write(f'  Failed: {failed_files}')
        self.stdout.write(f'  Pending: {pending_files}')
        self.stdout.write(f'  Corrupted: {corrupted_files}')

        if total_files > 0:
            success_rate = (processed_files / total_files) * 100
            self.stdout.write(f'\n  Success Rate: {success_rate:.1f}%')

        # Check chunks
        if check_chunks:
            self.stdout.write(f'\n{"="*60}')
            self.stdout.write('CHUNK VALIDATION')
            self.stdout.write(f'{"="*60}')

            recent_files = UploadedFile.objects.filter(uploaded_at__gte=cutoff_time)
            files_with_chunks = 0
            files_without_chunks = 0
            total_chunks = 0

            for uploaded_file in recent_files:
                chunk_count = DocumentChunk.objects.filter(
                    uploaded_file=uploaded_file
                ).count()
                
                if chunk_count > 0:
                    files_with_chunks += 1
                    total_chunks += chunk_count
                else:
                    if uploaded_file.processing_status == 'ready':
                        files_without_chunks += 1

            self.stdout.write(f'  Files with chunks: {files_with_chunks}')
            self.stdout.write(f'  Files without chunks (but ready): {files_without_chunks}')
            self.stdout.write(f'  Total chunks: {total_chunks}')
            
            if files_with_chunks > 0:
                avg_chunks = total_chunks / files_with_chunks
                self.stdout.write(f'  Average chunks per file: {avg_chunks:.1f}')

        # Check embeddings
        if check_embeddings:
            self.stdout.write(f'\n{"="*60}')
            self.stdout.write('EMBEDDING VALIDATION')
            self.stdout.write(f'{"="*60}')

            recent_files = UploadedFile.objects.filter(uploaded_at__gte=cutoff_time)
            files_with_embeddings = 0
            files_without_embeddings = 0
            total_embeddings = 0
            chunks_without_embeddings = 0

            for uploaded_file in recent_files:
                chunks = DocumentChunk.objects.filter(uploaded_file=uploaded_file)
                chunk_count = chunks.count()
                
                if chunk_count > 0:
                    chunks_with_emb = chunks.exclude(embedding__isnull=True).exclude(embedding='[]').count()
                    chunks_without_emb = chunks.filter(Q(embedding__isnull=True) | Q(embedding='[]')).count()
                    
                    if chunks_with_emb > 0:
                        files_with_embeddings += 1
                        total_embeddings += chunks_with_emb
                    
                    if chunks_without_emb > 0 and uploaded_file.processing_status == 'ready':
                        files_without_embeddings += 1
                        chunks_without_embeddings += chunks_without_emb

            self.stdout.write(f'  Files with embeddings: {files_with_embeddings}')
            self.stdout.write(f'  Files without embeddings (but ready): {files_without_embeddings}')
            self.stdout.write(f'  Total embeddings: {total_embeddings}')
            self.stdout.write(f'  Chunks missing embeddings: {chunks_without_embeddings}')

            if files_with_embeddings > 0:
                avg_embeddings = total_embeddings / files_with_embeddings
                self.stdout.write(f'  Average embeddings per file: {avg_embeddings:.1f}')

        # Check for issues
        self.stdout.write(f'\n{"="*60}')
        self.stdout.write('ISSUE DETECTION')
        self.stdout.write(f'{"="*60}')

        issues = []

        # Files stuck in processing
        stuck_files = UploadedFile.objects.filter(
            uploaded_at__lt=cutoff_time - timedelta(hours=2),
            processing_status='processing'
        ).count()
        if stuck_files > 0:
            issues.append(f'  ⚠ {stuck_files} files stuck in processing status')

        # Files with errors
        error_files = UploadedFile.objects.filter(
            uploaded_at__gte=cutoff_time,
            processing_error__isnull=False
        ).exclude(processing_status='ready')
        if error_files.exists():
            issues.append(f'  ⚠ {error_files.count()} files with processing errors')
            self.stdout.write('\n  Recent errors:')
            for file in error_files[:5]:
                self.stdout.write(f'    - {file.filename}: {file.processing_error[:100]}')

        if issues:
            self.stdout.write('\n'.join(issues))
        else:
            self.stdout.write('  ✓ No issues detected')

        # Check for processing failures and send alerts if needed
        self.stdout.write(f'\n{"="*60}')
        self.stdout.write('ALERT CHECK')
        self.stdout.write(f'{"="*60}')
        
        try:
            alert_result = alert_manager.check_processing_failures()
            self.stdout.write(f'  Status: {alert_result["status"]}')
            self.stdout.write(f'  Total files: {alert_result["total_files"]}')
            self.stdout.write(f'  Failed files: {alert_result["failed_files"]}')
            self.stdout.write(f'  Failure rate: {alert_result["failure_rate_percent"]:.1f}%')
            self.stdout.write(f'  Threshold: {alert_result["threshold_rate"]:.1f}% or {alert_result["threshold_count"]} failures')
            
            if alert_result['alert_sent']:
                self.stdout.write(self.style.SUCCESS('  ✓ Alert sent successfully'))
            elif alert_result['status'] == 'alert':
                self.stdout.write(self.style.WARNING('  ⚠ Alert threshold exceeded but rate limited'))
            else:
                self.stdout.write('  ✓ No alert needed')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Error checking alerts: {e}'))
            logger.error(f'Error checking alerts: {e}', exc_info=True)

        self.stdout.write(f'\n{"="*60}\n')

