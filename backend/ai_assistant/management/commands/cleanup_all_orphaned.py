"""
Management command to clean up ALL orphaned records:
- UploadedFile records with missing physical files
- DocumentChunk records with null uploaded_file
- DocumentFile records with null uploaded_file
- Duplicate file_hash records (keep the most recent one)
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.core.files.storage import default_storage
from ai_assistant.models import UploadedFile, DocumentChunk, DocumentFile
from django.db.models import Count, Max


class Command(BaseCommand):
    help = 'Clean up all orphaned records: missing files, orphaned chunks, orphaned document files, and duplicate hashes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--delete-missing-files',
            action='store_true',
            help='Delete UploadedFile records where physical file is missing',
        )
        parser.add_argument(
            '--delete-orphaned-chunks',
            action='store_true',
            help='Delete DocumentChunk records with null uploaded_file',
        )
        parser.add_argument(
            '--delete-orphaned-doc-files',
            action='store_true',
            help='Delete DocumentFile records with null uploaded_file',
        )
        parser.add_argument(
            '--fix-duplicate-hashes',
            action='store_true',
            help='Fix duplicate file_hash records (keep most recent, delete others)',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Run all cleanup operations',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        delete_all = options['all']
        
        delete_missing = options['delete_missing_files'] or delete_all
        delete_orphaned_chunks = options['delete_orphaned_chunks'] or delete_all
        delete_orphaned_doc_files = options['delete_orphaned_doc_files'] or delete_all
        fix_duplicates = options['fix_duplicate_hashes'] or delete_all
        
        if not any([delete_missing, delete_orphaned_chunks, delete_orphaned_doc_files, fix_duplicates]):
            self.stdout.write(self.style.WARNING(
                'No cleanup operations specified. Use --all or specify individual operations.'
            ))
            return
        
        stats = {
            'missing_files_deleted': 0,
            'orphaned_chunks_deleted': 0,
            'orphaned_doc_files_deleted': 0,
            'duplicate_hashes_fixed': 0,
            'related_chunks_deleted': 0,
            'related_doc_files_deleted': 0,
        }
        
        with transaction.atomic():
            # 1. Clean up UploadedFile records with missing physical files
            if delete_missing:
                self.stdout.write('\n=== Cleaning Missing Files ===')
                missing_files = []
                for uf in UploadedFile.objects.all():
                    if not default_storage.exists(uf.filename):
                        missing_files.append(uf)
                
                self.stdout.write(f'Found {len(missing_files)} UploadedFile records with missing physical files')
                
                for uf in missing_files:
                    if dry_run:
                        self.stdout.write(f'  [DRY RUN] Would delete: ID={uf.id}, Hash={uf.file_hash[:12]}..., Filename={uf.filename}')
                    else:
                        # Count related records
                        chunks_count = DocumentChunk.objects.filter(uploaded_file=uf).count()
                        doc_files_count = DocumentFile.objects.filter(uploaded_file=uf).count()
                        
                        # Delete related records
                        DocumentChunk.objects.filter(uploaded_file=uf).delete()
                        DocumentFile.objects.filter(uploaded_file=uf).delete()
                        
                        # Delete the UploadedFile (this will free the file_hash)
                        uf.delete()
                        
                        stats['missing_files_deleted'] += 1
                        stats['related_chunks_deleted'] += chunks_count
                        stats['related_doc_files_deleted'] += doc_files_count
                        
                        self.stdout.write(f'  ✓ Deleted: ID={uf.id}, Hash={uf.file_hash[:12]}...')
            
            # 2. Clean up orphaned DocumentChunk records
            if delete_orphaned_chunks:
                self.stdout.write('\n=== Cleaning Orphaned DocumentChunks ===')
                orphaned_chunks = DocumentChunk.objects.filter(uploaded_file__isnull=True)
                count = orphaned_chunks.count()
                self.stdout.write(f'Found {count} orphaned DocumentChunk records')
                
                if dry_run:
                    for chunk in orphaned_chunks[:10]:
                        self.stdout.write(f'  [DRY RUN] Would delete chunk ID={chunk.id}')
                    if count > 10:
                        self.stdout.write(f'  [DRY RUN] ... and {count - 10} more')
                else:
                    orphaned_chunks.delete()
                    stats['orphaned_chunks_deleted'] = count
                    self.stdout.write(f'  ✓ Deleted {count} orphaned DocumentChunk records')
            
            # 3. Clean up orphaned DocumentFile records
            if delete_orphaned_doc_files:
                self.stdout.write('\n=== Cleaning Orphaned DocumentFiles ===')
                orphaned_doc_files = DocumentFile.objects.filter(uploaded_file__isnull=True)
                count = orphaned_doc_files.count()
                self.stdout.write(f'Found {count} orphaned DocumentFile records')
                
                if dry_run:
                    for doc_file in orphaned_doc_files[:10]:
                        self.stdout.write(f'  [DRY RUN] Would delete DocumentFile ID={doc_file.id}, Title={doc_file.title}')
                    if count > 10:
                        self.stdout.write(f'  [DRY RUN] ... and {count - 10} more')
                else:
                    # Delete related chunks first
                    for doc_file in orphaned_doc_files:
                        DocumentChunk.objects.filter(document_file=doc_file).delete()
                    
                    orphaned_doc_files.delete()
                    stats['orphaned_doc_files_deleted'] = count
                    self.stdout.write(f'  ✓ Deleted {count} orphaned DocumentFile records')
            
            # 4. Fix duplicate file_hash records
            if fix_duplicates:
                self.stdout.write('\n=== Fixing Duplicate File Hashes ===')
                duplicate_hashes = UploadedFile.objects.values('file_hash').annotate(
                    count=Count('file_hash')
                ).filter(count__gt=1)
                
                self.stdout.write(f'Found {duplicate_hashes.count()} duplicate hash values')
                
                for dup in duplicate_hashes:
                    hash_val = dup['file_hash']
                    files = UploadedFile.objects.filter(file_hash=hash_val).order_by('-uploaded_at')
                    
                    if files.count() > 1:
                        # Keep the most recent one
                        keep_file = files.first()
                        delete_files = files[1:]
                        
                        if dry_run:
                            self.stdout.write(f'  [DRY RUN] Hash {hash_val[:12]}...: Keep ID={keep_file.id}, Delete {len(delete_files)} duplicates')
                            for df in delete_files:
                                self.stdout.write(f'      Would delete: ID={df.id}, Status={df.processing_status}')
                        else:
                            for df in delete_files:
                                # Delete related records
                                DocumentChunk.objects.filter(uploaded_file=df).delete()
                                DocumentFile.objects.filter(uploaded_file=df).delete()
                                
                                # Delete the duplicate UploadedFile
                                df.delete()
                                stats['duplicate_hashes_fixed'] += 1
                            
                            self.stdout.write(f'  ✓ Fixed hash {hash_val[:12]}...: Kept ID={keep_file.id}, Deleted {len(delete_files)} duplicates')
        
        # Summary
        self.stdout.write(self.style.SUCCESS(
            f'\n=== Cleanup Summary ==='
            f'\n  Missing files deleted: {stats["missing_files_deleted"]}'
            f'\n  Related chunks deleted: {stats["related_chunks_deleted"]}'
            f'\n  Related DocumentFiles deleted: {stats["related_doc_files_deleted"]}'
            f'\n  Orphaned chunks deleted: {stats["orphaned_chunks_deleted"]}'
            f'\n  Orphaned DocumentFiles deleted: {stats["orphaned_doc_files_deleted"]}'
            f'\n  Duplicate hashes fixed: {stats["duplicate_hashes_fixed"]}'
        ))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n[DRY RUN] No records were actually deleted. Run without --dry-run to perform cleanup.'))

