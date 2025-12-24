"""
Management command to extract and populate metadata for existing documents.

Usage:
    python manage.py extract_document_metadata [--dry-run] [--limit=N]
"""

import json
import logging
from django.core.management.base import BaseCommand
from ai_assistant.models import DocumentFile
from ai_assistant.utils.product_detector import detect_product, detect_content_type
from ai_assistant.utils.version_detector import detect_version

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Extract and populate metadata for existing documents'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without saving changes to database',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of documents to process',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if metadata already exists',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']
        force = options['force']
        
        self.stdout.write(self.style.SUCCESS('Starting metadata extraction...'))
        
        # Get all documents
        queryset = DocumentFile.objects.all()
        
        if not force:
            # Only process documents without metadata or with empty metadata
            queryset = queryset.filter(
                **{}  # Will filter for empty metadata
            )
        
        # Apply limit if specified
        if limit:
            queryset = queryset[:limit]
        
        total_docs = queryset.count()
        self.stdout.write(f'Found {total_docs} documents to process')
        
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        for doc in queryset:
            try:
                # Skip if metadata already exists and not forcing
                current_metadata = {}
                if doc.metadata:
                    try:
                        current_metadata = json.loads(doc.metadata) if isinstance(doc.metadata, str) else doc.metadata
                    except json.JSONDecodeError:
                        pass
                
                if current_metadata and not force:
                    if (current_metadata.get('product_category') or 
                        current_metadata.get('content_type') or 
                        current_metadata.get('version')):
                        skipped_count += 1
                        self.stdout.write(self.style.WARNING(f'Skipping {doc.title} (metadata already exists)'))
                        continue
                
                # Create search text from title, filename, and description
                search_text = f"{doc.title} {doc.filename} {doc.description or ''}"
                
                # Auto-detect metadata
                product_category = detect_product(search_text) or ''
                content_type = detect_content_type(search_text) or ''
                version = detect_version(search_text) or ''
                
                # Only update if we detected something or if forcing
                if product_category or content_type or version or force:
                    # Prepare metadata
                    new_metadata = {
                        'product_category': product_category,
                        'content_type': content_type,
                        'version': version,
                        'document_type': doc.document_type
                    }
                    
                    # Merge with existing metadata
                    if current_metadata:
                        new_metadata.update(current_metadata)
                    
                    # Update the document
                    doc.metadata = json.dumps(new_metadata)
                    
                    if not dry_run:
                        doc.save()
                    
                    updated_count += 1
                    
                    # Show what was detected
                    detected = []
                    if product_category:
                        detected.append(f"Product: {product_category}")
                    if content_type:
                        detected.append(f"Type: {content_type}")
                    if version:
                        detected.append(f"Version: {version}")
                    
                    if detected:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✓ {doc.title[:50]} - {", ".join(detected)}'
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  {doc.title[:50]} - No metadata detected'
                            )
                        )
                else:
                    skipped_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'  {doc.title[:50]} - No metadata detected')
                    )
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'✗ Error processing {doc.title}: {str(e)}')
                )
                logger.error(f"Error processing document {doc.id}: {e}")
        
        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('Summary:'))
        self.stdout.write(f'  Total documents: {total_docs}')
        self.stdout.write(f'  Updated: {updated_count}')
        self.stdout.write(f'  Skipped: {skipped_count}')
        self.stdout.write(f'  Errors: {error_count}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN - No changes were saved'))
            self.stdout.write('Run without --dry-run to apply changes')
        else:
            self.stdout.write(self.style.SUCCESS(f'\nSuccessfully updated {updated_count} documents!'))

