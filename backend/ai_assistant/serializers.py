from rest_framework import serializers
from .models import (
    PDFDocument, WebLink, KnowledgeShare, 
    UploadedFile, DocumentChunk, DocumentFile, QueryHistory
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
    
    class Meta:
        model = DocumentFile
        fields = [
            'id', 'title', 'filename', 'document_type', 'description', 'uploaded_by', 
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


class QueryHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = QueryHistory
        fields = '__all__'
        read_only_fields = ('created_at', 'user')
