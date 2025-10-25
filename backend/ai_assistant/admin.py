from django.contrib import admin
from .models import PDFDocument, UploadedFile, DocumentChunk, DocumentFile, WebLink, KnowledgeShare, QueryHistory


@admin.register(PDFDocument)
class PDFDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'filename', 'uploaded_by', 'uploaded_at', 'file_size', 'page_count')
    list_filter = ('uploaded_at', 'uploaded_by')
    search_fields = ('title', 'filename', 'description')
    readonly_fields = ('file_size', 'uploaded_at')
    
    def file_size_mb(self, obj):
        return f"{obj.file_size / (1024*1024):.2f} MB" if obj.file_size else "0 MB"
    file_size_mb.short_description = "File Size"


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ('filename', 'uploaded_by', 'uploaded_at', 'file_size', 'page_count')
    list_filter = ('uploaded_at', 'uploaded_by')
    search_fields = ('filename', 'intro')
    readonly_fields = ('file_hash', 'uploaded_at', 'file_size', 'page_count')


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ('uploaded_file', 'page_number', 'chunk_index', 'created_at')
    list_filter = ('uploaded_file', 'page_number', 'created_at')
    search_fields = ('content', 'uploaded_file__filename')
    readonly_fields = ('created_at',)

@admin.register(DocumentFile)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'filename', 'document_type', 'uploaded_by', 'uploaded_at', 'file_size', 'page_count')
    list_filter = ('document_type', 'uploaded_at', 'uploaded_by')
    search_fields = ('title', 'filename', 'description')
    readonly_fields = ('uploaded_at', 'file_size', 'page_count')


@admin.register(WebLink)
class WebLinkAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'added_by', 'created_at')
    list_filter = ('created_at', 'added_by')
    search_fields = ('title', 'url', 'tags')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(KnowledgeShare)
class KnowledgeShareAdmin(admin.ModelAdmin):
    list_display = ('enabled', 'created_by', 'created_at')
    list_filter = ('enabled', 'created_at')
    readonly_fields = ('share_token', 'created_at')


@admin.register(QueryHistory)
class QueryHistoryAdmin(admin.ModelAdmin):
    list_display = ('query_type', 'query', 'user', 'created_at')
    list_filter = ('query_type', 'created_at', 'user')
    search_fields = ('query', 'response')
    readonly_fields = ('created_at',)
