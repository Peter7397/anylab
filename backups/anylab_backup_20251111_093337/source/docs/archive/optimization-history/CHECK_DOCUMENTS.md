# Check Documents in Database

Run these commands in Django shell to see what's actually in your database:

```bash
cd /Volumes/Orico/Anylab103/backend
source venv/bin/activate
python manage.py shell
```

Then in the shell (NO indentation, start at column 0):

```python
from ai_assistant.models import UploadedFile, DocumentFile, DocumentChunk

# Check UploadedFile model
print("=== UploadedFile Model ===")
print(f"Total UploadedFiles: {UploadedFile.objects.count()}")
print(f"With status 'ready': {UploadedFile.objects.filter(processing_status='ready').count()}")
print(f"With chunks_created=True: {UploadedFile.objects.filter(chunks_created=True).count()}")
print(f"With actual chunks: {UploadedFile.objects.filter(id__in=DocumentChunk.objects.values_list('uploaded_file_id', flat=True).distinct()).count()}")

# Check DocumentFile model
print("\n=== DocumentFile Model ===")
print(f"Total DocumentFiles: {DocumentFile.objects.count()}")
print(f"With uploaded_file linked: {DocumentFile.objects.exclude(uploaded_file__isnull=True).count()}")

# Check DocumentChunk
print("\n=== DocumentChunk Model ===")
print(f"Total chunks: {DocumentChunk.objects.count()}")
print(f"Linked to UploadedFile: {DocumentChunk.objects.exclude(uploaded_file__isnull=True).count()}")
print(f"Linked to DocumentFile: {DocumentChunk.objects.exclude(document_file__isnull=True).count()}")

# Show sample ready documents
print("\n=== Sample Ready Documents (UploadedFile) ===")
ready_docs = UploadedFile.objects.filter(processing_status='ready')[:5]
for doc in ready_docs:
    chunk_count = DocumentChunk.objects.filter(uploaded_file=doc).count()
    print(f"ID {doc.id}: {doc.filename[:50]} - chunks_created={doc.chunks_created}, actual_chunks={chunk_count}")

# Check if documents have chunks but chunks_created=False
print("\n=== Documents with chunks but chunks_created=False ===")
docs_with_chunks = UploadedFile.objects.filter(
    id__in=DocumentChunk.objects.values_list('uploaded_file_id', flat=True).distinct()
).filter(chunks_created=False)
print(f"Count: {docs_with_chunks.count()}")
for doc in docs_with_chunks[:5]:
    chunk_count = DocumentChunk.objects.filter(uploaded_file=doc).count()
    print(f"ID {doc.id}: {doc.filename[:50]} - status={doc.processing_status}, chunks={chunk_count}")
```

This will show you:
1. Where your documents are stored
2. What their actual status is
3. Whether they have chunks
4. Why the command isn't finding them

