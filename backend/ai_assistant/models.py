from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.utils import timezone
from pgvector.django import VectorField
import hashlib

class UploadedFile(models.Model):
    """Enhanced file storage with hash-based deduplication"""
    filename = models.CharField(max_length=255, db_index=True)
    file_hash = models.CharField(max_length=64, unique=True, db_index=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    intro = models.TextField(null=True, blank=True)
    file_size = models.BigIntegerField(default=0, db_index=True)  # Indexed for duplicate detection
    page_count = models.IntegerField(default=0)
    
    # NEW: Processing status tracking for automatic processing
    PROCESSING_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('metadata_extracting', 'Extracting Metadata'),
        ('chunking', 'Generating Chunks'),
        ('embedding', 'Creating Embeddings'),
        ('ready', 'Ready for Search'),
        ('failed', 'Processing Failed'),
    ]
    
    processing_status = models.CharField(
        max_length=20,
        choices=PROCESSING_STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    
    # Track processing completion stages
    metadata_extracted = models.BooleanField(default=False)
    chunks_created = models.BooleanField(default=False)
    embeddings_created = models.BooleanField(default=False)
    
    # Error tracking
    processing_error = models.TextField(null=True, blank=True)
    processing_started_at = models.DateTimeField(null=True, blank=True)
    processing_completed_at = models.DateTimeField(null=True, blank=True)
    
    # Quality metrics (maintain performance standards)
    chunk_count = models.IntegerField(default=0)  # Actual chunks created
    embedding_count = models.IntegerField(default=0)  # Actual embeddings created
    
    # Document truncation tracking
    is_truncated = models.BooleanField(default=False, help_text="True if document was truncated due to size limits")
    processing_coverage = models.FloatField(default=100.0, help_text="Percentage of document that was processed (0-100)")
    
    def is_ready_for_search(self):
        """Check if file is fully processed and ready for RAG/search"""
        return (
            self.processing_status == 'ready' and
            self.metadata_extracted and
            self.chunks_created and
            self.embeddings_created and
            self.chunk_count > 0 and
            self.embedding_count > 0
        )
    
    @classmethod
    def find_duplicates(cls, file_hash=None, filename=None, file_size=None):
        """
        Enhanced duplicate detection
        
        Checks BOTH file hash AND filename for better deduplication
        """
        duplicates = []
        
        # Check by hash first (most reliable)
        if file_hash:
            hash_matches = cls.objects.filter(file_hash=file_hash)
            duplicates.extend(list(hash_matches))
        
        # Also check by filename and size (catches re-uploads with same name)
        if filename and file_size:
            filename_matches = cls.objects.filter(
                filename=filename,
                file_size=file_size
            )
            duplicates.extend(list(filename_matches))
        
        # Remove duplicates from list
        seen_ids = set()
        unique_duplicates = []
        for dup in duplicates:
            if dup.id not in seen_ids:
                seen_ids.add(dup.id)
                unique_duplicates.append(dup)
        
        return unique_duplicates
    
    def __str__(self):
        return self.filename

    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['processing_status']),
            models.Index(fields=['metadata_extracted', 'chunks_created', 'embeddings_created']),
            # Performance index for duplicate detection
            models.Index(fields=['filename', 'file_size']),
        ]

class DocumentFile(models.Model):
    """Document model for storing various file types"""
    DOCUMENT_TYPES = [
        ('pdf', 'PDF Document'),
        ('doc', 'Word Document'),
        ('docx', 'Word Document'),
        ('xls', 'Excel Spreadsheet'),
        ('xlsx', 'Excel Spreadsheet'),
        ('ppt', 'PowerPoint Presentation'),
        ('pptx', 'PowerPoint Presentation'),
        ('txt', 'Text Document'),
        ('rtf', 'Rich Text Document'),
        ('SSB_KPR', 'SSB/KPR File'),
        ('ssb', 'SSB Entry'),
        ('github', 'GitHub Repository'),
        ('forum', 'Forum Post'),
        ('html', 'HTML Content'),
        ('url', 'Web URL'),
        ('video', 'Video Transcript'),
        ('image', 'Image with OCR'),
    ]
    
    title = models.CharField(max_length=255)
    file = models.FileField(
        upload_to='documents/', 
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'rtf', 'mhtml', 'html'])],
        null=True, blank=True
    )
    filename = models.CharField(max_length=255, null=True, blank=True)
    document_type = models.CharField(max_length=10, choices=DOCUMENT_TYPES, default='pdf')
    description = models.TextField(blank=True, null=True)
    source_url = models.URLField(blank=True, null=True)  # For scraped content
    metadata = models.JSONField(default=dict, blank=True)  # Additional metadata
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    page_count = models.IntegerField(default=0)
    file_size = models.BigIntegerField(default=0)
    
    # Link to UploadedFile for processing status tracking
    uploaded_file = models.ForeignKey(UploadedFile, on_delete=models.SET_NULL, null=True, blank=True, related_name='document_files')

    def __str__(self):
        return self.title
    
    def get_processing_status(self):
        """Get processing status from linked UploadedFile"""
        if self.uploaded_file:
            return {
                'status': self.uploaded_file.processing_status,
                'metadata_extracted': self.uploaded_file.metadata_extracted,
                'chunks_created': self.uploaded_file.chunks_created,
                'embeddings_created': self.uploaded_file.embeddings_created,
                'chunk_count': self.uploaded_file.chunk_count,
                'embedding_count': self.uploaded_file.embedding_count,
                'is_ready': self.uploaded_file.is_ready_for_search(),
                'processing_error': self.uploaded_file.processing_error,
                'is_truncated': self.uploaded_file.is_truncated,
                'processing_coverage': self.uploaded_file.processing_coverage,
            }
        return {
            'status': 'unknown',
            'metadata_extracted': False,
            'chunks_created': False,
            'embeddings_created': False,
            'chunk_count': 0,
            'embedding_count': 0,
            'is_ready': False,
            'processing_error': None,
            'is_truncated': False,
            'processing_coverage': 0.0,
        }

    class Meta:
        ordering = ['-uploaded_at']

