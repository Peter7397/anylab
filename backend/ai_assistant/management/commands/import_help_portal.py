"""
Management command to import and process help portal documents

Usage:
    python manage.py import_help_portal
    python manage.py import_help_portal --force  # Reprocess even if already processed
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from ai_assistant.models import HelpPortalDocument, UploadedFile, DocumentChunk
from ai_assistant.rag_service import EnhancedRAGService
import os
import hashlib
import logging
from pathlib import Path
import re

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Import and process help portal documents'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reprocessing of already processed documents',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        # Find help portal documents
        # __file__ is ai_assistant/management/commands/import_help_portal.py
        # .parent.parent.parent.parent goes up to 'backend' directory
        help_portal_path = Path(__file__).parent.parent.parent.parent / 'media' / 'documents' / 'help_portal' / 'Docs' / 'EN'
        
        if not help_portal_path.exists():
            self.stdout.write(
                self.style.ERROR(f'Help portal directory not found: {help_portal_path}')
            )
            return
        
        # Find all PDFs
        pdf_files = list(help_portal_path.glob('*.pdf'))
        
        if not pdf_files:
            self.stdout.write(self.style.WARNING('No PDF files found in help portal directory'))
            return
        
        self.stdout.write(f'Found {len(pdf_files)} PDF files')
        
        # Initialize RAG service
        rag_service = EnhancedRAGService()
        
        stats = {
            'total': len(pdf_files),
            'processed': 0,
            'skipped': 0,
            'failed': 0,
        }
        
        for pdf_file in sorted(pdf_files):
            try:
                self.stdout.write(f'\nProcessing: {pdf_file.name}')
                result = self._process_document(pdf_file, rag_service, force)
                
                if result == 'skipped':
                    stats['skipped'] += 1
                elif result == 'failed':
                    stats['failed'] += 1
                else:
                    stats['processed'] += 1
                    self.stdout.write(self.style.SUCCESS(f'✓ Processed: {pdf_file.name}'))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error processing {pdf_file.name}: {str(e)}'))
                stats['failed'] += 1
                logger.error(f'Error processing {pdf_file.name}: {str(e)}', exc_info=True)
        
        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('Processing complete!'))
        self.stdout.write(f'  Total files: {stats["total"]}')
        self.stdout.write(f'  Processed: {stats["processed"]}')
        self.stdout.write(f'  Skipped: {stats["skipped"]}')
        self.stdout.write(f'  Failed: {stats["failed"]}')
    
    def _process_document(self, pdf_file, rag_service, force):
        """Process a single document"""
        
        # Calculate file hash
        file_hash = self._compute_file_hash(pdf_file)
        
        # Check if document already exists
        help_doc, created = HelpPortalDocument.objects.get_or_create(
            file_hash=file_hash,
            defaults={
                'filename': pdf_file.name,
                'file_path': str(pdf_file),
                'file_size': pdf_file.stat().st_size,
                'category': self._classify_document(pdf_file.name),
                'document_type': self._extract_document_type(pdf_file.name),
                'version': self._extract_version(pdf_file.name),
                'status': 'pending',
            }
        )
        
        # Skip if already processed and not forcing
        if not created and help_doc.status == 'completed' and not force:
            return 'skipped'
        
        # Check if UploadedFile already exists
        uploaded_file = None
        if help_doc.uploaded_file:
            uploaded_file = help_doc.uploaded_file
            # Check for existing chunks
            existing_chunks = DocumentChunk.objects.filter(uploaded_file=uploaded_file).count()
            if existing_chunks > 0 and not force:
                help_doc.status = 'completed'
                help_doc.chunk_count = existing_chunks
                help_doc.save()
                return 'skipped'
        
        try:
            # Update status to processing
            help_doc.status = 'processing'
            help_doc.save()
            
            # Process the PDF
            if not uploaded_file:
                result = rag_service.process_pdf_and_build_index(
                    pdf_file,
                    title=pdf_file.stem,
                    file_hash=file_hash
                )
                
                if result.get('success'):
                    uploaded_file_id = result.get('uploaded_file_id')
                    uploaded_file = UploadedFile.objects.get(id=uploaded_file_id)
                else:
                    help_doc.status = 'failed'
                    help_doc.error_message = result.get('error', 'Unknown error')
                    help_doc.save()
                    return 'failed'
            else:
                # Update chunk count
                chunks = DocumentChunk.objects.filter(uploaded_file=uploaded_file).count()
                help_doc.chunk_count = chunks
            
            # Update help document
            help_doc.uploaded_file = uploaded_file
            help_doc.status = 'completed'
            help_doc.processed_at = timezone.now()
            help_doc.chunk_count = DocumentChunk.objects.filter(uploaded_file=uploaded_file).count()
            help_doc.save()
            
            return 'success'
            
        except Exception as e:
            help_doc.status = 'failed'
            help_doc.error_message = str(e)
            help_doc.save()
            logger.error(f'Error processing {pdf_file.name}: {str(e)}', exc_info=True)
            return 'failed'
    
    def _compute_file_hash(self, file_path):
        """Compute MD5 hash of file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _classify_document(self, filename):
        """Classify document by filename"""
        filename_lower = filename.lower()
        
        if 'cds' in filename_lower:
            return 'cds'
        elif 'ecm' in filename_lower or 'openlab-server' in filename_lower:
            return 'ecm'
        elif 'testservices' in filename_lower or 'test-services' in filename_lower:
            return 'services'
        elif 'sample' in filename_lower or 'balancebridge' in filename_lower:
            return 'shared'
        else:
            return 'other'
    
    def _extract_document_type(self, filename):
        """Extract document type from filename"""
        filename_lower = filename.lower()
        
        if 'install' in filename_lower:
            return 'Installation Guide'
        elif 'admin' in filename_lower:
            return 'Administration Guide'
        elif 'user' in filename_lower:
            return 'User Guide'
        elif 'release' in filename_lower:
            return 'Release Notes'
        elif 'requirement' in filename_lower:
            return 'Requirements Document'
        elif 'configure' in filename_lower or 'config' in filename_lower:
            return 'Configuration Guide'
        elif 'quick' in filename_lower or 'reference' in filename_lower:
            return 'Quick Reference'
        elif 'declaration' in filename_lower:
            return 'Quality Declaration'
        else:
            return 'Documentation'
    
    def _extract_version(self, filename):
        """Extract version from filename"""
        # Look for patterns like v2.8, v3.6, 2.8, 3.6
        match = re.search(r'v?([0-9]+\.[0-9]+)', filename)
        if match:
            return f"v{match.group(1)}"
        return ''

