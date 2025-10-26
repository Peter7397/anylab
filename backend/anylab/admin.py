from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from users.models import User, Role, UserRole
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