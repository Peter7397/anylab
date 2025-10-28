"""
Request/Response Serializers Module

This module provides comprehensive serializers for request validation
and response formatting for the AI Assistant application.
"""

from rest_framework import serializers
from django.core.files.uploadedfile import InMemoryUploadedFile
from typing import Dict, Any, List, Optional
from .models import (
    PDFDocument, WebLink, KnowledgeShare, 
    UploadedFile, DocumentChunk, DocumentFile, QueryHistory
)
from .metadata_schema import OrganizationMode, DocumentType, FilterCriteria, SortOrder


# ============================================================================
# REQUEST SERIALIZERS
# ============================================================================

class ChatRequestSerializer(serializers.Serializer):
    """Serializer for chat requests"""
    prompt = serializers.CharField(max_length=2000, help_text="The user's prompt or question")
    max_tokens = serializers.IntegerField(min_value=1, max_value=2048, required=False, default=256)
    temperature = serializers.FloatField(min_value=0.0, max_value=2.0, required=False, default=0.3)
    top_p = serializers.FloatField(min_value=0.0, max_value=1.0, required=False, default=0.9)
    top_k = serializers.IntegerField(min_value=1, max_value=100, required=False, default=40)
    repeat_penalty = serializers.FloatField(min_value=0.0, max_value=2.0, required=False, default=1.1)
    num_ctx = serializers.IntegerField(min_value=512, max_value=4096, required=False, default=1024)


class RAGSearchRequestSerializer(serializers.Serializer):
    """Serializer for RAG search requests"""
    query = serializers.CharField(max_length=500, help_text="Search query")
    search_mode = serializers.ChoiceField(
        choices=['comprehensive', 'advanced', 'enhanced', 'basic'],
        default='comprehensive',
        help_text="Search mode"
    )
    top_k = serializers.IntegerField(min_value=1, max_value=50, required=False, default=10)
    include_stats = serializers.BooleanField(required=False, default=False)


class VectorSearchRequestSerializer(serializers.Serializer):
    """Serializer for vector search requests"""
    query = serializers.CharField(max_length=500, help_text="Search query")
    search_mode = serializers.ChoiceField(
        choices=['comprehensive', 'advanced', 'enhanced', 'basic'],
        default='comprehensive',
        help_text="Search mode"
    )
    top_k = serializers.IntegerField(min_value=1, max_value=50, required=False, default=10)


class DocumentUploadRequestSerializer(serializers.Serializer):
    """Serializer for document upload requests"""
    file = serializers.FileField(help_text="Document file to upload")
    title = serializers.CharField(max_length=200, required=False, help_text="Document title")
    description = serializers.CharField(max_length=1000, required=False, help_text="Document description")
    document_type = serializers.ChoiceField(
        choices=[(choice.value, choice.value) for choice in DocumentType],
        required=False,
        help_text="Document type"
    )
    organization_mode = serializers.ChoiceField(
        choices=[(choice.value, choice.value) for choice in OrganizationMode],
        required=False,
        default='general',
        help_text="Organization mode"
    )
    
    def validate_file(self, value):
        """Validate uploaded file"""
        if not isinstance(value, InMemoryUploadedFile):
            raise serializers.ValidationError("Invalid file type")
        
        # Check file size (max 500MB to allow large manuals and documents)
        if value.size > 500 * 1024 * 1024:
            raise serializers.ValidationError("File size must be less than 500MB")
        
        # Check file extension
        allowed_extensions = ['.pdf', '.txt', '.doc', '.docx', '.html', '.htm']
        if not any(value.name.lower().endswith(ext) for ext in allowed_extensions):
            raise serializers.ValidationError(f"File type not supported. Allowed: {', '.join(allowed_extensions)}")
        
        return value


class FilterCriteriaSerializer(serializers.Serializer):
    """Serializer for filter criteria"""
    field = serializers.CharField(max_length=100, help_text="Field to filter on")
    operator = serializers.ChoiceField(
        choices=['eq', 'ne', 'gt', 'gte', 'lt', 'lte', 'contains', 'icontains', 'in', 'isnull'],
        help_text="Filter operator"
    )
    value = serializers.CharField(max_length=500, help_text="Filter value")


class DocumentFilterRequestSerializer(serializers.Serializer):
    """Serializer for document filtering requests"""
    query = serializers.CharField(max_length=500, required=False, help_text="Search query")
    organization_mode = serializers.ChoiceField(
        choices=[(choice.value, choice.value) for choice in OrganizationMode],
        default='general',
        help_text="Organization mode"
    )
    filters = FilterCriteriaSerializer(many=True, required=False, help_text="Filter criteria")
    sort_order = serializers.ChoiceField(
        choices=[(choice.value, choice.value) for choice in SortOrder],
        default='relevance',
        help_text="Sort order"
    )
    page = serializers.IntegerField(min_value=1, required=False, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=100, required=False, default=20)
    user_preferences = serializers.JSONField(required=False, help_text="User preferences")
    search_history = serializers.ListField(
        child=serializers.CharField(max_length=500),
        required=False,
        help_text="Search history"
    )


