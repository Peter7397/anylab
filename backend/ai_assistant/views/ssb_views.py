"""
SSB Import View - DEPRECATED

This endpoint is no longer used. All document uploads now go through
the standard document upload flow (/api/ai/documents/upload/) which
automatically creates chunks and embeddings for RAG.

Kept for reference but not registered in URLs.
"""

import logging
import json
import re
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import DocumentFile, DocumentChunk
from ..serializers import DocumentSerializer
from .base_views import (
    success_response, error_response, bad_request_response
)

logger = logging.getLogger(__name__)


def _create_ssb_chunks(document_file: DocumentFile, file_content: str):
    """Create RAG chunks from SSB file content"""
    try:
        from ai_assistant.services import EmbeddingService
        
        # Split content into chunks (simple approach - 1000 chars per chunk)
        chunk_size = 1000
        chunks = []
        for i in range(0, len(file_content), chunk_size):
            chunk_text = file_content[i:i+chunk_size]
            if chunk_text.strip():
                chunks.append({
                    'content': chunk_text,
                    'index': i // chunk_size
                })
        
        # Create DocumentChunk entries (without embeddings for now - will be indexed when needed)
        for chunk_data in chunks:
            DocumentChunk.objects.create(
                document_file=document_file,
                content=chunk_data['content'],
                page_number=1,
                chunk_index=chunk_data['index'],
                created_at=timezone.now()
            )
        
        logger.info(f"Created {len(chunks)} RAG chunks for SSB file {document_file.filename}")
        
    except Exception as e:
        logger.error(f"Error creating RAG chunks for SSB file: {e}")
        # Don't fail the import if chunking fails


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def import_ssb_file(request):
    """Import SSB/KPR data from uploaded HTML or text file"""
    try:
        if 'file' not in request.FILES:
            return bad_request_response('No file provided')

        uploaded_file = request.FILES['file']
        filename = uploaded_file.name
        logger.info(f"Processing uploaded file: {filename}")
        
        # Read file content
        try:
            file_content = uploaded_file.read().decode('utf-8')
        except UnicodeDecodeError:
            # Try with different encoding for MHTML or other formats
            uploaded_file.seek(0)
            file_content = uploaded_file.read().decode('latin-1')
            logger.info("Used latin-1 encoding to read file")
        
        logger.info(f"File size: {len(file_content)} characters")
        
        # Skip parsing for large files - just store as reference file
        # Extract product info from filename (e.g., "M84xx" -> product info)
        product_name = "Agilent Products"
        if "M84" in filename:
            product_name = "Agilent Mass Spectrometry (M84xx Series)"
        elif "77xx" in filename or "78xx" in filename:
            product_name = "Agilent GC (77xx/78xx Series)"
        
        # Count approximate KPR entries (quick regex count without full parsing)
        kpr_count = len(re.findall(r'KPR#:\s*\d+', file_content))
        
        # Store as a single file, not individual KPRs
        # Check if file with same name already exists
        existing = DocumentFile.objects.filter(
            document_type='SSB_KPR',
            filename=filename
        ).first()
        
        imported_count = 0
        updated_count = 0
        
        # Save the uploaded file to storage
        from django.core.files.base import ContentFile
        from django.core.files.storage import default_storage
        file_content_bytes = file_content.encode('utf-8')
        content_file = ContentFile(file_content_bytes, name=filename)
        
        if existing:
            # Update existing - delete old file and save new one
            if existing.file:
                existing.file.delete(save=False)
            existing.title = filename
            existing.filename = filename
            existing.description = f"KPR index file with {kpr_count} entries"
            existing.file_size = len(file_content)
            existing.file = content_file
            existing.metadata = json.dumps({
                'filename': filename,
                'kpr_count': kpr_count,
                'product': product_name,
                'imported_at': timezone.now().isoformat()
            })
            existing.save()
            updated_count = 1
            doc_to_return = existing
        else:
            # Create new document for the entire file
            doc = DocumentFile.objects.create(
                title=filename,
                filename=filename,
                file=content_file,
                document_type='SSB_KPR',
                description=f"KPR index file with {kpr_count} entries",
                metadata=json.dumps({
                    'filename': filename,
                    'kpr_count': kpr_count,
                    'product': product_name,
                    'imported_at': timezone.now().isoformat()
                }),
                page_count=1,
                file_size=len(file_content)
            )
            imported_count = 1
            doc_to_return = doc
        
        # Create RAG chunks for the document
        if doc_to_return:
            _create_ssb_chunks(doc_to_return, file_content)
        
        # Return the document with proper serialization
        from ..serializers import DocumentSerializer
        doc = existing if updated_count else doc_to_return
        
        # Serialize the document with file URL
        serializer = DocumentSerializer(doc, context={'request': request})
        
        result = {
            'imported': imported_count,
            'updated': updated_count,
            'skipped': 0,
            'total': 1,
            'document': serializer.data
        }
        
        return success_response(
            f"Successfully imported {imported_count} new and updated {updated_count} existing KPR entries",
            result
        )

    except UnicodeDecodeError as e:
        logger.error(f"Encoding error: {e}")
        return bad_request_response('Unable to decode file. Please use UTF-8 encoded HTML or text files.')
    except Exception as e:
        logger.error(f"Import error: {e}", exc_info=True)
        return error_response(f"Failed to import file: {str(e)}", 500)
