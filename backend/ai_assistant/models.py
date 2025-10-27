from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.utils import timezone
from pgvector.django import VectorField
import hashlib

class UploadedFile(models.Model):
    """Enhanced file storage with hash-based deduplication"""
    filename = models.CharField(max_length=255)
    file_hash = models.CharField(max_length=64, unique=True, db_index=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    intro = models.TextField(null=True, blank=True)
    file_size = models.BigIntegerField(default=0)
    page_count = models.IntegerField(default=0)

    def __str__(self):
        return self.filename

    class Meta:
        ordering = ['-uploaded_at']

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

    def __str__(self):
        return self.title

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