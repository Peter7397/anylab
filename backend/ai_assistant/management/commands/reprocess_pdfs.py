import os
import fitz  # PyMuPDF
import hashlib
import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.storage import default_storage
from ai_assistant.models import DocumentFile, PDFDocument, UploadedFile, DocumentChunk
from ai_assistant.rag_service import EnhancedRAGService

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Reprocess existing PDF files to extract text content and create searchable chunks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reprocessing even if chunks already exist',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without actually doing it',
        )
        parser.add_argument(
            '--file-id',
            type=int,
            help='Process only a specific file ID',
        )

    def handle(self, *args, **options):
        force = options['force']
        dry_run = options['dry_run']
        file_id = options['file_id']
        
        self.stdout.write(
            self.style.SUCCESS('Starting PDF reprocessing...')
        )
        
        # Initialize RAG service
        rag_service = EnhancedRAGService()
        
        # Get all PDF files
        pdf_files = []
        
        # Get DocumentFile PDFs
        doc_pdfs = DocumentFile.objects.filter(document_type='pdf')
        if file_id:
            doc_pdfs = doc_pdfs.filter(id=file_id)
        
        for doc in doc_pdfs:
            if doc.file and doc.file.name:
                pdf_files.append({
                    'id': doc.id,
                    'title': doc.title,
                    'file_path': doc.file.path if hasattr(doc.file, 'path') else None,
                    'file_name': doc.file.name,
                    'model': 'DocumentFile',
                    'uploaded_by': doc.uploaded_by
                })
        
        # Get legacy PDFDocument PDFs
        legacy_pdfs = PDFDocument.objects.all()
        if file_id:
            legacy_pdfs = legacy_pdfs.filter(id=file_id)
            
        for pdf in legacy_pdfs:
            if pdf.file and pdf.file.name:
                pdf_files.append({
                    'id': pdf.id,
                    'title': pdf.title,
                    'file_path': pdf.file.path if hasattr(pdf.file, 'path') else None,
                    'file_name': pdf.file.name,
                    'model': 'PDFDocument',
                    'uploaded_by': pdf.uploaded_by
                })
        
        self.stdout.write(f"Found {len(pdf_files)} PDF files to process")
        
        if dry_run:
            self.stdout.write("DRY RUN - No files will be processed")
            for pdf in pdf_files:
                self.stdout.write(f"  - {pdf['title']} ({pdf['model']} ID: {pdf['id']})")
            return
        
        processed_count = 0
        error_count = 0
        
        for pdf_info in pdf_files:
            try:
                self.stdout.write(f"Processing: {pdf_info['title']} (ID: {pdf_info['id']})")
                
                # Check if file exists
                if not pdf_info['file_path'] or not os.path.exists(pdf_info['file_path']):
                    self.stdout.write(
                        self.style.WARNING(f"  File not found: {pdf_info['file_name']}")
                    )
                    error_count += 1
                    continue
                
                # Check if already processed (unless force is True)
                if not force:
                    existing_chunks = DocumentChunk.objects.filter(
                        uploaded_file__filename=pdf_info['title']
                    ).count()
                    if existing_chunks > 0:
                        self.stdout.write(
                            self.style.WARNING(f"  Already processed ({existing_chunks} chunks exist)")
                        )
                        continue
                
                # Process the PDF file
                success = self._process_pdf_file(
                    pdf_info, rag_service
                )
                
                if success:
                    processed_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✓ Successfully processed")
                    )
                else:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f"  ✗ Failed to process")
                    )
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"  ✗ Error processing {pdf_info['title']}: {str(e)}")
                )
                logger.error(f"Error processing PDF {pdf_info['title']}: {e}")
        
        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write(
            self.style.SUCCESS(f"Processing complete!")
        )
        self.stdout.write(f"  Processed: {processed_count}")
        self.stdout.write(f"  Errors: {error_count}")
        self.stdout.write(f"  Total: {len(pdf_files)}")

    def _process_pdf_file(self, pdf_info, rag_service):
        """Process a single PDF file and create text chunks"""
        try:
            file_path = pdf_info['file_path']
            
            # Compute file hash
            file_hash = self._compute_file_hash(file_path)
            
            # Check if UploadedFile already exists
            uploaded_file, created = UploadedFile.objects.get_or_create(
                file_hash=file_hash,
                defaults={
                    'filename': pdf_info['title'],
                    'file_size': os.path.getsize(file_path),
                    'uploaded_by': pdf_info['uploaded_by']
                }
            )
            
            if not created:
                # File already exists, check if it has chunks
                existing_chunks = DocumentChunk.objects.filter(uploaded_file=uploaded_file).count()
                if existing_chunks > 0:
                    self.stdout.write(f"    File already has {existing_chunks} chunks")
                    return True
            
            # Process PDF with PyMuPDF
            doc = fitz.open(file_path)
            chunks = []
            page_count = len(doc)
            
            for page_num, page in enumerate(doc, start=1):
                text = page.get_text()
                if text.strip():
                    chunks.append(text)
            
            doc.close()
            
            # Update UploadedFile with page count
            uploaded_file.page_count = page_count
            uploaded_file.intro = chunks[0][:200] if chunks else None
            uploaded_file.save()
            
            # Create document chunks (without embeddings for now to speed up processing)
            for idx, content in enumerate(chunks):
                DocumentChunk.objects.create(
                    uploaded_file=uploaded_file,
                    content=content,
                    page_number=idx + 1,
                    chunk_index=idx
                )
            
            self.stdout.write(f"    Created {len(chunks)} text chunks")
            return True
            
        except Exception as e:
            logger.error(f"Error processing PDF file {pdf_info['title']}: {e}")
            return False

    def _compute_file_hash(self, file_path):
        """Compute SHA-256 hash of a file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