class ScrapingConfigSerializer(serializers.Serializer):
    """Serializer for scraping configuration"""
    max_pages = serializers.IntegerField(min_value=1, max_value=1000, required=False, default=100)
    delay_between_requests = serializers.FloatField(min_value=0.1, max_value=10.0, required=False, default=1.0)
    timeout = serializers.IntegerField(min_value=5, max_value=300, required=False, default=30)
    retry_attempts = serializers.IntegerField(min_value=1, max_value=10, required=False, default=3)


class SSBScrapingRequestSerializer(serializers.Serializer):
    """Serializer for SSB scraping requests"""
    config = ScrapingConfigSerializer(required=False, help_text="Scraping configuration")


class ForumScrapingRequestSerializer(serializers.Serializer):
    """Serializer for forum scraping requests"""
    config = ScrapingConfigSerializer(required=False, help_text="Scraping configuration")


class GitHubScanningRequestSerializer(serializers.Serializer):
    """Serializer for GitHub scanning requests"""
    config = ScrapingConfigSerializer(required=False, help_text="Scanning configuration")


class HTMLParsingRequestSerializer(serializers.Serializer):
    """Serializer for HTML parsing requests"""
    url = serializers.URLField(required=False, help_text="URL to parse")
    html_text = serializers.CharField(required=False, help_text="HTML text to parse")
    config = ScrapingConfigSerializer(required=False, help_text="Parsing configuration")
    
    def validate(self, data):
        """Validate that either URL or html_text is provided"""
        if not data.get('url') and not data.get('html_text'):
            raise serializers.ValidationError("Either URL or html_text must be provided")
        return data


class FilterPresetRequestSerializer(serializers.Serializer):
    """Serializer for filter preset requests"""
    name = serializers.CharField(max_length=100, help_text="Preset name")
    preset_data = serializers.JSONField(help_text="Preset data")


class MetadataUpdateRequestSerializer(serializers.Serializer):
    """Serializer for metadata update requests"""
    metadata_updates = serializers.JSONField(help_text="Metadata updates")


# ============================================================================
# RESPONSE SERIALIZERS
# ============================================================================

class BaseResponseSerializer(serializers.Serializer):
    """Base response serializer"""
    success = serializers.BooleanField(help_text="Success status")
    message = serializers.CharField(help_text="Response message")
    timestamp = serializers.DateTimeField(help_text="Response timestamp")


class ChatResponseSerializer(BaseResponseSerializer):
    """Serializer for chat responses"""
    data = serializers.DictField(help_text="Chat response data")


class SearchResponseSerializer(BaseResponseSerializer):
    """Serializer for search responses"""
    data = serializers.DictField(help_text="Search results data")


class DocumentResponseSerializer(BaseResponseSerializer):
    """Serializer for document responses"""
    data = serializers.DictField(help_text="Document data")


class ScrapingResponseSerializer(BaseResponseSerializer):
    """Serializer for scraping responses"""
    data = serializers.DictField(help_text="Scraping results data")


class StatusResponseSerializer(BaseResponseSerializer):
    """Serializer for status responses"""
    data = serializers.DictField(help_text="Status data")


class AnalyticsResponseSerializer(BaseResponseSerializer):
    """Serializer for analytics responses"""
    data = serializers.DictField(help_text="Analytics data")


class ErrorResponseSerializer(serializers.Serializer):
    """Serializer for error responses"""
    error = serializers.DictField(help_text="Error information")
    timestamp = serializers.DateTimeField(help_text="Error timestamp")


# ============================================================================
# MODEL SERIALIZERS (Enhanced)
# ============================================================================

class PDFDocumentSerializer(serializers.ModelSerializer):
    """Enhanced serializer for PDF Document model"""
    
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


class DocumentFileSerializer(serializers.ModelSerializer):
    """Enhanced serializer for DocumentFile model"""
    
    file_size_mb = serializers.SerializerMethodField()
    uploaded_date = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    metadata = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentFile
        fields = [
            'id', 'title', 'filename', 'document_type', 'description', 'uploaded_by', 
            'uploaded_at', 'page_count', 'file_size_mb', 'uploaded_date', 'file_url', 'metadata'
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
    
    def get_metadata(self, obj):
        if obj.metadata:
            try:
                import json
                return json.loads(obj.metadata)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}


class QueryHistorySerializer(serializers.ModelSerializer):
    """Enhanced serializer for QueryHistory model"""
    
    class Meta:
        model = QueryHistory
        fields = '__all__'
        read_only_fields = ('created_at', 'user')


class WebLinkSerializer(serializers.ModelSerializer):
    """Enhanced serializer for WebLink model"""
    
    class Meta:
        model = WebLink
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'added_by')


class KnowledgeShareSerializer(serializers.ModelSerializer):
    """Enhanced serializer for KnowledgeShare model"""
    
    class Meta:
        model = KnowledgeShare
        fields = '__all__'
        read_only_fields = ('created_at', 'created_by')


class UploadedFileSerializer(serializers.ModelSerializer):
    """Enhanced serializer for UploadedFile model"""
    
    class Meta:
        model = UploadedFile
        fields = '__all__'
        read_only_fields = ('uploaded_at', 'uploaded_by', 'file_hash')


class DocumentChunkSerializer(serializers.ModelSerializer):
    """Enhanced serializer for DocumentChunk model"""
    
    uploaded_file = UploadedFileSerializer(read_only=True)
    
    class Meta:
        model = DocumentChunk
        fields = '__all__'
        read_only_fields = ('created_at',)
