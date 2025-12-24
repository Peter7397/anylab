"""
Management command to restore database records for existing files in media directory.
This is useful when database was reset but files still exist on disk.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from django.db import connection
from ai_assistant.models import DocumentFile, UploadedFile
import os
import hashlib
from pathlib import Path


class Command(BaseCommand):
    help = 'Restore database records for files that exist in media directory but are missing from database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--directory',
            type=str,
            default='uploads',
            help='Subdirectory in media folder to scan (default: uploads)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be restored without actually creating records'
        )

    def handle(self, *args, **options):
        media_root = settings.MEDIA_ROOT
        scan_dir = os.path.join(media_root, options['directory'])
        dry_run = options['dry_run']
        
        if not os.path.exists(scan_dir):
            self.stdout.write(self.style.ERROR(f'Directory not found: {scan_dir}'))
            return
        
        self.stdout.write(f'Scanning directory: {scan_dir}')
        self.stdout.write(f'Mode: {"DRY RUN" if dry_run else "RESTORE"}')
        self.stdout.write('=' * 60)
        
        pdf_files = [p for p in Path(scan_dir).glob('*.pdf') if not p.name.startswith('._')]
        total_files = len(pdf_files)
        restored_count = 0
        skipped_count = 0
        
        self.stdout.write(f'\nFound {total_files} PDF files (excluding metadata files)\n')
        
        for pdf_path in pdf_files:
            filename = pdf_path.name
            file_path = str(pdf_path)
            file_size = os.path.getsize(file_path)
            
            # Check if already exists
            existing = DocumentFile.objects.filter(filename=filename).first()
            if existing:
                self.stdout.write(self.style.WARNING(f'  ⏭️  Skipped: {filename} (already in database)'))
                skipped_count += 1
                continue
            
            # Calculate file hash
            try:
                with open(file_path, 'rb') as f:
                    file_hash = hashlib.sha256(f.read()).hexdigest()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ❌ Error reading {filename}: {e}'))
                continue
            
            # Check for duplicates by hash (use only existing fields)
            duplicate = UploadedFile.objects.only('id', 'filename', 'file_hash').filter(file_hash=file_hash).first()
            
            if dry_run:
                status = 'WOULD CREATE' if not duplicate else 'WOULD LINK (duplicate)'
                self.stdout.write(f'  📄 {status}: {filename} ({file_size:,} bytes)')
            else:
                # Create UploadedFile if needed (using raw SQL to avoid Django ORM field issues)
                if not duplicate:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """INSERT INTO ai_assistant_uploadedfile 
                               (filename, file_hash, file_size, page_count, uploaded_at)
                               VALUES (%s, %s, %s, %s, NOW())
                               RETURNING id""",
                            [filename, file_hash, file_size, 0]
                        )
                        uploaded_file_id = cursor.fetchone()[0]
                else:
                    uploaded_file_id = duplicate.id
                    self.stdout.write(self.style.WARNING(f'  🔗 Linked to existing: {filename}'))
                
                # Create DocumentFile record using raw SQL
                relative_path = os.path.relpath(file_path, media_root)
                title = os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ')
                file_path_db = f'{options["directory"]}/{filename}'
                
                with connection.cursor() as cursor:
                    cursor.execute(
                        """INSERT INTO ai_assistant_documentfile 
                           (title, filename, file, document_type, uploaded_at, file_size, page_count, uploaded_file_id, metadata)
                           VALUES (%s, %s, %s, %s, NOW(), %s, %s, %s, '{}'::jsonb)
                           RETURNING id""",
                        [title, filename, file_path_db, 'pdf', file_size, 0, uploaded_file_id]
                    )
                    doc_id = cursor.fetchone()[0]
                
                self.stdout.write(self.style.SUCCESS(f'  ✅ Restored: {filename} (ID: {doc_id})'))
                restored_count += 1
            
            if (restored_count + skipped_count) % 50 == 0:
                self.stdout.write(f'\nProgress: {restored_count + skipped_count}/{total_files} files processed...\n')
        
        self.stdout.write('\n' + '=' * 60)
        if dry_run:
            self.stdout.write(self.style.WARNING(f'\nDRY RUN: Would restore {total_files - skipped_count} files'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\n✅ Restored: {restored_count} files'))
            self.stdout.write(self.style.WARNING(f'⏭️  Skipped: {skipped_count} files (already exist)'))
            if restored_count > 0:
                self.stdout.write(self.style.WARNING(
                    '\n⚠️  NOTE: Files are restored but NOT processed yet.\n'
                    'Run: python manage.py reprocess_pdfs --all\n'
                    'to generate chunks and embeddings for these files.'
                ))

