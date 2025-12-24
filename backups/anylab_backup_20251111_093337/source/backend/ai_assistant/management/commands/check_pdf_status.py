from django.core.management.base import BaseCommand
from ai_assistant.models import DocumentFile, PDFDocument, DocumentChunk, UploadedFile

class Command(BaseCommand):
    help = 'Check the processing status of existing PDF files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed information for each file',
        )

    def handle(self, *args, **options):
        detailed = options['detailed']
        
        self.stdout.write(
            self.style.SUCCESS('Checking PDF processing status...')
        )
        
        # Get all PDF files
        pdf_files = []
        
        # Get DocumentFile PDFs
        doc_pdfs = DocumentFile.objects.filter(document_type='pdf')
        for doc in doc_pdfs:
            pdf_files.append({
                'id': doc.id,
                'title': doc.title,
                'model': 'DocumentFile',
                'file_name': doc.file.name if doc.file else None,
                'page_count': doc.page_count,
                'file_size': doc.file_size,
                'uploaded_by': doc.uploaded_by,
                'uploaded_at': doc.uploaded_at
            })
        
        # Get legacy PDFDocument PDFs
        legacy_pdfs = PDFDocument.objects.all()
        for pdf in legacy_pdfs:
            pdf_files.append({
                'id': pdf.id,
                'title': pdf.title,
                'model': 'PDFDocument',
                'file_name': pdf.file.name if pdf.file else None,
                'page_count': pdf.page_count,
                'file_size': pdf.file_size,
                'uploaded_by': pdf.uploaded_by,
                'uploaded_at': pdf.uploaded_at
            })
        
        self.stdout.write(f"Found {len(pdf_files)} PDF files")
        
        # Check processing status
        processed_count = 0
        unprocessed_count = 0
        total_chunks = 0
        
        for pdf_info in pdf_files:
            # Check if this PDF has been processed into chunks
            chunks = DocumentChunk.objects.filter(
                uploaded_file__filename=pdf_info['title']
            )
            
            chunk_count = chunks.count()
            has_embeddings = chunks.filter(embedding__isnull=False).count()
            
            if chunk_count > 0:
                processed_count += 1
                total_chunks += chunk_count
                status = "✓ Processed"
                if has_embeddings == chunk_count:
                    status += " (with embeddings)"
                elif has_embeddings > 0:
                    status += f" (partial embeddings: {has_embeddings}/{chunk_count})"
                else:
                    status += " (no embeddings)"
            else:
                unprocessed_count += 1
                status = "✗ Not processed"
            
            if detailed:
                self.stdout.write(f"\n{pdf_info['title']} ({pdf_info['model']} ID: {pdf_info['id']})")
                self.stdout.write(f"  Status: {status}")
                self.stdout.write(f"  File: {pdf_info['file_name']}")
                self.stdout.write(f"  Pages: {pdf_info['page_count']}")
                self.stdout.write(f"  Size: {pdf_info['file_size']} bytes")
                self.stdout.write(f"  Uploaded by: {pdf_info['uploaded_by']}")
                self.stdout.write(f"  Uploaded at: {pdf_info['uploaded_at']}")
                if chunk_count > 0:
                    self.stdout.write(f"  Chunks: {chunk_count}")
                    self.stdout.write(f"  Embeddings: {has_embeddings}/{chunk_count}")
            else:
                self.stdout.write(f"  {pdf_info['title']}: {status}")
        
        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write(
            self.style.SUCCESS(f"Status Summary:")
        )
        self.stdout.write(f"  Total PDFs: {len(pdf_files)}")
        self.stdout.write(f"  Processed: {processed_count}")
        self.stdout.write(f"  Unprocessed: {unprocessed_count}")
        self.stdout.write(f"  Total chunks: {total_chunks}")
        
        if unprocessed_count > 0:
            self.stdout.write(
                self.style.WARNING(f"\n{unprocessed_count} PDFs need processing. Run:")
            )
            self.stdout.write("  python manage.py reprocess_pdfs")
        
        # Check for chunks without embeddings
        chunks_without_embeddings = DocumentChunk.objects.filter(embedding__isnull=True).count()
        if chunks_without_embeddings > 0:
            self.stdout.write(
                self.style.WARNING(f"\n{chunks_without_embeddings} chunks need embeddings. Run:")
            )
            self.stdout.write("  python manage.py add_embeddings")
