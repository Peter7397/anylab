"""
Management command to check processing logs for errors and warnings.

Usage:
    python manage.py check_logs
    python manage.py check_logs --hours 48
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count
from datetime import timedelta
from ai_assistant.models import UploadedFile
import logging
import re

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check processing logs for errors and warnings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Time window in hours (default: 24)'
        )
        parser.add_argument(
            '--level',
            type=str,
            choices=['error', 'warning', 'all'],
            default='all',
            help='Log level to check (default: all)'
        )

    def handle(self, *args, **options):
        hours = options.get('hours', 24)
        level = options.get('level', 'all')
        cutoff_time = timezone.now() - timedelta(hours=hours)

        self.stdout.write(f'\n{"="*60}')
        self.stdout.write('PROCESSING LOG ANALYSIS')
        self.stdout.write(f'{"="*60}')
        self.stdout.write(f'Time window: Last {hours} hours\n')

        # Check database for processing errors
        self.stdout.write('Database Errors:')
        files_with_errors = UploadedFile.objects.filter(
            uploaded_at__gte=cutoff_time,
            processing_error__isnull=False
        ).exclude(processing_status='ready')

        error_count = files_with_errors.count()
        if error_count > 0:
            self.stdout.write(self.style.WARNING(f'  ⚠ Found {error_count} files with processing errors:'))
            
            # Group by error type
            error_types = {}
            for file in files_with_errors[:50]:  # Limit to first 50
                error_msg = file.processing_error or 'Unknown error'
                # Extract error type (first part before colon or first word)
                error_type = error_msg.split(':')[0].split()[0] if error_msg else 'Unknown'
                if error_type not in error_types:
                    error_types[error_type] = []
                error_types[error_type].append({
                    'filename': file.filename,
                    'error': error_msg[:100],
                    'status': file.processing_status
                })

            for error_type, files in list(error_types.items())[:10]:
                self.stdout.write(f'\n  {error_type} ({len(files)} files):')
                for file_info in files[:3]:  # Show first 3 examples
                    self.stdout.write(f'    - {file_info["filename"]}: {file_info["error"]}')
                if len(files) > 3:
                    self.stdout.write(f'    ... and {len(files) - 3} more')
        else:
            self.stdout.write(self.style.SUCCESS('  ✓ No processing errors found'))

        # Check for common issues
        self.stdout.write(f'\nCommon Issues:')
        
        # Files stuck in processing
        stuck_files = UploadedFile.objects.filter(
            uploaded_at__lt=cutoff_time - timedelta(hours=2),
            processing_status='processing'
        )
        if stuck_files.exists():
            self.stdout.write(self.style.WARNING(f'  ⚠ {stuck_files.count()} files stuck in processing'))
        else:
            self.stdout.write(self.style.SUCCESS('  ✓ No stuck files'))

        # Corrupted files
        corrupted_files = UploadedFile.objects.filter(
            uploaded_at__gte=cutoff_time,
            processing_status='corrupted'
        )
        if corrupted_files.exists():
            self.stdout.write(self.style.WARNING(f'  ⚠ {corrupted_files.count()} corrupted files'))
        else:
            self.stdout.write(self.style.SUCCESS('  ✓ No corrupted files'))

        # Files with no text
        no_text_files = UploadedFile.objects.filter(
            uploaded_at__gte=cutoff_time,
            processing_status='no_text_available'
        )
        if no_text_files.exists():
            self.stdout.write(self.style.WARNING(f'  ⚠ {no_text_files.count()} files with no text'))
        else:
            self.stdout.write(self.style.SUCCESS('  ✓ No files with no text issues'))

        # Processing status distribution
        self.stdout.write(f'\nProcessing Status Distribution:')
        statuses = UploadedFile.objects.filter(
            uploaded_at__gte=cutoff_time
        ).values('processing_status').annotate(
            count=Count('id')
        ).order_by('-count')

        for status in statuses:
            status_name = status['processing_status'] or 'unknown'
            count = status['count']
            percentage = (count / files_with_errors.count() * 100) if files_with_errors.exists() else 0
            self.stdout.write(f'  {status_name}: {count} ({percentage:.1f}%)')

        self.stdout.write(f'\n{"="*60}\n')

