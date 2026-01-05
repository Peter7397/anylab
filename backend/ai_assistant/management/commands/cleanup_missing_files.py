"""
Management command to clean up failed file uploads that don't exist on disk

Usage:
    python manage.py cleanup_missing_files [--dry-run] [--confirm]
"""

from django.core.management.base import BaseCommand
from ai_assistant.models import UploadedFile, DocumentFile, DocumentChunk
import os
from django.conf import settings


class Command(BaseCommand):
    help = 'Remove failed file uploads that do not exist on disk'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion (required for actual deletion)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        confirm = options['confirm']
        
        if not dry_run and not confirm:
            self.stdout.write(self.style.ERROR(
                'ERROR: This will delete database records. Use --dry-run to preview or --confirm to proceed.'
            ))
            return
        
        # Find failed files
        failed_files = UploadedFile.objects.filter(processing_status='failed')
        
        # Check which ones are missing from disk
        missing_files = []
        existing_files = []
        
        for f in failed_files:
            file_path = os.path.join(settings.MEDIA_ROOT, f.filename)
            if os.path.exists(file_path):
                existing_files.append(f)
            else:
                missing_files.append(f)
        
        self.stdout.write(f'\nFound {failed_files.count()} failed files:')
        self.stdout.write(f'  - {len(missing_files)} missing from disk (will be deleted)')
        self.stdout.write(f'  - {len(existing_files)} exist on disk (can be retried)')
        
        if not missing_files:
            self.stdout.write(self.style.SUCCESS('\nNo missing files to clean up!'))
            return
        
        # Show files that will be deleted
        self.stdout.write(self.style.WARNING(f'\nFiles to be deleted ({len(missing_files)}):'))
        for f in missing_files[:20]:
            # Count related records
            doc_files = DocumentFile.objects.filter(uploaded_file=f).count()
            chunks = DocumentChunk.objects.filter(uploaded_file=f).count()
            self.stdout.write(
                f'  ID={f.id}: {f.filename[:50]} '
                f'(DocumentFiles: {doc_files}, Chunks: {chunks})'
            )
        
        if len(missing_files) > 20:
            self.stdout.write(f'  ... and {len(missing_files) - 20} more files')
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS(
                f'\nDRY RUN: Would delete {len(missing_files)} UploadedFile records and related data.'
            ))
            return
        
        if not confirm:
            self.stdout.write(self.style.ERROR(
                '\nERROR: Use --confirm to actually delete these records.'
            ))
            return
        
        # Actually delete
        self.stdout.write(self.style.WARNING('\nDeleting records...'))
        
        deleted_count = 0
        deleted_doc_files = 0
        deleted_chunks = 0
        
        for f in missing_files:
            try:
                # Count before deletion
                doc_files_count = DocumentFile.objects.filter(uploaded_file=f).count()
                chunks_count = DocumentChunk.objects.filter(uploaded_file=f).count()
                
                # Delete related DocumentFiles (they will cascade delete chunks)
                DocumentFile.objects.filter(uploaded_file=f).delete()
                deleted_doc_files += doc_files_count
                
                # Delete any remaining chunks
                remaining_chunks = DocumentChunk.objects.filter(uploaded_file=f).count()
                DocumentChunk.objects.filter(uploaded_file=f).delete()
                deleted_chunks += remaining_chunks
                
                # Delete the UploadedFile
                f.delete()
                deleted_count += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'  Error deleting ID={f.id}: {str(e)}'
                ))
        
        self.stdout.write(self.style.SUCCESS(
            f'\nSuccessfully deleted:'
            f'\n  - {deleted_count} UploadedFile records'
            f'\n  - {deleted_doc_files} DocumentFile records'
            f'\n  - {deleted_chunks} DocumentChunk records'
        ))

