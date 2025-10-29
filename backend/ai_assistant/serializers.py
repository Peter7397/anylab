from rest_framework import serializers
from .models import (
    PDFDocument, WebLink, KnowledgeShare, 
    UploadedFile, DocumentChunk, DocumentFile, QueryHistory,
    HelpPortalDocument
)


class PDFDocumentSerializer(serializers.ModelSerializer):
    """Serializer for PDF Document model."""
    
    file_size_mb = serializers.SerializerMethodField()
    uploaded_date = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = PDFDocument
        fields = [
            'id', 'title', 'filename', 'description', 'uploaded_by', 
            'uploaded_at', 'page_count', 'file_size_mb', 'uploaded_date', 'file_url'
        ]
        read_only_fields = ['id', 'uploaded_by', 'uploaded_at', 'file_size_mb', 
                           'uploaded_date', 'file_url']
    
    def get_file_size_mb(self, obj):
        if obj.file_size:
            return f"{obj.file_size / (1024*1024):.2f} MB"
        return "0 MB"
    
    def get_uploaded_date(self, obj):
        return obj.uploaded_at.strftime("%Y-%m-%d %H:%M:%S") if obj.uploaded_at else ""
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
        return None


class PDFUploadSerializer(serializers.ModelSerializer):
    """Serializer for PDF upload."""
    
    class Meta:
        model = PDFDocument
        fields = ['title', 'file', 'description']
    
    def validate_file(self, value):
        """Validate uploaded file."""
        # Check file size (max 50MB)
        if value.size > 50 * 1024 * 1024:
            raise serializers.ValidationError("File size must be less than 50MB.")
        
        # Check file extension
        if not value.name.lower().endswith('.pdf'):
            raise serializers.ValidationError("Only PDF files are allowed.")
        
        return value
    
    def create(self, validated_data):
        """Create PDF document with user info."""
        request = self.context.get('request')
        validated_data['filename'] = validated_data['file'].name
        
        # Set uploaded_by if user is authenticated, otherwise leave it null
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            validated_data['uploaded_by'] = request.user
        
        return super().create(validated_data)


class PDFSearchSerializer(serializers.Serializer):
    """Serializer for PDF search."""
    
    query = serializers.CharField(max_length=200)
    search_type = serializers.ChoiceField(
        choices=['title', 'content', 'both'],
        default='both'
    )


class WebLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebLink
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'added_by')


class KnowledgeShareSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeShare
        fields = '__all__'
        read_only_fields = ('created_at', 'created_by')


class UploadedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = '__all__'
        read_only_fields = ('uploaded_at', 'uploaded_by', 'file_hash')


class DocumentChunkSerializer(serializers.ModelSerializer):
    uploaded_file = UploadedFileSerializer(read_only=True)
    
    class Meta:
        model = DocumentChunk
        fields = '__all__'
        read_only_fields = ('created_at',)

class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for Document model (various file types)"""
    file_size_mb = serializers.SerializerMethodField()
    uploaded_date = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    processing_status = serializers.SerializerMethodField()
    uploaded_file_id = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentFile
        fields = [
            'id', 'title', 'filename', 'document_type', 'description', 'uploaded_by', 
            'uploaded_at', 'page_count', 'file_size_mb', 'uploaded_date', 'file_url',
            'metadata', 'source_url', 'processing_status', 'uploaded_file_id'
        ]
        read_only_fields = ['id', 'uploaded_by', 'uploaded_at', 'file_size_mb', 
                           'uploaded_date', 'file_url', 'metadata', 'source_url', 'processing_status', 'uploaded_file_id']
    
    def get_file_size_mb(self, obj):
        if obj.file_size:
            return f"{obj.file_size / (1024*1024):.2f} MB"
        return "0 MB"
    
    def get_uploaded_date(self, obj):
        return obj.uploaded_at.strftime("%Y-%m-%d %H:%M:%S") if obj.uploaded_at else ""
    
    def get_file_url(self, obj):
        request = self.context.get('request')
        if not request:
            return None
        
        # For SSB_KPR documents (MHTML), use the HTML view endpoint
        if obj.document_type == 'SSB_KPR':
            return request.build_absolute_uri(f'/api/ai/documents/{obj.id}/html/')
        
        # Check if DocumentFile has a file field (legacy documents)
        if obj.file and hasattr(obj.file, 'url'):
            return request.build_absolute_uri(obj.file.url)
        
        # For uploaded documents, file is stored via UploadedFile
        # The file is in media/uploads/filename.ext
        if hasattr(obj, 'uploaded_file') and obj.uploaded_file:
            # Generate URL from UploadedFile.filename
            # uploaded_file.filename is stored as 'uploads/filename.ext'
            media_url = request.build_absolute_uri(f'/media/{obj.uploaded_file.filename}')
            return media_url
        
        return None
    
    def get_processing_status(self, obj):
        """Get processing status from linked UploadedFile"""
        return obj.get_processing_status()

    def get_uploaded_file_id(self, obj):
        return obj.uploaded_file.id if getattr(obj, 'uploaded_file', None) else None


class QueryHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = QueryHistory
        fields = '__all__'
        read_only_fields = ('created_at', 'user')


class HelpPortalDocumentSerializer(serializers.ModelSerializer):
    """Serializer for Help Portal Document model"""
    
    file_size_mb = serializers.SerializerMethodField()
    discovered_date = serializers.SerializerMethodField()
    processed_date = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = HelpPortalDocument
        fields = [
            'id', 'filename', 'file_path', 'file_size', 'file_size_mb', 'file_hash',
            'category', 'category_display', 'document_type', 'version',
            'status', 'status_display', 'chunk_count', 'error_message',
            'discovered_at', 'discovered_date', 'processed_at', 'processed_date',
            'metadata'
        ]
        read_only_fields = [
            'id', 'file_hash', 'chunk_count', 'discovered_at', 'processed_at'
        ]
    
    def get_file_size_mb(self, obj):
        if obj.file_size:
            return f"{obj.file_size / (1024*1024):.2f} MB"
        return "0 MB"
    
    def get_discovered_date(self, obj):
        return obj.discovered_at.strftime("%Y-%m-%d %H:%M:%S") if obj.discovered_at else ""
    
    def get_processed_date(self, obj):
        return obj.processed_at.strftime("%Y-%m-%d %H:%M:%S") if obj.processed_at else ""
