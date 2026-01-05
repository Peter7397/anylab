"""
Management command to clean up orphaned files that don't exist on disk

This command:
1. Checks all UploadedFile records
2. Verifies if physical files exist on disk
3. Removes orphaned records including:
   - DocumentChunk entries (with embeddings in pgvector)
   - DocumentFile entries
   - UploadedFile entries

Usage:
    python manage.py cleanup_orphaned_files [--dry-run] [--confirm]
"""

from django.core.management.base import BaseCommand
from ai_assistant.models import UploadedFile, DocumentFile, DocumentChunk
import os
from django.conf import settings
from django.db import transaction


class Command(BaseCommand):
    help = 'Remove all orphaned files (database records without physical files) including embeddings'

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
        parser.add_argument(
            '--status',
            type=str,
            help='Only check files with specific processing status (e.g., "failed", "ready")',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        confirm = options['confirm']
        status_filter = options.get('status')
        
        if not dry_run and not confirm:
            self.stdout.write(self.style.ERROR(
                'ERROR: This will delete database records. Use --dry-run to preview or --confirm to proceed.'
            ))
            return
        
        # Get all UploadedFile records (or filtered by status)
        if status_filter:
            uploaded_files = UploadedFile.objects.filter(processing_status=status_filter)
            self.stdout.write(f'Checking files with status: {status_filter}')
        else:
            uploaded_files = UploadedFile.objects.all()
            self.stdout.write('Checking all UploadedFile records...')
        
        total_files = uploaded_files.count()
        self.stdout.write(f'Total files to check: {total_files}')
        
        # Check which ones are missing from disk
        missing_files = []
        existing_files = []
        error_files = []
        
        self.stdout.write('\nChecking file existence on disk...')
        for f in uploaded_files:
            try:
                file_path = os.path.join(settings.MEDIA_ROOT, f.filename)
                if os.path.exists(file_path):
                    existing_files.append(f)
                else:
                    missing_files.append(f)
            except Exception as e:
                error_files.append((f, str(e)))
        
        self.stdout.write(f'\nResults:')
        self.stdout.write(f'  ✓ {len(existing_files)} files exist on disk')
        self.stdout.write(f'  ✗ {len(missing_files)} files missing from disk (orphaned)')
        if error_files:
            self.stdout.write(f'  ⚠ {len(error_files)} files had errors during check')
        
        if not missing_files:
            self.stdout.write(self.style.SUCCESS('\nNo orphaned files found! All files exist on disk.'))
            if error_files:
                self.stdout.write(self.style.WARNING('\nFiles with errors:'))
                for f, error in error_files[:10]:
                    self.stdout.write(f'  ID={f.id}: {f.filename[:50]} - {error}')
            return
        
        # Show detailed information about orphaned files
        self.stdout.write(self.style.WARNING(f'\nOrphaned files to be deleted ({len(missing_files)}):'))
        
        total_chunks = 0
        total_doc_files = 0
        total_embeddings = 0
        
        for f in missing_files[:50]:  # Show first 50
            # Count related records
            doc_files_count = DocumentFile.objects.filter(uploaded_file=f).count()
            chunks_count = DocumentChunk.objects.filter(uploaded_file=f).count()
            embeddings_count = DocumentChunk.objects.filter(uploaded_file=f, embedding__isnull=False).count()
            
            total_chunks += chunks_count
            total_doc_files += doc_files_count
            total_embeddings += embeddings_count
            
            status_info = f'[{f.processing_status}]' if f.processing_status != 'ready' else ''
            self.stdout.write(
                f'  ID={f.id}: {f.filename[:60]} {status_info} '
                f'(DocumentFiles: {doc_files_count}, Chunks: {chunks_count}, Embeddings: {embeddings_count})'
            )
        
        if len(missing_files) > 50:
            # Count remaining files
            remaining = missing_files[50:]
            for f in remaining:
                doc_files_count = DocumentFile.objects.filter(uploaded_file=f).count()
                chunks_count = DocumentChunk.objects.filter(uploaded_file=f).count()
                embeddings_count = DocumentChunk.objects.filter(uploaded_file=f, embedding__isnull=False).count()
                
                total_chunks += chunks_count
                total_doc_files += doc_files_count
                total_embeddings += embeddings_count
            
            self.stdout.write(f'  ... and {len(missing_files) - 50} more files')
        
        self.stdout.write(f'\nSummary of data to be deleted:')
        self.stdout.write(f'  - {len(missing_files)} UploadedFile records')
        self.stdout.write(f'  - {total_doc_files} DocumentFile records')
        self.stdout.write(f'  - {total_chunks} DocumentChunk records')
        self.stdout.write(f'  - {total_embeddings} Embeddings (pgvector entries)')
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS(
                f'\nDRY RUN: Would delete {len(missing_files)} orphaned files and all related data.'
            ))
            return
        
        if not confirm:
            self.stdout.write(self.style.ERROR(
                '\nERROR: Use --confirm to actually delete these records.'
            ))
            return
        
        # Actually delete
        self.stdout.write(self.style.WARNING('\nDeleting orphaned records...'))
        
        deleted_count = 0
        deleted_doc_files = 0
        deleted_chunks = 0
        deleted_embeddings = 0
        errors = []
        
        # Use transaction for atomic deletion
        with transaction.atomic():
            for f in missing_files:
                try:
                    # Count before deletion
                    doc_files_count = DocumentFile.objects.filter(uploaded_file=f).count()
                    chunks_count = DocumentChunk.objects.filter(uploaded_file=f).count()
                    embeddings_count = DocumentChunk.objects.filter(uploaded_file=f, embedding__isnull=False).count()
                    
                    # Delete related DocumentFiles first (they may cascade delete chunks)
                    DocumentFile.objects.filter(uploaded_file=f).delete()
                    deleted_doc_files += doc_files_count
                    
                    # Delete any remaining chunks (this will also delete embeddings from pgvector)
                    # Due to CASCADE, deleting DocumentChunk automatically removes the vector from pgvector
                    remaining_chunks = DocumentChunk.objects.filter(uploaded_file=f)
                    deleted_chunks += remaining_chunks.count()
                    deleted_embeddings += remaining_chunks.filter(embedding__isnull=False).count()
                    remaining_chunks.delete()
                    
                    # Delete the UploadedFile
                    f.delete()
                    deleted_count += 1
                    
                    if deleted_count % 10 == 0:
                        self.stdout.write(f'  Processed {deleted_count}/{len(missing_files)} files...')
                    
                except Exception as e:
                    errors.append((f.id, str(e)))
                    self.stdout.write(self.style.ERROR(
                        f'  Error deleting ID={f.id}: {str(e)}'
                    ))
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Successfully deleted:'
            f'\n  - {deleted_count} UploadedFile records'
            f'\n  - {deleted_doc_files} DocumentFile records'
            f'\n  - {deleted_chunks} DocumentChunk records'
            f'\n  - {deleted_embeddings} Embeddings (pgvector entries removed)'
        ))
        
        if errors:
            self.stdout.write(self.style.ERROR(
                f'\n⚠ {len(errors)} files had errors during deletion:'
            ))
            for file_id, error in errors[:10]:
                self.stdout.write(f'  ID={file_id}: {error}')
        
        # Also check for orphaned DocumentChunks (chunks without UploadedFile or DocumentFile)
        self.stdout.write('\nChecking for orphaned DocumentChunks...')
        orphaned_chunks = DocumentChunk.objects.filter(
            uploaded_file__isnull=True,
            document_file__isnull=True
        )
        orphaned_count = orphaned_chunks.count()
        
        if orphaned_count > 0:
            orphaned_embeddings = orphaned_chunks.filter(embedding__isnull=False).count()
            self.stdout.write(self.style.WARNING(
                f'Found {orphaned_count} orphaned DocumentChunks (no parent file) with {orphaned_embeddings} embeddings'
            ))
            
            if confirm:
                orphaned_chunks.delete()
                self.stdout.write(self.style.SUCCESS(
                    f'✓ Deleted {orphaned_count} orphaned DocumentChunks and {orphaned_embeddings} embeddings'
                ))
            else:
                self.stdout.write('  (Use --confirm to delete these as well)')
        
        self.stdout.write(self.style.SUCCESS('\n✓ Cleanup completed!'))

