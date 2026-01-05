"""
Management command to retry processing failed file uploads

Usage:
    python manage.py retry_failed_uploads [--all] [--file-id ID] [--check-only]
"""

from django.core.management.base import BaseCommand
from ai_assistant.models import UploadedFile
from ai_assistant.tasks import process_file_automatically
import os
from django.conf import settings


class Command(BaseCommand):
    help = 'Retry processing failed file uploads that exist on disk'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Retry all failed files (including those that may not exist)',
        )
        parser.add_argument(
            '--file-id',
            type=int,
            help='Retry a specific file by ID',
        )
        parser.add_argument(
            '--check-only',
            action='store_true',
            help='Only check which files exist, do not retry',
        )

    def handle(self, *args, **options):
        if options['file_id']:
            # Retry specific file
            try:
                uploaded_file = UploadedFile.objects.get(id=options['file_id'])
                self._retry_file(uploaded_file, check_only=options['check_only'])
            except UploadedFile.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'File with ID {options["file_id"]} not found'))
        else:
            # Get failed files
            failed_files = UploadedFile.objects.filter(
                processing_status='failed',
                filename__startswith='uploads/'
            ).order_by('-id')
            
            self.stdout.write(f'Found {failed_files.count()} failed files')
            
            if options['check_only']:
                self._check_files(failed_files)
            elif options['all']:
                self._retry_all(failed_files)
            else:
                # Only retry files that exist on disk
                self._retry_existing(failed_files)

    def _check_files(self, files):
        """Check which files exist on disk"""
        existing = []
        missing = []
        
        for f in files:
            file_path = os.path.join(settings.MEDIA_ROOT, f.filename)
            if os.path.exists(file_path):
                existing.append(f)
            else:
                missing.append(f)
        
        self.stdout.write(self.style.SUCCESS(f'\nFiles that EXIST on disk ({len(existing)}):'))
        for f in existing[:10]:
            self.stdout.write(f'  ID={f.id}: {f.filename[:60]}')
        
        self.stdout.write(self.style.WARNING(f'\nFiles that are MISSING ({len(missing)}):'))
        for f in missing[:10]:
            self.stdout.write(f'  ID={f.id}: {f.filename[:60]}')
        
        if len(existing) > 10:
            self.stdout.write(f'  ... and {len(existing) - 10} more existing files')
        if len(missing) > 10:
            self.stdout.write(f'  ... and {len(missing) - 10} more missing files')

    def _retry_existing(self, files):
        """Retry only files that exist on disk"""
        existing = []
        for f in files:
            file_path = os.path.join(settings.MEDIA_ROOT, f.filename)
            if os.path.exists(file_path):
                existing.append(f)
        
        self.stdout.write(f'\nFound {len(existing)} failed files that exist on disk')
        
        if not existing:
            self.stdout.write(self.style.WARNING('No files to retry'))
            return
        
        self.stdout.write('Retrying files...')
        retried = 0
        for f in existing:
            if self._retry_file(f):
                retried += 1
        
        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully queued {retried} files for reprocessing'))

    def _retry_all(self, files):
        """Retry all failed files regardless of whether they exist"""
        self.stdout.write(f'\nRetrying all {files.count()} failed files...')
        retried = 0
        for f in files:
            if self._retry_file(f):
                retried += 1
        
        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully queued {retried} files for reprocessing'))

    def _retry_file(self, uploaded_file, check_only=False):
        """Retry processing a single file"""
        file_path = os.path.join(settings.MEDIA_ROOT, uploaded_file.filename)
        exists = os.path.exists(file_path)
        
        if check_only:
            status = 'EXISTS' if exists else 'MISSING'
            self.stdout.write(f'  ID={uploaded_file.id}: {uploaded_file.filename[:50]} - {status}')
            return exists
        
        if not exists:
            self.stdout.write(self.style.WARNING(
                f'  ID={uploaded_file.id}: {uploaded_file.filename[:50]} - SKIPPED (file not found)'
            ))
            return False
        
        try:
            # Reset status
            uploaded_file.processing_status = 'pending'
            uploaded_file.processing_error = ''
            uploaded_file.processing_started_at = None
            uploaded_file.save(update_fields=['processing_status', 'processing_error', 'processing_started_at'])
            
            # Queue for processing
            process_file_automatically.delay(uploaded_file.id)
            
            self.stdout.write(self.style.SUCCESS(
                f'  ID={uploaded_file.id}: {uploaded_file.filename[:50]} - QUEUED'
            ))
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'  ID={uploaded_file.id}: {uploaded_file.filename[:50]} - ERROR: {str(e)}'
            ))
            return False

