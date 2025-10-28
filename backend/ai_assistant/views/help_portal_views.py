"""
Views for Help Portal document management
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count
from django.core.management import call_command
from io import StringIO
from ai_assistant.models import HelpPortalDocument
from ai_assistant.serializers import HelpPortalDocumentSerializer
from pathlib import Path
import os

import logging
logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_help_portal_documents(request):
    """List all help portal documents with their processing status"""
    try:
        documents = HelpPortalDocument.objects.all()
        
        # Get filters from query parameters
        category = request.query_params.get('category')
        status_filter = request.query_params.get('status')
        
        if category:
            documents = documents.filter(category=category)
        if status_filter:
            documents = documents.filter(status=status_filter)
        
        # Serialize documents
        serializer = HelpPortalDocumentSerializer(documents, many=True)
        
        # Get statistics
        stats = {
            'total': documents.count(),
            'pending': documents.filter(status='pending').count(),
            'processing': documents.filter(status='processing').count(),
            'completed': documents.filter(status='completed').count(),
            'failed': documents.filter(status='failed').count(),
            'skipped': documents.filter(status='skipped').count(),
        }
        
        # Category breakdown
        category_stats = documents.values('category').annotate(count=Count('id'))
        
        return Response({
            'documents': serializer.data,
            'statistics': stats,
            'category_breakdown': list(category_stats),
        })
        
    except Exception as e:
        logger.error(f'Error listing help portal documents: {str(e)}')
        return Response(
            {'error': 'Failed to list help portal documents'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def help_portal_statistics(request):
    """Get statistics about help portal documents"""
    try:
        total = HelpPortalDocument.objects.count()
        by_status = HelpPortalDocument.objects.values('status').annotate(count=Count('id'))
        by_category = HelpPortalDocument.objects.values('category').annotate(count=Count('id'))
        
        return Response({
            'total_documents': total,
            'by_status': {item['status']: item['count'] for item in by_status},
            'by_category': list(by_category),
        })
        
    except Exception as e:
        logger.error(f'Error getting help portal statistics: {str(e)}')
        return Response(
            {'error': 'Failed to get statistics'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def run_help_portal_import(request):
    """Trigger help portal import from UI"""
    try:
        # Get path from request
        folder_path = request.data.get('folder_path', '')
        force = request.data.get('force', False)
        
        # Validate path
        if not folder_path:
            default_path = Path(__file__).parent.parent.parent / 'media' / 'documents' / 'help_portal' / 'Docs' / 'EN'
            folder_path = str(default_path)
        else:
            if not os.path.exists(folder_path):
                return Response(
                    {'error': 'Folder path does not exist'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Check for duplicates before importing
        import sys
        
        # Capture command output
        old_stdout = sys.stdout
        sys.stdout = output_buffer = StringIO()
        
        try:
            args = []
            if force:
                args = ['--force']
            call_command('import_help_portal', *args, verbosity=2)
        finally:
            sys.stdout = old_stdout
        
        output = output_buffer.getvalue()
        
        return Response({
            'success': True,
            'message': 'Import completed successfully',
            'output': output
        })
        
    except Exception as e:
        logger.error(f'Error running help portal import: {str(e)}')
        return Response(
            {'error': f'Import failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_help_portal_duplicates(request):
    """Check for duplicate documents in the help portal"""
    try:
        import hashlib
        from pathlib import Path
        
        # Get folder path
        folder_path = request.query_params.get('folder_path', '')
        
        if not folder_path:
            default_path = Path(__file__).parent.parent.parent / 'media' / 'documents' / 'help_portal' / 'Docs' / 'EN'
            folder_path = str(default_path)
        
        if not os.path.exists(folder_path):
            return Response(
                {'error': 'Folder path does not exist'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find all PDFs
        pdf_files = list(Path(folder_path).glob('*.pdf'))
        
        duplicates = []
        existing = set()
        
        for pdf_file in pdf_files:
            # Calculate hash
            with open(pdf_file, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            
            # Check if already exists in database
            exists = HelpPortalDocument.objects.filter(file_hash=file_hash).exists()
            if exists:
                duplicates.append({
                    'filename': pdf_file.name,
                    'file_path': str(pdf_file),
                    'status': 'duplicate'
                })
            else:
                existing.add(file_hash)
        
        return Response({
            'total_files': len(pdf_files),
            'duplicates': len(duplicates),
            'new_files': len(pdf_files) - len(duplicates),
            'duplicate_files': duplicates,
            'will_process': len(pdf_files) - len(duplicates)
        })
        
    except Exception as e:
        logger.error(f'Error checking duplicates: {str(e)}')
        return Response(
            {'error': f'Failed to check duplicates: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

