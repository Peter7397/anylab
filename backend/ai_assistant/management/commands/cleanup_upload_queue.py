"""
Management command to clean up upload queue

Cleans up failed jobs, error files, and optionally all queue items.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.files.storage import default_storage
from django.db import transaction
import os
import logging

from ai_assistant.models import UploadJob, UploadedFile

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean up upload queue - remove failed jobs, error files, and optionally all items'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Clean ALL jobs and files (not just failed ones)',
        )
        parser.add_argument(
            '--failed-only',
            action='store_true',
            help='Clean only failed/cancelled jobs and failed files (default)',
        )
        parser.add_argument(
            '--delete-files',
            action='store_true',
            help='Also delete physical files from storage',
        )
        parser.add_argument(
            '--clean-temp',
            action='store_true',
            help='Clean temporary files in upload_queue directory',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        delete_all = options['all']
        delete_files = options['delete_files']
        clean_temp = options['clean_temp']
        failed_only = options.get('failed_only', not delete_all)  # Default to failed_only if --all not specified

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        # Statistics
        stats = {
            'jobs_deleted': 0,
            'files_deleted': 0,
            'temp_files_deleted': 0,
            'storage_cleaned': 0,
        }

        try:
            with transaction.atomic():
                # 1. Clean up UploadJob records
                self.stdout.write('\n=== Cleaning Upload Jobs ===')
                
                if delete_all:
                    jobs_to_delete = UploadJob.objects.all()
                    self.stdout.write(f'Found {jobs_to_delete.count()} total jobs to delete')
                else:
                    # Only failed, cancelled, or stuck jobs
                    jobs_to_delete = UploadJob.objects.filter(
                        status__in=['failed', 'cancelled']
                    ) | UploadJob.objects.filter(
                        status='queued',
                        created_at__lt=timezone.now() - timezone.timedelta(hours=24)
                    )
                    self.stdout.write(f'Found {jobs_to_delete.count()} failed/stuck jobs to delete')

                for job in jobs_to_delete:
                    if dry_run:
                        self.stdout.write(f'  [DRY RUN] Would delete job: {job.job_id} ({job.status})')
                    else:
                        job.delete()
                        stats['jobs_deleted'] += 1
                        self.stdout.write(f'  ✓ Deleted job: {job.job_id} ({job.status})')

                # 2. Clean up UploadedFile records
                self.stdout.write('\n=== Cleaning Uploaded Files ===')
                
                if delete_all:
                    files_to_delete = UploadedFile.objects.filter(processing_status='failed')
                    self.stdout.write(f'Found {files_to_delete.count()} failed files to delete')
                else:
                    # Only failed files
                    files_to_delete = UploadedFile.objects.filter(processing_status='failed')
                    self.stdout.write(f'Found {files_to_delete.count()} failed files to delete')

                for uploaded_file in files_to_delete:
                    if dry_run:
                        self.stdout.write(f'  [DRY RUN] Would delete file: {uploaded_file.filename} (ID: {uploaded_file.id})')
                    else:
                        # Delete physical file if requested
                        if delete_files and uploaded_file.filename:
                            try:
                                if default_storage.exists(uploaded_file.filename):
                                    default_storage.delete(uploaded_file.filename)
                                    stats['storage_cleaned'] += 1
                                    self.stdout.write(f'  ✓ Deleted file from storage: {uploaded_file.filename}')
                            except Exception as e:
                                self.stdout.write(self.style.WARNING(f'  ⚠ Could not delete file {uploaded_file.filename}: {e}'))
                        
                        uploaded_file.delete()
                        stats['files_deleted'] += 1
                        self.stdout.write(f'  ✓ Deleted file record: {uploaded_file.filename}')

                # 3. Clean up temporary files in upload_queue directory
                if clean_temp:
                    self.stdout.write('\n=== Cleaning Temporary Files ===')
                    from django.conf import settings
                    import shutil
                    
                    temp_dir = os.path.join(settings.MEDIA_ROOT, 'upload_queue')
                    if os.path.exists(temp_dir):
                        temp_files = []
                        for root, dirs, files in os.walk(temp_dir):
                            for file in files:
                                temp_files.append(os.path.join(root, file))
                        
                        self.stdout.write(f'Found {len(temp_files)} temporary files')
                        
                        for temp_file in temp_files:
                            if dry_run:
                                self.stdout.write(f'  [DRY RUN] Would delete: {temp_file}')
                            else:
                                try:
                                    os.remove(temp_file)
                                    stats['temp_files_deleted'] += 1
                                    self.stdout.write(f'  ✓ Deleted: {temp_file}')
                                except Exception as e:
                                    self.stdout.write(self.style.WARNING(f'  ⚠ Could not delete {temp_file}: {e}'))
                        
                        # Remove empty directories
                        if not dry_run:
                            try:
                                for root, dirs, files in os.walk(temp_dir, topdown=False):
                                    for dir_name in dirs:
                                        dir_path = os.path.join(root, dir_name)
                                        try:
                                            if not os.listdir(dir_path):
                                                os.rmdir(dir_path)
                                                self.stdout.write(f'  ✓ Removed empty directory: {dir_path}')
                                        except Exception as e:
                                            self.stdout.write(self.style.WARNING(f'  ⚠ Could not remove directory {dir_path}: {e}'))
                            except Exception as e:
                                self.stdout.write(self.style.WARNING(f'  ⚠ Error cleaning directories: {e}'))

                if not dry_run:
                    self.stdout.write('\n=== Summary ===')
                    self.stdout.write(self.style.SUCCESS(f'✓ Deleted {stats["jobs_deleted"]} jobs'))
                    self.stdout.write(self.style.SUCCESS(f'✓ Deleted {stats["files_deleted"]} file records'))
                    if delete_files:
                        self.stdout.write(self.style.SUCCESS(f'✓ Deleted {stats["storage_cleaned"]} files from storage'))
                    if clean_temp:
                        self.stdout.write(self.style.SUCCESS(f'✓ Deleted {stats["temp_files_deleted"]} temporary files'))
                else:
                    self.stdout.write('\n=== Dry Run Summary ===')
                    self.stdout.write(f'Would delete {stats["jobs_deleted"]} jobs')
                    self.stdout.write(f'Would delete {stats["files_deleted"]} file records')
                    if delete_files:
                        self.stdout.write(f'Would delete {stats["storage_cleaned"]} files from storage')
                    if clean_temp:
                        self.stdout.write(f'Would delete {stats["temp_files_deleted"]} temporary files')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during cleanup: {e}'))
            logger.error(f'Error during upload queue cleanup: {e}', exc_info=True)
            raise

