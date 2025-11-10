"""
Django management command to check documents in database

Shows detailed information about where documents are stored and their status.
"""

from django.core.management.base import BaseCommand
from ai_assistant.models import UploadedFile, DocumentFile, DocumentChunk

class Command(BaseCommand):
    help = 'Check documents in database and their processing status'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('Database Document Check'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('')

        # Check UploadedFile model
        self.stdout.write(self.style.SUCCESS('=== UploadedFile Model ==='))
        total_uploaded = UploadedFile.objects.count()
        ready_uploaded = UploadedFile.objects.filter(processing_status='ready').count()
        chunks_created_flag = UploadedFile.objects.filter(chunks_created=True).count()
        
        # Count documents with actual chunks
        uploaded_with_chunks = UploadedFile.objects.filter(
            id__in=DocumentChunk.objects.values_list('uploaded_file_id', flat=True).distinct()
        ).count()
        
        self.stdout.write(f'Total UploadedFiles: {total_uploaded}')
        self.stdout.write(f'  With status "ready": {ready_uploaded}')
        self.stdout.write(f'  With chunks_created=True: {chunks_created_flag}')
        self.stdout.write(f'  With actual chunks: {uploaded_with_chunks}')
        self.stdout.write('')

        # Check DocumentFile model
        self.stdout.write(self.style.SUCCESS('=== DocumentFile Model ==='))
        total_docfiles = DocumentFile.objects.count()
        docfiles_with_uploaded = DocumentFile.objects.exclude(uploaded_file__isnull=True).count()
        docfiles_with_chunks = DocumentFile.objects.filter(
            uploaded_file__in=UploadedFile.objects.filter(
                id__in=DocumentChunk.objects.values_list('uploaded_file_id', flat=True).distinct()
            )
        ).count()
        
        self.stdout.write(f'Total DocumentFiles: {total_docfiles}')
        self.stdout.write(f'  With uploaded_file linked: {docfiles_with_uploaded}')
        self.stdout.write(f'  With chunks (via uploaded_file): {docfiles_with_chunks}')
        self.stdout.write('')

        # Check DocumentChunk
        self.stdout.write(self.style.SUCCESS('=== DocumentChunk Model ==='))
        total_chunks = DocumentChunk.objects.count()
        chunks_linked_uploaded = DocumentChunk.objects.exclude(uploaded_file__isnull=True).count()
        chunks_linked_docfile = DocumentChunk.objects.exclude(document_file__isnull=True).count()
        
        self.stdout.write(f'Total chunks: {total_chunks}')
        self.stdout.write(f'  Linked to UploadedFile: {chunks_linked_uploaded}')
        self.stdout.write(f'  Linked to DocumentFile: {chunks_linked_docfile}')
        self.stdout.write('')

        # Show sample ready documents
        self.stdout.write(self.style.SUCCESS('=== Sample Ready Documents (UploadedFile) ==='))
        ready_docs = UploadedFile.objects.filter(processing_status='ready')[:10]
        if ready_docs:
            for doc in ready_docs:
                chunk_count = DocumentChunk.objects.filter(uploaded_file=doc).count()
                self.stdout.write(
                    f'ID {doc.id}: {doc.filename[:60]:60} - '
                    f'chunks_created={doc.chunks_created}, actual_chunks={chunk_count}'
                )
        else:
            self.stdout.write('  No documents with status "ready"')
        self.stdout.write('')

        # Check documents with chunks but chunks_created=False
        self.stdout.write(self.style.SUCCESS('=== Documents with chunks but chunks_created=False ==='))
        docs_with_chunks = UploadedFile.objects.filter(
            id__in=DocumentChunk.objects.values_list('uploaded_file_id', flat=True).distinct()
        ).filter(chunks_created=False)
        count_mismatch = docs_with_chunks.count()
        self.stdout.write(f'Count: {count_mismatch}')
        if count_mismatch > 0:
            for doc in docs_with_chunks[:10]:
                chunk_count = DocumentChunk.objects.filter(uploaded_file=doc).count()
                self.stdout.write(
                    f'ID {doc.id}: {doc.filename[:60]:60} - '
                    f'status={doc.processing_status}, chunks={chunk_count}'
                )
        self.stdout.write('')

        # Check DocumentFile -> UploadedFile links
        self.stdout.write(self.style.SUCCESS('=== DocumentFile -> UploadedFile Links ==='))
        docfiles = DocumentFile.objects.exclude(uploaded_file__isnull=True)[:10]
        if docfiles:
            for docfile in docfiles:
                uploaded = docfile.uploaded_file
                chunk_count = DocumentChunk.objects.filter(uploaded_file=uploaded).count() if uploaded else 0
                self.stdout.write(
                    f'DocumentFile ID {docfile.id}: {docfile.title[:50]:50} -> '
                    f'UploadedFile ID {uploaded.id if uploaded else "None"} '
                    f'(chunks={chunk_count})'
                )
        else:
            self.stdout.write('  No DocumentFiles linked to UploadedFiles')
        self.stdout.write('')

        # Summary and recommendations
        self.stdout.write(self.style.SUCCESS('=== Recommendations ==='))
        
        if total_chunks > 0 and uploaded_with_chunks > 0:
            self.stdout.write(self.style.SUCCESS(
                f'✅ Found {uploaded_with_chunks} documents with chunks!'
            ))
            self.stdout.write('')
            self.stdout.write('To reprocess for GraphRAG improvements:')
            self.stdout.write('  python manage.py reprocess_graph_rag --any-status')
        else:
            self.stdout.write(self.style.WARNING(
                '⚠️  No documents with chunks found'
            ))
            self.stdout.write('')
            self.stdout.write('Documents need to be processed first:')
            self.stdout.write('  python manage.py reprocess_pdfs')

