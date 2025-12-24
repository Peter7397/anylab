"""
Management command to add HTML files to existing SSB_KPR documents that don't have files

This command:
1. Finds all SSB_KPR documents without files
2. Attempts to recreate HTML from metadata and chunks
3. Saves the HTML as files
4. Updates the documents with the file field populated
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.files.base import ContentFile
from ai_assistant.models import DocumentFile, DocumentChunk
import json
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Add HTML files to existing SSB_KPR documents without files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview what would be done without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write('=' * 60)
        self.stdout.write('SSB_KPR File Retrofit Command')
        self.stdout.write('=' * 60)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN MODE - No changes will be made\n'))
        
        # Find documents without files
        kpr_docs = DocumentFile.objects.filter(document_type='SSB_KPR')
        docs_without_files = kpr_docs.filter(file__isnull=True) | kpr_docs.filter(file='')
        total_count = docs_without_files.count()
        
        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('✓ All SSB_KPR documents already have files'))
            return
        
        self.stdout.write(f'\nFound {total_count} SSB_KPR documents without files')
        
        updated_count = 0
        skipped_count = 0
        
        for doc in docs_without_files:
            try:
                # Try to recreate HTML from chunks
                chunks = DocumentChunk.objects.filter(
                    document_file=doc
                ).order_by('chunk_index', 'page_number')
                
                if chunks.exists():
                    # Reconstruct HTML from chunks
                    html_content = self._reconstruct_html_from_chunks(chunks, doc)
                    
                    if html_content:
                        if not dry_run:
                            # Create HTML file
                            html_filename = f"SSB_{doc.metadata.get('kpr_number', doc.id)}.html"
                            html_bytes = html_content.encode('utf-8')
                            html_file = ContentFile(html_bytes, name=html_filename)
                            
                            # Save file
                            doc.file = html_file
                            doc.file_size = len(html_bytes)
                            if not doc.filename or doc.filename == '':
                                doc.filename = html_filename
                            doc.save()
                            
                        self.stdout.write(self.style.SUCCESS(
                            f'✓ Updated: {doc.title}'
                        ))
                        updated_count += 1
                    else:
                        self.stdout.write(self.style.WARNING(
                            f'⚠ Skipped: {doc.title} (no content to recreate)'
                        ))
                        skipped_count += 1
                else:
                    # No chunks available - create placeholder HTML
                    if not dry_run:
                        html_content = self._create_placeholder_html(doc)
                        html_bytes = html_content.encode('utf-8')
                        html_file = ContentFile(html_bytes, name=f"SSB_{doc.id}.html")
                        
                        doc.file = html_file
                        doc.file_size = len(html_bytes)
                        if not doc.filename or doc.filename == '':
                            doc.filename = f"SSB_{doc.id}.html"
                        doc.save()
                    
                    self.stdout.write(self.style.WARNING(
                        f'⚠ Created placeholder for: {doc.title} (no chunks)'
                    ))
                    updated_count += 1
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'✗ Error updating {doc.title}: {e}'
                ))
                skipped_count += 1
        
        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('Summary:')
        self.stdout.write(f'  Total found: {total_count}')
        self.stdout.write(f'  Updated: {updated_count}')
        self.stdout.write(f'  Skipped: {skipped_count}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nThis was a DRY RUN. No changes were made.'))
            self.stdout.write('Run without --dry-run to apply changes.')
        else:
            self.stdout.write(self.style.SUCCESS('\n✓ Retrofit completed!'))

    def _reconstruct_html_from_chunks(self, chunks, doc):
        """Reconstruct HTML from document chunks"""
        html_parts = ['<html><head><title>%s</title></head><body>' % doc.title]
        html_parts.append('<h1>%s</h1>' % doc.title)
        
        if doc.description:
            html_parts.append(f'<p><strong>Description:</strong> {doc.description}</p>')
        
        if doc.metadata:
            metadata = doc.metadata if isinstance(doc.metadata, dict) else json.loads(doc.metadata)
            html_parts.append('<h2>Metadata</h2>')
            html_parts.append('<ul>')
            for key, value in metadata.items():
                if isinstance(value, list):
                    value = ', '.join(str(v) for v in value)
                html_parts.append(f'<li><strong>{key}:</strong> {value}</li>')
            html_parts.append('</ul>')
        
        html_parts.append('<h2>Content</h2>')
        
        for chunk in chunks:
            html_parts.append(f'<p>{chunk.content}</p>')
        
        html_parts.append('</body></html>')
        return ''.join(html_parts)

    def _create_placeholder_html(self, doc):
        """Create a placeholder HTML file with metadata only"""
        metadata = doc.metadata if isinstance(doc.metadata, dict) else json.loads(doc.metadata) if doc.metadata else {}
        
        html = f'''<!DOCTYPE html>
<html>
<head>
    <title>{doc.title}</title>
    <meta charset="utf-8">
</head>
<body>
    <h1>{doc.title}</h1>
    <p><strong>Document Type:</strong> SSB_KPR</p>
    <p><strong>Description:</strong> {doc.description or 'N/A'}</p>
    
    <h2>Metadata</h2>
    <ul>
'''
        
        for key, value in metadata.items():
            if isinstance(value, list):
                value = ', '.join(str(v) for v in value)
            html += f'        <li><strong>{key}:</strong> {value}</li>\n'
        
        html += '''    </ul>
    
    <p><em>Note: This file was created retroactively from metadata.</em></p>
</body>
</html>'''
        
        return html