class DocumentChunk(models.Model):
    """Document chunks with vector embeddings for RAG"""
    uploaded_file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE, related_name='pages', null=True, blank=True)
    document_file = models.ForeignKey(DocumentFile, on_delete=models.CASCADE, related_name='chunks', null=True, blank=True)
    content = models.TextField()
    embedding = VectorField(dimensions=1024, null=True, blank=True)  # BGE-M3 dimension - allow null for existing data
    page_number = models.IntegerField(default=1)
    chunk_index = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)  # Allow null for existing data

    def __str__(self):
        filename = (
            self.uploaded_file.filename 
            if self.uploaded_file 
            else (self.document_file.filename if self.document_file else 'Unknown')
        )
        return f"{filename} - Page {self.page_number}"

    class Meta:
        ordering = ['uploaded_file', 'document_file', 'page_number', 'chunk_index']

# Legacy PDFDocument for backward compatibility
class PDFDocument(models.Model):
    """Legacy PDF model for backward compatibility"""
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='pdfs/', validators=[FileExtensionValidator(allowed_extensions=['pdf'])])
    filename = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    page_count = models.IntegerField(default=0)
    file_size = models.BigIntegerField(default=0)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-uploaded_at']

class WebLink(models.Model):
    title = models.CharField(max_length=255)
    url = models.URLField()
    tags = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']

class KnowledgeShare(models.Model):
    enabled = models.BooleanField(default=False)
    share_token = models.CharField(max_length=64, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Knowledge Share ({'Enabled' if self.enabled else 'Disabled'})"

class QueryHistory(models.Model):
    """Store query history for RAG and Vector search"""
    query = models.TextField()
    response = models.TextField()
    sources = models.JSONField(default=list)
    query_type = models.CharField(max_length=20, choices=[
        ('rag', 'RAG Search'),
        ('vector', 'Vector Search'),
        ('chat', 'Free Chat')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.query_type}: {self.query[:50]}..."

    class Meta:
        ordering = ['-created_at']


class HelpPortalDocument(models.Model):
    """Track help portal documents and their processing status"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ]
    
    CATEGORY_CHOICES = [
        ('cds', 'OpenLab CDS'),
        ('ecm', 'OpenLab Server/ECM XT'),
        ('shared', 'Shared Services'),
        ('services', 'Test Services'),
        ('other', 'Other'),
    ]
    
    filename = models.CharField(max_length=255)
    file_path = models.CharField(max_length=512)
    file_size = models.BigIntegerField(default=0)
    file_hash = models.CharField(max_length=64, unique=True, db_index=True)
    
    # Classification
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    document_type = models.CharField(max_length=100, blank=True)  # e.g., 'Installation Guide', 'Release Notes'
    version = models.CharField(max_length=50, blank=True)  # e.g., 'v2.8', 'v3.6'
    
    # Processing status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Tracking
    uploaded_file = models.ForeignKey(UploadedFile, on_delete=models.SET_NULL, null=True, blank=True)
    chunk_count = models.IntegerField(default=0)
    
    # Timestamps
    discovered_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Error tracking
    error_message = models.TextField(blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        return self.filename
    
    class Meta:
        ordering = ['category', 'filename']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['category']),
            models.Index(fields=['file_hash']),
        ]