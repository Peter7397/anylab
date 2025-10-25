from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from users.models import User, Role, UserRole
from monitoring.models import System, SystemMetrics, LogEntry, Alert, NetworkConnection, DatabaseMetrics
from maintenance.models import MaintenanceTask, MaintenanceSchedule, SQLQuery, DatabaseBackup, PerformanceBaseline
from ai_assistant.models import (
    KnowledgeDocument, DocumentChunk, ChatSession, ChatMessage, 
    AIModel, AIConversationTemplate, AIUsageLog
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'employee_id', 'department', 'is_active', 'last_login')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'department', 'created_at')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'employee_id')
    ordering = ('username',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('OneLab Info', {
            'fields': ('employee_id', 'department', 'position', 'phone', 'avatar', 'last_login_ip')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('OneLab Info', {
            'fields': ('employee_id', 'department', 'position', 'phone')
        }),
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'assigned_by', 'assigned_at', 'is_active')
    list_filter = ('is_active', 'assigned_at', 'role')
    search_fields = ('user__username', 'user__email', 'role__name')
    ordering = ('-assigned_at',)


@admin.register(System)
class SystemAdmin(admin.ModelAdmin):
    list_display = ('name', 'hostname', 'ip_address', 'status', 'last_seen', 'created_at')
    list_filter = ('status', 'os_type', 'created_at')
    search_fields = ('name', 'hostname', 'ip_address')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(SystemMetrics)
class SystemMetricsAdmin(admin.ModelAdmin):
    list_display = ('system', 'timestamp', 'cpu_usage', 'memory_usage', 'disk_usage')
    list_filter = ('timestamp', 'system')
    search_fields = ('system__name', 'system__hostname')
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('system', 'timestamp', 'level', 'source', 'message')
    list_filter = ('level', 'source', 'timestamp', 'system')
    search_fields = ('system__name', 'message', 'ip_address')
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('title', 'system', 'severity', 'status', 'created_at')
    list_filter = ('severity', 'status', 'created_at', 'system')
    search_fields = ('title', 'description', 'system__name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)


@admin.register(NetworkConnection)
class NetworkConnectionAdmin(admin.ModelAdmin):
    list_display = ('system', 'local_address', 'local_port', 'remote_address', 'remote_port', 'protocol', 'status')
    list_filter = ('protocol', 'status', 'timestamp', 'system')
    search_fields = ('system__name', 'local_address', 'remote_address', 'process_name')
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)


@admin.register(DatabaseMetrics)
class DatabaseMetricsAdmin(admin.ModelAdmin):
    list_display = ('system', 'timestamp', 'active_connections', 'slow_queries', 'query_time_avg')
    list_filter = ('timestamp', 'system')
    search_fields = ('system__name',)
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)


@admin.register(MaintenanceTask)
class MaintenanceTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'task_type', 'priority', 'status', 'assigned_to', 'scheduled_date')
    list_filter = ('task_type', 'priority', 'status', 'scheduled_date', 'assigned_to')
    search_fields = ('title', 'description', 'assigned_to__username')
    ordering = ('-scheduled_date',)
    filter_horizontal = ('systems',)


@admin.register(MaintenanceSchedule)
class MaintenanceScheduleAdmin(admin.ModelAdmin):
    list_display = ('name', 'frequency', 'interval', 'start_date', 'end_date', 'is_active')
    list_filter = ('frequency', 'is_active', 'start_date')
    search_fields = ('name', 'description')
    ordering = ('name',)


@admin.register(SQLQuery)
class SQLQueryAdmin(admin.ModelAdmin):
    list_display = ('system', 'query_type', 'execution_time', 'rows_affected', 'timestamp')
    list_filter = ('query_type', 'timestamp', 'system')
    search_fields = ('system__name', 'query_text', 'user__username')
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)


@admin.register(DatabaseBackup)
class DatabaseBackupAdmin(admin.ModelAdmin):
    list_display = ('backup_name', 'system', 'backup_type', 'status', 'started_at', 'completed_at')
    list_filter = ('backup_type', 'status', 'started_at', 'system')
    search_fields = ('backup_name', 'system__name', 'created_by__username')
    ordering = ('-started_at',)
    readonly_fields = ('started_at', 'completed_at')


@admin.register(PerformanceBaseline)
class PerformanceBaselineAdmin(admin.ModelAdmin):
    list_display = ('name', 'system', 'cpu_baseline', 'memory_baseline', 'is_active')
    list_filter = ('is_active', 'created_at', 'system')
    search_fields = ('name', 'system__name')
    ordering = ('name',)


@admin.register(KnowledgeDocument)
class KnowledgeDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'document_type', 'status', 'uploaded_by', 'created_at')
    list_filter = ('document_type', 'status', 'language', 'created_at')
    search_fields = ('title', 'content', 'uploaded_by__username')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'processing_started', 'processing_completed')


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ('document', 'chunk_index', 'content_preview')
    list_filter = ('document', 'chunk_index')
    search_fields = ('document__title', 'content')
    ordering = ('document', 'chunk_index')
    
    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content Preview'


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'session_type', 'created_at', 'is_active')
    list_filter = ('session_type', 'is_active', 'created_at')
    search_fields = ('title', 'user__username')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'message_type', 'content_preview', 'timestamp')
    list_filter = ('message_type', 'timestamp', 'session__session_type')
    search_fields = ('content', 'session__title', 'session__user__username')
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)
    
    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content Preview'


@admin.register(AIModel)
class AIModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'model_type', 'mode', 'is_active', 'is_default')
    list_filter = ('model_type', 'mode', 'is_active', 'is_default')
    search_fields = ('name', 'description')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AIConversationTemplate)
class AIConversationTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'template_type', 'is_active', 'created_at')
    list_filter = ('template_type', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AIUsageLog)
class AIUsageLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'model', 'model_mode', 'tokens_used', 'response_time', 'timestamp')
    list_filter = ('model_mode', 'request_type', 'timestamp', 'model__model_type')
    search_fields = ('user__username', 'model__name')
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',) 