#!/usr/bin/env python
"""
Management script for unprocessed documents
Can either delete unprocessed documents or reprocess them
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anylab.settings')
django.setup()

from ai_assistant.models import UploadedFile, DocumentFile, DocumentChunk
from django.utils import timezone
from django.db import transaction


def list_unprocessed_documents():
    """List all unprocessed documents"""
    unprocessed = UploadedFile.objects.exclude(processing_status='ready').order_by('-uploaded_at')
    failed = UploadedFile.objects.filter(processing_status='failed')
    pending = UploadedFile.objects.filter(processing_status='pending')
    
    print("\n" + "="*80)
    print("UNPROCESSED DOCUMENTS REPORT")
    print("="*80)
    print(f"\nTotal unprocessed: {unprocessed.count()}")
    print(f"  - Pending: {pending.count()}")
    print(f"  - Failed: {failed.count()}")
    print(f"  - In Progress: {unprocessed.exclude(processing_status__in=['pending', 'failed']).count()}")
    
    print("\n" + "-"*80)
    print("PENDING DOCUMENTS:")
    print("-"*80)
    for doc in pending[:20]:  # Show first 20
        print(f"  [{doc.id}] {doc.filename} (uploaded: {doc.uploaded_at.strftime('%Y-%m-%d %H:%M')})")
    if pending.count() > 20:
        print(f"  ... and {pending.count() - 20} more pending documents")
    
    print("\n" + "-"*80)
    print("FAILED DOCUMENTS:")
    print("-"*80)
    for doc in failed[:20]:  # Show first 20
        error_preview = doc.processing_error[:100] if doc.processing_error else "No error message"
        print(f"  [{doc.id}] {doc.filename}")
        print(f"      Error: {error_preview}...")
    if failed.count() > 20:
        print(f"  ... and {failed.count() - 20} more failed documents")
    
    print("\n" + "-"*80)
    print("IN PROGRESS DOCUMENTS:")
    print("-"*80)
    in_progress = unprocessed.exclude(processing_status__in=['pending', 'failed', 'ready'])
    for doc in in_progress[:20]:
        print(f"  [{doc.id}] {doc.filename} - Status: {doc.processing_status}")
    if in_progress.count() > 20:
        print(f"  ... and {in_progress.count() - 20} more in-progress documents")
    
    return unprocessed


def delete_unprocessed_documents(dry_run=False):
    """Delete all unprocessed documents and their associated data"""
    unprocessed = UploadedFile.objects.exclude(processing_status='ready')
    
    print("\n" + "="*80)
    print("DELETE UNPROCESSED DOCUMENTS")
    print("="*80)
    print(f"\nFound {unprocessed.count()} unprocessed documents")
    
    if dry_run:
        print("\n🔍 DRY RUN MODE - No files will be deleted")
        print("\nDocuments that would be deleted:")
        for doc in unprocessed[:50]:
            print(f"  - {doc.filename} (ID: {doc.id}, Status: {doc.processing_status})")
        if unprocessed.count() > 50:
            print(f"  ... and {unprocessed.count() - 50} more")
        return
    
    print("\n⚠️  WARNING: This will permanently delete:")
    print(f"  - {unprocessed.count()} unprocessed UploadedFile records")
    
    # Count related objects
    document_files = DocumentFile.objects.filter(uploaded_file__in=unprocessed)
    chunks = DocumentChunk.objects.filter(uploaded_file__in=unprocessed)
    
    print(f"  - {document_files.count()} related DocumentFile records")
    print(f"  - {chunks.count()} related DocumentChunk records")
    
    response = input("\nAre you sure you want to proceed? (type 'yes' to confirm): ")
    if response.lower() != 'yes':
        print("❌ Deletion cancelled")
        return
    
    print("\n🗑️  Deleting documents...")
    
    # Get IDs before any operations
    uploaded_ids = list(unprocessed.values_list('id', flat=True))
    
    try:
        # Delete chunks first (outside transaction to avoid cascade issues)
        chunks_deleted = chunks.delete()[0]
        print(f"  ✅ Deleted {chunks_deleted} document chunks")
        
        # Delete document files
        files_deleted = document_files.delete()[0]
        print(f"  ✅ Deleted {files_deleted} document files")
        
        # Delete uploaded files one by one, each in its own transaction
        # This avoids cascade issues with missing tables
        uploaded_deleted = 0
        for uploaded_id in uploaded_ids:
            try:
                # Use raw SQL to delete directly, avoiding Django ORM cascade issues
                from django.db import connection
                with connection.cursor() as cursor:
                    # Delete the record directly
                    cursor.execute("DELETE FROM ai_assistant_uploadedfile WHERE id = %s", [uploaded_id])
                    if cursor.rowcount > 0:
                        uploaded_deleted += 1
            except Exception as e:
                # Try Django ORM as fallback
                try:
                    UploadedFile.objects.filter(id=uploaded_id).delete()
                    uploaded_deleted += 1
                except Exception as e2:
                    print(f"  ⚠️  Could not delete file ID {uploaded_id}: {str(e2)[:100]}")
        
        print(f"  ✅ Deleted {uploaded_deleted} uploaded file records")
        
        print(f"\n✅ Successfully deleted {uploaded_deleted} unprocessed documents and all related data")
    except Exception as e:
        print(f"\n❌ Error during deletion: {e}")
        print("Some documents may have been deleted. Please check the database.")
        import traceback
        traceback.print_exc()


def reset_for_reprocessing(dry_run=False):
    """Reset unprocessed documents to 'pending' status so they can be reprocessed"""
    unprocessed = UploadedFile.objects.exclude(processing_status='ready')
    
    print("\n" + "="*80)
    print("RESET UNPROCESSED DOCUMENTS FOR REPROCESSING")
    print("="*80)
    print(f"\nFound {unprocessed.count()} unprocessed documents")
    
    if dry_run:
        print("\n🔍 DRY RUN MODE - No changes will be made")
        print("\nDocuments that would be reset:")
        for doc in unprocessed[:50]:
            print(f"  - {doc.filename} (ID: {doc.id}, Status: {doc.processing_status})")
        if unprocessed.count() > 50:
            print(f"  ... and {unprocessed.count() - 50} more")
        return
    
    print("\n⚠️  This will reset processing status to 'pending' for:")
    print(f"  - {unprocessed.count()} unprocessed documents")
    print("\nExisting chunks and embeddings will be deleted and regenerated.")
    
    response = input("\nAre you sure you want to proceed? (type 'yes' to confirm): ")
    if response.lower() != 'yes':
        print("❌ Reset cancelled")
        return
    
    print("\n🔄 Resetting documents for reprocessing...")
    
    with transaction.atomic():
        # Delete existing chunks for these documents
        chunks = DocumentChunk.objects.filter(uploaded_file__in=unprocessed)
        chunks_deleted = chunks.delete()[0]
        print(f"  ✅ Deleted {chunks_deleted} existing chunks")
        
        # Reset all processing flags
        updated = unprocessed.update(
            processing_status='pending',
            metadata_extracted=False,
            chunks_created=False,
            embeddings_created=False,
            chunk_count=0,
            embedding_count=0,
            processing_error=None,
            processing_started_at=None,
            processing_completed_at=None,
            is_truncated=False,
            processing_coverage=100.0,
        )
        print(f"  ✅ Reset {updated} documents to 'pending' status")
    
    print(f"\n✅ Successfully reset {updated} documents. They are now ready for reprocessing.")
    print("\n💡 Next steps:")
    print("   1. The documents will be automatically processed when you upload new files")
    print("   2. Or trigger processing manually via the API/admin interface")


def reprocess_documents():
    """Actually trigger reprocessing of pending documents"""
    from ai_assistant.tasks import process_file_automatically
    
    pending = UploadedFile.objects.filter(processing_status='pending')
    
    print("\n" + "="*80)
    print("REPROCESS DOCUMENTS")
    print("="*80)
    print(f"\nFound {pending.count()} pending documents")
    
    if pending.count() == 0:
        print("✅ No pending documents to process")
        return
    
    print("\n⚠️  This will queue all pending documents for processing.")
    print("   Processing will happen in the background via Celery.")
    print("   This may take a while depending on the number of documents.")
    
    response = input("\nProceed with queuing documents for processing? (type 'yes' to confirm): ")
    if response.lower() != 'yes':
        print("❌ Processing cancelled")
        return
    
    print("\n🔄 Queuing documents for background processing...")
    
    queued_count = 0
    
    for doc in pending:
        try:
            print(f"  Queuing: {doc.filename} (ID: {doc.id})...")
            # Queue via Celery task
            process_file_automatically.delay(doc.id)
            queued_count += 1
            print(f"    ✅ Queued")
        except Exception as e:
            print(f"    ❌ Error queuing: {str(e)}")
    
    print(f"\n✅ Queued {queued_count} documents for processing")
    print("\n💡 Documents are now being processed in the background.")
    print("   Check the status in the admin interface or via the API.")


def main():
    """Main menu"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
    else:
        print("\n" + "="*80)
        print("UNPROCESSED DOCUMENTS MANAGER")
        print("="*80)
        print("\nOptions:")
        print("  1. list          - List all unprocessed documents")
        print("  2. delete       - Delete all unprocessed documents (permanent)")
        print("  3. reset         - Reset unprocessed documents to 'pending' status")
        print("  4. reprocess     - Reprocess all pending documents now")
        print("  5. dry-run       - Show what would be deleted/reset (no changes)")
        print("\nUsage:")
        print("  python manage_unprocessed_documents.py <command>")
        print("\nExamples:")
        print("  python manage_unprocessed_documents.py list")
        print("  python manage_unprocessed_documents.py delete")
        print("  python manage_unprocessed_documents.py reset")
        print("  python manage_unprocessed_documents.py reprocess")
        return
    
    if command == 'list':
        list_unprocessed_documents()
    elif command == 'delete':
        delete_unprocessed_documents(dry_run=False)
    elif command == 'reset':
        reset_for_reprocessing(dry_run=False)
    elif command == 'reprocess':
        reprocess_documents()
    elif command == 'dry-run':
        print("\n🔍 DRY RUN MODE")
        print("\n1. DELETE OPERATION:")
        delete_unprocessed_documents(dry_run=True)
        print("\n2. RESET OPERATION:")
        reset_for_reprocessing(dry_run=True)
    else:
        print(f"❌ Unknown command: {command}")
        print("Use 'list', 'delete', 'reset', 'reprocess', or 'dry-run'")


if __name__ == '__main__':
    main()

