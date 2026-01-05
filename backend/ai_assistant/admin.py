from django.contrib import admin
from .models import PDFDocument, UploadedFile, DocumentChunk, DocumentFile, WebLink, KnowledgeShare, QueryHistory, HelpPortalDocument, WebsiteSource, UploadJob
from .tasks import process_file_automatically, process_upload_job


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
    list_display = ('filename', 'uploaded_by', 'uploaded_at', 'file_size', 'page_count', 'processing_status')
    list_filter = ('uploaded_at', 'uploaded_by', 'processing_status')
    search_fields = ('filename', 'intro')
    readonly_fields = ('file_hash', 'uploaded_at', 'file_size', 'page_count')
    actions = ['retry_processing']

    def retry_processing(self, request, queryset):
        count = 0
        for uf in queryset:
            try:
                uf.processing_status = 'pending'
                uf.processing_error = ''
                uf.metadata_extracted = False
                uf.chunks_created = False
                uf.embeddings_created = False
                uf.chunk_count = 0
                uf.embedding_count = 0
                uf.save()
                process_file_automatically.delay(uf.id)
                count += 1
            except Exception:
                continue
        self.message_user(request, f"Re-queued processing for {count} file(s)")
    retry_processing.short_description = "Retry processing for selected uploads"


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


@admin.register(HelpPortalDocument)
class HelpPortalDocumentAdmin(admin.ModelAdmin):
    list_display = ('filename', 'category', 'status', 'chunk_count', 'discovered_at')
    list_filter = ('status', 'category', 'discovered_at')
    search_fields = ('filename', 'document_type', 'version')
    readonly_fields = ('file_hash', 'discovered_at', 'processed_at')


@admin.register(UploadJob)
class UploadJobAdmin(admin.ModelAdmin):
    list_display = ('job_id', 'job_type', 'status', 'priority', 'total_items', 'completed_items', 'failed_items', 'paused', 'created_at', 'created_by')
    list_filter = ('job_type', 'status', 'priority', 'paused', 'created_at')
    search_fields = ('job_id', 'source_path', 'created_by__username')
    readonly_fields = ('job_id', 'created_at', 'started_at', 'completed_at', 'get_progress_percentage')
    ordering = ('-priority', '-created_at')
    
    fieldsets = (
        ('Job Information', {
            'fields': ('job_id', 'job_type', 'source_path', 'status', 'priority')
        }),
        ('Progress', {
            'fields': ('total_items', 'completed_items', 'failed_items', 'get_progress_percentage', 'last_processed_file_index')
        }),
        ('Control', {
            'fields': ('paused', 'cancelled')
        }),
        ('Metadata', {
            'fields': ('metadata', 'error_message', 'file_errors')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'started_at', 'completed_at', 'created_by')
        }),
    )
    
    actions = ['retry_job', 'pause_jobs', 'resume_jobs']
    
    def get_progress_percentage(self, obj):
        return f"{obj.get_progress_percentage()}%"
    get_progress_percentage.short_description = 'Progress'
    
    def retry_job(self, request, queryset):
        """Retry selected jobs"""
        count = 0
        for job in queryset:
            if job.status in ['failed', 'cancelled']:
                job.status = 'queued'
                job.paused = False
                job.cancelled = False
                job.completed_items = 0
                job.failed_items = 0
                job.last_processed_file_index = 0
                job.error_message = None
                job.save()
                process_upload_job.delay(str(job.job_id))
                count += 1
        self.message_user(request, f"Re-queued {count} job(s)")
    retry_job.short_description = "Retry selected jobs"
    
    def pause_jobs(self, request, queryset):
        """Pause selected jobs"""
        count = 0
        for job in queryset:
            if job.status in ['queued', 'uploading', 'processing']:
                job.paused = True
                if job.status in ['uploading', 'processing']:
                    job.status = 'paused'
                job.save()
                count += 1
        self.message_user(request, f"Paused {count} job(s)")
    pause_jobs.short_description = "Pause selected jobs"
    
    def resume_jobs(self, request, queryset):
        """Resume selected jobs"""
        count = 0
        for job in queryset:
            if job.paused:
                job.paused = False
                if job.status == 'paused':
                    job.status = 'queued'
                job.save()
                process_upload_job.delay(str(job.job_id))
                count += 1
        self.message_user(request, f"Resumed {count} job(s)")
    resume_jobs.short_description = "Resume selected jobs"


@admin.register(WebsiteSource)
class WebsiteSourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'domain', 'url', 'processing_status', 'chunk_count', 'created_at')
    list_filter = ('processing_status', 'domain', 'auto_refresh', 'created_at')
    search_fields = ('url', 'title', 'description', 'domain')
    readonly_fields = ('processing_status', 'chunk_count', 'embedding_count', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('url', 'domain', 'title', 'description')
        }),
        ('Processing Status', {
            'fields': ('processing_status', 'metadata_extracted', 'chunks_created', 'embeddings_created')
        }),
        ('Quality Metrics', {
            'fields': ('chunk_count', 'embedding_count', 'page_count')
        }),
        ('Refresh Settings', {
            'fields': ('auto_refresh', 'refresh_interval_days', 'last_refreshed_at', 'next_refresh_at')
        }),
        ('Error Tracking', {
            'fields': ('processing_error', 'processing_started_at', 'processing_completed_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata', 'uploaded_file', 'created_by'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
