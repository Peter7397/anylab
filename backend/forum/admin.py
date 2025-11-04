from django.contrib import admin
from .models import (
    ForumCategory, ForumTag, ForumPost, ForumReply, ForumAttachment,
    ForumLike, ForumMention, ForumNotification, ForumPostTag
)


@admin.register(ForumCategory)
class ForumCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'sort_order', 'is_public_visible', 'allow_public_post', 'is_active', 'created_at')
    list_filter = ('is_public_visible', 'allow_public_post', 'is_active')
    search_fields = ('name', 'description')
    ordering = ('sort_order', 'name')


@admin.register(ForumTag)
class ForumTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'usage_count', 'created_at')
    search_fields = ('name',)
    ordering = ('-usage_count', 'name')


@admin.register(ForumPost)
class ForumPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'status', 'is_pinned', 'is_featured', 'view_count', 'like_count', 'reply_count', 'created_at')
    list_filter = ('status', 'is_pinned', 'is_featured', 'is_public_visible', 'category', 'created_at')
    search_fields = ('title', 'content', 'author__username')
    readonly_fields = ('view_count', 'like_count', 'reply_count', 'created_at', 'updated_at', 'last_reply_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'content', 'author', 'category')
        }),
        ('状态', {
            'fields': ('status', 'is_pinned', 'is_featured', 'pinned_at')
        }),
        ('权限', {
            'fields': ('is_public_visible', 'allow_public_reply')
        }),
        ('统计', {
            'fields': ('view_count', 'like_count', 'reply_count')
        }),
        ('时间', {
            'fields': ('created_at', 'updated_at', 'last_reply_at')
        }),
    )
    
    def get_tags_display(self, obj):
        """Display tags for the post"""
        tags = obj.tags.all()
        return ', '.join([tag.name for tag in tags])
    get_tags_display.short_description = 'Tags'


@admin.register(ForumReply)
class ForumReplyAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'post', 'parent_reply', 'like_count', 'created_at')
    list_filter = ('is_public_visible', 'created_at')
    search_fields = ('content', 'author__username', 'post__title')
    readonly_fields = ('like_count', 'created_at', 'updated_at')


@admin.register(ForumAttachment)
class ForumAttachmentAdmin(admin.ModelAdmin):
    list_display = ('filename', 'post', 'reply', 'file_size', 'uploaded_by', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('filename',)


@admin.register(ForumLike)
class ForumLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'like_type', 'post', 'reply', 'created_at')
    list_filter = ('like_type', 'created_at')


@admin.register(ForumMention)
class ForumMentionAdmin(admin.ModelAdmin):
    list_display = ('mentioned_user', 'mentioned_by', 'post', 'reply', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')


@admin.register(ForumNotification)
class ForumNotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'notification_type', 'actor', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('recipient__username', 'actor__username')

